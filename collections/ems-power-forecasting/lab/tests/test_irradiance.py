# @AI_GENERATED
"""第 03 章一致性测试：辐照 -> 光伏出力转换（POA、温度、逆变削峰、并网点）。

锚定正文 03.x 手算：
  GHI=800、K_t=1.0、T_amb=20 °C -> POA=800、T_cell=45 °C、降额 7%（factor 0.93）
  P_module = 30×0.8×0.93 = 22.32 MW；P_ac = 22.32×0.95 = 21.204 MW
  削峰：G=1000、STC -> P_module=30 -> 30×0.95=28.5 -> 削到 25 MW（削 3.5 MW）
"""
from __future__ import annotations

import pytest

from ems_lab.irradiance import (
    cell_temperature,
    ghi_to_poa,
    inverter_ac,
    pv_dc_power,
    pv_pcc_power,
    temperature_factor,
)


def test_ghi_to_poa_default():
    # 教学示例 K_t=1.0 -> POA = GHI
    assert ghi_to_poa(800.0) == pytest.approx(800.0)


def test_cell_temperature_above_ambient():
    # POA=800、T_amb=20 -> T_cell = 20 + (45−20)×800/800 = 45 °C
    assert cell_temperature(20.0, 800.0) == pytest.approx(45.0)
    # NOCT 模型：800 W/m² 下电池比环境高 25 °C
    assert cell_temperature(0.0, 800.0) == pytest.approx(25.0)


def test_temperature_factor_derating():
    # T_cell=45 -> ΔT=20 -> factor = 1 − 0.0035×20 = 0.93
    assert temperature_factor(45.0) == pytest.approx(0.93)
    # STC 温度 -> factor = 1（无降额）
    assert temperature_factor(25.0) == pytest.approx(1.0)
    # 低温 -> factor > 1（增益）
    assert temperature_factor(5.0) == pytest.approx(1.07)


def test_pv_dc_power_with_temperature():
    # G=800、T_cell=45 -> P_module = 30×0.8×0.93 = 22.32 MW
    assert pv_dc_power(30.0, 800.0, 45.0) == pytest.approx(22.32)


def test_pv_dc_power_stc_reduces_to_linear():
    # STC（T_cell=25）-> 退化为 02 章理想线性 30×800/1000 = 24 MW
    assert pv_dc_power(30.0, 800.0, 25.0) == pytest.approx(24.0)


def test_inverter_ac_efficiency():
    # 22.32 × 0.95 = 21.204 MW（无削峰）
    assert inverter_ac(22.32, 0.95) == pytest.approx(21.204)


def test_inverter_ac_clipping():
    # 30 × 0.95 = 28.5 > 25 -> 削到 25 MW，削峰量 3.5 MW
    assert inverter_ac(30.0, 0.95, 25.0) == pytest.approx(25.0)
    assert (30.0 * 0.95 - inverter_ac(30.0, 0.95, 25.0)) == pytest.approx(3.5)


def test_real_stacking_peak_clipping():
    # 真实叠加态：G=1000 时温度随辐照一起涨，不再冻结 STC
    # T_cell = 20 + (45−20)×1000/800 = 51.25 °C；factor = 1 − 0.0035×26.25 = 0.908125
    t_cell = cell_temperature(20.0, 1000.0)
    assert t_cell == pytest.approx(51.25)
    assert temperature_factor(t_cell) == pytest.approx(0.908125)
    # P_module = 30×1.0×0.908125 = 27.24375 MW；×0.95 = 25.8815625 > 25 -> 削到 25
    dc = pv_dc_power(30.0, 1000.0, t_cell)
    assert dc == pytest.approx(27.24375)
    assert dc * 0.95 == pytest.approx(25.8815625)
    assert inverter_ac(dc, 0.95, 25.0) == pytest.approx(25.0)
    # 削峰量 = 25.8815625 − 25 ≈ 0.88 MW（真实叠加态）
    assert (dc * 0.95 - inverter_ac(dc, 0.95, 25.0)) == pytest.approx(0.8815625)


def test_inverter_ac_no_clip_when_under_rating():
    # 22.32 MW 直流 < 25 MW 额定 -> 不削峰
    assert inverter_ac(22.32, 0.95, 25.0) == pytest.approx(21.204)


def test_pv_pcc_power_subtracts_limit():
    # 21.204 − 0.8 = 20.404 MW（衔接 02 章限电减法）
    assert pv_pcc_power(21.204, 0.8) == pytest.approx(20.404)


def test_pv_pcc_power_floor_zero():
    # 减项大于出力时下界为 0
    assert pv_pcc_power(0.5, 1.0) == pytest.approx(0.0)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        ghi_to_poa(-1.0)
    with pytest.raises(ValueError):
        pv_dc_power(-1.0, 800.0, 25.0)
    with pytest.raises(ValueError):
        pv_dc_power(30.0, 800.0, 25.0, g_ref=0.0)
    with pytest.raises(ValueError):
        inverter_ac(30.0, eta=1.5)
    with pytest.raises(ValueError):
        cell_temperature(20.0, 800.0, noct_irr=0.0)
# @AI_GENERATED: end