# @AI_GENERATED
"""第 08 章配图：并网调试三项 + PI 整定 + 阶梯控制曲线。

参数对齐章节 08.2~08.3：[教学示例]
- 调压功能：U_PCC=1.008 pu
- 电压限值：U_PCC<1.070 pu, U_35kV∈[0.93,1.07]
- PI 整定：Kp=8000, Ki=2000
- 阶梯控制：-30%→-60%→-30%→0 四段
"""
from __future__ import annotations

import numpy as np

from _style import (C_DIS, C_CHG, C_ACC, C_LIMIT, C_GRID, C_OK, C_PURPLE,
                    IMG_DIR, save, note, plt)


def fig_commissioning_steps():
    steps = ["第1步\n调压功能验证", "第2步\n电压限制功能", "第3步\n临界电压限制"]
    subjects = ["PID参数\n超调量\n调节时间", "37.5kV\n站内限值", "1.092pu\nPCC限值"]
    values = [1.008, 1.0357, 1.092]
    refs = [1.000, 37.5 / 35.0, 1.070]
    colors_step = [C_OK, C_ACC, C_LIMIT]
    oper_descs = ["投入AVC\n响应正常", "未触发\n限值有效", "越限跳机\n保护正确"]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5), sharey=False)

    for idx, (ax, step, subj, v, ref, cs, od) in enumerate(
            zip(axes, steps, subjects, values, refs, colors_step, oper_descs)):
        ax.bar(["目标值"], [v], width=0.35, color=cs, alpha=0.85)
        if idx > 0:
            ax.axhline(ref, color=C_LIMIT, ls="--", lw=1.8, label=f"限值 {ref:.3f}")
            ax.legend(fontsize=8, loc="upper right")
        else:
            ax.axhline(ref, color=C_GRID, ls=":", lw=1.2, label=f"额定 {ref:.3f}")
            ax.legend(fontsize=8)

        offset = 0.002 if idx < 2 else 0.003
        ax.text(0, v + offset, f"{v:.3f}", ha="center", fontsize=12, fontweight="bold", color=cs)
        ax.text(0, v - 0.012 if idx > 0 else v + 0.005, od, ha="center", fontsize=9, color=cs,
                bbox=dict(fc="white", ec=cs, alpha=0.9, boxstyle="round,pad=0.15"))

        ax.set_xticklabels([])
        ax.set_title(f"{step}\n{subj}", fontsize=9.5)
        if idx == 0:
            ax.set_ylabel("PCC 电压 (pu)")
        if idx == 1:
            ax.set_ylabel("35kV 电压 (pu)")

    fig.suptitle("AVC 并网调试三步走：功能→限值→保护  [教学示例]", fontsize=11)
    save(fig, "ch08_commissioning_steps")


def fig_pi_tuning():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    K_vals = np.array([1500, 3000, 5000, 8000, 12000])
    metrics = {"超调量 (%)": np.array([1.2, 2.0, 3.5, 6.8, 14.0]),
               "稳态余差 (pu)": np.array([0.0008, 0.0003, 0.0001, 0.00005, 0.00003]),
               "调节时间 (s)": np.array([15.5, 8.2, 5.0, 3.0, 1.8])}

    ax = axes[0]
    ax.plot(K_vals, metrics["超调量 (%)"], "o-", color=C_DIS, lw=2.4, label="超调量 %", ms=8)
    ax.axvline(8000, color=C_ACC, ls="--", lw=1.5)
    note(ax, "Kp=8000 推荐\nd>(PCS 死区)", (8000, 6.8), (10000, 12))
    ax.set_xlabel("Kp (比例系数)")
    ax.set_ylabel("超调量 (%)")
    ax.set_title("Kp↑ → 超调↑ 稳态余差↓")
    ax.legend(fontsize=8)

    ax = axes[1]
    ax3 = ax.twinx()
    ax3.plot(K_vals, metrics["稳态余差 (pu)"], "s-", color=C_CHG, lw=2.2, label="稳态余差", ms=8)
    ax3.set_ylabel("稳态余差 (pu)", color=C_CHG)
    ax3.tick_params(axis="y", labelcolor=C_CHG)
    ax.set_xlabel("Kp (比例系数)")
    ax.set_ylabel("超调量 (%)", color=C_DIS)
    ax.tick_params(axis="y", labelcolor=C_DIS)
    ax.plot(K_vals, metrics["超调量 (%)"], "o-", color=C_DIS, lw=2.4, ms=8, label="超调量")
    ax.axvline(8000, color=C_ACC, ls="--", lw=1.5)
    ax.set_title("Kp 整定：超调量 vs 稳态余差")

    fig.suptitle("PI 参数整定：建议 Kp>PCS 死区，兼顾超调与余差  [教学示例]", fontsize=11)
    save(fig, "ch08_pi_tuning")


def fig_stepped_control():
    t = np.arange(0, 90, 0.5)
    u = np.ones_like(t) * 1.030
    q = np.zeros_like(t)

    stages = [(0, 20, -0.30, "阶梯1\nQ=-30%"), (20, 45, -0.60, "阶梯2\nQ=-60%"),
              (45, 70, -0.30, "阶梯3\nQ=-30%"), (70, 90, 0.00, "归位\nQ=0")]
    colors = [C_ACC, C_LIMIT, C_ACC, C_OK]

    for t0, t1, q_cmd, label in stages:
        mask = (t >= t0) & (t < t1)
        q[mask] = 1000 * q_cmd

    for i in range(1, len(t)):
        u[i] = u[i - 1] + 0.00002 * q[i] * 0.5

    fig, ax1 = plt.subplots(figsize=(10, 4.2))
    ax2 = ax1.twinx()
    ax1.plot(t, u, color=C_PURPLE, lw=2.2, label="PCC 电压 (pu)")
    ax2.fill_between(t, 0, q, alpha=0.3, color=C_CHG)
    ax2.plot(t, q, color=C_CHG, lw=1.8, label="Q 指令 (kvar)", drawstyle="steps-post", alpha=0.7)

    for t0, t1, q_cmd, label in stages:
        mid = (t0 + t1) / 2
        offset = 50 if q_cmd < -0.15 else -80
        note(ax2, label, (mid, 1000 * q_cmd), (mid + 5, 1000 * q_cmd + offset))

    ax1.set_xlabel("时间 (s)")
    ax1.set_ylabel("PCC 电压 (pu)", color=C_PURPLE)
    ax2.set_ylabel("Q 指令 (kvar)", color=C_CHG)
    ax1.set_title("多级阶梯 Q 指令：-30%→-60%→-30%→0 将电压拉回安全范围")
    ax1.tick_params(axis="y", labelcolor=C_PURPLE)
    ax2.tick_params(axis="y", labelcolor=C_CHG)

    fig.suptitle("阶梯无功控制：避免振荡，稳定收敛至 1.000 pu  [教学示例]", fontsize=11)
    save(fig, "ch08_stepped_control")


def main():
    fig_commissioning_steps()
    fig_pi_tuning()
    fig_stepped_control()
    print(f"  ch08: 3 figures saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end