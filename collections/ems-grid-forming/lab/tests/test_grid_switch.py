# @AI_GENERATED
"""第 05 章一致性测试：并网冲击电流、预同步阈值、切换时序、黑启动带载。

锚定正文 05.x 手算：
  冲击电流：幅值差 0.02 pu → 0.2 pu；相位差 0.1 rad → 1.0 pu（I=ΔU/X_s，X_s=0.1 pu）
  预同步阈值（I_max=0.1 pu）：ΔV_max=0.01 pu，Δθ_max=0.01 rad≈0.57°；达标 Δθ=0.01 rad → 0.1 pu
  切换时序：预同步 Δθ0=0.1 rad、Δf=0.05 Hz → t≈0.318 s；解列 P=0.2 pu、爬坡 0.5 pu/s → 0.4 s
  黑启动带载：X_s=0.1 pu、允许跌落 0.05 pu → 单次最大无功阶跃 0.5 pu；一次带 0.6 pu → ΔV=0.06 pu（越限）
"""
from __future__ import annotations

import pytest

from ems_lab.grid_switch import (
    amplitude_threshold_pu,
    inrush_from_amplitude,
    inrush_from_phase,
    max_load_step_pu,
    phase_threshold_rad,
    pre_sync_time,
    unload_time,
    voltage_drop_pu,
)


def test_inrush_from_amplitude():
    # 幅值差 0.02 pu、X_s=0.1 pu → 冲击 0.2 pu
    assert inrush_from_amplitude(0.02) == pytest.approx(0.2)


def test_inrush_from_amplitude_zero():
    # 幅值一致 → 无冲击
    assert inrush_from_amplitude(0.0) == pytest.approx(0.0)


def test_inrush_from_phase():
    # 相位差 0.1 rad（5.7°）、X_s=0.1 pu → 冲击 1.0 pu
    assert inrush_from_phase(0.1) == pytest.approx(1.0)


def test_inrush_from_phase_small():
    # 预同步达标 Δθ=0.01 rad → 冲击 0.1 pu
    assert inrush_from_phase(0.01) == pytest.approx(0.1)


def test_amplitude_threshold():
    # I_max=0.1 pu、X_s=0.1 pu → ΔV_max=0.01 pu
    assert amplitude_threshold_pu() == pytest.approx(0.01)


def test_phase_threshold():
    # I_max=0.1 pu、X_s=0.1 pu、V=1.0 → Δθ_max=0.01 rad（约 0.57°）
    assert phase_threshold_rad() == pytest.approx(0.01)


def test_phase_threshold_consistent_with_inrush():
    # 阈值反推自洽：Δθ_max 下的冲击恰等于 I_max
    dtheta_max = phase_threshold_rad()
    assert inrush_from_phase(dtheta_max) == pytest.approx(0.1)


def test_amplitude_threshold_consistent_with_inrush():
    # ΔV_max 下的冲击恰等于 I_max
    dv_max = amplitude_threshold_pu()
    assert inrush_from_amplitude(dv_max) == pytest.approx(0.1)


def test_pre_sync_time():
    # Δθ0=0.1 rad、Δf=0.05 Hz → t = 0.1/(2π·0.05) ≈ 0.318 s
    assert pre_sync_time(0.1, 0.05) == pytest.approx(0.3183, rel=1e-3)


def test_pre_sync_time_symmetric():
    # 追赶时长对相位差/调频量的符号对称（取绝对值）
    assert pre_sync_time(-0.1, 0.05) == pytest.approx(pre_sync_time(0.1, 0.05))
    assert pre_sync_time(0.1, -0.05) == pytest.approx(pre_sync_time(0.1, 0.05))


def test_unload_time():
    # P=0.2 pu、爬坡 0.5 pu/s → 回零 0.4 s
    assert unload_time(0.2) == pytest.approx(0.4)


def test_voltage_drop():
    # 黑启动带载：ΔQ=0.6 pu、X_s=0.1 pu → 电压跌落 0.06 pu
    assert voltage_drop_pu(0.6) == pytest.approx(0.06)


def test_voltage_drop_batches():
    # 分批带载的无功阶跃：0.05/0.15/0.40 pu → 0.005/0.015/0.040 pu
    assert voltage_drop_pu(0.05) == pytest.approx(0.005)
    assert voltage_drop_pu(0.15) == pytest.approx(0.015)
    assert voltage_drop_pu(0.40) == pytest.approx(0.040)


def test_max_load_step():
    # 允许跌落 0.05 pu、X_s=0.1 pu → 单次最大无功阶跃 0.5 pu
    assert max_load_step_pu() == pytest.approx(0.5)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        inrush_from_amplitude(0.02, 0.0)
    with pytest.raises(ValueError):
        inrush_from_phase(0.01, xs=0.0)
    with pytest.raises(ValueError):
        inrush_from_phase(0.01, v=0.0)
    with pytest.raises(ValueError):
        amplitude_threshold_pu(xs=0.0)
    with pytest.raises(ValueError):
        phase_threshold_rad(xs=0.0)
    with pytest.raises(ValueError):
        pre_sync_time(0.1, 0.0)
    with pytest.raises(ValueError):
        unload_time(-0.2)
    with pytest.raises(ValueError):
        unload_time(0.2, 0.0)
    with pytest.raises(ValueError):
        voltage_drop_pu(0.6, 0.0)
    with pytest.raises(ValueError):
        max_load_step_pu(xs=0.0)
# @AI_GENERATED: end