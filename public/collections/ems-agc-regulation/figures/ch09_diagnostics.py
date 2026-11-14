# @AI_GENERATED
"""第 09 章配图：故障归因 + 评分损失 + 时域诊断 + 五类误区（增强版）。

所有参数均为 [教学示例]，不可直接用于现场整定。
"""
from __future__ import annotations

import numpy as np

from _style import (C_K1, C_K2, C_K3, C_GRID, C_LIMIT, C_OK, C_ACC, C_PURPLE, C_CHG,
                    IMG_DIR, manifest, save, plt)


def fig_failure_attribution():
    """四类故障的 K1/K2/K3 得分降幅对比 + 时域波形（诊断决策树已移至正文 Mermaid）。"""
    w1, w2, w3 = 0.30, 0.20, 0.50

    # 故障定义
    base = {"K1": 85, "K2": 83.3, "K3": 66.7, "label": "基准\n正常"}
    f1 = {"K1": 85, "K2": 50, "K3": 66.7, "label": "故障一\n死区过大"}
    f2 = {"K1": 85, "K2": 83.3, "K3": 66.7, "label": "故障二\n单通道断链"}
    f3 = {"K1": 85, "K2": 83.3, "K3": 20, "label": "故障三\nSOC偏高"}
    f4 = {"K1": 85, "K2": 83.3, "K3": 40, "label": "故障四\n公式错误"}

    scenarios = [base, f1, f2, f3, f4]
    n = len(scenarios)

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(15, 6), width_ratios=[1.12, 1])

    # 左图：分组柱状图 + 综合评分
    x = np.arange(n)
    width = 0.22

    bars_k1 = ax.bar(x - width, [s["K1"] for s in scenarios], width, color=C_K1, alpha=0.9, edgecolor="white", label="K1 (w=30%)")
    bars_k2 = ax.bar(x, [s["K2"] for s in scenarios], width, color=C_K2, alpha=0.9, edgecolor="white", label="K2 (w=20%)")
    bars_k3 = ax.bar(x + width, [s["K3"] for s in scenarios], width, color=C_K3, alpha=0.9, edgecolor="white", label="K3 (w=50%)")

    # 综合评分 + 损失归因
    for i, s in enumerate(scenarios):
        k1s = s["K1"]
        k2s = s["K2"]
        k3s = s["K3"]
        total = w1 * k1s + w2 * k2s + w3 * k3s
        baseline_total = w1 * base["K1"] + w2 * base["K2"] + w3 * base["K3"]
        loss = baseline_total - total

        color = C_OK if total >= 80 else C_LIMIT
        ax.text(i, 100, f"{total:.0f} 分", ha="center", fontsize=10, fontweight="bold", color=color)
        if i > 0 and loss > 0.5:
            ax.text(i, 92, f"-{loss:.1f}", ha="center", fontsize=8, color=C_LIMIT)

    ax.axhline(80, color=C_LIMIT, ls="--", lw=1.8, label="合格线 80 分")
    ax.set_xticks(x)
    ax.set_xticklabels([s["label"] for s in scenarios], fontsize=9)
    ax.set_ylabel("单指标得分", fontsize=11)
    ax.set_title("四类故障 K1/K2/K3 得分对比", fontsize=12, pad=12)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax.set_ylim(0, 110)

    # 右图：故障时域波形对比（模拟 60 控制周期）
    t_periods = np.arange(1, 61)
    target = 70.0
    rng = np.random.default_rng(42)

    # 基准正常波形
    p_base = target + rng.normal(0.2, 0.5, 60)
    # 故障一：死区过大，1/3 周期不响应（持平）
    p_dead = np.where(np.arange(60) % 3 == 0, np.full(60, target + 5) * 0 + target,
                      target + rng.normal(0.3, 0.6, 60))
    # 故障三：SOC 偏高，系统性偏向上（充电受限→实际偏高）
    p_soc_high = target + 1.8 + rng.normal(0, 0.8, 60)
    # 故障四：公式错误，偏差放大
    p_formula = target + rng.normal(0.5, 1.2, 60)

    ax2.plot(t_periods, p_base, color=C_OK, lw=2.2, label="基准 正常")
    ax2.plot(t_periods, p_dead, color=C_K2, lw=1.5, ls="--", alpha=0.85, label="故障一 死区(间歇)")
    ax2.plot(t_periods, p_soc_high, color=C_CHG, lw=1.5, ls="-.", alpha=0.85, label="故障三 SOC偏高(系统性)")
    ax2.plot(t_periods, p_formula, color=C_LIMIT, lw=1.5, ls=":", alpha=0.85, label="故障四 公式错误(离散)")

    ax2.axhline(target, color=C_GRID, ls="--", lw=1, alpha=0.5)
    ax2.axhspan(target - 3, target + 3, color=C_OK, alpha=0.06)
    ax2.axhline(target + 3, color=C_LIMIT, ls=":", lw=1, alpha=0.6)
    ax2.axhline(target - 3, color=C_LIMIT, ls=":", lw=1, alpha=0.6)

    # 标注异常特征
    ax2.annotate("间歇不跟踪\n→ K2 恶化", xy=(20, p_dead[19]),
                xytext=(5, target + 8),
                arrowprops=dict(arrowstyle="->", color=C_K2), fontsize=7.5, color=C_K2,
                bbox=dict(fc="white", ec=C_K2, alpha=0.85, boxstyle="round"))
    ax2.annotate("系统性偏高\n→ K3 恶化", xy=(40, p_soc_high[39]),
                xytext=(45, target - 5),
                arrowprops=dict(arrowstyle="->", color=C_CHG), fontsize=7.5, color=C_CHG,
                bbox=dict(fc="white", ec=C_CHG, alpha=0.85, boxstyle="round"))
    ax2.annotate("离散度大\n→ K3 恶化", xy=(55, p_formula[54]),
                xytext=(48, target + 7),
                arrowprops=dict(arrowstyle="->", color=C_LIMIT), fontsize=7.5, color=C_LIMIT,
                bbox=dict(fc="white", ec=C_LIMIT, alpha=0.85, boxstyle="round"))

    ax2.set_xlabel("控制周期", fontsize=11)
    ax2.set_ylabel("出力 (MW)", fontsize=11)
    ax2.set_title("时域波形特征对比  [Pn=100 MW, 60周期]", fontsize=12, pad=12)
    ax2.legend(fontsize=7.5, loc="upper right", framealpha=0.9)
    ax2.set_xlim(0, 60)

    fig.suptitle("AGC 典型故障根因诊断：评分从哪里丢的？评分对比 + 时域波形  [教学示例]",
                 fontsize=13, y=1.02)
    fig.text(0.5, -0.02,
             "诊断逻辑：总分<80 → 定位受损指标(K1/K2/K3) → 检查系统性偏置/离散度/通信/死区 → 根因锁定",
             ha="center", fontsize=8.5, color=C_GRID)

    totals = [w1 * s["K1"] + w2 * s["K2"] + w3 * s["K3"] for s in scenarios]
    manifest("ch09_failure_attribution",
             [w1, w2, w3, 80, 85, 83.3, 66.7, 50, 20, 40, 1.8, 0.5, 1.2] + totals)
    save(fig, "ch09_failure_attribution")


