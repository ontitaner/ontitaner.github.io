# @AI_GENERATED
"""ch07 示例：现货市场报价决策（对齐正文 §07.3）

主线场景：放电成本 450 元/MWh，预测 LMP 600 元/MWh，margin 10%
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lab.ems_lab.spot import should_discharge, bid_price


def main():
    print("现货市场报价  [主线: 成本450, 预测LMP600, margin10%]\n")

    print("=== 放电决策（正文 §07.2） ===")
    print(f"  LMP=600 > 450? {should_discharge(600.0, 450.0)}")
    print(f"  LMP=400 > 450? {should_discharge(400.0, 450.0)}\n")

    print("=== 报价（正文 §07.3） ===")
    print(f"  预测600, margin10% → 报价 = {bid_price(450.0, 600.0, 0.1):.0f} 元/MWh")
    print(f"  预测400, margin10% → 报价 = {bid_price(450.0, 400.0, 0.1):.0f} 元/MWh")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end