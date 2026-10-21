"""第 05 章 5.10 最小闭环：用 ems_lab 的 SOP 函数重跑不同持续时长的可承诺功率。

输入：瞬时可放 2450 kW，SOC 20% 时可放电量
算法：sop_for_duration = min(P_瞬时, E / T)
输出：各持续时长的可承诺功率

运行（在 lab 目录下）：
    python examples/ch05_sop_duration.py
"""
import sys
from pathlib import Path

# 直接运行脚本时 Python 只把 examples/ 放进搜索路径，这里补上 lab/ 以便导入 ems_lab
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.battery import actual_capacity_kwh, dischargeable_energy_kwh, sop_for_duration  # noqa: E402

P_INSTANT_KW = 2450.0


def main():
    e = dischargeable_energy_kwh(0.20, actual_capacity_kwh(5016, 0.92), 0.05, 0.931)
    print(f"可放电量 {e:.2f} kWh，拐点 T* = {e / P_INSTANT_KW * 60:.1f} min")
    got = []
    for minutes in (5, 15, 30, 60, 120):
        p = sop_for_duration(P_INSTANT_KW, e, minutes * 60)   # 真实函数的时长单位是秒
        got.append(p)
        print(f"持续 {minutes:>3} min：{p:7.1f} kW")
    assert got[:2] == [2450.0, 2450.0] and abs(got[2] - 1288.89) < 0.01
    print("自检通过")

if __name__ == "__main__":
    main()

