# @AI_GENERATED
"""第 09 章核心模块：验收失败根因诊断。

诊断 = 从验收/结算的「结果值」反推「原因值」，与配置对表，定位三类根因：
1. 配置错误（伪失败）：参数误设、出力方向接反 —— 改配置/对时即过。
2. 能力不足（真失败）：SOC 不足、J/D 整定本身偏小 —— 需补容量/重新整定。
3. 量测污染（数据问题）：时钟未对时、RoCoF 窗口混扰动 —— 需挑干净窗口重测。

反推对表（对齐 07/08 手算，主线 50 MW/100 MWh、S_n=50 MVA、f_n=50 Hz）：
- 一次调频：实测 ΔP → 反推 D = ΔP·f_n/|Δf|；配置 D=33.333（δ=3%）；
  实测 0.3 pu → D=25（δ=4%）≠ 配置 → 根因「参数误设」。
- 惯量：J_eq_total → 本站贡献 J_station = J_eq_total − J_sys0；
  J_eq=10 s → 3.333 s ≪ 配置 13.333 s，SOC=40% < 50% → 根因「SOC 不足」。
- 结算方向：期望增发 +0.4 pu、实测 −0.4 pu → 根因「出力方向接反」。
- 证据链：最大偏差 15 ms > 10 ms → 根因「时钟未对时」。
"""
from __future__ import annotations

from dataclasses import dataclass

# 反推值与配置值的对表容差：区分「参数被改」与「浮点近似」。
# 参数误设至少差几个 pu（25 vs 33.333），浮点近似误差仅 ~1e-4，故 1e-2 足够。
_EPS = 1e-2


@dataclass(frozen=True)
class DiagnosisCriteria:
    """验收失败诊断教学参数（与前序一致，非整定值）。"""

    tol_pu: float = 0.02        # 一次调频允许偏差（pu）
    d_config: float = 33.333    # 配置 D（δ=3%）
    df_hz: float = -0.6         # 试验频率阶跃（负 = 跌落）
    expected_pu: float = 0.4    # 一次调频期望增发（= D·|Δf|/f_n）
    j_eq_req_s: float = 20.0    # 合同要求等效惯量（03.2 总 20 s）
    j_sys0_s: float = 6.667     # 系统原有惯量（50×0.1/0.75 ≈ 6.667 s）
    j_config_s: float = 13.333  # 配置 J_vsg（40/3 s）
    soc_min: float = 0.50       # 惯量支撑最低 SOC（门槛）
    ts_bias_max_ms: float = 10.0  # 证据链时钟偏差上限（ms）


# ---------- 反推函数 ----------

def back_calc_D(measured_pu: float, df_hz: float, f_n: float = 50.0) -> float:
    """由实测增发反推实际 D：D = ΔP·f_n/|Δf|。

    实测 0.3 pu、Δf=−0.6 Hz → 0.3×50/0.6 = 25 pu（δ=100/25=4%）。
    """
    if df_hz == 0:
        raise ValueError("Δf 不能为 0（无法反推 D）")
    return measured_pu * f_n / abs(df_hz)


def back_calc_station_J(j_eq_total_s: float, j_sys0_s: float) -> float:
    """由系统总等效惯量反推本站贡献：J_station = J_eq_total − J_sys0。

    J_eq=10 s、J_sys0=6.667 s → 3.333 s（≪ 配置 13.333 s）。
    """
    return j_eq_total_s - j_sys0_s


# ---------- 诊断函数 ----------

def diagnose_pfr_failure(measured_pu: float, expected_pu: float, tol_pu: float,
                         d_config: float, df_hz: float, f_n: float = 50.0) -> str:
    """一次调频验收失败根因诊断。

    反推 D_actual = ΔP·f_n/|Δf|，与配置 d_config 对表：
    - 达标：|measured − expected| ≤ tol → 'pass'；
    - 反推 D ≠ 配置 D → 'param_mismatch'（参数被改，如 D 误设 25）；
    - 反推 D = 配置 D 但偏差超 tol → 'expected_wrong'（期望值口径错，设备输出其实正确）。
    """
    if abs(measured_pu - expected_pu) <= tol_pu:
        return "pass"
    d_actual = back_calc_D(measured_pu, df_hz, f_n)
    if abs(d_actual - d_config) > _EPS:
        return "param_mismatch"
    return "expected_wrong"


def diagnose_inertia_failure(j_eq_total_s: float, j_eq_req_s: float, j_sys0_s: float,
                             j_config_s: float, soc: float, soc_min: float) -> str:
    """惯量响应验收失败根因诊断。

    - 达标：J_eq_total ≥ J_eq_req → 'pass'；
    - 反推本站贡献 J_station = J_eq_total − J_sys0，再逐层定位：
      - SOC < soc_min → 'soc_low'（SOC 不足，支撑打折）；
      - J_station < J_config → 'underperformed'（配置了没发挥，量测污染嫌疑）；
      - 否则 → 'param_j_low'（J 整定本身偏小）。
    """
    if j_eq_total_s >= j_eq_req_s:
        return "pass"
    j_station = back_calc_station_J(j_eq_total_s, j_sys0_s)
    if soc < soc_min:
        return "soc_low"
    if j_station < j_config_s - _EPS:
        return "underperformed"
    return "param_j_low"


def diagnose_direction(expected_pu: float, measured_pu: float) -> str:
    """出力方向诊断：期望与实测符号相反 → 出力方向接反。

    期望 +0.4 pu（增发）、实测 −0.4 pu（减发）→ 'reversed'。
    """
    if expected_pu == 0 or measured_pu == 0:
        raise ValueError("期望/实测不能为 0（无法判定方向）")
    return "reversed" if expected_pu * measured_pu < 0 else "normal"


def diagnose_clock(max_bias_ms: float, max_ms: float = 10.0) -> str:
    """证据链时钟偏差诊断：偏差 > 阈值 → 时钟未对时。

    最大偏差 15 ms > 10 ms → 'clock_drift'。
    """
    return "clock_drift" if max_bias_ms > max_ms else "pass"
# @AI_GENERATED: end