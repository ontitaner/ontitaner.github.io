# @AI_GENERATED
"""第 12 章一致性测试：锚定正文手算数值与边界语义。

主案例：箱3 偏差 -2.25 -> -3.25 漂移触发；11 点切前 7 训练 / 后 4 验证；
再训练 v2=[+0.5,-0.9,-3.25]；验证集 v1 RMSE=1.25、v2 RMSE=0.25；
发布卡 release=True；回滚卡线上 1.5 > 基线 1.25 -> True。
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.versioning import (  # noqa: E402
    detect_drift,
    release_check,
    retrain_bias,
    rmse_of,
    should_rollback,
    time_split,
)

P_PHYS = [2, 3, 10, 15, 20, 22, 24, 20, 21, 22, 23]
P_MEAS = [2.5, 3.5, 9.1, 14.1, 16.75, 18.75, 20.75, 16.5, 17.5, 18.5, 19.5]
BIAS_V1 = [0.5, -0.9, -2.25]
BIAS_V2 = [0.5, -0.9, -3.25]


def test_detect_drift_trigger():
    # 12.4 主案例：|−3.25 − (−2.25)| = 1.0 >= 1.0 -> True（等号算触发）
    assert detect_drift(-3.25, -2.25) is True


def test_detect_drift_boundary_equal():
    # 边界语义：|漂移| 恰好等于阈值也触发（>= 不是 >）
    assert detect_drift(-1.0, 0.0, threshold=1.0) is True


def test_detect_drift_no_drift():
    # 未漂移：drift 0.0 < 1.0 -> False
    assert detect_drift(-2.25, -2.25) is False


def test_time_split_main():
    (tr_p, tr_m), (va_p, va_m) = time_split(P_PHYS, P_MEAS, split_idx=7)
    assert tr_p == [2, 3, 10, 15, 20, 22, 24]
    assert tr_m == [2.5, 3.5, 9.1, 14.1, 16.75, 18.75, 20.75]
    assert va_p == [20, 21, 22, 23]
    assert va_m == [16.5, 17.5, 18.5, 19.5]


def test_time_split_length_mismatch():
    with pytest.raises(ValueError):
        time_split([1.0, 2.0], [1.0], split_idx=1)


def test_time_split_invalid_idx():
    with pytest.raises(ValueError):
        time_split(P_PHYS, P_MEAS, split_idx=0)
    with pytest.raises(ValueError):
        time_split(P_PHYS, P_MEAS, split_idx=len(P_PHYS))


def test_retrain_bias_v2():
    (tr_p, tr_m), _ = time_split(P_PHYS, P_MEAS, split_idx=7)
    v2 = retrain_bias(tr_p, tr_m)
    assert v2 == pytest.approx(BIAS_V2, abs=1e-9)


def test_rmse_v1_vs_v2():
    (tr_p, tr_m), (va_p, va_m) = time_split(P_PHYS, P_MEAS, split_idx=7)
    v2 = retrain_bias(tr_p, tr_m)
    assert rmse_of(va_p, va_m, BIAS_V1) == pytest.approx(1.25, abs=1e-9)
    assert rmse_of(va_p, va_m, v2) == pytest.approx(0.25, abs=1e-9)


def test_release_check_pass():
    # 12.7 主案例：0.25 < 1.25、准确率 (1-0.25/30)x100=99.166...% >= 80%
    check = release_check(0.25, 1.25)
    assert check["improved"] is True
    assert check["accuracy"] == pytest.approx(99.1666667, abs=1e-4)
    assert check["accuracy_ok"] is True
    assert check["release"] is True


def test_release_check_equal_not_improved():
    # 边界语义：rmse_new == rmse_prev 时 improved=False（严格 <），不发布
    check = release_check(1.25, 1.25)
    assert check["improved"] is False
    assert check["release"] is False


def test_release_check_accuracy_below_threshold():
    # 即使 RMSE 改进，准确率不达标也不发布
    check = release_check(8.0, 10.0)   # accuracy = (1-8/30)x100 = 73.33% < 80%
    assert check["improved"] is True
    assert check["accuracy_ok"] is False
    assert check["release"] is False


def test_should_rollback_trigger():
    # 12.8 主案例：线上 1.5 > 基线 1.25 -> 回滚
    assert should_rollback(1.5, 1.25) is True


def test_should_rollback_boundary_equal():
    # 边界语义：等号不回滚（严格 >）
    assert should_rollback(1.25, 1.25) is False