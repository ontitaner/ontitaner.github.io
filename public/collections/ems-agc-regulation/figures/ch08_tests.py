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
    """联调试验二：三场景阶跃响应对比（上调/下调/小幅）+ K1K2K3 评估矩阵"""
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

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), gridspec_kw={"height_ratios": [1.2, 1]})

    # 左上：三场景叠加对比
    ax = axes[0, 0]
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

    # 右上：K1/K2/K3 雷达式评估矩阵（3×3 标准化得分）
    ax2 = axes[0, 1]
    k1_scores = [min(100, 100 * r[4] / 1.0) for r in results]
    k2_scores = [max(0, 100 * (1 - r[5] / 30.0)) for r in results]
    k3_scores = [max(0, 100 * (1 - r[6] / 3.0)) for r in results]
    totals = [0.3 * k1 + 0.2 * k2 + 0.5 * k3 for k1, k2, k3 in zip(k1_scores, k2_scores, k3_scores)]

    x = np.arange(3)
    width = 0.22
    ax2.bar(x - width, k1_scores, width, color=C_K1, alpha=0.85, label="K1 (w=30%)", edgecolor="white")
    ax2.bar(x, k2_scores, width, color=C_K2, alpha=0.85, label="K2 (w=20%)", edgecolor="white")
    ax2.bar(x + width, k3_scores, width, color=C_K3, alpha=0.85, label="K3 (w=50%)", edgecolor="white")

    for i, (k1, k2, k3, tot) in enumerate(zip(k1_scores, k2_scores, k3_scores, totals)):
        ax2.text(i, 105, f"{tot:.1f} 分", ha="center", fontsize=11, fontweight="bold",
                 color=C_OK if tot >= 80 else C_LIMIT)
        ax2.text(i - width, k1 + 2, f"{k1:.0f}", ha="center", fontsize=7.5, color=C_K1)
        ax2.text(i, k2 + 2, f"{k2:.0f}", ha="center", fontsize=7.5, color=C_K2)
        ax2.text(i + width, k3 + 2, f"{k3:.0f}", ha="center", fontsize=7.5, color=C_K3)

    ax2.axhline(80, color=C_LIMIT, ls="--", lw=1.5, label="合格线 80")
    ax2.set_xticks(x)
    ax2.set_xticklabels(["上调\n17.7MW", "下调\n15MW", "小幅\n5MW"], fontsize=9)
    ax2.set_ylabel("单项得分")
    ax2.set_title("K1/K2/K3 评估矩阵  [华东权重]", fontsize=10)
    ax2.legend(fontsize=7.5, loc="lower right")
    ax2.set_ylim(0, 120)

    # 左下：单场景放大（上调 52.3→70 MW），含全部标注
    ax3 = axes[1, 0]
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
    ax4 = axes[1, 1]
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
    """四时刻证据链：甘特图时间线 + 多场景对齐 + 证据溯源表"""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), width_ratios=[1.2, 0.9, 0.8])

    # 左图：四时刻证据链甘特图（同原来但增强标注）
    ax = axes[0]

    events = [
        ("调度主站下发\nP_target=70 MW\n14:30:00.000\nGPS时标锁定", 0, 0.0, C_PURPLE),
        ("EMS 接收\n校验+死区判定\n14:30:00.200\n通信≤200ms", 0.20, 0.2, C_ACC),
        ("PCS 开始动作\n出力52.3→爬坡\n14:30:00.500\n启机≤300ms", 0.50, 0.5, C_K2),
        ("进入稳态\n出力=70.1 MW\n14:30:15.200\nK3=0.1% Pn", 15.20, 15.2, C_OK),
    ]

    y_positions = [3, 2, 1, 0]

    for (label, start_t, _, color), y in zip(events, y_positions):
        ax.barh(y, 0.15, left=start_t, color=color, alpha=0.85, height=0.55, edgecolor="white")
        ax.text(start_t - 0.2, y, label, ha="right", va="center", fontsize=7.5,
                bbox=dict(fc="white", ec=color, alpha=0.88, boxstyle="round"))
        ax.axvline(start_t, color=color, ls=":", lw=1, alpha=0.4)

    # K2 区
    ax.axhspan(-0.8, 3.8, xmin=0/16, xmax=0.5/16, color=C_K2, alpha=0.08)
    ax.annotate(f"K2 = 0.5 - 0 = 0.5 s\n（达标 OK）", xy=(0.25, 2.2),
                fontsize=9.5, color=C_K2, ha="center", fontweight="bold",
                bbox=dict(fc="white", ec=C_K2, alpha=0.9, boxstyle="round"))

    # K1 区
    ax.axhspan(-0.8, 3.8, xmin=0.5/16, xmax=15.2/16, color=C_K1, alpha=0.06)
    ax.annotate("K1 = 17.7÷14.7 = 1.20 MW/s\n（达标 OK）", xy=(7.8, 2.2),
                fontsize=9.5, color=C_K1, ha="center", fontweight="bold",
                bbox=dict(fc="white", ec=C_K1, alpha=0.9, boxstyle="round"))

    # K3 标注
    ax.annotate(f"K3 = |70.1−70|÷100 = 0.1% Pn\n（达标 OK）", xy=(15.2, -0.5),
                fontsize=8.5, color=C_K3, ha="right", va="bottom",
                bbox=dict(fc="white", ec=C_K3, alpha=0.9, boxstyle="round"))

    # 通信延迟预算标注
    ax.annotate("通信延迟\n≤200ms", xy=(0.2, 2.5), xytext=(0.05, 3.5),
                arrowprops=dict(arrowstyle="->", color=C_ACC), fontsize=7, color=C_ACC,
                bbox=dict(fc="white", ec=C_ACC, alpha=0.85, boxstyle="round"))

    ax.set_yticks([])
    ax.set_xlabel("时间 (s, 从 T_cmd 起算)")
    ax.set_title("四时刻证据链 (GPS 时标对账)", fontsize=10)
    ax.set_xlim(-2.0, 16.5)
    ax.set_ylim(-1, 4.2)

    # 中图：时标对齐核查表（表格形式）
    ax2 = axes[1]
    ax2.axis("off")

    table_data = [
        ["时刻", "来源", "时标", "偏差", "判定"],
        ["T_cmd", "调度主站", "14:30:00.000", "—", "基准"],
        ["T_recv", "EMS日志", "14:30:00.200", "+200 ms", "OK"],
        ["T_start", "PCS录波", "14:30:00.500", "+500 ms", "OK"],
        ["T_end", "稳态判定", "14:30:15.200", "+15.2 s", "OK"],
        ["T_sample", "调度采样", "14:31:00.000", "+60 s", "K3=0.1%"],
    ]

    table = ax2.table(cellText=table_data, cellLoc="center", loc="center",
                       colWidths=[0.15, 0.18, 0.22, 0.15, 0.12])
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.5)

    # 着色
    for i in range(len(table_data)):
        for j in range(5):
            cell = table[i, j]
            if i == 0:
                cell.set_facecolor(C_GRID)
                cell.set_text_props(color="white", fontweight="bold")
            elif j == 4 and table_data[i][j] == "OK":
                cell.set_facecolor("#d4edda")
                cell.set_text_props(color=C_OK, fontweight="bold")
            elif i == 5:
                cell.set_facecolor("#e8f5e9")

    ax2.set_title("时标对齐核查表 (多方证据溯源)", fontsize=10, y=0.98)

    # 右图：证据类型与保存要求
    ax3 = axes[2]
    ax3.axis("off")

    evidence_items = [
        ("调度指令\n日志截图", "必须", C_PURPLE, "含GPS时标\n指令值+时刻"),
        ("PCS录波\n曲线", "必须", C_OK, "≥4通道\n有功+无功+频率"),
        ("EMS事件\n记录", "必须", C_K3, "含t1/t2/t3\n超时告警"),
        ("稳态区间\n统计数据", "必须", C_K2, "均值+标准差\n≥30周期"),
        ("104报文\n抓包", "建议", C_ACC, "Wireshark\n含时标字段"),
        ("时钟同步\n校验记录", "必须", C_LIMIT, "NTP/GPS\n偏差<10ms"),
    ]

    for i, (name, required, color, detail) in enumerate(evidence_items):
        y = 0.88 - i * 0.15
        req_color = C_LIMIT if required == "必须" else C_ACC
        ax3.text(0.02, y, f"● {name}", fontsize=8, color=color, fontweight="bold",
                 transform=ax3.transAxes)
        ax3.text(0.35, y, f"[{required}]", fontsize=7.5, color=req_color, fontweight="bold",
                 transform=ax3.transAxes)
        ax3.text(0.55, y, detail, fontsize=7, color=C_GRID, transform=ax3.transAxes)

    ax3.set_title("联调证据清单 (6类)", fontsize=10)

    fig.suptitle("AGC 联调四时刻证据链——时标对账 + 多方溯源 + 证据清单  [14:30:00.000 起, 教学示例]",
                 fontsize=12, y=1.03)
    fig.text(0.5, -0.02,
             "K2 = 0.5s OK  |  K1 = 1.20 MW/s OK  |  K3 = 0.1% Pn OK  |  全链路时标闭环可追溯",
             ha="center", fontsize=9, color=C_GRID)

    manifest("ch08_evidence_chain",
             [0.0, 0.2, 0.5, 15.2, 0.5, 1.20, 0.1, 70.0, 52.3, 70.1, 100, 14.5, 30, 60, 200, 300, 10])
    save(fig, "ch08_evidence_chain")


def main():
    fig_step_response_test()
    fig_evidence_chain()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end