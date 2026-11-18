# @AI_GENERATED
"""ch08 AGC 并网联调验收规范 — 阶跃响应自检 + 参数一致性校验 lab。

演示阶跃试验 K1/K2/K3 自检逻辑与参数一致性校验。
运行方式: python lab/examples/ch08_testing.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from ems_lab.agc_core import Region, REGION_PARAMS, PN, clamp  # noqa: E402


def step_response_check(
    p_start_mw: float, p_target_mw: float, p_actual_ss_mw: float,
    t_response_s: float, t_ramp_s: float,
    k1_required: float, k2_required_s: float, k3_required_pct: float,
    pn_mw: float = PN,
) -> dict:
    """阶跃响应试验自检（正文 08 章四时刻证据链口径）。

    输入参数与正文四时刻 T_cmd → T_start → T_end 一一对应：
        t_response_s = T_start − T_cmd（K2 响应时间）
        t_ramp_s     = T_end − T_start（K1 调节速率的爬坡时长）
    K1 调节速率 = (P_target − P_start) / t_ramp_s
    K2 响应时间 = t_response_s
    K3 调节精度 = |P_ss − P_target| / Pn × 100%
    """
    k1_actual = abs(p_target_mw - p_start_mw) / t_ramp_s if t_ramp_s > 0 else 0.0
    k2_actual = t_response_s
    k3_actual = abs(p_actual_ss_mw - p_target_mw) / pn_mw * 100.0 if pn_mw > 0 else 0.0

    return {
        "k1_actual_mw_per_s": round(k1_actual, 2),
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
    # 正文 08 章四时刻证据链：52.3→70 MW，K1=1.20、K2=0.5、K3=0.1%（全部达标）
    r = step_response_check(52.3, 70.0, 70.1, 0.5, 14.7, 1.20, 0.5, 0.1)
    assert abs(r["k1_actual_mw_per_s"] - 1.20) < 0.01
    assert abs(r["k2_actual_s"] - 0.5) < 0.01
    assert abs(r["k3_actual_pct"] - 0.1) < 0.01
    assert r["all_pass"], "正文四时刻证据链应全部达标"

    # 同一场景按华东细则限值考核：K2=0.5<60s、K3=0.1%<3% 仍通过
    p = REGION_PARAMS[Region.HUADONG]
    k1_req = p["k1_min_pn_per_min"] * PN / 60
    r2 = step_response_check(52.3, 70.0, 70.1, 0.5, 14.7, k1_req, p["k2_max_s"], p["k3_max_pct"])
    assert r2["k2_pass"] and r2["k3_pass"], "K2=0.5<60s、K3=0.1%<3% 应通过"

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

    # 正文 08 章四时刻证据链场景（52.3→70 MW，全部达标）
    r = step_response_check(52.3, 70.0, 70.1, 0.5, 14.7, 1.20, 0.5, 0.1)
    print(f"\n【正文四时刻证据链 52.3→70MW】")
    print(f"  K1={r['k1_actual_mw_per_s']:.2f}MW/s "
          f"{'✓' if r['k1_pass'] else '✗'}")
    print(f"  K2={r['k2_actual_s']}s "
          f"{'✓' if r['k2_pass'] else '✗'}")
    print(f"  K3={r['k3_actual_pct']}% "
          f"{'✓' if r['k3_pass'] else '✗'}")
    print(f"  验收: {'✓ 通过' if r['all_pass'] else '✗ 不达标'}")

    # 不达标场景：响应慢 + 爬坡慢 + 超调
    r2 = step_response_check(52.3, 70.0, 71.0, 1.0, 25.0, 1.20, 0.5, 0.1)
    print(f"\n【不达标场景：响应慢+爬坡慢+超调】")
    print(f"  K1={r2['k1_actual_mw_per_s']:.2f}MW/s "
          f"{'✓' if r2['k1_pass'] else '✗'}")
    print(f"  K2={r2['k2_actual_s']}s "
          f"{'✓' if r2['k2_pass'] else '✗'}")
    print(f"  K3={r2['k3_actual_pct']}% "
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