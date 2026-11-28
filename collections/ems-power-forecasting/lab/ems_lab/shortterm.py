# @AI_GENERATED
"""第 05 章核心模块：短期功率预测（物理基值 + 分箱偏差修正）。

约定（对齐 03.x / 05.x 手算、附录B）：
- 短期预测 0-72h（日前为主）：输入 NWP 气象源（GHI / T_amb / v，经第 04 章门控），
  输出并网点出力预测 P_hat。
- 建模范式：物理基值（复用第 03 章光伏链，保饱和区正确）+ 分箱偏差修正（学掉系统性偏差）。
- 偏差 = 实测 P_meas − 物理预测 P_phys；分箱统计每箱偏差均值 bias_k 作为修正项。
- 最终预测 P_hat = P_phys + bias_k（bias_k 为 P_phys 所在箱的偏差均值）。

教学示例默认值（对齐 03.x / 05.x 手算，主线 30 MWp 光伏）：
- P_rated = 30 MWp、逆变额定 25 MW、限电 0.8 MW（复用 03 章）
- 历史 6 样本按 P_phys 分 3 箱 [0,5) / [5,20) / [20,∞)：
  偏差均值 bias = [+0.5, −0.9, −2.25] MW（低出力物理略低估、正午物理高估）
- 手算主案例：NWP GHI=800、T_amb=20 -> P_phys=20.404 -> 箱3 -> P_hat = 20.404 − 2.25 = 18.154 MW
"""
from __future__ import annotations

from ems_lab.irradiance import (
    cell_temperature,
    ghi_to_poa,
    inverter_ac,
    pv_dc_power,
    pv_pcc_power,
)

P_RATED = 30.0       # 主线光伏额定 MWp
INV_RATING = 25.0    # 逆变器额定（饱和边界）MW
LIMIT_MW = 0.8       # 调度限电 MW（对齐 03.4 手算）


def physical_forecast(ghi: float, t_amb: float, p_rated: float = P_RATED,
                      transposition: float = 1.0, inv_rating: float = INV_RATING,
                      limit_mw: float = LIMIT_MW, eta: float = 0.95) -> float:
    """NWP（GHI, T_amb）-> 并网点光伏物理预测 P_phys（复用 03 章光伏链）。

    链路：GHI -> POA -> T_cell -> P_module -> P_ac（逆变削峰）-> P_pv（减限电）。
    手算主案例：GHI=800、T_amb=20 -> 20.404 MW（对齐 03.4）。
    """
    poa = ghi_to_poa(ghi, transposition)
    t_cell = cell_temperature(t_amb, poa)
    p_dc = pv_dc_power(p_rated, poa, t_cell)
    p_ac = inverter_ac(p_dc, eta, inv_rating)
    return pv_pcc_power(p_ac, limit_mw, maint_mw=0.0)


def _bin_index(value: float, bin_edges: list[float]) -> int:
    """返回 value 所在箱（0 起）。

    箱 0: value < e0；中间箱 i: e_{i-1} ≤ value < e_i；末箱: value ≥ 最后一个边界。
    """
    for i, edge in enumerate(bin_edges):
        if value < edge:
            return i
    return len(bin_edges)


def fit_bin_bias(p_phys_list: list[float], p_meas_list: list[float],
                 bin_edges: list[float]) -> list[float]:
    """从历史 (P_phys, P_meas) 分箱统计偏差均值（偏差 = 实测 − 物理）。

    返回 bias（长度 = len(bin_edges) + 1）；空箱偏差记 0.0（无样本不修正）。
    手算：6 样本、边界 [5, 20] -> bias = [+0.5, −0.9, −2.25]。
    """
    if len(p_phys_list) != len(p_meas_list):
        raise ValueError(f"物理与实测样本数须一致，实际 {len(p_phys_list)} vs {len(p_meas_list)}")
    if any(bin_edges[i] >= bin_edges[i + 1] for i in range(len(bin_edges) - 1)):
        raise ValueError(f"分箱边界须严格升序，实际 {bin_edges}")
    n_bins = len(bin_edges) + 1
    sums = [0.0] * n_bins
    counts = [0] * n_bins
    for p_phys, p_meas in zip(p_phys_list, p_meas_list):
        k = _bin_index(p_phys, bin_edges)
        sums[k] += p_meas - p_phys
        counts[k] += 1
    return [sums[k] / counts[k] if counts[k] else 0.0 for k in range(n_bins)]


def bias_correct(p_phys: float, bin_edges: list[float], bias: list[float]) -> float:
    """分箱偏差修正：P_hat = P_phys + bias[所在箱]。

    边界语义：边界值 5.0 归箱2（5 ≤ x < 20）；20.0 归箱3（x ≥ 20）。
    """
    if len(bias) != len(bin_edges) + 1:
        raise ValueError(f"偏差箱数须 = 边界数 + 1，实际 {len(bias)} vs {len(bin_edges)} + 1")
    return p_phys + bias[_bin_index(p_phys, bin_edges)]


def short_term_forecast(ghi: float, t_amb: float, bin_edges: list[float],
                        bias: list[float], **kwargs) -> float:
    """端到端短期预测：物理基值 + 分箱偏差修正 -> P_hat。

    主案例：short_term_forecast(800, 20, [5, 20], [0.5, -0.9, -2.25]) -> 18.154。
    """
    p_phys = physical_forecast(ghi, t_amb, **kwargs)
    return bias_correct(p_phys, bin_edges, bias)
# @AI_GENERATED: end