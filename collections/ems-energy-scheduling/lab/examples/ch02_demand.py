# @AI_GENERATED
"""ch02 示例：需量削峰（对齐正文 §02.2/02.3）

主线场景：日负荷峰值 7.0 MW，目标需量 5.0 MW，BESS 放电上限 2.0 MW
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lab.ems_lab.demand import peak_demand, demand_charge, shave, shaved_peak


def main():
    print("需量削峰  [主线: 峰值7MW→目标5MW，BESS 2MW]\n")

    load = [3.0, 5.0, 7.0, 6.0]
    print("=== 需量电费（正文 §02.2） ===")
    peak = peak_demand(load)
    print(f"  最大需量 = {peak} MW")
    print(f"  需量电费 = {demand_charge(peak, 40.0):,.0f} 元/月\n")

    print("=== 削峰（正文 §02.3） ===")
    bess = shave(load, 2.0, 5.0)
    new_peak = shaved_peak(load, bess)
    print(f"  BESS 放电序列 = {bess}")
    print(f"  削峰后最大需量 = {new_peak} MW")
    print(f"  削峰后电费 = {demand_charge(new_peak, 40.0):,.0f} 元/月")
    print(f"  月节省 = {demand_charge(peak, 40.0) - demand_charge(new_peak, 40.0):,.0f} 元")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end