# @AI_GENERATED
"""一致性测试：多资源分配器 — 正文 03 章手算验证

正文示例：Q_total=−8000 kvar
SVG ±15 Mvar, PCS×10 ±50 Mvar, 电容 −10 Mvar
"""
from lab.ems_lab.resource_allocator import allocate, ResourceConfig, Strategy


def _default_resources():
    return [
        ResourceConfig(name="SVG", q_rating_kvar=15000, q_used_kvar=0,
                       discrete_steps=[], speed_rank=1, cost_rank=3),
        ResourceConfig(name="PCS", q_rating_kvar=50000, q_used_kvar=0,
                       discrete_steps=[], speed_rank=2, cost_rank=2),
        ResourceConfig(name="电容", q_rating_kvar=10000, q_used_kvar=0,
                       discrete_steps=[-10000], speed_rank=3, cost_rank=1),
    ]


def test_speed_priority():
    resources = _default_resources()
    r = allocate(-8000, resources, Strategy.SPEED_PRIORITY)
    assert r["SVG"] == -8000
    assert r["PCS"] == 0
    assert r["电容"] == 0


def test_economic_priority():
    resources = _default_resources()
    r = allocate(-8000, resources, Strategy.ECONOMIC_PRIORITY)
    assert r["电容"] == -10000.0
    assert r["PCS"] == 2000.0
    assert r["SVG"] == 0.0


def test_capacity_proportional():
    resources = _default_resources()
    r = allocate(-8000, resources, Strategy.CAPACITY_PROPORTIONAL)
    assert abs(r["SVG"] + r["PCS"] + r["电容"] + 8000) < 1.0
# @AI_GENERATED: end