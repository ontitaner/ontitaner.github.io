# @AI_GENERATED
"""ch06 示例：日内滚动修正与 MAPE（对齐正文 §06.2/06.3）

主线场景：预测价 [谷350, 平700, 峰1200]，实际 [350, 1300, 1200]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lab.ems_lab.rolling import arbitrage_profit, fixed_plan_profit, mape


def main():
    print("日内滚动修正  [主线: 平段700→1300 涨过峰段]\n")

    forecast = [350.0, 700.0, 1200.0]
    actual = [350.0, 1300.0, 1200.0]

    fixed = fixed_plan_profit(forecast, actual)
    ideal = arbitrage_profit(actual)
    print("=== 固定计划 vs 理想重排（正文 §06.2） ===")
    print(f"  固定计划收益(谷充→峰放) = {fixed:.2f} 元")
    print(f"  理想重排收益(谷充→平放) = {ideal:.2f} 元")
    print(f"  改善 = {ideal - fixed:.2f} 元\n")

    print("=== MAPE（正文 §06.3） ===")
    print(f"  本场景 MAPE = {mape(forecast, actual):.2f}%")
    print(f"  示例 MAPE   = {mape([100.0, 200.0], [110.0, 180.0]):.2f}%")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end