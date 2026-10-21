# @AI_GENERATED
"""第 14 章配图：固定窗口 vs 滑差需量、按剩余时间计算所需放电、削峰前后的并网点功率与需量。

曲线直接调用 lab/ems_lab/demand.py 与 constraints.py 的实现生成，数值均为 [教学示例]。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.constraints import device_interval, export_limit_interval, import_limit_interval, project
from ems_lab.demand import (
    DemandWindowTracker,
    control_target_kw,
    fixed_window_demands,
    required_extra_discharge_kw,
    sliding_window_demands,
)

MIN = 60.0


def manifest(name: str, numbers: list[float]) -> None:
    payload = {"_comment": "@AI_GENERATED", "figure": f"{name}.png",
               "numbers": sorted(set(float(n) for n in numbers)),
               "_comment_end": "@AI_GENERATED: end"}
    (IMG_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def fig_fixed_vs_sliding():
    minutes = np.arange(60)
    p = np.where((minutes >= 7) & (minutes < 22), 2400.0, 1500.0)
    fixed = fixed_window_demands(p, MIN, 15 * MIN)
    sliding = sliding_window_demands(p, MIN, 15 * MIN, step_s=MIN)
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.step(np.append(minutes, 60), np.append(p, p[-1]), where="post", color=C_GRID, lw=1.3,
            label="进口功率 P_import（1 分钟平均）")
    for k, d in enumerate(fixed):
        ax.hlines(d, k * 15, (k + 1) * 15, color=C_CHG, lw=3,
                  label="固定窗口需量（每 15 分钟一个值）" if k == 0 else None)
        ax.text(k * 15 + 7.5, d + 30, f"{d:.0f}", ha="center", va="bottom", color=C_CHG, fontsize=9)
    for k in range(1, 4):
        ax.axvline(k * 15, color=C_CHG, ls=":", lw=1)
    ends = np.arange(15, 15 + len(sliding))
    ax.plot(ends, sliding, color=C_DIS, lw=2.2, marker=".", ms=5,
            label="滑差需量（每 1 分钟算一次最近 15 分钟平均，画在窗口结束时刻）")
    kmax = int(np.argmax(sliding))
    ax.annotate(f"滑差最大 {sliding[kmax]:.0f} kW\n（窗口 {kmax}～{kmax + 15} 分钟正好套住尖峰）",
                xy=(ends[kmax], sliding[kmax]), xytext=(27, 2240), color=C_DIS, fontsize=9,
                arrowprops=dict(arrowstyle="->", color=C_DIS), bbox=dict(fc="white", ec="none", alpha=0.9))
    ax.text(7.7, 2230, f"固定窗口最大 {max(fixed):.0f} kW\n（尖峰被边界切成两半）", color=C_CHG, fontsize=9,
            bbox=dict(fc="white", ec="none", alpha=0.9))
    ax.set_xlabel("时间 (分钟)")
    ax.set_ylabel("功率 / 需量 (kW)")
    ax.set_xlim(0, 60)
    ax.set_ylim(1300, 2900)
    ax.set_xticks(range(0, 61, 5))
    ax.set_title("同一段负荷：固定窗口 vs 滑差需量（15 分钟周期、1 分钟滑差）  [教学示例]", fontsize=10)
    ax.legend(loc="upper right", fontsize=8.5)
    save(fig, "ch14_fixed_vs_sliding")
    manifest("ch14_fixed_vs_sliding", [1, 7, 15, 22, 1500, 1920, 1980, 2400])


def fig_required_discharge():
    """负荷在第 5 分钟从 1700 跳到 2200，目标 1800：第 5 分钟就反应 vs 第 10 分钟才反应。"""
    t = np.arange(0, 15 * 60 + 1, 10.0)
    load = np.where(t < 5 * 60, 1700.0, 2200.0)
    e5 = 1700 * 5 / 60
    early = required_extra_discharge_kw(e5, 2200, 10 * MIN, 1800, 15 * MIN)
    late = required_extra_discharge_kw(e5 + 2200 * 5 / 60, 2200, 5 * MIN, 1800, 15 * MIN)
    imp_early = np.where(t < 5 * 60, load, load - early)
    imp_late = np.where(t < 10 * 60, load, load - late)

    def cum_kwh(x):
        return np.concatenate([[0], np.cumsum(x[:-1] * np.diff(t) / 3600)])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axes[0]
    tm = t / 60
    ax.plot(tm, load, color=C_GRID, lw=1.5, ls="--", label="不控制")
    ax.plot(tm, imp_early, color=C_OK, lw=2.2, label=f"第 5 分钟反应：放电 {early:.0f} kW")
    ax.plot(tm, imp_late, color=C_DIS, lw=2.2, label=f"第 10 分钟才反应：放电 {late:.0f} kW")
    ax.axhline(1800, color=C_LIMIT, ls=":", lw=1.2)
    ax.text(0.2, 1815, "目标 1800 kW", color=C_LIMIT, fontsize=9)
    ax.set_xlabel("周期内时间 (分钟)")
    ax.set_ylabel("进口功率 P_import (kW)")
    ax.set_ylim(1300, 2350)
    ax.set_xlim(0, 15)
    ax.annotate("1850 高于目标也没关系：\n前 5 分钟只有 1700，\n周期平均正好 1800", xy=(12.5, 1850), xytext=(10.3, 1930),
                fontsize=8.5, color=C_OK, arrowprops=dict(arrowstyle="->", color=C_OK))
    ax.legend(loc="lower left", fontsize=8.5)
    ax.set_title("反应越晚，需要的放电功率越大", fontsize=10)

    ax = axes[1]
    budget = 1800 * 15 / 60
    ax.plot(tm, cum_kwh(load), color=C_GRID, lw=1.5, ls="--", label="不控制")
    ax.plot(tm, cum_kwh(imp_early), color=C_OK, lw=2.2, label="第 5 分钟反应")
    ax.plot(tm, cum_kwh(imp_late), color=C_DIS, lw=2.2, label="第 10 分钟反应")
    ax.axhline(budget, color=C_LIMIT, ls=":", lw=1.2)
    ax.text(0.2, budget + 14, f"本周期电量预算 = 1800 × 0.25 h = {budget:.0f} kWh", color=C_LIMIT, fontsize=9)
    ax.plot([0, 15], [0, budget], color=C_LIMIT, lw=0.8, alpha=0.5, label="按 1800 kW 匀速消耗预算")
    ax.set_xlabel("周期内时间 (分钟)")
    ax.set_ylabel("周期内累计进口电量 (kWh)")
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 540)
    ax.legend(loc="lower right", fontsize=8.5)
    ax.set_title("需量 = 周期末累计电量 ÷ 周期：两种反应都刚好用完预算", fontsize=10)
    save(fig, "ch14_required_discharge")
    manifest("ch14_required_discharge", [5, 10, 350, 450, 700, 1700, 1800, 2200])


def simulate_peak_shaving():
    """8:00～12:00，10 s 一步。储能只做需量控制（请求 0），进口上限由需量跟踪器按剩余时间给出。"""
    dt = 10.0
    t = np.arange(8 * 3600, 12 * 3600, dt)
    rng = np.random.default_rng(3)
    h = t / 3600
    load = 1450 + 120 * np.sin((h - 8) * 2.1) + rng.normal(0, 40, t.size)
    load += 750 * ((h >= 9.15) & (h < 9.65))  # 设备启动，持续 30 分钟
    load += 1000 * ((h >= 10.55) & (h < 10.72))  # 短时冲击 10 分钟
    goal = 1800.0
    target = control_target_kw(goal, margin_kw=50)  # 控制目标 1750
    tracker = DemandWindowTracker(window_s=900, target_kw=target)
    p_bess = np.zeros_like(t)
    for k, tk in enumerate(t):
        tracker.update(tk, load[k] - p_bess[k - 1] if k else load[k])  # 电表测到的是上一步执行后的进口
        allowed = tracker.allowed_import_kw()
        cs = [device_interval(available_charge_kw=1000, available_discharge_kw=1000),
              export_limit_interval(load[k], 0.0, 0.0),
              import_limit_interval(load[k], 0.0, allowed)]
        p_bess[k] = project(0.0, cs).final_kw
    imp_before = load
    imp_after = load - p_bess
    return t, load, p_bess, imp_before, imp_after, goal, target


def fig_peak_shaving():
    t, load, p_bess, before, after, goal, target = simulate_peak_shaving()
    d_before = fixed_window_demands(before, 10.0, 900)
    d_after = fixed_window_demands(after, 10.0, 900)
    h = t / 3600
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True, gridspec_kw={"height_ratios": [1.6, 0.9, 1.3]})
    ax = axes[0]
    ax.plot(h, before, color=C_GRID, lw=1.0, label="削峰前 P_import（= 负荷）")
    ax.plot(h, after, color=C_PURPLE, lw=1.3, label="削峰后 P_import")
    ax.axhline(goal, color=C_LIMIT, ls="--", lw=1.2)
    ax.axhline(target, color=C_LIMIT, ls=":", lw=1)
    ax.text(8.02, goal + 25, f"需量目标 {goal:.0f} kW", color=C_LIMIT, fontsize=9)
    ax.text(8.02, target - 30, f"控制目标 {target:.0f} kW（裕度 50）", color=C_LIMIT, fontsize=9, va="top")
    ax.set_ylabel("进口功率 (kW)")
    ax.set_ylim(1100, 2700)
    ax.legend(loc="upper right", fontsize=8.5)
    ax.set_title("需量控制：按周期剩余时间计算允许进口，储能只在需要时放电  [教学示例]", fontsize=10)
    ax.annotate("削峰后的功率可以短时高于目标：\n周期前段用得少，预算还有富余", xy=(9.22, 2050), xytext=(9.75, 2150),
                fontsize=8.5, color=C_PURPLE, arrowprops=dict(arrowstyle="->", color=C_PURPLE), va="center",
                bbox=dict(fc="white", ec="none", alpha=0.9))
    ax.annotate("", xy=(10.64, 1850), xytext=(10.2, 2080), arrowprops=dict(arrowstyle="->", color=C_PURPLE))

    ax = axes[1]
    ax.fill_between(h, 0, p_bess, color=C_DIS, alpha=0.6, label="储能放电 P_BESS")
    ax.set_ylabel("储能 (kW)")
    ax.set_ylim(0, 1100)
    ax.legend(loc="upper left", fontsize=8.5)

    ax = axes[2]
    starts = 8 + np.arange(len(d_before)) * 0.25
    ax.bar(starts + 0.125 - 0.055, d_before, width=0.1, color=C_GRID, alpha=0.7, label="削峰前 15 分钟需量")
    ax.bar(starts + 0.125 + 0.055, d_after, width=0.1, color=C_PURPLE, alpha=0.8, label="削峰后 15 分钟需量")
    ax.axhline(goal, color=C_LIMIT, ls="--", lw=1.2)
    ax.set_ylim(1200, 2450)
    ax.set_ylabel("需量 (kW)")
    ax.set_xlabel("时刻 (h)")
    ax.text(8.02, 2330, f"本段最大需量：削峰前 {max(d_before):.0f} kW → 削峰后 {max(d_after):.0f} kW",
            fontsize=9.5, fontweight="bold")
    ax.legend(loc="upper right", fontsize=8.5)
    ax.set_xticks(np.arange(8, 12.01, 0.5))
    save(fig, "ch14_peak_shaving")
    manifest("ch14_peak_shaving", [50, 1747, 1750, 1800, 2237])
    return max(d_before), max(d_after)


def main():
    fig_fixed_vs_sliding()
    fig_required_discharge()
    fig_peak_shaving()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
