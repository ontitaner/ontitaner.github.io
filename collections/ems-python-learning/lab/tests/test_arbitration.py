import math

import pytest

from ems_lab.arbitration import (
    Limit,
    Priority,
    Request,
    arbitrate,
    device_limit,
    export_limit,
    import_limit,
    naive_limit_each_then_sum,
)

P = Priority
CAP = device_limit(available_charge_kw=500, available_discharge_kw=800)  # 允许 [−500, +800]


# ---------------------------------------------------------------- 18.4 合成后统一投影
def test_same_direction_naive_overshoots():
    reqs = [Request("计划", P.P3_DISPATCH, 600), Request("一次调频", P.P3_DISPATCH, 300, "delta")]
    assert naive_limit_each_then_sum(reqs, [CAP]) == pytest.approx(900)  # 超出可放 100 kW
    r = arbitrate(reqs, [CAP])
    assert (r.composed_kw, r.final_kw, r.unserved_kw) == (900, 800, 100)
    assert r.limiting == ["BMS/PCS 能力"]


def test_opposite_direction_naive_undershoots():
    reqs = [Request("计划", P.P3_DISPATCH, 900), Request("一次调频", P.P3_DISPATCH, -300, "delta")]
    assert naive_limit_each_then_sum(reqs, [CAP]) == pytest.approx(500)  # 少放了 100 kW
    r = arbitrate(reqs, [CAP])
    assert (r.composed_kw, r.final_kw, r.unserved_kw) == (600, 600, 0)
    assert r.limiting == []


# ---------------------------------------------------------------- 覆盖与过滤
def test_override_keeps_most_important_setpoint():
    reqs = [
        Request("经济", P.P5_ECONOMIC, -400),
        Request("AGC", P.P3_DISPATCH, 500),
        Request("测试", P.P6_MAINTENANCE, 100),
    ]
    r = arbitrate(reqs, [CAP])
    assert r.base_source == "AGC" and r.final_kw == 500
    assert {s for s, _ in r.rejected} == {"经济", "测试"}


def test_invalid_and_expired_requests_rejected():
    reqs = [
        Request("AGC", P.P3_DISPATCH, 500, valid=False),
        Request("计划", P.P3_DISPATCH, 300, expires_at=10),
        Request("经济", P.P5_ECONOMIC, 200),
    ]
    r = arbitrate(reqs, [CAP], now=20)
    assert r.base_source == "经济" and r.final_kw == 200
    reasons = dict(r.rejected)
    assert "无效" in reasons["AGC"] and "过期" in reasons["计划"]


def test_no_request_uses_default():
    r = arbitrate([], [CAP])
    assert r.final_kw == 0 and r.base_source is None and r.notes


def test_emergency_overrides_delta_too():
    reqs = [
        Request("稳控", P.P1_GRID_EMERGENCY, 1000),
        Request("AGC", P.P3_DISPATCH, 500),
        Request("一次调频", P.P3_DISPATCH, -50, "delta"),
    ]
    low_soc = device_limit(500, 200, name="BMS 可放（低 SOC）")
    r = arbitrate(reqs, [low_soc])
    assert r.base_source == "稳控" and r.deltas == []
    assert (r.final_kw, r.unserved_kw) == (200, 800)  # 能力不足必须上报
    assert r.limiting == ["BMS 可放（低 SOC）"]


# ---------------------------------------------------------------- 18.6 冲突故事
def test_agc_vs_hard_export_limit():
    # 负荷 300 kW、无光伏、接入协议不允许倒送 → P_BESS ≤ 300
    lim = export_limit(p_load_kw=300, p_pv_kw=0, p_export_max_kw=0, hard=True)
    r = arbitrate([Request("AGC", P.P3_DISPATCH, 500)], [CAP, lim])
    assert (r.final_kw, r.unserved_kw) == (300, 200)
    assert r.limiting == ["防倒送"]


