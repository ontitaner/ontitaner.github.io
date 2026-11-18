"""第 04、05 章手算例子的测试。每个测试名后注明对应正文小节。"""
import math

import pytest

from ems_lab.battery import (
    NCM_OCV_TEACHING,
    OCV_SOC_TEACHING,
    BmsReport,
    CoulombCounter,
    SocPermissionGate,
    SocZones,
    ac_limits_from_dc,
    actual_capacity_kwh,
    aggregate_soc,
    ah_drift_soc,
    balancing_time_h,
    bms_power_limit_kw,
    c_rate,
    chargeable_energy_kwh,
    check_bms_report,
    classify_soc,
    combine_capability,
    current_from_c_rate,
    dischargeable_energy_kwh,
    energy_limited_power_kw,
    joule_heat_w,
    min_with_reason,
    ocv_from_soc,
    ocv_slope_v_per_soc,
    round_trip_efficiency,
    series_parallel,
    soc_error_from_voltage_error,
    soc_from_ocv,
    soc_window_factors,
    soc_window_limits_kw,
    sop_for_duration,
    stack_energy,
    stack_power_limit_kw,
    temperature_c_limits,
    terminal_voltage_v,
    update_soc,
)


# ================================================================ 第 04 章
def test_cell_to_cabinet_hierarchy_4_5():
    cell = series_parallel(3.2, 314, 1)
    assert cell.energy_kwh == pytest.approx(1.0048)
    cluster = series_parallel(3.2, 314, 416)
    assert cluster.voltage_v == pytest.approx(1331.2)
    assert cluster.energy_kwh == pytest.approx(418.0, abs=0.01)
    cabinet = series_parallel(3.2, 314, 416, 12)
    assert cabinet.capacity_ah == 3768
    assert cabinet.energy_kwh == pytest.approx(5015.96, abs=0.01)
    # 280 Ah 电芯的上一代配置
    assert series_parallel(3.2, 280, 416, 10).energy_kwh == pytest.approx(3727.36, abs=0.01)
    # 单体工作电压 2.8～3.6 V 时的簇电压范围
    assert series_parallel(2.8, 314, 416).voltage_v == pytest.approx(1164.8)
    assert series_parallel(3.6, 314, 416).voltage_v == pytest.approx(1497.6)


def test_c_rate_and_cluster_power_4_3():
    i = current_from_c_rate(0.5, 314)
    assert i == 157
    assert c_rate(-157, 314) == 0.5  # 充电电流为负，倍率取幅值
    p_cluster = bms_power_limit_kw(157, 1331.2)
    assert p_cluster == pytest.approx(209.0, abs=0.01)
    assert 12 * p_cluster == pytest.approx(2507.9, abs=0.1)
    with pytest.raises(ValueError):
        c_rate(100, 0)


def test_joule_heat_and_terminal_voltage_4_7():
    r = 0.25e-3
    assert joule_heat_w(157, r) == pytest.approx(6.162, abs=0.001)
    assert joule_heat_w(314, r) == pytest.approx(4 * joule_heat_w(157, r))  # 电流翻倍，发热 4 倍
    assert joule_heat_w(-157, r) == joule_heat_w(157, r)                    # 充电同样发热
    assert 416 * joule_heat_w(157, r) == pytest.approx(2563.4, abs=0.1)
    assert joule_heat_w(157, 3 * r) == pytest.approx(18.49, abs=0.01)       # 低温内阻 ×3
    assert terminal_voltage_v(3.30, 157, r) == pytest.approx(3.26075)
    assert terminal_voltage_v(3.30, 157, 3 * r) == pytest.approx(3.18225)
    assert terminal_voltage_v(3.30, -157, r) == pytest.approx(3.33925)


@pytest.mark.parametrize("temp, chg, dis", [(25, 0.5, 0.5), (10, 0.25, 0.5), (5, 0.1, 0.45), (0, 0.0, 0.4),
                                            (-5, 0.0, 0.35), (52.5, 0.1, 0.225), (70, 0.0, 0.0)])
def test_temperature_c_limits_4_7(temp, chg, dis):
    c, d = temperature_c_limits(temp)
    assert c == pytest.approx(chg)
    assert d == pytest.approx(dis)


