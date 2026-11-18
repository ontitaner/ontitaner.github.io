"""第 13 章最小闭环：电价→充放电计划→SOC→收益。

输入：低价充电、高价放电两个时段
算法：BatterySpec/soc_step 更新 SOC，validate_plan 校验计划，schedule_energy_revenue 计算收益
输出：逐时段 SOC、计划可行性和净收益
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.arbitrage import BatterySpec, soc_step, validate_plan  # noqa: E402
from ems_lab.economics import schedule_energy_revenue  # noqa: E402


def main():
    battery = BatterySpec(2000, 500, 500, soc_min=0.10, soc_max=0.90, eta_charge=0.95, eta_discharge=0.95)
    prices = [0.30, 1.20]
    plan = [-500, 500]  # 低价充电、高价放电；每时段 1 h
    check = validate_plan(plan, battery, 0.50, dt_h=1.0)
    soc = check.soc
    revenue = schedule_energy_revenue(plan, prices, 1.0)
    print(f"时段0：电价 {prices[0]:.2f}，充电 {plan[0]} kW，SOC {soc[0]:.2%} → {soc[1]:.2%}")
    print(f"时段1：电价 {prices[1]:.2f}，放电 {plan[1]} kW，SOC {soc[1]:.2%} → {soc[2]:.2%}")
    print(f"计划可行：{check.feasible}，净收益：{revenue:.2f} 元")
    assert check.feasible and abs(soc[1] - 0.7375) < 1e-9 and abs(soc[2] - 0.474342) < 1e-6
    assert abs(revenue - 450) < 1e-9
    print("自检通过")


if __name__ == "__main__":
    main()

