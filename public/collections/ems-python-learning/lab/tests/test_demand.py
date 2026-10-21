import pytest

from ems_lab.constraints import device_interval, export_limit_interval, import_limit_interval, project
from ems_lab.demand import (
    DemandWindowTracker,
    allowed_import_kw,
    basic_charge_by_capacity,
    basic_charge_by_demand,
    control_target_kw,
    demand_power_kw,
    fixed_window_demands,
    monthly_max_demand,
    predict_demand_kw,
    required_extra_discharge_kw,
    sliding_window_demands,
)

MIN = 60.0


def spike_profile():
    """第 14 章示例：基础 1500 kW，第 7～22 分钟有 2400 kW 的 15 分钟尖峰（1 分钟一个点）。"""
    return [2400.0 if 7 <= m < 22 else 1500.0 for m in range(45)]


def test_demand_counts_import_only():
    assert demand_power_kw(-300) == 0.0
    assert demand_power_kw(500) == 500


def test_fixed_vs_sliding_hand_calc():
    p = spike_profile()
    fixed = fixed_window_demands(p, dt_s=MIN, window_s=15 * MIN)
    # 窗口 [0,15)：7 分钟 1500 + 8 分钟 2400 → 1980；[15,30)：7 分钟 2400 + 8 分钟 1500 → 1920
    assert fixed == [pytest.approx(1980), pytest.approx(1920), pytest.approx(1500)]
    sliding = sliding_window_demands(p, dt_s=MIN, window_s=15 * MIN, step_s=MIN)
    assert max(sliding) == pytest.approx(2400)  # 滑差窗口正好对准尖峰
    assert max(sliding) >= max(fixed)
    assert len(sliding) == 45 - 15 + 1


def test_window_misalignment_changes_result():
    p = spike_profile()
    # EMS 窗口比电表晚 7 分钟：EMS 看到的窗口正好套住尖峰
    shifted = fixed_window_demands(p, MIN, 15 * MIN, offset_s=7 * MIN)
    assert shifted[0] == pytest.approx(2400)
    with pytest.raises(ValueError):
        fixed_window_demands(p, 7, 900)  # 周期不是采样间隔的整数倍


def test_negative_import_not_netted():
    # 前 7 分钟倒送 500，后 8 分钟进口 1000：需量 = 8000/15 ≈ 533，而不是净值 4500/15 = 300
    p = [-500.0] * 7 + [1000.0] * 8
    assert fixed_window_demands(p, MIN, 15 * MIN)[0] == pytest.approx(8000 / 15)


def test_predict_and_required_discharge_hand_calc():
    # 前 10 分钟平均 1700 kW → 已累计 283.33 kWh；此刻进口 2200 kW，剩 5 分钟，目标 1800
    e = 1700 * 10 / 60
    assert e == pytest.approx(283.333, abs=1e-3)
    assert predict_demand_kw(e, 2200, 5 * MIN, 15 * MIN) == pytest.approx(1866.67, abs=0.01)
    assert allowed_import_kw(e, 5 * MIN, 1800, 15 * MIN) == pytest.approx(2000)
    assert required_extra_discharge_kw(e, 2200, 5 * MIN, 1800, 15 * MIN) == pytest.approx(200)
    # 不超目标时不需要放电
    assert required_extra_discharge_kw(e, 1900, 5 * MIN, 1800, 15 * MIN) == 0.0
    with pytest.raises(ValueError):
        allowed_import_kw(e, 0, 1800)


def test_late_reaction_doubles_required_power():
    # 负荷在第 5 分钟跳到 2200：第 5 分钟就反应 vs 第 10 分钟才反应
    early = required_extra_discharge_kw(1700 * 5 / 60, 2200, 10 * MIN, 1800, 15 * MIN)
    late = required_extra_discharge_kw(1700 * 5 / 60 + 2200 * 5 / 60, 2200, 5 * MIN, 1800, 15 * MIN)
    assert early == pytest.approx(350)
    assert late == pytest.approx(700)


def test_control_target_margin():
    assert control_target_kw(1800, 50) == 1750
    with pytest.raises(ValueError):
        control_target_kw(1800, -1)


def test_basic_charge_hand_calc():
    # [教学示例单价]：按需量 36 元/kW·月，按容量 24 元/kVA·月，变压器 2500 kVA
    assert basic_charge_by_capacity(2500, 24) == pytest.approx(60000)
    assert basic_charge_by_demand(2000, 36) == pytest.approx(72000)
    assert basic_charge_by_demand(1800, 36) == pytest.approx(64800)
    # 一个月里只有一次 2200 的峰值，其余都在 1800 以下：整月按 2200 计费
    month = [1700.0] * 2975 + [2200.0]
    assert monthly_max_demand(month) == 2200
    assert basic_charge_by_demand(monthly_max_demand(month), 36) - basic_charge_by_demand(1800, 36) == pytest.approx(14400)