def test_low_temperature_cluster_power_4_7():
    c, d = temperature_c_limits(5)
    assert bms_power_limit_kw(current_from_c_rate(c, 314), 1331.2) == pytest.approx(41.8, abs=0.05)
    assert bms_power_limit_kw(current_from_c_rate(d, 314), 1331.2) == pytest.approx(188.1, abs=0.05)


def test_ocv_flat_plateau_4_6():
    lfp_slope = ocv_slope_v_per_soc(0.45)
    ncm_slope = ocv_slope_v_per_soc(0.45, OCV_SOC_TEACHING, NCM_OCV_TEACHING)
    assert lfp_slope == pytest.approx(0.1)   # 1 mV / 1% SOC
    assert ncm_slope == pytest.approx(0.5)   # 5 mV / 1% SOC
    # 5 mV 的电压误差 → LFP 5% SOC 误差，三元 1%
    assert soc_error_from_voltage_error(0.005, 0.45) == pytest.approx(0.05)
    assert soc_error_from_voltage_error(0.005, 0.45, OCV_SOC_TEACHING, NCM_OCV_TEACHING) == pytest.approx(0.01)
    # 正查、反查互逆
    assert soc_from_ocv(ocv_from_soc(0.07)) == pytest.approx(0.07)
    assert ocv_from_soc(0.45) == pytest.approx(3.295)


def test_balancing_time_4_9():
    assert balancing_time_h(0.01, 314, 0.1) == pytest.approx(31.4)


def test_bms_report_passthrough_and_checks_4_12():
    ok = BmsReport(soc=0.6, soh=0.95, available_charge_kw=1470, available_discharge_kw=2500,
                   max_cell_v=3.34, min_cell_v=3.31, max_cell_temp_c=28, min_cell_temp_c=22)
    r = check_bms_report(ok, 2700, 2700)
    assert (r.available_charge_kw, r.available_discharge_kw, r.issues) == (1470, 2500, ())  # 合理就原样用

    stale = BmsReport(0.6, 0.95, 1470, 2500, age_s=12)
    assert check_bms_report(stale, 2700, 2700).available_discharge_kw == 0

    bad = BmsReport(soc=1.3, soh=0.95, available_charge_kw=-800, available_discharge_kw=25000,
                    discharge_allowed=True, max_cell_v=3.2, min_cell_v=3.4)
    r = check_bms_report(bad, 2700, 2700)
    assert (r.available_charge_kw, r.available_discharge_kw) == (0, 0)
    assert len(r.issues) == 4  # 负值、超物理上限、SOC 越界、电压颠倒

    flag = BmsReport(0.6, 0.95, 1470, 2500, charge_allowed=False)
    r = check_bms_report(flag, 2700, 2700)
    assert r.available_charge_kw == 0 and r.available_discharge_kw == 2500
    assert "禁充" in r.issues[0]

    nan = BmsReport(0.6, 0.95, math.nan, 2500)
    assert check_bms_report(nan, 2700, 2700).available_charge_kw == 0


def test_barrel_effect_4_13():
    e = stack_energy([0.60, 0.58, 0.55, 0.45], 400, soc_min=0.05, soc_max=0.95)
    assert e.dischargeable_kwh == pytest.approx(640)
    assert e.ideal_dischargeable_kwh == pytest.approx(792)
    assert e.chargeable_kwh == pytest.approx(560)
    assert e.ideal_chargeable_kwh == pytest.approx(648)
    assert stack_power_limit_kw([209] * 11 + [150]) == 1800
    assert sum([209] * 11 + [150]) == 2449


# ================================================================ 第 05 章
def test_update_soc_efficiency_5_5():
    d = update_soc(0.60, 200, 3600, 1000, eta_charge=0.95, eta_discharge=0.95)
    assert d.soc == pytest.approx(0.60 - 200 / 0.95 / 1000)  # ≈ 0.3895
    assert d.soc == pytest.approx(0.3895, abs=1e-4)
    assert d.stored_delta_kwh == pytest.approx(-210.53, abs=0.01)
    c = update_soc(0.60, -200, 3600, 1000, eta_charge=0.95, eta_discharge=0.95)
    assert c.soc == pytest.approx(0.79)
    assert not c.violated and c.reason is None


