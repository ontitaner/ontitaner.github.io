"""第04章配套示例：成组、OCV、温度限值和簇间木桶效应。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.battery import (  # noqa: E402
    current_from_c_rate,
    bms_power_limit_kw,
    ocv_slope_v_per_soc,
    soc_error_from_voltage_error,
    series_parallel,
    stack_energy,
    temperature_c_limits,
)


def main() -> None:
    cluster = series_parallel(3.2, 314, 416, 1)
    cabinet = series_parallel(3.2, 314, 416, 12)
    current = current_from_c_rate(0.5, 314)
    cluster_power = bms_power_limit_kw(current, cluster.voltage_v)
    charge_c, discharge_c = temperature_c_limits(5)
    cold_charge = bms_power_limit_kw(current_from_c_rate(charge_c, 314), cluster.voltage_v)
    energy = stack_energy([0.60, 0.58, 0.55, 0.45], 400, 0.05, 0.95)

    print(f"416串簇电压：{cluster.voltage_v:.1f} V")
    print(f"12簇标称能量：{cabinet.energy_kwh:.1f} kWh")
    print(f"0.5C簇功率：{cluster_power:.1f} kW")
    print(f"5℃允许充电：{charge_c:.1f}C，约 {cold_charge:.1f} kW/簇")
    print(f"LFP平台斜率：{ocv_slope_v_per_soc(0.45):.1f} V/SOC")
    print(f"5mV电压误差对应SOC误差：{soc_error_from_voltage_error(0.005, 0.45) * 100:.1f}%")
    print(f"簇间不一致实际可放：{energy.dischargeable_kwh:.0f} kWh，理想：{energy.ideal_dischargeable_kwh:.0f} kWh")

    assert cluster.voltage_v == 1331.2
    assert round(cabinet.energy_kwh, 1) == 5016.0
    assert round(cluster_power, 1) == 209.0
    assert round(cold_charge, 1) == 41.8
    assert energy.dischargeable_kwh == 640
    print("自检通过")


if __name__ == "__main__":
    main()

