# @AI_GENERATED
"""第 01 章配图：光伏接入后的净负荷特性、储能调节和不同电压等级的输电损耗。

负荷、光伏、储能数据均为 [教学示例]，用于说明净负荷、爬坡和输电损耗的计算方法。
"""
from __future__ import annotations

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, plt, save
from ems_lab.economics import load_curve_stats, max_ramp_up_per_h, net_load, three_phase_line_loss_kw

HOURS = np.arange(24)
LOAD_GW = [32, 31, 30, 29.5, 29.5, 30.5, 33, 36, 39.5, 42, 43.5, 44,
           42.5, 42, 43, 43.5, 44, 45.5, 47.5, 48, 47, 44.5, 40, 35.5]
PV_GW = [0, 0, 0, 0, 0, 0, 0.5, 2.5, 6, 10, 13.5, 16,
         17, 16.5, 14.5, 11, 7, 3, 0.5, 0, 0, 0, 0, 0]
# 储能：5 GW 在 11～14 时充电，17～20 时以 4.25 GW 放电（往返效率 0.85）[教学示例]
P_BESS_GW = [0.0] * 24
for _h in (11, 12, 13, 14):
    P_BESS_GW[_h] = -5.0
for _h in (17, 18, 19, 20):
    P_BESS_GW[_h] = 4.25


def fig_duck_curve():
    net = net_load(LOAD_GW, PV_GW)
    after = [n - p for n, p in zip(net, P_BESS_GW)]  # 放电为正 → 电网要供的净负荷减少
    s_load, s_net, s_after = load_curve_stats(LOAD_GW), load_curve_stats(net), load_curve_stats(after)

    fig, axes = plt.subplots(2, 1, figsize=(9.5, 8.2), sharex=True)

    # ---------- 上图：负荷、光伏、净负荷 ----------
    ax = axes[0]
    ax.fill_between(HOURS, 0, PV_GW, color=C_ACC, alpha=0.35, label="光伏出力")
    ax.plot(HOURS, LOAD_GW, color="k", lw=1.8, marker="o", ms=3, label="用电负荷")
    ax.plot(HOURS, net, color=C_PURPLE, lw=2.6, marker="o", ms=3, label="净负荷 = 负荷 − 光伏")
    ax.annotate(f"夜间低谷 {s_load.valley:g} GW", xy=(3.5, 29.5), xytext=(0.3, 22),
                arrowprops=dict(arrowstyle="->", color=C_GRID), fontsize=9)
    ax.annotate(f"“鸭肚子”：午间净负荷 {s_net.valley:g} GW\n比夜间低谷还低 → 常规机组要压出力",
                xy=(12.5, 25.5), xytext=(4.6, 9.5), arrowprops=dict(arrowstyle="->", color=C_PURPLE),
                fontsize=9, color=C_PURPLE)
    ramp = max_ramp_up_per_h(net, 1.0)
    ax.annotate(f"“鸭脖子”：傍晚爬坡\n最快 {ramp:g} GW/h（16→17 时）", xy=(16.6, 40.5), xytext=(17.4, 24),
                arrowprops=dict(arrowstyle="->", color=C_DIS), fontsize=9, color=C_DIS)
    ax.annotate(f"“鸭头”：晚高峰 {s_net.peak:g} GW\n光伏帮不上忙", xy=(19, 48), xytext=(20.3, 51.5),
                arrowprops=dict(arrowstyle="->", color="k"), fontsize=9, ha="left")
    ax.set_ylabel("功率 (GW)")
    ax.set_ylim(0, 60)
    ax.legend(loc="upper left", ncol=3, fontsize=9)
    ax.set_title("光伏接入后的净负荷特性（鸭形曲线）  [教学示例数据]")

    # ---------- 下图：储能如何改造鸭子 ----------
    ax = axes[1]
    ax.plot(HOURS, net, color=C_PURPLE, lw=1.6, ls="--", marker="o", ms=3, label="净负荷（无储能）")
    ax.plot(HOURS, after, color=C_OK, lw=2.6, marker="o", ms=3, label="净负荷（有储能）")
    ax.fill_between(HOURS, net, after, where=np.array(after) > np.array(net), color=C_CHG, alpha=0.35,
                    interpolate=True, label="储能充电 5 GW（吸收午间光伏）")
    ax.fill_between(HOURS, net, after, where=np.array(after) < np.array(net), color=C_DIS, alpha=0.35,
                    interpolate=True, label="储能放电 4.25 GW（顶晚高峰）")
    ax.annotate(f"峰谷差 {s_net.peak_valley_diff:g} → {s_after.peak_valley_diff:g} GW\n"
                f"最快爬坡 {ramp:g} → {max_ramp_up_per_h(after, 1.0):g} GW/h",
                xy=(0.3, 50.5), fontsize=9.5, va="top",
                bbox=dict(fc="white", ec=C_GRID, boxstyle="round,pad=0.3"))
    ax.annotate(f"21 时成了新高峰 {s_after.peak:g} GW\n放电时段要优化（第 13 章）", xy=(21, 44.5), xytext=(19.2, 26),
                arrowprops=dict(arrowstyle="->", color=C_LIMIT), fontsize=9, color=C_LIMIT)
    ax.set_ylabel("功率 (GW)")
    ax.set_ylim(20, 52)
    ax.set_xlabel("时刻 (h)")
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlim(-0.3, 23.3)
    ax.legend(loc="lower left", ncol=2, fontsize=8.8)
    ax.set_title("加入 5 GW / 20 GWh 储能：中午充、傍晚放")
    save(fig, "ch01_duck_curve")


def fig_line_loss():
    levels = [10, 35, 110, 220, 500]
    p_kw, r = 10_000.0, 1.0
    losses = [three_phase_line_loss_kw(p_kw, u, r) for u in levels]
    currents = [p_kw / (np.sqrt(3) * u) for u in levels]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    colors = [C_DIS, C_ACC, C_OK, C_CHG, C_PURPLE]
    bars = ax.bar([f"{u} kV" for u in levels], losses, color=colors, alpha=0.8)
    ax.set_yscale("log")
    for b, loss, i in zip(bars, losses, currents):
        loss_txt = f"{loss:,.0f}" if loss >= 100 else (f"{loss:.1f}" if loss >= 1 else f"{loss:.2f}")
        pct = loss / p_kw * 100
        pct_txt = f"{pct:.0f}%" if pct >= 1 else f"{pct:.2g}%"
        ax.text(b.get_x() + b.get_width() / 2, loss * 1.35,
                f"{loss_txt} kW\n（占 {pct_txt}）\n电流 {i:.0f} A",
                ha="center", va="bottom", fontsize=8.8)
    ax.set_ylim(0.1, 3e4)
    ax.set_ylabel("线路损耗 (kW，对数刻度)")
    ax.set_xlabel("输电电压（线电压）")
    ax.set_title("输送 10 MW、每相电阻 1 Ω：损耗与电压的平方成反比  [教学示例]")
    ax.grid(axis="x", visible=False)
    save(fig, "ch01_line_loss")


def main():
    fig_duck_curve()
    fig_line_loss()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
