"""第 11 章 11.4 示例：用 lab 的真实实现重跑“调度改设点、中途 BMS 降额”的逐拍表。

输入：改设点前下发 −200 kW；第 1 拍起设点 +600 kW；Ramp 200 kW/s；周期 1 s；
      BMS 可放能力第 4 拍降到 100 kW、第 5 拍恢复 1000 kW；可充能力 1000 kW
算法：RateLimiter（Ramp）+ limit_then_ramp（限幅 → Ramp → 兜底 → reset 同步）
输出：每拍下发值，与正文逐拍表逐行一致

运行（在 lab 目录下）：
    python examples/ch11_ramp_example.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.control import RateLimiter, limit_then_ramp  # noqa: E402

RATE_KW_S = 200.0
DT_S = 1.0
P_CHARGE_MAX_KW = 1000.0
P0_KW = -200.0
REQUESTS_KW = [600.0] * 8
DIS_MAX_KW = [1000.0, 1000.0, 1000.0, 100.0, 1000.0, 1000.0, 1000.0, 1000.0]
EXPECTED_KW = [0, 200, 400, 100, 300, 500, 600, 600]


def run_trace():
    """逐拍调用真实实现；RateLimiter.output 就是正文里的 P_prev。"""
    ramp = RateLimiter(up_rate=RATE_KW_S, down_rate=RATE_KW_S, initial=P0_KW)
    rows = []
    for req, cap in zip(REQUESTS_KW, DIS_MAX_KW):
        prev = ramp.output
        out = limit_then_ramp(req, ramp, DT_S, P_CHARGE_MAX_KW, cap)
        rows.append((prev, cap, out, out - prev))
    return rows


def main():
    rows = run_trace()
    print("拍  上一拍  可放上限  下发  变化量")
    for k, (prev, cap, out, delta) in enumerate(rows, start=1):
        print(f"{k:>2}  {prev:>6.0f}  {cap:>6.0f}  {out:>4.0f}  {delta:>+6.0f}")
    assert [r[2] for r in rows] == EXPECTED_KW
    # 主动变化不超过 r×dt；只有第 4 拍（安全收缩）允许超过
    assert all(abs(r[3]) <= RATE_KW_S * DT_S for k, r in enumerate(rows, start=1) if k != 4)
    assert rows[3][3] == -300
    print("自检通过")


if __name__ == "__main__":
    main()

