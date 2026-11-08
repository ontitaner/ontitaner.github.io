# @AI_GENERATED
"""ch07b AGC 辅助服务经济性决策 — 容量 vs 里程补偿 lab。

演示不同分数、不同区域 KP 下的补偿收益对比与盈亏平衡分析。
运行方式: python lab/ch07b_economics.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, ".")
from lab.agc_core import Region, REGION_PARAMS, PN


def revenue_cap(score: float) -> float:
    """容量补偿收入（华东/山西）。"""
    base = 20000
    return base * min(score, 100) / 80.0 if score < 80 else base


def revenue_mile(score: float, kp: float, mileage_mwh: float) -> float:
    """里程补偿收入（东北）。"""
    return mileage_mwh * kp * score / 100.0


def breakeven_score(kp: float, mileage_mwh: float) -> float:
    """盈亏平衡分：容量收入 = 里程收入。"""
    return 20000 / (mileage_mwh * kp / 100.0)


def test():
    assert abs(revenue_cap(80) - 20000) < 0.01, "80分容量应为20000"
    mile_80 = revenue_mile(80, 10, 360)
    assert mile_80 < 20000, f"80分里程({mile_80:.0f})应 < 20000"

    be = breakeven_score(10, 360)
    assert be > 50, f"盈亏平衡分({be:.1f})应 > 50"
    print("  ✓ 经济性自测通过")


def main():
    print("=" * 60)
    print("ch07b AGC 容量 vs 里程补偿经济决策")
    print("=" * 60)

    print(f"\n【参数】PN={PN:.0f}MW, 月调频电量 ≈ 360MWh ({PN*.05:.0f}MW × 5% × 720h)")
    print(f"  容量补偿基价 = 20000 元/月（华东/山西）")

    scores = [60, 70, 75, 80, 85, 90, 95, 100]
    print(f"\n【华东 KP=10 元/MWh】")
    hdr = f"{'分数':>6}{'容量(元)':>12}{'里程(元)':>12}{'里程更优?':>10}"
    print(hdr)
    print("-" * len(hdr))
    for s in scores:
        cap = revenue_cap(s)
        mile = revenue_mile(s, 10, 360)
        better = "✓" if mile > cap else ""
        print(f"{s:>6.0f}{cap:>12.0f}{mile:>12.0f}{better:>10}")

    be_hd = breakeven_score(10, 360)
    print(f"\n  盈亏平衡点 ≈ {be_hd:.1f} 分（容量 vs 里程收入相等）")

    print(f"\n【三区域盈亏平衡点】")
    for region in Region:
        p = REGION_PARAMS[region]
        be = breakeven_score(p["kp_yuan_per_mwh"], 360)
        print(f"  {region.value} KP={p['kp_yuan_per_mwh']}元/MWh → 平衡 {be:.1f} 分")

    print(f"\n【不同调频电量下的盈亏平衡（华东 KP=10）】")
    for mwh in [360, 800, 1500, 2500]:
        be = breakeven_score(10, mwh)
        print(f"  月电量 {mwh:>5}MWh → 平衡 {be:.1f} 分"
              f"{' ← 可接受' if be < 90 else ''}")

    print(f"\n结论：月调频电量越大，里程补偿越有利（盈亏平衡分越低）。")
    print(f"  若每月调频电量 > 2500MWh，里程补偿在多数分数下反超容量补偿。")

    print("\n" + "=" * 60)
    test()
    print("=" * 60)


if __name__ == "__main__":
    main()