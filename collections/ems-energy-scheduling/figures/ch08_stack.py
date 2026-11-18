# @AI_GENERATED
"""第 08 章配图：辅助服务叠加的容量分配。

参数对齐章节 08.2：[教学示例]
- P_nom=50 MW，仅套利：套利 50
- 叠加调频：PFR 10 + 套利 40
- 再叠加调压：PFR 10 + 调压 5 + 套利 35
"""
from __future__ import annotations

from _style import C_DIS, C_CHG, C_SOC, C_GRID, save, plt


def fig_stack():
    scenarios = ["仅套利", "套利+调频", "套利+调频+调压"]
    pfr = [0, 10, 10]
    volt = [0, 0, 5]
    arb = [50, 40, 35]

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    x = range(3)
    ax.bar(x, arb, color=C_DIS, width=0.5, label="套利")
    ax.bar(x, pfr, bottom=arb, color=C_CHG, width=0.5, label="一次调频 PFR")
    ax.bar(x, volt, bottom=[a + p for a, p in zip(arb, pfr)], color=C_SOC, width=0.5, label="调压")

    for i in x:
        total = arb[i] + pfr[i] + volt[i]
        ax.text(i, total + 0.8, f"{total} MW", ha="center", fontsize=11, fontweight="bold")
        ax.text(i, arb[i] / 2, f"{arb[i]}", ha="center", color="white",
                fontsize=10, fontweight="bold")

    ax.set_xticks(list(x))
    ax.set_xticklabels(scenarios)
    ax.set_ylabel("容量 (MW)")
    ax.set_ylim(0, 58)
    ax.legend(fontsize=8.5, loc="upper right")
    ax.set_title("容量叠加：50 MW 在套利与辅助服务间的分配  [教学示例]")
    save(fig, "ch08_stack")


def main():
    fig_stack()
    print("  ch08: 1 figure saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end