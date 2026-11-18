from datetime import date, datetime, timedelta, timezone

import pytest

from ems_lab.arbitrage import (
    SLOTS_PER_DAY,
    BatterySpec,
    PlanCurve,
    PlanDateMismatch,
    TouPeriod,
    cycle_net_profit,
    greedy_plan,
    plan_energy_cost,
    rule_based_plan,
    slot_deviation,
    soc_step,
    spread_threshold,
    tou_prices,
    validate_plan,
)
from ems_lab.constraints import device_interval, export_limit_interval, import_limit_interval, project

# 第 13 章的教学示例电价（元/kWh），非任何地区真实电价
PERIODS = [
    TouPeriod(0, 8, "谷", 0.30),
    TouPeriod(8, 11, "峰", 1.10),
    TouPeriod(11, 13, "平", 0.65),
    TouPeriod(13, 15, "谷", 0.30),
    TouPeriod(15, 17, "平", 0.65),
    TouPeriod(17, 19, "峰", 1.10),
    TouPeriod(19, 21, "尖峰", 1.35),
    TouPeriod(21, 24, "平", 0.65),
]
BAT = BatterySpec(capacity_kwh=4000, p_max_charge_kw=1000, p_max_discharge_kw=1000,
                  soc_min=0.10, soc_max=0.90, eta_charge=0.92, eta_discharge=0.92)


def test_tou_prices_expand_and_validate():
    prices = tou_prices(PERIODS)
    assert len(prices) == SLOTS_PER_DAY
    assert prices[0] == 0.30 and prices[32] == 1.10 and prices[80] == 1.35 and prices[95] == 0.65
    with pytest.raises(ValueError, match="覆盖"):
        tou_prices(PERIODS[:-1])
    with pytest.raises(ValueError, match="重叠"):
        tou_prices(PERIODS + [TouPeriod(1, 2, "谷", 0.3)])
    with pytest.raises(ValueError, match="跨零点"):
        tou_prices([TouPeriod(22, 6, "谷", 0.3)])


def test_cycle_profit_hand_calc():
    # 放 1000 kWh，谷 0.30 充、峰 1.10 放，往返效率 85%，退化成本 0.10 元/kWh
    r = cycle_net_profit(1000, price_discharge=1.10, price_charge=0.30, round_trip_eff=0.85,
                         degradation_cost_per_kwh=0.10)
    assert r.charge_kwh == pytest.approx(1176.47, abs=0.01)
    assert r.charge_cost == pytest.approx(352.94, abs=0.01)
    assert r.revenue == pytest.approx(1100)
    assert r.degradation_cost == pytest.approx(100)
    assert r.net == pytest.approx(647.06, abs=0.01)


def test_spread_threshold_hand_calc():
    # 谷充：0.30 × (1/0.85 − 1) + 0.10 ≈ 0.153
    assert spread_threshold(0.30, 0.85, 0.10) == pytest.approx(0.1529, abs=1e-4)
    # 平充：门槛更高，因为损耗掉的电更贵
    assert spread_threshold(0.65, 0.85, 0.10) == pytest.approx(0.2147, abs=1e-4)
    # 正好在门槛上：净收益为 0
    th = spread_threshold(0.30, 0.85, 0.10)
    assert cycle_net_profit(1000, 0.30 + th, 0.30, 0.85, 0.10).net == pytest.approx(0, abs=1e-9)
    # 平→峰：价差 0.45 大于门槛，赚钱；谷→平 0.35 也赚钱
    assert cycle_net_profit(1, 1.10, 0.65, 0.85, 0.10).net == pytest.approx(0.2353, abs=1e-4)
    assert cycle_net_profit(1, 0.65, 0.30, 0.85, 0.10).net == pytest.approx(0.1971, abs=1e-4)
    with pytest.raises(ValueError):
        spread_threshold(0.3, 0)


def test_soc_step_efficiency_direction():
    # 放电 1000 kW × 0.25 h = 250 kWh，电池要多出 250/0.92
    assert soc_step(0.5, 1000, 0.25, BAT) == pytest.approx(0.5 - 250 / 0.92 / 4000)
    assert soc_step(0.5, -1000, 0.25, BAT) == pytest.approx(0.5 + 250 * 0.92 / 4000)


