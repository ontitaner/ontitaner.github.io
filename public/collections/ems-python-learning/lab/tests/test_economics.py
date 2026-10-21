"""第 01、03 章手算例子的测试。数值均为 [教学示例]。"""
import math

import pytest

from ems_lab.economics import (
    annual_net_cashflow,
    arbitrage_cycle,
    breakeven_discharge_price,
    breakeven_spread,
    charge_energy_for_discharge,
    degradation_cost_per_kwh,
    demand_charge_saving,
    load_curve_stats,
    max_ramp_up_per_h,
    net_load,
    net_profit_per_kwh,
    one_way_to_round_trip,
    round_trip_efficiency,
    round_trip_to_one_way,
    schedule_energy_revenue,
    simple_payback_years,
    three_phase_line_loss_kw,
    worth_cycling,
)

# 第 01 章 1.6 的逐时负荷与光伏（GW，0:00～23:00）[教学示例]，与 figures/ch01.py 保持一致
LOAD_GW = [32, 31, 30, 29.5, 29.5, 30.5, 33, 36, 39.5, 42, 43.5, 44,
           42.5, 42, 43, 43.5, 44, 45.5, 47.5, 48, 47, 44.5, 40, 35.5]
PV_GW = [0, 0, 0, 0, 0, 0, 0.5, 2.5, 6, 10, 13.5, 16,
         17, 16.5, 14.5, 11, 7, 3, 0.5, 0, 0, 0, 0, 0]


# ---------------- 第 01 章 ----------------


@pytest.mark.parametrize(
    "u_kv, loss_kw",
    [(10, 1000.0), (35, 81.63), (110, 8.264), (220, 2.066), (500, 0.4)],
)
def test_line_loss_by_voltage_level(u_kv, loss_kw):
    # 1.3 手算：输送 10 MW，每相电阻 1 Ω，功率因数 1
    assert three_phase_line_loss_kw(10_000, u_kv, 1.0) == pytest.approx(loss_kw, rel=1e-3)


def test_line_loss_scaling_and_pf():
    base = three_phase_line_loss_kw(10_000, 10, 1.0)
    assert three_phase_line_loss_kw(10_000, 20, 1.0) == pytest.approx(base / 4)  # 电压翻倍 → 1/4
    assert three_phase_line_loss_kw(10_000, 10, 1.0, pf=0.8) == pytest.approx(base / 0.64)  # 无功也吃损耗
    with pytest.raises(ValueError):
        three_phase_line_loss_kw(10_000, 0, 1.0)


def test_duck_curve_point_and_stats():
    net = net_load(LOAD_GW, PV_GW)
    assert net[13] == pytest.approx(25.5)  # 13:00 负荷 42 − 光伏 16.5
    assert net[19] == pytest.approx(48)  # 19:00 光伏已为 0

    s_load = load_curve_stats(LOAD_GW)
    assert (s_load.peak, s_load.valley, s_load.peak_valley_diff) == (48, 29.5, 18.5)
    assert s_load.peak_valley_ratio == pytest.approx(0.385, abs=1e-3)
    assert s_load.load_factor == pytest.approx(0.819, abs=1e-3)
    assert sum(LOAD_GW) == pytest.approx(943.5)  # 逐时 GW 相加 = 全天 GWh
    assert sum(PV_GW) == pytest.approx(118)  # 光伏电量约占 12.5%

    s_net = load_curve_stats(net)
    assert (s_net.peak, s_net.valley, s_net.peak_valley_diff) == (48, 25.5, 22.5)
    assert s_net.peak_valley_ratio == pytest.approx(0.469, abs=1e-3)
    assert s_net.load_factor == pytest.approx(0.717, abs=1e-3)


