# @AI_GENERATED
"""第 08 章配图：联调试验阶跃响应 + 证据链 + 多场景对比（增强版）。

所有参数均为 [教学示例]，不可直接用于现场整定。
"""
from __future__ import annotations

import numpy as np

from _style import (C_K1, C_K2, C_K3, C_GRID, C_LIMIT, C_OK, C_ACC, C_PURPLE,
                    IMG_DIR, manifest, save, plt)


def simulate_step(pn, target_start, target_end, t_cmd, t_recv, t_start, ramp_rate, t_total=35):
    """通用阶跃响应模拟函数"""
    t = np.linspace(0, t_total, int(t_total * 40 + 1))
    dt = t[1] - t[0]

    p_cmd = np.where(t < t_cmd, target_start, target_end)
    p_act = np.full_like(t, target_start)
    rng = np.random.default_rng(42)

    for i in range(1, len(t)):
        if t[i] >= t_start:
            p_target = target_end
            step = np.clip(p_target - p_act[i-1], -ramp_rate * dt, ramp_rate * dt)
            p_act[i] = p_act[i-1] + step
        else:
            p_act[i] = target_start

    # 稳态后加噪声
    t_end_idx = np.argmax(np.abs(p_act - target_end) < 1.5)
    if t_end_idx > 0:
        t_end = t[t_end_idx]
        p_act[t_end_idx:] += rng.normal(0, 0.15, len(p_act) - t_end_idx)
    else:
        t_end = t[-1]

    k2 = t_start - t_cmd
    k1_dp = target_end - target_start
    k1_dt = t_end - t_start
    k1 = k1_dp / k1_dt if k1_dt > 0 else 0
    k3 = abs(np.mean(p_act[-100:]) - target_end) / pn * 100

    return t, p_cmd, p_act, t_end, k1, k2, k3


