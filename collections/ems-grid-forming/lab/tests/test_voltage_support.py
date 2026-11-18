# @AI_GENERATED
"""第 04 章一致性测试：电压支撑（Q-V 下垂反读）、弱电网电压-无功敏感度、多机均流、环流。

锚定正文 04.x 手算：
  电压支撑：V=0.98 → Q=(1.0−0.98)/0.05=0.4 pu（20 Mvar）；V=1.02 → Q=−0.4 pu（吸收）
  敏感度：ΔQ=0.2 pu → 本站 ΔV=0.2/1.8≈0.111 pu，强电网 ΔV=0.2/3≈0.067 pu（1.67 倍）
  多机均流：k_q1=0.05、k_q2=0.10、总 0.3 pu → Q1=0.2 / Q2=0.1（2:1 反比）
  环流：幅值差 0.02 pu、X_s1=X_s2=0.1 pu → 0.1 pu（5 Mvar）
"""
from __future__ import annotations

import pytest

from ems_lab.voltage_support import (
    circ_current_pu,
    q_from_voltage,
    share_q,
    voltage_deviation_pu,
)
from ems_lab.vsg import VSGConfig, q_v_droop


def test_q_from_voltage_nominal():
    # 额定电压 → 无功参考（Q_ref=0）
    assert q_from_voltage(1.0) == pytest.approx(0.0)


def test_q_from_voltage_support():
    # 电压跌 0.02 pu → 增发 0.4 pu = 20 Mvar
    assert q_from_voltage(0.98) == pytest.approx(0.4)


def test_q_from_voltage_absorb():
    # 电压升 0.02 pu → 吸收 0.4 pu（Q<0）
    assert q_from_voltage(1.02) == pytest.approx(-0.4)


def test_q_from_voltage_inverse_of_vsg_droop():
    # 与 02 章 q_v_droop 互为反函数（同一参数）
    cfg = VSGConfig()
    for q in (0.0, 0.2, -0.2, 0.4):
        v = q_v_droop(q, cfg)
        assert q_from_voltage(v, cfg.v_ref, cfg.k_q, cfg.q_ref) == pytest.approx(q)


def test_voltage_deviation_weak_grid():
    # ΔQ=0.2 pu、SCR=1.8 → ΔV≈0.111 pu
    assert voltage_deviation_pu(0.2, 1.8) == pytest.approx(0.1111, rel=1e-3)


def test_voltage_deviation_strong_grid():
    # ΔQ=0.2 pu、SCR=3.0 → ΔV≈0.067 pu
    assert voltage_deviation_pu(0.2, 3.0) == pytest.approx(0.0667, rel=1e-3)


def test_voltage_deviation_ratio():
    # 本站电压敏感度是强电网的 1.67 倍（X_g 之比 = 0.556/0.333）
    assert voltage_deviation_pu(0.2, 1.8) / voltage_deviation_pu(0.2, 3.0) == pytest.approx(
        5.0 / 3.0, rel=1e-3
    )


def test_share_q_inverse_proportional():
    # 多机均流：k_q1=0.05、k_q2=0.10、总 0.3 pu → Q1=0.2 / Q2=0.1（2:1）
    q1, q2 = share_q(0.3, 0.05, 0.10)
    assert q1 == pytest.approx(0.2)
    assert q2 == pytest.approx(0.1)


def test_share_q_ratio_and_sum():
    # Q1/Q2 = k_q2/k_q1，且 Q1+Q2 = q_total
    q1, q2 = share_q(0.3, 0.05, 0.10)
    assert q1 / q2 == pytest.approx(0.10 / 0.05)
    assert q1 + q2 == pytest.approx(0.3)


def test_share_q_same_slope_splits_evenly():
    # k_q 相同时均分
    q1, q2 = share_q(0.3, 0.05, 0.05)
    assert q1 == pytest.approx(0.15)
    assert q2 == pytest.approx(0.15)


def test_circ_current():
    # 幅值差 0.02 pu、X_s1=X_s2=0.1 pu → 0.1 pu
    assert circ_current_pu(0.02, 0.1, 0.1) == pytest.approx(0.1)


def test_circ_current_zero_when_no_diff():
    # 幅值一致 → 无环流
    assert circ_current_pu(0.0, 0.1, 0.1) == pytest.approx(0.0)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        q_from_voltage(1.0, k_q=0.0)
    with pytest.raises(ValueError):
        voltage_deviation_pu(0.2, 0.0)
    with pytest.raises(ValueError):
        share_q(0.3, 0.0, 0.1)
    with pytest.raises(ValueError):
        share_q(0.3, 0.05, 0.0)
    with pytest.raises(ValueError):
        circ_current_pu(0.02, 0.0, 0.0)
# @AI_GENERATED: end