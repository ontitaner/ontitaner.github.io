# @AI_GENERATED
"""第17章四模式对照修复图：所有面板使用共同t0～t3时间轴和−500～+500 kvar量程。"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt

from _style import C_CHG, C_GRID, C_LIMIT, C_OK, IMG_DIR


def main() -> None:
    times = [0, 1, 2, 3]
    labels = ["t0", "t1", "t2", "t3"]
    panels = [
        ("定 Q\n依据：调度 Q 设点", [-300.0, -300.0, -300.0, -300.0], C_CHG),
        ("定 PF\n依据：PF 目标 + 当前 P", [-262.9, -262.9, -131.5, -131.5], C_CHG),
        ("Q-U 下垂\n依据：当前 U", [-200.0, -100.0, 0.0, 0.0], C_OK),
        ("定电压 AVC\n依据：U 目标 + 当前 U + 历史", [-300.0, -260.0, -200.0, -220.0], C_LIMIT),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.2), sharex=True, sharey=True)
    for ax, (title, values, color) in zip(axes.flat, panels):
        ax.axhline(0, color=C_GRID, lw=0.8)
        ax.plot(times, values, "-o", color=color, lw=2.4, ms=7)
        for t, value in zip(times, values):
            ax.annotate(f"{value:.1f}", (t, value), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=8.5)
        ax.set_title(title, fontsize=10)
        ax.set_xticks(times, labels)
        ax.set_ylim(-500, 500)
        ax.set_ylabel("Q 请求 (kvar)")
        ax.grid(alpha=0.3)
    axes[1, 0].set_xlabel("共同场景：U 1.030 → 1.020 → 1.010 → 1.010 pu")
    axes[1, 1].set_xlabel("共同场景：P 800 → 800 → 400 → 400 kW")
    fig.suptitle("同一过压场景：四种模式的 Q 请求依据不同（Q<0 为吸收）", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = IMG_DIR / "ch17_modes_compare_fixed.png"
    fig.savefig(out, bbox_inches="tight", dpi=150)
    plt.close(fig)
    (IMG_DIR / "ch17_modes_compare_fixed.json").write_text(
        json.dumps({"figure": out.name, "numbers": [-500.0, -300.0, -262.9, -260.0, -220.0, -200.0,
                                                       -131.5, -100.0, 0.0, 1.0, 2.0, 3.0, 1.010, 1.020,
                                                       1.030, 400.0, 500.0, 800.0]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"saved {out}")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
