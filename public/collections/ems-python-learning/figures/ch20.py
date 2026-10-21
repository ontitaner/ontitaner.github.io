# @AI_GENERATED
"""第 20 章配图：告警防抖/滞回、控制决策限制链。数据来自 lab/ems_lab/observability.py，数值为 [教学示例]。"""
from __future__ import annotations

import json
import math
import random

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, IMG_DIR, plt, save

from ems_lab.observability import AlarmManager, AlarmRule, Limit, Severity, apply_limit_chain, naive_alarm_count

RULE = AlarmRule("CELL_T_HIGH", "电芯温度高", Severity.MINOR, raise_at=45.0, clear_at=42.0,
                 on_delay_s=5.0, off_delay_s=10.0)


def manifest(name: str, numbers: list[float]) -> None:
    payload = {"_comment": "@AI_GENERATED", "figure": f"{name}.png",
               "numbers": sorted(set(float(n) for n in numbers)),
               "_comment_end": "@AI_GENERATED: end"}
    (IMG_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def noisy_temperature(seed: int = 3):
    # 与 tests/test_observability.py 相同的输入：44～46 ℃ 抖动 10 分钟，然后降到 40 ℃
    rng = random.Random(seed)
    ts = list(range(0, 900))
    vals = [45.0 + 0.8 * math.sin(t / 7) + rng.gauss(0, 0.3) if t < 600 else 40.0 for t in ts]
    return ts, vals


def fig_alarm_debounce():
    ts, vals = noisy_temperature()
    am = AlarmManager([RULE])
    for t, v in zip(ts, vals):
        am.update(t, "舱1/簇3", RULE.code, v)
    rec = am.records[0]
    naive_times = [ts[i + 1] for i in range(len(vals) - 1) if vals[i] <= 45.0 < vals[i + 1]]
    n_naive = naive_alarm_count(vals, 45.0)

    fig, axes = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    ax = axes[0]
    ax.plot(ts, vals, color=C_DIS, lw=1.0, label="电芯最高温度")
    ax.axhline(45, color=C_LIMIT, ls="--", lw=1.2)
    ax.axhline(42, color=C_OK, ls="--", lw=1.2)
    ax.text(700, 45.25, "产生阈值 45 ℃（持续 5 s）", color=C_LIMIT, fontsize=9)
    ax.text(700, 42.25, "恢复阈值 42 ℃（持续 10 s）", color=C_OK, fontsize=9)
    ax.set_ylabel("温度 (℃)")
    ax.set_ylim(38.5, 47.5)
    ax.set_title("同一段温度数据：单阈值告警 vs 延时 + 滞回 + 去重  [教学示例]")
    ax.legend(loc="lower left")

    ax = axes[1]
    ax.vlines(naive_times, 1.6, 2.4, color=C_LIMIT, lw=0.9)
    ax.text(5, 2.62, f"单阈值、无延时：{n_naive} 条“新告警”", color=C_LIMIT, fontsize=9)
    ax.barh(0.8, rec.t_cleared - rec.t_raised, left=rec.t_raised, height=0.5, color=C_ACC, alpha=0.8)
    ax.text(5, 1.2, f"告警管理：1 条（产生 {rec.t_raised} s，出现 {rec.occurrences} 次，恢复 {rec.t_cleared} s）",
            color="k", fontsize=9)
    ax.set_yticks([])
    ax.set_ylim(0.3, 3.0)
    ax.set_xlabel("时间 (s)")
    ax.set_xlim(0, 900)
    save(fig, "ch20_alarm_debounce")
    manifest("ch20_alarm_debounce", [1, 5, 10, 42, 44, 45, 46, 600])


def fig_limit_chain():
    limits = [Limit("可放能力(BMS)", -500, 80), Limit("防倒送", -500, 60), Limit("Ramp", 20, 60)]
    final, steps = apply_limit_chain(100, limits)
    labels = ["请求\n计划曲线"] + [s.name.replace("(", "\n(") for s in steps] + ["下发", "实际\n(下一周期读回)"]
    values = [100] + [s.after_kw for s in steps] + [final, 58]
    colors = [C_GRID] + [C_LIMIT if s.binding else C_OK for s in steps] + [C_DIS, C_CHG]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.bar(range(len(values)), values, color=colors, alpha=0.85, width=0.6)
    for i, (b, v) in enumerate(zip(bars, values)):
        ax.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:g} kW", ha="center", fontsize=10)
    for i, s in enumerate(steps, start=1):
        tag = f"上限 {s.upper_kw:g}\n压下 {s.before_kw - s.after_kw:g} kW" if s.binding else f"区间 [{s.lower_kw:g}, {s.upper_kw:g}]\n未限制"
        ax.text(i, 12, tag, ha="center", fontsize=8.5, color="white" if s.binding else "k")
    ax.set_xticks(range(len(values)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("有功 (kW，放电为正)")
    ax.set_ylim(0, 118)
    ax.grid(axis="x", visible=False)
    ax.set_title("决策审计：目标 100 kW 为什么只发了 60 kW（红色 = 起作用的约束）  [教学示例]")
    save(fig, "ch20_limit_chain")
    manifest("ch20_limit_chain", [20, 58, 60, 80, 100])


def main():
    fig_alarm_debounce()
    fig_limit_chain()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
