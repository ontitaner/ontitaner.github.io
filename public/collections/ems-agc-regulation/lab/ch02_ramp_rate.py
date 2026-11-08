# @AI_GENERATED
"""ch02 AGC 调节速率瓶颈与整定 — K1 三级限速校验 lab。

原样复制教材代码块，补运行示例与自测。
运行方式: python lab/ch02_ramp_rate.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, ".")
from lab.agc_core import clamp


# ── 教材原样代码 ────────────────────────────────────────

def check_ramp_rate_multilevel(
    pcs_ramp: float,        # PCS 硬件级 ramp rate (MW/s)
    ems_safety_limit: float, # EMS 安全限速 (MW/s)
    alloc_synthesis: float,  # 分配模块合成速率 (MW/s)
    k1_required: float,      # 调度要求 K1 (MW/s)
    margin: float = 1.2      # 安全裕量系数
) -> dict:
    """逐层校验 AGC 多级限速链路，定位瓶颈环节"""
    effective = min(pcs_ramp, ems_safety_limit, alloc_synthesis)

    result = {
        "k1_effective": effective,        # 实际可用 ramp rate（瓶颈值）
        "target_with_margin": k1_required * margin,
        "pass": effective >= k1_required * margin,
        "bottleneck": None                # 瓶颈到底在哪一层
    }

    if not result["pass"]:
        if pcs_ramp < k1_required * margin:
            result["bottleneck"] = "PCS硬件"
        elif ems_safety_limit < k1_required * margin:
            result["bottleneck"] = "EMS安全限速"
        else:
            result["bottleneck"] = "分配模块合成"

    return result


# ── 教材示例复现 ────────────────────────────────────────

def demo_textbook_example():
    """教材示例：K1_required=1.0 Pn/min=1.67 MW/s, Pn=100MW"""
    k1_mw_per_s = 1.0 * 100 / 60  # 1.67 MW/s
    r = check_ramp_rate_multilevel(
        pcs_ramp=0.8,
        ems_safety_limit=1.0,
        alloc_synthesis=1.2,
        k1_required=k1_mw_per_s,
    )
    return r


def demo_all_pass():
    """全部富裕场景：PCS=2.5, EMS=2.5, 合成=2.0"""
    k1_mw_per_s = 1.0 * 100 / 60
    return check_ramp_rate_multilevel(
        pcs_ramp=2.5,
        ems_safety_limit=2.5,
        alloc_synthesis=2.0,
        k1_required=k1_mw_per_s,
    )


def demo_ems_block():
    """EMS 安全限速卡脖子场景"""
    k1_mw_per_s = 1.0 * 100 / 60
    return check_ramp_rate_multilevel(
        pcs_ramp=2.0,
        ems_safety_limit=1.0,
        alloc_synthesis=2.0,
        k1_required=k1_mw_per_s,
    )


# ── 4 台 PCS 场景 ─────────────────────────────────────

def demo_4pcs():
    """教材 4 台 25MW PCS 场景：单台需 ≥0.42 MW/s"""
    n_pcs = 4
    k1_mw_per_s = 1.0 * 100 / 60  # 1.67 MW/s
    single_need = k1_mw_per_s / n_pcs  # 0.42 MW/s
    pcs_ramp = 0.8  # PCS 实际 ramp

    result = {
        "total_pn_mw": 100,
        "n_pcs": n_pcs,
        "k1_mw_per_s": k1_mw_per_s,
        "single_pcs_need_mw_per_s": round(single_need, 2),
        "pcs_actual_ramp": pcs_ramp,
        "pcs_ok": pcs_ramp >= single_need,
    }

    r = check_ramp_rate_multilevel(
        pcs_ramp=pcs_ramp,
        ems_safety_limit=1.0,  # 教材中的"安全限速不小心设成了1.0"
        alloc_synthesis=2.0,
        k1_required=k1_mw_per_s,
    )
    result["check"] = r
    return result


# ── 自测 ────────────────────────────────────────────────

def test():
    r = demo_textbook_example()
    assert abs(r["k1_effective"] - 0.8) < 0.01, f"effective应为0.8，{r['k1_effective']}"
    assert not r["pass"], "PCS=0.8 < 1.67×1.2=2.0，应不通过"
    assert r["bottleneck"] == "PCS硬件"

    r2 = demo_all_pass()
    assert r2["pass"], "全部富裕应通过"

    r3 = demo_ems_block()
    assert not r3["pass"]
    assert r3["bottleneck"] == "EMS安全限速", f"瓶颈应为EMS，{r3['bottleneck']}"
    print("  ✓ 三级限速自测通过")


# ── 主函数 ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("ch02 K1 三级限速校验 — check_ramp_rate_multilevel()")
    print("=" * 60)

    print("\n【教材示例】Pn=100MW, K1_required=1.0Pn/min=1.67MW/s")
    print("  PCS=0.8MW/s, EMS=1.0MW/s, 合成=1.2MW/s")
    r = demo_textbook_example()
    print(f"  → effective={r['k1_effective']}MW/s, "
          f"target_margin={r['target_with_margin']:.1f}MW/s, "
          f"pass={r['pass']}, bottleneck={r['bottleneck']}")
    print(f"  → 结论：min(0.8,1.0,1.2)=0.8MW/s < 2.0MW/s，卡在 PCS 硬件层！")

    print("\n【全部富裕】PCS=2.5, EMS=2.5, 合成=2.0")
    r2 = demo_all_pass()
    print(f"  → effective={r2['k1_effective']}MW/s, pass={r2['pass']}")

    print("\n【EMS卡脖子】PCS=2.0, EMS=1.0, 合成=2.0")
    r3 = demo_ems_block()
    print(f"  → effective=1.0MW/s, bottleneck={r3['bottleneck']}")
    print(f"  → 教材原文：EMS安全限速不小心设成了1.0，整个K1就被EMS自己卡死了！")

    print("\n【4台PCS场景】单台需 ≥0.42MW/s, PCS实际=0.8MW/s")
    r4 = demo_4pcs()
    print(f"  → PCS满足要求: {r4['pcs_ok']}, "
          f"但 EMS=1.0 < 1.67→K1被卡: {r4['check']['bottleneck']}")

    print("\n" + "=" * 60)
    test()
    print("=" * 60)


if __name__ == "__main__":
    main()