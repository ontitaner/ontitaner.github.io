import pytest

from ems_lab.frequency import (
    PrimaryFrequencyConfig,
    RocofEstimator,
    droop_gain_kw_per_hz,
    primary_frequency_power,
    swing_rocof_hz_per_s,
    virtual_inertia_power,
)

P_RATED = 100_000.0  # 100 MW


def test_droop_gain_from_ratio():
    # δ=2%，Pn=100 MW → K = 100 MW / (0.02×50 Hz) = 100 MW/Hz
    assert droop_gain_kw_per_hz(P_RATED, 0.02) == pytest.approx(100_000)


def test_primary_frequency_hand_calc_shift():
    # 第 15 章手算：49.90 Hz，死区 0.03（连续型）→ 有效偏差 -0.07 Hz → +7 MW
    cfg = PrimaryFrequencyConfig(p_rated_kw=P_RATED)
    assert primary_frequency_power(49.90, cfg) == pytest.approx(7_000)
    assert primary_frequency_power(50.10, cfg) == pytest.approx(-7_000)


def test_primary_frequency_hand_calc_cut():
    cfg = PrimaryFrequencyConfig(p_rated_kw=P_RATED, deadband_mode="cut")
    assert primary_frequency_power(49.90, cfg) == pytest.approx(10_000)


def test_primary_frequency_deadband_and_limit():
    cfg = PrimaryFrequencyConfig(p_rated_kw=P_RATED)
    assert primary_frequency_power(49.98, cfg) == 0.0
    assert primary_frequency_power(50.02, cfg) == 0.0
    # 49.5 Hz：-0.47 Hz × 100 MW/Hz = 47 MW，被 10% 限幅到 10 MW
    assert primary_frequency_power(49.5, cfg) == pytest.approx(10_000)


def test_swing_equation_hand_calc():
    # 100 GW 系统、H=5 s、跳机 3 GW → -0.15 Hz/s
    assert swing_rocof_hz_per_s(-0.03, 5.0) == pytest.approx(-0.15)


def test_virtual_inertia_direction():
    # 频率下跌（df/dt<0）→ 放电（正）
    assert virtual_inertia_power(-0.15, h_virtual_s=4.0, s_rated_kw=P_RATED) == pytest.approx(2_400)
    assert virtual_inertia_power(0.15, 4.0, P_RATED) < 0


def test_rocof_estimator_linear_ramp():
    est = RocofEstimator(window_s=0.5)
    result = None
    for i in range(100):
        t = i * 0.02
        result = est.update(t, 50.0 - 0.2 * t)
    assert result == pytest.approx(-0.2, abs=1e-9)
def test_ch15_primary_frequency_trace_example():
    """15 章最小闭环：频率序列→死区/下垂→功率序列。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch15_primary_frequency_trace.py"
    runpy.run_path(str(script), run_name="__main__")

