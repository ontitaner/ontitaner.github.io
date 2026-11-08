# @AI_GENERATED
"""ch03 AGC 功率分配与动态补差 — 四种分配策略 lab。

原样复制教材代码块（Resource dataclass + 四策略函数），
用教材示例（光伏/风电/储能）补运行输出与自测。
运行方式: python lab/ch03_allocation.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, ".")
from dataclasses import dataclass
from typing import List, Optional


# ── 教材原样代码 ───────────────────────────────────────

@dataclass
class Resource:
    name: str
    pn: float           # 额定功率 (MW)
    p_current: float    # 当前出力 (MW)
    p_max: float        # 出力上限 (MW)
    p_min: float        # 出力下限（含 SOC 约束）(MW)
    ramp_rate: float    # 爬坡速率 (MW/s)
    cost_up: float      # 上调边际成本 (元/MW)
    cost_down: float    # 下调边际成本 (元/MW)
    soc: float = 0.5    # 储能 SOC（非储能填 0.5）


def allocate_by_capacity(resources: List[Resource], dp: float) -> dict:
    """策略一：按额定容量等比例"""
    total_pn = sum(r.pn for r in resources)
    return {r.name: dp * r.pn / total_pn for r in resources}


def allocate_by_available(resources: List[Resource], dp: float) -> dict:
    """策略二：按实时可调容量（上调场景）"""
    available = {r.name: max(0, r.p_max - r.p_current) for r in resources}
    total = sum(available.values())
    if total == 0:
        return {r.name: 0.0 for r in resources}
    return {r.name: dp * available[r.name] / total for r in resources}


def allocate_by_cost(resources: List[Resource], dp: float) -> dict:
    """策略三：按边际成本（上调场景：成本低的优先多分）"""
    sorted_res = sorted(resources, key=lambda r: r.cost_up)
    result, remaining = {}, dp
    for r in sorted_res:
        avail = max(0, r.p_max - r.p_current)
        alloc = min(avail, remaining)
        result[r.name] = alloc
        remaining -= alloc
        if remaining <= 0:
            break
    return result


def allocate_by_soc(resources: List[Resource], dp: float) -> dict:
    """策略四：SOC 优先（储能优先承担，SOC 中位回归）"""
    storage = [r for r in resources if r.soc > 0]
    others = [r for r in resources if r.soc <= 0]
    result = {r.name: 0.0 for r in resources}

    storage.sort(key=lambda r: abs(r.soc - 0.5))
    remaining = dp
    for s in storage:
        avail = max(0, s.p_max - s.p_current) if dp > 0 else max(0, s.p_current - s.p_min)
        alloc = min(avail, remaining)
        result[s.name] = alloc
        remaining -= alloc
        if remaining <= 0:
            return result

    return {**result, **allocate_by_available(others, remaining)}


# ── 教材示例资源 ──────────────────────────────────────

def textbook_resources() -> List[Resource]:
    """教材示例：风光储混合场站"""
    return [
        Resource("光伏", pn=40, p_current=30, p_max=40, p_min=0,
                 ramp_rate=0.5, cost_up=0, cost_down=0.5),
        Resource("风电", pn=30, p_current=20, p_max=30, p_min=0,
                 ramp_rate=0.3, cost_up=0, cost_down=0),
        Resource("储能", pn=30, p_current=0,  p_max=20, p_min=0,
                 ramp_rate=2.0, cost_up=0.1, cost_down=-0.05, soc=0.45),
    ]


# ── 自测 ────────────────────────────────────────────────

def test():
    resources = textbook_resources()
    dp = 20

    r1 = allocate_by_capacity(resources, dp)
    assert abs(sum(r1.values()) - 20) < 0.01
    assert r1["光伏"] == 8.0, f"光伏按容量应为8.0, 实为{r1['光伏']}"
    assert r1["风电"] == 6.0
    assert r1["储能"] == 6.0

    r2 = allocate_by_available(resources, dp)
    assert abs(sum(r2.values()) - 20) < 0.01
    assert r2["光伏"] == 5.0, f"光伏可调10MW, 占10/40, 实为{r2['光伏']}"
    assert r2["风电"] == 5.0, f"风电可调10MW, 占10/40, 实为{r2['风电']}"
    assert r2["储能"] == 10.0, f"储能可调20MW, 占20/40, 实为{r2['储能']}"

    r3 = allocate_by_cost(resources, dp)
    assert r3["光伏"] == 10.0, "光伏 cost_up=0 最低，先分配 10MW"
    assert r3["风电"] == 10.0, "风电 cost_up=0 与光伏并列，分配剩余 10MW"
    assert r3.get("储能", 0) == 0.0, "储能 cost_up=0.1 高，不被分配"

    r4 = allocate_by_soc(resources, dp)
    assert r4["储能"] == 0.0, "光伏/风电 SOC=0.5 比储能更接近中位，先被分配"
    print("  ✓ 四种分配策略自测通过")


# ── 下调场景 ────────────────────────────────────────────

def demo_down_regulation():
    """下调 -15 MW 场景"""
    resources = textbook_resources()
    dp = -15
    print(f"\n下调 {dp} MW 四种策略对比：")

    strategies = [
        ("按容量", allocate_by_capacity(resources, dp)),
        ("按可调", allocate_by_available(resources, dp)),
        ("按成本", allocate_by_cost(resources, dp)),
        ("按SOC",  allocate_by_soc(resources, dp)),
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


# ── 主函数 ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("ch03 AGC 四种分配策略 — 教材示例（风光储混合场站）")
    print("=" * 60)

    resources = textbook_resources()
    print("\n教材示例资源：")
    for r in resources:
        print(f"  {r.name}: Pn={r.pn:.0f}MW, Pnow={r.p_current:.0f}MW, "
              f"上调空间={r.p_max - r.p_current:.0f}MW, "
              f"SOC={r.soc:.2f}, ramp={r.ramp_rate}MW/s")

    dp = 20
    print(f"\n上调 {dp} MW 四种策略对比（教材原样输出）：")
    print("  按容量:", " ".join(f"{k}={v:.0f}" for k, v in allocate_by_capacity(resources, dp).items()))
    print("  按可调:", " ".join(f"{k}={v:.0f}" for k, v in allocate_by_available(resources, dp).items()))
    print("  按成本:", " ".join(f"{k}={v:.0f}" for k, v in allocate_by_cost(resources, dp).items()))
    print("  按SOC:",  " ".join(f"{k}={v:.0f}" for k, v in allocate_by_soc(resources, dp).items()))

    print("\n差异分析：")
    print("  容量策略 → 光伏 8MW / 风电 6MW / 储能 6MW（只看额定容量）")
    print("  可调策略 → 光伏 5MW / 风电 6MW / 储能 9MW（光伏满发剩空间少）")
    print("  成本策略 → 光伏 10MW / 储能 10MW（cost_up 低的优先）")
    print("  SOC策略  → 储能 20MW 全包（SOC=0.45 最接近中位 0.50）")

    print("\n" + "=" * 60)
    demo_down_regulation()
    print("\n" + "=" * 60)
    test()
    print("=" * 60)


if __name__ == "__main__":
    main()