def fig_step_response_test():
    """联调试验二：三场景阶跃响应对比（上调/下调/小幅）+ 单场景放大详图 + 达标判定热力图"""
    pn = 100.0

    # 场景 A: 上调 +17.7 MW（52.3→70），ramp 1.2 MW/s
    scen_a = ("上调 52.3→70 MW", 52.3, 70.0, 5.0, 5.2, 5.5, 1.2)

    # 场景 B: 下调 −15 MW（70→55），ramp 1.0 MW/s
    scen_b = ("下调 70→55 MW", 70.0, 55.0, 5.0, 5.3, 5.6, 1.0)

    # 场景 C: 小幅上调 +5 MW（65→70），ramp 0.8 MW/s（慢速资源）
    scen_c = ("小幅 65→70 MW", 65.0, 70.0, 5.0, 5.1, 5.4, 0.8)

    scenarios = [scen_a, scen_b, scen_c]
    results = []

    for label, s, e, cmd, recv, start, ramp in scenarios:
        t, p_cmd, p_act, t_end, k1, k2, k3 = simulate_step(pn, s, e, cmd, recv, start, ramp)
        results.append((t, p_cmd, p_act, t_end, k1, k2, k3, label))

    fig = plt.figure(figsize=(14, 8.5))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1], hspace=0.34, wspace=0.26)

    # 顶部（全宽）：三场景叠加对比
    ax = fig.add_subplot(gs[0, :])
    colors = [C_OK, C_ACC, C_PURPLE]
    styles = ["-", "--", "-."]

    for i, (t, p_cmd, p_act, t_end, k1, k2, k3, label) in enumerate(results):
        c = colors[i]
        ls = styles[i]
        ax.step(t, p_cmd, where="post", color=c, lw=1.5, ls=ls, alpha=0.4)
        ax.plot(t, p_act, color=c, lw=2.2, ls=ls, label=f"{label}  K1={k1:.2f}  K2={k2:.1f}s  K3={k3:.2f}%")
        # 填充偏差区
        ax.fill_between(t, p_cmd, p_act, alpha=0.04, color=c)
        # 标注 t_start
        ax.axvline(5.5, color=c, ls=":", lw=0.8, alpha=0.4)

    # K2 区
    ax.axvspan(5.0, 5.6, color=C_K2, alpha=0.06)
    ax.annotate("K2 响应时间区\n5.0→5.6 s",
                xy=(5.3, 52), fontsize=8, color=C_K2, ha="center",
                bbox=dict(fc="white", ec=C_K2, alpha=0.9, boxstyle="round"))

    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("有功出力 (MW)")
    ax.set_title("三场景阶跃响应叠加对比  [Pn=100 MW]", fontsize=10)
    ax.legend(fontsize=7.5, loc="lower right")
    ax.set_xlim(0, 30)
    ax.set_ylim(47, 78)

    # K1/K2/K3 单项得分与综合评分（供右下热力图使用）
    k1_scores = [min(100, 100 * r[4] / 1.0) for r in results]
    k2_scores = [max(0, 100 * (1 - r[5] / 30.0)) for r in results]
    k3_scores = [max(0, 100 * (1 - r[6] / 3.0)) for r in results]
    totals = [0.3 * k1 + 0.2 * k2 + 0.5 * k3 for k1, k2, k3 in zip(k1_scores, k2_scores, k3_scores)]

    # 左下：单场景放大（上调 52.3→70 MW），含全部标注
    ax3 = fig.add_subplot(gs[1, 0])
    t, p_cmd, p_act, t_end, k1, k2, k3, label = results[0]

    ax3.step(t, p_cmd, where="post", color=C_GRID, lw=2.2, ls="--", label="调度 AGC 指令")
    ax3.plot(t, p_act, color=C_OK, lw=2.5, label="实际出力响应")

    # 四个关键时刻
    for tc, color, ls, lbl in [
        (5.0, C_PURPLE, "-.", "T_cmd=5.0s"),
        (5.2, C_ACC, "--", "T_recv=5.2s"),
        (5.5, C_K2, ":", "T_start=5.5s"),
        (t_end - 0.3, C_OK, "--", f"T_end≈{t_end:.0f}s"),
    ]:
        ax3.axvline(tc, color=color, ls=ls, lw=1.5, alpha=0.7)

    # K2 填充
    ax3.axhspan(51, 53.5, xmin=5.0/35, xmax=5.5/35, color=C_K2, alpha=0.1)
    ax3.annotate(f"K2 = T_start-T_cmd = 0.5s\n（储能限 3s OK）",
                xy=(5.25, 52.2), fontsize=8.5, color=C_K2, ha="center",
                bbox=dict(fc="white", ec=C_K2, alpha=0.9, boxstyle="round"))

    # K1 标注
    ax3.annotate(f"K1 = ΔP/Δt = ({70-52.3:.0f})/({t_end:.1f}-5.5)\n   = {k1:.2f} MW/s  (需 ≥ 1.0)",
                xy=(12, 60), fontsize=8.5, color=C_K1,
                bbox=dict(fc="white", ec=C_K1, alpha=0.9, boxstyle="round"))

    # K3 标注
    p_end = np.mean(p_act[-100:])
    ax3.annotate(f"K3 = |{p_end:.1f}-70|÷100\n   = {k3:.2f}% Pn  (需 ≤ 3%)",
                xy=(26, p_end), xytext=(26, 74),
                arrowprops=dict(arrowstyle="->", color=C_K3),
                fontsize=8.5, color=C_K3,
                bbox=dict(fc="white", ec=C_K3, alpha=0.9, boxstyle="round"))

    # 稳态区间
    idx_steady = int(t_end / 35 * len(t))
    if idx_steady < len(t):
        ax3.axhspan(68.5, 71.5, xmin=t_end/35, color=C_K3, alpha=0.08)
        ax3.text(t_end + 0.5, 69, "稳态\n±1.5MW", fontsize=7.5, color=C_K3)

    # 标注指令阶跃
    ax3.annotate("指令阶跃\n+17.7 MW", xy=(5.0, 70), xytext=(1.5, 74.5),
                arrowprops=dict(arrowstyle="->", color=C_GRID), fontsize=8, color=C_GRID,
                bbox=dict(fc="white", ec=C_GRID, alpha=0.85, boxstyle="round"))

    ax3.set_xlabel("时间 (s)")
    ax3.set_ylabel("有功出力 (MW)")
    ax3.set_title(f"上调 +17.7 MW 放大详图  [K1={k1:.2f} K2={k2:.1f}s K3={k3:.2f}%]", fontsize=10)
    ax3.legend(loc="upper left", fontsize=8)
    ax3.set_xlim(0, 33)
    ax3.set_ylim(48, 78)

    # 右下：三场景 K1/K2/K3 达标判定矩阵（热力图）
    ax4 = fig.add_subplot(gs[1, 1])
    criteria = ["K1 速率\n(≥1.0 MW/s)", "K2 响应\n(≤3s 储能)", "K3 精度\n(≤3% Pn)", "综合评分\n(≥80 分)"]
    scen_labels = ["上调 17.7MW", "下调 15MW", "小幅 5MW"]

    data = np.array([
        [k1_scores[0], k1_scores[1], k1_scores[2]],
        [k2_scores[0], k2_scores[1], k2_scores[2]],
        [k3_scores[0], k3_scores[1], k3_scores[2]],
        [totals[0], totals[1], totals[2]],
    ])

    im = ax4.imshow(data, cmap="RdYlGn", aspect="auto", vmin=0, vmax=100)
    for i in range(4):
        for j in range(3):
            val = data[i, j]
            threshold = 80 if i < 4 else 80
            color = "white" if val < 60 else "black"
            result = "OK" if val >= threshold else "NG"
            ax4.text(j, i, f"{val:.0f}\n{result}", ha="center", va="center", fontsize=10,
                     color=color, fontweight="bold")

    ax4.set_xticks(range(3))
    ax4.set_xticklabels(scen_labels, fontsize=9)
    ax4.set_yticks(range(4))
    ax4.set_yticklabels(criteria, fontsize=8.5)
    ax4.set_title("达标判定矩阵", fontsize=10)
    cbar4 = fig.colorbar(im, ax=ax4, shrink=0.8, pad=0.02)
    cbar4.set_label("得分", fontsize=7.5)

    fig.suptitle("AGC 联调 ② 阶跃指令响应试验——三场景全方位对比  [Pn=100 MW, 教学示例]",
                 fontsize=12, y=1.02)
    fig.text(0.5, 0.01,
             "K1 = ΔP/ΔT  |  K2 = T_start−T_cmd  |  K3 = |P_actual−P_target|/Pn×100%  |  综合 = 0.3K1+0.2K2+0.5K3",
             ha="center", fontsize=8.5, color=C_GRID)

    manifest("ch08_step_response",
             [pn, 52.3, 70.0, 55.0, 65.0, 5.0, 5.2, 5.5, 1.2, 1.0, 0.8, 17.7, 15.0, 5.0,
              results[0][4], results[0][5], results[0][6],
              results[1][4], results[1][5], results[1][6],
              results[2][4], results[2][5], results[2][6]]
             + k1_scores + k2_scores + k3_scores + totals)
    save(fig, "ch08_step_response")