def test_duck_curve_ramp():
    net = net_load(LOAD_GW, PV_GW)
    assert max_ramp_up_per_h(LOAD_GW, 1.0) == pytest.approx(3.5)  # 7:00→8:00
    assert max_ramp_up_per_h(net, 1.0) == pytest.approx(5.5)  # 16:00→17:00
    # 5.5 GW/h ≈ 91.7 MW/min；煤电按每分钟 1.5% 额定功率爬坡，需要约 6.1 GW 机组同时爬
    mw_per_min = max_ramp_up_per_h(net, 1.0) * 1000 / 60
    assert mw_per_min == pytest.approx(91.7, abs=0.1)
    assert mw_per_min / 0.015 / 1000 == pytest.approx(6.1, abs=0.05)
    with pytest.raises(ValueError):
        load_curve_stats([])


def test_why_electricity_is_hard_to_store():
    # 1.4 手算：在线机组 50 GW、H = 4 s，转子动能 = 4 × 50 GW·s = 200 GW·s ≈ 55.6 MWh，只够满发 4 秒
    rotor_mwh = 4 * 50_000 / 3600  # MW·s → MWh
    assert rotor_mwh == pytest.approx(55.6, abs=0.1)
    assert rotor_mwh / (sum(LOAD_GW) * 1000) < 1e-4  # 不到全天用电量的万分之一
    # 20 GWh 储能约占全天用电量 943.5 GWh 的 2.1%
    assert 20 / sum(LOAD_GW) == pytest.approx(0.021, abs=5e-4)


def test_ch01_self_check_answers():
    # 自测 1：35 kV → 110 kV，损耗约降为 1/9.9
    ratio = three_phase_line_loss_kw(10_000, 35, 1.0) / three_phase_line_loss_kw(10_000, 110, 1.0)
    assert ratio == pytest.approx((110 / 35) ** 2)
    assert ratio == pytest.approx(9.9, abs=0.05)
    # 自测 3：峰 60、谷 36、平均 50
    s = load_curve_stats([60, 36, 54])
    assert (s.peak_valley_diff, s.peak_valley_ratio) == (24, pytest.approx(0.4))
    assert s.load_factor == pytest.approx(0.833, abs=1e-3)
    # 自测 4：净负荷 22 → 38 GW，1 小时上升 16 GW
    net = net_load([40, 44], [18, 6])
    assert net == [22, 38]
    assert max_ramp_up_per_h(net, 1.0) == pytest.approx(16)


def test_duck_curve_with_storage():
    # 1.6 手算：5 GW 储能 11～14 时充电（20 GWh），17～20 时以 4.25 GW 放电（17 GWh，η=0.85）
    p_bess = [0.0] * 24
    for h in (11, 12, 13, 14):
        p_bess[h] = -5.0
    for h in (17, 18, 19, 20):
        p_bess[h] = 4.25
    assert round_trip_efficiency(4.25 * 4, 5 * 4) == pytest.approx(0.85)
    # 储能放电为正：放电让电网要供的净负荷减少，充电让它增加
    after = [n - p for n, p in zip(net_load(LOAD_GW, PV_GW), p_bess)]
    s = load_curve_stats(after)
    assert (s.peak, s.valley, s.peak_valley_diff) == (44.5, 29.5, 15.0)
    assert after.index(s.peak) == 21  # 新的高峰挪到了 21:00
    assert max_ramp_up_per_h(after, 1.0) == pytest.approx(4.5)


# ---------------- 第 03 章：效率 ----------------


def test_efficiency_conversions():
    assert round_trip_efficiency(1700, 2000) == pytest.approx(0.85)
    assert charge_energy_for_discharge(1800, 0.85) == pytest.approx(2117.65, abs=0.01)
    assert one_way_to_round_trip(0.92, 0.92) == pytest.approx(0.8464)
    assert round_trip_to_one_way(0.85) == pytest.approx(0.922, abs=1e-3)
    with pytest.raises(ValueError):
        charge_energy_for_discharge(100, 0)
    with pytest.raises(ValueError):
        one_way_to_round_trip(1.2, 0.9)


# ---------------- 第 03 章：套利 ----------------


