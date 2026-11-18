import pytest

from ems_lab.allocation import (
    AllocationResult,
    Unit,
    allocate_by_capability,
    allocate_soc_balance,
    check_allocation,
    round_setpoints,
    simulate_soc,
    units_to_run,
    water_fill,
)


def _units():
    return [
        Unit("PCS1", 400, 400),
        Unit("PCS2", 300, 300),
        Unit("PCS3", 200, 200),
        Unit("PCS4", 100, 100),
    ]


# ---------------------------------------------------------------- 18.8 手算
def test_capability_proportional():
    r = allocate_by_capability(800, _units())
    assert r.setpoints == pytest.approx({"PCS1": 320, "PCS2": 240, "PCS3": 160, "PCS4": 80})
    assert r.unserved_kw == pytest.approx(0) and check_allocation(r, _units()) == []


def test_offline_unit_redistributed_and_unserved_reported():
    us = _units()
    us[0].online = False
    r = allocate_by_capability(800, us)
    assert r.setpoints == pytest.approx({"PCS1": 0, "PCS2": 300, "PCS3": 200, "PCS4": 100})
    assert r.unserved_kw == pytest.approx(200)
    assert any("离线" in n for n in r.notes) and any("未满足" in n for n in r.notes)
    assert check_allocation(r, us) == []


def test_charging_direction():
    r = allocate_by_capability(-500, _units())
    assert r.setpoints["PCS1"] == pytest.approx(-200)
    assert sum(r.setpoints.values()) == pytest.approx(-500)


def _soc_units():
    return [
        Unit("簇A", 500, 500, soc=0.7, energy_kwh=1000),
        Unit("簇B", 500, 500, soc=0.3, energy_kwh=1000),
        Unit("簇C", 500, 500, soc=0.3, energy_kwh=1000),
    ]


def test_soc_balance_discharge_with_water_fill():
    # 放电权重 (SOC−0.1)：0.6:0.2:0.2 → 600/200/200；簇A 顶到 500，余 100 再平分
    r = allocate_soc_balance(1000, _soc_units(), soc_min=0.1, soc_max=0.9)
    assert r.setpoints == pytest.approx({"簇A": 500, "簇B": 250, "簇C": 250})
    assert r.iterations == 2


def test_soc_balance_charge_low_soc_gets_more():
    # 充电权重 (0.9−SOC)：0.2:0.6:0.6 → −100/−300/−300
    r = allocate_soc_balance(-700, _soc_units(), soc_min=0.1, soc_max=0.9)
    assert r.setpoints == pytest.approx({"簇A": -100, "簇B": -300, "簇C": -300})


def test_water_fill_all_saturated():
    alloc, _ = water_fill(1000, {"a": 300, "b": 300}, {"a": 1, "b": 1})
    assert alloc == {"a": 300, "b": 300}


def test_rounding_keeps_total():
    us = [Unit(n, 500, 500) for n in ("A", "B", "C")]
    r = allocate_by_capability(1000, us)
    rr = round_setpoints(r, us, 1.0)
    assert sorted(rr.setpoints.values()) == [333, 333, 334]
    assert rr.allocated_kw == 1000 and check_allocation(rr, us) == []


def test_check_allocation_catches_errors():
    us = _units()
    us[3].online = False
    bad = AllocationResult({"PCS1": 500, "PCS2": 0, "PCS3": 0, "PCS4": 10}, 510, 510, 0, 1)
    issues = check_allocation(bad, us)
    assert any("越限" in i for i in issues) and any("离线" in i for i in issues)


def test_units_to_run():
    assert units_to_run(1200, 500, 4) == 3  # 最少台数
    assert units_to_run(1200, 500, 4, 0.2, "spread") == 4  # 每台 300 ≥ 100
    assert units_to_run(250, 500, 4, 0.2, "spread") == 2  # 每台 125 ≥ 100；开 3 台就只剩 83
    assert units_to_run(3000, 500, 4) == 4  # 全开也不够
    assert units_to_run(0, 500, 4) == 0


def test_soc_gamma_weighting():
    r1 = allocate_soc_balance(700, _soc_units(), 0.1, 0.9, gamma=1)
    r2 = allocate_soc_balance(700, _soc_units(), 0.1, 0.9, gamma=2)
    assert r1.setpoints["簇A"] == pytest.approx(420)  # 0.6:0.2:0.2
    # γ=2：0.36:0.04:0.04 → 簇A 应分 572.7，顶到 500，余 200 由 B、C 平分
    assert r2.setpoints == pytest.approx({"簇A": 500, "簇B": 100, "簇C": 100})
    with pytest.raises(ValueError):
        allocate_soc_balance(600, _soc_units(), gamma=0)


def _spread(socs, k):
    vals = [v[k] for v in socs.values()]
    return max(vals) - min(vals)


def test_soc_balance_trajectories():
    # 4 簇各 250 kW / 1000 kWh，初始 SOC 90/70/60/40%，总放电 600 kW，看 2 h（第 120 个点）
    units = [Unit(f"簇{i}", 250, 250, soc=s, energy_kwh=1000) for i, s in enumerate((0.9, 0.7, 0.6, 0.4))]
    _, cap, un_cap = simulate_soc(units, 600, 4 * 3600, 60, "capability")
    _, g1, un_g1 = simulate_soc(units, 600, 4 * 3600, 60, "soc", gamma=1)
    _, g2, _ = simulate_soc(units, 600, 4 * 3600, 60, "soc", gamma=2)
    assert _spread(cap, 120) == pytest.approx(0.5, abs=0.01)  # 按能力：差距不变
    assert _spread(g1, 120) == pytest.approx(0.25, abs=0.01)  # γ=1：按比例缩小
    assert _spread(g2, 120) < 0.16  # γ=2：收敛更快
    # γ=1 各簇剩余电量比例不变 → 同时放空
    assert (g1["簇0"][120] - 0.05) / (g1["簇3"][120] - 0.05) == pytest.approx(0.85 / 0.35, rel=0.01)
    # 按能力分配：SOC 低的簇先放空，总出力提前不足（约 3.35 h）；SOC 均衡在 4 h 前一直满足
    first_short_cap = next(i for i, u in enumerate(un_cap) if abs(u) > 1)
    assert first_short_cap < 210
    assert all(abs(u) < 1 for u in un_g1[:235])

def test_ch18_arbitration_allocation_example():
    """18 章最小闭环：仲裁→约束→PCS 分配→校验。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch18_arbitration_allocation.py"
    runpy.run_path(str(script), run_name="__main__")

