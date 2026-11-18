# @AI_GENERATED
"""多资源无功分配器：三种策略

对应章节：03 多资源无功分配

教学示例默认值（对齐 03.2~03.5 手算）：
  - SVG ±15 Mvar（快速连续）
  - PCS ×10 ×5 MVA（中速）
  - 电容组 1×10 Mvar（离散−10000 kvar 一档）
  Q_total=−8000 kvar

三种策略：
  1. 按剩余容量比例：Q_i ∝ S_i_remain
  2. 按响应速度优先：SVG 先吃饱 → PCS → 电容
  3. 按经济损耗优先：电容最便宜 → PCS → SVG
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Strategy(Enum):
    CAPACITY_PROPORTIONAL = "capacity_proportional"
    SPEED_PRIORITY = "speed_priority"
    ECONOMIC_PRIORITY = "economic_priority"


@dataclass
class ResourceConfig:
    name: str
    q_rating_kvar: float
    q_used_kvar: float = 0.0
    discrete_steps: List[float] = field(default_factory=list)
    speed_rank: int = 1
    cost_rank: int = 1

    @property
    def q_remaining_kvar(self) -> float:
        return self.q_rating_kvar - abs(self.q_used_kvar)


def allocate(
    q_total: float,
    resources: List[ResourceConfig],
    strategy: Strategy = Strategy.SPEED_PRIORITY,
) -> dict:
    q_remaining_total = sum(r.q_remaining_kvar for r in resources)
    result: dict = {}

    if strategy == Strategy.CAPACITY_PROPORTIONAL:
        for r in resources:
            if q_remaining_total == 0:
                result[r.name] = 0.0
            else:
                ratio = r.q_remaining_kvar / q_remaining_total
                result[r.name] = q_total * ratio

    elif strategy == Strategy.SPEED_PRIORITY:
        ranked = sorted(resources, key=lambda r: r.speed_rank)
        remaining_need = q_total
        for r in ranked:
            if remaining_need == 0:
                result[r.name] = 0.0
                continue
            alloc = max(-r.q_remaining_kvar, min(r.q_remaining_kvar, remaining_need))
            result[r.name] = alloc
            remaining_need -= alloc

    elif strategy == Strategy.ECONOMIC_PRIORITY:
        ranked = sorted(resources, key=lambda r: r.cost_rank)
        remaining_need = q_total
        for r in ranked:
            if remaining_need == 0:
                result[r.name] = 0.0
                continue
            if r.discrete_steps:
                positive_steps = [s for s in sorted(r.discrete_steps) if s != 0]
                alloc = _pick_discrete(remaining_need, r.q_rating_kvar, positive_steps)
            else:
                alloc = max(-r.q_remaining_kvar, min(r.q_remaining_kvar, remaining_need))
            result[r.name] = alloc
            remaining_need -= alloc

    return result


def _pick_discrete(
    remaining_need: float,
    q_rating: float,
    steps: List[float],
) -> float:
    best = 0.0
    best_gap = float('inf')
    for s in steps:
        gap = abs(remaining_need - s)
        if gap < best_gap and abs(s) <= q_rating:
            best = s
            best_gap = gap
    if best_gap == float('inf'):
        best = max(-q_rating, min(q_rating, remaining_need))
    return best
# @AI_GENERATED: end