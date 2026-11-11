# @AI_GENERATED
"""ch02 AGC 调节速率瓶颈与整定 — K1 三级限速校验 lab。

原样复制教材代码块，补运行示例与自测。
运行方式: python lab/examples/ch02_ramp_rate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from ems_lab.agc_core import clamp, should_track  # noqa: E402


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
    """教材 4 台 25MW PCS 场景：单台需 ≥0.42 MW/s（无余量）或 ≥0.5 MW/s（留 20%）。"""
    n_pcs = 4
    k1_mw_per_s = 1.0 * 100 / 60  # 1.67 MW/s（场站总要求）
    single_need = k1_mw_per_s / n_pcs          # 0.42 MW/s（不留余量）
    single_need_margin = k1_mw_per_s * 1.2 / n_pcs  # 0.5 MW/s（留 20%）

    single_actual = 0.2           # 现场单台 ramp
    pcs_synthesis = single_actual * n_pcs  # 4 台合成 0.8 MW/s

    result = {
        "total_pn_mw": 100,
        "n_pcs": n_pcs,
        "k1_mw_per_s": k1_mw_per_s,
        "single_pcs_need_mw_per_s": round(single_need, 2),
        "single_pcs_need_with_margin": round(single_need_margin, 2),
        "single_actual_ramp": single_actual,
        "pcs_synthesis": pcs_synthesis,
        "single_pcs_ok": single_actual >= single_need,
    }

    r = check_ramp_rate_multilevel(
        pcs_ramp=pcs_synthesis,   # 4 台合成 0.8
        ems_safety_limit=1.0,     # 教材中的"安全限速不小心设成了1.0"
        alloc_synthesis=1.2,      # 教材中的分配模块合成
        k1_required=k1_mw_per_s,
    )
    result["check"] = r
    return result


def demo_deadband():
    """指令死区逐拍追踪：deadband=2.0, p_prev=100.0 覆盖 t=0/1/2/3 四拍。"""
    deadband = 2.0
    p_prev = 100.0
    cases = [
        ("t=0 初始无变化", 100.0),
        ("t=1 恰好等于死区", 102.0),
        ("t=2 连续小步长", 101.2),
        ("t=3 反向同幅", 98.0),
    ]
    rows = []
    for label, p_new in cases:
        change = round(abs(p_new - p_prev), 2)
        track = should_track(p_new, p_prev, deadband)
        rows.append((label, p_new, change, track))
    return rows


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

    rows = demo_deadband()
    assert rows[0][3] is False, "t=0 初始无变化应不跟踪"
    assert rows[1][3] is True, "t=1 恰好等于死区应跟踪"
    assert rows[2][3] is False, "t=2 连续小步长 1.2 < 2.0 应不跟踪"
    assert rows[3][3] is True, "t=3 反向同幅应跟踪"
    print("  ✓ 指令死区逐拍追踪自测通过")


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

    print("\n【4台PCS场景】单台需 ≥0.42MW/s(无余量)/≥0.5MW/s(留20%), 现场单台=0.2→合成0.8")
    r4 = demo_4pcs()
    print(f"  → 单台达标: {r4['single_pcs_ok']}（0.2 < 0.42）, "
          f"合成={r4['pcs_synthesis']}MW/s, "
          f"min(0.8,1.0,1.2)={r4['check']['k1_effective']}MW/s → 卡 {r4['check']['bottleneck']}")

    print("\n【指令死区逐拍追踪】deadband=2.0, p_prev=100.0")
    for label, p_new, change, track in demo_deadband():
        print(f"  {label}: p_new={p_new}, |change|={change}, should_track={track}")
    print("  → 结论：变化量 >= 死区(2.0)才跟踪；1.2 被判定'变化太小' → K2 不合格")

    print("\n" + "=" * 60)
    test()
    print("=" * 60)


if __name__ == "__main__":
    main()