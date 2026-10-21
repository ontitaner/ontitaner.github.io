import pytest

from ems_lab.agc import (
    AgcReceiver,
    AgcReceiverConfig,
    StationModel,
    StepMetrics,
    ace_mw,
    command_at,
    decode_normalized,
    decode_scaled,
    evaluate_step,
    performance_index,
    regulation_capability,
    simulate_thermal_bess,
    simulate_tracking,
)


# ---------------------------------------------------------------- ACE 手算（16.3）
def test_ace_own_area_trip():
    # 本区域机组跳闸：频率 −0.05 Hz，联络线多受入 30 MW（ΔP_tie=−30），B=1000 MW/Hz
    assert ace_mw(-30, -0.05, 1000) == pytest.approx(-80)  # 本区域缺 80 MW → AGC 增发 80 MW


def test_ace_neighbor_trip_is_zero():
    # 邻区跳闸：本区域一次调频多送出 50 MW，频率 −0.05 Hz → ACE=0，本区域 AGC 不动
    assert ace_mw(50, -0.05, 1000) == pytest.approx(0)


def test_ace_rejects_negative_bias():
    with pytest.raises(ValueError):
        ace_mw(0, 0, -1000)


# ---------------------------------------------------------------- 遥调量解码（16.10 故障二）
def test_decode_scaled_and_normalized():
    assert decode_scaled(800, 10.0) == pytest.approx(8000)  # 原始值 800，系数 10 kW
    assert decode_normalized(0.8, 10_000) == pytest.approx(8000)
    # 满量程误填为单台 PCS 2500 kW：指令被缩小到 1/4
    assert decode_normalized(0.8, 2_500) == pytest.approx(2000)
    with pytest.raises(ValueError):
        decode_normalized(1.5, 10_000)


# ---------------------------------------------------------------- 设点接收
def _rx():
    return AgcReceiver(AgcReceiverConfig(p_min_kw=-10_000, p_max_kw=10_000, max_age_s=30, hold_s=60))


def test_receiver_accepts_valid_setpoint():
    rx = _rx()
    sp = rx.update(now=100, value_kw=8000, stamp_s=99)
    assert (sp.p_kw, sp.status) == (8000, "ACCEPTED")


def test_receiver_rejects_out_of_range_and_holds():
    rx = _rx()
    rx.update(100, 5000, 100)
    sp = rx.update(101, 80_000, 101)  # 缩放错导致 10 倍
    assert sp.status == "HOLD" and sp.p_kw == 5000 and "越量程" in sp.reason


def test_receiver_stale_timestamp_is_not_fresh():
    rx = _rx()
    rx.update(100, 5000, 100)
    sp = rx.update(150, 5000, 100)  # 寄存器仍在刷新，但时标 50 s 前
    assert sp.status == "HOLD" and "时标" in sp.reason


def test_receiver_link_loss_hold_then_fallback():
    rx = _rx()
    rx.update(100, 5000, 100)
    assert rx.update(140, None, None, link_ok=False, schedule_kw=1000).status == "HOLD"
    sp = rx.update(170, None, None, link_ok=False, schedule_kw=1000)  # 超过保持 60 s
    assert (sp.status, sp.p_kw) == ("FALLBACK", 1000)


def test_receiver_agc_off_tracks_schedule():
    sp = _rx().update(0, 8000, 0, agc_enabled=False, schedule_kw=1500)
    assert (sp.status, sp.p_kw) == ("AGC_OFF", 1500)


# ---------------------------------------------------------------- 可调能力（16.8 手算）
def test_regulation_capability_low_soc():
    # 10 MW / 20 MWh，SOC 15%，下限 10%，要求持续 15 min
    up, down = regulation_capability(0.15, 20_000, 10_000, 10_000, 0.10, 0.90, 0.25)
    assert up == pytest.approx(4000)  # (0.15−0.10)×20000/0.25
    assert down == pytest.approx(-10_000)  # 电量足够，受功率限制


# ---------------------------------------------------------------- 跟踪仿真与指标（16.6 手算）
def test_command_at_step_sequence():
    cmds = [(10, 8000), (60, -6000)]
    assert command_at(cmds, 5) == 0 and command_at(cmds, 10) == 8000 and command_at(cmds, 61) == -6000