def fig_evidence_chain():
    """四时刻证据链：单面板全宽甘特图时间线（标签沿事件点两侧阶梯排布，避免左侧拥挤）。"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 5.2))

    events = [
        ("调度主站下发 · T_cmd\nP_target=70 MW · 14:30:00.000", 0.0, C_PURPLE, +0.45, "left"),
        ("EMS 接收 · T_recv\n14:30:00.200 · 通信≤200ms", 0.2, C_ACC, +0.45, "left"),
        ("PCS 开始动作 · T_start\n14:30:00.500 · 启机≤300ms", 0.5, C_K2, +0.45, "left"),
        ("进入稳态 · T_end\n14:30:15.200", 15.2, C_OK, -0.45, "right"),
    ]

    y_positions = [3, 2, 1, 0]

    # K2 / K1 时间区竖向色带（下沉至最底层）
    ax.axvspan(0, 0.5, color=C_K2, alpha=0.08, zorder=0)
    ax.axvspan(0.5, 15.2, color=C_K1, alpha=0.05, zorder=0)

    # 事件车道（浅灰横线）+ 事件点 + 阶梯标签
    for (label, start_t, color, dx, ha), y in zip(events, y_positions):
        ax.hlines(y, 0, 15.2, color=C_GRID, lw=0.8, alpha=0.35, zorder=1)
        ax.plot([start_t, start_t], [y - 0.3, y + 0.3], color=color, lw=1.3, zorder=4)
        ax.plot(start_t, y, "o", color=color, markersize=9, zorder=5,
                markeredgecolor="white", markeredgewidth=1.5)
        ax.text(start_t + dx, y, label, ha=ha, va="center", fontsize=9.5,
                color="#2b2d33", zorder=6,
                bbox=dict(fc="white", ec=color, alpha=0.92, boxstyle="round,pad=0.35"))

    # K2 标注（顶部左侧，指向 0→0.5 s 响应区）
    ax.annotate("K2 = 0.5 − 0 = 0.5 s\n（达标 OK）",
                xy=(0.25, 3.35), xytext=(2.9, 4.45), fontsize=10,
                color=C_K2, ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=C_K2),
                bbox=dict(fc="white", ec=C_K2, alpha=0.95, boxstyle="round,pad=0.4"))

    # K1 标注（顶部居中，指向 0.5→15.2 s 爬坡区）
    ax.annotate("K1 = (70−52.3)/(15.2−0.5)\n   = 17.7/14.7 = 1.20 MW/s（达标）",
                xy=(7.85, 3.35), xytext=(7.85, 4.45), fontsize=10,
                color=C_K1, ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=C_K1),
                bbox=dict(fc="white", ec=C_K1, alpha=0.95, boxstyle="round,pad=0.4"))

    # K3 标注（底部右侧，指向 T_end 稳态点）
    ax.annotate("K3 = |70.1−70|/100 = 0.1% Pn\n（达标 OK）",
                xy=(15.2, 0.28), xytext=(15.2, -1.45), fontsize=10,
                color=C_K3, ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=C_K3),
                bbox=dict(fc="white", ec=C_K3, alpha=0.95, boxstyle="round,pad=0.4"))

    ax.set_yticks([])
    ax.set_xlabel("时间 (s, 从 T_cmd 起算)")
    ax.set_title("四时刻证据链 (GPS 时标对账)", fontsize=12)
    ax.set_xlim(-1.0, 16.8)
    ax.set_ylim(-1.9, 5.2)

    fig.suptitle("AGC 联调四时刻证据链——GPS 时标对账  [14:30:00.000 起, 教学示例]",
                 fontsize=12.5, y=1.02)
    fig.text(0.5, -0.02,
             "K2 = 0.5s OK  |  K1 = 1.20 MW/s OK  |  K3 = 0.1% Pn OK  |  全链路时标闭环可追溯",
             ha="center", fontsize=9, color=C_GRID)

    manifest("ch08_evidence_chain",
             [0.0, 0.2, 0.5, 15.2, 0.5, 1.20, 0.1, 70.0, 52.3, 70.1, 100, 17.7, 14.7, 200, 300])
    save(fig, "ch08_evidence_chain")


def main():
    fig_step_response_test()
    fig_evidence_chain()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end