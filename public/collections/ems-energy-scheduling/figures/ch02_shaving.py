# @AI_GENERATED
"""第 02 章配图：需量削峰。

参数对齐章节 02.2/02.3：[教学示例]
- 日负荷峰值 7.0 MW，目标需量 5.0 MW，BESS 放电上限 2.0 MW
- 削峰后最大需量 = 5.0 MW
"""
from __future__ import annotations

import numpy as np

from _style import C_LOAD, C_DIS, C_TARGET, C_ACC, save, note, plt

LOAD = [3.5, 3.0, 2.8, 2.6, 2.8, 3.2, 4.0, 5.0, 6.0, 6.5, 6.8, 7.0,
        6.5, 5.8, 5.5, 5.6, 6.2, 6.8, 7.0, 6.5, 5.8, 5.0, 4.2, 3.8]
TARGET = 5.0
P_MAX = 2.0


def fig_shaving():
    hours = np.arange(24)
    load = np.array(LOAD)
    bess = np.minimum(P_MAX, np.maximum(0.0, load - TARGET))
    shaved = load - bess

    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.plot(hours, load, color=C_LOAD, lw=2.2, marker="o", ms=4, label="原始负荷")
    ax.plot(hours, shaved, color=C_ACC, lw=2.2, marker="s", ms=4, label="削峰后负荷")
    ax.fill_between(hours, shaved, load, where=bess > 0, color=C_DIS, alpha=0.28,
                    label="BESS 放电削峰")
    ax.axhline(TARGET, color=C_TARGET, ls="--", lw=1.4)
    ax.text(23.4, TARGET + 0.1, f"目标需量 {TARGET:.0f} MW", color=C_TARGET,
            ha="right", fontsize=9.5)

    note(ax, "峰值 7.0 MW\n超需量 2.0 MW", (11, 7.0), (15, 7.4))
    note(ax, "BESS 放电 2.0 MW\n削到 5.0 MW", (11, 5.0), (13.5, 5.6))

    ax.set_xlabel("小时 (h)")
    ax.set_ylabel("功率 (MW)")
    ax.set_xticks(hours)
    ax.set_ylim(0, 8.0)
    ax.legend(loc="upper left", fontsize=8.5)
    ax.set_title("需量削峰：峰值 7.0 → 5.0 MW（BESS 2 MW）  [教学示例]")
    save(fig, "ch02_shaving")


def main():
    fig_shaving()
    print("  ch02: 1 figure saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end