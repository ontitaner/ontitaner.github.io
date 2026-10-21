# @AI_GENERATED
"""第 19 章配图：闭环仿真场景结果。曲线全部来自 lab/ems_lab/sim.py，参数为 [教学示例]。"""
from __future__ import annotations

import json

from _style import C_ACC, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save

from ems_lab.sim import (
    INF,
    EmsConfig,
    Fault,
    PlantConfig,
    Scenario,
    first_event_time,
    longest_excursion_s,
    run,
    step_profile,
)

TOL = 10.0
TARGET = -30.0


def manifest(name: str, numbers: list[float]) -> None:
    payload = {"_comment": "@AI_GENERATED", "figure": f"{name}.png",
               "numbers": sorted(set(float(n) for n in numbers)),
               "_comment_end": "@AI_GENERATED: end"}
    (IMG_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _spans_above(t, x, level):
    spans, start = [], None
    for ti, xi in zip(t, x):
        if xi > level and start is None:
            start = ti
        elif xi <= level and start is not None:
            spans.append((start, ti))
            start = None
    if start is not None:
        spans.append((start, t[-1]))
    return spans


def fig_load_drop():
    tr = run(Scenario("负荷突降防倒送", t_end_s=30, load_kw=step_profile(15, 800, 300)))
    exc = longest_excursion_s(tr.t, tr.p_pcc, 0.0, TOL)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8.6), sharex=True, gridspec_kw={"height_ratios": [1, 1.6, 1.6]})

    ax = axes[0]
    ax.plot(tr.t, tr.p_load, color="k", lw=1.6, label="负荷 P_load")
    ax.set_ylabel("负荷 (kW)")
    ax.set_ylim(0, 1000)
    ax.annotate("t=15 s 负荷 800→300 kW", xy=(15, 550), xytext=(17.5, 780), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=C_GRID))
    ax.set_title("场景 S1：负荷突降时的防倒送闭环（电表延迟 0.5 s，PCS 延迟 0.2 s + τ=0.3 s）  [教学示例]")
    ax.legend(loc="lower left")

    ax = axes[1]
    for a, b in _spans_above(tr.t, tr.p_pcc, TOL):
        ax.axvspan(a, b, color=C_LIMIT, alpha=0.12)
    ax.plot(tr.t, tr.p_pcc_seen, color=C_GRID, lw=1.2, ls="--", label="EMS 看到的 P_PCC（延迟+噪声）")
    ax.plot(tr.t, tr.p_pcc, color=C_PURPLE, lw=2, label="并网点真实 P_PCC（送电为正）")
    ax.axhline(0, color=C_LIMIT, lw=1.2)
    ax.axhline(TOL, color=C_LIMIT, lw=0.9, ls=":")
    ax.axhline(TARGET, color=C_OK, lw=1.2, ls="--")
    ax.text(8.2, 18, "倒送限值 0 kW + 容差 10 kW", color=C_LIMIT, fontsize=9)
    ax.text(8.2, TARGET - 38, "控制目标 −30 kW（保留取电裕量）", color=C_OK, fontsize=9)
    ax.text(16.9, 200, f"倒送持续 {exc:.2f} s\n断言：≤ 2 s", color=C_LIMIT, fontsize=9,
            bbox=dict(fc="white", ec=C_LIMIT, alpha=0.9, boxstyle="round,pad=0.3"))
    ax.set_ylabel("P_PCC (kW)")
    ax.set_ylim(-300, 330)
    ax.legend(loc="lower right", fontsize=8.5)

    ax = axes[2]
    ax.plot(tr.t, [600] * len(tr.t), color=C_GRID, lw=1, ls=":", label="策略请求 600 kW")
    ax.step(tr.t, tr.p_cmd, where="post", color=C_ACC, lw=1.6, label="EMS 下发值")
    ax.plot(tr.t, tr.p_bess, color=C_DIS, lw=2, label="PCS 实际 P_BESS（放电为正）")
    ax.annotate("约束收缩：一步压下\n（不受 Ramp 限制）", xy=(15.75, 330), xytext=(18.3, 470), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=C_GRID))
    ax.annotate("主动上升：受 Ramp 100 kW/s\n（每 0.2 s 最多 +20 kW 的台阶）", xy=(8.3, 585), xytext=(9.2, 380),
                fontsize=9, arrowprops=dict(arrowstyle="->", color=C_GRID))
    ax.set_ylabel("P_BESS (kW)")
    ax.set_ylim(0, 700)
    ax.set_xlabel("时间 (s)")
    ax.legend(loc="lower right", fontsize=8.5)
    ax.set_xlim(8, 26)
    save(fig, "ch19_load_drop")
    manifest("ch19_load_drop", [-30, 0.2, 0.3, 0.5, 1.15, 2, 10, 15, 100, 274, 294, 300, 600, 800])


