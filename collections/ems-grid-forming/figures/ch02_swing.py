# @AI_GENERATED
"""第 02 章配图 1：VSG 摇摆方程频率轨迹（J 扫描 + D 扫描）。

参数对齐章节 02.5 手算：
- P_ref=0.5 pu、功率缺口 P 突增到 0.6 pu、dt=0.1 s、共 40 拍（4 s）
- 左图：J 扫描（J=4/8 s，演示 J 决定初始 RoCoF，稳态相同 49.75 Hz）
- 右图：D 扫描（D=20/40 pu，演示 D 决定稳态频偏，初始 RoCoF 相同 -1.25 Hz/s）
"""
from __future__ import annotations

import numpy as np

from _style import C_GFM, C_INERTIA, note, plt, save


def swing_trace(J, D, p_ref=0.5, p_e=0.6, dt=0.1, n=40):
    omega = 1.0
    out = [omega]
    for _ in range(n):
        dw = (p_ref - p_e - D * (omega - 1.0)) / J
        omega = omega + dt * dw
        out.append(omega)
    return out


def fig_swing():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
    t = np.arange(0, 4.1, 0.1)

    # 左图：J 扫描
    ax = axes[0]
    for J, c, lab in [(4.0, C_INERTIA, "J=4 s"), (8.0, C_GFM, "J=8 s")]:
        f = np.array(swing_trace(J, 20.0)) * 50.0
        ax.plot(t, f, color=c, label=lab, linewidth=1.8)
    ax.axhline(49.75, color="gray", linestyle="--", linewidth=0.9)
    ax.set_title("J 扫描：J 决定 RoCoF")
    ax.set_xlabel("时间 t (s)")
    ax.set_ylabel("频率 f (Hz)")
    ax.legend(loc="lower right")
    note(ax, "J=4 s：初始 RoCoF -1.25 Hz/s", xy=(0.1, 49.875), xytext=(0.9, 49.915))
    note(ax, "J=8 s：初始 RoCoF -0.625 Hz/s", xy=(0.1, 49.9375), xytext=(1.4, 49.965))

    # 右图：D 扫描
    ax = axes[1]
    for D, c, lab in [(20.0, C_INERTIA, "D=20 pu"), (40.0, C_GFM, "D=40 pu")]:
        f = np.array(swing_trace(4.0, D)) * 50.0
        ax.plot(t, f, color=c, label=lab, linewidth=1.8)
    ax.axhline(49.75, color="gray", linestyle="--", linewidth=0.9)
    ax.axhline(49.875, color="gray", linestyle="--", linewidth=0.9)
    ax.set_title("D 扫描：D 决定稳态频偏")
    ax.set_xlabel("时间 t (s)")
    ax.set_ylabel("频率 f (Hz)")
    ax.legend(loc="lower right")
    note(ax, "D=20 pu → 49.75 Hz", xy=(3.6, 49.755), xytext=(2.0, 49.70))
    note(ax, "D=40 pu → 49.875 Hz", xy=(3.6, 49.878), xytext=(1.6, 49.95))

    return fig


def main():
    save(fig_swing(), "ch02_swing")
# @AI_GENERATED: end