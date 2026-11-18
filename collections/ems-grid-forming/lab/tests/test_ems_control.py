# @AI_GENERATED
"""第 06 章一致性测试：参数一致性校验对象切换 + 并离网状态机。

锚定正文 06.x 手算：
  参数校验（构网三参数 J/D/V_ref）：J>0、D>0 且 δ%=100/D ∈ [1,10]、V_ref ∈ [0.9,1.1]
    J=4.0/D=20/V_ref=1.0 合法；J=0、D=0、D=200(δ=0.5%)、V_ref=1.2 非法
  状态机（三状态）：并网+转入离网→离网；离网+再并网→并网；
    并网/离网+电网全黑→黑启动；黑启动+带载完成→离网；非法迁移抛 ValueError
  时序：解列 0.4+0.1=0.5 s；再并网 0.318+0.2+0.4≈0.92 s
"""
from __future__ import annotations

import pytest

from ems_lab.ems_control import (
    EV_BLACKOUT,
    EV_LOADED,
    EV_RESYNC,
    EV_UNLOAD,
    GridMode,
    resync_duration_s,
    transition,
    unload_duration_s,
    validate_vsg_params,
)
from ems_lab.inertia import D_to_droop_pct


# ---------- 06.3 参数一致性校验 ----------

def test_validate_vsg_params_valid():
    # J=4.0、D=20、V_ref=1.0（02 章教学值）→ 合法，错误列表为空
    assert validate_vsg_params(4.0, 20.0, 1.0) == []


def test_validate_vsg_params_j_zero():
    # J=0 → 退回无惯量电流源，非法
    errors = validate_vsg_params(0.0, 20.0, 1.0)
    assert errors and "J" in errors[0]


def test_validate_vsg_params_d_zero():
    # D=0 → 无阻尼会振荡，非法
    errors = validate_vsg_params(4.0, 0.0, 1.0)
    assert errors and "D" in errors[0]


def test_validate_vsg_params_droop_high():
    # D=200 → δ=0.5% < 1%，非法
    errors = validate_vsg_params(4.0, 200.0, 1.0)
    assert errors and "调差率" in errors[0]


def test_validate_vsg_params_droop_low():
    # D=5 → δ=20% > 10%，非法
    errors = validate_vsg_params(4.0, 5.0, 1.0)
    assert errors and "调差率" in errors[0]


def test_validate_vsg_params_droop_boundary():
    # δ% 边界语义：D=10→10%（含上限）、D=100→1%（含下限）均合法
    assert validate_vsg_params(4.0, 10.0, 1.0) == []
    assert validate_vsg_params(4.0, 100.0, 1.0) == []


def test_validate_vsg_params_vref_high():
    # V_ref=1.2 > 1.1，非法
    errors = validate_vsg_params(4.0, 20.0, 1.2)
    assert errors and "V_ref" in errors[0]


def test_validate_vsg_params_vref_boundary():
    # V_ref 边界语义：0.9 / 1.1（含端点）均合法
    assert validate_vsg_params(4.0, 20.0, 0.9) == []
    assert validate_vsg_params(4.0, 20.0, 1.1) == []


def test_droop_pct_from_D():
    # D=20 → δ=5%（复用 03 章倒数关系）
    assert D_to_droop_pct(20.0) == pytest.approx(5.0)


# ---------- 06.4 并离网状态机 ----------

def test_transition_unload():
    # 并网 + 转入离网 → 离网
    assert transition(GridMode.ON_GRID, EV_UNLOAD) is GridMode.ISLAND


def test_transition_resync():
    # 离网 + 再并网 → 并网
    assert transition(GridMode.ISLAND, EV_RESYNC) is GridMode.ON_GRID


def test_transition_blackout_on_grid():
    # 并网 + 电网全黑 → 黑启动
    assert transition(GridMode.ON_GRID, EV_BLACKOUT) is GridMode.BLACK_START


def test_transition_blackout_island():
    # 离网 + 电网全黑 → 黑启动（全黑时先黑启动，而非盲目再并网）
    assert transition(GridMode.ISLAND, EV_BLACKOUT) is GridMode.BLACK_START


def test_transition_loaded():
    # 黑启动 + 带载完成 → 离网
    assert transition(GridMode.BLACK_START, EV_LOADED) is GridMode.ISLAND


def test_transition_invalid():
    # 非法迁移：并网状态下不允许「带载完成」
    with pytest.raises(ValueError):
        transition(GridMode.ON_GRID, EV_LOADED)


# ---------- 06.4 状态机时序（复用 05 章时序门） ----------

def test_unload_duration():
    # 解列：回零 0.4 s + 延时 0.1 s = 0.5 s
    assert unload_duration_s() == pytest.approx(0.5)


def test_resync_duration():
    # 再并网：预同步 0.318 s + 窗口 0.2 s + 功率转移 0.4 s ≈ 0.92 s
    assert resync_duration_s() == pytest.approx(0.9183, abs=1e-3)


def test_invalid_inputs():
    # D 必须为正
    with pytest.raises(ValueError):
        D_to_droop_pct(0.0)
# @AI_GENERATED: end