# @AI_GENERATED
"""ch03 示例：光伏功率平滑与储能补偿（对齐正文 §03.2/03.3/03.4）

主线场景：光伏峰值 30 MW，半正弦 6:00–18:00
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lab.ems_lab.solar import pv_curve, moving_average, bess_for_smoothing, track_error


def main():
    print("光储协同：光伏曲线 + 功率平滑  [主线: 峰值30MW]\n")

    print("=== 半正弦曲线（正文 §03.2） ===")
    for t in (6.0, 9.0, 12.0, 20.0):
        print(f"  pv_curve({t:>4}) = {pv_curve(t):.2f} MW")

    print("\n=== 滑动平均与储能补偿（正文 §03.3） ===")
    series = [1, 2, 3, 4, 5]
    smooth = moving_average(series, 3)
    bess = bess_for_smoothing(series, 3)
    print(f"  原序列   = {series}")
    print(f"  平滑序列 = {smooth}")
    print(f"  储能补偿 = {bess}  (+放电/-充电)")

    print("\n=== 跟踪误差（正文 §03.4） ===")
    err = track_error([100.0, 100.0], [98.0, 103.0])
    print(f"  track_error = {err}  (实际-计划)")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end