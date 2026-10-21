"""第 05 章 5.12 最小闭环：用 ems_lab.battery.dischargeable_energy_kwh 重跑 5.1 场景复盘。

输入：显示 SOC 30%，漂移 −6 点、效率 0.931、最低簇再低 2 点
算法：逐项修正后按 (SOC − 下限) × 容量 × 效率 计算可放电量
输出：每一步的可放电量和可放时长

运行（在 lab 目录下）：
    python examples/ch05_scenario_recap.py
"""
import sys
from pathlib import Path

# 直接运行脚本时 Python 只把 examples/ 放进搜索路径，这里补上 lab/ 以便导入 ems_lab
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.battery import dischargeable_energy_kwh  # noqa: E402

CAP_KWH, SOC_MIN, P_KW = 2000.0, 0.10, 1000.0


def main():
    steps = [("EMS 的估算", 0.30, 1.0), ("① 修正漂移", 0.24, 1.0),
             ("② 再乘效率", 0.24, 0.931), ("③ 再看最低簇", 0.22, 0.931)]
    minutes = []
    for name, soc, eta in steps:
        e = dischargeable_energy_kwh(soc, CAP_KWH, SOC_MIN, eta)
        minutes.append(e / P_KW * 60)
        print(f"{name:<8}{e:7.1f} kWh → {minutes[-1]:4.1f} min")
    assert [round(m, 1) for m in minutes] == [24.0, 16.8, 15.6, 13.4]
    print("自检通过")

if __name__ == "__main__":
    main()

