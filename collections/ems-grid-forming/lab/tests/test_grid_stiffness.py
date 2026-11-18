# @AI_GENERATED
"""一致性测试：电网强弱与相位偏移 — 正文 01.5 手算验证（pu 体系）

对齐 01.5 手算：
  SCR=1.8 → Z_g≈0.556 pu → Δθ(0.2 pu)≈0.111 rad≈6.4°
  SCR=3.0 → Z_g≈0.333 pu → Δθ(0.2 pu)≈0.067 rad≈3.8°
  比值 ≈ 1.67
"""
import pytest

from ems_lab.grid_stiffness import grid_category, phase_offset_deg, phase_offset_rad, z_grid


def test_z_grid_weak():
    assert z_grid(1.8) == pytest.approx(0.5556, rel=1e-3)


def test_z_grid_strong():
    assert z_grid(3.0) == pytest.approx(0.3333, rel=1e-3)


def test_phase_offset_rad_weak():
    # 01.5：0.2 × 0.556 ≈ 0.111 rad
    assert phase_offset_rad(0.2, 1.8) == pytest.approx(0.1111, rel=1e-3)


def test_phase_offset_deg_weak():
    # 01.5：0.111 rad ≈ 6.4°
    assert phase_offset_deg(0.2, 1.8) == pytest.approx(6.366, abs=0.05)


def test_phase_offset_deg_strong():
    # 01.5：0.067 rad ≈ 3.8°
    assert phase_offset_deg(0.2, 3.0) == pytest.approx(3.82, abs=0.05)


def test_ratio_weak_to_strong():
    # 01.5：0.556 / 0.333 ≈ 1.67 倍
    ratio = z_grid(1.8) / z_grid(3.0)
    assert ratio == pytest.approx(1.6667, rel=1e-3)


def test_grid_category_boundaries():
    # 01.5 判定口径表：>=3 强，[2,3) 弱，<2 极弱
    assert grid_category(1.8) == "极弱电网"
    assert grid_category(2.0) == "弱电网"
    assert grid_category(2.5) == "弱电网"
    assert grid_category(3.0) == "强电网"


def test_z_grid_invalid():
    with pytest.raises(ValueError):
        z_grid(0.0)
    with pytest.raises(ValueError):
        z_grid(-1.0)
# @AI_GENERATED: end