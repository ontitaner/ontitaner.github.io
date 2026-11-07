# @AI_GENERATED
"""第六章实验：EMS 控制链完整仿真。

从频率采样 → 死区处理 → 能力校验 → 状态机 → PCS 响应模拟，
全链路打通，可调参数观察输出变化。
"""
from freq_core import (
    DeadbandMode, FreqRegStateMachine, FreqRegStatus, FreqSample,
    PrimaryFreqConfig, primary_freq_delta, simulate_pcs_response,
    print_summary,
)


def _full_chain_simulation(f_start_hz: float, f_end_hz: float,
                           delay_s: float = 0.2, tau_s: float = 0.3,
                           ramp_rate_mw_per_s: float = 50.0) -> list:
    """完整控制链仿真。

    频率线性扫描从 f_start → f_end，每 0.1s 一帧。
    返回 [(t, f, p_theory, p_exec, status), ...]
    """
    cfg = PrimaryFreqConfig(deadband_hz=0.05, droop_ratio=0.03,
                            p_rated_mw=100.0, limit_up_ratio=0.10,
                            limit_down_ratio=0.10,
                            deadband_mode=DeadbandMode.SHIFT)
    sm = FreqRegStateMachine(cfg)
    sm.arm()

    total_s = 15.0
    dt_s = 0.1
    n = int(total_s / dt_s) + 1

    freq_samples = []
    p_theory = []
    statuses = []
    for i in range(n):
        t = i * dt_s
        if t < 2.0:
            f = 50.0
        elif t < 8.0:
            frac = (t - 2.0) / 6.0
            f = 50.0 + (f_start_hz - 50.0) * frac
        else:
            f = f_start_hz
        fs = FreqSample(ts=t, f_hz=f)
        freq_samples.append(fs)
        status, _ = sm.step(fs)
        dt, de = primary_freq_delta(f, 20.0, 100.0, cfg)
        p_theory.append(de)
        statuses.append(status)

    p_exec = simulate_pcs_response(p_theory, delay_s, tau_s, ramp_rate_mw_per_s)

    records = []
    for i in range(n):
        records.append((
            freq_samples[i].ts,
            freq_samples[i].f_hz,
            p_theory[i],
            p_exec[i],
            statuses[i],
        ))
    return records


def _demo():
    print("全链路仿真 (频率 50.00 → 49.88 Hz, 斜坡 6s):")
    records = _full_chain_simulation(49.88, 49.88)
    print(f"  {'t(s)':>6s}  {'f(Hz)':>7s}  {'pt(MW)':>8s}  {'pe(MW)':>8s}  {'状态':>8s}")
    for i, (t, f, pt, pe, status) in enumerate(records):
        if i % 10 == 0:
            print(f"  {t:>6.1f}  {f:>7.2f}  {pt:>8.2f}  {pe:>8.2f}  {status.value:>8s}")


def _test_chain():
    records = _full_chain_simulation(49.88, 49.88)
    # 死区内（前 2s）出力应为 0
    assert all(abs(r[2]) < 0.01 for r in records if r[0] < 2.0), "死区内出力应为 0"
    # 最终稳态出力应接近理论值
    final_p = records[-1][3]
    final_pt = records[-1][2]
    assert abs(final_p - final_pt) < 2.0, \
        f"稳态出力({final_p:.2f})应接近理论({final_pt:.2f})"


def main():
    _demo()
    _test_chain()
    print("\n✓ 第六章实验自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end