# @AI_GENERATED
"""第 04 章核心模块：NWP 气象数据质量门控（坏数据识别）。

约定（对齐 04.x 手算、附录B）：
- 门控对象：NWP 格点/测站下发的气象序列（辐照 GHI、温度 T_amb、风速 v）。
- 五类坏数据：缺测(missing)、超限(range)、跳变(step)、卡死(stuck)、时标错位(timestamp)。
- 判定均输出"掩码"（bool 列表）：True = 坏点，False = 好点。
- 边界语义：跳变判定"首点不判、缺测点不参与"；卡死判定"夜间 0 值豁免"。

教学示例阈值（对齐 04.x 手算、附录B）：
- 物理范围：GHI [0, 1200] W/m²；温度 [-40, 50] °C；风速 [0, 40] m/s
- 辐照变化率上限 600 W/(m²·15min)；卡死判定 连续 4 个点值相同
- 时标网格 15 min，容差 ±2.5 min
"""
from __future__ import annotations

import math


def _is_missing(v) -> bool:
    """缺测判定：None 或 float 的 NaN。"""
    return v is None or (isinstance(v, float) and math.isnan(v))


def missing_mask(values: list) -> list[bool]:
    """缺测掩码：NaN/None 记缺测。

    教学示例：GHI=[800, 810, nan, ...] -> 第 3 个点（索引 2）缺测。
    """
    return [_is_missing(v) for v in values]


def range_mask(values: list, vmin: float, vmax: float) -> list[bool]:
    """物理范围掩码：值 < vmin 或 > vmax 记超限（缺测点不在此判，由缺测负责）。

    教学示例：GHI 范围 [0, 1200] -> -50（负值）与 1300（超上限）都超限。
    """
    if vmin >= vmax:
        raise ValueError(f"范围下界必须小于上界，实际 [{vmin}, {vmax}]")
    return [not _is_missing(v) and (v < vmin or v > vmax) for v in values]


def step_mask(values: list, max_step: float) -> list[bool]:
    """跳变掩码：相邻"有效点"差值绝对值 > max_step 时，记后一点为跳变。

    首点不判；缺测点跳过、与"上一个有效点"比较。
    教学示例：max_step=600 -> 300 之后接 1200，Δ=900 > 600 -> 1200 判跳变；
             820 之后接 300，Δ=520 <= 600 -> 300 不判（云团经过，不误杀）。
    """
    if max_step < 0:
        raise ValueError(f"变化率上限不能为负，实际 {max_step}")
    mask = [False] * len(values)
    last = None
    for i, v in enumerate(values):
        if _is_missing(v):
            continue
        if last is not None and abs(v - last) > max_step:
            mask[i] = True
        last = v
    return mask


def stuck_mask(values: list, max_run: int = 4, allow_flat: float = 0.0) -> list[bool]:
    """卡死掩码：连续 >= max_run 个点值完全相同（且值 != allow_flat）记整段卡死。

    allow_flat 默认 0.0：夜间辐照恒 0 是合法平坦，不判卡死（夜间零值豁免）。
    教学示例：820×4 -> 4 点全判卡死；0×5（夜间）-> 不判。
    """
    if max_run < 2:
        raise ValueError(f"卡死判定长度至少为 2，实际 {max_run}")
    mask = [False] * len(values)
    n = len(values)
    i = 0
    while i < n:
        if _is_missing(values[i]):
            i += 1
            continue
        j = i
        while j + 1 < n and not _is_missing(values[j + 1]) and values[j + 1] == values[i]:
            j += 1
        run_len = j - i + 1
        if run_len >= max_run and values[i] != allow_flat:
            for k in range(i, j + 1):
                mask[k] = True
        i = j + 1
    return mask


def timestamp_mask(times_min: list, dt_minutes: float = 15.0,
                   tol_minutes: float = 2.5) -> list[bool]:
    """时标错位掩码：偏离 dt_minutes 网格（分钟）超过 tol_minutes 记错位。

    times_min 为"距当日 00:00 的分钟数"（浮点）。
    教学示例：15 min 网格、容差 ±2.5 min ->
              11:00 = 660.0 分钟 -> 0 偏移 -> 对齐；
              12:07:30 = 727.5 分钟 -> 偏移 7.5 min > 2.5 -> 错位。
    """
    if dt_minutes <= 0:
        raise ValueError(f"网格间隔必须为正，实际 {dt_minutes}")
    mask = []
    for t in times_min:
        offset = t % dt_minutes
        offset = min(offset, dt_minutes - offset)
        mask.append(offset > tol_minutes)
    return mask


def quality_mask(values: list, vmin: float, vmax: float, max_step: float,
                 max_run: int = 4, allow_flat: float = 0.0) -> list[bool]:
    """综合坏点掩码 = 缺测 | 超限 | 跳变 | 卡死（时标单独用 timestamp_mask）。

    教学示例：GHI=[800, 810, nan, 820, 820, 820, 820, 300, 1200, 1300]
              -> 缺测(索引2) + 卡死(索引3~6) + 跳变(索引8) + 超限(索引9)
              -> 坏点 7 个、有效点 3 个、有效点率 30%。
    """
    m_miss = missing_mask(values)
    m_range = range_mask(values, vmin, vmax)
    m_step = step_mask(values, max_step)
    m_stuck = stuck_mask(values, max_run, allow_flat)
    return [a or b or c or d for a, b, c, d in zip(m_miss, m_range, m_step, m_stuck)]


def fill_missing(values: list) -> list:
    """缺测点回填：内部缺测线性插值，首尾缺测用最近有效值回填。

    教学示例：GHI=[810, nan, 820] -> 缺测点 = (810+820)/2 = 815。
    """
    out = list(values)
    n = len(out)
    valid_idx = [i for i, v in enumerate(out) if not _is_missing(v)]
    if not valid_idx:
        return out
    first, last = valid_idx[0], valid_idx[-1]
    for i in range(first):          # 首部缺测 -> 最近有效值
        out[i] = out[first]
    for i in range(last + 1, n):    # 尾部缺测 -> 最近有效值
        out[i] = out[last]
    for a, b in zip(valid_idx, valid_idx[1:]):  # 内部缺测 -> 线性插值
        if b - a == 1:
            continue
        for i in range(a + 1, b):
            out[i] = out[a] + (out[b] - out[a]) * (i - a) / (b - a)
    return out
# @AI_GENERATED: end