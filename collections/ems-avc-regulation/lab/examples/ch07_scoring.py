# @AI_GENERATED
"""ch07 示例：月度考核评分计算（重心口算对齐）

主线场景：50MW/100MWh 储能电站，某月考核数据：
  VQR=95.64%, 投运率=98.7%, 响应时间均值=22s
  S_month = 83.2×0.5 + 100×0.3 + 76.7×0.2 = 86.9
"""
from lab.ems_lab.scoring import (
    s_voltage, s_availability, s_performance, monthly_score, capacity_compensation
)


def main():
    vqr = 0.9564
    availability = 0.987
    t_avg = 22.0

    sv = s_voltage(vqr)
    sa = s_availability(availability)
    sq = s_performance(t_avg)
    score = monthly_score(vqr, availability, t_avg)

    compensation = capacity_compensation(
        q_rated_mvar=20,
        hours=30 * 24 * availability,
        price_per_mvarh=10,
        score_ratio=score / 100.0,
    )

    print("月度 AVC 考核评分  [主线: 50MW/100MWh 储能电站]")
    print(f"  电压合格率:   {vqr*100:.2f}%  → S_voltage = {sv:.1f}")
    print(f"  投运率:       {availability*100:.1f}% → S_availability = {sa:.0f}")
    print(f"  响应时间均值: {t_avg:.0f}s  → S_performance = {sq:.1f}")
    print(f"  ─────────────────────────────────")
    print(f"  S_month = {sv:.1f}×0.5 + {sa:.0f}×0.3 + {sq:.1f}×0.2 = {score:.1f}")
    print(f"  考核系数: {score:.1f} ≥ 80 → 1.0（无惩罚）")
    print(f"  容量补偿: {compensation:.0f} 元")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end