def test_rule_based_plan_is_infeasible_without_soc_check():
    prices = tou_prices(PERIODS)
    plan = rule_based_plan(prices, BAT, charge_at_or_below=0.30, discharge_at_or_above=1.10)
    check = validate_plan(plan, BAT, soc0=0.10)
    # 谷时 8 小时满功率充电 = 8000 kWh，远超 4000 kWh 容量
    assert not check.feasible
    assert any("超过上限" in v for v in check.violations)


def test_validate_plan_power_and_start_soc():
    plan = [0.0] * SLOTS_PER_DAY
    plan[0] = 1200
    check = validate_plan(plan, BAT, soc0=0.5)
    assert any("超过可放" in v for v in check.violations)
    assert not validate_plan([0.0] * 96, BAT, soc0=0.95).feasible
    assert validate_plan([0.0] * 96, BAT, soc0=0.5, soc_end_min=0.6).violations[-1].startswith("日末")


def test_greedy_plan_feasible_two_cycles_and_soc_neutral():
    prices = tou_prices(PERIODS)
    g = greedy_plan(prices, BAT, soc0=0.10, degradation_cost_per_kwh=0.10)
    check = validate_plan(g.plan_kw, BAT, soc0=0.10)
    assert check.feasible, check.violations
    assert check.soc[-1] == pytest.approx(0.10, abs=1e-9)  # 日末回到起点
    # 两充两放：上午谷充、早峰放；午间谷充、晚峰/尖峰放
    assert any(p < 0 for p in g.plan_kw[:32])
    assert any(p > 0 for p in g.plan_kw[32:44])
    assert any(p < 0 for p in g.plan_kw[52:60])
    assert any(p > 0 for p in g.plan_kw[68:84])
    # 尖峰时段比峰时段优先放电
    assert sum(g.plan_kw[76:84]) >= sum(g.plan_kw[68:76])
    # 期望收益 = 按计划算出的电费节省 − 退化成本
    discharged = sum(max(p, 0) for p in g.plan_kw) * 0.25
    assert g.expected_profit == pytest.approx(plan_energy_cost(g.plan_kw, prices) - 0.10 * discharged)
    assert g.expected_profit > 0


def test_greedy_hand_example_four_slots():
    # 第 13 章手算：4 个时段、无损耗、无退化，电池 250 kWh 正好是满功率一个时段的电量
    bat = BatterySpec(capacity_kwh=250, p_max_charge_kw=1000, p_max_discharge_kw=1000,
                      soc_min=0.0, soc_max=1.0, eta_charge=1.0, eta_discharge=1.0)
    g = greedy_plan([0.30, 1.10, 0.65, 1.35], bat, soc0=0.0)
    # 第一对 (0→3) 价差最大 1.05；第二对 (2→1) “先放后充”，价差 0.45
    assert g.pairs == [(0, 3, pytest.approx(1000)), (2, 1, pytest.approx(1000))]
    assert g.plan_kw == [pytest.approx(-1000), pytest.approx(1000), pytest.approx(-1000), pytest.approx(1000)]
    assert g.expected_profit == pytest.approx(375)  # 250 × (1.05 + 0.45) = 250 × (0.80 + 0.70)
    assert validate_plan(g.plan_kw, bat, soc0=0.0).soc == [0, 1, 0, 1, 0]


def test_greedy_plan_skips_unprofitable_spread():
    flat = [0.65] * 48 + [0.70] * 48  # 价差 0.05，低于门槛
    g = greedy_plan(flat, BAT, soc0=0.5, degradation_cost_per_kwh=0.10)
    assert all(p == 0 for p in g.plan_kw)


def test_plan_invalid_when_start_soc_differs():
    # 按 SOC 50% 编的“先放后充”计划，实际起点只有 20%：执行到中途越下限
    prices = [1.10] * 16 + [0.30] * 80
    g = greedy_plan(prices, BAT, soc0=0.50, degradation_cost_per_kwh=0.10)
    assert validate_plan(g.plan_kw, BAT, soc0=0.50).feasible
    bad = validate_plan(g.plan_kw, BAT, soc0=0.20)
    assert not bad.feasible and any("低于下限" in v for v in bad.violations)


