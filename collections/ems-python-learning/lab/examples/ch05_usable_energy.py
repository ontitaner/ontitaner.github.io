"""第 05 章 5.6 最小闭环：用 ems_lab 的能量函数重跑“能量瀑布”。

输入：额定 5016 kWh、SOH 92%、SOC 50%、窗口 5%～95%、效率 0.931
算法：actual_capacity_kwh → dischargeable_energy_kwh / chargeable_energy_kwh
输出：交流侧可放、可充电量

运行（在 lab 目录下）：
    python examples/ch05_usable_energy.py
"""
import sys
from pathlib import Path

# 直接运行脚本时 Python 只把 examples/ 放进搜索路径，这里补上 lab/ 以便导入 ems_lab
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.battery import actual_capacity_kwh, chargeable_energy_kwh, dischargeable_energy_kwh  # noqa: E402

ETA = 0.95 * 0.98


def main():
    cap = actual_capacity_kwh(5016, 0.92)                    # ① 当前实际容量
    e_dis = dischargeable_energy_kwh(0.50, cap, 0.05, ETA)   # ② ③ 可放（放电乘效率）
    e_chg = chargeable_energy_kwh(0.50, cap, 0.95, ETA)      # ④ 可充（充电除效率）
    print(f"当前实际容量 {cap:.2f} kWh，可放 {e_dis:.2f} kWh，可充 {e_chg:.2f} kWh")
    assert abs(e_dis - 1933.34) < 0.01 and abs(e_chg - 2230.53) < 0.01
    assert dischargeable_energy_kwh(0.04, cap, 0.05) == 0.0  # 已低于下限：0 而不是负数
    print("自检通过")

if __name__ == "__main__":
    main()

