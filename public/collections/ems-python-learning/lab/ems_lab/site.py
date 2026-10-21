"""第 07 章：电站测量平面、效率链、方向换算与站点功率平衡。

约定（附录 B）：
- 效率链上的功率一律以“从电池流向电网”为正：放电为正、充电为负；
- P_BESS 指 PCS 交流端口功率（放电为正），P_PCC 指并网点净功率（向电网送电为正）；
- 电表“进口为正”只在接入层出现：P_import = −P_PCC；
- 负荷、辅助用电、损耗为正值。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .control import clamp_power
from .power import pcc_injection_kw


# ---------------------------------------------------------------- 效率链
@dataclass(frozen=True)
class Stage:
    """效率链中的一个环节（PCS、变压器、线路……），按“直流侧 → 电网侧”的顺序排列。

    eta_discharge：功率从电池流向电网时，本环节“出 / 入”之比；
    eta_charge：功率从电网流向电池时的效率；None 表示与放电相同。
    两个方向的效率可能不同（PCS 尤其如此），不能混用。
    """

    name: str
    eta_discharge: float
    eta_charge: float | None = None

    def __post_init__(self):
        for eta in (self.eta_discharge, self.eta_charge):
            if eta is not None and not 0 < eta <= 1:
                raise ValueError(f"{self.name} 效率必须在 (0, 1] 内")

    @property
    def eta_chg(self) -> float:
        return self.eta_discharge if self.eta_charge is None else self.eta_charge


@dataclass
class ChainResult:
    """各测量平面上的功率与各环节损耗。

    powers_kw[0] 是直流侧，powers_kw[-1] 是最靠电网的一侧，长度 = 环节数 + 1；
    losses_kw[i] 是第 i 个环节的损耗（恒为非负）。
    """

    names: list[str]
    powers_kw: list[float]
    losses_kw: list[float]

    @property
    def total_loss_kw(self) -> float:
        return sum(self.losses_kw)


def _losses(powers: list[float]) -> list[float]:
    # 损耗 = 靠直流侧的功率 − 靠电网侧的功率。放电时两者为正、前者大；
    # 充电时两者为负、后者绝对值大。两种情况下这个差都是非负的。
    return [powers[i] - powers[i + 1] for i in range(len(powers) - 1)]


def chain_from_dc(p_dc_kw: float, stages: Sequence[Stage]) -> ChainResult:
    """已知直流侧功率，逐级推算到电网侧。

    放电（p > 0）：功率向电网流，每过一个环节乘以 η_放；
    充电（p < 0）：功率从电网流来，电网侧要比直流侧多，每过一个环节除以 η_充。
    """
    powers = [p_dc_kw]
    p = p_dc_kw
    for st in stages:
        p = p * st.eta_discharge if p >= 0 else p / st.eta_chg
        powers.append(p)
    return ChainResult([st.name for st in stages], powers, _losses(powers))


def chain_from_grid(p_grid_kw: float, stages: Sequence[Stage]) -> ChainResult:
    """已知电网侧功率，逐级反推到直流侧（与 chain_from_dc 互逆）。"""
    powers = [p_grid_kw]
    p = p_grid_kw
    for st in reversed(stages):
        p = p / st.eta_discharge if p >= 0 else p * st.eta_chg
        powers.append(p)
    powers.reverse()
    return ChainResult([st.name for st in stages], powers, _losses(powers))


def transformer_loss_kw(s_kva: float, s_rated_kva: float, p_noload_kw: float, p_load_rated_kw: float) -> float:
    """变压器损耗 = 空载损耗 + 负载损耗 × (S / S_rated)²。

    空载损耗（铁损）只要变压器带电就存在，与功率无关；负载损耗（铜损）与电流平方成正比。
    所以“变压器效率”不是常数：轻载时效率低，空载时效率无意义但损耗仍在。
    """
    if s_rated_kva <= 0 or s_kva < 0 or p_noload_kw < 0 or p_load_rated_kw < 0:
        raise ValueError("参数必须非负，额定容量必须为正")
    return p_noload_kw + p_load_rated_kw * (s_kva / s_rated_kva) ** 2


def round_trip_efficiency(stages: Sequence[Stage]) -> float:
    """功率链自身的往返效率（充一次再放一次）：Π η_放 × Π η_充。

    注意：不含电池本体的充放电损耗，也不含待机时的空载损耗和辅助用电。
    """
    eff = 1.0
    for st in stages:
        eff *= st.eta_discharge * st.eta_chg
    return eff


# ---------------------------------------------------------------- 方向与变比换算（只在接入层使用）
def pcc_from_meter(p_meter_kw: float, meter_import_positive: bool = True) -> float:
    """把电表读数换成控制层方向 P_PCC（向电网送电为正）。

    meter_import_positive=True：电表“从电网取电为正”（进口为正），需要取反。
    """
    return -p_meter_kw if meter_import_positive else p_meter_kw


def import_from_pcc(p_pcc_kw: float) -> float:
    """控制层 P_PCC → 计费/需量使用的进口功率 P_import = −P_PCC。"""
    return -p_pcc_kw


def correct_ratio_kw(p_reported_kw: float, ratio_configured: float, ratio_actual: float) -> float:
    """变比配置错误时的修正：真实值 = 上报值 × 实际变比 / 配置变比。

    例：CT 实际 1500/5（=300），电表里配置成 1000/5（=200），上报值只有真实值的 2/3。
    """
    if ratio_configured <= 0 or ratio_actual <= 0:
        raise ValueError("变比必须为正")
    return p_reported_kw * ratio_actual / ratio_configured


# ---------------------------------------------------------------- 功率平衡
def site_pcc_kw(
    p_pv_kw: float,
    p_bess_kw: float,
    p_load_kw: float,
    p_aux_kw: float = 0.0,
    p_loss_kw: float = 0.0,
    load_includes_aux: bool = False,
) -> float:
    """站点功率平衡 P_PCC = P_PV + P_BESS − P_load − P_aux − P_loss。

    - p_bess_kw 必须是 PCS 交流侧功率（PCS 损耗已经包含在内，不能再扣）；
    - p_loss_kw 只包含 PCS 交流端口到并网点之间、没有被任何测点反映的损耗；
    - load_includes_aux=True 表示负荷测点已经包含辅助用电，此时不能再减一次 P_aux。
    """
    aux = 0.0 if load_includes_aux else p_aux_kw
    return pcc_injection_kw(p_bess_kw, p_load_kw, aux, p_loss_kw, p_pv_kw)


def bess_command_for_pcc_target(
    p_pcc_target_kw: float,
    p_pv_kw: float,
    p_load_kw: float,
    p_aux_kw: float = 0.0,
    p_loss_kw: float = 0.0,
    available_charge_kw: float | None = None,
    available_discharge_kw: float | None = None,
    load_includes_aux: bool = False,
) -> float:
    """由并网点目标反算储能交流侧指令。

    ``p_load_kw`` 默认不含辅助用电；若负荷测点已包含辅助用电，传入
    ``load_includes_aux=True``，避免在目标反算中重复加上 ``p_aux_kw``。
    给出可充/可放能力时，再按方向限幅（第 12 章会把它扩展成完整的可行域）。
    """
    aux = 0.0 if load_includes_aux else p_aux_kw
    p = p_pcc_target_kw - p_pv_kw + p_load_kw + aux + p_loss_kw
    if available_charge_kw is not None and available_discharge_kw is not None:
        p = clamp_power(p, available_charge_kw, available_discharge_kw)
    return p


def diagnose_balance(
    p_pcc_measured_kw: float,
    p_pv_kw: float,
    p_bess_kw: float,
    p_load_kw: float,
    p_aux_kw: float = 0.0,
    p_loss_kw: float = 0.0,
    tol_kw: float = 5.0,
) -> list[str]:
    """对比“电表实测的 P_PCC”和“各分项算出的 P_PCC”，给出可能的原因。

    残差 = 实测 − 计算。返回空列表表示在容差内一致。
    这只是调试辅助：给出的是“嫌疑”，最终要靠方向核对试验和图纸确认。
    """
    computed = site_pcc_kw(p_pv_kw, p_bess_kw, p_load_kw, p_aux_kw, p_loss_kw)
    residual = p_pcc_measured_kw - computed
    if abs(residual) <= tol_kw:
        return []
    hints: list[str] = []
    if p_aux_kw and abs(residual - p_aux_kw) <= tol_kw:
        hints.append("辅助负荷可能被重复统计：P_load 测点已包含 P_aux")
    if p_aux_kw and abs(residual + p_aux_kw) <= tol_kw:
        hints.append("辅助负荷可能漏计：有一路辅助用电没有进入 P_load 或 P_aux")
    if p_bess_kw and abs(residual + 2 * p_bess_kw) <= tol_kw:
        hints.append("储能功率方向可能接反：残差约为 −2 × P_BESS")
    if abs(computed) > tol_kw and abs(p_pcc_measured_kw + computed) <= tol_kw:
        hints.append("并网点电表方向可能接反：实测值与计算值大小相等、符号相反")
    if not hints and abs(computed) > tol_kw and p_pcc_measured_kw * computed > 0:
        ratio = p_pcc_measured_kw / computed
        hints.append(f"实测是计算值的 {ratio:.2f} 倍：检查 CT/PT 变比或缩放系数")
    if not hints:
        hints.append(f"残差 {residual:+.1f} kW 无法归因：检查未计入的负荷、损耗或测点时间不同步")
    return hints


def check_direction(delta_expected_kw: float, delta_observed_kw: float, tol_ratio: float = 0.2) -> str:
    """方向核对试验的判定：储能按已知步长变化后，测点变化是否符合预期。

    delta_expected_kw：按约定“应该”变化多少（例如储能多放 100 kW，P_PCC 应 +100）；
    delta_observed_kw：实际读到的变化量（已经过接入层换算）。
    """
    if delta_expected_kw == 0:
        raise ValueError("试验步长不能为 0")
    if abs(delta_observed_kw) < tol_ratio * abs(delta_expected_kw):
        return "无响应：检查通信、测点映射或 PCS 是否执行"
    ratio = delta_observed_kw / delta_expected_kw
    if ratio < 0:
        return "方向相反：检查电表/PCS 的正方向定义和接入层换算"
    if abs(ratio - 1) > tol_ratio:
        return f"幅值偏差：实测变化是预期的 {ratio:.2f} 倍，检查变比、缩放系数或单位"
    return "OK"