def test_update_soc_keeps_violation_5_5():
    u = update_soc(0.92, -200, 3600, 1000, eta_charge=0.95, soc_max=0.95)
    assert u.soc == 0.95
    assert u.soc_raw == pytest.approx(1.11)
    assert u.violated and u.reason == "above_max"
    low = update_soc(0.08, 100, 3600, 1000, soc_min=0.05)
    assert low.soc == 0.05 and low.soc_raw == pytest.approx(-0.02) and low.reason == "below_min"
    with pytest.raises(ValueError):
        update_soc(0.5, math.nan, 1, 1000)
    with pytest.raises(ValueError):
        update_soc(0.5, 100, 1, 1000, eta_discharge=1.2)


def test_round_trip_efficiency_5_5():
    rte = round_trip_efficiency([0.98, 0.95], [0.95, 0.98])
    assert rte == pytest.approx(0.86676, abs=1e-5)
    assert 100 * rte == pytest.approx(86.68, abs=0.01)


def test_usable_energy_window_5_6():
    cap = actual_capacity_kwh(5016, 0.92)
    assert cap == pytest.approx(4614.72)
    eta = 0.95 * 0.98
    assert dischargeable_energy_kwh(0.50, cap, 0.05, eta) == pytest.approx(1933.34, abs=0.01)
    assert chargeable_energy_kwh(0.50, cap, 0.95, eta) == pytest.approx(2230.54, abs=0.01)
    assert dischargeable_energy_kwh(0.04, cap, 0.05) == 0.0  # 已低于下限：不是负数


def test_ah_drift_5_3():
    assert ah_drift_soc(0.5, 24, 314) == pytest.approx(0.0382, abs=1e-4)


def test_coulomb_counter_and_calibration_5_3():
    true_cc = CoulombCounter(314, 0.5)
    biased = CoulombCounter(314, 0.5)
    for _ in range(3600):
        true_cc.update(10.0, 1.0)
        biased.update(10.0 + 0.5, 1.0)  # 电流传感器零点偏差 +0.5 A
    assert true_cc.soc == pytest.approx(0.5 - 10 / 314)
    assert true_cc.soc - biased.soc == pytest.approx(ah_drift_soc(0.5, 1, 314))
    biased.calibrate(true_cc.soc)
    assert biased.soc == true_cc.soc and biased.throughput_ah == 0
    full = CoulombCounter(314, 0.5)
    full.update(-157, 3600)
    assert full.soc == pytest.approx(1.0)


def _coulomb_trace(hours):
    """按 5.3 追踪表的输入跑前 hours 步，返回 (真实, 零点偏差, 增益误差) 三个 SOC。"""
    currents = [60, 60, 0, 0, -60, -60]
    truth, biased, gained = (CoulombCounter(314, 0.50) for _ in range(3))
    for i in currents[:hours]:
        truth.update(i, 3600)
        biased.update(i + 0.5, 3600)   # 零点偏差 +0.5 A
        gained.update(i * 1.01, 3600)  # 增益误差 +1%
    return truth.soc, biased.soc, gained.soc


@pytest.mark.parametrize("hours, soc_true, soc_bias, soc_gain", [
    (1, 30.892, 30.732, 30.701),
    (2, 11.783, 11.465, 11.401),
    (3, 11.783, 11.306, 11.401),
    (4, 11.783, 11.146, 11.401),
    (5, 30.892, 30.096, 30.701),
    (6, 50.000, 49.045, 50.000),
])
def test_coulomb_trace_table_5_3(hours, soc_true, soc_bias, soc_gain):
    """5.3 追踪表逐行核对（正文保留 3 位小数，单位 %）。"""
    t, b, g = _coulomb_trace(hours)
    assert t * 100 == pytest.approx(soc_true, abs=5e-4)
    assert b * 100 == pytest.approx(soc_bias, abs=5e-4)
    assert g * 100 == pytest.approx(soc_gain, abs=5e-4)


def test_coulomb_trace_conclusions_5_3():
    """5.3 结论：零点偏差单向累积、与充放电无关；增益误差一个循环后抵消；单步手算 30.89%。"""
    t, b, g = _coulomb_trace(6)
    assert b - t == pytest.approx(-0.5 * 6 / 314, abs=1e-12)
    assert g - t == pytest.approx(0.0, abs=1e-12)
    assert _coulomb_trace(1)[0] == pytest.approx(0.50 - 60 / 314)   # 手算一步：0.3089
    assert ah_drift_soc(0.5, 1, 314) * 100 == pytest.approx(0.159, abs=5e-4)  # 每小时 0.159%


