# @AI_GENERATED
"""ch07b 示例：SVG vs 储能无功全寿命经济决策

主线场景：50MW/100MWh 储能电站设计阶段
  S=50 MVA, H=4000h, ΔP=0.5 元/kWh, η=0.9
  SVG 初投 180 万, 10 年运维 50 万, 全寿命 230 万
  Q_avg=10 Mvar → 年损失 180 万, 10 年 1800 万
  ROI > 20 倍, 盈亏 Q_avg≈3.6 Mvar
"""
from lab.ems_lab.economics import (
    pcs_opportunity_cost, svg_lifecycle_cost, svg_roi, breakeven_q
)


def main():
    print("SVG vs 储能无功：全寿命经济决策  [主线: 50MW/100MWh 储能电站]\n")

    pcs = pcs_opportunity_cost(q_avg_mvar=10.0)
    svg = svg_lifecycle_cost()
    roi = svg_roi(q_avg_mvar=10.0)

    print("--- 储能 PCS 扛无功的机会成本 ---")
    print(f"  Q_avg=10 Mvar → 被挤占 P={pcs['p_displaced_mw']:.1f} MW")
    print(f"  年损失电量: {pcs['p_displaced_mw']*4000:.0f} MWh")
    print(f"  年损失收益: {pcs['annual_loss_wan']:.0f} 万元")
    print(f"  10 年累计:  {pcs['total_loss_wan']:.0f} 万元")

    print("\n--- SVG 全寿命成本 ---")
    print(f"  初投:       {svg['initial_invest_wan']:.0f} 万元")
    print(f"  10 年运维:  {svg['total_maintenance_wan']:.0f} 万元")
    print(f"  10 年总计:  {svg['total_wan']:.0f} 万元")
    print(f"  年化成本:   {svg['annualized_wan']:.0f} 万元/年")

    print("\n--- 投资回报 ---")
    print(f"  SVG 投资 {roi['svg_total_wan']:.0f} 万 → 省下 {roi['pcs_loss_wan']:.0f} 万")
    print(f"  ROI = {roi['roi']:.1f} 倍 (保守估算 Q=10 Mvar)")
    print(f"  正文高方案: 30% PCS 容量被占 → 年损失 400 万 → ROI > 20 倍")
    print(f"  盈亏平衡 Q_avg ≈ {roi['breakeven_q_mvar']:.1f} Mvar")
    print(f"  → Q_avg > {roi['breakeven_q_mvar']:.1f} Mvar → 投 SVG 是正确决策")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end