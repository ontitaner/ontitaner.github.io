# @AI_GENERATED
"""死区与滞回控制器（pu 体系）

对应章节：02 AVC核心参数与整定（死区宽度），04 考核指标（合格范围 vs 死区）

教学示例默认值（对齐附录 B 与 02.3 手算，均为 pu 体系）：
  连续死区：center=1.000 pu, half_width=0.010 pu
            |ΔU|>db 后按 (|ΔU|−db) 线性过渡，边界处连续归零，无功率跳变
  滞回死区：outer_half_width=0.010 pu, return_ratio=0.6
            进入阈 = center ± 0.010 pu，退出阈 = center ± 0.006 pu

符号约定（附录 B）：ΔU = U − U_target，正=偏高需吸收 Q（负），负=偏低需发出 Q（正）。
"""
from __future__ import annotations


class Deadband:
    """连续型死区：死区外返回减去半宽后的偏差，边界处连续归零，无功率跳变。"""

    def __init__(self, center: float = 1.0, half_width: float = 0.010):
        self.center = center
        self.half_width = half_width

    def apply(self, value: float) -> float:
        """返回死区处理后的偏差：value 相对 center 超出 half_width 的部分。"""
        upper = self.center + self.half_width
        lower = self.center - self.half_width
        if value > upper:
            return value - upper
        if value < lower:
            return value - lower
        return 0.0

    def in_deadband(self, value: float) -> bool:
        return abs(value - self.center) <= self.half_width


class HysteresisDeadband:
    """滞回死区：进入阈 outer_half_width，退出阈 outer_half_width × return_ratio。"""

    def __init__(self, center: float = 1.0, outer_half_width: float = 0.010,
                 return_ratio: float = 0.6):
        self.center = center
        self.outer_half_width = outer_half_width
        self.return_ratio = return_ratio
        self._inside = True
        self._upper_on = center + outer_half_width
        self._upper_off = center + outer_half_width * return_ratio
        self._lower_on = center - outer_half_width
        self._lower_off = center - outer_half_width * return_ratio

    @property
    def state(self) -> str:
        return "inside" if self._inside else "outside"

    def apply(self, value: float) -> float:
        if self._inside:
            if value > self._upper_on:
                self._inside = False
                return value - self._upper_on
            if value < self._lower_on:
                self._inside = False
                return value - self._lower_on
            return 0.0
        if self._lower_off <= value <= self._upper_off:
            self._inside = True
            return 0.0
        if value > self._upper_off:
            return value - self._upper_off
        return value - self._lower_off
# @AI_GENERATED: end