# ---------------- 计划曲线：跨日与时区
CST = timezone(timedelta(hours=8))


def test_plan_curve_slot_index_and_timezone():
    pts = tuple(float(k) for k in range(96))
    plan = PlanCurve(date(2024, 7, 2), pts, CST)
    assert plan.value_at(datetime(2024, 7, 2, 8, 14, 59, tzinfo=CST)) == 32
    assert plan.value_at(datetime(2024, 7, 2, 8, 15, 0, tzinfo=CST)) == 33
    # UTC 16:00（7 月 1 日）= 北京时间 7 月 2 日 00:00 → 第 0 点
    assert plan.slot_index(datetime(2024, 7, 1, 16, 0, tzinfo=timezone.utc)) == 0
    # UTC 7 月 2 日 16:00 = 北京时间 7 月 3 日：不属于这条计划
    with pytest.raises(PlanDateMismatch):
        plan.slot_index(datetime(2024, 7, 2, 16, 0, tzinfo=timezone.utc))
    with pytest.raises(ValueError, match="时区"):
        plan.slot_index(datetime(2024, 7, 2, 8, 0))
    with pytest.raises(ValueError):
        PlanCurve(date(2024, 7, 2), pts[:95], CST)


def test_slot_deviation():
    assert slot_deviation(800, 190) == (pytest.approx(-10), pytest.approx(-0.05))
    assert slot_deviation(0, 0) == (0, 0.0)


def test_plan_is_cut_by_realtime_constraints():
    # 计划放电 800，但此刻负荷 600、光伏 400、零倒送：防倒送把它截到 200
    cs = [device_interval(1000, 1000), export_limit_interval(600, 400, 0),
          import_limit_interval(600, 400, 1800)]
    r = project(800, cs)
    assert r.final_kw == pytest.approx(200) and r.binding == "防倒送"

# ---------------- 第 13 章正文与自测中的其他手算
def test_higher_degradation_skips_flat_to_peak_pairs():
    eta = BAT.round_trip_eff
    assert cycle_net_profit(1, 1.10, 0.65, eta, 0.10).net > 0
    assert cycle_net_profit(1, 1.10, 0.65, eta, 0.35).net == pytest.approx(-0.018, abs=1e-3)
    assert cycle_net_profit(1, 1.35, 0.65, eta, 0.35).net > 0  # 平充 → 尖峰放仍赚钱
    prices = tou_prices(PERIODS)
    g = greedy_plan(prices, BAT, soc0=0.10, degradation_cost_per_kwh=0.35)
    assert not any(prices[c] == 0.65 and prices[d] == 1.10 for c, d, _ in g.pairs)
    assert validate_plan(g.plan_kw, BAT, soc0=0.10).feasible


def test_greedy_full_day_numbers_in_text():
    prices = tou_prices(PERIODS)
    g = greedy_plan(prices, BAT, soc0=0.10, degradation_cost_per_kwh=0.10)
    e = lambda a, b: sum(g.plan_kw[a:b]) * 0.25  # noqa: E731
    assert e(0, 32) == pytest.approx(-3478.3, abs=0.1)
    assert e(32, 44) == pytest.approx(2944, abs=0.1)
    assert e(44, 52) == pytest.approx(-1478.3, abs=0.1)
    assert e(52, 60) == pytest.approx(-2000, abs=0.1)
    assert e(68, 76) == pytest.approx(944, abs=0.1)
    assert e(76, 84) == pytest.approx(2000, abs=0.1)
    assert g.expected_profit == pytest.approx(3784, abs=1)


def test_chapter13_self_check_answers():
    r = cycle_net_profit(2000, 1.00, 0.35, 0.88, 0.08)
    assert r.net == pytest.approx(1044.55, abs=0.01)
    assert spread_threshold(0.35, 0.88, 0.08) == pytest.approx(0.1277, abs=1e-4)
    cs = [device_interval(1000, 1000), export_limit_interval(900, 500, 0)]
def test_ch13_arbitrage_trace_example():
    """13 章最小闭环：电价→计划→SOC→收益。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch13_arbitrage_trace.py"
    runpy.run_path(str(script), run_name="__main__")

