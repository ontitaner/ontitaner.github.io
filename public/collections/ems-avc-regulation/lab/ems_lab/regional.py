# @AI_GENERATED
"""跨省调度细则参数适配

对应章节：05 跨区调度细则适配

教学示例默认值（对齐 05.2 手算）：
  江苏：死区±0.5 kV, 合格范围±0.5 kV, 采样1min, 含正含负
  山西：死区±0.7 kV, 合格范围±0.7 kV, 电压中枢点, 含正含负, 无功+能量可用率
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class RegionalRule:
    province: str
    voltage_deadband_kv: float
    voltage_band_kv: float
    sample_interval_s: int
    measure_point: str
    score_weights: tuple
    include_positive_q: bool
    include_negative_q: bool
    include_reactive_energy: bool = False
    include_availability: bool = True


RULES = {
    "江苏": RegionalRule(
        province="江苏",
        voltage_deadband_kv=0.5,
        voltage_band_kv=0.5,
        sample_interval_s=60,
        measure_point="PCC 并网点",
        score_weights=(0.5, 0.3, 0.2),
        include_positive_q=True,
        include_negative_q=True,
    ),
    "山西": RegionalRule(
        province="山西",
        voltage_deadband_kv=0.7,
        voltage_band_kv=0.7,
        sample_interval_s=60,
        measure_point="电压中枢点",
        score_weights=(0.5, 0.3, 0.2),
        include_positive_q=True,
        include_negative_q=True,
        include_reactive_energy=True,
    ),
}


def get_rule(province: str) -> RegionalRule:
    return RULES.get(province, RULES["江苏"])
# @AI_GENERATED: end