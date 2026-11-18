# @AI_GENERATED
"""第 16 章配图：AGC 跟踪与教学版考核指标、SOC 耗尽、火储联合。

曲线由 lab/ems_lab/agc.py 算出，参数和指标定义均为 [教学示例]。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.agc import (
    StationModel,
    evaluate_step,
    regulation_capability,
    simulate_thermal_bess,
    simulate_tracking,
)

BESS = StationModel(p_rated_kw=10_000, ramp_kw_per_s=1000, tau_s=1.0, delay_s=2.0, offset_kw=-80, energy_kwh=20_000)
CMDS = [(10, 8000), (60, -6000), (110, 2000)]
BAND = 200  # 判定带 2% Pn [教学示例]


def manifest(name: str, numbers: list[float]) -> None:
    payload = {"_comment": "@AI_GENERATED", "figure": f"{name}.png",
               "numbers": sorted(set(float(n) for n in numbers)),
               "_comment_end": "@AI_GENERATED: end"}
    (IMG_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def fig_tracking():
    r = simulate_tracking(CMDS, BESS, 160, dt=0.1)
    s = evaluate_step(r.t, r.p_act, 10, 60, 0, 8000, BAND)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    ax.step(r.t, r.p_cmd / 1000, where="post", color=C_GRID, ls="--", lw=1.6, label="AGC 设点（调度下发）")
    ax.plot(r.t, r.p_act / 1000, color=C_DIS, lw=2.2, label="储能实际出力（考核点）")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("有功 (MW，放电为正)")
    ax.set_title("10 MW 储能跟踪三次 AGC 设点  [教学示例]")
    ax.legend(loc="lower left")
    ax.axvspan(8, 32, color=C_ACC, alpha=0.12)
    ax.text(20, 9.2, "右图放大", ha="center", fontsize=9)
    ax.set_ylim(-7.5, 10)

    ax = axes[1]
    m = (r.t >= 8) & (r.t <= 32)
    ax.step(r.t[m], r.p_cmd[m] / 1000, where="post", color=C_GRID, ls="--", lw=1.6)
    ax.plot(r.t[m], r.p_act[m] / 1000, color=C_DIS, lw=2.2)
    ax.axhspan((8000 - BAND) / 1000, (8000 + BAND) / 1000, color=C_OK, alpha=0.18)
    ax.text(31.5, 8.35, "目标带 ±0.2 MW", ha="right", fontsize=9, color=C_OK)
    t0, t1, t2 = 10, 10 + s.response_time_s, 10 + s.reach_time_s
    # 响应时间
    ax.annotate("", xy=(t1, 1.2), xytext=(t0, 1.2), arrowprops=dict(arrowstyle="<->", color=C_PURPLE))
    ax.text((t0 + t1) / 2 + 0.3, 1.5, f"响应时间\n{s.response_time_s:.1f} s", ha="center", color=C_PURPLE, fontsize=9)
    ax.axvline(t0, color=C_GRID, lw=0.8, ls=":")
    ax.text(t0 + 0.2, -0.6, "t=10 s 下发", fontsize=8.5, color=C_GRID)
    # 调节速率
    p_l = np.interp(t1, r.t, r.p_act) / 1000
    p_r = np.interp(t2, r.t, r.p_act) / 1000
    ax.plot([t1, t2], [p_l, p_r], color=C_CHG, lw=1.4, ls="--")
    ax.text(13.6, 4.6, f"调节速率\n≈ {s.rate_kw_per_s:.0f} kW/s", color=C_CHG, fontsize=9, ha="center")
    # 调节精度
    ax.annotate(f"调节精度：进入目标带后\n平均偏差 ≈ {s.accuracy_kw:.0f} kW\n（站用电未补偿）", xy=(26, 7.92),
                xytext=(22.5, 4.6), fontsize=9, arrowprops=dict(arrowstyle="->"))
    ax.set_xlim(8, 32)
    ax.set_ylim(-1, 9.3)
    ax.set_xlabel("时间 (s)")
    ax.set_title("第一次设点 0 → 8 MW 的三个指标")
    manifest("ch16_agc_tracking", [0, 0.2, 2, 2.7, 8, 10, 83, 200, 826])
    save(fig, "ch16_agc_tracking")


def fig_soc_depletion():
    model = StationModel(p_rated_kw=10_000, ramp_kw_per_s=1000, tau_s=1.0, delay_s=2.0, energy_kwh=20_000, soc0=0.15)
    r = simulate_tracking([(10, 8000)], model, 1800, dt=1.0)
    up, _ = regulation_capability(0.15, 20_000, 10_000, 10_000, soc_min=0.10, soc_max=0.90, sustain_h=0.25)
    tm = r.t / 60
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True, gridspec_kw={"height_ratios": [1.6, 1]})
    ax = axes[0]
    ax.step(tm, r.p_cmd / 1000, where="post", color=C_GRID, ls="--", lw=1.6, label="AGC 设点 8 MW")
    ax.plot(tm, r.p_act / 1000, color=C_DIS, lw=2.2, label="实际出力")
    ax.fill_between(tm, r.p_act / 1000, r.p_cmd / 1000, where=r.p_cmd - r.p_act > 500, color=C_LIMIT, alpha=0.2,
                    label="跟踪偏差（考核扣分）")
    ax.axhline(up / 1000, color=C_OK, ls="-.", lw=1.5)
    ax.text(1.0, up / 1000 + 0.3, f"如实上送的可调上限 {up / 1000:.0f} MW（持续 15 min 的电量约束）", color=C_OK, fontsize=9)
    ax.set_ylabel("有功 (MW)")
    ax.set_ylim(-0.5, 10)
    ax.set_title("SOC 15% 时仍上送 10 MW 可调能力：调度按 8 MW 调用，约 15 min 后电量耗尽  [教学示例]")
    ax.legend(loc="lower left", bbox_to_anchor=(0.06, 0.04))
    ax = axes[1]
    ax.plot(tm, r.soc * 100, color=C_CHG, lw=2)
    ax.axhline(5, color=C_LIMIT, ls="--", lw=1)
    ax.text(0.5, 6, "SOC 下限 5%：BMS 禁止放电", color=C_LIMIT, fontsize=9)
    ax.set_ylabel("SOC (%)")
    ax.set_xlabel("时间 (min)")
    ax.set_ylim(0, 18)
    manifest("ch16_soc_depletion", [4, 5, 8, 15, 20])
    save(fig, "ch16_soc_depletion")


def fig_thermal_bess():
    cmds = [(10, 180_000)]
    thermal = StationModel(p_rated_kw=300_000, ramp_kw_per_s=100, tau_s=5, delay_s=5, p_min_kw=150_000)
    bess = StationModel(p_rated_kw=9_000, ramp_kw_per_s=3000, tau_s=0.5, delay_s=2, energy_kwh=4_500)
    alone = simulate_tracking(cmds, thermal, 420, dt=0.1, p0_kw=150_000)
    th, p_b, total = simulate_thermal_bess(cmds, thermal, bess, 420, dt=0.1, p0_kw=150_000)
    fig, axes = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True, gridspec_kw={"height_ratios": [1.7, 1]})
    ax = axes[0]
    ax.step(alone.t, alone.p_cmd / 1000, where="post", color=C_GRID, ls="--", lw=1.6, label="AGC 设点 150 → 180 MW")
    ax.plot(alone.t, alone.p_act / 1000, color=C_ACC, lw=2.2, label="火电机组单独跟踪（约 2% Pn/min）")
    ax.plot(th.t, total / 1000, color=C_OK, lw=2.2, label="火储联合出力（机组 + 储能）")
    ax.set_ylabel("考核点有功 (MW)")
    ax.set_ylim(147, 184)
    ax.legend(loc="lower right")
    ax.set_title("火储联合调频：储能先顶上差额，机组慢慢到位后储能退出  [教学示例]")
    ax = axes[1]
    ax.plot(th.t, p_b / 1000, color=C_DIS, lw=2)
    ax.axhline(9, color=C_LIMIT, ls="--", lw=1)
    ax.text(300, 7.6, "储能额定 9 MW", color=C_LIMIT, fontsize=9)
    ax.set_ylabel("储能出力 (MW)")
    ax.set_xlabel("时间 (s)")
    ax.set_ylim(-1, 10.5)
    manifest("ch16_thermal_bess", [2, 9, 150, 180, 300])
    save(fig, "ch16_thermal_bess")


def main():
    fig_tracking()
    fig_soc_depletion()
    fig_thermal_bess()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
