# @AI_GENERATED
"""第二章实验：死区类型对调频出力的影响。

验证：Pn=100 MW, δ=3%, 死区 ±0.06 Hz 时，
连续型 vs 截断型在 49.90 Hz 处的出力差 = 4.0 MW。
"""
import numpy as np

from freq_core import (
    FN, DeadbandMode, FreqSample, FreqRegStateMachine,
    PrimaryFreqConfig, apply_deadband, primary_freq_delta, print_summary,
)


def _compare() -> dict:
    cfg_shift = PrimaryFreqConfig(deadband_mode=DeadbandMode.SHIFT, deadband_hz=0.06,
                                  droop_ratio=0.03, p_rated_mw=100.0,
                                  limit_up_ratio=0.10, limit_down_ratio=0.10)
    cfg_cut = PrimaryFreqConfig(deadband_mode=DeadbandMode.CUT, deadband_hz=0.06,
                                droop_ratio=0.03, p_rated_mw=100.0,
                                limit_up_ratio=0.10, limit_down_ratio=0.10)

    freqs = np.linspace(49.70, 50.30, 401)
    shift_theory = []
    cut_theory = []
    shift_exec = []
    cut_exec = []

    for f in freqs:
        st, se = primary_freq_delta(f, 50.0, 100.0, cfg_shift)
        ct, ce = primary_freq_delta(f, 50.0, 100.0, cfg_cut)
        shift_theory.append(st)
        shift_exec.append(se)
        cut_theory.append(ct)
        cut_exec.append(ce)

    # 关键工作点：49.90 Hz
    f_check = 49.90
    st_check, _ = primary_freq_delta(f_check, 50.0, 100.0, cfg_shift)
    ct_check, _ = primary_freq_delta(f_check, 50.0, 100.0, cfg_cut)

    return {
        "K (MW/Hz)": cfg_shift.k,
        "连续型 @49.90Hz (MW)": st_check,
        "截断型 @49.90Hz (MW)": ct_check,
        "差值 (MW)": ct_check - st_check,
        "差值 = 死区×K (MW)": cfg_shift.deadband_hz * cfg_shift.k,
    }


def _test_compare():
    result = _compare()
    assert abs(result["差值 (MW)"] - 4.0) < 0.02, f"差值应为 4.0 MW，实际 {result['差值 (MW)']:.2f}"
    assert abs(result["差值 (MW)"] - result["差值 = 死区×K (MW)"]) < 0.02


def _deadband_modes_demo():
    print("\n死区处理函数行为演示 (deadband = 0.06 Hz):")
    test_deltas = [0.0, -0.03, -0.06, -0.10, -0.15, 0.05, 0.07]
    print(f"  {'Δf':>8s}  {'shift':>8s}  {'cut':>8s}")
    for d in test_deltas:
        s = apply_deadband(d, 0.06, DeadbandMode.SHIFT)
        c = apply_deadband(d, 0.06, DeadbandMode.CUT)
        print(f"  {d:>8.2f}  {s:>8.2f}  {c:>8.2f}")


def _state_machine_demo():
    print("\n状态机行为演示:")
    cfg = PrimaryFreqConfig(deadband_hz=0.06)
    sm = FreqRegStateMachine(cfg)

    sm.arm()
    print(f"  初始状态: {sm.status.value}")

    events = [
        FreqSample(ts=0.0, f_hz=50.02),   # 死区内
        FreqSample(ts=1.0, f_hz=49.92),   # 越死区
        FreqSample(ts=2.0, f_hz=49.92),   # 冻结检测触发
        FreqSample(ts=3.0, f_hz=49.92),
        FreqSample(ts=4.0, f_hz=49.92),
        FreqSample(ts=5.0, f_hz=49.92),
        FreqSample(ts=6.0, f_hz=49.92),
    ]
    for e in events:
        status, reason = sm.step(e)
        print(f"  t={e.ts:.0f}s  f={e.f_hz:.2f}Hz  →  {status.value}" +
              (f" ({reason.value})" if reason.value != "none" else ""))


def main():
    result = _compare()
    print_summary("死区类型出力对比 (Pn=100MW, δ=3%, 死区 ±0.06Hz)", result)
    _deadband_modes_demo()
    _state_machine_demo()
    _test_compare()
    print("\n✓ 第二章实验自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end