def fig_misconception_scores():
    """五类误区的评分损失 + 雷达图多维对比 + 误区前后对比"""
    w1, w2, w3 = 0.30, 0.20, 0.50

    # 场景定义（误区前→误区后）
    scenarios = [
        ("理想最优", {"K1": 100, "K2": 100, "K3": 100}, None, C_OK),
        ("误区一\n调太快", {"K1": 100, "K2": 100, "K3": 70}, "K3 超调/振荡恶化", C_ACC),
        ("误区二\n死区放宽", {"K1": 100, "K2": 50, "K3": 100}, "1/3 指令不跟踪", C_ACC),
        ("误区三\n容量越大越好", {"K1": 100, "K2": 100, "K3": 100}, "容量不影响 K 值", C_GRID),
        ("误区四\n忽略104链路", {"K1": 100, "K2": 70, "K3": 100}, "通信劣化", C_ACC),
        ("误区五\n自评分≠调度", {"K1": 100, "K2": 100, "K3": 67}, "采样窗口偏移", C_ACC),
    ]

    totals = [w1 * s[1]["K1"] + w2 * s[1]["K2"] + w3 * s[1]["K3"] for s in scenarios]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), width_ratios=[1, 1, 1.1])

    # 左图：评分损失瀑布 + 损失归因
    ax = axes[0]
    labels = [s[0].replace("\n", " ") for s in scenarios]
    x = np.arange(len(labels))
    colors_bar = [C_OK] + [C_LIMIT if t < 80 else C_ACC for t in totals[1:]]

    bars = ax.bar(x, totals, color=colors_bar, alpha=0.85, width=0.55, edgecolor="white")
    ax.axhline(80, color=C_LIMIT, ls="--", lw=1.8, label="合格线 80 分")
    ax.axhline(100, color=C_GRID, ls=":", lw=1, alpha=0.5)

    for bar, (name, scores, detail, clr), total in zip(bars, scenarios, totals):
        color = C_OK if total >= 80 else C_LIMIT
        ax.text(bar.get_x() + bar.get_width() / 2, total + 1.5,
                f"{total:.0f}", ha="center", fontsize=10, fontweight="bold", color=color)
        if detail:
            ax.text(bar.get_x() + bar.get_width() / 2, total - 9,
                    detail, ha="center", fontsize=6.5, color=C_GRID, rotation=90)

    # 损失箭头标注
    for i in range(1, len(scenarios)):
        loss = totals[0] - totals[i]
        if loss > 0.5:
            ax.annotate(f"-{loss:.0f}分", xy=(i, totals[i]),
                       xytext=(i, totals[i] - 20 if totals[i] > 50 else totals[i] + 15),
                       arrowprops=dict(arrowstyle="->", color=C_LIMIT, lw=1),
                       fontsize=7.5, color=C_LIMIT, ha="center")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.5, rotation=15)
    ax.set_ylabel("综合评分")
    ax.set_title("五类误区综合评分损失", fontsize=10)
    ax.set_ylim(0, 115)
    ax.legend(fontsize=7.5)

    # 中图：K1/K2/K3 三维雷达对比（理想 vs 误区）
    ax2 = axes[1]
    categories_radar = ["K1 速率", "K2 响应", "K3 精度"]
    N = len(categories_radar)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    # 理想
    ideal_vals = [100, 100, 100]
    ideal_vals += ideal_vals[:1]
    ax2.fill(angles, ideal_vals, color=C_OK, alpha=0.25, edgecolor=C_OK, lw=2)
    ax2.plot(angles, ideal_vals, "o-", color=C_OK, lw=2.5, label="理想 100分")

    # 误区对比
    for (name, scores, detail, clr), ls in zip(scenarios[1:], ["--", "-.", ":", "--", "-."]):
        vals = [scores["K1"], scores["K2"], scores["K3"]]
        vals += vals[:1]
        ax2.plot(angles, vals, ls, color=clr, lw=1.8, alpha=0.8, label=f"{name[:4]} {totals[scenarios.index((name,scores,detail,clr))]:.0f}分")
        ax2.fill(angles, vals, color=clr, alpha=0.05)

    ax2.set_xticks(angles[:-1])
    ax2.set_xticklabels(categories_radar, fontsize=9)
    ax2.set_ylim(0, 110)
    ax2.set_title("K1/K2/K3 雷达多维对比", fontsize=10)
    ax2.legend(fontsize=6, loc="upper right", ncol=2)

    # 右图：误区前后对比详情表 + 损失占比
    ax3 = axes[2]
    ax3.axis("off")

    # 损失分解表
    table_data = [["误区", "K1", "K2", "K3", "总分", "损失", "主因"]]
    for name, scores, detail, clr in scenarios[1:]:
        k1, k2, k3 = scores["K1"], scores["K2"], scores["K3"]
        tw = w1 * k1 + w2 * k2 + w3 * k3
        loss = totals[0] - tw
        # 找最大损失来源
        losses = [w1*(100-k1), w2*(100-k2), w3*(100-k3)]
        max_idx = np.argmax(losses)
        main_cause = ["K1", "K2", "K3"][max_idx]
        table_data.append([name.replace("\n", ""), f"{k1}", f"{k2}", f"{k3}", f"{tw:.0f}", f"-{loss:.0f}", main_cause])

    table = ax3.table(cellText=table_data, cellLoc="center", loc="center",
                       colWidths=[0.13, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09])
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.scale(1, 1.4)

    # 着色
    for i in range(len(table_data)):
        for j in range(7):
            cell = table[i, j]
            if i == 0:
                cell.set_facecolor(C_GRID)
                cell.set_text_props(color="white", fontweight="bold")
            elif j == 5:
                cell.set_text_props(color=C_LIMIT, fontweight="bold")
            elif j == 6:
                cell.set_text_props(color=C_PURPLE, fontweight="bold")

    ax3.set_title("误区损失分解明细  [华东权重 30/20/50]", fontsize=10, y=0.98)

    # K3 胜负手提示
    ax3.text(0.05, -0.12, "[!] 关键发现：K3 占 50% 权重，K3 损失 = 总分损失的主要来源",
             transform=ax3.transAxes, fontsize=8.5, color=C_LIMIT, fontweight="bold",
             bbox=dict(fc="white", ec=C_LIMIT, alpha=0.9, boxstyle="round"))

    fig.suptitle("AGC 常见认知误区对考核评分的影响——评分+雷达+分解三维全景  [30%/20%/50% 华东权重]",
                 fontsize=12, y=1.03)
    fig.text(0.5, -0.06,
             "K1_score = min(100, K1/K1_req×100)  |  K2_score = 100×(1−K2/30)  |  K3_score = 100×(1−K3/K3_limit)  |  总分 = 0.3K1+0.2K2+0.5K3",
             ha="center", fontsize=8, color=C_GRID)

    manifest("ch09_misconception_scores",
             [w1, w2, w3, 80, 100, 70, 50, 67, 30, 3.0] + totals)
    save(fig, "ch09_misconception_scores")


def main():
    fig_failure_attribution()
    fig_misconception_scores()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end