@pytest.mark.parametrize("example_name", [
    "ch05_capability.py",
    "ch05_cluster_soc.py",
    "ch05_coulomb_counting.py",
    "ch05_ocv_calibration.py",
    "ch05_scenario_recap.py",
    "ch05_soc_efficiency.py",
    "ch05_soc_window.py",
    "ch05_sop_duration.py",
    "ch05_usable_energy.py",
])
def test_ch05_example_scripts(example_name):
    """第05章全部读者示例可运行，并通过正文中的自检。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / example_name
    runpy.run_path(str(script), run_name="__main__")


def test_aggregate_soc_5_8():
    socs = [0.60, 0.58, 0.55, 0.45]
    assert aggregate_soc(socs, "mean") == pytest.approx(0.545)
    assert aggregate_soc(socs, "min") == 0.45
    assert aggregate_soc(socs, "max") == 0.60
    assert aggregate_soc(socs, "weighted", [400, 400, 400, 320]) == pytest.approx(0.55)
    with pytest.raises(ValueError):
        aggregate_soc(socs, "weighted")
    # 用平均 SOC 估算可放电量会高估（与木桶效应计算对照）
    mean_based = 4 * 400 * (aggregate_soc(socs) - 0.05)
    assert mean_based == pytest.approx(792)
    assert 4 * 400 * (aggregate_soc(socs, "min") - 0.05) == pytest.approx(640)


@pytest.mark.parametrize("soc, zone", [(0.02, "hard_low"), (0.03, "stop_low"), (0.10, "warn_low"),
                                       (0.15, "normal"), (0.50, "target"), (0.55, "target"),
                                       (0.85, "normal"), (0.86, "warn_high"), (0.95, "stop_high"),
                                       (0.98, "hard_high")])
def test_classify_soc_5_7(soc, zone):
    assert classify_soc(soc, SocZones()) == zone


def test_soc_zones_validation_5_7():
    with pytest.raises(ValueError):
        SocZones(op_min=0.2, warn_min=0.15)


def test_soc_window_factors_5_7():
    z = SocZones()
    assert soc_window_factors(0.125, z) == pytest.approx((1.0, 0.5))
    assert soc_window_factors(0.875, z) == pytest.approx((0.5, 1.0))
    assert soc_window_factors(0.05, z) == pytest.approx((1.0, 0.0))


def test_soc_permission_hysteresis_5_7():
    gate = SocPermissionGate(SocZones(), band=0.02)
    seq = [0.12, 0.099, 0.105, 0.115, 0.121, 0.13]
    assert [gate.update(s)[1] for s in seq] == [True, False, False, False, True, True]
    gate = SocPermissionGate(SocZones(), band=0.02)
    seq = [0.89, 0.901, 0.895, 0.885, 0.879]
    assert [gate.update(s)[0] for s in seq] == [True, False, False, False, True]


def test_soc_window_limits_with_gate_5_7():
    gate = SocPermissionGate(SocZones())
    assert soc_window_limits_kw(0.50, SocZones(), 2500, 2500, gate) == pytest.approx((2500, 2500))
    assert soc_window_limits_kw(0.095, SocZones(), 2500, 2500, gate) == pytest.approx((2500, 0))
    # 回到 11%：比例已不为 0，但仍在滞回带内，保持禁放
    assert soc_window_limits_kw(0.11, SocZones(), 2500, 2500, gate) == pytest.approx((2500, 0))


def test_sop_duration_5_10():
    cap = actual_capacity_kwh(5016, 0.92)
    e = dischargeable_energy_kwh(0.20, cap, 0.05, 0.95 * 0.98)
    assert e == pytest.approx(644.45, abs=0.01)
    assert sop_for_duration(2450, e, 15 * 60) == 2450
    assert sop_for_duration(2450, e, 30 * 60) == pytest.approx(1288.89, abs=0.01)
    assert sop_for_duration(2450, e, 3600) == pytest.approx(644.45, abs=0.01)
    assert energy_limited_power_kw(e, 2 * 3600) == pytest.approx(322.22, abs=0.01)
    with pytest.raises(ValueError):
        energy_limited_power_kw(100, 0)


def test_capability_min_with_reason_5_11():
    chg_ac, dis_ac = ac_limits_from_dc(1470, 2500, 0.98)
    assert chg_ac == pytest.approx(1500)
    assert dis_ac == pytest.approx(2450)
    cap = combine_capability(
        charge_limits={"BMS": chg_ac, "PCS": 2500, "SOC 窗口": 2500, "并网点需量": 4000 - 2000 - 50},
        discharge_limits={"BMS": dis_ac, "PCS": 2500, "SOC 窗口": 2500, "并网点防倒送": 2000 + 50 - 0},
    )
    assert cap.available_charge_kw == pytest.approx(1500) and cap.charge_limited_by == "BMS"
    assert cap.available_discharge_kw == 2050 and cap.discharge_limited_by == "并网点防倒送"


def test_ocv_steep_region_calibration_5_4():
    # 7% 处于 5%～10% 的陡峭段：20 mV / 1%，5 mV 误差只造成 0.25% SOC 误差
    assert ocv_slope_v_per_soc(0.07) == pytest.approx(2.0)
    assert soc_error_from_voltage_error(0.005, 0.07) == pytest.approx(0.0025)
    # 图 5.3：在 5% 静置校准后残差 +0.25%；在 50% 平台区强行校准会偏 +5%
    assert soc_from_ocv(ocv_from_soc(0.05) + 0.005) - 0.05 == pytest.approx(0.0025)
    assert soc_from_ocv(ocv_from_soc(0.50) + 0.005) - 0.50 == pytest.approx(0.05)
    assert ah_drift_soc(0.5, 22, 314) == pytest.approx(0.0350, abs=1e-4)


def test_nameplate_overestimate_and_rte_steps_5_5_5_6():
    assert 5016 * 0.45 == pytest.approx(2257.2)
    assert 5016 * 0.45 / 1933.34 - 1 == pytest.approx(0.1675, abs=1e-3)  # 高估约 17%
    assert 100 * 0.98 * 0.95 == pytest.approx(93.1)


def test_self_check_answers_ch05():
    d = update_soc(0.50, 300, 3600, 1000, eta_discharge=0.95)
    assert d.soc == pytest.approx(0.1842, abs=1e-4)
    c = update_soc(0.50, -300, 3600, 1000, eta_charge=0.95)
    assert c.soc == pytest.approx(0.785)
    assert round_trip_efficiency([0.97, 0.96], [0.96, 0.97]) == pytest.approx(0.8671, abs=1e-4)
    e = dischargeable_energy_kwh(0.30, actual_capacity_kwh(5016, 0.92), 0.05, 0.95 * 0.98)
    assert sop_for_duration(2450, e, 3600) == pytest.approx(1074.1, abs=0.1)
    _, dis = ac_limits_from_dc(0, 2000, 0.98)
    assert min_with_reason({"BMS": dis, "PCS": 2500, "防倒送": 1800}) == (1800, "防倒送")
    assert min_with_reason({"BMS": dis, "PCS": 2500, "防倒送": 3000}) == (pytest.approx(1960), "BMS")
    assert ah_drift_soc(0.3, 72, 314) == pytest.approx(0.0688, abs=1e-4)


def test_self_check_answers_ch04():
    e = stack_energy([0.5, 0.5, 0.5, 0.3], 400, 0.05, 0.95)
    assert e.dischargeable_kwh == pytest.approx(400)
    assert 4 * 400 * (aggregate_soc([0.5, 0.5, 0.5, 0.3]) - 0.05) == pytest.approx(640)
    # 4.1 / 4.7：5℃ 时 12 簇按最冷一簇限流
    c, _ = temperature_c_limits(5)
    per_cluster = bms_power_limit_kw(current_from_c_rate(c, 314), 1331.2)
    assert stack_power_limit_kw([per_cluster] * 12) == pytest.approx(501.6, abs=0.1)


def test_min_with_reason_edge_cases_5_11():
    assert min_with_reason({"BMS": 500, "PCS": 500}) == (500, "BMS")  # 并列取先登记的
    with pytest.raises(ValueError):
        min_with_reason({"BMS": math.nan})
    with pytest.raises(ValueError):
        min_with_reason({"BMS": -10})
    with pytest.raises(ValueError):
        min_with_reason({})


def test_ch04_battery_basics_example():
    """第04章配套示例可运行并通过自检。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch04_battery_basics.py"
    runpy.run_path(str(script), run_name="__main__")

