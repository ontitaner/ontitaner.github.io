"""第 14 章最小闭环：逐分钟进口→剩余预算→储能动作。

输入：15 分钟窗口，前 10 分钟进口 1700 kW，第 10 分钟升到 2200 kW，目标 1800 kW
算法：预测需量、允许进口、计算额外放电
输出：预测值、允许进口和需要的储能功率
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.demand import allowed_import_kw, predict_demand_kw, required_extra_discharge_kw  # noqa: E402


def main():
    target, window_s = 1800.0, 900.0
    elapsed_kwh = 1700 * 10 / 60
    remain_s = 5 * 60
    predict = predict_demand_kw(elapsed_kwh, 2200, remain_s, window_s)
    allowed = allowed_import_kw(elapsed_kwh, remain_s, target, window_s)
    extra = required_extra_discharge_kw(elapsed_kwh, 2200, remain_s, target, window_s)
    print(f"已用电量：{elapsed_kwh:.2f} kWh")
    print(f"无储能预测需量：{predict:.2f} kW")
    print(f"剩余允许进口：{allowed:.2f} kW")
    print(f"储能需要额外放电：{extra:.2f} kW")
    assert abs(predict - 1866.67) < 0.01
    assert abs(allowed - 2000) < 1e-9 and abs(extra - 200) < 1e-9
    print("自检通过")


if __name__ == "__main__":
    main()

