# @AI_GENERATED
"""第 02 章核心模块：VSG 虚拟同步机——J/D/V_ref 三参数的离散化摇摆方程。

参数与约定对齐章节 02.x 手算与 00.6 约定：
- J：虚拟惯量系数（秒），摇摆方程写成 J·dω/dt = P_ref − P − D·(ω − 1)，
  其中 ω、P 均为标幺值。
- D：阻尼系数（pu）。
- P_ref：有功参考（pu），基准 S_n = 50 MVA。
- ω：VSG 自建角频率（pu），额定 = 1.0。
- dt：离散步长（秒）。
- V_ref / k_q / Q_ref：Q-V 下垂参数，V = V_ref − k_q·(Q − Q_ref)。

全部为无状态的纯推进函数，数值与正文手算一致，一致性测试见 tests/test_vsg.py。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VSGConfig:
    """VSG 三参数 + 下垂参数（教学示例默认值，对齐正文手算）。"""

    J: float = 4.0        # 虚拟惯量（秒）
    D: float = 20.0       # 阻尼（pu）
    p_ref: float = 0.5    # 有功参考（pu）
    v_ref: float = 1.0    # 电压参考（pu）
    k_q: float = 0.05     # Q-V 下垂斜率（pu/pu）
    q_ref: float = 0.0    # 无功参考（pu）
    dt: float = 0.1       # 离散步长（秒）

    def __post_init__(self):
        if self.J <= 0:
            raise ValueError(f"J 必须为正（虚拟惯量），实际 {self.J}")
        if self.D < 0:
            raise ValueError(f"D 不能为负（阻尼），实际 {self.D}")
        if self.dt <= 0:
            raise ValueError(f"dt 必须为正（离散步长），实际 {self.dt}")


def swing_domega(omega: float, p_e: float, cfg: VSGConfig) -> float:
    """摇摆方程右侧：J·dω/dt = p_ref − p_e − D·(ω − 1)，返回 dω/dt（pu/s）。"""
    return (cfg.p_ref - p_e - cfg.D * (omega - 1.0)) / cfg.J


def swing_step(omega: float, p_e: float, cfg: VSGConfig) -> float:
    """前向欧拉推进一拍：ω_next = ω + dt·dω/dt。"""
    return omega + cfg.dt * swing_domega(omega, p_e, cfg)


def rocof_hz(p_e: float, p_ref: float, J: float, f_n: float = 50.0) -> float:
    """功率不平衡瞬间的初始 RoCoF（Hz/s）：f_n·(p_ref − p_e)/J。

    p_e > p_ref（功率缺口）时为负值，表示频率跌落。
    """
    return f_n * (p_ref - p_e) / J


def q_v_droop(q: float, cfg: VSGConfig) -> float:
    """Q-V 下垂：V = v_ref − k_q·(q − q_ref)。"""
    return cfg.v_ref - cfg.k_q * (q - cfg.q_ref)
# @AI_GENERATED: end