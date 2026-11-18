# @AI_GENERATED
"""第 01 章配图：有功电流如何推歪并网点电压相位（弱电网 vs 强电网）。

参数对齐章节 01.5 手算：[教学示例]
- 短路比 SCR：本站 1.8（极弱）、对比 3（强）
- 电网等值阻抗 Z_g(pu) = 1/SCR：弱 0.556、强 0.333（高压电网以感抗为主，X_g ≈ Z_g）
- 有功电流扰动 Δi_d = 0.2 pu
- 相位偏移 Δθ ≈ Δi_d·X_g：弱 0.111 rad ≈ 6.4°、强 0.067 rad ≈ 3.8°，比值 1.67×
- 左图：相量图（机理：V_pcc = V_g + j·i_d·X_g，PLL 锁 V_pcc 的相位）
- 右图：Δθ-Δi_d 定量（斜率 = 1/SCR = X_g）
"""
from __future__ import annotations

import math

import numpy as np

from _style import C_GFM, C_TRIP, plt, save


def fig_paradigm():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))

    Xg_w = 0.556   # SCR = 1.8
    Xg_s = 0.333   # SCR = 3.0
    i_d = 0.2
    drop_w = i_d * Xg_w   # 0.1112 → 手算记 0.111 pu
    drop_s = i_d * Xg_s   # 0.0666 → 手算记 0.067 pu
    th_w = math.degrees(math.atan2(drop_w, 1.0))   # 相量真实方向 ≈6.34°
    th_s = math.degrees(math.atan2(drop_s, 1.0))   # ≈3.83°
    th_w_deg = drop_w * 180.0 / math.pi            # 小信号 0.111 rad ≈ 6.37°（与正文手算一致）
    th_s_deg = drop_s * 180.0 / math.pi            # 0.067 rad ≈ 3.82°（与正文手算一致）

    # ---------- 左：相量图（机理） ----------
    ax = axes[0]
    # 电网电压 V_g（水平参考，1 pu）
    ax.annotate("", xy=(1.0, 0), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color="black", lw=2.0))
    ax.text(0.30, -0.022, "电网电压 V_g = 1∠0° pu", fontsize=9)

    # 弱电网 V_pcc 及其压降
    ax.annotate("", xy=(1.0, drop_w), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color=C_TRIP, lw=2.2))
    ax.plot([1.0, 1.0], [0, drop_w], ls="--", color=C_TRIP, lw=1.3)
    ax.text(1.04, drop_w + 0.006, f"弱电网 V_pcc  ∠{th_w_deg:.1f}°（SCR=1.8，压降 0.111 pu）",
            color=C_TRIP, fontsize=9)

    # 强电网 V_pcc 及其压降
    ax.annotate("", xy=(1.0, drop_s), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color=C_GFM, lw=2.2))
    ax.plot([1.0, 1.0], [0, drop_s], ls=":", color=C_GFM, lw=1.3)
    ax.text(1.04, drop_s - 0.024, f"强电网 V_pcc  ∠{th_s_deg:.1f}°（SCR=3，压降 0.067 pu）",
            color=C_GFM, fontsize=9)

    # 顶部结论：压降来源 + PLL 机理（放在箭头末端上方空白区，避免遮挡）
    ax.text(0.0, 0.34, "压降 j·i_d·X_g（有功电流 × 感抗）：弱 0.111 pu / 强 0.067 pu\n"
                       "PLL 锁的正是 V_pcc 的相位 θ，弱电网 θ 更大 → 更易失锁",
            fontsize=8.5, color="#222222", va="top")

    ax.set_xlim(-0.12, 1.72)
    ax.set_ylim(-0.04, 0.38)
    ax.set_xlabel("实轴（同相分量）")
    ax.set_ylabel("虚轴（正交分量）")
    ax.set_title("机理：有功电流推歪并网点电压相位（相量图）  [教学示例]")

    # ---------- 右：Δθ-Δi_d（定量） ----------
    ax2 = axes[1]
    i_range = np.linspace(0, 0.5, 60)
    th_w_line = i_range * Xg_w * 180.0 / math.pi   # 小信号：Δθ = Δi_d·X_g
    th_s_line = i_range * Xg_s * 180.0 / math.pi

    ax2.plot(i_range, th_w_line, "-", color=C_TRIP, lw=2.2, label="弱电网（SCR=1.8）")
    ax2.plot(i_range, th_s_line, "-", color=C_GFM, lw=2.2, label="强电网（SCR=3）")

    # 0.2 pu 处关键点（只用短线定位，不用贯穿全图的横/竖线）
    th_w_at = i_d * Xg_w * 180.0 / math.pi   # 6.37°
    th_s_at = i_d * Xg_s * 180.0 / math.pi   # 3.82°
    ax2.plot([i_d], [th_w_at], "o", color=C_TRIP, ms=6)
    ax2.plot([i_d], [th_s_at], "o", color=C_GFM, ms=6)
    ax2.plot([i_d, i_d], [0, th_w_at], ls=":", color="#bbbbbb", lw=1.0)
    ax2.plot([0, i_d], [th_w_at, th_w_at], ls="--", color=C_TRIP, lw=1.0)
    ax2.plot([0, i_d], [th_s_at, th_s_at], ls="--", color=C_GFM, lw=1.0)

    ax2.annotate(f"Δi_d=0.2 pu：弱电网 {th_w_at:.1f}° / 强电网 {th_s_at:.1f}°\n"
                 "同一扰动，相位偏移相差 1.67 倍",
                 xy=(i_d, th_w_at), xytext=(0.02, 13.0),
                 fontsize=9, color="#333333",
                 arrowprops=dict(arrowstyle="->", color="#666666", lw=0.8))

    ax2.set_xlabel("有功电流扰动 Δi_d (pu)")
    ax2.set_ylabel("相位偏移 Δθ (°)")
    ax2.set_xlim(0, 0.52)
    ax2.set_ylim(0, 18.0)
    ax2.set_title("定量：相位偏移随有功电流线性增长（斜率=1/SCR）  [教学示例]")
    ax2.legend(loc="upper left", fontsize=8.5)

    save(fig, "ch01_paradigm")


def main():
    fig_paradigm()
    print("  ch01: 1 figure saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end