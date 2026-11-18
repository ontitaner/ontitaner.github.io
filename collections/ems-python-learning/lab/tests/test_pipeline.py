"""第 09 章：控制流水线骨架的测试。手算例子：1 MW 储能，BMS 降额到可放 800 kW。"""
import pytest

from ems_lab.datapoint import Measurement, Quality
from ems_lab.frequency import PrimaryFrequencyConfig
from ems_lab.pipeline import (
    AGC_TARGET,
    BMS_CHG,
    BMS_DIS,
    BMS_SOC,
    METER_F,
    METER_P,
    PCS_P,
    AgcStrategy,
    Capability,
    ControlPipeline,
    ControlRequest,
    MockPcs,
    OperatingState,
    PipelineConfig,
    PowerCommand,
    PrimaryFrequencyStrategy,
    ScheduleStrategy,
    arbitrate,
    naive_limit_each_then_sum,
    project,
    take_snapshot,
    validate,
)

PFR_CFG = PrimaryFrequencyConfig(p_rated_kw=1000, droop_ratio=0.02, deadband_hz=0.03, limit_ratio=0.10)


def good(name, value, t, unit="kW"):
    return Measurement(name, value, unit, Quality.GOOD, t, t)


def site(t, chg=1000.0, dis=800.0, soc=0.5, p_bess=0.0, p_pcc=-500.0, f=50.0, agc=900.0):
    pts = {
        BMS_CHG: good(BMS_CHG, chg, t),
        BMS_DIS: good(BMS_DIS, dis, t),
        BMS_SOC: good(BMS_SOC, soc, t, ""),
        PCS_P: good(PCS_P, p_bess, t),
        METER_P: good(METER_P, p_pcc, t),
        METER_F: good(METER_F, f, t, "Hz"),
    }
    if agc is not None:
        pts[AGC_TARGET] = good(AGC_TARGET, agc, t)
    return pts


def state(chg=1000.0, dis=800.0, p_bess=0.0, p_pcc=None):
    return OperatingState(0.0, Capability(chg, dis, "test"), p_bess, p_pcc, 50.0, 0.5, None)


# ---------------- 9.3 为什么不能各自限幅后相加
def test_limit_each_then_sum_exceeds_capability():
    # AGC +900，一次调频 +70（49.90 Hz），BMS 可放 800
    reqs = [ControlRequest("agc", 900, "base", 20, ""), ControlRequest("pfr", 70, "delta", 30, "")]
    cap = Capability(1000, 800, "BMS")
    naive = naive_limit_each_then_sum(reqs, cap)
    assert naive == 870  # 800 + 70：超出可放能力 70 kW
    combined, _ = arbitrate(reqs)
    assert combined == 970
    res = project(combined, state())
    assert res.p_out_kw == 800 and res.active == ("可放能力",)


def test_limit_each_then_sum_under_delivers_with_opposite_signs():
    # 频率 50.10 Hz → 一次调频 −70；AGC +900
    reqs = [ControlRequest("agc", 900, "base", 20, ""), ControlRequest("pfr", -70, "delta", 30, "")]
    cap = Capability(1000, 800, "BMS")
    assert naive_limit_each_then_sum(reqs, cap) == 730  # 800 − 70：少放了 70 kW，一次调频被“吃掉”
    combined, _ = arbitrate(reqs)
    assert project(combined, state()).p_out_kw == 800  # 830 → 800，能力用满


def test_arbitrate_picks_highest_priority_base_plus_deltas():
    reqs = [
        ControlRequest("schedule", 300, "base", 10, ""),
        ControlRequest("agc", 900, "base", 20, ""),
        ControlRequest("pfr", 70, "delta", 30, ""),
    ]
    total, used = arbitrate(reqs)
    assert total == 970
    assert [r.source for r in used] == ["agc", "pfr"]


# ---------------- 约束投影：并网点限值换算、电表失效、冲突
def test_pcc_export_limit_forces_charge():
    # 光伏富余：P_PCC=+300（送电），储能 0 → 其他部分 +300；防倒送上限 0 → 储能上限 −300
    res = project(0.0, state(p_bess=0.0, p_pcc=300.0), pcc_export_limit_kw=0.0)
    assert res.upper_kw == -300 and res.p_out_kw == -300 and res.active == ("防倒送",)


def test_meter_unavailable_is_conservative():
    res = project(500.0, state(p_pcc=None), pcc_export_limit_kw=0.0)
    assert res.p_out_kw == 0.0 and "保守禁放" in res.active[0]


def test_constraint_conflict_reported():
    # 富余 1200 kW，可充只有 1000：防倒送做不到，取最大充电并上报冲突
    res = project(0.0, state(chg=1000, p_pcc=1200.0), pcc_export_limit_kw=0.0)
    assert res.conflict and res.p_out_kw == -1000
    assert "防倒送" in res.active[0]


