# @AI_GENERATED
"""死区与滞回控制器

对应章节：02 AVC核心参数与整定（死区宽度），04 考核指标（合格范围 vs 死区）

教学示例默认值（对齐 02.2 / 04.3）：
  死区：center=116.0 kV, half_width=0.5 kV
  滞回：return_ratio=0.6（返回阈 = center + half_width × return_ratio）
"""
from __future__ import annotations


class Deadband:
    def __init__(self, center: float, half_width: float):
        self.center = center
        self.half_width = half_width
        self._inside = True

    def apply(self, value: float) -> float:
        upper = self.center + self.half_width
        lower = self.center - self.half_width
        if value > upper:
            return value - upper
        elif value < lower:
            return value - lower
        return 0.0

    def in_deadband(self, value: float) -> bool:
        return abs(value - self.center) <= self.half_width


class Hysteresis:
    def __init__(self, center: float, half_width: float, return_ratio: float = 0.6):
        self.center = center
        self.half_width = half_width
        self.return_ratio = return_ratio
        self._inside = True
        self._upper_on = center + half_width
        self._upper_off = center + half_width * return_ratio
        self._lower_on = center - half_width
        self._lower_off = center - half_width * return_ratio

    def apply(self, value: float) -> float:
        if self._inside and value > self._upper_on:
            self._inside = False
            return value - self._upper_on
        if self._inside and value < self._lower_on:
            self._inside = False
            return value - self._lower_on
        if not self._inside and self._lower_off <= value <= self._upper_off:
            self._inside = True
            return 0.0
        if self._inside:
            return 0.0
        if value > self._upper_off:
            return value - self._upper_off
        return value - self._lower_off
# @AI_GENERATED: end