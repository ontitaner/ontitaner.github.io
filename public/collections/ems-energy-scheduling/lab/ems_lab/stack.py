# @AI_GENERATED
"""辅助服务叠加的容量分配

对应章节：08 辅助服务叠加

教学示例（对齐 08.3）：
  额定 50MW，一次调频（PFR）备用 10MW，剩余 40MW 用于套利放电。
"""
from __future__ import annotations


def capacity_split(p_nom: float = 50.0, pfr_reserve: float = 10.0,
                   volt_reserve: float = 0.0) -> dict:
    """返回 {pfr, volt, arbitrage, total}（MW）。

    调频、电压备用按顺序占用容量，剩余容量留给套利。
    """
    pfr = min(pfr_reserve, p_nom)
    volt = min(volt_reserve, p_nom - pfr)
    arbitrage = p_nom - pfr - volt
    return dict(pfr=pfr, volt=volt, arbitrage=arbitrage, total=p_nom)
# @AI_GENERATED: end