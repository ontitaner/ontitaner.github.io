"""第 06 章手算例子的测试。PCS 参数均为 [教学示例]。"""
import pytest

from ems_lab.pcs import (
    PcsRating,
    allocate_pq,
    apparent_from_current_kva,
    apply_pcs_limits,
    available_apparent_kva,
    current_from_apparent_a,
    dc_limited_power_kw,
    decode_bits,
    pq_boundary,
    temperature_derate_ratio,
)

# 06 章示例 PCS：1000 kVA、交流 690 V、放电上限 1000 kW、充电上限 750 kW
RATING = PcsRating(s_rated_kva=1000, u_rated_v=690, p_discharge_max_kw=1000, p_charge_max_kw=750)


def test_rated_current_and_four_quadrant_current():
    # 1000 kVA / 690 V → 额定电流约 836.7 A
    assert current_from_apparent_a(1000, 690) == pytest.approx(836.7, abs=0.1)
    # 6.4 手算：P=800、Q=600 → S=1000 kVA，电流同样是 836.7 A
    assert apparent_from_current_kva(690, RATING.rated_current_a) == pytest.approx(1000)


def test_voltage_low_reduces_capacity():
    # 电压跌到 0.9 pu（621 V），电流顶在 836.7 A → 只剩 900 kVA
    assert available_apparent_kva(RATING, 621, 25) == pytest.approx(900)
    # 电压偏高时电流没到上限，但不能超过铭牌 1000 kVA
    assert available_apparent_kva(RATING, 720, 25) == pytest.approx(1000)


def test_current_margin_keeps_capacity():
    # 有 10% 电流裕量的 PCS：0.9 pu 时 min(1000, 990) = 990 kVA
    r = PcsRating(s_rated_kva=1000, u_rated_v=690, i_max_a=1.1 * RATING.rated_current_a)
    assert available_apparent_kva(r, 621, 25) == pytest.approx(990)


def test_temperature_derate():
    assert temperature_derate_ratio(RATING, 40) == pytest.approx(1.0)
    assert temperature_derate_ratio(RATING, 50) == pytest.approx(0.9)
    assert temperature_derate_ratio(RATING, 60) == pytest.approx(0.0)
    # 0.9 pu 电压 + 50 °C → 1000 × 0.9 × 0.9 = 810 kVA
    assert available_apparent_kva(RATING, 621, 50) == pytest.approx(810)
    assert available_apparent_kva(RATING, 690, 50) == pytest.approx(900)


def test_dc_voltage_limits_discharge():
    # 直流电流上限 1200 A：电池 750 V 时只能 900 kW；850 V 时 1020 kW（再被 1000 kW 截断）
    assert dc_limited_power_kw(750, 1200) == pytest.approx(900)
    assert dc_limited_power_kw(850, 1200) == pytest.approx(1020)


def test_p_priority_compresses_q():
    # 810 kVA 可用，EMS 要 P=800、Q=300：有功优先 → Q 只剩 √(810²−800²) ≈ 126.9
    r = allocate_pq(800, 300, 810, priority="P")
    assert r.p_kw == pytest.approx(800)
    assert r.q_kvar == pytest.approx(126.9, abs=0.1)
    assert r.q_unserved_kvar == pytest.approx(173.1, abs=0.1)
    assert any("有功优先" in s for s in r.reasons)


def test_q_priority_compresses_p():
    r = allocate_pq(800, 300, 810, priority="Q")
    assert r.q_kvar == pytest.approx(300)
    assert r.p_kw == pytest.approx(752.4, abs=0.1)
    assert r.p_unserved_kw == pytest.approx(47.6, abs=0.1)


def test_q_after_p_textbook_345():
    # 900 kVA，P=540 → Q 最多 720（3-4-5 勾股数）
    r = allocate_pq(540, 800, 900)
    assert r.q_kvar == pytest.approx(720)


def test_charge_asymmetry():
    # 要求充电 900 kW，充电上限 750 kW → 实际 −750
    r = allocate_pq(-900, 0, 1000, p_charge_max_kw=750, p_discharge_max_kw=1000)
    assert r.p_kw == pytest.approx(-750)
    assert r.p_unserved_kw == pytest.approx(-150)
    # 同样幅值的放电不受影响
    assert allocate_pq(900, 0, 1000, 750, 1000).p_kw == pytest.approx(900)


def test_apply_pcs_limits_correct_and_reject():
    r = apply_pcs_limits(800, 300, RATING, u_line_v=621, temp_c=50)
    assert r.p_kw == pytest.approx(800)
    assert r.q_kvar == pytest.approx(126.9, abs=0.1)
    assert "810" in r.reasons[0]
    rej = apply_pcs_limits(500, 0, RATING, 690, 25, running=False)
    assert (rej.p_kw, rej.q_kvar, rej.p_unserved_kw) == (0.0, 0.0, 500)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        allocate_pq(100, 0, 100, priority="X")
    with pytest.raises(ValueError):
        allocate_pq(100, 0, 100, p_charge_max_kw=-1)


def test_pq_boundary_inside_circle_and_charge_limit():
    ps, qs = pq_boundary(900, p_charge_max_kw=750, p_discharge_max_kw=1000)
    assert min(ps) == pytest.approx(-750)
    assert max(ps) == pytest.approx(900)
    assert all(p * p + q * q <= 900**2 + 1e-6 for p, q in zip(ps, qs))


def test_step_up_reduces_current():
    # 6.10 手算：1 MW 在 690 V 约 837 A，升到 35 kV 约 16.5 A
    assert current_from_apparent_a(1000, 690) == pytest.approx(837, abs=0.5)
    assert current_from_apparent_a(1000, 35_000) == pytest.approx(16.5, abs=0.05)


def test_quiz_500kva_400v():
    # 6.15 自测 3：500 kVA / 400 V，电压 360 V → 450 kVA；降额 0.8 → 360 kVA
    r = PcsRating(s_rated_kva=500, u_rated_v=400, derate_temp_c=(40, 50), derate_ratio=(1.0, 0.8))
    assert r.rated_current_a == pytest.approx(721.7, abs=0.1)
    assert available_apparent_kva(r, 360, 25) == pytest.approx(450)
    assert available_apparent_kva(r, 360, 50) == pytest.approx(360)


def test_decode_bits():
    names = {0: "运行", 1: "并网", 3: "降额"}
    assert decode_bits(0b1011, names) == ["运行", "并网", "降额"]
    assert decode_bits(0b10000, names) == ["未定义位 bit4"]
    assert decode_bits(0, names) == []
def test_ch06_minimal_example():
    """06 章最小闭环：能力计算 → P-Q 投影 → 输出未满足量。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch06_pcs_projection.py"
    runpy.run_path(str(script), run_name="__main__")

