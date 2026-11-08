# @AI_GENERATED
"""ch05 AGC 跨区调度细则适配 — 三区域参数对比 lab。

演示华东/东北/山西三套参数的 K1 达标验证与薪酬模式差异。
运行方式: python lab/ch05_regional.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, ".")
from lab.agc_core import (
    k1_rating, k2_rating, k3_rating, composite_score,
    Region, REGION_PARAMS, PN, clamp,
)


def check_k1_by_region(pcs_ramp_mw_per_s: float) -> list[dict]:
    """同一 PCS ramp 在不同区域的 K1 评分。"""
    results = []
    for region in Region:
        p = REGION_PARAMS[region]
        k1_mw_per_s = p["k1_min_pn_per_min"] * PN / 60
        margin = pcs_ramp_mw_per_s / k1_mw_per_s
        k1 = k1_rating(pcs_ramp_mw_per_s, k1_mw_per_s)
        results.append({
            "region": region.value,
            "k1_min_mw_per_s": round(k1_mw_per_s, 2),
            "k1_min_pn_per_min": p["k1_min_pn_per_min"],
            "actual_mw_per_s": pcs_ramp_mw_per_s,
            "margin_ratio": round(margin, 2),
            "k1_score": round(k1, 1),
            "pass": k1 >= 80,
        })
    return results


def compensation_compare():
    """教材两种补偿范式对比。"""
    return [
        {
            "范式": "可用率+容量补偿",
            "区域": "华东/山西",
            "收入公式": "可用调节容量 × 补偿单价 × 投运率",
            "特点": "主要是把容量拿出来给调度用，类似租赁费",
            "与动作量关系": "调多调少，收入差不多",
            "EMS重点": "保投运率、保通信在线",
        },
        {
            "范式": "调节里程+效果补偿",
            "区域": "东北",
            "收入公式": "累计调节里程 × 里程单价 × K1/K2/K3 综合系数",
            "特点": "按实际干活的量计酬",
            "与动作量关系": "动作越频繁、幅度越大，收入越高",
            "EMS重点": "频繁动作→高收入，但SOC消耗快→需经济优化",
        },
    ]


def test():
    results = check_k1_by_region(1.67)
    assert results[0]["pass"], "华东 K1≥1.0 Pn/min 应 pass"
    assert results[1]["pass"], "东北 K1≥0.75 Pn/min 应 pass"
    assert results[2]["margin_ratio"] < 1.0, "山西 K1≥1.2 Pn/min, 1.67/2.0=0.83 < 1"
    print("  ✓ 三区域参数自测通过")


def main():
    print("=" * 60)
    print("ch05 三区域（华东/东北/山西）参数差异")
    print("=" * 60)

    print(f"\n区域考核标准（Pn={PN:.0f}MW）：")
    hdr = f"{'指标':>22}{'华东':>10}{'东北':>10}{'山西':>10}"
    print(hdr)
    print("-" * len(hdr))
    for key, label in [
        ("k1_min_pn_per_min", "K1 最低(Pn/min)"),
        ("k2_max_s", "K2 上限(s)"),
        ("k3_max_pct", "K3 上限(% Pn)"),
        ("ace_deadband_mw", "ACE 死区(MW)"),
        ("kp_yuan_per_mwh", "KP 单价(元/MWh)"),
    ]:
        row = f"{label:>22}"
        for region in Region:
            row += f"{REGION_PARAMS[region][key]:>10g}"
        print(row)

    print(f"\nPCS ramp=1.67MW/s (= 1.0Pn/min 对 100MW) 在各区域的 K1：")
    results = check_k1_by_region(1.67)
    hdr2 = f"{'区域':>6}{'要求MW/s':>10}{'margin':>8}{'K1分数':>8}{'通过':>6}"
    print(hdr2)
    print("-" * len(hdr2))
    for r in results:
        status = "✓" if r["pass"] else "✗"
        print(f"{r['region']:>6}{r['k1_min_mw_per_s']:>10.2f}"
              f"{r['margin_ratio']:>8.2f}{r['k1_score']:>8.1f}{status:>6}")

    print(f"\n补偿范式对比：")
    for c in compensation_compare():
        print(f"  {c['范式']}（{c['区域']}）:")
        print(f"    {c['收入公式']}")
        print(f"    {c['特点']}")
        print(f"    {c['EMS重点']}")

    print(f"\n结论：同一套控制器，华东80+分 vs 山西不到70分→差10分以上。")
    print(f"  部署前必须确认所在省网细则版本。")

    print("\n" + "=" * 60)
    test()
    print("=" * 60)


if __name__ == "__main__":
    main()