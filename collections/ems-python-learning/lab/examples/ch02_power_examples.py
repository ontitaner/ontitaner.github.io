"""第02章配套练习：功率/电量、三相功率、PF、P-Q能力和PCC平衡。

从 lab 目录运行：
    python examples/ch02_power_examples.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.power import (  # noqa: E402
    apparent_power,
    energy_kwh_trapezoid,
    max_active_power,
    pcc_injection_kw,
    power_factor,
)


def main() -> None:
    print("一、功率与电量")
    print(f"1000 kW × 0.5 h = {1000 * 0.5:.0f} kWh")
    print(f"梯形积分 0→1000 kW、1 h = {energy_kwh_trapezoid([0, 1800, 3600], [0, 500, 1000]):.0f} kWh")

    print("二、三相功率")
    p_w = 3**0.5 * 400 * 1443 * 1
    print(f"√3 × 400 V × 1443 A × 1 = {p_w:.0f} W")

    print("三、功率三角形")
    s = apparent_power(80, 60)
    pf = power_factor(80, 60)
    print(f"P=80 kW、Q=60 kvar → S={s:.0f} kVA、PF={pf:.1f}")

    print("四、P-Q能力")
    print(f"S=100 kVA、Q=60 kvar → P最大={max_active_power(100, 60):.0f} kW")

    print("五、PCC功率平衡")
    pcc = pcc_injection_kw(200, 500, p_aux_kw=10, p_loss_kw=5)
    print(f"PCC注入 = 200 − 500 − 10 − 5 = {pcc:.0f} kW")

    assert energy_kwh_trapezoid([0, 1800], [1000, 1000]) == 500
    assert abs(p_w - 1_000_000) < 500
    assert s == 100 and pf == 0.8
    assert max_active_power(100, 60) == 80
    assert pcc == -315
    print("自检通过")


if __name__ == "__main__":
    main()

