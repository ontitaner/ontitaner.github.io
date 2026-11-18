"""第 19 章：闭环场景测试。每个测试的文档字符串写明它防的是哪一种现场事故。

断言一律带容差和持续时间；参数均为 [教学示例]/[仿真配置]，现场以项目规程和验收大纲为准。
"""
import pytest

from ems_lab.frequency import PrimaryFrequencyConfig
from ems_lab.sim import (
    INF,
    EmsConfig,
    Fault,
    PlantConfig,
    Scenario,
    check_le,
    constant,
    evidence,
    first_event_time,
    longest_excursion_s,
    max_rate_over_window_kw_s,
    max_rise_rate_kw_s,
    power_balance_residual_kw,
    run,
    step_profile,
    steps_profile,
    window,
)

TOL_KW = 10.0  # 并网点功率判定容差 [教学示例]
BACKFEED_ALLOWED_S = 2.0  # 允许的暂态倒送持续时间，应小于逆功率保护延时 [项目配置示例]
HEAVY_LOAD = constant(1000.0)


def load_drop_scenario(**kw) -> Scenario:
    return Scenario("负荷突降防倒送", t_end_s=30, load_kw=step_profile(15, 800, 300), **kw)


# ---------------------------------------------------------------- S1 负荷突降
def test_s1_load_drop_no_sustained_backfeed():
    """事故：工厂大设备停机，负荷突降，储能仍按 600 kW 放电 → 倒送，逆功率保护跳闸或被考核。

    断言：① 倒送超过容差的持续时间 ≤ 2 s；② 5 s 后并网点稳定在目标 −30 kW ±15 kW；
    ③ 储能指令方向是“减少放电”；④ 主动上升速率 ≤ Ramp；⑤ 功率平衡恒成立。
    """
    tr = run(load_drop_scenario())
    target = -30.0
    checks = [
        check_le("倒送持续时间", longest_excursion_s(tr.t, tr.p_pcc, 0.0, TOL_KW), BACKFEED_ALLOWED_S,
                 "longest(P_PCC > 0 + 10 kW) <= 2.0 s"),
        check_le("稳态偏差", max(abs(p - target) for p in window(tr.t, tr.p_pcc, 20)), 15.0,
                 "max|P_PCC - (-30)| over t>=20 s <= 15 kW"),
        check_le("指令上升速率", max_rise_rate_kw_s(tr.decisions), 100.0 + 1e-6,
                 "max(ΔP_cmd/Δt) <= 100 kW/s"),
        check_le("功率平衡残差", power_balance_residual_kw(tr), 1e-6,
                 "|P_PCC - (P_PV + P_BESS - P_load - P_aux - P_loss)| <= 1e-6 kW"),
    ]
    final_after = [d.final_kw for d in tr.decisions if d.t >= 20]
    assert max(final_after) < 600 - 250  # 方向：负荷少了 500 kW，放电应明显减少
    assert all("防倒送" in d.binding for d in tr.decisions if d.t >= 20)
    ev = evidence(tr, checks)
    assert ev["verdict"] == "PASS", ev["checks"]
    assert ev["faults"] == [] and ev["sim_version"] and ev["config_version"] == "cfg-demo-1"


def test_s1b_timestamp_alignment_matters_with_meter_delay():
    """事故：电表延迟 1 s，EMS 用“最新的 PCS 功率”减“1 s 前的并网点功率”估净负荷，
    两个量不是同一时刻的，闭环来回振荡，防倒送时好时坏。

    断言：对齐时标时稳态偏差小于 15 kW；不对齐时振荡幅度大 10 倍以上。
    """
    plant = PlantConfig(meter_delay_s=1.0)
    good = run(load_drop_scenario(plant=plant))
    bad = run(load_drop_scenario(plant=plant, ems=EmsConfig(align_timestamps=False)))
    spread_good = max(window(good.t, good.p_pcc, 20)) - min(window(good.t, good.p_pcc, 20))
    spread_bad = max(window(bad.t, bad.p_pcc, 20)) - min(window(bad.t, bad.p_pcc, 20))
    assert spread_good < 15.0
    assert spread_bad > 10 * spread_good
    assert longest_excursion_s(bad.t, bad.p_pcc, 0.0, TOL_KW) > 0  # 稳态阶段仍有倒送
    assert max(window(bad.t, bad.p_pcc, 20)) > TOL_KW


