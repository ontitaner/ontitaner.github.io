# @AI_GENERATED
"""第 03 章核心模块：惯量支撑与一次调频融合。

约定（对齐 00.6 / 02.x / 03.x 手算）：
- RoCoF（Hz/s）与系统等效惯量 J_eq（秒）的反比关系：RoCoF = f_n·ΔP_pu / J_eq。
- 惯量支撑功率（pu）：P_inertia = J·|RoCoF| / f_n，即虚拟惯量在频率变化率下释放的功率。
- 阻尼 D 与一次调频调差率 δ% 的倒数关系：D = 100 / δ%（即 δ% = 100 / D）。
- 构网型无死区下垂：ΔP_pu = −D·Δf/f_n；传统一次调频在此之上叠加 ±db_hz 死区。

教学示例默认值（对齐 03.x 手算，主线 50 MW/100 MWh、S_n=50 MVA）：
- 功率缺口 ΔP=0.1 pu、f_n=50 Hz、系统 RoCoF=0.75 Hz/s（00.1 场景）
- 系统原等效惯量 J_sys0 = 50×0.1/0.75 ≈ 6.667 s（折算到站级 50 MVA 基准）；本站虚拟惯量 13.333 s → 总 20 s（3 倍）
  → RoCoF 0.75 → 0.25 Hz/s
- 调差率 δ=3% → D = 100/3 ≈ 33.333 pu；D=20/40（02 章教学值）对应 δ=5%/2.5%
- 频率跌 0.6 Hz：构网型增发 20 MW；传统（死区 ±0.06 Hz）只增发 18 MW
"""
from __future__ import annotations


def system_rocof_hz(delta_p_pu: float, J_eq: float, f_n: float = 50.0) -> float:
    """系统 RoCoF（Hz/s）= f_n·ΔP_pu / J_eq。

    J_eq 为系统等效惯量（秒，折算到同一基准）。J_eq 越大 RoCoF 越小。
    """
    if J_eq <= 0:
        raise ValueError(f"J_eq 必须为正（等效惯量），实际 {J_eq}")
    return f_n * delta_p_pu / J_eq


def system_inertia_s(delta_p_pu: float, rocof_hz: float, f_n: float = 50.0) -> float:
    """由 RoCoF 反求等效惯量：J_eq = f_n·ΔP_pu / RoCoF（秒）。

    用于把 00.1 的 RoCoF=0.75 Hz/s 折算成系统等效惯量。
    """
    if rocof_hz == 0:
        raise ValueError("RoCoF 不能为 0（无法反求惯量）")
    return f_n * delta_p_pu / rocof_hz


def inertia_power_pu(J: float, rocof_hz: float, f_n: float = 50.0) -> float:
    """惯量支撑功率（pu）：P_inertia = J·|RoCoF| / f_n。

    虚拟惯量 J 在频率变化率 RoCoF 下释放的功率；RoCoF 归零时该功率自动归零。
    """
    if J < 0:
        raise ValueError(f"J 不能为负（虚拟惯量），实际 {J}")
    if f_n <= 0:
        raise ValueError(f"f_n 必须为正，实际 {f_n}")
    return J * abs(rocof_hz) / f_n


def droop_to_D(droop_pct: float) -> float:
    """调差率 δ%（如 3.0）→ 阻尼 D = 100/δ%（pu）。

    δ=3% → D≈33.333 pu；δ 越小（越陡），D 越大。
    """
    if droop_pct <= 0:
        raise ValueError(f"调差率必须为正，实际 {droop_pct}%")
    return 100.0 / droop_pct


def D_to_droop_pct(D: float) -> float:
    """阻尼 D → 调差率 δ% = 100/D。

    D=20 → δ=5%；D=40 → δ=2.5%。
    """
    if D <= 0:
        raise ValueError(f"D 必须为正，实际 {D}")
    return 100.0 / D


def pfr_deadzone(df_hz: float, db_hz: float = 0.06) -> float:
    """传统一次调频死区：|Δf| ≤ 死区时有效频差为 0，否则扣除死区。

    边界语义：|Δf| == db_hz 时视为在死区内（返回 0），与 00.2「死区内不响应」一致。
    """
    if db_hz < 0:
        raise ValueError(f"死区不能为负，实际 {db_hz}")
    if abs(df_hz) <= db_hz:
        return 0.0
    return df_hz - db_hz * (1.0 if df_hz > 0 else -1.0)


def gridforming_delta_p_pu(df_hz: float, D: float, f_n: float = 50.0) -> float:
    """构网型无死区下垂：ΔP_pu = −D·Δf/f_n。

    Δf<0（频率跌落）时 ΔP_pu>0，表示增发功率。
    """
    return -D * df_hz / f_n


def pfr_delta_p_pu(df_hz: float, D: float, db_hz: float = 0.06, f_n: float = 50.0) -> float:
    """传统一次调频（有死区）下垂：ΔP_pu = −D·deadzone(Δf)/f_n。

    死区内有效频差为 0 时显式返回 0.0，避免浮点负零（-0.0）干扰打印与断言。
    """
    dz = pfr_deadzone(df_hz, db_hz)
    if dz == 0.0:
        return 0.0
    return -D * dz / f_n


def support_duration_h(energy_kwh: float, power_kw: float) -> float:
    """支撑可持续时间（小时）= 可用能量（kWh）/ 支撑功率（kW）。"""
    if power_kw <= 0:
        raise ValueError(f"支撑功率必须为正，实际 {power_kw}")
    return energy_kwh / power_kw
# @AI_GENERATED: end