def fig_timestamp_align():
    plant = PlantConfig(meter_delay_s=1.0)
    good = run(Scenario("对齐", t_end_s=30, load_kw=step_profile(15, 800, 300), plant=plant))
    bad = run(Scenario("不对齐", t_end_s=30, load_kw=step_profile(15, 800, 300), plant=plant,
                       ems=EmsConfig(align_timestamps=False)))
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True)
    ax = axes[0]
    ax.plot(bad.t, bad.p_pcc, color=C_LIMIT, lw=1.6, label="不对齐：最新 PCS 功率 − 1 s 前的电表值")
    ax.plot(good.t, good.p_pcc, color=C_OK, lw=2, label="对齐：取电表采样时刻的 PCS 功率")
    ax.axhline(0, color=C_LIMIT, lw=1)
    ax.axhline(TARGET, color=C_GRID, lw=1, ls="--")
    ax.set_ylabel("P_PCC (kW)")
    ax.set_title("同一套控制参数，电表延迟 1 s：净负荷估计的两个量不是同一时刻，闭环就会振荡  [教学示例]")
    ax.legend(loc="lower right", fontsize=8.5)
    ax.set_ylim(-800, 400)
    ax = axes[1]
    ax.plot(bad.t, bad.p_bess, color=C_LIMIT, lw=1.6, label="不对齐：P_BESS")
    ax.plot(good.t, good.p_bess, color=C_OK, lw=2, label="对齐：P_BESS")
    ax.set_ylabel("P_BESS (kW)")
    ax.set_xlabel("时间 (s)")
    ax.set_xlim(12, 30)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylim(min(bad.p_bess) - 80, 800)
    ax.text(18.6, min(bad.p_bess) - 45, "过度修正：放电变成了充电", color=C_LIMIT, fontsize=9)
    ax.legend(loc="upper right", fontsize=8.5)
    save(fig, "ch19_timestamp_align")
    manifest("ch19_timestamp_align", [-30, 0, 1])


def fig_meter_frozen():
    kw = dict(t_end_s=30, load_kw=step_profile(18, 800, 300), faults=[Fault("meter_freeze", 12)])
    good = run(Scenario("冻结检测", **kw))
    bad = run(Scenario("不检测冻结", ems=EmsConfig(meter_frozen_s=INF), **kw))
    t_alarm = first_event_time(good.events, "METER_BAD")
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True)
    ax = axes[0]
    ax.plot(good.t, good.p_pcc_seen, color=C_GRID, lw=1.2, ls="--", label="EMS 看到的 P_PCC（t=12 s 起冻结）")
    ax.plot(bad.t, bad.p_pcc, color=C_LIMIT, lw=1.8, label="不检测冻结：真实 P_PCC")
    ax.plot(good.t, good.p_pcc, color=C_OK, lw=2, label="检测冻结并降级：真实 P_PCC")
    ax.axhline(0, color=C_LIMIT, lw=1)
    for x, txt in [(12, "电表冻结"), (t_alarm, "判冻结\n降级"), (18, "负荷突降")]:
        ax.axvline(x, color=C_GRID, lw=0.8, ls=":")
        ax.text(x + 0.15, 450, txt, fontsize=9, va="top")
    ax.set_ylabel("P_PCC (kW)")
    ax.set_ylim(-1000, 470)
    ax.set_title("场景 S4：电表冻结。冻结检测 3 s 后禁止放电，负荷突降时不再倒送  [教学示例]")
    ax.legend(loc="lower left", fontsize=8.5)
    ax = axes[1]
    ax.plot(bad.t, bad.p_bess, color=C_LIMIT, lw=1.8, label="不检测冻结：P_BESS 一直 600 kW")
    ax.plot(good.t, good.p_bess, color=C_OK, lw=2, label="检测冻结：P_BESS 降到 0")
    ax.set_ylabel("P_BESS (kW)")
    ax.set_xlabel("时间 (s)")
    ax.set_xlim(8, 30)
    ax.set_ylim(-50, 750)
    ax.legend(loc="center right", fontsize=8.5)
    save(fig, "ch19_meter_frozen")
    manifest("ch19_meter_frozen", [0, 3, 4, 12, 18, 300, 600, 800])


def main():
    fig_load_drop()
    fig_timestamp_align()
    fig_meter_frozen()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
