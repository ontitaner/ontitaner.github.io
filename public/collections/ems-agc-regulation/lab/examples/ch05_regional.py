# @AI_GENERATED
"""ch05 AGC 跨区调度细则适配 — 三区域参数对比 lab。

核心演示：同一台设备，换一套细则（华东/东北/山西）分数就变。
  设备 A（合格设备）：PCS 1.8 MW/s、K3 0.5% → 三地都合格，但东北最吃分
  设备 B（偏弱设备）：PCS 1.0 MW/s、K3 1.5% → 三地都不合格，东北最惨
运行方式: python lab/examples/ch05_regional.py
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
    Region, PN, REGION_PARAMS, k1_rating, k2_rating, k3_rating, composite_score,
    k2_chain_budget,
)

DEVICES = {
    "A 合格设备": {"pcs_ramp_mw_per_s": 1.8, "k3_pct": 0.5},
    "B 偏弱设备": {"pcs_ramp_mw_per_s": 1.0, "k3_pct": 1.5},
}


def k1_required_mw_per_s(region: Region, pn_mw: float = PN) -> float:
    """区域 K1 要求换算成 MW/s：K1(Pn/min) × Pn ÷ 60。"""
    return REGION_PARAMS[region]["k1_min_pn_per_min"] * pn_mw / 60.0


def k2_chain_total(poll_period_s: float) -> float:
    """K2 端到端延时（复用 04 章六段链路预算）。"""
    return k2_chain_budget(poll_period_s=poll_period_s)["total_s"]


def check_by_region(pcs_ramp_mw_per_s: float, k3_pct: float,
                    pn_mw: float = PN) -> list[dict]:
    """同一台设备在三套细则下的 K1/K2/K3 与综合评分。"""
    rows = []
    for region in Region:
        p = REGION_PARAMS[region]
        req = k1_required_mw_per_s(region, pn_mw)
        k2_total = k2_chain_total(p["poll_period_s"])
        k1 = k1_rating(pcs_ramp_mw_per_s, req)
        k2 = k2_rating(k2_total, p["k2_max_s"])
        k3 = k3_rating(k3_pct, p["k3_max_pct"])
        comp = composite_score(k1, k2, k3)
        rows.append({
            "region": region.value,
            "k1_req_mw_per_s": round(req, 2),
            "k1_score": round(k1, 1),
            "k1_pass": k1 >= 100.0,
            "k2_total_s": round(k2_total, 1),
            "k2_limit_s": p["k2_max_s"],
            "k2_score": round(k2, 1),
            "k3_score": round(k3, 1),
            "composite": comp,
            "pass": comp >= p["score_pass"],
            "pass_line": p["score_pass"],
        })
    return rows


def compensation_compare() -> list[dict]:
    """两种补偿范式对比。"""
    return [
        {"范式": "容量补偿", "区域": "华东/山西",
         "公式": "可调容量 × 10 元/MW·月 × 投运率 × 评分系数",
         "与动作量关系": "无关", "EMS 重点": "保投运率、保通信在线"},
        {"范式": "里程补偿", "区域": "东北",
         "公式": "累计调节里程 × 0.5 元/MW × 评分系数",
         "与动作量关系": "正比", "EMS 重点": "多跟踪 + 保评分 + 控 SOC"},
    ]


def test():
    a = check_by_region(**{"pcs_ramp_mw_per_s": 1.8, "k3_pct": 0.5})
    b = check_by_region(**{"pcs_ramp_mw_per_s": 1.0, "k3_pct": 1.5})
    assert a[0]["k1_score"] == 100.0, f"设备A 华东 K1 应 100, 实为 {a[0]['k1_score']}"
    assert a[1]["k1_score"] == 72.0, f"设备A 东北 K1 应 72, 实为 {a[1]['k1_score']}"
    assert a[0]["k2_score"] == 77.5, f"华东 K2 应 77.5, 实为 {a[0]['k2_score']}"
    assert a[1]["k2_score"] == 68.3, f"东北 K2 应 68.3, 实为 {a[1]['k2_score']}"
    assert a[0]["pass"] and a[1]["pass"] and a[2]["pass"], "设备A 三地都应合格"
    assert a[0]["composite"] > a[1]["composite"], "设备A 华东分数应高于东北"
    assert not b[0]["pass"] and not b[1]["pass"], "设备B 三地都不合格"
    assert b[0]["composite"] > b[1]["composite"], "设备B 华东分数应高于东北"
    print("  ✓ ch05 三区域参数自测通过")


def main():
    print("=" * 82)
    print("ch05 三区域（华东/东北/山西）AGC 细则差异（Pn=100MW）")
    print("=" * 82)

    print("\n【① 三份细则的参数对照】")
    hdr = f"{'参数':>24}{'华东':>12}{'东北':>12}{'山西':>12}"
    print(hdr)
    print("-" * len(hdr))
    labels = [
        ("k1_min_pn_per_min", "K1 最低要求(Pn/min)"),
        ("k1_req_mw_per_s", "K1 要求换算(MW/s)"),
        ("k2_max_s", "K2 上限(s)"),
        ("k3_max_pct", "K3 上限(% Pn)"),
        ("cmd_deadband_mw", "指令死区(MW)"),
        ("poll_period_s", "104 轮询周期(s)"),
        ("availability_min", "投运率要求"),
        ("score_pass", "合格线(分)"),
    ]
    for key, label in labels:
        row = f"{label:>24}"
        for region in Region:
            if key == "k1_req_mw_per_s":
                val = k1_required_mw_per_s(region)
            else:
                val = REGION_PARAMS[region][key]
            row += f"{val:>12g}"
        print(row)
    print(f"{'补偿模式':>24}" + "".join(
        f"{REGION_PARAMS[r]['compensation_mode']:>12}" for r in Region))

    for idx, (name, dev) in enumerate(DEVICES.items(), start=2):
        print(f"\n【{'②' if idx == 2 else '③'} 设备{name[0]}："
              f"PCS ramp {dev['pcs_ramp_mw_per_s']:.1f} MW/s、"
              f"K3 {dev['k3_pct']:.1f}%（{name[2:]}）】")
        rows = check_by_region(**dev)
        hdr2 = f"{'区域':>6}{'K1要求':>9}{'K1分':>7}{'K1达标':>7}" \
               f"{'K2延时':>8}{'K2限值':>8}{'K2分':>7}{'K3分':>7}{'综合':>7}{'合格线':>7}{'判定':>7}"
        print(hdr2)
        print("-" * len(hdr2))
        for r in rows:
            print(f"{r['region']:>6}{r['k1_req_mw_per_s']:>9.2f}{r['k1_score']:>7.1f}"
                  f"{'✓' if r['k1_pass'] else '✗':>7}"
                  f"{r['k2_total_s']:>8.1f}{r['k2_limit_s']:>8.0f}"
                  f"{r['k2_score']:>7.1f}{r['k3_score']:>7.1f}"
                  f"{r['composite']:>7.1f}{r['pass_line']:>7.0f}"
                  f"{'合格' if r['pass'] else '不合格':>7}")
        best = max(rows, key=lambda r: r["composite"])
        worst = min(rows, key=lambda r: r["composite"])
        print(f"  → 最高分 {best['region']} {best['composite']:.1f} 分，"
              f"最低分 {worst['region']} {worst['composite']:.1f} 分，"
              f"跨区落差 {best['composite']-worst['composite']:.1f} 分")

    print("\n【④ K1 拿满分所需的最小 PCS ramp（同一设备 1.8 MW/s 的对照）】")
    for region in Region:
        req = k1_required_mw_per_s(region)
        print(f"  {region.value:>4}：K1 ≥ {REGION_PARAMS[region]['k1_min_pn_per_min']:.1f} Pn/min"
              f" = {req:.2f} MW/s"
              f" → 1.8 MW/s 折算 {min(100.0, 1.8/req*100):.0f} 分")

    print("\n【⑤ 指令死区校验（规则：死区 ≤ 调度最小指令步长 ÷ 2）】")
    min_step = {Region.HUADONG: 1.0, Region.DONGBEI: 0.5, Region.SHANXI: 1.0}
    copied = REGION_PARAMS[Region.HUADONG]["cmd_deadband_mw"]
    for region in Region:
        p = REGION_PARAMS[region]
        rule = min_step[region] / 2
        own = p["cmd_deadband_mw"]
        print(f"  {region.value:>4}（轮询 {p['poll_period_s']:.0f} s，最小步长 "
              f"{min_step[region]:.1f} MW → 死区上限 {rule:.2f} MW）："
              f"本地 {own:.1f} MW {'合规' if own <= rule else '违规'}"
              f"；照搬华东 {copied:.1f} MW {'合规' if copied <= rule else '违规'}")

    print("\n【⑥ 补偿范式对比】")
    for c in compensation_compare():
        print(f"  {c['范式']}（{c['区域']}）")
        print(f"    公式      ：{c['公式']}")
        print(f"    与动作量  ：{c['与动作量关系']}")
        print(f"    EMS 重点  ：{c['EMS 重点']}")

    print("\n" + "=" * 82)
    test()
    print("=" * 82)


if __name__ == "__main__":
    main()