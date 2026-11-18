# @AI_GENERATED
"""ch01 示例：分时电价查询 + 一充一放收益（对齐正文 §01.3）

主线场景：50MW/100MWh 储能电站，谷充 80MWh → 峰放 76MWh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lab.ems_lab.tariff import price_at, period_at, valley_hours, peak_hours
from lab.ems_lab.schedule import one_cycle


def main():
    print("分时电价 + 一充一放套利  [主线: 谷0.35/平0.70/峰1.20 元/kWh]\n")

    print("=== 时段查询 ===")
    print(f"  10:00 电价 = {price_at(10):.2f} 元/kWh，时段 = {period_at(10)}")
    print(f"  03:00 电价 = {price_at(3):.2f} 元/kWh，时段 = {period_at(3)}")
    print(f"  谷段小时 = {valley_hours()}")
    print(f"  峰段小时 = {peak_hours()}\n")

    r = one_cycle(80.0)
    print("=== 一充一放收益（正文 §01.3 手算对照） ===")
    print(f"  电网吸收 e_grid = {r['e_grid']:.2f} MWh  (80/0.95)")
    print(f"  并网输出 e_out  = {r['e_out']:.2f} MWh  (80×0.95)")
    print(f"  充电成本 cost   = {r['cost']:.2f} 元    (84.21×350)")
    print(f"  放电收入 revenue= {r['revenue']:.2f} 元    (76×1200)")
    print(f"  净收益 profit   = {r['profit']:.2f} 元")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end