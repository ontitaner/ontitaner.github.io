# @AI_GENERATED
"""第 11 章核心模块：预测 EMS 流水线与数据契约。

约定（对齐 04/05/06 章手算、附录B/C）：
- 流水线四段：气象入站 → 数据质量门控 → 模型推理 → 预测发布。
- 数据契约：发布频率 15 min 一点（一天 96 点）、单位 MW（并网点）、时标对齐 15min 网格 ±2.5min。
- 门控复用 04 章 quality_mask，回填复用 04 章 fill_missing，推理复用 05 章 short_term_forecast。
- 发布记录 status 标记：valid = 门控通过的好点；filled = 坏点经回填后发布的点。

教学示例默认值（对齐 04/05 章手算，主线 30 MW 光伏）：
- 发布频率 DT = 15 min、时标容差 ±2.5 min（对齐 04 章 timestamp_mask）
- 门控阈值：GHI [0, 1200] W/m²、跳变上限 600 W/(m²·15min)（对齐 04 章）
- 短期分箱 [5, 20]、偏差 [+0.5, −0.9, −2.25]（对齐 05 章）
- 手算主案例：11:00 GHI=800、T_amb=20 -> 门控通过 -> P_hat=18.154 -> 发布 -> 契约校验通过
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ems_lab.nwp_quality import fill_missing, quality_mask
from ems_lab.shortterm import short_term_forecast

DT_MINUTES = 15.0    # 发布频率：15 min 一点，一天 96 点
TOL_MINUTES = 2.5     # 时标容差：±2.5 min（对齐 04 章 timestamp_mask）
UNIT = "MW"           # 发布单位：并网点出力

GHI_VMIN = 0.0        # GHI 物理范围下界（对齐 04 章）
GHI_VMAX = 1200.0     # GHI 物理范围上界（对齐 04 章）
GHI_MAX_STEP = 600.0  # GHI 跳变上限 W/(m²·15min)（对齐 04 章）

BIN_EDGES = [5.0, 20.0]          # 短期分箱边界（对齐 05 章）
BIAS = [0.5, -0.9, -2.25]        # 分箱偏差均值（对齐 05 章）

STATUS_VALID = "valid"    # 门控通过的好点
STATUS_FILLED = "filled"  # 坏点经回填后发布


@dataclass
class ForecastRecord:
    """一条预测发布记录（数据契约的载体）。"""

    timestamp_min: float   # 距当日 00:00 的分钟数（应落在 15min 网格 ±2.5min 内）
    p_hat: float           # 预测出力（MW，并网点）
    status: str            # valid=门控通过 / filled=坏点回填后发布
    version: str = "v1"    # 模型版本
    unit: str = UNIT       # 单位


def run_forecast_pipeline(ghi_seq: list, t_amb_seq: list, times_min: list,
                          bin_edges: list = BIN_EDGES, bias: list = BIAS,
                          vmin: float = GHI_VMIN, vmax: float = GHI_VMAX,
                          max_step: float = GHI_MAX_STEP, **kwargs) -> list[ForecastRecord]:
    """气象入站 → 门控 → 回填 → 推理 → 发布，返回 ForecastRecord 列表。

    四段职责：
    1. 入站：NWP 下发 GHI/T_amb 序列 + 时标（本章以 GHI 门控为例，T_amb 假设已干净）。
    2. 门控：quality_mask 识别缺测/超限/跳变/卡死坏点。
    3. 回填：坏点置 NaN 后 fill_missing（内部线性插值、首尾最近有效值）。
    4. 推理 + 发布：逐点 short_term_forecast，坏点回填的记录 status=filled。

    主案例：run_forecast_pipeline([800, nan, 820], [20, 20, 20], [660, 675, 690])
        -> [valid@660=18.154, filled@675=18.394, valid@690=18.633]
    """
    if not (len(ghi_seq) == len(t_amb_seq) == len(times_min)):
        raise ValueError(
            f"辐照/温度/时标序列长度须一致，实际 {len(ghi_seq)} vs {len(t_amb_seq)} vs {len(times_min)}"
        )
    bad = quality_mask(list(ghi_seq), vmin, vmax, max_step)
    ghi_filled = fill_missing([math.nan if b else g for g, b in zip(ghi_seq, bad)])
    records: list[ForecastRecord] = []
    for t, g, ta, b in zip(times_min, ghi_filled, t_amb_seq, bad):
        p_hat = short_term_forecast(g, ta, bin_edges, bias, **kwargs)
        records.append(ForecastRecord(t, p_hat, STATUS_FILLED if b else STATUS_VALID))
    return records


def validate_contract(records: list[ForecastRecord],
                      dt: float = DT_MINUTES, tol: float = TOL_MINUTES) -> list[dict]:
    """对每条预测发布记录做数据契约校验（发布前的最后一道把关）。

    校验项：
    - aligned：时标是否落在 dt 网格 ±tol 内（复用 04 章 timestamp_mask 的偏移口径）
    - unit_ok：单位是否为 MW
    - status_ok：状态是否为合法枚举（valid/filled）
    - p_hat_ok：预测值是否非负
    - ok：以上全部通过

    主案例：记录 660.0 min -> 偏移 0 -> aligned=True；
             记录 727.5 min -> 偏移 7.5 > 2.5 -> aligned=False -> ok=False。
    """
    if dt <= 0:
        raise ValueError(f"发布频率必须为正，实际 {dt}")
    out: list[dict] = []
    for r in records:
        offset = r.timestamp_min % dt
        offset = min(offset, dt - offset)
        aligned = offset <= tol + 1e-9
        unit_ok = r.unit == UNIT
        status_ok = r.status in (STATUS_VALID, STATUS_FILLED)
        p_hat_ok = r.p_hat >= 0.0
        out.append({
            "timestamp_min": r.timestamp_min,
            "aligned": aligned,
            "unit_ok": unit_ok,
            "status_ok": status_ok,
            "p_hat_ok": p_hat_ok,
            "ok": aligned and unit_ok and status_ok and p_hat_ok,
        })
    return out
# @AI_GENERATED: end