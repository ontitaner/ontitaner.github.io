# @AI_GENERATED
"""ch07 AGC 月度考核与结算模型 — K1/K2/K3 综合评分 + 补偿对比 lab。

复现正文 07 章的两组基准数：
    评分卡：K1=0.85 Pn/min、K2=5 s、K3=2% → 85 / 83.3 / 33.3 → 综合 58.9（不合格）
    补偿  ：容量 100×10×0.98×0.80 = 784 元；里程 50000×0.5×0.80 = 20000 元
运行方式: python lab/examples/ch07_scoring.py
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
    Region, PN, W_K1, W_K2, W_K3,
    score_card, capacity_revenue, mileage_revenue,
    CAP_PRICE_YUAN_PER_MW_MONTH, MILE_PRICE_YUAN_PER_MW, AVAILABILITY_RATE,
)

MILEAGE_MW_PER_MONTH = 50000.0
K2_LIMIT_S = 30.0   # 07 章按储能通用 K2≤30 s 考核（区域细则上限见 05 章）


def textbook_card() -> dict:
    """正文 07.1 现场场景：0.85 Pn/min、5 s、2% 的评分卡（返回原始分与加权项）。"""
    card = score_card(0.85 * PN / 60, 5.0, 2.0, Region.HUADONG, k2_limit_s=K2_LIMIT_S)
    return {
        "k1": card.k1, "k2": card.k2, "k3": card.k3,
        "composite": card.composite, "pass": card.passed,
    }


def weighted_terms() -> tuple[float, float, float, float]:
    """用未取整的单项分算三个加权项，复现正文 25.5 + 16.7 + 16.7 = 58.9。"""
    k1 = 0.85 * 100.0
    k2 = 100.0 * (1 - 5.0 / K2_LIMIT_S)
    k3 = 100.0 * (1 - 2.0 / 3.0)
    t1, t2, t3 = round(W_K1 * k1, 1), round(W_K2 * k2, 1), round(W_K3 * k3, 1)
    return (t1, t2, t3, round(t1 + t2 + t3, 1))


def test():
    c = textbook_card()
    assert c["k1"] == 85.0, f"0.85Pn/min 应得 85 分, 实为 {c['k1']}"
    assert c["k2"] == 83.3, f"K2=5s/限值30s 应得 83.3 分, 实为 {c['k2']}"
    assert c["k3"] == 33.3, f"K3=2%/限值3% 应得 33.3 分, 实为 {c['k3']}"
    assert c["composite"] == 58.9, f"综合应 58.9, 实为 {c['composite']}"
    assert not c["pass"], "58.9 < 80 应判不合格"

    assert abs(capacity_revenue(80) - 784.0) < 0.01, "80 分容量补偿应 784 元"
    assert abs(mileage_revenue(80, MILEAGE_MW_PER_MONTH) - 20000.0) < 0.01, \
        "80 分里程补偿应 20000 元"
    print("  ✓ ch07 评分卡与补偿基准自测通过")


def main():
    print("=" * 68)
    print("ch07 AGC 月度考核评分 + 容量/里程补偿（PN=100MW 教学基线）")
    print("=" * 68)

    print(f"\n【评分公式】K1=min(100,100×实际/要求)  K2=100×(1-实际/限值)"
          f"  K3=100×(1-实际/限值)")
    print(f"【权重】K1 {W_K1:.2f} / K2 {W_K2:.2f} / K3 {W_K3:.2f}")

    print("\n【① 正文基准评分卡（华东）】")
    c = textbook_card()
    t1, t2, t3, tot = weighted_terms()
    print(f"  输入：K1=0.85 Pn/min（要求 1.0）K2=5 s（限值 {K2_LIMIT_S:.0f} s）K3=2%（限值 3%）")
    print(f"  单项：K1={c['k1']:.1f}  K2={c['k2']:.1f}  K3={c['k3']:.1f}")
    print(f"  加权：{W_K1:.2f}×{c['k1']:.1f}={t1:.1f} + "
          f"{W_K2:.2f}×{c['k2']:.1f}={t2:.1f} + "
          f"{W_K3:.2f}×{c['k3']:.1f}={t3:.1f}")
    print(f"  综合：{tot:.1f} 分 → {'合格' if c['pass'] else '不合格'}（合格线 80）")
    print(f"  诊断：K3 只贡献 {t3:.1f} 分，是丢分的胜负手")

    print("\n【② 多场景评分卡对比（K2 统一按 30 s 限值）】")
    scenarios = [
        ("优秀", 1.20, 3.0, 0.5, Region.HUADONG),
        ("达标", 1.05, 6.0, 0.6, Region.HUADONG),
        ("挣扎", 0.85, 5.0, 2.0, Region.HUADONG),
        ("东北对标", 0.85, 5.0, 2.0, Region.DONGBEI),
    ]
    hdr = f"{'场景':>8}{'区域':>6}{'K1':>8}{'K2':>8}{'K3':>8}{'综合':>8}{'判定':>8}"
    print(hdr)
    print("-" * 60)
    for label, k1_pn, k2_s, k3_pct, region in scenarios:
        card = score_card(k1_pn * PN / 60, k2_s, k3_pct, region, k2_limit_s=K2_LIMIT_S)
        verdict = "合格" if card.passed else "不合格"
        print(f"{label:>8}{card.region:>6}{card.k1:>8.1f}{card.k2:>8.1f}"
              f"{card.k3:>8.1f}{card.composite:>8.1f}{verdict:>8}")

    print("\n【③ 两种补偿模式（同一 80 分基线）】")
    print(f"  容量：可调容量 {PN:.0f} MW × {CAP_PRICE_YUAN_PER_MW_MONTH:.0f} 元/MW·月"
          f" × 投运率 {AVAILABILITY_RATE:.2f} × 评分系数 0.80")
    cap80 = capacity_revenue(80)
    print(f"        = {PN:.0f}×{CAP_PRICE_YUAN_PER_MW_MONTH:.0f}"
          f"×{AVAILABILITY_RATE:.2f}×0.80 = {cap80:.0f} 元/月")
    print(f"  里程：累计里程 {MILEAGE_MW_PER_MONTH:.0f} MW × {MILE_PRICE_YUAN_PER_MW:.1f} 元/MW"
          f" × 评分系数 0.80")
    mile80 = mileage_revenue(80, MILEAGE_MW_PER_MONTH)
    print(f"        = {MILEAGE_MW_PER_MONTH:.0f}×{MILE_PRICE_YUAN_PER_MW:.1f}"
          f"×0.80 = {mile80:.0f} 元/月")
    print(f"  差额：{mile80 - cap80:+.0f} 元/月（里程是容量的 {mile80/cap80:.0f} 倍）")

    print("\n【④ 评分敏感度：分数每变 1 分值多少钱】")
    hdr4 = f"{'月评':>6}{'评分系数':>10}{'容量(元)':>12}{'里程(元)':>12}"
    print(hdr4)
    print("-" * len(hdr4))
    for s in (60, 70, 80, 90, 95, 100):
        print(f"{s:>6}{s/100:>10.2f}{capacity_revenue(s):>12.0f}"
              f"{mileage_revenue(s, MILEAGE_MW_PER_MONTH):>12.0f}")
    print(f"  容量每 1 分 ≈ {PN*CAP_PRICE_YUAN_PER_MW_MONTH*AVAILABILITY_RATE/100:.2f} 元/月")
    print(f"  里程每 1 分 ≈ {MILEAGE_MW_PER_MONTH*MILE_PRICE_YUAN_PER_MW/100:.0f} 元/月"
          f"（里程模式对分数敏感 {mileage_revenue(1,MILEAGE_MW_PER_MONTH)/capacity_revenue(1):.0f} 倍）")

    print("\n" + "=" * 68)
    test()
    print("=" * 68)


if __name__ == "__main__":
    main()