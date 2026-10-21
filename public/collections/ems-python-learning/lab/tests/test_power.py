import math

import pytest

from ems_lab.power import (
    apparent_power,
    energy_kwh_trapezoid,
    max_active_power,
    max_reactive_power,
    pcc_injection_kw,
    power_factor,
)


def test_apparent_power_and_pf_textbook_triangle():
    # 第 02 章手算：P=80 kW, Q=60 kvar → S=100 kVA, PF=0.8
    assert apparent_power(80, 60) == pytest.approx(100)
    assert power_factor(80, 60) == pytest.approx(0.8)
    assert power_factor(-80, -60) == pytest.approx(0.8)  # 幅值，与方向无关
    assert power_factor(0, 0) == 1.0


def test_pq_capability_competition():
    # PCS 100 kVA，电网要 60 kvar，则有功最多 80 kW
    assert max_active_power(100, 60) == pytest.approx(80)
    assert max_reactive_power(100, 80) == pytest.approx(60)
    with pytest.raises(ValueError):
        max_active_power(100, 120)


def test_energy_trapezoid_constant_and_ramp():
    # 恒定 1000 kW 持续 0.5 h → 500 kWh
    assert energy_kwh_trapezoid([0, 1800], [1000, 1000]) == pytest.approx(500)
    # 0 → 1000 kW 线性爬升 1 h → 500 kWh（三角形面积）
    assert energy_kwh_trapezoid([0, 1800, 3600], [0, 500, 1000]) == pytest.approx(500)
    with pytest.raises(ValueError):
        energy_kwh_trapezoid([0, 10, 10], [1, 1, 1])


@pytest.mark.parametrize(
    "p_bess, p_load, expected",
    [
        (0, 100, -100),  # 全部从电网取电
        (30, 100, -70),  # 储能分担 30
        (120, 100, 20),  # 倒送 20
        (-20, 100, -120),  # 储能充电，取电更多
    ],
)
def test_pcc_balance_table(p_bess, p_load, expected):
    assert pcc_injection_kw(p_bess, p_load) == pytest.approx(expected)


def test_pcc_balance_with_aux_loss_and_pv():
    # 第 02 章练习 1：负荷 500、储能放 200、辅助 10、损耗 5 → -315
    assert pcc_injection_kw(200, 500, 10, 5) == pytest.approx(-315)
    assert pcc_injection_kw(0, 300, p_pv_kw=400) == pytest.approx(100)
    assert not math.isnan(pcc_injection_kw(0, 0))


def test_ch02_power_examples_script():
    """第02章读者示例可运行并通过自检。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch02_power_examples.py"
    runpy.run_path(str(script), run_name="__main__")

