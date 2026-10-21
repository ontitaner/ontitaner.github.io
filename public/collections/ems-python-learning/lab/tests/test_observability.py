import math
import random

import pytest

from ems_lab.observability import (
    AlarmManager,
    AlarmRule,
    AlarmState,
    DecisionAudit,
    Limit,
    Severity,
    SoeEvent,
    apply_limit_chain,
    availability,
    check_param_consistency,
    count_binding,
    naive_alarm_count,
    round_trip_efficiency,
    soe_sequence,
    success_rate,
    tracking_error,
)

TEMP_RULE = AlarmRule("CELL_T_HIGH", "电芯温度高", Severity.MINOR, raise_at=45.0, clear_at=42.0,
                      on_delay_s=5.0, off_delay_s=10.0)


def noisy_temperature(seed: int = 3):
    """温度在 44～46 ℃ 之间抖动 10 分钟，然后降到 40 ℃。[教学示例]"""
    rng = random.Random(seed)
    ts = list(range(0, 900))
    vals = [45.0 + 0.8 * math.sin(t / 7) + rng.gauss(0, 0.3) if t < 600 else 40.0 for t in ts]
    return ts, vals


# ---------------------------------------------------------------- 告警：防抖、滞回、去重
def test_alarm_debounce_hysteresis_dedup_vs_naive():
    ts, vals = noisy_temperature()
    am = AlarmManager([TEMP_RULE])
    for t, v in zip(ts, vals):
        am.update(t, "电池舱1/簇3", "CELL_T_HIGH", v)
    assert naive_alarm_count(vals, 45.0) > 30  # 单阈值：几十条告警刷屏
    assert len(am.records) == 1  # 延时 + 滞回 + 去重：只有一条
    rec = am.records[0]
    assert rec.state is AlarmState.CLEARED_UNACK  # 恢复了，但没人确认过
    assert rec.t_cleared >= 600 + 10  # 恢复也要持续 10 s
    am.ack(rec.t_cleared + 5, rec.alarm_id, "值班员A")
    assert rec.state is AlarmState.CLOSED and am.active() == []


def test_alarm_lifecycle_ack_then_auto_close():
    am = AlarmManager([TEMP_RULE])
    for t in range(0, 6):
        am.update(t, "舱1", "CELL_T_HIGH", 47.0)
    rec = am.active()[0]
    assert rec.state is AlarmState.ACTIVE_UNACK and rec.t_raised == 5
    am.ack(8, rec.alarm_id, "值班员A")
    assert rec.state is AlarmState.ACTIVE_ACK
    for t in range(10, 21):
        am.update(t, "舱1", "CELL_T_HIGH", 41.0)
    assert rec.state is AlarmState.CLOSED and rec.t_closed == 20
    assert [a for _, _, a in am.log] == ["产生", "确认(值班员A)", "自动恢复并关闭"]


def test_alarm_retrigger_before_close_counts_occurrence():
    am = AlarmManager([AlarmRule("COMM", "通信中断", Severity.MAJOR, raise_at=0.5, clear_at=0.4)])
    seq = [1, 0, 1, 0, 1]  # 通信时断时续
    for t, v in enumerate(seq):
        am.update(t, "PCS1", "COMM", v)
    assert len(am.records) == 1 and am.records[0].occurrences == 3


def test_latched_alarm_needs_manual_reset():
    rule = AlarmRule("FIRE", "消防动作", Severity.CRITICAL, raise_at=0.5, clear_at=0.4, latched=True)
    am = AlarmManager([rule])
    am.update(0, "舱2", "FIRE", 1)
    am.update(1, "舱2", "FIRE", 0)  # 信号消失
    rec = am.records[0]
    assert rec.state is AlarmState.ACTIVE_UNACK and not rec.condition_present
    with pytest.raises(ValueError, match="未确认"):
        am.reset(2, rec.alarm_id, "站长")
    am.ack(3, rec.alarm_id, "站长")
    am.reset(4, rec.alarm_id, "站长")
    assert rec.state is AlarmState.CLOSED and rec.closed_by == "站长"


def test_latched_alarm_cannot_reset_while_present():
    rule = AlarmRule("ESTOP", "急停", Severity.CRITICAL, raise_at=0.5, clear_at=0.4, latched=True)
    am = AlarmManager([rule])
    am.update(0, "站", "ESTOP", 1)
    rec = am.records[0]
    am.ack(1, rec.alarm_id, "站长")
    with pytest.raises(ValueError, match="条件仍存在"):
        am.reset(2, rec.alarm_id, "站长")


