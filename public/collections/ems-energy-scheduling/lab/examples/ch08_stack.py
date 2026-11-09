# @AI_GENERATED
"""ch08 示例：辅助服务叠加的容量分配（对齐正文 §08.2）

主线场景：P_nom=50MW，PFR 备用 10MW，调压 5MW
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lab.ems_lab.stack import capacity_split


def main():
    print("辅助服务叠加  [主线: P_nom=50MW]\n")

    print("=== 容量切分（正文 §08.2） ===")
    for pfr, volt in ((0.0, 0.0), (10.0, 0.0), (10.0, 5.0)):
        r = capacity_split(50.0, pfr, volt)
        print(f"  PFR={pfr:>4}, 调压={volt:>4} → "
              f"PFR {r['pfr']:>4} MW + 调压 {r['volt']:>4} MW + 套利 {r['arbitrage']:>4} MW")

    print("\n=== 超额需求（正文 §08 自测4） ===")
    r = capacity_split(50.0, 60.0, 0.0)
    print(f"  PFR 需求 60MW → {r}")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end