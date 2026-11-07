# @AI_GENERATED
"""第四章实验：性能指标体系与时序分解。

模拟一次频率阶跃→爬坡→稳定的全过程，计算 t0.1 / t0.9 / ts，
并对比不同 ramp_rate 对时序指标的影响。
"""
from freq_core import (
    FreqSample, PrimaryFreqConfig, DeadbandMode,
    compute_timing_metrics, generate_freq_step, primary_freq_delta,
    simulate_pcs_response, print_summary,
)


def _simulate_step_response(delay_s: float, tau_s: float,
                            ramp_rate_mw_per_s: float = 50.0) -> dict:
    """模拟一次频率阶跃的完整响应时序。"""
    cfg = PrimaryFreqConfig(deadband_hz=0.05, droop_ratio=0.03,
                            p_rated_mw=100.0, limit_up_ratio=0.10,
                            limit_down_ratio=0.10,
                            deadband_mode=DeadbandMode.CUT)

    freq_samples = generate_freq_step(fn=50.0, step_to_hz=49.88, step_at_s=2.0,
                                       total_s=20.0, dt_s=0.1)
    n = len(freq_samples)

    # 计算理论出力序列
    p_theory_series = []
    for fs in freq_samples:
        dt, _ = primary_freq_delta(fs.f_hz, 50.0, 100.0, cfg)
        p_theory_series.append(dt)

    # 模拟实际出力（含时延+惰性+ramp）
    p_actual = simulate_pcs_response(p_theory_series, delay_s, tau_s, ramp_rate_mw_per_s)

    # 计算时序指标
    t_series = [s.ts for s in freq_samples]
    f_series = [s.f_hz for s in freq_samples]
    metrics = compute_timing_metrics(t_series, f_series, p_actual,
                                      deadband_hz=0.05, p_stable_band_mw=1.0)
    return metrics


def _time_budget_demo():
    print("\n时序预算分解 (Pn=100MW, 频率阶跃 50.00→49.88 Hz):")
    print(f"  {'场景':30s}  {'t0.1(s)':>8s}  {'t0.9(s)':>8s}  {'ts(s)':>8s}")
    scenarios = [
        ("理想 PCS (τ=0.05s, rr=1000)", 0.1, 0.05, 1000.0),
        ("典型 PCS (τ=0.3s, rr=50)", 0.2, 0.30, 50.0),
        ("老旧 PCS (τ=0.8s, rr=20)", 0.3, 0.80, 20.0),
        ("高延迟 (通信 0.5s)", 0.5, 0.30, 50.0),
    ]
    for name, delay, tau, ramp in scenarios:
        m = _simulate_step_response(delay, tau, ramp)
        t01 = m.get("t01_s", "N/A")
        t09 = m.get("t09_s", "N/A")
        ts = m.get("ts_s", "N/A")
        t01_s = f"{t01:.2f}" if isinstance(t01, (int, float)) else str(t01)
        t09_s = f"{t09:.2f}" if isinstance(t09, (int, float)) else str(t09)
        ts_s = f"{ts:.2f}" if isinstance(ts, (int, float)) else str(ts)
        print(f"  {name:30s}  {t01_s:>8s}  {t09_s:>8s}  {ts_s:>8s}")


def _test_timing():
    m = _simulate_step_response(0.2, 0.3, 50.0)
    assert "t01_s" in m, "应计算 t0.1"
    t01 = m["t01_s"]
    ts = m["ts_s"]
    if isinstance(t01, (int, float)):
        assert t01 > 0, "t0.1 应 > 0"
    if isinstance(ts, (int, float)):
        assert ts > t01, f"ts({ts}) 应 > t0.1({t01})"


def main():
    m = _simulate_step_response(0.2, 0.3, 50.0)
    result = {
        "t0 (s)": m.get("t0", 0),
        "t0.1 (s)": m.get("t01_s", 0),
        "t0.9 (s)": m.get("t09_s", 0),
        "ts 稳定 (s)": m.get("ts_s", 0),
        "p_initial (MW)": m.get("p_initial_mw", 0),
        "p_target (MW)": m.get("p_target_mw", 0),
    }
    print_summary("时序指标计算 (典型 PCS)", result)
    _time_budget_demo()
    _test_timing()
    print("\n✓ 第四章实验自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end