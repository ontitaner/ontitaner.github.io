"""第 12 章最小闭环：多个约束→交集→请求投影→原因。

输入：BMS/PCS、SOC、防倒送、进口上限和请求
算法：构造区间→求交集→project 投影
输出：最终功率、可行域、绑定约束
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.constraints import device_interval, export_limit_interval, import_limit_interval, project, soc_interval  # noqa: E402


def main():
    constraints = [
        device_interval(500, 800),
        soc_interval(0.50, 1000),
        export_limit_interval(600, 400, 0, 30, 10),
        import_limit_interval(600, 400, 1800, 30, 10),
    ]
    result = project(800, constraints)
    print(f"可行域：[{result.lower_kw:.0f}, {result.upper_kw:.0f}] kW")
    print(f"请求：800 kW → 最终：{result.final_kw:.0f} kW")
    print(f"绑定：{result.binding}，未满足：{800 - result.final_kw:.0f} kW")
    assert result.final_kw == 240
    assert result.lower_kw == -500 and result.upper_kw == 240
    assert result.final_kw == 240 and result.binding == "防倒送"
    print("自检通过")


if __name__ == "__main__":
    main()