def test_tracker_matches_fixed_window_and_rolls_over():
    p = spike_profile()
    tr = DemandWindowTracker(window_s=15 * MIN, target_kw=1800)
    for m, v in enumerate(p):
        tr.update(m * MIN, v)
    tr.update(45 * MIN, 0.0)  # 最后一个样本保持到第 45 分钟，结算第 3 个窗口
    assert tr.completed == [pytest.approx(1980), pytest.approx(1920), pytest.approx(1500)]
    with pytest.raises(ValueError):
        tr.update(10, 0.0)


def test_tracker_predict_and_allowed():
    tr = DemandWindowTracker(window_s=15 * MIN, target_kw=1800)
    for s in range(0, 10 * 60 + 1, 1):  # 前 10 分钟 1700 kW，1 秒一个点
        tr.update(s, 1700.0)
    tr.update(10 * 60 + 1, 2200.0)  # 第 10 分 1 秒起跳到 2200
    assert tr.elapsed_s == pytest.approx(601)
    assert tr.predict() == pytest.approx((1700 * 601 + 2200 * 299) / 900, rel=1e-6)
    assert tr.allowed_import_kw() == pytest.approx((1800 * 900 - 1700 * 601) / 299, rel=1e-6)


def test_charging_raises_demand_and_export_limit_coexists():
    # 第 00 章 ②：负荷 1500，套利想以 600 kW 充电 → 进口 2100 超过 1800；进口上限把充电削到 300
    cs = [device_interval(1000, 1000), import_limit_interval(1500, 0, 1800), export_limit_interval(1500, 0, 0)]
    r = project(-600, cs)
    assert r.final_kw == pytest.approx(-300)
    # 同一时刻可行域 = [−300, +1500]：需量管下限，防倒送管上限
    assert (r.lower_kw, r.upper_kw) == (pytest.approx(-300), pytest.approx(1000))
    assert project(2000, [import_limit_interval(1500, 0, 1800), export_limit_interval(1500, 0, 0)]).final_kw == 1500

# ---------------- 第 14 章自测答案
def test_chapter14_self_check_answers():
    # 1. 容量/需量计收平衡点
    assert basic_charge_by_capacity(3150, 24) / 36 == pytest.approx(2100)
    # 2. 10 分钟 2000 kW 尖峰：固定窗口最坏 1800、最好 1600，滑差 1800
    worst = [2000.0] * 10 + [1400.0] * 20
    best = [1400.0] * 10 + [2000.0] * 10 + [1400.0] * 10
    assert max(fixed_window_demands(worst, MIN, 15 * MIN)) == pytest.approx(1800)
    assert max(fixed_window_demands(best, MIN, 15 * MIN)) == pytest.approx(1600)
    assert max(sliding_window_demands(best, MIN, 15 * MIN, MIN)) == pytest.approx(1800)
    # 3. 已过 12 分钟、已用 350 kWh、进口 1900
    assert predict_demand_kw(350, 1900, 3 * MIN, 15 * MIN) == pytest.approx(1780)
    assert allowed_import_kw(350, 3 * MIN, 1800, 15 * MIN) == pytest.approx(2000)
    assert required_extra_discharge_kw(350, 1900, 3 * MIN, 1800, 15 * MIN) == 0.0
    # 5. 负荷 1400，套利充 800，目标 1800，零倒送，设备 ±1000
    r = project(-800, [device_interval(1000, 1000), import_limit_interval(1400, 0, 1800),
                       export_limit_interval(1400, 0, 0)])
    assert (r.lower_kw, r.upper_kw, r.final_kw) == (pytest.approx(-400), pytest.approx(1000), pytest.approx(-400))


def test_load_exceeds_import_limit_beyond_device_capability():
    # 14.9：负荷 2900 需要放 1100，储能只能放 1000 → 放满并记录缺口 100
    r = project(0, [device_interval(1000, 1000), import_limit_interval(2900, 0, 1800),
                    export_limit_interval(2900, 0, 0)])
    assert r.final_kw == pytest.approx(1000)
def test_ch14_demand_trace_example():
    """14 章最小闭环：逐分钟预算→允许进口→额外放电。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch14_demand_trace.py"
    runpy.run_path(str(script), run_name="__main__")

