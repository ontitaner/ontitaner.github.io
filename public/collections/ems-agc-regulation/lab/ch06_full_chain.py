# @AI_GENERATED
"""ch06 AGC 实现与调节品质 — 完整分配流水线 lab。

原样复制教材代码（AgcConfig/Resource/agc_allocate/clamp），
用教材示例演示死区→ramp约束→分配→限幅→下发全链路。
运行方式: python lab/ch06_full_chain.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, ".")
from dataclasses import dataclass, field
from typing import List


# ── 教材原样代码 ───────────────────────────────────────

@dataclass
class AgcConfig:
    pn_mw: float = 100.0
    p_min_mw: float = 0.0
    p_max_mw: float = 100.0
    ramp_limit_pn_per_min: float = 1.2   # EMS 限速
    cmd_deadband_mw: float = 0.3
    alloc_mode: str = "avail_cap"         # cap / avail_cap / soc_first


@dataclass
class Resource:
    name: str
    pn_mw: float
    p_current_mw: float
    p_min_mw: float
    p_max_mw: float
    ramp_up_mw_per_s: float
    ramp_down_mw_per_s: float
    soc_pct: float = 50.0


def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def agc_allocate(p_target_mw: float, resources: List[Resource],
                 p_current_total: float, cfg: AgcConfig, dt_s: float):
    delta_total = p_target_mw - p_current_total

    # ① 指令死区
    if abs(delta_total) <= cfg.cmd_deadband_mw:
        return {r.name: r.p_current_mw for r in resources}

    # ② ramp 约束
    max_delta = cfg.ramp_limit_pn_per_min * cfg.pn_mw * dt_s / 60.0
    delta_total = max(-max_delta, min(delta_total, max_delta))

    # ③ 分配
    allocations = {}
    if cfg.alloc_mode == "avail_cap":
        avail = {r.name: (r.p_max_mw - r.p_current_mw) if delta_total > 0
                 else (r.p_current_mw - r.p_min_mw) for r in resources}
        total_avail = sum(avail.values())
        if total_avail == 0:
            return {r.name: r.p_current_mw for r in resources}
        for r in resources:
            share = delta_total * avail[r.name] / total_avail
            allocations[r.name] = clamp(r.p_current_mw + share,
                                        r.p_min_mw, r.p_max_mw)

    elif cfg.alloc_mode == "soc_first":
        sorted_res = sorted(resources,
            key=lambda r: r.soc_pct if delta_total > 0 else -r.soc_pct)
        remaining = delta_total
        for r in sorted_res:
            if delta_total > 0:
                max_delta_i = min(r.p_max_mw - r.p_current_mw,
                                  r.ramp_up_mw_per_s * dt_s)
            else:
                max_delta_i = min(r.p_current_mw - r.p_min_mw,
                                  r.ramp_down_mw_per_s * dt_s)
            alloc = max(-max_delta_i, min(remaining,
                       max_delta_i)) if delta_total > 0 else \
                    max(-max_delta_i, min(remaining,
                       -max_delta_i) if delta_total < 0 else 0)
            allocations[r.name] = r.p_current_mw + alloc
            remaining -= alloc
            if abs(remaining) < 0.001:
                break

    return allocations


# ── 教材示例资源 ──────────────────────────────────────

def build_resources() -> List[Resource]:
    return [
        Resource(name="BESS_A", pn_mw=40, p_current_mw=20, p_min_mw=5,
                 p_max_mw=40, ramp_up_mw_per_s=2.0, ramp_down_mw_per_s=2.0,
                 soc_pct=70),
        Resource(name="BESS_B", pn_mw=30, p_current_mw=15, p_min_mw=3,
                 p_max_mw=30, ramp_up_mw_per_s=1.5, ramp_down_mw_per_s=1.5,
                 soc_pct=30),
        Resource(name="BESS_C", pn_mw=30, p_current_mw=5, p_min_mw=2,
                 p_max_mw=30, ramp_up_mw_per_s=1.0, ramp_down_mw_per_s=1.0,
                 soc_pct=50),
    ]


# ── 自测 ────────────────────────────────────────────────

def test():
    resources = build_resources()
    cfg = AgcConfig(pn_mw=100, alloc_mode="avail_cap", dt_s=4)

    r = agc_allocate(p_target_mw=40.0, resources=resources,
                     p_current_total=40.0, cfg=cfg, dt_s=4.0)
    assert all(v == r.resources_p_current if 'resources_p_current' in locals()
               else r[rname] == 20 for rname in ["BESS_A"])
    print("  ✓ 完整分配流水线自测通过")


def main():
    print("=" * 60)
    print("ch06 AGC 完整分配流水线 — agc_allocate()")
    print("=" * 60)

    resources = build_resources()
    p_total = sum(r.p_current_mw for r in resources)

    print("\n资源状态：")
    for r in resources:
        print(f"  {r.name}: Pn={r.pn_mw:.0f}MW, Pnow={r.p_current_mw:.0f}MW, "
              f"SOC={r.soc_pct:.0f}%, ramp={r.ramp_up_mw_per_s}MW/s")

    cfg = AgcConfig(
        pn_mw=100, p_max_mw=100,
        ramp_limit_pn_per_min=1.2,
        cmd_deadband_mw=0.3,
        alloc_mode="avail_cap",
    )

    test_cases = [
        ("上调 10MW (avail_cap)", 50.0, "avail_cap"),
        ("上调 40MW (avail_cap)", 80.0, "avail_cap"),
        ("下调 15MW (avail_cap)", 25.0, "avail_cap"),
        ("死区内 (+0.2MW)", 40.2, "avail_cap"),
        ("上调 10MW (soc_first)", 50.0, "soc_first"),
        ("上调 30MW (soc_first)", 70.0, "soc_first"),
    ]

    for label, target, mode in test_cases:
        cfg2 = AgcConfig(pn_mw=100, p_max_mw=100,
                         ramp_limit_pn_per_min=cfg.ramp_limit_pn_per_min,
                         cmd_deadband_mw=cfg.cmd_deadband_mw,
                         alloc_mode=mode)
        r = agc_allocate(p_target_mw=target, resources=resources,
                         p_current_total=p_total, cfg=cfg2, dt_s=4.0)
        alloc_str = "  ".join(f"{k}={v:.1f}" for k, v in r.items())
        skip = "(跳过=死区内)" if all(
            abs(v - r2.p_current_mw) < 0.01
            for v, r2 in zip(r.values(), resources)) else ""
        print(f"  [{label}] {alloc_str} {skip}")

    print(f"\n结论：死区→ramp约束(max_delta={cfg.ramp_limit_pn_per_min*100*4/60:.1f}MW)→分配→限幅→下发。")
    print(f"  任何一级拦截都会阻止功率下发。")

    print("\n" + "=" * 60)
    test()
    print("=" * 60)


if __name__ == "__main__":
    main()