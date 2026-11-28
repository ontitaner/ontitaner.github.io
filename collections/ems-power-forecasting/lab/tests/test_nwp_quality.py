# @AI_GENERATED
"""第 04 章一致性测试：NWP 气象数据质量门控（五类坏点 + 综合掩码 + 缺测回填）。

锚定正文 04.x 手算（主线 30 MW 光伏，GHI 范围 [0,1200]、变化率上限 600、卡死 4 点、夜间 0 值豁免）：
  GHI=[800,810,NaN,820,820,820,820,300,1200,1300]
  -> 缺测(索引2) + 卡死(索引3~6) + 跳变(索引8) + 超限(索引9) -> 坏点 7 个、有效点 3 个、有效点率 30%
  回填：内部缺测线性插值 815；时标 15min 网格、容差 ±2.5min
"""
from __future__ import annotations

import pytest

from ems_lab.nwp_quality import (
    fill_missing,
    missing_mask,
    quality_mask,
    range_mask,
    step_mask,
    stuck_mask,
    timestamp_mask,
)


def test_missing_mask():
    assert missing_mask([800.0, 810.0, float("nan"), 820.0]) == [
        False, False, True, False,
    ]
    assert missing_mask([None, 800.0]) == [True, False]


def test_range_mask():
    # -50（负值）与 1300（超上限）超限；1200 恰等于上限不超限
    assert range_mask([-50.0, 800.0, 1200.0, 1300.0], 0.0, 1200.0) == [
        True, False, False, True,
    ]


def test_range_mask_skips_missing():
    # 缺测点不在超限判定内（由缺测负责）
    assert range_mask([float("nan"), 800.0], 0.0, 1200.0) == [False, False]


def test_step_mask_first_point_and_missing():
    # 首点不判、缺测点跳过
    assert step_mask([300.0, 1200.0], 600.0) == [False, True]
    assert step_mask([300.0, float("nan"), 1200.0], 600.0) == [False, False, True]


def test_step_mask_cloud_no_false_kill():
    # 820 -> 300 差 520 <= 600，不判跳变（云团经过）
    assert step_mask([820.0, 300.0], 600.0) == [False, False]


def test_stuck_mask_flat_run():
    # 820×4 -> 4 点全判卡死
    assert stuck_mask([820.0, 820.0, 820.0, 820.0], 4, 0.0) == [
        True, True, True, True,
    ]
    # 3 点恒等 < max_run=4 -> 不判
    assert stuck_mask([820.0, 820.0, 820.0], 4, 0.0) == [False, False, False]


def test_stuck_mask_night_zero_exempt():
    # 夜间 0×5 是合法平坦，不判卡死
    assert stuck_mask([0.0, 0.0, 0.0, 0.0, 0.0], 4, 0.0) == [
        False, False, False, False, False,
    ]


def test_timestamp_mask():
    # 11:00 = 660 min -> 对齐；12:07:30 = 727.5 min -> 偏移 7.5 > 2.5 -> 错位
    assert timestamp_mask([660.0]) == [False]
    assert timestamp_mask([727.5]) == [True]
    assert timestamp_mask([662.0]) == [False]   # 偏移 2 min <= 2.5，仍对齐


def test_quality_mask_combined():
    ghi = [800.0, 810.0, float("nan"), 820.0, 820.0, 820.0, 820.0, 300.0, 1200.0, 1300.0]
    m = quality_mask(ghi, 0.0, 1200.0, 600.0, 4, 0.0)
    assert m == [False, False, True, True, True, True, True, False, True, True]
    assert sum(m) == 7          # 坏点 7 个
    assert len(m) - sum(m) == 3  # 有效点 3 个
    assert (len(m) - sum(m)) / len(m) == pytest.approx(0.3)  # 有效点率 30%


def test_quality_mask_all_good():
    assert quality_mask([800.0, 810.0, 820.0], 0.0, 1200.0, 600.0, 4, 0.0) == [
        False, False, False,
    ]


def test_fill_missing_internal_linear():
    # 内部缺测线性插值：(810+820)/2 = 815
    out = fill_missing([810.0, float("nan"), 820.0])
    assert out[1] == pytest.approx(815.0)


def test_fill_missing_edges_nearest():
    # 首尾缺测用最近有效值回填
    assert fill_missing([float("nan"), float("nan"), 800.0]) == [800.0, 800.0, 800.0]
    assert fill_missing([800.0, float("nan"), float("nan")]) == [800.0, 800.0, 800.0]


def test_fill_missing_all_missing_unchanged():
    import math
    out = fill_missing([float("nan"), float("nan")])
    assert all(math.isnan(v) for v in out)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        range_mask([800.0], 1200.0, 0.0)   # vmin >= vmax
    with pytest.raises(ValueError):
        step_mask([800.0], -1.0)            # max_step < 0
    with pytest.raises(ValueError):
        stuck_mask([800.0, 800.0], 1)       # max_run < 2
    with pytest.raises(ValueError):
        timestamp_mask([660.0], dt_minutes=0.0)  # 网格间隔非正
# @AI_GENERATED: end