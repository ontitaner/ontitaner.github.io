"""第 11 章各节示例：用 lab 的真实实现重算正文的逐项/逐拍表（11.4 Ramp 见 ch11_ramp_example.py）。

输入：各节“已知条件”表中的数值（[教学示例]）
算法：clamp_power、deadband_cut/deadband_shift、Hysteresis、LowPassFilter、interp_table、
      PIController（条件积分），以及本文件中的 ModeMachine（11.8 状态机的类写法）
输出：每节的结果，与正文表格逐行一致（assert 自检）

运行（在 lab 目录下）：
    python examples/ch11_control_examples.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.control import (  # noqa: E402
    Hysteresis,
    LowPassFilter,
    PIController,
    clamp_power,
    deadband_cut,
    deadband_shift,
    interp_table,
)


# ---------------------------------------------------------------- 11.1 clamp
def clamp_example():
    """可充 500 kW、可放 800 kW，三个请求的 (请求, 输出, 截掉)。"""
    return [(req, clamp_power(req, 500.0, 800.0), req - clamp_power(req, 500.0, 800.0))
            for req in (1000.0, -700.0, 300.0)]


# ---------------------------------------------------------------- 11.2 死区
def deadband_example(width=0.03, k=1000.0):
    """四次频率测量的 (频率, 截断型 ΔP, 连续型 ΔP)，ΔP = −K × 有效偏差。"""
    rows = []
    for f in (50.02, 49.96, 49.90, 50.05):
        df = round(f - 50.0, 4)
        rows.append((f, round(-k * deadband_cut(df, width), 6) + 0.0,
                     round(-k * deadband_shift(df, width), 6) + 0.0))
    return rows


# ---------------------------------------------------------------- 11.3 滞回
HY_SOC = [18, 16, 14.8, 16.5, 19, 23, 25.3, 24, 20]


def hysteresis_example():
    """低 SOC 自充：低于 15% 开启、高于 25% 停止，返回每 10 min 的开关状态。"""
    h = Hysteresis(on_below=15.0, off_above=25.0)
    return [h.update(v) for v in HY_SOC]


# ---------------------------------------------------------------- 11.5 低通
def lowpass_example():
    """τ = 1 s、dt = 0.2 s，第 1 拍起 50.00 → 49.90 Hz，返回第 0～10 拍输出。"""
    f = LowPassFilter(1.0)
    return [f.update(50.0, 0.2)] + [f.update(49.9, 0.2) for _ in range(10)]


# ---------------------------------------------------------------- 11.6 查表插值
TEMPS = [-10, 0, 10, 30, 45, 55]
RATIOS = [0.0, 0.3, 1.0, 1.0, 0.5, 0.0]


def interp_example(p_rated=1000.0):
    """放电温度降额表：返回 (温度, 允许比例, 允许放电 kW)。"""
    return [(t, interp_table(t, TEMPS, RATIOS), p_rated * interp_table(t, TEMPS, RATIOS))
            for t in (5, 38, 50, 60)]


# ---------------------------------------------------------------- 11.7 PI
def pi_example(rest_kw, u_min, u_max=1000.0, kp=0.2, ki=0.4, dt=1.0):
    """防倒送闭环：P_PCC[k] = P_rest[k] + u[k−1]，目标 0 kW。返回每拍 (P_PCC, u, 积分, 是否顶住)。"""
    pi = PIController(kp, ki, u_min, u_max, anti_windup=True)
    u, rows = 0.0, []
    for rest in rest_kw:
        p_pcc = rest + u
        u = pi.update(0.0 - p_pcc, dt)
        rows.append((p_pcc, u, pi.integral, pi.saturated))
    return rows


# ---------------------------------------------------------------- 11.8 状态机
class ModeMachine:
    """待机 / 运行 / 降额 / 故障 四状态机（11.8 正文代码的类写法）。

    - 保护动作：任一状态 → 故障；故障只有在保护消失且人工复归后才回到待机；
    - 降额 → 运行：能力恢复（可放 ≥ 指令）需连续保持 hold_s 秒；
    - 每个状态的默认输出：待机 0、故障 0、运行 = 指令、降额 = min(指令, 可放能力)。
    """

    def __init__(self, hold_s: float = 3.0, initial: str = "待机"):
        self.hold_s = hold_s
        self.state = initial      # 重启时应按设备实际状态传入
        self.ok_s = 0.0           # 降额状态下能力恢复已连续保持的时间
        self.reason = ""

    def update(self, cmd_kw: float, cap_kw: float, fault: bool, ack: bool, dt: float = 1.0) -> float:
        s, why = self.state, "保持"
        if fault:
            s, why = "故障", "保护动作"
        elif s == "故障":
            s, why = ("待机", "保护已消失且人工复归") if ack else ("故障", "未复归，拒绝指令")
        elif s == "待机":
            if cmd_kw != 0:
                s, why = ("降额", "能力不足") if cap_kw < cmd_kw else ("运行", "收到有效指令")
            else:
                why = "指令为 0"
        elif s == "运行":
            if cmd_kw == 0:
                s, why = "待机", "指令为 0"
            elif cap_kw < cmd_kw:
                s, why = "降额", "能力下降"
        elif s == "降额":
            self.ok_s = self.ok_s + dt if cap_kw >= cmd_kw else 0.0
            if cmd_kw == 0:
                s, why = "待机", "指令为 0"
            elif self.ok_s >= self.hold_s:
                s, why = "运行", f"能力恢复已持续 {self.hold_s:g} s"
            else:
                why = f"能力恢复计时 {self.ok_s:g} s" if self.ok_s else "能力仍不足"
        if s != "降额":
            self.ok_s = 0.0
        self.state, self.reason = s, why
        return {"待机": 0.0, "故障": 0.0, "运行": cmd_kw, "降额": min(cmd_kw, cap_kw)}[s]


SM_INPUTS = [(0, 1000, False, False), (500, 1000, False, False), (500, 300, False, False),
             (500, 1000, False, False), (500, 1000, False, False), (500, 1000, False, False),
             (500, 1000, True, False), (500, 1000, False, False), (500, 1000, False, True),
             (500, 1000, False, False)]


def state_machine_example():
    """11.8 示例：返回每秒 (状态, 下发值, 原因)。"""
    m = ModeMachine(hold_s=3.0)
    rows = []
    for cmd, cap, fault, ack in SM_INPUTS:
        out = m.update(cmd, cap, fault, ack)
        rows.append((m.state, out, m.reason))
    return rows


def main():
    assert [(r[1], r[2]) for r in clamp_example()] == [(800, 200), (-500, -200), (300, 0)]
    assert [(r[1], r[2]) for r in deadband_example()] == [(0, 0), (40, 10), (100, 70), (-50, -20)]
    assert hysteresis_example() == [False, False, True, True, True, True, False, False, False]
    ys = lowpass_example()
    assert [round(ys[k], 4) for k in (1, 5, 10)] == [49.9833, 49.9402, 49.9162]
    assert [round(r[2], 1) for r in interp_example()] == [650.0, 733.3, 250.0, 0.0]
    a = pi_example([300.0] * 10, u_min=-1000.0)
    assert (round(a[-1][0], 1), round(a[-1][1], 1)) == (7.5, -294.8)
    b = pi_example([600.0] * 5 + [100.0] * 7, u_min=-400.0)
    assert [r[1] for r in b[2:5]] == [-400.0] * 3 and all(r[3] for r in b[2:5])
    assert [round(r[2], 1) for r in b[2:5]] == [-336.0] * 3
    assert (round(b[5][0], 1), round(b[5][1], 1)) == (-300.0, -156.0)
    sm = state_machine_example()
    assert [(s, o) for s, o, _ in sm] == [("待机", 0), ("运行", 500), ("降额", 300), ("降额", 500),
                                          ("降额", 500), ("运行", 500), ("故障", 0), ("故障", 0),
                                          ("待机", 0), ("运行", 500)]
    for t, (s, o, why) in enumerate(sm):
        print(f"t{t}  {s}  {o:>5.0f} kW  {why}")
    print("自检通过")


if __name__ == "__main__":
    main()

