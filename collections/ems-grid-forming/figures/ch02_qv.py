# @AI_GENERATED
"""第 02 章配图 2：Q-V 下垂曲线（V_ref 与 k_q）。

参数对齐章节 02.5 手算：V = V_ref − k_q·(Q − Q_ref)，V_ref=1.0, k_q=0.05。
"""
from __future__ import annotations

import numpy as np

from _style import C_INERTIA, note, plt, save


def fig_qv():
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    q = np.linspace(-0.4, 0.4, 100)
    v = 1.0 - 0.05 * q
    ax.plot(q, v, color=C_INERTIA, linewidth=1.8)
    ax.scatter([0.2, -0.2], [0.99, 1.01], color="black", zorder=3)
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=0.9)
    ax.axvline(0.0, color="gray", linestyle="--", linewidth=0.9)
    ax.set_title("Q-V 下垂：V = V_ref − k_q·(Q − Q_ref)")
    ax.set_xlabel("无功 Q (pu)")
    ax.set_ylabel("电压 V (pu)")
    note(ax, "Q=+0.2 pu → V=0.99 pu", xy=(0.2, 0.99), xytext=(-0.15, 0.965))
    note(ax, "Q=-0.2 pu → V=1.01 pu", xy=(-0.2, 1.01), xytext=(-0.42, 1.03))
    return fig


def main():
    save(fig_qv(), "ch02_qv")
# @AI_GENERATED: end