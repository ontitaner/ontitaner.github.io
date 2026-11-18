# @AI_GENERATED
"""ch03 示例：多资源无功分配三种策略对比

主线场景：50MW/100MWh 储能电站第三个月扩容后
SVG ±15 Mvar, PCS×10 ±50 Mvar, 电容 1×10 Mvar（离散 −10000）
Q_total=−8000 kvar（需吸收 8 Mvar）
"""
from lab.ems_lab.resource_allocator import allocate, ResourceConfig, Strategy


def _resources():
    return [
        ResourceConfig(name="SVG", q_rating_kvar=15000,
                       discrete_steps=[], speed_rank=1, cost_rank=3),
        ResourceConfig(name="PCS", q_rating_kvar=50000,
                       discrete_steps=[], speed_rank=2, cost_rank=2),
        ResourceConfig(name="电容", q_rating_kvar=10000,
                       discrete_steps=[-10000], speed_rank=3, cost_rank=1),
    ]


def main():
    q_total = -8000
    print(f"多资源无功分配三种策略  [主线: SVG±15Mvar PCS±50Mvar 电容−10Mvar]\n")
    for strategy, label in [
        (Strategy.CAPACITY_PROPORTIONAL, "按剩余容量比例"),
        (Strategy.SPEED_PRIORITY, "按响应速度（SVG优先）"),
        (Strategy.ECONOMIC_PRIORITY, "按经济损耗（电容优先）"),
    ]:
        r = allocate(q_total, _resources(), strategy)
        total = sum(r.values())
        print(f"  {label}:")
        for name in ["SVG", "PCS", "电容"]:
            print(f"    {name}: {r[name]:+7.0f} kvar")
        print(f"    合计: {total:+7.0f} kvar  (需求 {q_total:+5.0f})")
        print()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end