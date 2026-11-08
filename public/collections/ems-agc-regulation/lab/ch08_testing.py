# @AI_GENERATED
"""ch08 AGC 并网联调验收规范 — 阶跃响应自检 + 参数一致性校验 lab。

演示阶跃试验 K1/K2/K3 自检逻辑与参数一致性校验。
运行方式: python lab/ch08_testing.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, ".")
from lab.agc_core import Region, REGION_PARAMS, PN, clamp


def step_response_check(
    p_start_mw: float, p_end_mw: float,
    t_rise_s: float, t_settle_s: float,
    p_target_mw: float,
    k1_required: float, k2_required_s: float, k3_required_pct: float,
) -> dict:
    """阶跃响应试验自检。

    Args:
        p_start_mw: 起始功率
        p_end_mw: 终点功率
        t_rise_s: 上升时间（到达 90% 的时间）
        t_settle_s: 稳定时间（进入 ±2% 稳态带的时间）
        p_target_mw: 目标功率
    """
    k1_actual = abs(p_end_mw - p_start_mw) / t_rise_s if t_rise_s > 0 else 0
    k2_actual = t_settle_s
    k3_actual = abs(p_end_mw - p_target_mw) / p_target_mw * 100 if p_target_mw > 0 else 0

    return {
        "k1_actual_mw_per_s": round(k1_actual, 3),
        "k2_actual_s": round(k2_actual, 1),
        "k3_actual_pct": round(k3_actual, 2),
        "k1_pass": k1_actual >= k1_required,
        "k2_pass": k2_actual <= k2_required_s,
        "k3_pass": k3_actual <= k3_required_pct,
        "all_pass": (k1_actual >= k1_required and k2_actual <= k2_required_s
                     and k3_actual <= k3_required_pct),
    }


def param_consistency_check(
    dispatch_params: dict, local_params: dict
) -> dict:
    """调度下发参数与本地 EMS 参数一致性校验。"""
    mismatches = {}
    for key in dispatch_params:
        if key in local_params:
            d_val, l_val = dispatch_params[key], local_params[key]
            diff = abs(d_val - l_val) / abs(d_val) * 100 if abs(d_val) > 0 else 0
            if diff >= 1.0:
                mismatches[key] = {"dispatch": d_val, "local": l_val,
                                   "diff_pct": round(diff, 2)}
    return {"mismatches": mismatches, "pass": len(mismatches) == 0,
            "count": len(mismatches)}


def test():
    r = step_response_check(10, 45, 30, 35, 45, 1.6, 30, 3)
    assert abs(r["k1_actual_mw_per_s"] - 1.167) < 0.01
    assert not r["k2_pass"], "35s > 30s, K2 不通过"
    assert r["k3_pass"], "0% 偏差, K3 应通过"
    assert not r["all_pass"], "K1 和 K2 都不达标"

    p = REGION_PARAMS[Region.HUADONG]
    k1_req = p["k1_min_pn_per_min"] * PN / 60
    r2 = step_response_check(10, 45, 30, 35, 45, k1_req, p["k2_max_s"], p["k3_max_pct"])
    assert not r2["k2_pass"], "K2=35s > 30s 华东应不通过"

    rp = param_consistency_check(
        {"deadband_mw": 5.0, "k1_min": 1.0},
        {"deadband_mw": 5.0, "k1_min": 1.0})
    assert rp["pass"]

    rp2 = param_consistency_check({"deadband": 5.0}, {"deadband": 6.0})
    assert not rp2["pass"]
    print("  ✓ 并网验收自测通过")


def main():
    print("=" * 60)
    print("ch08 AGC 并网联调验收 — 阶跃响应自检 + 参数一致性校验")
    print("=" * 60)

    p = REGION_PARAMS[Region.HUADONG]
    k1_req = p["k1_min_pn_per_min"] * PN / 60

    print(f"\n区域：{Region.HUADONG.value}  K1≥{k1_req:.2f}MW/s  "
          f"K2≤{p['k2_max_s']}s  K3≤{p['k3_max_pct']}%")

    # 优秀场景
    r = step_response_check(10, 45, 25, 28, 45, k1_req, p["k2_max_s"], p["k3_max_pct"])
    print(f"\n【阶跃响应 10→45MW】")
    print(f"  K1={r['k1_actual_mw_per_s']}MW/s "
          f"{'✓' if r['k1_pass'] else '✗'}")
    print(f"  K2={r['k2_actual_s']}s "
          f"{'✓' if r['k2_pass'] else '✗'}")
    print(f"  K3={r['k3_actual_pct']}% "
          f"{'✓' if r['k3_pass'] else '✗'}")
    print(f"  验收: {'✓ 通过' if r['all_pass'] else '✗ 不达标'}")

    # 不达标场景
    r2 = step_response_check(10, 38, 35, 42, 45, k1_req, p["k2_max_s"], p["k3_max_pct"])
    print(f"\n【不及格场景 10→38MW（响应慢+超调）】")
    print(f"  K1={r2['k1_actual_mw_per_s']:.1f}MW/s "
          f"{'✓' if r2['k1_pass'] else '✗'}")
    print(f"  K2={r2['k2_actual_s']}s "
          f"{'✓' if r2['k2_pass'] else '✗'}")
    print(f"  K3={r2['k3_actual_pct']:.1f}% "
          f"{'✓' if r2['k3_pass'] else '✗'}")
    print(f"  验收: {'✓ 通过' if r2['all_pass'] else '✗ 不达标'}")

    print(f"\n【参数一致性校验】")
    rp = param_consistency_check(
        {"deadband_mw": 5.0, "k1_min": 1.0, "k2_max_s": 30},
        {"deadband_mw": 5.0, "k1_min": 1.0, "k2_max_s": 30})
    cnt = rp["count"]
    print(f"  {'✓ 全部一致' if rp['pass'] else 'x ' + str(cnt) + ' 项不一致'}")
    print(f"  如有不一致项，必须排查定位后方可投入 AGC 运行。")

    print("\n" + "=" * 60)
    test()
    print("=" * 60)


if __name__ == "__main__":
    main()