def test_degradation_cost():
    # 电池重置成本 108 万元，6000 次循环，每次放 1800 kWh → 0.10 元/kWh
    assert degradation_cost_per_kwh(1_080_000, 6000, 1800) == pytest.approx(0.10)
    with pytest.raises(ValueError):
        degradation_cost_per_kwh(1, 0, 1800)


def test_arbitrage_cycle_breakdown():
    # 3.6 手算：放 1800 kWh，峰 1.10、谷 0.30，η=0.85，退化 0.10 元/kWh
    r = arbitrage_cycle(1800, 1.10, 0.30, 0.85, 0.10)
    assert r.e_ch_kwh == pytest.approx(2117.65, abs=0.01)
    assert r.discharge_revenue == pytest.approx(1980)
    assert r.ideal_charge_cost == pytest.approx(540)
    assert r.efficiency_loss_cost == pytest.approx(95.29, abs=0.01)
    assert r.charge_cost == pytest.approx(635.29, abs=0.01)
    assert r.degradation_cost == pytest.approx(180)
    assert r.gross_profit == pytest.approx(1344.71, abs=0.01)
    assert r.net_profit == pytest.approx(1164.71, abs=0.01)
    # 分解项加起来必须等于净收益（瀑布图的一致性）
    parts = r.discharge_revenue - r.ideal_charge_cost - r.efficiency_loss_cost - r.degradation_cost
    assert parts == pytest.approx(r.net_profit)


def test_breakeven_thresholds():
    assert breakeven_discharge_price(0.30, 0.85, 0.10) == pytest.approx(0.4529, abs=1e-4)
    assert breakeven_spread(0.30, 0.85, 0.10) == pytest.approx(0.1529, abs=1e-4)
    assert breakeven_spread(0.65, 0.85, 0.10) == pytest.approx(0.2147, abs=1e-4)
    assert breakeven_spread(0.30, 1.0, 0.0) == pytest.approx(0.0)  # 无损耗、无退化：有价差就赚


def test_same_spread_different_outcome():
    # 同样 0.20 元价差：谷 0.30 充 → 0.50 放 赚钱；平 0.65 充 → 0.85 放 亏钱
    assert net_profit_per_kwh(0.50, 0.30, 0.85, 0.10) == pytest.approx(0.0471, abs=1e-4)
    assert net_profit_per_kwh(0.85, 0.65, 0.85, 0.10) == pytest.approx(-0.0147, abs=1e-4)
    assert worth_cycling(0.50, 0.30, 0.85, 0.10)
    assert not worth_cycling(0.85, 0.65, 0.85, 0.10)
    # 加 0.05 元/kWh 安全裕度后，第一种也不做了
    assert not worth_cycling(0.50, 0.30, 0.85, 0.10, margin_per_kwh=0.05)


def test_second_cycle_flat_to_peak():
    # 两充两放的第二次：平 0.65 充 → 峰 1.10 放
    assert net_profit_per_kwh(1.10, 0.65, 0.85, 0.10) == pytest.approx(0.2353, abs=1e-4)
    assert arbitrage_cycle(1800, 1.10, 0.65, 0.85, 0.10).net_profit == pytest.approx(423.53, abs=0.01)


# ---------------- 第 03 章：其他收益与回收期 ----------------


def test_demand_charge_saving():
    assert demand_charge_saving(500, 40) == pytest.approx(20_000)
    assert demand_charge_saving(500, 40, months=12) == pytest.approx(240_000)


def test_schedule_energy_revenue_sign_convention():
    # 充 1000 kW × 2 h（电价 0.20、0.25），放 850 kW × 2 h（电价 0.90、1.00）
    p = [-1000, -1000, 850, 850]
    price = [0.20, 0.25, 0.90, 1.00]
    assert schedule_energy_revenue(p, price, 1.0) == pytest.approx(1165)
    assert round_trip_efficiency(850 * 2, 1000 * 2) == pytest.approx(0.85)
    with pytest.raises(ValueError):
        schedule_energy_revenue([1], [1, 2], 1.0)