# ---------------- 完整周期与可追溯记录
def test_full_cycle_hand_calc_and_trace():
    pcs = MockPcs(1000)
    cfg = PipelineConfig(p_rated_kw=1000, dt_s=0.2, ramp_kw_per_s=1000)
    pipe = ControlPipeline(cfg, [AgcStrategy(), PrimaryFrequencyStrategy(PFR_CFG)], pcs,
                           clock=iter([0.0, 0.02]).__next__, p_initial_kw=700)
    rec = pipe.run_cycle(site(100.0, f=49.90), now=100.0)
    log = rec.as_log()
    assert log["requests"] == [("agc", "base", 900.0), ("pfr", "delta", pytest.approx(70.0))]
    assert log["request_reasons"] == [("agc", "调度 AGC 目标"), ("pfr", "f=49.900 Hz 下垂")]
    assert log["combined_kw"] == pytest.approx(970.0)
    assert log["constrained_kw"] == 800 and log["active_constraints"] == ["可放能力"]
    assert log["constraint_conflict"] is False and log["ramped_kw"] == 800
    assert log["final_kw"] == 800  # 700 → 800：本周期 Ramp 允许 +200
    assert log["seq"] == 1 and log["accepted"] and log["p_actual_kw"] == 800
    assert log["command_reason"] == "agc+pfr" and log["feedback_note"] == ""
    assert rec.command.expires_at == pytest.approx(102.0)
    assert not rec.issues


def test_ramp_limits_step_then_reaches_target():
    pcs = MockPcs(1000)
    cfg = PipelineConfig(p_rated_kw=1000, dt_s=0.2, ramp_kw_per_s=1000, cycle_budget_s=10)
    pipe = ControlPipeline(cfg, [AgcStrategy()], pcs, clock=lambda: 0.0)
    outs = [pipe.run_cycle(site(t, agc=900), now=t).command.target_kw for t in (0.0, 0.2, 0.4, 0.6, 0.8)]
    assert outs == [200, 400, 600, 800, 800]


def test_bms_comm_failed_goes_to_safe_zero_immediately():
    pcs = MockPcs(1000)
    cfg = PipelineConfig(p_rated_kw=1000, ramp_kw_per_s=100)
    pipe = ControlPipeline(cfg, [AgcStrategy()], pcs, clock=lambda: 0.0, p_initial_kw=800)
    pts = site(10.0)
    pts[BMS_DIS] = Measurement(BMS_DIS, None, "kW", Quality.COMM_FAILED, 10.0, 10.0)
    rec = pipe.run_cycle(pts, now=10.0)
    assert rec.command.target_kw == 0.0  # 不按 Ramp 慢慢降，能力归零立即生效
    assert any("COMM_FAILED" in s for s in rec.issues)


def test_stale_data_rejected_by_validation():
    pts = site(0.0)
    snap = take_snapshot(pts, t=3.0)  # 电表数据已 3 s，允许 1 s
    data = validate(snap, {METER_P: 1.0, BMS_DIS: 5.0})
    assert data.rejected[METER_P] == "STALE" and BMS_DIS in data.values


def test_strategy_exception_is_isolated():
    class Broken:
        name = "broken"

        def request(self, state):
            raise ZeroDivisionError("bug")

    pcs = MockPcs(1000)
    pipe = ControlPipeline(PipelineConfig(p_rated_kw=1000, ramp_kw_per_s=10000), [Broken(), AgcStrategy()], pcs,
                           clock=lambda: 0.0)
    rec = pipe.run_cycle(site(0.0, dis=1000), now=0.0)
    assert rec.command.target_kw == 900  # AGC 照常工作
    assert any("broken" in s for s in rec.issues)


def test_overrun_skips_dispatch_and_keeps_last():
    pcs = MockPcs(1000)
    cfg = PipelineConfig(p_rated_kw=1000, cycle_budget_s=0.1)
    pipe = ControlPipeline(cfg, [AgcStrategy()], pcs, clock=iter([0.0, 0.5]).__next__, p_initial_kw=300)
    rec = pipe.run_cycle(site(0.0), now=0.0)
    assert rec.overrun and rec.command is None and pcs.executed == []
    assert pipe.missed_deadlines == 1 and pipe.ramp.output == 300


# ---------------- 命令幂等、过期、重启恢复
def test_duplicate_command_executed_once_and_expired_rejected():
    pcs = MockPcs(1000)
    cmd = PowerCommand(7, 1, 500.0, created_at=0.0, expires_at=2.0, reason="agc")
    assert pcs.apply(cmd, 0.1).accepted
    fb = pcs.apply(cmd, 0.6)  # 超时重发同一序号
    assert fb.accepted and "不再执行" in fb.note
    assert pcs.executed == [7]
    old = PowerCommand(8, 2, 900.0, created_at=0.0, expires_at=2.0, reason="agc")
    fb = pcs.apply(old, 5.0)  # 网络恢复后才送到
    assert not fb.accepted and "过期" in fb.note and pcs.p_actual_kw == 500


