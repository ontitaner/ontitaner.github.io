# @AI_GENERATED
"""第 06 章核心模块：超短期功率预测（持续法 + 滚动外推）。

约定（对齐 06.x 手算、附录B）：
- 超短期预测 15min-4h：输入最近 15min 实测出力序列（并网点，经第 04 章门控后的好点），
  输出未来 horizon 步（每步 15min）的并网点出力预测。
- 建模范式：持续法（baseline）+ 滚动外推（最近变化率外推 + 物理 clamp + 滚动更新）。
- 变化率 Δ = P_meas(t) − P_meas(t−1)（两点斜率，MW/步）；历史不足 2 点时 Δ = 0（退化为持续法）。
- 滚动外推：P_hat(t+h) = clamp(P_meas(t) + Δ·h, 0, P_max)，h = 1..horizon。
- P_max = 25 MW（逆变额定，对齐 05.1 的"物理天花板"；并网点还要减限电 0.8，真实天花板略低于 25）。

教学示例默认值（对齐 06.x 手算，主线 30 MW 光伏，15min 网格）：
- 滚动窗口长度 3：历史实测 [16, 17, 18] -> Δ = +1 -> 外推 [19, 20, 21, 22]
- 滚动更新：新实测 18.5 -> 窗口 [17, 18, 18.5] -> Δ = +0.5 -> 外推 [19.0, 19.5, 20.0, 20.5]
- 触顶 clamp：历史 [22, 24] -> Δ = +2 -> [26, 28, 30, 32] 均截到 25 -> [25, 25, 25, 25]
- 退化：历史仅 1 点 [18] -> Δ = 0 -> 退化为持续法 [18, 18, 18, 18]
"""
from __future__ import annotations

P_MAX = 25.0        # 物理天花板（逆变额定）MW，对齐 05.1
WINDOW_LEN = 3      # 滚动窗口长度（教学示例）


def persistence_forecast(p_now: float, horizon: int) -> list[float]:
    """持续法（persistence）：未来 horizon 步全部 = 当前实测 p_now。

    主案例：persistence_forecast(18.0, 4) -> [18.0, 18.0, 18.0, 18.0]。
    """
    if horizon < 0:
        raise ValueError(f"预测步数不能为负，实际 {horizon}")
    return [p_now] * horizon


def _trend_slope(history: list[float]) -> float:
    """最近变化率 Δ = history[-1] − history[-2]（两点斜率，MW/步）。

    历史不足 2 点（只有当前值）时返回 0.0（退化为持续法）。
    """
    if len(history) < 2:
        return 0.0
    return history[-1] - history[-2]


def rolling_extrapolate(history: list[float], horizon: int,
                        p_max: float = P_MAX) -> list[float]:
    """滚动外推：P_hat(t+h) = clamp(history[-1] + Δ·h, 0, p_max)，h = 1..horizon。

    history 为最近实测序列（时间升序，含当前点）；Δ 用最近两点斜率。
    主案例：rolling_extrapolate([16, 17, 18], 4) -> [19.0, 20.0, 21.0, 22.0]。
    """
    if not history:
        raise ValueError("历史实测序列不能为空")
    if horizon < 0:
        raise ValueError(f"预测步数不能为负，实际 {horizon}")
    if p_max <= 0.0:
        raise ValueError(f"物理上限必须为正，实际 {p_max}")
    slope = _trend_slope(history)
    last = history[-1]
    out: list[float] = []
    for h in range(1, horizon + 1):
        v = last + slope * h
        out.append(min(max(v, 0.0), p_max))
    return out


def roll_window(history: list[float], new_meas: float,
                max_len: int = WINDOW_LEN) -> list[float]:
    """滚动窗口右移：追加新实测，超长丢弃最旧，保持窗口长度 max_len。

    主案例：roll_window([16, 17, 18], 18.5) -> [17, 18, 18.5]。
    """
    if max_len < 1:
        raise ValueError(f"窗口长度至少为 1，实际 {max_len}")
    out = list(history) + [new_meas]
    return out[-max_len:]
# @AI_GENERATED: end