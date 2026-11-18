# @AI_GENERATED
"""第 03 章配图 2：构网型 vs 传统一次调频下垂曲线（死区对比）。

参数对齐章节 03.5 手算：
- D = 100/3 ≈ 33.333 pu（调差率 δ=3%）
- 构网型：ΔP = −D·Δf/f_n（无死区，过原点）
- 传统：ΔP = −D·deadzone(Δf)/f_n（死区 ±0.06 Hz，区内 0、区外扣除）
- Δf=-0.6 Hz：构网型 +20 MW，传统 +18 MW（差 2 MW）
"""
from __future__ import annotations

import numpy as np

from _style import C_DB, C_GFM, note, plt, save


def fig_droop():
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    f_n = 50.0
    D = 100.0 / 3.0

    df = np.linspace(-1.0, 0.0, 400)
    gfm = -D * df / f_n * 50.0          # MW，构网型无死区
    eff = np.where(df <= -0.06, df + 0.06, 0.0)  # 传统死区后有效频差
    pfr = -D * eff / f_n * 50.0

    ax.plot(df, gfm, color=C_GFM, label="构网型（无死区）", linewidth=1.8)
    ax.plot(df, pfr, color=C_DB, label="传统一次调频（死区 ±0.06 Hz）", linewidth=1.8)

    ax.axvspan(-0.06, 0.0, color=C_DB, alpha=0.15)
    ax.axvline(-0.06, color="gray", linestyle="--", linewidth=0.9)
    ax.axvline(0.0, color="gray", linestyle="--", linewidth=0.9)

    ax.scatter([-0.6], [20.0], color=C_GFM, zorder=3)
    ax.scatter([-0.6], [18.0], color=C_DB, zorder=3)
    note(ax, "Δf=-0.6 Hz → 构网型 +20 MW", xy=(-0.6, 20), xytext=(-0.38, 25.5))
    note(ax, "Δf=-0.6 Hz → 传统 +18 MW", xy=(-0.6, 18), xytext=(-0.76, 13.0))
    note(ax, "死区内构网型已出力，传统为 0", xy=(-0.04, -D * (-0.04) / f_n * 50.0),
         xytext=(-0.30, 6.5))

    ax.set_title("死区对比：构网型无死区下垂 vs 传统一次调频")
    ax.set_xlabel("频率偏差 Δf (Hz)")
    ax.set_ylabel("有功增量 ΔP (MW，正为增发)")
    ax.legend(loc="upper left")
    ax.set_xlim(-1.0, 0.0)
    ax.set_ylim(0, 30)
    return fig


def main():
    save(fig_droop(), "ch03_droop")
# @AI_GENERATED: end