def test_low_side_rule_and_invalid_hysteresis():
    am = AlarmManager([AlarmRule("SOC_LOW", "SOC 低", Severity.MINOR, raise_at=0.12, clear_at=0.15, high=False)])
    am.update(0, "堆1", "SOC_LOW", 0.11)
    assert am.active()[0].state is AlarmState.ACTIVE_UNACK
    am.update(1, "堆1", "SOC_LOW", 0.13)  # 在滞回带内，保持
    assert am.active()[0].condition_present
    with pytest.raises(ValueError):
        AlarmRule("X", "x", Severity.MINOR, raise_at=45, clear_at=46)


# ---------------------------------------------------------------- 决策审计：100 kW 为什么只发了 60 kW
def test_decision_audit_explains_100_to_60():
    limits = [
        Limit("可放能力(BMS)", -500, 80),
        Limit("防倒送", -500, 60),
        Limit("Ramp", 40 - 20, 40 + 20),  # 上周期 40 kW，100 kW/s × 0.2 s
    ]
    final, steps = apply_limit_chain(100, limits)
    assert final == 60
    audit = DecisionAudit(
        cycle_id=1024, seq=88, t_mono_s=3600.2, t_wall="2026-01-01T10:00:00.200+08:00", mode="计划跟踪",
        requests=[("计划曲线", 100)], requested_kw=100, steps=steps, final_kw=final,
        soc=0.35, avail_charge_kw=500, avail_discharge_kw=80,
        data_quality={"pcc_meter": "GOOD", "bms": "GOOD"}, config_version="cfg-12", software_version="ems-2.3.1",
        ack="接受", actual_kw=58,
    )
    assert audit.binding() == ["可放能力(BMS)", "防倒送"]
    text = audit.explain()
    assert "可放能力(BMS) [-500, 80] 压到 80" in text and "防倒送 [-500, 60] 压到 60" in text
    assert "Ramp [20, 60] 未限制" in text and text.endswith("下发 60 kW → 实际 58 kW")
    d = audit.to_dict()
    assert d["binding"] == ["可放能力(BMS)", "防倒送"] and d["config_version"] == "cfg-12"
    assert count_binding([audit, audit], "防倒送") == 2


# ---------------------------------------------------------------- 参数一致性
def test_param_consistency_detects_mismatch_and_missing():
    expected = {"pfr_deadband_hz": 0.03, "pfr_droop": 0.02, "ramp_kw_s": 100.0}
    readback = {"pfr_deadband_hz": 0.05, "pfr_droop": 0.02, "ramp_kw_s": None}
    bad = {m.name: m.note for m in check_param_consistency(expected, readback)}
    assert bad == {"pfr_deadband_hz": "数值不一致", "ramp_kw_s": "设备未上送或读取失败"}


# ---------------------------------------------------------------- SOE
def test_soe_sorted_by_device_timestamp_not_arrival():
    arrived = [
        SoeEvent(1_000_120, "PCS1", "直流过流跳闸", 1, t_received_ms=1_001_900),
        SoeEvent(1_000_080, "BMS1", "簇3 接触器断开", 1, t_received_ms=1_002_300),
        SoeEvent(1_000_050, "BMS1", "簇3 电芯过温三级", 1, t_received_ms=1_002_300),
    ]
    order = [e.point for e in soe_sequence(arrived)]
    assert order == ["簇3 电芯过温三级", "簇3 接触器断开", "直流过流跳闸"]


# ---------------------------------------------------------------- KPI
def test_availability_merges_overlaps():
    day = 86400.0
    assert availability(day, [(3600, 7200), (5400, 9000)]) == pytest.approx(1 - 5400 / day)
    assert availability(day, []) == 1.0


def test_round_trip_efficiency_with_soc_correction():
    assert round_trip_efficiency(1000, 850, 0.5, 0.5, 1000) == pytest.approx(0.85)
    assert round_trip_efficiency(1000, 850, 0.50, 0.52, 1000) == pytest.approx(0.87)


def test_tracking_and_success_rate():
    s = tracking_error([100, 100, 100, 100], [98, 101, 80, 100], tol_kw=5)
    assert s.max_abs_kw == 20 and s.within_ratio == 0.75 and s.mean_abs_kw == pytest.approx(5.75)
    assert success_rate(8638, 8640) == pytest.approx(0.99977, abs=1e-5)
def test_ch20_observability_trace_example():
    """20 章最小闭环：告警生命周期、审计、KPI。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch20_observability_trace.py"
    runpy.run_path(str(script), run_name="__main__")