def test_simple_payback():
    gross = arbitrage_cycle(1800, 1.10, 0.30, 0.85).gross_profit  # 投资回收用电费差，不再扣退化
    cash = annual_net_cashflow(gross, 330, 40_000)
    assert cash == pytest.approx(403_753, abs=1)
    assert simple_payback_years(2_000_000, cash) == pytest.approx(4.95, abs=0.01)
    assert math.isinf(simple_payback_years(2_000_000, -1))


# ---------------- 第 03 章：补充手算与自测 ----------------


def test_naive_vs_real_estimate():
    # 3.1：“价差 0.8 × 2000 度 = 1600 元”的朴素算法，对比真实净收益 1164.71 元
    naive = (1.10 - 0.30) * 2000
    real = arbitrage_cycle(1800, 1.10, 0.30, 0.85, 0.10).net_profit
    assert naive == pytest.approx(1600)
    assert real / naive == pytest.approx(0.728, abs=1e-3)


def test_low_efficiency_breakeven_and_two_cycles():
    assert breakeven_spread(0.30, 0.75, 0.10) == pytest.approx(0.20)
    assert breakeven_spread(0.30, 0.85, 0.0) == pytest.approx(0.053, abs=1e-3)  # 不计退化时的阈值
    first = arbitrage_cycle(1800, 1.10, 0.30, 0.85, 0.10).net_profit
    second = arbitrage_cycle(1800, 1.10, 0.65, 0.85, 0.10).net_profit
    assert first + second == pytest.approx(1588.24, abs=0.01)


def test_curtailment_recovery():
    # 3.5：限电时段充入本要弃掉的 2000 kWh（充电成本按 0），晚间放出 1700 kWh，上网电价 0.35
    r = arbitrage_cycle(1700, 0.35, 0.0, 0.85, 0.10)
    assert r.e_ch_kwh == pytest.approx(2000)
    assert r.discharge_revenue == pytest.approx(595)
    assert r.charge_cost == pytest.approx(0)
    assert r.degradation_cost == pytest.approx(170)
    assert r.net_profit == pytest.approx(425)
    assert breakeven_discharge_price(0.0, 0.85, 0.10) == pytest.approx(0.10)  # 只要覆盖退化


def test_calendar_life_limits_throughput():
    # 深入：330 次/年 × 15 年 = 4950 次，少于 6000 次循环寿命，按实际吞吐量折算退化成本更高
    cycles = 330 * 15
    assert cycles == 4950
    assert degradation_cost_per_kwh(1_080_000, cycles, 1800) == pytest.approx(0.1212, abs=1e-4)


def test_ch03_self_check_answers():
    assert charge_energy_for_discharge(900, 0.90) == pytest.approx(1000)  # 自测 1
    assert net_profit_per_kwh(0.95, 0.25, 0.88, 0.08) == pytest.approx(0.5859, abs=1e-4)  # 自测 2
    assert arbitrage_cycle(3600, 0.95, 0.25, 0.88, 0.08).net_profit == pytest.approx(2109.27, abs=0.01)
    assert breakeven_discharge_price(0.40, 0.85, 0.10) == pytest.approx(0.5706, abs=1e-4)  # 自测 3
    assert breakeven_spread(0.40, 0.85, 0.10) == pytest.approx(0.1706, abs=1e-4)
    assert degradation_cost_per_kwh(1_500_000, 5000, 2500) == pytest.approx(0.12)  # 自测 5
    assert simple_payback_years(3_000_000, 500_000) == pytest.approx(6.0)  # 自测 6
def test_ch01_example_script():
    """第01章读者示例：线路损耗、净负荷和储能调节。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch01_power_system.py"
    runpy.run_path(str(script), run_name="__main__")


def test_ch03_economics_trace_example():
    """第03章读者示例可运行并通过自检。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch03_economics_trace.py"
    runpy.run_path(str(script), run_name="__main__")

