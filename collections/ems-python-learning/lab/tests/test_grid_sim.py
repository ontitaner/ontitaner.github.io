"""第15章低阶电网频率模型的边界和可重复性测试。"""

import pytest

from ems_lab.grid_sim import BessParams, GridParams, simulate_trip


def test_no_trip_keeps_nominal_frequency():
    result = simulate_trip(0.0, GridParams(), BessParams(), t_end_s=2.0, dt=0.01, t_trip_s=1.0)
    assert result.nadir_hz == pytest.approx(50.0)
    assert result.nadir_time_s == pytest.approx(0.0)


def test_trip_frequency_drops_and_reports_nadir():
    result = simulate_trip(0.03, GridParams(), BessParams(), t_end_s=10.0, dt=0.01, t_trip_s=1.0)
    assert result.f_hz[0] == pytest.approx(50.0)
    assert result.nadir_hz < 50.0
    assert 1.0 <= result.nadir_time_s <= 10.0
    assert len(result.t) == len(result.f_hz) == len(result.p_gov) == len(result.p_damping)


def test_storage_support_improves_frequency_nadir():
    grid = GridParams()
    without_bess = simulate_trip(0.03, grid, BessParams(), t_end_s=10.0, dt=0.01, t_trip_s=1.0)
    with_bess = simulate_trip(
        0.03,
        grid,
        BessParams(rating_pu=0.02, droop_ratio=0.01, deadband_hz=0.03, tau_s=0.2),
        t_end_s=10.0,
        dt=0.01,
        t_trip_s=1.0,
    )
    assert with_bess.nadir_hz > without_bess.nadir_hz
    assert max(with_bess.p_bess) > 0.0


def test_grid_sim_is_deterministic():
    args = (0.03, GridParams(), BessParams(rating_pu=0.02), 5.0, 0.01, 1.0)
    first = simulate_trip(*args)
    second = simulate_trip(*args)
    assert first.nadir_hz == second.nadir_hz
    assert first.nadir_time_s == second.nadir_time_s
    assert (first.f_hz == second.f_hz).all()


def test_invalid_inertia_is_rejected():
    with pytest.raises(ValueError, match="惯性时间常数"):
        simulate_trip(0.03, GridParams(h_s=0.0), BessParams(), t_end_s=1.0)
