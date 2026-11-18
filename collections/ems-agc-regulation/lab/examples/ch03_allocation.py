# @AI_GENERATED
"""ch03 AGC 功率分配与动态补差 — 四种分配策略 lab。

调用真实模块 ems_lab.agc_core 的 Resource + 四个分配函数 + dynamic_supplement，
用教材示例（光伏/风电/储能）补运行输出与自测，含动态补差逐拍追踪。
运行方式: python lab/examples/ch03_allocation.py
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
    Resource, allocate_by_capacity, allocate_by_available,
    allocate_by_cost, allocate_by_soc, dynamic_supplement,
)


def textbook_resources():
    """教材示例：风光储混合场站（非储能 soc=-1.0，储能 soc=0.45）。"""
    return [
        Resource("光伏", pn=40, p_current=30, p_max=40, p_min=0,
                 ramp_rate=0.5, cost_up=0.0, cost_down=0.5),
        Resource("风电", pn=30, p_current=20, p_max=30, p_min=0,
                 ramp_rate=0.3, cost_up=0.0, cost_down=0.0),
        Resource("储能", pn=30, p_current=0, p_max=20, p_min=0,
                 ramp_rate=2.0, cost_up=0.1, cost_down=-0.05, soc=0.45),
    ]


def test():
    """四种策略 + 动态补差四拍追踪自测（与正文手算逐字一致）。"""
    resources = textbook_resources()
    dp = 20

    # 策略一：按额定容量 40:30:30 等比例，总 100
    r1 = allocate_by_capacity(resources, dp)
    assert abs(sum(r1.values()) - 20) < 0.01
    assert r1["光伏"] == 8.0, f"光伏按容量应为8.0, 实为{r1['光伏']}"
    assert r1["风电"] == 6.0
    assert r1["储能"] == 6.0

    # 策略二：按可调容量（上调空间 10:10:20 = 40）
    r2 = allocate_by_available(resources, dp)
    assert abs(sum(r2.values()) - 20) < 0.01
    assert r2["光伏"] == 5.0, f"光伏可调10MW, 占10/40, 实为{r2['光伏']}"
    assert r2["风电"] == 5.0
    assert r2["储能"] == 10.0

    # 策略三：按边际成本（上调，cost_up 0:0:0.1，光伏先10、风电再10）
    r3 = allocate_by_cost(resources, dp)
    assert r3["光伏"] == 10.0, "光伏 cost_up=0 最低，先分配 10MW"
    assert r3["风电"] == 10.0, "风电 cost_up=0 与光伏并列，分配剩余 10MW"
    assert r3["储能"] == 0.0, "储能 cost_up=0.1 高，不被分配"

    # 策略四：SOC 优先（储能 soc=0.45 > soc_low=0.2，优先放电 20MW）
    r4 = allocate_by_soc(resources, dp)
    assert r4["储能"] == 20.0, f"储能 SOC 优先应全包 20MW, 实为{r4['储能']}"
    assert r4["光伏"] == 0.0 and r4["风电"] == 0.0

    # 下调 -15：按可调容量（下调空间 30:20:0 = 50）
    r5 = allocate_by_available(resources, -15)
    assert abs(sum(r5.values()) + 15) < 0.01
    assert r5["光伏"] == -9.0, f"光伏下调空间30MW, 占30/50, 实为{r5['光伏']}"
    assert r5["风电"] == -6.0
    assert r5["储能"] == 0.0, "储能 p_current=0 无下调空间"

    # 动态补差逐拍追踪（threshold=0.5 MW，正文补差门槛 <0.5% Pn）
    target = {"光伏": 35.0, "风电": 25.0, "储能": 10.0}
    # t=0 初始：无偏差 → 不触发
    s0 = dynamic_supplement(target, {"光伏": 35.0, "风电": 25.0, "储能": 10.0}, resources)
    assert all(v == 0.0 for v in s0.values()), "t=0 无偏差不触发"
    # t=1 边界：偏差恰好 -0.5 → 触发（>= 阈值）
    s1 = dynamic_supplement(target, {"光伏": 35.0, "风电": 25.5, "储能": 10.0}, resources)
    assert abs(sum(s1.values()) + 0.5) < 0.01, "t=1 偏差 0.5 恰好触发"
    # t=2 连续：风电缺 3MW（实际 22 < 目标 25）→ 偏差 +3，缺口转给可调资源补 +3
    s2 = dynamic_supplement(target, {"光伏": 35.0, "风电": 22.0, "储能": 10.0}, resources)
    assert abs(sum(s2.values()) - 3.0) < 0.01, "t=2 风电缺口 3MW 被补差"
    # t=3 异常：目标/实际全零 → 不触发
    s3 = dynamic_supplement({"光伏": 0.0, "风电": 0.0, "储能": 0.0},
                            {"光伏": 0.0, "风电": 0.0, "储能": 0.0}, resources)
    assert all(v == 0.0 for v in s3.values()), "t=3 全零不触发"
    print("  ✓ 四种分配策略 + 动态补差逐拍追踪自测通过")


def demo_down_regulation():
    """下调 -15 MW 场景"""
    resources = textbook_resources()
    dp = -15
    print(f"\n下调 {dp} MW 四种策略对比：")

    strategies = [
        ("按容量", allocate_by_capacity(resources, dp)),
        ("按可调", allocate_by_available(resources, dp)),
        ("按成本", allocate_by_cost(resources, dp)),
        ("按SOC", allocate_by_soc(resources, dp)),
    ]

    header = f"{'策略':>8}" + "".join(f"{r.name:>10}" for r in resources) + f"{'合计':>10}"
    print(header)
    print("-" * len(header))
    for name, s in strategies:
        row = f"{name:>8}"
        for r in resources:
            row += f"{s.get(r.name, 0):>10.1f}"
        row += f"{sum(s.values()):>10.1f}"
        print(row)


def demo_supplement_trace():
    """动态补差逐拍追踪演示（正文「动态补差逻辑」四拍）。"""
    resources = textbook_resources()
    print("\n动态补差逐拍追踪（threshold=0.5 MW，即 <0.5% Pn 的门槛）：")
    base = {"光伏": 35.0, "风电": 25.0, "储能": 10.0}
    cases = [
        ("t=0 初始（无偏差）", base, {"光伏": 35.0, "风电": 25.0, "储能": 10.0}),
        ("t=1 边界（偏差恰 0.5）", base, {"光伏": 35.0, "风电": 25.5, "储能": 10.0}),
        ("t=2 连续（风电缺 3）", base, {"光伏": 35.0, "风电": 22.0, "储能": 10.0}),
        ("t=3 异常（目标/实际全零）", {"光伏": 0.0, "风电": 0.0, "储能": 0.0},
         {"光伏": 0.0, "风电": 0.0, "储能": 0.0}),
    ]
    for label, target, actual in cases:
        s = dynamic_supplement(target, actual, resources)
        dev = sum(target[k] - actual[k] for k in target)
        print(f"  {label}: 偏差={dev:+.1f}MW → 补差 {s}")


def main():
    print("=" * 60)
    print("ch03 AGC 四种分配策略 — 教材示例（风光储混合场站）")
    print("=" * 60)

    resources = textbook_resources()
    print("\n教材示例资源：")
    for r in resources:
        soc = "无" if r.soc < 0 else f"{r.soc:.2f}"
        print(f"  {r.name}: Pn={r.pn:.0f}MW, Pnow={r.p_current:.0f}MW, "
              f"上调空间={r.p_max - r.p_current:.0f}MW, "
              f"SOC={soc}, ramp={r.ramp_rate}MW/s")

    dp = 20
    print(f"\n上调 {dp} MW 四种策略对比（正文原样输出）：")
    print("  按容量:", " ".join(f"{k}={v:.0f}" for k, v in allocate_by_capacity(resources, dp).items()))
    print("  按可调:", " ".join(f"{k}={v:.0f}" for k, v in allocate_by_available(resources, dp).items()))
    print("  按成本:", " ".join(f"{k}={v:.0f}" for k, v in allocate_by_cost(resources, dp).items()))
    print("  按SOC:", " ".join(f"{k}={v:.0f}" for k, v in allocate_by_soc(resources, dp).items()))

    print("\n差异分析：")
    print("  容量策略 -> 光伏 8MW / 风电 6MW / 储能 6MW（只看额定容量）")
    print("  可调策略 -> 光伏 5MW / 风电 5MW / 储能 10MW（看实时上调空间）")
    print("  成本策略 -> 光伏 10MW / 风电 10MW / 储能 0MW（cost_up 低的优先）")
    print("  SOC策略  -> 储能 20MW 全包（储能 SOC=0.45 优先放电）")

    print("\n" + "=" * 60)
    demo_down_regulation()
    print("\n" + "=" * 60)
    demo_supplement_trace()
    print("\n" + "=" * 60)
    test()
    print("=" * 60)


if __name__ == "__main__":
    main()