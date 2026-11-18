"""第01章配套练习：输电损耗、净负荷和储能对鸭子曲线的影响。

从 lab 目录运行：
    python examples/ch01_power_system.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.economics import (  # noqa: E402
    load_curve_stats,
    max_ramp_up_per_h,
    net_load,
    three_phase_line_loss_kw,
)

LOAD_GW = [32, 31, 30, 29.5, 29.5, 30.5, 33, 36, 39.5, 42, 43.5, 44,
           42.5, 42, 43, 43.5, 44, 45.5, 47.5, 48, 47, 44.5, 40, 35.5]
PV_GW = [0, 0, 0, 0, 0, 0, 0.5, 2.5, 6, 10, 13.5, 16,
         17, 16.5, 14.5, 11, 7, 3, 0.5, 0, 0, 0, 0, 0]
P_BESS_GW = [0.0] * 24
for hour in (11, 12, 13, 14):
    P_BESS_GW[hour] = -5.0  # 充电为负
for hour in (17, 18, 19, 20):
    P_BESS_GW[hour] = 4.25  # 放电为正


def main() -> None:
    print("一、三相线路损耗")
    for voltage_kv in (10, 35, 110):
        loss_kw = three_phase_line_loss_kw(10_000, voltage_kv, 1.0)
        print(f"输送 10 MW、{voltage_kv:>3} kV：损耗 {loss_kw:.2f} kW")

    net = net_load(LOAD_GW, PV_GW)
    before = load_curve_stats(net)
    after = load_curve_stats([n - p for n, p in zip(net, P_BESS_GW)])
    print("\n二、净负荷与储能")
    print(f"无储能：峰值 {before.peak:g} GW，谷值 {before.valley:g} GW，峰谷差 {before.peak_valley_diff:g} GW")
    print(f"有储能：峰值 {after.peak:g} GW，谷值 {after.valley:g} GW，峰谷差 {after.peak_valley_diff:g} GW")
    print(f"最大爬坡：{max_ramp_up_per_h(net, 1.0):g} → {max_ramp_up_per_h([n - p for n, p in zip(net, P_BESS_GW)], 1.0):g} GW/h")

    assert round(three_phase_line_loss_kw(10_000, 10, 1.0), 3) == 1000.0
    assert round(three_phase_line_loss_kw(10_000, 110, 1.0), 3) == 8.264
    assert before.peak_valley_diff == 22.5
    assert after.peak_valley_diff == 15.0
    assert max_ramp_up_per_h(net, 1.0) == 5.5
    print("\n自检通过")


if __name__ == "__main__":
    main()