# ---------------------------------------------------------------- S2 SOC 下限
def test_s2_soc_lower_limit_never_violated():
    """事故：SOC 到下限仍在放电，BMS 过放保护切断直流接触器，功率瞬间从几百 kW 掉到 0，
    同时电池寿命受损。

    断言：① SOC 最低值 ≥ 下限 − 0.2%；② BMS 未保护动作；③ EMS 下发值从不超过可放能力；
    ④ 实际功率超出可放能力不超过 20 kW（PCS 跟随滞后）；⑤ 能量守恒：ΔSOC × 容量 与 ∫P/η 一致。
    """
    plant = PlantConfig(soc0=0.13, capacity_kwh=100.0)
    tr = run(Scenario("SOC 下限", t_end_s=80, load_kw=HEAVY_LOAD, request_kw=constant(500), plant=plant))
    assert min(tr.soc) >= plant.soc_min - 0.002
    assert not tr.bms_tripped
    assert all(d.final_kw <= d.upper_kw + 1e-9 for d in tr.decisions)
    assert max(b - a for b, a in zip(tr.p_bess, tr.avail_dis)) <= 20.0
    dt = tr.t[1] - tr.t[0]
    e_out_kwh = sum(p / plant.eta_dis if p > 0 else p * plant.eta_ch for p in tr.p_bess) * dt / 3600
    assert (plant.soc0 - tr.soc[-1]) * plant.capacity_kwh == pytest.approx(e_out_kwh, rel=1e-6)
    assert tr.p_bess[-1] < 20.0  # 到下限附近，放电已基本停止


# ---------------------------------------------------------------- S3 BMS 降额
def test_s3_bms_derate_takes_effect_immediately():
    """事故：电池温度高，BMS 把可放能力从 1000 kW 降到 200 kW，EMS 却按 Ramp 100 kW/s 慢慢降，
    4 秒内持续超出 BMS 允许值，BMS 过流保护切簇。

    断言：① 降额当周期下发值 ≤ 200 kW；② 实际功率在 2 s 内降到 200 + 10 kW 以下；
    ③ 降额解除后按 Ramp 回升，不跳变（Ramp 内部状态已同步）。
    """
    tr = run(Scenario("BMS 降额", t_end_s=35, load_kw=HEAVY_LOAD, faults=[Fault("bms_derate", 15, 25, 200.0)]))
    first = next(d for d in tr.decisions if d.t >= 15)
    assert first.final_kw <= 200.0 and "可放能力" in first.binding
    assert max(window(tr.t, tr.p_bess, 17, 25)) <= 200.0 + TOL_KW
    assert max_rise_rate_kw_s(tr.decisions, 24.9) <= 100.0 + 1e-6
    assert max(d.final_kw for d in tr.decisions if 25 <= d.t < 25.3) <= 200.0 + 100.0 * 0.4 + 1e-6


# ---------------------------------------------------------------- S4 电表失效降级
@pytest.mark.parametrize("kind", ["meter_freeze", "meter_stale", "meter_fail"])
def test_s4_meter_bad_degrades_before_load_drop(kind):
    """事故：电表通信异常，EMS 读到的并网点功率一直停在 −226 kW（在取电），
    随后负荷突降，EMS 以为仍在取电，继续大功率放电，持续倒送。

    冻结：数值不变但时标在刷新（网关缓存）；过期：时标不刷新；失效：读不到。
    断言：① 故障后 4 s 内进入降级并告警；② 降级后下发值 ≤ 0；③ 负荷突降后并网点不倒送。
    """
    tr = run(Scenario(kind, t_end_s=30, load_kw=step_profile(18, 800, 300), faults=[Fault(kind, 12)]))
    t_alarm = first_event_time(tr.events, "METER_BAD")
    assert t_alarm is not None and t_alarm <= 12 + 4.0
    assert all(d.final_kw <= 0.0 for d in tr.decisions if d.t >= t_alarm)
    assert max(window(tr.t, tr.p_pcc, 18)) <= TOL_KW


