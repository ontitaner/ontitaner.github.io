# @AI_GENERATED
"""第 07 章一致性测试：构网型并网测试与验收（五项验收指标 + 证据链时标对齐）。

锚定正文 07.x 手算（复用 03/05 章纯函数，本模块只做验收封装）：
  惯量响应：ΔP=0.1 pu → RoCoF=0.25 → J_eq=20 s 达标；RoCoF=0.75 → 6.667 s 不达标
  一次调频：Δf=−0.6 Hz、D=33.333 pu → 构网 0.4 pu=20 MW；传统(死区) 0.36 pu=18 MW
  并网冲击：Δθ=0.01 rad → 0.1 pu 达标；Δθ=0.1 rad → 1.0 pu 越限；ΔV=0.02 → 0.2 pu 越限
  黑启动：ΔV_max=0.05 → 单次最大 0.5 pu；带 0.6 pu → 0.06 pu 越限
  证据链：跨设备时钟偏差 ≤ 10 ms 达标
"""
from __future__ import annotations

import pytest

from ems_lab.acceptance import (
    AcceptanceCriteria,
    EvidenceRecord,
    blackstart_acceptance,
    clock_bias_ms,
    clock_bias_pass,
    evidence_chain_pass,
    inertia_acceptance,
    inrush_components,
    inrush_pass,
    measure_rocof_hz,
    pfr_acceptance,
    pfr_gridforming_pu,
    pfr_traditional_pu,
    response_time_ms,
)


# ---------- 07.3 惯量响应验收 ----------

def test_measure_rocof():
    # 00.1 场景：频率 0.8 s 跌 0.6 Hz → RoCoF 0.75 Hz/s
    assert measure_rocof_hz(0.6, 0.8) == pytest.approx(0.75)


def test_measure_rocof_invalid_window():
    # 窗口时长必须为正
    with pytest.raises(ValueError):
        measure_rocof_hz(0.6, 0.0)


def test_inertia_pass():
    # 改造后 RoCoF=0.25 → J_eq=20 s ≥ 合同 20 s → 合格
    ok, j_eq = inertia_acceptance(0.1, 0.25)
    assert ok and j_eq == pytest.approx(20.0)


def test_inertia_fail():
    # 改造前 RoCoF=0.75 → J_eq≈6.667 s < 20 s → 不合格
    ok, j_eq = inertia_acceptance(0.1, 0.75)
    assert (not ok) and j_eq == pytest.approx(6.6667, abs=1e-3)


# ---------- 07.4 一次调频验收 ----------

def test_pfr_gridforming():
    # Δf=−0.6、D=33.333 → 增发 0.4 pu = 20 MW
    assert pfr_gridforming_pu(-0.6, 33.333) == pytest.approx(0.4, abs=1e-3)


def test_pfr_traditional_large():
    # 传统死区 ±0.06：有效频差 −0.54 → 0.36 pu = 18 MW
    assert pfr_traditional_pu(-0.6, 33.333) == pytest.approx(0.36, abs=1e-3)


def test_pfr_traditional_deadzone():
    # Δf=−0.04 在死区内 → 传统完全不响应（0）
    assert pfr_traditional_pu(-0.04, 33.333) == 0.0


def test_pfr_acceptance_pass():
    # 期望增发 0.4 pu，实测 0.4 pu，偏差 ≤ 0.02 → 合格
    ok, measured = pfr_acceptance(-0.6, 33.333, 0.4)
    assert ok and measured == pytest.approx(0.4, abs=1e-3)


def test_pfr_acceptance_fail():
    # 期望 0.45 pu，实测 0.4 pu，偏差 0.05 > 0.02 → 不合格
    ok, _ = pfr_acceptance(-0.6, 33.333, 0.45)
    assert not ok


# ---------- 07.5 并网冲击验收 ----------

def test_inrush_phase_ok():
    # 预同步达标 Δθ=0.01 rad → 相位冲击 0.1 pu（= I_max）
    i_amp, i_ph = inrush_components(0.0, 0.01)
    assert i_amp == pytest.approx(0.0)
    assert i_ph == pytest.approx(0.1)


def test_inrush_phase_not_synced():
    # 未预同步 Δθ=0.1 rad → 相位冲击 1.0 pu（越限 10 倍）
    _, i_ph = inrush_components(0.0, 0.1)
    assert i_ph == pytest.approx(1.0)


def test_inrush_amplitude():
    # 幅值差 ΔV=0.02 pu → 幅值冲击 0.2 pu（越限）
    i_amp, _ = inrush_components(0.02, 0.0)
    assert i_amp == pytest.approx(0.2)


def test_inrush_pass_boundary():
    # 冲击 ≤ 0.1 合格（含端点）；0.2 越限
    assert inrush_pass(0.1) is True
    assert inrush_pass(0.2) is False


# ---------- 07.6 黑启动带载验收 ----------

def test_blackstart_pass():
    # 单次最大无功阶跃 0.5 pu → 跌落 0.05 pu（= ΔV_max，含端点）→ 合格
    ok, dv = blackstart_acceptance(0.5)
    assert ok and dv == pytest.approx(0.05)


def test_blackstart_fail():
    # 一次带 0.6 pu → 跌落 0.06 pu > 0.05 → 越限
    ok, dv = blackstart_acceptance(0.6)
    assert (not ok) and dv == pytest.approx(0.06)


# ---------- 07.7 证据链时标对齐 ----------

def test_clock_bias():
    assert clock_bias_ms(0.0, 5.0) == pytest.approx(5.0)
    assert clock_bias_ms(205.0, 200.0) == pytest.approx(5.0)


def test_clock_bias_pass():
    assert clock_bias_pass(5.0) is True
    assert clock_bias_pass(10.0) is True      # 含端点
    assert clock_bias_pass(15.0) is False


def test_response_time():
    # 响应时间 = T_start − T_cmd = 200 − 0 = 200 ms
    assert response_time_ms(200.0, 0.0) == pytest.approx(200.0)


def test_evidence_chain_pass():
    # 三个事件跨调度/EMS/PCS 记录，最大偏差 5 ms ≤ 10 ms → 合格
    records = [
        EvidenceRecord("T_evt", "调度主站", 0.0),
        EvidenceRecord("T_evt", "EMS", 5.0),
        EvidenceRecord("T_start", "调度主站", 200.0),
        EvidenceRecord("T_start", "EMS", 205.0),
        EvidenceRecord("T_end", "调度主站", 800.0),
        EvidenceRecord("T_end", "PCS 录波", 803.0),
    ]
    ok, max_bias = evidence_chain_pass(records)
    assert ok and max_bias == pytest.approx(5.0)


def test_evidence_chain_fail():
    # 存在 15 ms 偏差 > 10 ms → 不合格
    records = [
        EvidenceRecord("T_evt", "调度主站", 0.0),
        EvidenceRecord("T_evt", "EMS", 15.0),
        EvidenceRecord("T_start", "调度主站", 200.0),
        EvidenceRecord("T_start", "EMS", 200.0),
    ]
    ok, max_bias = evidence_chain_pass(records)
    assert (not ok) and max_bias == pytest.approx(15.0)


def test_evidence_chain_empty():
    # 空证据链非法
    with pytest.raises(ValueError):
        evidence_chain_pass([])
# @AI_GENERATED: end