# @AI_GENERATED
"""分时电价表与时段查询

对应章节：01 峰谷套利

教学示例默认值（对齐 01.2 / 附录B）：
  谷 0.35 / 平 0.70 / 峰 1.20 元/kWh
"""
from __future__ import annotations

# 24 小时电价（元/kWh），索引 0~23
PRICES = [0.35] * 8 + [0.70] * 2 + [1.20] * 2 + [0.70] * 5 + [1.20] * 4 + [0.70] * 2 + [0.35]

# 分段：[start_hour, end_hour, 时段名, 电价（元/kWh）]
PERIODS = [
    (0, 8, "valley", 0.35),
    (8, 10, "flat", 0.70),
    (10, 12, "peak", 1.20),
    (12, 17, "flat", 0.70),
    (17, 21, "peak", 1.20),
    (21, 23, "flat", 0.70),
    (23, 24, "valley", 0.35),
]


def price_at(hour: float) -> float:
    """返回某时刻（0~24 小时，可为小数）的电价（元/kWh）。"""
    return PRICES[int(hour) % 24]


def period_at(hour: float) -> str:
    """返回某时刻所属时段名：valley / flat / peak。"""
    p = price_at(hour)
    if p == 0.35:
        return "valley"
    if p == 0.70:
        return "flat"
    return "peak"


def valley_hours() -> list:
    """返回谷段小时列表 [0,1,...,7,23]。"""
    hours = []
    for start, end, name, _ in PERIODS:
        if name == "valley":
            hours.extend(range(start, end))
    return sorted(set(h % 24 for h in hours))


def peak_hours() -> list:
    """返回峰段小时列表 [10,11,17,18,19,20]。"""
    hours = []
    for start, end, name, _ in PERIODS:
        if name == "peak":
            hours.extend(range(start, end))
    return sorted(set(h % 24 for h in hours))
# @AI_GENERATED: end