# @AI_GENERATED
"""ch07 AGC 月度考核与结算模型 — K1/K2/K3 综合评分 + 补偿对比 lab。

演示评分卡计算 + 容量补偿 vs 里程补偿（统一 80 分基线）。
运行方式: python lab/ch07_scoring.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, ".")
from lab.agc_core import (
    k1_rating, k2_rating, k3_rating, composite_score,
    Region, REGION_PARAMS, PN, clamp,
)


def score_card(k1_mw_per_s: float, k2_s: float, k3_pct: float,
               region: Region = Region.HUADONG) -> dict:
    """单次考核 K1/K2/K3 + 综合评分。"""
    p = REGION_PARAMS[region]
    k1 = k1_rating(k1_mw_per_s, p["k1_min_pn_per_min"] * PN / 60)
    k2 = k2_rating(k2_s, p["k2_max_s"])
    k3 = k3_rating(k3_pct, p["k3_max_pct"])
    comp = composite_score(k1, k2, k3)
    return {
        "region": region.value, "k1": round(k1, 1), "k2": round(k2, 1),
        "k3": round(k3, 1), "composite": round(comp, 1), "pass": comp >= 80,
    }


def compensation_cap(score: float) -> float:
    """容量补偿：固定月费 20000 元 × 分数系数（80 分以下扣减）。"""
    base = 20000
    return base * min(score, 100) / 80.0 if score < 80 else base


def compensation_mile(score: float, pn_mw: float = 100.0,
                      kp: float = 10.0) -> float:
    """里程补偿：调频电量 × KP × 分数系数。"""
    monthly_mwh = pn_mw * 0.05 * 720
    return monthly_mwh * kp * score / 100.0


def test():
    card = score_card(1.2 * PN / 60, 25, 2.5)
    assert card["k1"] >= 100, f"1.2Pn/min应对华东满分, 实为{card['k1']}"
    assert card["pass"]
    print("  ✓ 综合评分自测通过")


def main():
    print("=" * 60)
    print("ch07 AGC 月度考核评分 + 补偿对比（统一 80 分基线）")
    print("=" * 60)

    print("\n【评分卡】")
    scenarios = [
        ("优秀", 1.2 * PN / 60, 22, 2.0, Region.HUADONG),
        ("达标", 0.9 * PN / 60, 30, 3.5, Region.HUADONG),
        ("挣扎", 0.6 * PN / 60, 38, 5.5, Region.HUADONG),
        ("东北对标挣扎", 0.6 * PN / 60, 38, 5.5, Region.DONGBEI),
    ]
    hdr = f"{'场景':>14}{'区域':>6}{'K1':>8}{'K2':>8}{'K3':>8}{'综合':>8}{'通过':>6}"
    print(hdr)
    print("-" * len(hdr))
    for label, k1, k2, k3, region in scenarios:
        c = score_card(k1, k2, k3, region)
        print(f"{label:>14}{c['region']:>6}{c['k1']:>8.1f}{c['k2']:>8.1f}"
              f"{c['k3']:>8.1f}{c['composite']:>8.1f}"
              f"{'✓' if c['pass'] else '✗':>6}")

    print(f"\n【补偿模式对比】100MW 场站，统一 80 分基线：")
    comp_hdr = f"{'模式':>12}{'补偿(元)':>12}{'说明':>30}"
    print(comp_hdr)
    print("-" * len(comp_hdr))
    cap80 = compensation_cap(80)
    mile80 = compensation_mile(80)
    print(f"{'容量补偿':>12}{cap80:>12.0f}{'固定月费 20000 元':>30}")
    print(f"{'里程补偿':>12}{mile80:>12.0f}{'KP=10元×3600MWh×0.80':>30}")
    print(f"{'差额':>12}{mile80 - cap80:>+12.0f}{'里程反超容量 ' + str(abs(mile80-cap80)) + ' 元':>30}")

    mile95 = compensation_mile(95)
    print(f"\n{'里程补偿(95分)':>12}{mile95:>12.0f}"
          f"{'KP=10元×3600MWh×0.95':>30}")

    print(f"\n结论：80 分下里程补偿 ({mile80:.0f}) 已反超容量 ({cap80:.0f})，")
    print(f"  但场站月调频电量波动大，电量低于 {int(20000*100/80/10)} MWh 时里程不利。")

    print("\n" + "=" * 60)
    test()
    print("=" * 60)


if __name__ == "__main__":
    main()