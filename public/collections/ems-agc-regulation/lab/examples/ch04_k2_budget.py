# @AI_GENERATED
"""ch04 AGC 考核指标与统计口径 — K2 时序预算 lab。

复用 agc_core.k2_chain_budget（正文 04 章「K2 的时间预算」表），
用教材示例（轮询=4s, K2=30s）演示逐节延迟累加：
104轮询→EMS解析→死区判定→下发→PCS响应→出力到达。
运行方式: python lab/examples/ch04_k2_budget.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from ems_lab.agc_core import k2_chain_budget  # noqa: E402


# ── 教材示例 ────────────────────────────────────────────

def demo_textbook_example():
    """教材示例：东北 K2=30s, 轮询=4s → total=9.5s, pass=✓"""
    return k2_chain_budget(poll_period_s=4.0, k2_limit_s=30.0)


def demo_worst_case():
    """最差场景：轮询提高到 10s"""
    return k2_chain_budget(poll_period_s=10.0, k2_limit_s=30.0)


def demo_all_regions():
    """三区域 K2 达标测试（限值与正文 05 章 REGION_PARAMS 一致）"""
    configs = [
        ("华东 K2≤60s, 轮询=8s", 8.0, 60.0),
        ("东北 K2≤30s, 轮询=4s", 4.0, 30.0),
        ("山西 K2≤60s, 轮询=8s", 8.0, 60.0),
    ]
    return [(label, k2_chain_budget(poll_period_s=poll, k2_limit_s=limit))
            for label, poll, limit in configs]


# ── 自测 ────────────────────────────────────────────────

def test():
    r = demo_textbook_example()
    assert r["total_s"] == 9.5, f"total应为9.5s, 实为{r['total_s']}"
    assert r["margin_s"] == 20.5
    assert r["margin_pct"] == 68.3, f"应68.3%, 实为{r['margin_pct']}%"
    assert r["pass"] is True, "9.5s < 30s 应通过"
    assert r["biggest_risk"] == "104轮询（最差=轮询周期）"

    r2 = demo_worst_case()
    assert r2["total_s"] == 15.5, f"轮询10s时total=15.5s, 实为{r2['total_s']}"
    assert r2["pass"] is True, "15.5s < 30s 仍通过"

    print("  ✓ K2 时序预算自测通过")


# ── 主函数 ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("ch04 K2 响应时间逐节预算 — k2_chain_budget()")
    print("=" * 60)

    r = demo_textbook_example()
    print(f"\n【教材示例】K2=30s, 轮询=4s")
    print(f"  → total=4+0.5+0.5+0.5+1+3=9.5s, margin=20.5s (68.3%), pass=✓")
    print(f"  → 最大贡献项 = '{r['biggest_risk']}' — 教材原文：K2预算中唯一不可控的大头")

    print("\n环节明细：")
    for k, v in r["chain_detail"].items():
        bar = "█" * int(v / max(r["chain_detail"].values()) * 20)
        pct = v / r["total_s"] * 100
        print(f"  {k:<26} {v:>5.1f}s  {pct:>5.1f}%  {bar}")

    r2 = demo_worst_case()
    print(f"\n【最差场景】轮询提高到 10s")
    print(f"  → total={r2['total_s']}s, margin={r2['margin_s']}s, pass={r2['pass']}")
    print(f"  → 教材原文：仅104延迟就吃掉1/3的K2预算")

    print(f"\n【三区域 K2 达标测试】")
    for label, rr in demo_all_regions():
        status = "✓" if rr["pass"] else "✗"
        print(f"  {label}: total={rr['total_s']}s, margin={rr['margin_s']:.1f}s ({rr['margin_pct']}%) {status}")

    print("\n" + "=" * 60)
    test()
    print("=" * 60)


if __name__ == "__main__":
    main()