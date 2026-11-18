# @AI_GENERATED
"""第 07b 章配图：经济模型对比、SOC 对收入的影响、盈亏平衡（增强版）。

所有参数均为 [教学示例]，不可直接用于现场整定。
"""
from __future__ import annotations

import numpy as np

from _style import (C_CAPACITY, C_MILEAGE, C_DIS, C_CHG, C_GRID, C_LIMIT, C_OK, C_ACC, C_PURPLE,
                    IMG_DIR, manifest, save, plt)


def fig_revenue_contrast():
    """同分不同价：容量 vs 里程模式，三子图——收入对比 + 敏感度曲线 + 成本结构"""
    pn = 100.0  # MW

    # 甲站：容量模式，评分 92，日里程 1200 MW
    score_a = 0.92
    daily_mile_a = 1200
    monthly_mile_a = daily_mile_a * 30
    capacity_price = 10.0
    run_rate = 0.98
    mileage_price = 0.5
    revenue_a_capacity = pn * capacity_price * run_rate * score_a
    revenue_a_mileage_if = monthly_mile_a * mileage_price * score_a

    # 乙站：里程模式，评分 88，日里程 2400 MW
    score_b = 0.88
    daily_mile_b = 2400
    monthly_mile_b = daily_mile_b * 30
    revenue_b_mileage = monthly_mile_b * mileage_price * score_b
    revenue_b_capacity_if = pn * capacity_price * run_rate * score_b

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), width_ratios=[1.05, 1.15, 1])

    # 左图：双站收入并排对比 + 公式拆解
    ax = axes[0]
    x = np.array([1, 3.5])
    width = 0.7
    stations = ["甲站", "乙站"]

    cap_bars = ax.bar(x - width / 2, [revenue_a_capacity, revenue_b_capacity_if], width,
                      color=C_CAPACITY, alpha=0.75, label="按容量结算")
    mile_bars = ax.bar(x + width / 2, [revenue_a_mileage_if, revenue_b_mileage], width,
                       color=C_MILEAGE, alpha=0.85, label="按里程结算")

    for bar, val in zip(cap_bars, [revenue_a_capacity, revenue_b_capacity_if]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 180,
                f"¥{val:.0f}", ha="center", fontsize=9, color=C_CAPACITY, fontweight="bold")
    for bar, val in zip(mile_bars, [revenue_a_mileage_if, revenue_b_mileage]):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 200,
                f"¥{val:.0f}", ha="center", fontsize=9, color="black", fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([f"甲站(92分)\n日{int(daily_mile_a)}MW", f"乙站(88分)\n日{int(daily_mile_b)}MW"], fontsize=9)
    ax.set_ylabel("月收入 (元)")
    ax.set_title("容量 vs 里程模式收入对比", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_ylim(0, max(revenue_b_mileage, revenue_b_capacity_if) * 1.35)

    # 公式拆解标注框
    ax.text(0.5, max(revenue_b_mileage, revenue_b_capacity_if) * 1.18,
            "容量：Pn×单价×投运率×评分系数", fontsize=7.5, color=C_CAPACITY,
            ha="center", bbox=dict(fc="white", ec=C_CAPACITY, alpha=0.85, boxstyle="round"))
    ax.text(3.0, max(revenue_b_mileage, revenue_b_capacity_if) * 1.18,
            "里程：Σ|ΔP|×单价×评分系数", fontsize=7.5, color="black",
            ha="center", bbox=dict(fc="white", ec=C_MILEAGE, alpha=0.85, boxstyle="round"))

    # 中图：日里程 × 评分的收入曲面（等高线式热力图）
    ax2 = axes[1]
    daily_range = np.linspace(400, 4000, 51)
    score_range = np.linspace(0.6, 1.0, 41)
    DD, SS = np.meshgrid(daily_range, score_range)
    RR = DD * 30 * mileage_price * SS  # 月收入矩阵

    # 填充等高线
    cf = ax2.contourf(DD, SS, RR / 1000, levels=15, cmap="YlOrRd", alpha=0.75)
    cs = ax2.contour(DD, SS, RR / 1000, levels=8, colors="black", linewidths=0.6, alpha=0.5)
    ax2.clabel(cs, inline=True, fontsize=7, fmt="%.0fk")

    # 标注甲站/乙站
    ax2.plot(daily_mile_a, score_a, "o", color=C_OK, ms=12, zorder=5, markeredgewidth=1.5, markeredgecolor="white")
    ax2.plot(daily_mile_b, score_b, "s", color=C_PURPLE, ms=12, zorder=5, markeredgewidth=1.5, markeredgecolor="white")
    ax2.annotate(f"甲站\n¥{revenue_a_mileage_if:.0f}",
                 xy=(daily_mile_a, score_a), xytext=(daily_mile_a - 800, score_a - 0.1),
                 arrowprops=dict(arrowstyle="->", color=C_OK, lw=1.5),
                 fontsize=8.5, color=C_OK, fontweight="bold",
                 bbox=dict(fc="white", ec=C_OK, alpha=0.9, boxstyle="round"))
    ax2.annotate(f"乙站\n¥{revenue_b_mileage:.0f}",
                 xy=(daily_mile_b, score_b), xytext=(daily_mile_b + 300, score_b - 0.12),
                 arrowprops=dict(arrowstyle="->", color=C_PURPLE, lw=1.5),
                 fontsize=8.5, color=C_PURPLE, fontweight="bold",
                 bbox=dict(fc="white", ec=C_PURPLE, alpha=0.9, boxstyle="round"))

    # 等收入参考线
    ax2.plot([400, 2200], [1.0, 0.6], ":", color=C_GRID, lw=1.2, alpha=0.6)
    ax2.text(2200, 0.59, "等收入\n¥16,560", fontsize=7, color=C_GRID, ha="center")

    ax2.set_xlabel("日累计里程 (MW)")
    ax2.set_ylabel("综合评分")
    ax2.set_title("日里程 × 评分 → 月收入等高线", fontsize=10)
    cbar = fig.colorbar(cf, ax=ax2, shrink=0.8, pad=0.02)
    cbar.set_label("月收入 (千元)", fontsize=8)
    ax2.set_xlim(400, 4000)
    ax2.set_ylim(0.6, 1.0)

    # 右图：成本结构拆解（里程模式净利润）
    ax3 = axes[2]
    cost_labels = ["里程收入\n(毛)", "电池折损\n0.08元/MW", "固定成本\n50元/天", "PCS损耗\n0.02元/MW", "净利润"]
    gross_b = revenue_b_mileage
    bat_cost_b = monthly_mile_b * 0.08
    fixed_b = 50 * 30
    pcs_cost_b = monthly_mile_b * 0.02
    net_b = gross_b - bat_cost_b - fixed_b - pcs_cost_b

    gross_a = revenue_a_capacity
    bat_cost_a = monthly_mile_a * 0.08
    fixed_a = 50 * 30
    pcs_cost_a = monthly_mile_a * 0.02
    net_a = gross_a - bat_cost_a - fixed_a - pcs_cost_a

    x2 = np.array([1, 3])
    w2 = 0.55
    colors_a = [C_CAPACITY, C_LIMIT, C_ACC, C_GRID, C_OK]
    colors_b = [C_MILEAGE, C_LIMIT, C_ACC, C_GRID, C_OK]

    for i, (name, val_a, val_b) in enumerate(
        [(cost_labels[0], gross_a, gross_b),
         (cost_labels[1], bat_cost_a, bat_cost_b),
         (cost_labels[2], fixed_a, fixed_b),
         (cost_labels[3], pcs_cost_a, pcs_cost_b),
         (cost_labels[4], net_a, net_b)]):
        ax3.bar(x2[0] - w2/2 + i*0.01, val_a, w2/5, bottom=0, color=colors_a[i], alpha=0.7 if i < 4 else 0.95,
                edgecolor="white", linewidth=0.5)

    ax3.bar(x2[0] - w2/2, 0, w2, bottom=0, color="none", edgecolor=C_CAPACITY, linewidth=1.5)
    ax3.bar(x2[1] - w2/2, 0, w2, bottom=0, color="none", edgecolor="black", linewidth=1.5)

    # 乙站堆叠柱状图
    bottom_b = 0
    for i, (c, v) in enumerate(zip(colors_b, [gross_b, -bat_cost_b, -fixed_b, -pcs_cost_b, net_b])):
        if v >= 0:
            ax3.bar(x2[1], v, w2, bottom=bottom_b if i == 0 else 0, color=c, alpha=0.85,
                    edgecolor="white", linewidth=0.5)
            if i == 0:
                bottom_b += v
        else:
            pass

    # 简化为分项柱
    x_pos = np.array([0.72, 2.72])
    bar_w = 0.4
    for xi, (gross, bat, fixed, pcs, net_, color_main, label) in enumerate(
        [(gross_a, bat_cost_a, fixed_a, pcs_cost_a, net_a, C_CAPACITY, "甲站(容量)"),
         (gross_b, bat_cost_b, fixed_b, pcs_cost_b, net_b, C_MILEAGE, "乙站(里程)")]):
        bottom = 0
        vals = [gross, -bat, -fixed, -pcs]
        clrs = [color_main, C_LIMIT, C_ACC, C_GRID]
        names = ["毛收入", "电池折损", "固定成本", "PCS损耗"]
        for v, cl, nm in zip(vals, clrs, names):
            if v >= 0:
                bar = ax3.bar(x_pos[xi], v, bar_w, bottom=bottom, color=cl, alpha=0.85,
                              edgecolor="white", linewidth=0.5)
                if abs(v) > 300:
                    ax3.text(x_pos[xi], bottom + v/2, nm, ha="center", fontsize=6.5, color="white", fontweight="bold")
                bottom += v
            else:
                bar = ax3.bar(x_pos[xi], v, bar_w, bottom=bottom, color=cl, alpha=0.85,
                              edgecolor="white", linewidth=0.5)
                if abs(v) > 300:
                    ax3.text(x_pos[xi], bottom + v/2, nm, ha="center", fontsize=6.5, color="white", fontweight="bold")
                bottom += v
        # 净利润标注
        ax3.text(x_pos[xi], bottom + 200 if net_ > 0 else bottom - 500,
                 f"净利\n¥{net_:.0f}", ha="center", fontsize=9, color=C_OK if net_ > 0 else C_LIMIT, fontweight="bold",
                 bbox=dict(fc="white", ec=C_OK if net_ > 0 else C_LIMIT, alpha=0.9, boxstyle="round"))

        # 净利润率
        margin = net_ / gross * 100 if gross > 0 else 0
        ax3.text(x_pos[xi], bottom + 800 if net_ > 0 else bottom - 1000,
                 f"利润率\n{margin:.0f}%", ha="center", fontsize=8, color=C_PURPLE,
                 bbox=dict(fc="white", ec=C_PURPLE, alpha=0.85, boxstyle="round"))

    ax3.set_xticks(x_pos)
    ax3.set_xticklabels([f"甲站(容量)\n评分 {score_a*100:.0f}", f"乙站(里程)\n评分 {score_b*100:.0f}"], fontsize=8.5)
    ax3.set_ylabel("金额 (元)")
    ax3.set_title("收入-成本=净利润拆解", fontsize=10)
    ax3.axhline(0, color="k", lw=0.8)

    fig.suptitle(f"AGC 辅助服务经济性决策：评分低 ≠ 收入低  [Pn={pn:.0f} MW, 里程单价{mileage_price}元/MW]",
                 fontsize=12, y=1.03)
    fig.text(0.5, -0.02,
             f"容量：{pn}×{capacity_price}×{run_rate}×评分  |  里程：日里程×30×{mileage_price}×评分  |  净利=收入−电池折损−固定成本−PCS损耗",
             ha="center", fontsize=8, color=C_GRID)

    manifest("ch07b_revenue_contrast",
             [pn, score_a, score_b, daily_mile_a, daily_mile_b,
              revenue_a_capacity, revenue_a_mileage_if, revenue_b_mileage, revenue_b_capacity_if,
              capacity_price, mileage_price, 30, net_a, net_b, bat_cost_a, bat_cost_b, 0.08, 50, 0.02,
              gross_a, gross_b, monthly_mile_a, monthly_mile_b])
    save(fig, "ch07b_revenue_contrast")


def fig_soc_economics():
    """SOC 对里程收入的影响：三子图——累计里程 + 累计收入 + SOC×月收入热力图"""
    day_miles = np.arange(1, 31)
    base_daily = 2400  # 乙站基准日里程 MW
    price = 0.5
    score = 0.88

    # SOC=50% 对称
    soc_balanced = np.full(30, base_daily)
    # SOC<20% 前半月上调受限
    soc_low = np.concatenate([np.full(15, base_daily * 0.5),
                              np.full(15, base_daily)])
    # SOC>90% 后半月下调受限
    soc_high = np.concatenate([np.full(10, base_daily),
                               np.full(20, base_daily * 0.5)])
    # SOC 频繁越限（摆动）
    rng = np.random.default_rng(42)
    soc_osc = base_daily * (0.7 + 0.3 * np.sin(np.linspace(0, 6 * np.pi, 30)) + rng.normal(0, 0.08, 30))
    soc_osc = np.clip(soc_osc, base_daily * 0.3, base_daily * 1.05)

    cum_balanced = np.cumsum(soc_balanced)
    cum_low = np.cumsum(soc_low)
    cum_high = np.cumsum(soc_high)
    cum_osc = np.cumsum(soc_osc)

    revenue_balanced = cum_balanced * price * score
    revenue_low = cum_low * price * score
    revenue_high = cum_high * price * score
    revenue_osc = cum_osc * price * score

    loss_low = revenue_balanced[-1] - revenue_low[-1]
    loss_high = revenue_balanced[-1] - revenue_high[-1]
    loss_osc = revenue_balanced[-1] - revenue_osc[-1]

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5), width_ratios=[1.1, 1.1, 0.9])

    # 左图：四条累计里程曲线 + 填充区
    ax = axes[0]
    ax.plot(day_miles, cum_balanced / 1000, color=C_OK, lw=2.5, label="SOC=50% 对称（基准）")
    ax.plot(day_miles, cum_low / 1000, color=C_DIS, lw=2.2, ls="--", label="SOC<20% 上调受限")
    ax.plot(day_miles, cum_high / 1000, color=C_CHG, lw=2.2, ls="-.", label="SOC>90% 下调受限")
    ax.plot(day_miles, cum_osc / 1000, color=C_PURPLE, lw=1.8, ls=":", label="SOC 频繁越限（摆动）")
    ax.fill_between(day_miles, cum_balanced / 1000, cum_low / 1000, alpha=0.08, color=C_DIS)
    ax.fill_between(day_miles, cum_balanced / 1000, cum_osc / 1000, alpha=0.06, color=C_PURPLE)

    # 标注月末差距
    gap_low = cum_balanced[-1] - cum_low[-1]
    gap_high = cum_balanced[-1] - cum_high[-1]
    gap_osc = cum_balanced[-1] - cum_osc[-1]
    ax.annotate(f"SOC<20% 损失\n里程 {gap_low/1000:.0f}k MW\n收入 ¥{gap_low*price*score:.0f}",
                xy=(30, cum_low[-1] / 1000), xytext=(20, cum_low[-1] / 1000 - 12),
                arrowprops=dict(arrowstyle="->", color=C_DIS, lw=1.2),
                fontsize=8, color=C_DIS, bbox=dict(fc="white", ec=C_DIS, alpha=0.9, boxstyle="round"))
    ax.annotate(f"频繁越限\n损失 ¥{gap_osc*price*score:.0f}",
                xy=(30, cum_osc[-1] / 1000), xytext=(21, cum_osc[-1] / 1000 + 5),
                arrowprops=dict(arrowstyle="->", color=C_PURPLE, lw=1.2),
                fontsize=8, color=C_PURPLE, bbox=dict(fc="white", ec=C_PURPLE, alpha=0.9, boxstyle="round"))

    # 半月分界线
    ax.axvline(15, color=C_GRID, ls=":", lw=1, alpha=0.5)
    ax.text(15.3, cum_balanced[-1] / 1000 * 0.88, "半月\n分界", fontsize=7, color=C_GRID)
    ax.axvline(20, color=C_GRID, ls=":", lw=1, alpha=0.5)
    ax.text(20.3, cum_balanced[-1] / 1000 * 0.75, "第20天\nSOC>90%\n限调加剧", fontsize=7, color=C_GRID)

    ax.set_xlabel("日期")
    ax.set_ylabel("累计里程 (×1000 MW)")
    ax.set_title(f"四种 SOC 状态累计里程对比  [日基准 {int(base_daily)} MW]", fontsize=10)
    ax.legend(fontsize=7, loc="upper left")
    ax.set_xlim(1, 30)

    # 中图：累计收入 + 日损失柱状图
    ax2 = axes[1]
    ax2.plot(day_miles, revenue_balanced / 1000, color=C_OK, lw=2.5, label="SOC=50% 对称")
    ax2.plot(day_miles, revenue_low / 1000, color=C_DIS, lw=2.2, ls="--", label="SOC<20%")
    ax2.plot(day_miles, revenue_high / 1000, color=C_CHG, lw=2.2, ls="-.", label="SOC>90%")
    ax2.plot(day_miles, revenue_osc / 1000, color=C_PURPLE, lw=1.8, ls=":", label="频繁越限")

    # 日均损失小柱状图（叠加在右侧轴）
    daily_loss_low = (soc_balanced - soc_low) * price * score / 1000
    daily_loss_high = (soc_balanced - soc_high) * price * score / 1000
    ax2b = ax2.twinx()
    ax2b.bar(day_miles[5:15] - 0.15, daily_loss_low[5:15], 0.3, color=C_DIS, alpha=0.3, label="日损失(低SOC)")
    ax2b.bar(day_miles[20:30] + 0.15, daily_loss_high[20:30], 0.3, color=C_CHG, alpha=0.3, label="日损失(高SOC)")
    ax2b.set_ylabel("日损失 (千元)", fontsize=8, color=C_LIMIT)
    ax2b.tick_params(axis="y", labelcolor=C_LIMIT, labelsize=7)

    # 月末损失标注
    ax2.annotate(f"SOC<20%\n累计损失 ¥{loss_low:.0f}\n({loss_low/revenue_balanced[-1]*100:.0f}%)",
                 xy=(15, revenue_low[14] / 1000), xytext=(6, revenue_low[14] / 1000 + 8),
                 arrowprops=dict(arrowstyle="->", color=C_DIS, lw=1.2),
                 fontsize=8, color=C_DIS, bbox=dict(fc="white", ec=C_DIS, alpha=0.9, boxstyle="round"))
    ax2.annotate(f"SOC>90%\n累计损失 ¥{loss_high:.0f}\n({loss_high/revenue_balanced[-1]*100:.0f}%)",
                 xy=(28, revenue_high[27] / 1000), xytext=(16, revenue_high[27] / 1000 + 6),
                 arrowprops=dict(arrowstyle="->", color=C_CHG, lw=1.2),
                 fontsize=8, color=C_CHG, bbox=dict(fc="white", ec=C_CHG, alpha=0.9, boxstyle="round"))
    ax2.annotate(f"频繁越限\n累计损失 ¥{loss_osc:.0f}\n({loss_osc/revenue_balanced[-1]*100:.0f}%)",
                 xy=(28, revenue_osc[27] / 1000), xytext=(20, revenue_osc[27] / 1000 - 4),
                 arrowprops=dict(arrowstyle="->", color=C_PURPLE, lw=1.2),
                 fontsize=8, color=C_PURPLE, bbox=dict(fc="white", ec=C_PURPLE, alpha=0.9, boxstyle="round"))

    ax2.set_xlabel("日期")
    ax2.set_ylabel("累计收入 (千元)")
    ax2.set_title(f"累计收入 + 日损失  [单价{price}元/MW, 评分{int(score*100)}]", fontsize=10)
    ax2.legend(fontsize=7, loc="upper left")
    ax2.set_xlim(1, 30)

    # 右图：SOC区间 vs 日里程 vs 收入 热力图
    ax3 = axes[2]
    soc_range = np.linspace(10, 95, 18)
    daily_mile_range = np.linspace(500, 3500, 15)
    SSOC, DDAILY = np.meshgrid(soc_range, daily_mile_range)

    # SOC 越接近 50% 越理想，越偏离越受限
    soc_factor = 1.0 - 0.7 * np.abs(SSOC - 50) / 45
    soc_factor = np.clip(soc_factor, 0.3, 1.0)
    effective_daily = DDAILY * soc_factor
    monthly_rev = effective_daily * 30 * price * score / 1000

    cf3 = ax3.contourf(SSOC, DDAILY, monthly_rev, levels=12, cmap="RdYlGn", alpha=0.8)
    cs3 = ax3.contour(SSOC, DDAILY, monthly_rev, levels=6, colors="black", linewidths=0.5, alpha=0.5)
    ax3.clabel(cs3, inline=True, fontsize=7, fmt="%.0fk")

    # 标注四个 SOC 场景
    soc_points = [(50, base_daily, C_OK, "对称 50%"),
                  (15, base_daily * 0.55, C_DIS, "<20%"),
                  (85, base_daily * 0.55, C_CHG, ">90%"),
                  (50, base_daily * 0.78, C_PURPLE, "摆动均值")]
    for sx, dy, cl, lb in soc_points:
        ax3.plot(sx, dy, "o", color=cl, ms=10, zorder=5, markeredgewidth=1.5, markeredgecolor="white")
        ax3.annotate(lb, xy=(sx, dy), xytext=(sx + 12 if sx < 60 else sx - 18, dy + 250),
                    arrowprops=dict(arrowstyle="->", color=cl, lw=1),
                    fontsize=8, color=cl, fontweight="bold")

    # 最佳运行区
    ax3.axvspan(35, 65, color=C_OK, alpha=0.06)
    ax3.text(50, 3300, "最佳\nSOC区\n35~65%", fontsize=7.5, color=C_OK, ha="center",
             bbox=dict(fc="white", ec=C_OK, alpha=0.85, boxstyle="round"))

    ax3.set_xlabel("SOC (%)")
    ax3.set_ylabel("日基准里程 (MW)")
    ax3.set_title("SOC × 日里程 → 月收入 (千元)", fontsize=10)
    cbar3 = fig.colorbar(cf3, ax=ax3, shrink=0.8, pad=0.02)
    cbar3.set_label("月收入 (千元)", fontsize=7.5)

    fig.suptitle("SOC 不平衡对 AGC 里程收入的隐性损失——四场景全方位对比  [教学示例]",
                 fontsize=12, y=1.03)
    fig.text(0.5, -0.02,
             "SOC 偏离 50% → 单方向可调容量受限 → 日里程下降 → 月收入成比例损失  |  SOC<20% 上调受限 / SOC>90% 下调受限",
             ha="center", fontsize=8, color=C_GRID)

    manifest("ch07b_soc_economics",
             [base_daily, price, score, revenue_balanced[-1], revenue_low[-1], revenue_high[-1],
              revenue_osc[-1], loss_low, loss_high, loss_osc, 30, 50, 20, 90, 0.5, 0.08])
    save(fig, "ch07b_soc_economics")


def main():
    fig_revenue_contrast()
    fig_soc_economics()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end