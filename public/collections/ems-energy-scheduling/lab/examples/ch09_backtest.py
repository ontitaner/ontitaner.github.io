# @AI_GENERATED
"""ch09 示例：收益复盘与偏差归因（对齐正文 §09.2/09.3）

主线场景：计划利润 61726，电价误差 −11800，能量不足 −3400 → 实际 46526
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lab.ems_lab.backtest import net_profit, attribution


def main():
    print("经济性后评估  [主线: 计划61726 → 实际46526]\n")

    print("=== 净收益（正文 §09.2） ===")
    net = net_profit(91200.0, 29474.0, 5000.0)
    print(f"  收入91200 - 成本29474 - 退化5000 = {net:.2f} 元\n")

    print("=== 偏差归因（正文 §09.3） ===")
    r = attribution(61726.0, 46526.0, {"price": -11800.0, "energy": -3400.0})
    print(f"  总偏差 gap     = {r['gap']:.0f} 元")
    print(f"  已解释 explained = {r['explained']:.0f} 元")
    print(f"  残差 residual   = {r['residual']:.0f} 元")
    print(f"  归因闭合 check  = {r['check']}")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end