def test_s4b_frozen_meter_without_detection_backfeeds():
    """反例：不做冻结检测（只看时标新鲜度），S4 的事故就会发生。"""
    tr = run(Scenario("冻结不检测", t_end_s=30, load_kw=step_profile(18, 800, 300),
                      faults=[Fault("meter_freeze", 12)], ems=EmsConfig(meter_frozen_s=INF)))
    assert first_event_time(tr.events, "METER_BAD") is None
    assert longest_excursion_s(tr.t, tr.p_pcc, 0.0, TOL_KW) > 10.0  # 持续倒送直到仿真结束


def test_s4c_packet_loss_tolerated_without_degrading():
    """事故：现场总线偶发丢包，EMS 把一次读失败就当成电表故障，频繁退出/投入防倒送，
    储能功率来回跳，告警刷屏。

    断言：30% 丢包下不降级、不告警，防倒送指标与无丢包时相同量级。
    """
    tr = run(load_drop_scenario(faults=[Fault("meter_drop", 5, value=0.3)]))
    assert tr.meter_comm_failures > 20
    assert first_event_time(tr.events, "METER_BAD") is None
    assert longest_excursion_s(tr.t, tr.p_pcc, 0.0, TOL_KW) <= BACKFEED_ALLOWED_S
    assert max(abs(p + 30.0) for p in window(tr.t, tr.p_pcc, 20)) <= 15.0


# ---------------------------------------------------------------- S5 PCS 拒绝指令
def test_s5_pcs_reject_syncs_ramp_to_actual():
    """事故：运维人员把 PCS 切到就地模式检修，EMS 没理会“拒绝”，内部 Ramp 和积分一路涨到 700 kW；
    切回远方的瞬间，PCS 收到 700 kW，功率阶跃冲击，并网点越限。

    断言：① 第一次被拒就告警；② 拒绝期间 EMS 内部状态与实测偏差 ≤ 20 kW；
    ③ 恢复后实际功率按 1 s 窗口计算的上升速率 ≤ 100 kW/s + 10%。
    """
    faults = [Fault("pcs_reject", 15, 25)]
    req = step_profile(15, 300, 700)
    tr = run(Scenario("PCS 拒绝", t_end_s=35, load_kw=HEAVY_LOAD, request_kw=req, faults=faults))
    assert first_event_time(tr.events, "PCS_REJECT") == pytest.approx(15.0)
    dt = tr.t[1] - tr.t[0]
    gap = [abs(d.ramp_after_ack_kw - tr.p_bess[int(round(d.t / dt))]) for d in tr.decisions if 15 <= d.t < 25]
    assert max(gap) <= 20.0
    assert max_rate_over_window_kw_s(tr.t, tr.p_bess, 1.0, t0=24.0) <= 110.0

    # 反例：不同步 Ramp 状态，EMS 内部“以为”已经到了几百 kW
    bad = run(Scenario("PCS 拒绝-不同步", t_end_s=35, load_kw=HEAVY_LOAD, request_kw=req, faults=faults,
                       ems=EmsConfig(sync_on_reject=False)))
    gap_bad = [abs(d.ramp_after_ack_kw - bad.p_bess[int(round(d.t / dt))]) for d in bad.decisions if 15 <= d.t < 25]
    assert max(gap_bad) > 100.0


# ---------------------------------------------------------------- S6 PCS 离线与重连
def test_s6_pcs_offline_then_reconnect_ramps_from_actual():
    """事故：PCS 通信中断后停机，通信恢复时 EMS 直接把断线前的 600 kW 发下去，功率阶跃。

    断言：① 离线期间能力置 0、下发 0 并告警；② 恢复后告警消除；
    ③ 恢复后每周期变化不超过 Ramp × 周期（100 kW/s × 0.2 s = 20 kW）。
    """
    tr = run(Scenario("PCS 离线", t_end_s=35, load_kw=HEAVY_LOAD, faults=[Fault("pcs_offline", 15, 20)]))
    assert first_event_time(tr.events, "PCS_OFFLINE") == pytest.approx(15.0)
    assert first_event_time(tr.events, "PCS_OFFLINE", "-") == pytest.approx(20.0)
    assert all(d.final_kw == 0.0 for d in tr.decisions if 15 <= d.t < 20)
    steps = [b.final_kw - a.final_kw for a, b in zip(tr.decisions, tr.decisions[1:]) if b.t >= 19.9]
    assert max(steps) <= 20.0 + 1e-6