def test_agc_vs_soft_export_strategy():
    # 防倒送只是 P4 策略（例如避免余电低价上网）：AGC（P3）优先，约束不生效但要记录
    lim = export_limit(300, 0, 0, hard=False, priority=P.P4_STRATEGY_LIMIT)
    r = arbitrate([Request("AGC", P.P3_DISPATCH, 500)], [CAP, lim])
    assert r.final_kw == 500
    assert r.skipped_limits and r.skipped_limits[0][0] == "防倒送"


def test_soft_export_applies_to_economic():
    lim = export_limit(300, 0, 0, hard=False, priority=P.P4_STRATEGY_LIMIT)
    r = arbitrate([Request("经济", P.P5_ECONOMIC, 500)], [CAP, lim])
    assert (r.final_kw, r.unserved_kw) == (300, 200)


def test_economic_vs_demand():
    # 负荷 1500 kW，需量上限 1800 kW → P_BESS ≥ −300；经济策略想充 500
    lim = import_limit(p_load_kw=1500, p_pv_kw=0, p_import_max_kw=1800)
    r = arbitrate([Request("经济", P.P5_ECONOMIC, -500)], [CAP, lim])
    assert r.final_kw == -300 and r.unserved_kw == -200
    assert r.limiting == ["需量"]


def test_soft_limit_conflicting_with_hard_is_reported():
    # 负荷 2200、需量 1800 → 需要至少放 400；但 BMS 只允许放 200：需量无法满足，要上报冲突
    cap = device_limit(500, 200)
    lim = import_limit(2200, 0, 1800)
    r = arbitrate([Request("经济", P.P5_ECONOMIC, 0)], [cap, lim])
    assert r.conflict and r.final_kw == 0
    assert r.skipped_limits[0][0] == "需量"


def test_hard_conflict_outputs_zero():
    a = Limit("许可 A", 100, 200)
    b = Limit("许可 B", -200, -100)
    r = arbitrate([Request("AGC", P.P3_DISPATCH, 150)], [a, b])
    assert r.conflict and r.final_kw == 0


def test_audit_record_fields():
    r = arbitrate([Request("计划", P.P3_DISPATCH, 600), Request("一次调频", P.P3_DISPATCH, 300, "delta")], [CAP],
                  now=12.5, seq=42)
    a = r.as_audit()
    for key in ("seq", "t", "base", "deltas", "composed_kw", "final_kw", "unserved_kw", "limiting", "rejected"):
        assert key in a
    assert a["seq"] == 42 and a["unserved_kw"] == 100


def test_request_validation():
    with pytest.raises(ValueError):
        Request("x", 3, math.nan)
    with pytest.raises(ValueError):
        Request("x", 3, 1.0, kind="other")
    with pytest.raises(ValueError):
        Limit("策略", 0, 1, hard=False)

# ---------------------------------------------------------------- 18.1 场景与自测
def test_scene_18_1():
    reqs = [
        Request("AGC", P.P3_DISPATCH, 500),
        Request("一次调频", P.P3_DISPATCH, -50, "delta"),
        Request("经济", P.P5_ECONOMIC, -200),
    ]
    limits = [device_limit(500, 600), export_limit(300, 0, 0, hard=True)]
    r = arbitrate(reqs, limits)
    assert (r.composed_kw, r.final_kw, r.unserved_kw) == (450, 300, 150)
    assert r.limiting == ["防倒送"] and dict(r.rejected).keys() == {"经济"}


def test_self_check_18():
    cap = device_limit(400, 600)
    same = [Request("计划", 3, 500), Request("一次调频", 3, 200, "delta")]
    assert naive_limit_each_then_sum(same, [cap]) == 700
    assert arbitrate(same, [cap]).final_kw == 600
    opp = [Request("计划", 3, 700), Request("一次调频", 3, -250, "delta")]
    assert naive_limit_each_then_sum(opp, [cap]) == 350
    assert arbitrate(opp, [cap]).final_kw == 450
    r = arbitrate([Request("AGC", 3, 600)], [CAP, export_limit(400, 100, 0)])
    assert (r.final_kw, r.unserved_kw) == (300, 300)

