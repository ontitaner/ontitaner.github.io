# @AI_GENERATED
"""ch07b AGC 辅助服务经济性决策 — 容量 vs 里程补偿 + 电池折损 lab。

复现正文 07b 章的核心数：
    甲站（里程模式，92 分，日里程 1200 MW）→ 月收入 16560 元
    乙站（里程模式，88 分，日里程 2400 MW）→ 月收入 31680 元
    电池一次全循环折损 = 8000 万 ÷ 6000 ≈ 13300 元
运行方式: python lab/examples/ch07b_economics.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from ems_lab.agc_core import (  # noqa: E402
    PN, capacity_revenue, mileage_revenue,
    CAP_PRICE_YUAN_PER_MW_MONTH, MILE_PRICE_YUAN_PER_MW, AVAILABILITY_RATE,
)

DAYS_PER_MONTH = 30.0
BATTERY_MWH = 100.0
BATTERY_YUAN_PER_WH = 0.8
CYCLE_LIFE = 6000.0
FULL_CYCLE_COST = BATTERY_YUAN_PER_WH * BATTERY_MWH * 1e6 / CYCLE_LIFE  # ≈13333 元


def revenue_capacity(score: float, daily_mileage_mw: float = 0.0) -> float:
    """容量模式月收入：与动作量无关，只看容量×单价×投运率×评分系数。"""
    return capacity_revenue(score)


def revenue_mileage(score: float, daily_mileage_mw: float) -> float:
    """里程模式月收入：日里程 × 30 天 × 单价 × 评分系数。"""
    return mileage_revenue(score, daily_mileage_mw * DAYS_PER_MONTH)


def cycle_cost(daily_mwh: float) -> float:
    """日电池折损 = 一次全循环折损 × 日等效循环次数。"""
    return FULL_CYCLE_COST * (daily_mwh / BATTERY_MWH)


def net_margin(score: float, daily_mileage_mw: float, daily_mwh: float) -> float:
    """里程模式日净收入 = 日收入 − 日折损。"""
    return revenue_mileage(score, daily_mileage_mw) / DAYS_PER_MONTH - cycle_cost(daily_mwh)


def breakeven_mileage(score: float, daily_mwh: float) -> float:
    """里程模式盈亏平衡日里程（MW）：日收入 = 日折损 时的里程。"""
    unit = MILE_PRICE_YUAN_PER_MW * score / 100.0
    return cycle_cost(daily_mwh) / unit if unit > 0 else float("inf")


def test():
    assert abs(FULL_CYCLE_COST - 13333.33) < 1.0, "全循环折损应 ≈13333 元"
    assert abs(cycle_cost(10) - 1333.33) < 1.0, "10 MWh 日折损应 ≈1333 元"

    assert abs(revenue_capacity(92) - 902.0) < 1.0, "92 分容量月收入应 ≈902"
    assert abs(revenue_mileage(92, 1200) - 16560.0) < 1.0, "甲站里程月收入应 16560"
    assert abs(revenue_mileage(88, 2400) - 31680.0) < 1.0, "乙站里程月收入应 31680"

    assert net_margin(90, 400, 20) < 0, "低里程单价下日净收入应为负"
    print("  ✓ ch07b 经济性自测通过")


def main():
    print("=" * 70)
    print("ch07b AGC 容量 vs 里程补偿经济决策（PN=100MW 教学基线）")
    print("=" * 70)

    print(f"\n【参数】容量单价 {CAP_PRICE_YUAN_PER_MW_MONTH:.0f} 元/MW·月"
          f"（投运率 {AVAILABILITY_RATE:.2f}）  里程单价 {MILE_PRICE_YUAN_PER_MW:.1f} 元/MW")
    print(f"        电池 {BATTERY_MWH:.0f} MWh × {BATTERY_YUAN_PER_WH:.1f} 元/Wh"
          f" ÷ {CYCLE_LIFE:.0f} 次 = 全循环折损 {FULL_CYCLE_COST:.0f} 元")

    print("\n【① 同分不同价：评分是折扣率，动作量才是基数】")
    print(f"  甲站：里程模式 92 分，死区 0.3 MW，日里程 1200 MW")
    a = revenue_mileage(92, 1200)
    print(f"        月收入 = 1200×{DAYS_PER_MONTH:.0f}×{MILE_PRICE_YUAN_PER_MW:.1f}"
          f"×0.92 = {a:.0f} 元")
    print(f"  乙站：里程模式 88 分，死区 0.1 MW，日里程 2400 MW")
    b = revenue_mileage(88, 2400)
    print(f"        月收入 = 2400×{DAYS_PER_MONTH:.0f}×{MILE_PRICE_YUAN_PER_MW:.1f}"
          f"×0.88 = {b:.0f} 元")
    print(f"  对比：乙站评分低 4 分，收入却是甲站的 {b/a:.1f} 倍"
          f"（{b:.0f} vs {a:.0f}）——2 倍的盘子打八八折仍更大")
    print(f"  补充：若同站按容量结算，92 分仅 {revenue_capacity(92):.0f} 元、"
          f"88 分仅 {revenue_capacity(88):.0f} 元")
    print(f"        → 先选对结算模式（量级差 {a/revenue_capacity(92):.0f} 倍），再谈评分")

    print("\n【② 里程收入对日里程与评分的敏感度（月收入，元）】")
    hdr = f"{'日里程(MW)':>10}" + "".join(f"{s:>9}分" for s in (80, 88, 92, 96))
    print(hdr)
    print("-" * len(hdr))
    for m in (600, 1200, 1800, 2400, 3000):
        row = f"{m:>10}"
        for s in (80, 88, 92, 96):
            row += f"{revenue_mileage(s, m):>10.0f}"
        print(row)

    print("\n【③ 电池折损：日净收入（里程单价 0.5 元/MW）】")
    hdr3 = f"{'评分':>6}{'日里程(MW)':>12}{'日调节量(MWh)':>15}{'日收入(元)':>12}" \
           f"{'日折损(元)':>12}{'日净收入(元)':>14}"
    print(hdr3)
    print("-" * len(hdr3))
    for score, m, mwh in [(92, 1200, 10), (90, 400, 20), (88, 2400, 20), (88, 2400, 40)]:
        inc = revenue_mileage(score, m) / DAYS_PER_MONTH
        cost = cycle_cost(mwh)
        print(f"{score:>6}{m:>12}{mwh:>15.0f}{inc:>12.0f}{cost:>12.0f}{inc-cost:>14.0f}")
    print(f"  正文手算示例：92 分 / 日里程 1200 MW / 日调节量 10 MWh"
          f" → {revenue_mileage(92,1200)/DAYS_PER_MONTH:.0f} − {cycle_cost(10):.0f}"
          f" = {net_margin(92,1200,10):.0f} 元（亏）")

    print("\n【④ 盈亏平衡日里程（评分系数 0.90）】")
    for mwh in (5, 10, 20, 40):
        be = breakeven_mileage(90, mwh)
        print(f"  日调节量 {mwh:>3.0f} MWh → 折损 {cycle_cost(mwh):>7.0f} 元/天"
              f" → 需日里程 ≥ {be:>7.0f} MW 才不亏")
    print(f"  结论：{MILE_PRICE_YUAN_PER_MW:.1f} 元/MW 的低单价下，"
          f"储能 AGC 里程收入很难覆盖电池折损——这正是 07b 章「低单价 AGC 不经济」的量化依据。")

    print("\n" + "=" * 70)
    test()
    print("=" * 70)


if __name__ == "__main__":
    main()