# ---------------------------------------------------------------- S7 EMS 重启
def test_s7_restart_does_not_replay_old_command():
    """事故：EMS 宕机 10 s，期间 PCS 看门狗已把功率回零；EMS 重启后从持久化快照恢复，
    把宕机前的 600 kW 当成“当前指令”继续下发，功率从 0 瞬间跳到 600 kW。

    断言：① 重启后命令序号接着宕机前的序号（PCS 不会按旧序号拒绝）；
    ② 重启后先确认数据可信（降级等待）；③ 实际功率按 1 s 窗口上升速率 ≤ 110 kW/s。
    反例：按旧快照恢复时，上升速率远超 Ramp。
    """
    faults = [Fault("ems_down", 15, 25)]
    tr = run(Scenario("EMS 重启", t_end_s=40, load_kw=HEAVY_LOAD, faults=faults))
    before = [d for d in tr.decisions if d.t < 15][-1]
    after = [d for d in tr.decisions if d.t >= 25]
    assert after[0].seq == before.seq + 1 and after[0].accepted
    assert after[0].degraded and after[0].final_kw == 0.0
    assert max(window(tr.t, tr.p_bess, 22.0, 25.0)) < 5.0  # 看门狗（5 s）已把功率回零
    assert max_rate_over_window_kw_s(tr.t, tr.p_bess, 1.0, t0=25.0) <= 110.0

    bad = run(Scenario("EMS 重启-重放", t_end_s=40, load_kw=HEAVY_LOAD, faults=faults, replay_on_restart=True))
    assert max_rate_over_window_kw_s(bad.t, bad.p_bess, 1.0, t0=25.0) > 400.0


# ---------------------------------------------------------------- S8 时钟跳变
def test_s8_wall_clock_jump_uses_monotonic_time():
    """事故：站内对时装置恢复后，EMS 墙钟一次跳快 30 s，所有数据的“年龄”瞬间变成 30 s，
    全站判数据过期，储能集体退出；或者 dt = 30 s 让 Ramp 一步放开。

    断言：用单调时钟计算 dt 和数据年龄时，不降级、不告警、不跳变；用墙钟时会误降级。
    """
    faults = [Fault("clock_jump", 15, value=30.0)]
    tr = run(Scenario("时钟跳变", t_end_s=30, load_kw=HEAVY_LOAD, faults=faults))
    assert tr.events == []
    assert max_rise_rate_kw_s(tr.decisions) <= 100.0 + 1e-6
    assert all(d.t_wall - d.t == pytest.approx(30.0) for d in tr.decisions if d.t >= 15)  # 记录里保留墙钟

    naive = run(Scenario("时钟跳变-墙钟", t_end_s=30, load_kw=HEAVY_LOAD, faults=faults,
                         ems=EmsConfig(use_monotonic=False)))
    codes = {c for _, s, c in naive.events if s == "+"}
    assert {"CLOCK_DT", "METER_BAD"} <= codes
    assert any(d.degraded for d in naive.decisions if d.t > 15)


# ---------------------------------------------------------------- S9 一次调频方向
def test_s9_primary_frequency_direction_and_magnitude():
    """事故：接入层方向接反或下垂公式少了负号，频率低时储能反而充电（第 15 章案例三）。

    断言：频率 49.9 Hz 时指令 = 基点 300 + 70 kW；50.1 Hz 时 = 300 − 70 kW（连续型死区，δ=2%）。
    """
    pfr = PrimaryFrequencyConfig(p_rated_kw=1000.0)
    freq = steps_profile([(0.0, 50.0), (12.0, 49.9), (20.0, 50.1)])
    tr = run(Scenario("一次调频", t_end_s=30, load_kw=HEAVY_LOAD, request_kw=constant(300), freq_hz=freq, pfr=pfr))

    def cmd_at(t):
        return next(d.final_kw for d in tr.decisions if d.t >= t)

    assert cmd_at(11.0) == pytest.approx(300.0)
    assert cmd_at(15.0) == pytest.approx(370.0, abs=1.0)
    assert cmd_at(25.0) == pytest.approx(230.0, abs=1.0)

def test_ch19_sim_trace_example():
    """19 章最小闭环：仿真→断言→证据。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch19_sim_trace.py"
    runpy.run_path(str(script), run_name="__main__")

