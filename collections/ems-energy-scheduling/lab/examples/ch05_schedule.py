# @AI_GENERATED
"""ch05 示例：日前排程（一充一放 vs 两充两放，对齐正文 §05.2）

主线场景：谷0.35/平0.70/峰1.20 元/kWh，可用能量 80MWh
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lab.ems_lab.schedule import one_cycle, two_cycle


def main():
    print("日前优化排程  [主线: 谷0.35/平0.70/峰1.20]\n")

    one = one_cycle(80.0)
    print("=== 一充一放（正文 §05.2） ===")
    print(f"  谷充峰放收益 = {one['profit']:.2f} 元\n")

    two = two_cycle(80.0)
    print("=== 两充两放（正文 §05.2） ===")
    print(f"  第一段(谷充峰放)收益 = {two['first']['profit']:.2f} 元")
    print(f"  第二段(平充峰放)收益 = {two['second']['profit']:.2f} 元")
    print(f"  合计收益 = {two['profit']:.2f} 元")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end