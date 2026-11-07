# @AI_GENERATED
"""第 07 章配图：K1/K2/K3 评分瀑布 + 容量 vs 里程补偿对比（增强版）。

所有参数均为 [教学示例]，不可直接用于现场整定。
"""
from __future__ import annotations

import numpy as np

from _style import (C_K1, C_K2, C_K3, C_CAPACITY, C_MILEAGE, C_GRID, C_LIMIT, C_OK, C_ACC, C_PURPLE,
                    IMG_DIR, manifest, save, plt)


def fig_scoring_waterfall():
    """K1/K2/K3 三指标加权综合评分：瀑布 + 得分矩阵 + 区域差异"""
    pn = 100.0

    k1_raw, k1_req = 0.85, 1.0
    k2_raw, k2_limit = 5.0, 30.0
    k3_raw, k3_limit = 2.0, 3.0

    w_east = [0.30, 0.20, 0.50]  # 华东
    w_ne = [0.35, 0.25, 0.40]     # 东北
    w_shanxi = [0.30, 0.20, 0.50] # 山西（同华东）

    k1_score = min(100, 100 * k1_raw / k1_req)
    k2_score = max(0, 100 * (1 - k2_raw / k2_limit))
    k3_score = max(0, 100 * (1 - k3_raw / k3_limit))

    raw_scores = [k1_score, k2_score, k3_score]

    def calc_total(w):
        return w[0] * k1_score + w[1] * k2_score + w[2] * k3_score

    totals = [calc_total(w) for w in [w_east, w_ne, w_shanxi]]

    fig, axes = plt.subplots(1, 3, figsize=(14, 5.5), width_ratios=[1.1, 0.9, 1])

    # 左图：三指标分数堆叠瀑布（含加权过程）
    ax = axes[0]
    categories = ["K1", "K2", "K3"]
    scores_raw = [k1_score, k2_score, k3_score]
    scores_w = [k1_score * w_east[0], k2_score * w_east[1], k3_score * w_east[2]]

    x = np.arange(3)
    w_bar = 0.35

    b1 = ax.bar(x - w_bar / 2, scores_raw, w_bar, color=[C_K1, C_K2, C_K3], alpha=0.35,
                edgecolor="white", label="原始得分")
    b2 = ax.bar(x + w_bar / 2, scores_w, w_bar, color=[C_K1, C_K2, C_K3], alpha=0.85,
                edgecolor="white", label=f"加权后（{w_east[0]:.0%}/{w_east[1]:.0%}/{w_east[2]:.0%})")

    for i, (raw, wv) in enumerate(zip(scores_raw, scores_w)):
        ax.text(i - w_bar / 2, raw + 1, f"{raw:.0f}", ha="center", fontsize=9, color=C_GRID, fontweight="bold")
        ax.text(i + w_bar / 2, wv + 1, f"{wv:.1f}", ha="center", fontsize=9, color="black", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([f"K1\n{K1_WARNING_TIP}", f"K2\n{(1-k2_raw/k2_limit)*100:.0f}%", f"K3\n{(1-k3_raw/k3_limit)*100:.0f}%"], fontsize=9)
    ax.set_ylabel("得分")
    ax.set_title(f"K1/K2/K3 单项得分  [教学示例]", fontsize=10)
    ax.legend(fontsize=7.5)
    ax.set_ylim(0, 100)

    # 中图：三个区域的综合评分对比
    ax2 = axes[1]
    regions = ["华东\nw=30/20/50\n合格≥80", "东北\nw=35/25/40\n合格≥75", "山西\nw=30/20/50\n合格≥80"]
    colors_bar = [C_LIMIT if t < 80 else C_OK for t in totals]
    colors_bar[1] = C_OK if totals[1] >= 75 else C_LIMIT
    bars = ax2.bar(regions, totals, color=colors_bar, alpha=0.85, width=0.55, edgecolor="white")

    for bar, val, region, w in zip(bars, totals, regions, [w_east, w_ne, w_shanxi]):
        color = C_OK if ((w == w_ne and val >= 75) or (w != w_ne and val >= 80)) else C_LIMIT
        ax2.text(bar.get_x() + bar.get_width() / 2, val + 1.5,
                 f"{val:.1f} 分\n{'[OK] 合格' if color == C_OK else '[NG] 不合格'}",
                 ha="center", fontsize=10, color=color, fontweight="bold")

    ax2.axhline(80, color=C_LIMIT, ls="--", lw=1.5, label="华东/山西合格线 80")
    ax2.axhline(75, color=C_ACC, ls=":", lw=1.5, label="东北合格线 75")
    ax2.set_ylabel("综合评分")
    ax2.set_title("三区域综合评分对比", fontsize=10)
    ax2.legend(fontsize=7.5, loc="lower right")
    ax2.set_ylim(0, 85)

    # 右图：权重分配饼图 + 各区域标注
    ax3 = axes[2]
    wedges, texts, autotexts = ax3.pie(
        w_east, labels=["K1 速率", "K2 响应", "K3 精度"],
        colors=[C_K1, C_K2, C_K3],
        autopct="%1.0f%%", startangle=90, explode=(0.04, 0.04, 0.06),
        textprops={"fontsize": 9}, pctdistance=0.6
    )
    for at in autotexts:
        at.set_fontweight("bold")
    ax3.set_title("华东/山西权重 30/20/50", fontsize=10)

    # 关键提示框
    ax3.text(-1.5, -1.5, f"[!] K3 是胜负手\nK1+K2 拉满 = 50 分\nK3 占 50% 权重\n\nK3={k3_raw}% → 得分仅 {k3_score:.0f}\n加权 = {k3_score*w_east[2]:.1f} 分",
             fontsize=8.5, color=C_LIMIT,
             bbox=dict(fc="white", ec=C_LIMIT, alpha=0.9, boxstyle="round"),
             ha="center")

    fig.suptitle(f"AGC K1/K2/K3 考核评分模型（K1={k1_raw} MW/s, K2={k2_raw}s, K3={k3_raw}%）  [Pn={pn:.0f} MW]",
                 fontsize=12, y=1.03)
    fig.text(0.5, -0.01,
             f"K1_score=min(100,{k1_raw}/{k1_req}×100)={k1_score:.0f}  |  K2_score=100×(1−{k2_raw}/{k2_limit})={k2_score:.0f}  |  K3_score=100×(1−{k3_raw}/{k3_limit})={k3_score:.0f}  |  华东综合={totals[0]:.1f}",
             ha="center", fontsize=8.5, color=C_GRID)

    manifest("ch07_scoring_waterfall",
             [pn, k1_raw, k1_req, k2_raw, k2_limit, k3_raw, k3_limit,
              k1_score, k2_score, k3_score, totals[0], totals[1], totals[2],
              0.30, 0.20, 0.50, 0.35, 0.25, 0.40, 80, 75])
    save(fig, "ch07_scoring_waterfall")

    return k1_score, k2_score, k3_score, totals[0]


# Placeholder - computed in main
K1_WARNING_TIP = "速率"


def _set_warning_str(k1, k2, k3):
    global K1_WARNING_TIP
    K1_WARNING_TIP = f"{k1:.0f}分"


def fig_compensation_compare(k1_score, k2_score, k3_score, total_score):
    """容量 vs 里程补偿：收入对比 + 评分敏感度 + 盈亏平衡分析"""
    pn = 100.0
    capacity_price = 10.0
    run_rate = 0.98
    score_capacity = total_score / 100  # 80分
    score_mileage_example = 0.95

    revenue_capacity = pn * capacity_price * run_rate * score_capacity

    mileage_monthly = 50000.0
    mileage_price = 0.5
    revenue_mileage = mileage_monthly * mileage_price * score_mileage_example

    fig, axes = plt.subplots(1, 3, figsize=(14, 5.5), width_ratios=[1, 1.15, 1])

    # 左：收入并排柱状图
    ax = axes[0]
    modes = ["容量补偿\n华东/山西", "里程补偿\n东北"]
    revenues = [revenue_capacity, revenue_mileage]
    colors_bar = [C_CAPACITY, C_MILEAGE]
    bars = ax.bar(modes, revenues, color=colors_bar, alpha=0.85, width=0.45, edgecolor="white")
    for bar, val in zip(bars, revenues):
        ax.text(bar.get_x() + bar.get_width() / 2, val + max(revenues) * 0.02,
                f"¥{val:,.0f}", ha="center", fontsize=11, fontweight="bold",
                color=C_CAPACITY if val == revenue_capacity else "black")

    ax.annotate(f"¥{revenue_capacity:.0f} ≈ {pn:.0f}×{capacity_price}×{run_rate}×{score_capacity:.2f}",
                xy=(0, revenue_capacity), xytext=(0.6, revenue_capacity * 0.3),
                arrowprops=dict(arrowstyle="->", color=C_CAPACITY), fontsize=7.5, color=C_CAPACITY)
    ax.annotate(f"¥{revenue_mileage:.0f} ≈ {mileage_monthly:.0f}×{mileage_price}×{score_mileage_example:.2f}",
                xy=(1, revenue_mileage), xytext=(0.3, revenue_mileage * 0.5),
                arrowprops=dict(arrowstyle="->", color=C_MILEAGE), fontsize=7.5, color="black")
    ax.set_ylabel("月收入 (元)")
    ax.set_title(f"两种模式月收入  [Pn={pn:.0f} MW]", fontsize=10)
    ax.set_ylim(0, max(revenues) * 1.25)

    # 中：评分敏感度曲线
    ax2 = axes[1]
    scores = np.linspace(60, 100, 101)
    cap_income = pn * capacity_price * run_rate * scores / 100
    mile_base = mileage_monthly * mileage_price

    # 里程模式下，不同月里程量
    for monthly_mw, color, label in [
        (30000, C_LIMIT, "月 3 万 MW（低活跃）"),
        (50000, C_MILEAGE, "月 5 万 MW（示例）"),
        (70000, C_OK, "月 7 万 MW（高活跃）"),
    ]:
        mile_income = monthly_mw * mileage_price * scores / 100
        ax2.plot(scores, mile_income, color=color, lw=2.2, label=label)

    ax2.plot(scores, cap_income, color=C_CAPACITY, lw=2.5, ls="--", label="容量补偿")
    ax2.axvline(80, color=C_LIMIT, ls="--", lw=1.2, alpha=0.6)
    ax2.text(80.5, cap_income[20], "合格线", fontsize=7.5, color=C_LIMIT)

    # 标注：评分对收入的杠杆效应
    ax2.annotate("评分从 80→90 分\n里程收入涨 ¥{:.0f}".format(mileage_monthly*mileage_price*0.1),
                 xy=(85, mileage_monthly*mileage_price*0.85),
                 xytext=(70, mileage_monthly*mileage_price*0.55),
                 arrowprops=dict(arrowstyle="->", color=C_ACC),
                 fontsize=7.5, color=C_ACC,
                 bbox=dict(fc="white", ec=C_ACC, alpha=0.85))

    ax2.set_xlabel("综合评分")
    ax2.set_ylabel("月收入 (元)")
    ax2.set_title("评分 × 收入敏感度", fontsize=10)
    ax2.legend(fontsize=7, loc="upper left")
    ax2.set_xlim(58, 102)

    # 右：不同评分下的日里程盈亏平衡点
    ax3 = axes[2]
    daily_miles = np.linspace(200, 4000, 201)
    battery_cost_per_mw = 0.08  # 元/MW（电池折损）
    opportunity_cost_per_day = 50  # 元/天（固定成本）

    for sc, color, label in [(1.00, C_OK, "100分"), (0.90, C_ACC, "90分"), (0.80, C_LIMIT, "80分")]:
        revenue = daily_miles * 30 * mileage_price * sc
        cost = daily_miles * 30 * battery_cost_per_mw + opportunity_cost_per_day * 30
        profit = revenue - cost
        ax3.plot(daily_miles, profit, color=color, lw=2.2, label=label)
        # 找盈亏平衡点
        cross_idx = np.argmax(profit >= 0)
        if cross_idx > 0:
            ax3.axvline(daily_miles[cross_idx], color=color, ls=":", lw=1, alpha=0.5)
            ax3.text(daily_miles[cross_idx] + 30, 100,
                     f"{daily_miles[cross_idx]:.0f} MW", fontsize=7, color=color, rotation=90)

    ax3.axhline(0, color="k", lw=0.8)
    ax3.fill_between(daily_miles, -2000, 0, alpha=0.04, color=C_LIMIT)
    ax3.text(2000, -500, "亏损区", fontsize=8, color=C_LIMIT, ha="center")

    ax3.set_xlabel("日累计里程 (MW)")
    ax3.set_ylabel("月净利润 (元)")
    ax3.set_title("盈亏平衡分析（含电池折损）", fontsize=10)
    ax3.legend(fontsize=7.5)
    ax3.set_xlim(200, 4000)
    ax3.set_ylim(-1200, 3500)

    fig.suptitle(f"AGC 补偿经济模型对比  [Pn={pn:.0f} MW, 容量单价 {capacity_price}元/MW·月, 里程单价 {mileage_price}元/MW]",
                 fontsize=12, y=1.02)
    fig.text(0.5, -0.02,
             "容量：月收入 = P_avail × 单价 × 投运率 × 评分系数  |  里程：月收入 = Σ|ΔP| × 单价 × 评分系数  |  盈亏 = 收入 − 电池折损",
             ha="center", fontsize=8, color=C_GRID)

    manifest("ch07_compensation_compare",
             [pn, capacity_price, run_rate, score_capacity, score_mileage_example,
              revenue_capacity, revenue_mileage, mileage_monthly, mileage_price, 0.08, 50, 30])
    save(fig, "ch07_compensation_compare")


def main():
    _set_warning_str(85, 83.3, 33.3)
    k1 = 85
    k2 = 83.3
    k3 = 33.3
    total = 58.9

    fig_scoring_waterfall()
    fig_compensation_compare(k1, k2, k3, total)


if __name__ == "__main__":
    main()
# @AI_GENERATED: end