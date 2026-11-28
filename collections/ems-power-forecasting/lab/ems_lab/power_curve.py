# @AI_GENERATED
"""第 03 章核心模块：风速 -> 风机出力转换（功率曲线）。

约定（对齐 03.x 手算）：
- 标准四区功率曲线：v < v_ci 不发电；v_ci ≤ v < v_r 立方插值；v_r ≤ v ≤ v_co 额定（饱和）；v > v_co 切出停机。
- 立方插值：P = P_rated × (v³ − v_ci³)/(v_r³ − v_ci³)，体现风能 ∝ v³ 的三次方关系。
- 边界语义：v == v_ci -> 0；v == v_r -> 恰好额定；v == v_co -> 仍满发（超过才切出）。

教学示例默认值（对齐 03.x 手算，主线无风电，此处为教学示例单机）：
- P_rated = 2.5 MW、v_ci = 3 m/s、v_r = 12 m/s、v_co = 25 m/s
- 手算：v = 6 m/s（半额定风速）-> (216−27)/(1728−27) = 1/9 -> 2.5/9 ≈ 0.278 MW（只发额定 1/9）
- v = 9 m/s（3/4 额定风速）-> 702/1701 ≈ 0.413 -> 1.032 MW
- v = 12~25 m/s -> 2.5 MW（饱和）；v ≥ 26 m/s -> 0（切出）
"""
from __future__ import annotations


def wind_power(v: float, p_rated: float = 2.5, v_ci: float = 3.0,
               v_r: float = 12.0, v_co: float = 25.0) -> float:
    """风速 -> 单机出力（MW），标准四区功率曲线。

    v < v_ci（无风）或 v > v_co（切出）-> 0；
    v_ci ≤ v < v_r 立方插值（风能 ∝ v³）；v_r ≤ v ≤ v_co 额定（饱和区，变桨保持）。
    """
    if v < 0:
        raise ValueError(f"风速不能为负，实际 {v}")
    if p_rated < 0:
        raise ValueError(f"额定功率不能为负，实际 {p_rated}")
    if not (0 <= v_ci < v_r < v_co):
        raise ValueError(f"风速边界须满足 0 ≤ v_ci < v_r < v_co，实际 v_ci={v_ci}, v_r={v_r}, v_co={v_co}")
    if v < v_ci or v > v_co:
        return 0.0
    if v < v_r:
        return p_rated * (v ** 3 - v_ci ** 3) / (v_r ** 3 - v_ci ** 3)
    return p_rated
# @AI_GENERATED: end