# @AI_GENERATED
"""第 03 章一致性测试：惯量折算、惯量功率、D↔调差率、死区对比、支撑时长。

锚定正文 03.x 手算：
  J0 = 50×0.1/0.75 ≈ 6.667 s；叠加虚拟惯量后 J_eq=20 s → RoCoF 0.25 Hz/s
  惯量功率分摊：系统 1.67 MW + 本站 3.33 MW = 5.00 MW
  D = 100/δ：δ=3% → 33.333 pu；D=20/40 → δ=5%/2.5%
  死区对比（Δf=-0.6 Hz, D=33.333）：构网型 20 MW vs 传统 18 MW
"""
from __future__ import annotations

import pytest

from ems_lab.inertia import (
    D_to_droop_pct,
    droop_to_D,
    gridforming_delta_p_pu,
    inertia_power_pu,
    pfr_deadzone,
    pfr_delta_p_pu,
    support_duration_h,
    system_inertia_s,
    system_rocof_hz,
)

F_N = 50.0
DP = 0.1


def test_system_inertia_from_rocof():
    # 00.1：RoCoF=0.75 Hz/s → J_eq = 50×0.1/0.75 ≈ 6.667 s
    assert system_inertia_s(DP, 0.75, F_N) == pytest.approx(6.6667, rel=1e-3)


def test_rocof_after_adding_virtual_inertia():
    # 叠加到 3 倍惯量 20 s → RoCoF = 50×0.1/20 = 0.25 Hz/s
    assert system_rocof_hz(DP, 20.0, F_N) == pytest.approx(0.25)


def test_rocof_inverse_to_inertia():
    # RoCoF 与 J_eq 成反比：6.667 s → 0.75，20 s → 0.25（降到 1/3）
    j0 = system_inertia_s(DP, 0.75, F_N)
    assert system_rocof_hz(DP, j0, F_N) == pytest.approx(0.75)
    assert system_rocof_hz(DP, 20.0, F_N) == pytest.approx(0.25)


def test_inertia_power_split():
    # RoCoF=0.25 时：系统 1.67 MW + 本站 3.33 MW = 5.00 MW（=0.1 pu 缺口）
    j0 = system_inertia_s(DP, 0.75, F_N)
    j_vsg = 20.0 - j0
    p_sys = inertia_power_pu(j0, 0.25, F_N)
    p_vsg = inertia_power_pu(j_vsg, 0.25, F_N)
    assert p_sys * 50.0 == pytest.approx(1.6667, rel=1e-3)
    assert p_vsg * 50.0 == pytest.approx(3.3333, rel=1e-3)
    assert (p_sys + p_vsg) == pytest.approx(DP, rel=1e-3)


def test_inertia_power_zero_when_rocof_zero():
    # 惯量功率只在 RoCoF≠0 时存在
    assert inertia_power_pu(13.333, 0.0, F_N) == pytest.approx(0.0)


def test_droop_to_D():
    assert droop_to_D(3.0) == pytest.approx(33.3333, rel=1e-3)


def test_D_to_droop():
    assert D_to_droop_pct(20.0) == pytest.approx(5.0)
    assert D_to_droop_pct(40.0) == pytest.approx(2.5)


def test_pfr_deadzone_boundary():
    # |Δf| == 死区 0.06 时视为区内（返回 0）
    assert pfr_deadzone(-0.06) == pytest.approx(0.0)
    assert pfr_deadzone(0.06) == pytest.approx(0.0)
    assert pfr_deadzone(-0.04) == pytest.approx(0.0)
    assert pfr_deadzone(-0.6) == pytest.approx(-0.54)
    assert pfr_deadzone(0.6) == pytest.approx(0.54)


def test_gridforming_vs_pfr_at_large_drop():
    # Δf=-0.6 Hz, D=33.333：构网型 20 MW，传统 18 MW
    D = droop_to_D(3.0)
    assert gridforming_delta_p_pu(-0.6, D, F_N) * 50.0 == pytest.approx(20.0)
    assert pfr_delta_p_pu(-0.6, D, 0.06, F_N) * 50.0 == pytest.approx(18.0)


def test_gridforming_responds_in_deadzone():
    # Δf=-0.04 Hz（死区内）：构网型 1.33 MW，传统 0 MW
    D = droop_to_D(3.0)
    assert gridforming_delta_p_pu(-0.04, D, F_N) * 50.0 == pytest.approx(1.3333, rel=1e-3)
    assert pfr_delta_p_pu(-0.04, D, 0.06, F_N) == pytest.approx(0.0)


def test_support_duration():
    # 20 MWh / 5 MW = 4 h
    assert support_duration_h(20_000.0, 5_000.0) == pytest.approx(4.0)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        system_rocof_hz(DP, 0.0, F_N)
    with pytest.raises(ValueError):
        system_inertia_s(DP, 0.0, F_N)
    with pytest.raises(ValueError):
        inertia_power_pu(-1.0, 0.25, F_N)
    with pytest.raises(ValueError):
        droop_to_D(0.0)
    with pytest.raises(ValueError):
        D_to_droop_pct(0.0)
    with pytest.raises(ValueError):
        pfr_deadzone(-0.6, -0.06)
    with pytest.raises(ValueError):
        support_duration_h(20_000.0, 0.0)
# @AI_GENERATED: end