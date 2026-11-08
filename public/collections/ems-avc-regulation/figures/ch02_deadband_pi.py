# @AI_GENERATED
"""第 02 章配图：三种死区对比 + PI 调节收敛 + P-Q 能力圆。

参数对齐章节 02.2~02.5：[教学示例]
- 死区: db=±0.005 pu, 截断/连续两种
- PI: Kp=8000→实际约 5000, Ki=2000→滞后, Ts=1.0 s
- P-Q: S=1000 kVA, P=900 kW → Q_max=435.9 kvar
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Circle

from _style import (C_DIS, C_CHG, C_ACC, C_LIMIT, C_GRID, C_OK, C_PURPLE,
                    IMG_DIR, save, note, plt)


def fig_deadband():
    u = np.linspace(0.985, 1.015, 500)
    db = 0.005
    db_points = [0.008, 0.012, -0.003, -0.010]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    offsets = {
        0.008: (1.010, 220),
        0.012: (1.014, 340),
        -0.003: (0.994, -460),
        -0.010: (0.987, -540),
    }

    titles = ["截断型死区：|ΔU|>db 立刻动作", "连续型死区：|ΔU|>db 后线性过渡"]
    funcs = [
        lambda du: np.where(np.abs(du) > db, np.sign(du) * (np.abs(du) - db) * 50000, 0),
        lambda du: np.clip(np.where(np.abs(du) > db,
                                    np.sign(du) * (np.abs(du) - db) / (2 * db) * 500, 0), -500, 500),
    ]

    for idx, (ax, title, fn) in enumerate(zip(axes, titles, funcs)):
        du = u - 1.000
        q = fn(du)
        if idx == 0:
            jump = np.where(np.abs(np.diff(q)) > 5)[0]
            q_plot = q.copy()
            q_plot[jump] = np.nan
            ax.plot(u, q_plot, color=C_DIS, lw=2.4)
        else:
            ax.plot(u, q, color=C_CHG, lw=2.4)

        ax.axvspan(1.000 - db, 1.000 + db, color=C_ACC, alpha=0.2)
        ax.axvline(1.000 - db, color=C_OK, ls=":", lw=1.2)
        ax.axvline(1.000 + db, color=C_OK, ls=":", lw=1.2)
        ax.axhline(0, color="black", lw=0.6)

        for i, du_val in enumerate(db_points):
            q_val = fn(du_val)
            ax.plot(du_val + 1.000, q_val, "o", color=C_LIMIT, ms=8, zorder=5)
            note(ax, f"{'①②③④'[i]} ΔU={du_val:+.3f} pu → Q={q_val:.0f} kvar",
                 (du_val + 1.000, q_val), offsets[du_val], fontsize=9)

        ax.set_xlabel("PCC 电压 (pu)")
        ax.set_title(title, fontsize=10)
        ax.set_xlim(0.983, 1.017)
        ax.set_ylim(-600, 600)

    axes[0].set_ylabel("Q 请求 (kvar)")
    axes[0].text(1.000, -530, f"死区 ±{db:.3f} pu", ha="center", fontsize=9.5, color=C_ACC,
                 bbox=dict(fc="white", ec=C_ACC, alpha=0.95, boxstyle="round,pad=0.15"))
    fig.suptitle("死区 ±0.005 pu：截断型 vs 连续型对同一偏差的输出差异  [教学示例]", fontsize=11)
    save(fig, "ch02_deadband_compare")


def fig_pi_convergence():
    t = np.arange(0, 30, 0.1)
    dt = 0.1

    def simulate(kp, ki):
        u = np.ones_like(t) * 1.030
        q = np.zeros_like(t)
        integ = np.zeros_like(t)
        for i in range(1, len(t)):
            err = 1.000 - u[i - 1]
            integ[i] = integ[i - 1] + err * dt
            q[i] = kp * err + ki * integ[i]
            u[i] = u[i - 1] + 0.000025 * q[i] * dt + 0.01 * (1.000 - u[i - 1]) * dt
        return np.clip(q, -5500, 1000)

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6))

    ax = axes[0]
    q1 = simulate(8000, 2000)
    q2 = simulate(2000, 500)
    ax.plot(t, q1, color=C_CHG, lw=2.4, label="激进 PI (Kp=8000 Ki=2000)")
    ax.plot(t, q2, color=C_LIMIT, lw=2.4, ls="--", label="保守 PI (Kp=2000 Ki=500)")
    ax.axhline(0, color="black", lw=0.6)
    ax.axhline(-500, color=C_GRID, ls=":", lw=1.2)
    note(ax, "激进：3 s 到位\nKp 大，响应快", (3, -500), (7, -2800))
    note(ax, "保守：10 s 拉回\nKp 小，响应慢", (10, -200), (15, -2200))
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("Q (kvar)")
    ax.set_title("PI 参数对调节速度的影响")
    ax.legend(fontsize=8.5)
    ax.set_ylim(-5000, 500)

    ax = axes[1]
    u = np.ones_like(t) * 1.030
    q_p, q_i = np.zeros_like(t), np.zeros_like(t)
    integ = np.zeros_like(t)
    for i in range(1, len(t)):
        err = 1.000 - u[i - 1]
        integ[i] = integ[i - 1] + err * dt
        q_p[i] = 8000 * err
        q_i[i] = 2000 * integ[i]
        u[i] = u[i - 1] + 0.000025 * (q_p[i] + q_i[i]) * dt + 0.01 * (1.000 - u[i - 1]) * dt

    ax.plot(t, np.clip(q_p, -5500, 1000), color=C_DIS, lw=1.6, alpha=0.6, label="P 项（比例）")
    ax.plot(t, np.clip(q_i, -5500, 1000), color=C_CHG, lw=1.6, alpha=0.6, label="I 项（积分）")
    ax.plot(t, np.clip(q_p + q_i, -5500, 1000), color="black", lw=2.5, label="P+I 合计")
    ax.axhline(0, color="black", lw=0.6)
    note(ax, "P 主导早期\n快速压回", (2, q_p[20]), (6, -3000))
    note(ax, "I 持续累积\n消残差", (18, q_i[180]), (21, -1000))
    ax.set_xlabel("时间 (s)")
    ax.set_title("PI 分量分解：P 快速 + I 消除残差")
    ax.legend(fontsize=8.5)
    ax.set_ylim(-5000, 500)

    fig.suptitle("PI 调节收敛：参数敏感度 + P/I 分量分解  [Kp=8000 Ki=2000 Ts=1s 教学示例]", fontsize=11)
    save(fig, "ch02_pi_convergence")


def fig_pq_capability():
    s, p = 1000.0, 900.0
    q_max = np.sqrt(max(0, s**2 - p**2))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8),
                             gridspec_kw={"width_ratios": [1.15, 1]})

    ax = axes[0]
    ax.add_patch(Circle((0, 0), s, fill=True, color=C_CHG, alpha=0.08))
    ax.add_patch(Circle((0, 0), s, fill=False, color=C_CHG, lw=2.2))
    ax.axhline(0, color="black", lw=0.7)
    ax.axvline(0, color="black", lw=0.7)
    ax.plot(p, q_max, "o", color=C_LIMIT, ms=11, zorder=5)
    note(ax, f"P=900 kW\nQ_max={q_max:.1f} kvar\n√(1000²−900²)", (p, q_max), (550, 850))
    ax.plot(600, np.sqrt(1000**2 - 600**2), "o", color=C_OK, ms=10, zorder=5)
    note(ax, "P=600 kW\nQ_max=800 kvar", (600, np.sqrt(1000**2 - 600**2)), (200, 630))
    ax.text(600, -120, "放电 P>0", color=C_DIS, ha="center", fontsize=9)
    ax.text(-600, -120, "充电 P<0", color=C_CHG, ha="center", fontsize=9)
    ax.text(-800, 950, "发出 Q>0\n感性", color=C_PURPLE, fontsize=9, ha="center")
    ax.text(-800, -950, "吸收 Q<0\n容性", color=C_PURPLE, fontsize=9, ha="center")
    ax.set_xlim(-1100, 1100)
    ax.set_ylim(-1020, 1020)
    ax.set_aspect("equal")
    ax.set_xlabel("P (kW)")
    ax.set_ylabel("Q (kvar)")
    ax.set_title("P-Q 能力圆：P²+Q² ≤ S²")

    ax = axes[1]
    p_vals = [0, 300, 600, 900, 950]
    q_max_vals = [np.sqrt(max(0, s**2 - pv**2)) for pv in p_vals]
    colors = [C_OK, C_OK, C_ACC, C_LIMIT, C_LIMIT]
    bars = ax.bar([f"{pv}" for pv in p_vals], q_max_vals, color=colors, alpha=0.85, width=0.55)
    for bar, qv in zip(bars, q_max_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, qv + 15,
                f"{qv:.0f}", ha="center", fontsize=11, fontweight="bold")
    ax.set_ylabel("Q_max (kvar)")
    ax.set_xlabel("当前 P (kW)")
    ax.set_title("不同 P 水平下的 Q 上限\n1000 kVA PCS", fontsize=10)
    ax.set_ylim(0, 1100)

    fig.suptitle("P-Q 能力约束：有功越大，无功越少  [S=1000 kVA 教学示例]", fontsize=11)
    save(fig, "ch02_pq_capability")


def main():
    fig_deadband()
    fig_pi_convergence()
    fig_pq_capability()
    print(f"  ch02: 3 figures saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end