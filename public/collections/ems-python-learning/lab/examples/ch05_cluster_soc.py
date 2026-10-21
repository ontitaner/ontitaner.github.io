"""第 05 章 5.8 最小闭环：用 ems_lab 的聚合函数重跑簇间 SOC 的例子。

输入：4 簇 SOC 60%、58%、55%、45%，每簇 400 kWh，下限 5%
算法：aggregate_soc 四种取法 + stack_energy（木桶效应）
输出：按平均和按最低簇的可放电量

运行（在 lab 目录下）：
    python examples/ch05_cluster_soc.py
"""
import sys
from pathlib import Path

# 直接运行脚本时 Python 只把 examples/ 放进搜索路径，这里补上 lab/ 以便导入 ems_lab
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.battery import aggregate_soc, stack_energy  # noqa: E402

SOCS = [0.60, 0.58, 0.55, 0.45]


def main():
    for m in ("mean", "min", "max"):
        print(f"{m:<8}{aggregate_soc(SOCS, m):.1%}")
    w = aggregate_soc(SOCS, "weighted", [400, 400, 400, 320])
    print(f"{'weighted':<8}{w:.1%}")
    by_mean = 4 * 400 * (aggregate_soc(SOCS) - 0.05)
    st = stack_energy(SOCS, 400, 0.05, 0.95)
    print(f"按平均估可放 {by_mean:.0f} kWh，木桶效应下实际可放 {st.dischargeable_kwh:.0f} kWh")
    assert abs(w - 0.55) < 1e-9
    assert abs(st.dischargeable_kwh - 640) < 1e-6 and abs(by_mean - st.dischargeable_kwh - 152) < 1e-6
    print("自检通过")

if __name__ == "__main__":
    main()

