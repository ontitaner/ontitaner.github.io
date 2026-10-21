# @AI_GENERATED
"""第 00 章配图：一座工商业光储电站的 24 小时。

电价时段、负荷、光伏和策略规则均为 [教学示例]，用于把后续章节的功能放进同一个时间轴。
"""
from __future__ import annotations

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, plt, save

DT_H = 1 / 60  # 1 分钟
CAP_KWH = 4000.0
P_MAX = 1000.0
SOC_MIN, SOC_MAX = 0.10, 0.90
DEMAND_LIMIT = 1800.0  # 需量目标（进口功率上限）
ETA = 0.95  # 单向效率 [教学示例]

# 分时电价（元/kWh）[教学示例，非任何地区真实电价]
PERIODS = [(0, 8, "谷", 0.30), (8, 12, "峰", 1.10), (12, 17, "平", 0.65), (17, 21, "峰", 1.10), (21, 24, "平", 0.65)]


def price_at(h: float) -> tuple[str, float]:
    for a, b, name, p in PERIODS:
        if a <= h < b:
            return name, p
    return PERIODS[-1][2], PERIODS[-1][3]


def profiles(h: np.ndarray):
    load = 700 + 800 * ((h > 7.5) & (h < 19)) + 150 * np.sin(h / 24 * 6 * np.pi)
    spike = (h >= 4.5) & (h < 5.25)
    load = load + 1100 * spike  # 凌晨 4:30 夜班一台大设备启动，恰好撞上储能在充电
    pv = 2300 * np.clip(np.sin((h - 6.5) / 12 * np.pi), 0, None) ** 1.5
    return load, pv


def run_day():
    """按优先级执行的简化规则：SOC 保护 > 防倒送 > 需量 > 峰谷套利。"""
    h = np.arange(0, 24, DT_H)
    load, pv = profiles(h)
    soc = 0.15
    p_bess = np.zeros_like(h)
    pv_used = pv.copy()
    socs = np.zeros_like(h)
    for k, hh in enumerate(h):
        net = load[k] - pv[k]  # 不含储能时从电网取的功率（负值 = 光伏有富余）
        period, _ = price_at(hh)
        # 峰谷套利：谷时充电、峰时放电（放电不超过净负荷，否则会倒送）
        if period == "谷":
            p = -600.0
        elif period == "峰":
            p = min(P_MAX, max(net, 0.0))
        else:
            p = 0.0
        # 防倒送：光伏有富余时，储能吸收余电
        if net < 0:
            p = max(-P_MAX, net)
        # 需量控制：从电网取电不能超过目标（充电也会推高取电）
        if net - p > DEMAND_LIMIT:
            p = min(P_MAX, net - DEMAND_LIMIT)
        # SOC 保护：到下限不再放电、到上限不再充电
        if p > 0 and soc <= SOC_MIN:
            p = 0.0
        if p < 0 and soc >= SOC_MAX:
            p = 0.0
        # 储能吸收不了的余电：光伏限发兜底（仍然不倒送）
        if net - p < 0:
            pv_used[k] = load[k] - p
        p_bess[k] = p
        soc += (-p / ETA if p > 0 else -p * ETA) * DT_H / CAP_KWH
        socs[k] = soc
    pcc_import = load - pv_used - p_bess
    return h, load, pv, pv_used, p_bess, pcc_import, socs


def fig_day():
    h, load, pv, pv_used, p_bess, imp, soc = run_day()
    fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True,
                             gridspec_kw={"height_ratios": [0.8, 2, 1.5, 1.2]})
    ax = axes[0]
    colors = {"谷": C_CHG, "平": C_GRID, "峰": C_DIS}
    for a, b, name, p in PERIODS:
        ax.bar((a + b) / 2, p, width=b - a, color=colors[name], alpha=0.55, edgecolor="white")
        ax.text((a + b) / 2, p + 0.05, f"{name} {p:.2f}", ha="center", fontsize=9)
    ax.set_ylabel("电价\n(元/kWh)")
    ax.set_ylim(0, 1.45)
    ax.set_title("一座工商业光储电站的一天（储能 1 MW / 4 MWh）  [全部为教学示例数据]")

    ax = axes[1]
    ax.plot(h, load, color="k", lw=1.6, label="工厂负荷")
    ax.fill_between(h, 0, pv_used, color=C_ACC, alpha=0.35, label="光伏实际发电")
    ax.fill_between(h, pv_used, pv, color=C_ACC, alpha=0.12, hatch="//", edgecolor=C_ACC, lw=0,
                    label="光伏限发（储能已满）")
    ax.plot(h, imp, color=C_PURPLE, lw=2, label="并网取电 P_import（取电为正）")
    ax.axhline(DEMAND_LIMIT, color=C_LIMIT, ls="--", lw=1)
    ax.text(0.2, DEMAND_LIMIT + 60, "需量目标 1800 kW", color=C_LIMIT, fontsize=9)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("功率 (kW)")
    ax.legend(loc="upper right", ncol=2, fontsize=8.5)
    ax.set_ylim(-150, 3300)

    ax = axes[2]
    ax.fill_between(h, 0, p_bess, where=p_bess > 0, color=C_DIS, alpha=0.6, label="放电 (P>0)")
    ax.fill_between(h, 0, p_bess, where=p_bess < 0, color=C_CHG, alpha=0.6, label="充电 (P<0)")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("储能功率 (kW)")
    ax.legend(loc="lower right", fontsize=8.5)
    ax.set_ylim(-1250, 1250)

    ax = axes[3]
    ax.plot(h, soc * 100, color=C_OK, lw=2.2)
    ax.axhline(SOC_MIN * 100, color=C_LIMIT, ls=":", lw=1)
    ax.axhline(SOC_MAX * 100, color=C_LIMIT, ls=":", lw=1)
    ax.set_ylabel("SOC (%)")
    ax.set_ylim(0, 100)
    ax.set_xlabel("时刻 (h)")
    ax.set_xticks(range(0, 25, 2))

    # (横坐标, 文字, 放在上方?)
    notes = [
        (2.0, "① 谷时充电\n电价低", False),
        (5.0, "② 夜班设备启动\n减小充电保需量", True),
        (8.8, "③ 早峰放电\n替代高价电", True),
        (12.0, "④ 光伏富余\n先充电防倒送", False),
        (14.2, "④′ SOC 到上限\n光伏限发兜底", True),
        (19.0, "⑤ 晚峰放电\n到 SOC 下限停", True),
    ]
    for x, text, top in notes:
        axes[2].text(x, 1200 if top else -1200, text, ha="center", va="top" if top else "bottom", fontsize=8.5,
                     bbox=dict(fc="white", ec=C_GRID, alpha=0.92, boxstyle="round,pad=0.25"))
    save(fig, "ch00_day_profile_v2")


def main():
    fig_day()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
