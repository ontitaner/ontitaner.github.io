# @AI_GENERATED
"""PI 控制器（离散形式，带抗积分饱和与输出限幅）

对应章节：02 AVC核心参数与整定（Kp/Ki 整定），03 多资源分配，08 联调 PI 验证

教学示例默认值（对齐 02.3 手算）：
  Kp=8, Ki=0.3, out_max=+15000 kvar, out_min=−15000 kvar
"""
from __future__ import annotations


class PIController:
    def __init__(
        self,
        kp: float,
        ki: float,
        out_max: float = 15000.0,
        out_min: float = -15000.0,
        ts: float = 4.0,
    ):
        self.kp = kp
        self.ki = ki
        self.out_max = out_max
        self.out_min = out_min
        self.ts = ts
        self._integral: float = 0.0
        self._last_output: float = 0.0

    def step(self, error: float) -> float:
        self._integral += self.ki * error * self.ts
        if self._integral > self.out_max:
            self._integral = self.out_max
        elif self._integral < self.out_min:
            self._integral = self.out_min

        raw = self.kp * error + self._integral
        if raw > self.out_max:
            raw = self.out_max
        elif raw < self.out_min:
            raw = self.out_min

        self._last_output = raw
        return raw

    @property
    def integral(self) -> float:
        return self._integral

    @property
    def last_output(self) -> float:
        return self._last_output

    def reset(self):
        self._integral = 0.0
        self._last_output = 0.0
# @AI_GENERATED: end