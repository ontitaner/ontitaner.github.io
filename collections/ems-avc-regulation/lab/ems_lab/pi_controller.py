# @AI_GENERATED
"""PI 控制器（离散形式，带抗积分饱和与输出限幅）

对应章节：01 AVC控制模式与选型（定电压 PI 手算）、02 AVC核心参数与整定（Kp/Ki 整定）

教学示例默认值（对齐附录 B 与 01.6/02.4 手算，均为 pu 体系）：
  Kp=8000 kvar/pu, Ki=2000 kvar/(pu·s), Ts=4 s
  Q 输出限幅 out_max=+500 kvar / out_min=−500 kvar
  积分限幅 i_max=±300 kvar（独立于输出限幅，见 01.6 逐拍追踪）
"""
from __future__ import annotations


class PIController:
    def __init__(
        self,
        kp: float = 8000.0,
        ki: float = 2000.0,
        out_max: float = 500.0,
        out_min: float = -500.0,
        i_max: float | None = None,
        ts: float = 4.0,
    ):
        self.kp = kp
        self.ki = ki
        self.out_max = out_max
        self.out_min = out_min
        # 积分限幅：默认等于输出限幅，调用方可显式传 i_max（正文 01.6 取 ±300 kvar）
        self.i_max = out_max if i_max is None else i_max
        self.ts = ts
        self._integral: float = 0.0
        self._last_output: float = 0.0

    def step(self, error: float) -> float:
        """单拍 PI 迭代。

        error = U_target − U_pcc（电压偏低为正、偏高为负，与附录 B 的 ΔU 互为相反数）。
        返回 Q 指令值（已限幅到 [out_min, out_max]）。
        """
        self._integral += self.ki * error * self.ts
        if self._integral > self.i_max:
            self._integral = self.i_max
        elif self._integral < -self.i_max:
            self._integral = -self.i_max

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