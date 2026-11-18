# @AI_GENERATED
"""第 02 章一致性测试：VSG 摇摆方程与 Q-V 下垂，锚定正文 02.5 手算。"""
from __future__ import annotations

import pytest

from ems_lab.vsg import VSGConfig, q_v_droop, rocof_hz, swing_domega, swing_step


def cfg(**kw):
    return VSGConfig(**kw)


def test_swing_step_base():
    # 初始 ω=1, p_e=0.6, p_ref=0.5, J=4, D=20, dt=0.1
    # dω/dt = (0.5-0.6-20·0)/4 = -0.025; ω_next = 1 - 0.025·0.1 = 0.9975
    assert swing_step(1.0, 0.6, cfg()) == pytest.approx(0.9975)


def test_swing_domega_base():
    assert swing_domega(1.0, 0.6, cfg()) == pytest.approx(-0.025)


def test_j_doubling_halves_rocof():
    # J=4 -> -1.25 Hz/s; J=8 -> -0.625 Hz/s，恰好减半
    assert rocof_hz(0.6, 0.5, 4.0) == pytest.approx(-1.25)
    assert rocof_hz(0.6, 0.5, 8.0) == pytest.approx(-0.625)
    assert rocof_hz(0.6, 0.5, 4.0) == pytest.approx(2 * rocof_hz(0.6, 0.5, 8.0))


def test_steady_state_determined_by_D():
    # 稳态 dω/dt=0 → ω = 1 + (p_ref - p_e)/D
    for D in (20.0, 40.0):
        omega_ss = 1.0 + (0.5 - 0.6) / D
        assert swing_domega(omega_ss, 0.6, cfg(D=D)) == pytest.approx(0.0, abs=1e-12)
    assert 1.0 + (0.5 - 0.6) / 20.0 == pytest.approx(0.995)
    assert 1.0 + (0.5 - 0.6) / 40.0 == pytest.approx(0.9975)


def test_q_v_droop():
    assert q_v_droop(0.2, cfg()) == pytest.approx(0.99)
    assert q_v_droop(-0.2, cfg()) == pytest.approx(1.01)
    assert q_v_droop(0.0, cfg()) == pytest.approx(1.0)


def test_invalid_J():
    with pytest.raises(ValueError):
        VSGConfig(J=0.0)
    with pytest.raises(ValueError):
        VSGConfig(J=-1.0)


def test_invalid_D():
    with pytest.raises(ValueError):
        VSGConfig(D=-1.0)
# @AI_GENERATED: end