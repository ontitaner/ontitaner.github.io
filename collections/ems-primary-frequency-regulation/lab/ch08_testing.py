# @AI_GENERATED
"""第八章实验：试验验证仿真。

模拟并网验收试验中的几个关键测试项：
1. 防误动试验（小频差不动作）
2. 阶跃响应试验
3. 方向正确性校验
"""
from freq_core import (
    DeadbandMode, FreqSample, FreqRegStateMachine, FreqRegStatus,
    PrimaryFreqConfig, primary_freq_delta, simulate_pcs_response,
    rocof_estimate, print_summary,
)


def _misoperation_prevention_test() -> dict:
    """防误动试验：频率在死区内波动，不应产生出力。"""
    cfg = PrimaryFreqConfig(deadband_hz=0.05, droop_ratio=0.03,
                            p_rated_mw=100.0,
                            deadband_mode=DeadbandMode.SHIFT)
    sm = FreqRegStateMachine(cfg)
    sm.arm()

    test_points = [
        FreqSample(ts=0.0, f_hz=50.02),
        FreqSample(ts=1.0, f_hz=49.98),
        FreqSample(ts=2.0, f_hz=50.03),
        FreqSample(ts=3.0, f_hz=49.97),
        FreqSample(ts=4.0, f_hz=50.01),
        FreqSample(ts=5.0, f_hz=49.99),
    ]
    active_count = 0
    max_delta = 0.0
    for s in test_points:
        status, _ = sm.step(s)
        if status is FreqRegStatus.ACTIVE:
            active_count += 1
        th, _ = primary_freq_delta(s.f_hz, 50.0, 100.0, cfg)
        if abs(th) > abs(max_delta):
            max_delta = th

    passed = active_count == 0
    return {"误动次数": active_count, "最大出力 (MW)": max_delta, "通过": passed}


def _step_response_test() -> dict:
    """阶跃响应：频率 50.00 → 49.90 Hz，观测 t0.1/t0.9。"""
    cfg = PrimaryFreqConfig(deadband_hz=0.05, droop_ratio=0.03,
                            p_rated_mw=100.0,
                            deadband_mode=DeadbandMode.SHIFT)

    dt_s = 0.05
    n = 400  # 20s
    freq_pts = []
    p_theory = []
    for i in range(n):
        t = i * dt_s
        f = 49.90 if t >= 1.0 else 50.00
        freq_pts.append(FreqSample(ts=t, f_hz=f))
        th, _ = primary_freq_delta(f, 50.0, 100.0, cfg)
        p_theory.append(th)

    p_actual = simulate_pcs_response(p_theory, delay_s=0.1, tau_s=0.25, ramp_rate_mw_per_s=80.0)
    from freq_core import compute_timing_metrics
    t_series = [s.ts for s in freq_pts]
    f_series = [s.f_hz for s in freq_pts]
    metrics = compute_timing_metrics(t_series, f_series, p_actual, deadband_hz=0.05,
                                      p_stable_band_mw=1.0)
    return {
        "t0.1 (s)": metrics.get("t01_s", 0),
        "t0.9 (s)": metrics.get("t09_s", 0),
        "ts (s)": metrics.get("ts_s", 0),
    }


def _direction_test() -> dict:
    """方向校验：高频减出力、低频增出力。"""
    cfg = PrimaryFreqConfig(deadband_hz=0.05, droop_ratio=0.03,
                            p_rated_mw=100.0,
                            deadband_mode=DeadbandMode.SHIFT)

    # 高频
    th_high, _ = primary_freq_delta(50.10, 50.0, 100.0, cfg)
    # 低频
    th_low, _ = primary_freq_delta(49.90, 50.0, 100.0, cfg)

    return {
        "高频出力 (MW)": th_high,
        "低频出力 (MW)": th_low,
        "方向正确": th_high < 0 and th_low > 0,
    }


def _test_all():
    # 防误动
    m = _misoperation_prevention_test()
    assert m["通过"], "防误动试验应通过"

    # 阶跃
    s = _step_response_test()
    assert s["t0.9 (s)"] > s["t0.1 (s)"], "t0.9 应 > t0.1"

    # 方向
    d = _direction_test()
    assert d["方向正确"], "方向校验应正确"


def main():
    print_summary("防误动试验", _misoperation_prevention_test())
    print_summary("阶跃响应试验", _step_response_test())
    print_summary("方向校验", _direction_test())
    _test_all()
    print("\n✓ 第八章实验自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end