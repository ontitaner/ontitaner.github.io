# @AI_GENERATED
"""第 08 章一致性测试：惯量/阻尼拆分计量 + 结算 + 考核判定。

锚定正文 08.x 手算（主线 50 MW/100 MWh、S_n=50 MVA、J_vsg=13.333 s、D=33.333）：
- 拆分功率：惯量 3.333 MW（RoCoF=0.25），阻尼 20 MW（Δf=0.6 Hz）。
- 惯量电量：W_inertia = J·Δf·S_n/f_n = 8 MW·s，与 RoCoF/持续时长无关。
- 阻尼电量：W_droop = D·S_n/f_n·[Δf²/(2RoCoF)+Δf·T_hold] = 24+600 = 624 MW·s。
- 结算：惯量 300×13.333 = 4000 元；阻尼 360×(624/3600) = 62.4 元。
- 考核：完成率阈值 60%；同向 50% → 缺额计费 31.2 元；反向 → 加倍 124.8 元。
"""
from __future__ import annotations

import pytest

from ems_lab.settlement import (
    SettlementConfig,
    assess,
    completion_rate,
    droop_energy_mws,
    droop_power_mw,
    inertia_energy_mws,
    inertia_power_mw,
    mws_to_mwh,
    penalty_fee,
    settle_droop,
    settle_inertia,
    settle_inertia_as_energy,
    split_power_mw,
)

CFG = SettlementConfig()


def test_split_power():
    # RoCoF=0.25 → 惯量 3.333 MW；Δf=0.6 → 阻尼 20 MW
    p_inertia, p_droop = split_power_mw(0.6, 0.25, CFG)
    assert p_inertia == pytest.approx(3.3333, rel=1e-3)
    assert p_droop == pytest.approx(20.0, rel=1e-3)


def test_inertia_power_zero_when_rocof_zero():
    # 惯量功率只在频率变化时存在
    assert inertia_power_mw(13.333, 0.0, CFG) == pytest.approx(0.0)


def test_droop_power_scales_with_df():
    # D·Δf/f_n·S_n：Δf=0.3 → 10 MW，Δf=0.6 → 20 MW
    assert droop_power_mw(0.3, CFG) == pytest.approx(10.0, rel=1e-3)
    assert droop_power_mw(0.6, CFG) == pytest.approx(20.0, rel=1e-3)


def test_inertia_energy_independent_of_rocof_and_hold():
    # 惯量电量只与 J、Δf 有关：(40/3)×0.6 = 8 MW·s，改 RoCoF/T_hold 不变
    base = inertia_energy_mws(CFG)
    assert base == pytest.approx(8.0, rel=1e-3)
    assert base == pytest.approx((40.0 / 3.0) * 0.6, rel=1e-6)
    alt = SettlementConfig(rocof_hz=0.5, t_hold_s=60.0)
    assert inertia_energy_mws(alt) == pytest.approx(base, rel=1e-6)


def test_droop_energy_drop_and_hold():
    # 跌落段 24 + 稳定段 600 = 624 MW·s
    assert droop_energy_mws(CFG) == pytest.approx(624.0, rel=1e-3)


def test_droop_energy_grows_with_hold():
    # 稳定段随 T_hold 线性增长：T_hold=30 → 624；T_hold=60 → 624+600=1224
    long_hold = SettlementConfig(t_hold_s=60.0)
    assert droop_energy_mws(long_hold) == pytest.approx(1224.0, rel=1e-3)


def test_mws_to_mwh():
    assert mws_to_mwh(3600.0) == pytest.approx(1.0)
    assert mws_to_mwh(624.0) == pytest.approx(0.17333, rel=1e-4)


def test_completion_rate():
    assert completion_rate(312.0, 624.0) == pytest.approx(0.5)


def test_assess_verdict():
    assert assess(624.0, 624.0) == "pass"
    assert assess(624.0, 400.0) == "pass"          # 64.1% ≥ 60%
    assert assess(624.0, 312.0) == "under"         # 50% < 60%
    assert assess(624.0, -624.0) == "reverse"      # 反向


def test_assess_completion_boundary():
    # 边界：完成率恰为 60% 视为通过
    assert assess(624.0, 374.4) == "pass"


def test_penalty_under():
    # 完成率 50% → 缺额 312 MW·s = 0.08667 MWh → 360×0.08667 ≈ 31.2 元
    assert penalty_fee(624.0, 312.0, CFG) == pytest.approx(31.2, rel=1e-3)


def test_penalty_reverse():
    # 反向 → 加倍：2×360×(624/3600) = 124.8 元
    assert penalty_fee(624.0, -624.0, CFG) == pytest.approx(124.8, rel=1e-3)


def test_penalty_pass():
    assert penalty_fee(624.0, 624.0, CFG) == pytest.approx(0.0)


def test_settle_inertia_by_capacity():
    # 惯量按容量：300 × 13.333 = 4000 元
    assert settle_inertia(CFG) == pytest.approx(4000.0, rel=1e-3)


def test_settle_droop_by_energy():
    # 阻尼按电量：360 × 624/3600 = 62.4 元
    assert settle_droop(CFG) == pytest.approx(62.4, rel=1e-3)


def test_settle_inertia_as_energy_is_much_smaller():
    # 错误口径：惯量按电量只有 360×(8/3600) = 0.8 元，比正确口径小 5000 倍
    wrong = settle_inertia_as_energy(CFG)
    assert wrong == pytest.approx(0.8, rel=1e-3)
    assert settle_inertia(CFG) / wrong == pytest.approx(5000.0, rel=1e-3)


def test_config_validation():
    with pytest.raises(ValueError):
        SettlementConfig(completion_min=0.0)
    with pytest.raises(ValueError):
        SettlementConfig(sn_mva=0.0)
    with pytest.raises(ValueError):
        SettlementConfig(rocof_hz=0.0)
# @AI_GENERATED: end