def test_ideal_tracking_hand_calc():
    # 无惯性、无偏差：延迟 2 s，Ramp 1000 kW/s，0 → 8000 kW，判定带 200 kW
    m = StationModel(p_rated_kw=10_000, ramp_kw_per_s=1000, tau_s=0, delay_s=2.0, energy_kwh=20_000)
    r = simulate_tracking([(10, 8000)], m, 60)
    s = evaluate_step(r.t, r.p_act, 10, 60, 0, 8000, 200)
    assert s.response_time_s == pytest.approx(2.2, abs=0.15)  # 2 + 200/1000
    assert s.reach_time_s == pytest.approx(9.8, abs=0.15)  # 2 + 7800/1000
    assert s.rate_kw_per_s == pytest.approx(1000, rel=0.01)
    assert s.accuracy_kw == pytest.approx(0, abs=5)


def test_offset_hurts_accuracy():
    m = StationModel(p_rated_kw=10_000, ramp_kw_per_s=1000, tau_s=1.0, delay_s=2.0, offset_kw=-80, energy_kwh=20_000)
    r = simulate_tracking([(10, 8000)], m, 60)
    s = evaluate_step(r.t, r.p_act, 10, 60, 0, 8000, 200)
    assert 75 < s.accuracy_kw < 90  # 站用电没补偿，稳态差 80 kW
    assert s.rate_kw_per_s < 1000  # 一阶惯性让平均速率低于 Ramp


def test_performance_index_hand_calc():
    m = StepMetrics(0, 0, 8000, response_time_s=2.5, reach_time_s=12, rate_kw_per_s=800, accuracy_kw=80, reached=True)
    k = performance_index(m, rate_std_kw_per_s=500, t_std_s=10, err_allow_kw=200)
    assert k["k1"] == pytest.approx(1.6)
    assert k["k2"] == pytest.approx(0.6)
    assert k["k3"] == pytest.approx(0.75)
    assert k["kp"] == pytest.approx(0.72)


def test_soc_depletion_breaks_tracking():
    # SOC 15% 起步，持续 8 MW 放电：约 15 min 后到 5% 下限，出力归零
    m = StationModel(p_rated_kw=10_000, ramp_kw_per_s=1000, tau_s=1.0, delay_s=2.0, energy_kwh=20_000, soc0=0.15)
    r = simulate_tracking([(10, 8000)], m, 1800, dt=1.0)
    assert r.p_act[600] == pytest.approx(8000, abs=50)
    assert abs(r.p_act[-1]) < 50
    assert r.soc.min() == pytest.approx(0.05, abs=0.005)
    s = evaluate_step(r.t, r.p_act, 10, 1800, 0, 8000, 200)
    assert s.accuracy_kw > 3000  # 后半段完全跟不上


def test_thermal_bess_combined_tracks_faster():
    # 300 MW 机组从 150 MW 升到 180 MW，机组速率 100 kW/s（2% Pn/min 量级），配 9 MW 储能
    cmds = [(10, 180_000)]
    thermal = StationModel(p_rated_kw=300_000, ramp_kw_per_s=100, tau_s=5, delay_s=5, p_min_kw=150_000)
    bess = StationModel(p_rated_kw=9_000, ramp_kw_per_s=3000, tau_s=0.5, delay_s=2, energy_kwh=4_500)
    alone = simulate_tracking(cmds, thermal, 500, dt=0.1, p0_kw=150_000)
    th, p_b, total = simulate_thermal_bess(cmds, thermal, bess, 500, dt=0.1, p0_kw=150_000)
    k = int(40 / 0.1)  # 下发 30 s 后
    assert total[k] > alone.p_act[k] + 5_000  # 联合出力明显更接近设点
    assert abs(total[-1] - 180_000) < 500 and abs(p_b[-1]) < 500  # 机组到位后储能退出
    assert abs(p_b).max() <= 9_000 + 1e-6

def test_self_check_16():
    assert ace_mw(32, -0.04, 800) == pytest.approx(0)
    assert decode_normalized(0.6, 20_000) == pytest.approx(12_000)
    assert decode_normalized(0.6, 5_000) == pytest.approx(3_000)
    m = StationModel(p_rated_kw=10_000, ramp_kw_per_s=500, tau_s=0, delay_s=1.5, energy_kwh=20_000)
    r = simulate_tracking([(10, 4000)], m, 60)
    s = evaluate_step(r.t, r.p_act, 10, 60, 0, 4000, 100)
    assert s.response_time_s == pytest.approx(1.7, abs=0.15)
    assert s.reach_time_s == pytest.approx(9.3, abs=0.15)
    assert s.rate_kw_per_s == pytest.approx(500, rel=0.02)
    up, _ = regulation_capability(0.20, 40_000, 20_000, 20_000, 0.10, 0.90, 0.5)
    assert up == pytest.approx(8000)
def test_ch16_agc_trace_example():
    """16 章最小闭环：AGC 跟踪到响应指标。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch16_agc_trace.py"
    runpy.run_path(str(script), run_name="__main__")

