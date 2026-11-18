# @AI_GENERATED
"""ch04 示例：可行调度域与 SOC 递推（对齐正文 §04.2/04.3/04.4）

主线场景：E_nom=100MWh，SOC 10%~90%，P_nom=50MW，dt=1h
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lab.ems_lab.feasibility import available_energy, feasible_p
from lab.ems_lab.energy_flow import step_soc


def main():
    print("可行调度域  [主线: E=100MWh, SOC 10%~90%, P=50MW]\n")

    print("=== 可用能量（正文 §04.2） ===")
    for soc in (0.90, 0.50, 0.10):
        e_dis, e_chg = available_energy(soc)
        print(f"  SOC={soc:>4}: 可放 {e_dis:>4} MWh，可充 {e_chg:>4} MWh")

    print("\n=== 可行功率（正文 §04.3） ===")
    for soc in (0.90, 0.50, 0.10):
        p_dis, p_chg = feasible_p(soc, 1.0)
        print(f"  SOC={soc:>4}: 放电上限 {p_dis:>6.2f} MW，充电上限 {p_chg:>6.2f} MW")

    print("\n=== 单步 SOC 递推（正文 §04.4） ===")
    print(f"  充 50MW×1h: {step_soc(0.10, -50.0, 1.0):.4f}  (0.10+0.475)")
    print(f"  放 50MW×1h: {step_soc(0.90,  50.0, 1.0):.4f}  (0.90-0.5263)")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end