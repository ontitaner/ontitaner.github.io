# @AI_GENERATED
"""第 03 章配图 1：惯量折算（RoCoF 反比于等效惯量）。

参数对齐章节 03.2 手算：
- 系统原等效惯量 J0 = 6.667 s -> RoCoF = 0.75 Hz/s（00.1 场景，ΔP=0.1 pu）
- 叠加虚拟惯量后 J_eq = 20 s（3 倍） -> RoCoF = 0.25 Hz/s
- 左图：频率跌落轨迹 f(t) = 50 - RoCoF·t（4 s 窗口，纯惯量无阻尼）
- 右图：RoCoF–J_eq 反比曲线，标注两个工作点
"""
from __future__ import annotations

import numpy as np

from _style import C_GFM, C_INERTIA, note, plt, save


def fig_inertia():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))

    # 左图：频率跌落轨迹
    ax = axes[0]
    t = np.linspace(0, 4, 100)
    ax.plot(t, 50 - 0.75 * t, color=C_INERTIA, label="J_eq=6.667 s（原系统）", linewidth=1.8)
    ax.plot(t, 50 - 0.25 * t, color=C_GFM, label="J_eq=20 s（加虚拟惯量）", linewidth=1.8)
    ax.axhline(49.0, color="gray", linestyle="--", linewidth=0.9)
    ax.set_title("频率跌落轨迹：惯量拉慢 RoCoF")
    ax.set_xlabel("时间 t (s)")
    ax.set_ylabel("频率 f (Hz)")
    ax.legend(loc="upper right")
    note(ax, "RoCoF 0.75 Hz/s：4 s 跌到 47 Hz", xy=(4, 47), xytext=(1.0, 46.55))
    note(ax, "RoCoF 0.25 Hz/s：4 s 跌到 49 Hz", xy=(4, 49), xytext=(0.9, 49.28))

    # 右图：RoCoF–J_eq 反比曲线
    ax = axes[1]
    J = np.linspace(4, 24, 200)
    ax.plot(J, 50 * 0.1 / J, color=C_INERTIA, linewidth=1.8)
    for j_eq, c in [(6.667, C_INERTIA), (20.0, C_GFM)]:
        ax.scatter([j_eq], [50 * 0.1 / j_eq], color=c, zorder=3)
    ax.set_title("RoCoF = f_n·ΔP / J_eq（反比）")
    ax.set_xlabel("系统等效惯量 J_eq (s)")
    ax.set_ylabel("RoCoF (Hz/s)")
    note(ax, "6.667 s → 0.75 Hz/s", xy=(6.667, 0.75), xytext=(8.6, 0.88))
    note(ax, "20 s → 0.25 Hz/s", xy=(20, 0.25), xytext=(13.6, 0.33))

    return fig


def main():
    save(fig_inertia(), "ch03_inertia")
# @AI_GENERATED: end