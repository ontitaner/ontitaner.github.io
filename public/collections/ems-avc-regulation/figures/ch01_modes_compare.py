# @AI_GENERATED
"""第 01 章配图：四种 AVC 控制模式在同一过压场景下的请求对比。

参数对齐章节 01.2：[教学示例]
场景：U 从 1.030→1.020→1.010→1.010 pu, P 从 800→800→400→400 kW
定Q=−300, 定PF=−262.9/−131.5, Q-U下垂=−200/−100/0/0, 定电压PI=−500/−420/−360/−400
"""
from __future__ import annotations

import numpy as np

from _style import (C_OK, C_ACC, C_Q_ABSORB, C_TARGET, C_LIMIT,
                    IMG_DIR, save, note, plt)


def fig_modes_compare():
    t = np.arange(4)
    u = [1.030, 1.020, 1.010, 1.010]
    p = [800, 800, 400, 400]
    fixed = [-300, -300, -300, -300]
    pf = [-262.9, -262.9, -131.5, -131.5]
    droop = [-200, -100, 0, 0]
    avc = [-500, -420, -360, -400]

    panels = [
        ("定Q：调度设点 Q=−300 kvar", fixed, C_TARGET, "Q"),
        ("定PF： cosφ=0.95, P×tanφ", pf, C_ACC, "PF"),
        ("Q-U 下垂：ΔU → ΔQ", droop, C_OK, "Droop"),
        ("定电压 AVC：U 目标 + 历史积分", avc, C_LIMIT, "AVC"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.6), sharex=True, sharey=True)
    for ax, (title, vals, color, tag) in zip(axes.flat, panels):
        ax.axhline(0, color="#cccccc", lw=0.8)
        ax.plot(t, vals, "-o", color=color, lw=2.4, ms=7)
        for k, val in enumerate(vals):
            ax.annotate(f"{val:.0f}", (k, val), xytext=(0, 9 if val < 0 else -12),
                        textcoords="offset points", ha="center", fontsize=8.5)
        ax.set_title(title, fontsize=10)
        ax.set_xticks(t, ["t0\nU=1.030\nP=800", "t1\nU=1.020\nP=800", "t2\nU=1.010\nP=400", "t3\nU=1.010\nP=400"])
        ax.set_ylabel("Q 请求 (kvar, 吸收为负)")
        ax.set_ylim(-600, 200)

    fig.suptitle("同一过压场景：四种模式的 Q 请求依据不同  [教学示例]", fontsize=12)
    save(fig, "ch01_modes_compare")


def main():
    fig_modes_compare()
    print(f"  ch01: saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end