def test_recover_continues_seq_and_ramps_from_actual():
    pcs = MockPcs(1000)
    pcs.last_seq = 41
    cfg = PipelineConfig(p_rated_kw=1000, dt_s=0.2, ramp_kw_per_s=1000)
    pipe = ControlPipeline(cfg, [AgcStrategy()], pcs, clock=lambda: 0.0)
    pipe.recover(p_actual_kw=500.0, last_seq=41)
    rec = pipe.run_cycle(site(0.0, dis=1000, agc=1000), now=0.0)
    assert rec.command.seq == 42 and rec.feedback.accepted
    assert rec.command.target_kw == 700  # 从实测 500 起步，不是从 0 或旧指令起步


def test_rejected_command_resets_ramp():
    pcs = MockPcs(1000)
    pcs.last_seq = 100  # 设备记得的序号比 EMS 大（EMS 重启后忘了恢复序号）
    pipe = ControlPipeline(PipelineConfig(p_rated_kw=1000), [AgcStrategy()], pcs, clock=lambda: 0.0)
    rec = pipe.run_cycle(site(0.0), now=0.0)
    assert not rec.feedback.accepted and any("拒绝" in s for s in rec.issues)
    assert pipe.ramp.output == 0.0


# ---------------- 多速率与快照一致性
def test_snapshot_is_isolated_and_read_only():
    pts = site(0.0)
    snap = take_snapshot(pts, 0.0)
    pts[METER_P] = good(METER_P, 9999.0, 0.1)  # 采集线程在本周期中途写入新值
    assert snap.points[METER_P].value == -500.0
    with pytest.raises(TypeError):
        snap.points[METER_P] = None


def test_slow_setpoint_expiry():
    sch = ScheduleStrategy()
    sch.publish(300.0, now=0.0, ttl_s=60.0)
    s = lambda t: OperatingState(t, Capability(1000, 1000, ""), 0.0, None, None, None, None)  # noqa: E731
    assert sch.request(s(30.0)).p_kw == 300.0
    assert sch.request(s(61.0)) is None  # 慢环没按时更新：不沿用过期计划


def test_schedule_used_when_agc_unavailable():
    pcs = MockPcs(1000)
    sch = ScheduleStrategy()
    sch.publish(300.0, now=0.0, ttl_s=60.0)
    pipe = ControlPipeline(PipelineConfig(p_rated_kw=1000, ramp_kw_per_s=10000), [sch, AgcStrategy()], pcs,
                           clock=lambda: 0.0)
    rec = pipe.run_cycle(site(1.0, agc=None), now=1.0)
    assert rec.command.target_kw == 300.0
    assert any(AGC_TARGET in s for s in rec.issues)

# ---------------- 9.7 撕裂读、9.13 自测第 2 题
def test_torn_read_shifts_export_limit_by_500():
    # 真实：储能已在充电 −500，并网点 0 → 其他部分 +500，防倒送要求储能上限 −500
    truth = project(0.0, state(p_bess=-500.0, p_pcc=0.0), pcc_export_limit_kw=0.0)
    # 撕裂读：电表是新值 0，PCS 读数是旧值 0 → 误以为其他部分为 0，上限变成 0
    torn = project(0.0, state(p_bess=0.0, p_pcc=0.0), pcc_export_limit_kw=0.0)
    assert truth.upper_kw == -500 and torn.upper_kw == 0
    assert torn.p_out_kw - truth.p_out_kw == 500  # 指令差了整整 500 kW


def test_self_check_q2():
    cap = Capability(1000, 600, "BMS")
    same = [ControlRequest("agc", 550, "base", 20, ""), ControlRequest("pfr", 100, "delta", 30, "")]
    assert naive_limit_each_then_sum(same, cap) == 650
    assert project(arbitrate(same)[0], state(dis=600)).p_out_kw == 600
    opposite = [ControlRequest("agc", 550, "base", 20, ""), ControlRequest("pfr", -100, "delta", 30, "")]
    assert naive_limit_each_then_sum(opposite, cap) == 450
    assert project(arbitrate(opposite)[0], state(dis=600)).p_out_kw == 450
def test_ch08_architecture_trace_example():
    """08 章最小闭环：延迟预算和主备 fencing。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch08_architecture_trace.py"
    runpy.run_path(str(script), run_name="__main__")


def test_ch09_pipeline_trace_example():
    """09 章最小闭环：九步控制流水线对象追踪。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch09_pipeline_trace.py"
    runpy.run_path(str(script), run_name="__main__")

