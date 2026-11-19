# @AI_GENERATED
"""第 09 章一致性测试：验收失败根因诊断（反推对表 + 三类根因）。

锚定正文 09.x 手算（复用 07/08 章结果值，本模块只做反推与对表）：
  一次调频：实测 0.3 pu → 反推 D=25（δ=4%）≠ 配置 33.333 → 参数误设
  惯量：J_eq=10 s → 本站贡献 3.333 s ≪ 配置 13.333 s，SOC=40% < 50% → SOC 不足
  方向：期望 +0.4 / 实测 −0.4 → 出力方向接反
  时钟：最大偏差 15 ms > 10 ms → 时钟未对时
"""
from __future__ import annotations

import pytest

from ems_lab.diagnosis import (
    back_calc_D,
    back_calc_station_J,
    diagnose_clock,
    diagnose_direction,
    diagnose_inertia_failure,
    diagnose_pfr_failure,
)


# ---------- 09.2 反推函数 ----------

def test_back_calc_D():
    # 实测 0.3 pu、Δf=−0.6 Hz → D = 0.3×50/0.6 = 25 pu
    assert back_calc_D(0.3, -0.6) == pytest.approx(25.0)


def test_back_calc_D_zero_df():
    # Δf=0 无法反推 D
    with pytest.raises(ValueError):
        back_calc_D(0.3, 0.0)


def test_back_calc_station_J():
    # J_eq=10 s、J_sys0=6.667 s → 本站贡献 3.333 s
    assert back_calc_station_J(10.0, 6.667) == pytest.approx(3.333, abs=1e-3)


# ---------- 09.3 案例 A：一次调频失败（D 参数误设） ----------

def test_pfr_diagnose_pass():
    # 第 1 拍（达标）：实测 0.4 vs 期望 0.4，偏差 0 ≤ 0.02
    assert diagnose_pfr_failure(0.4, 0.4, 0.02, 33.333, -0.6) == "pass"


def test_pfr_diagnose_param_mismatch():
    # 第 2 拍（失败）：实测 0.3 → 反推 D=25 ≠ 配置 33.333 → 参数误设
    assert diagnose_pfr_failure(0.3, 0.4, 0.02, 33.333, -0.6) == "param_mismatch"


def test_pfr_diagnose_expected_wrong():
    # 设备输出正确（反推 D≈33.333=配置），但期望值口径错（0.5）→ expected_wrong
    assert diagnose_pfr_failure(0.4, 0.5, 0.02, 33.333, -0.6) == "expected_wrong"


# ---------- 09.4 案例 B：惯量失败（SOC 不足） ----------

def test_inertia_diagnose_pass():
    # 第 1 拍（SOC 正常）：J_eq=20 s ≥ 要求 20 s → pass
    assert diagnose_inertia_failure(20.0, 20.0, 6.667, 13.333, 0.60, 0.50) == "pass"


def test_inertia_diagnose_soc_low():
    # 第 2 拍（SOC 不足）：J_eq=10 s、SOC=40% < 50% → soc_low
    assert diagnose_inertia_failure(10.0, 20.0, 6.667, 13.333, 0.40, 0.50) == "soc_low"


def test_inertia_diagnose_underperformed():
    # SOC 正常但 J 只发挥 3.333 ≪ 配置 13.333 → 配置了没发挥（量测污染嫌疑）
    assert diagnose_inertia_failure(10.0, 20.0, 6.667, 13.333, 0.60, 0.50) == "underperformed"


def test_inertia_diagnose_param_j_low():
    # SOC 正常、发挥正常（反推 8.333=配置 8.333），但整定本身偏小 → param_j_low
    assert diagnose_inertia_failure(15.0, 20.0, 6.667, 8.333, 0.60, 0.50) == "param_j_low"


# ---------- 09.5 案例 C：结算反向（出力方向接反） ----------

def test_direction_reversed():
    # 期望 +0.4（增发）、实测 −0.4（减发）→ 方向接反
    assert diagnose_direction(0.4, -0.4) == "reversed"


def test_direction_normal():
    # 同号 → 方向正常
    assert diagnose_direction(0.4, 0.4) == "normal"


def test_direction_zero():
    # 实测为 0 无法判定方向
    with pytest.raises(ValueError):
        diagnose_direction(0.4, 0.0)


# ---------- 09.6 案例 D：证据链失败（时钟未对时） ----------

def test_clock_drift():
    # 最大偏差 15 ms > 10 ms → 时钟未对时
    assert diagnose_clock(15.0) == "clock_drift"


def test_clock_pass():
    # 最大偏差 5 ms ≤ 10 ms → 达标
    assert diagnose_clock(5.0) == "pass"
# @AI_GENERATED: end