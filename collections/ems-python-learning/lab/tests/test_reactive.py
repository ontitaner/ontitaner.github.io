import math

import pytest

from ems_lab.reactive import (
    AvcController,
    QuDroopConfig,
    naive_clamp_each,
    pf_signed,
    project_pq,
    q_for_voltage_change_kvar,
    q_from_pf,
    qu_droop_kvar,
    voltage_deviation_pct,
    voltage_rise_v,
)

# 17.2 手算：110 kV 线路 50 km，R=6.5 Ω、X=20 Ω [教学示例]
R, X, U = 6.5, 20.0, 110.0


def test_voltage_rise_hand_calc():
    assert voltage_rise_v(50_000, 0, R, X, U) == pytest.approx(2954.5, abs=0.1)
    assert voltage_rise_v(0, 20_000, R, X, U) == pytest.approx(3636.4, abs=0.1)
    total = voltage_rise_v(50_000, 20_000, R, X, U)
    assert total == pytest.approx(6590.9, abs=0.1)
    assert total / (U * 1000) * 100 == pytest.approx(6.0, abs=0.05)


def test_q_is_more_effective_than_p_on_high_voltage_line():
    dp = voltage_rise_v(10_000, 0, R, X, U)  # 多送 10 MW
    dq = voltage_rise_v(0, 10_000, R, X, U)  # 多发 10 Mvar
    assert dp == pytest.approx(590.9, abs=0.1)
    assert dq == pytest.approx(1818.2, abs=0.1)
    assert dq / dp == pytest.approx(X / R)


def test_low_voltage_cable_p_dominates():
    # 低压电缆 R/X≈3：有功对电压的影响反而更大
    assert voltage_rise_v(100, 0, 0.03, 0.01, 0.4) > voltage_rise_v(0, 100, 0.03, 0.01, 0.4)


def test_q_for_voltage_change():
    # 想抬高 1 kV：ΔQ ≈ 1000 × 110 / 20 = 5500 kvar
    assert q_for_voltage_change_kvar(1000, X, U) == pytest.approx(5500)


def test_voltage_deviation_pct():
    assert voltage_deviation_pct(10.7, 10.0) == pytest.approx(7.0)
    assert voltage_deviation_pct(9.3, 10.0) == pytest.approx(-7.0)


def test_q_from_pf_hand_calc():
    # P=800 kW、PF=0.95、发出 → Q ≈ 262.9 kvar
    assert q_from_pf(800, 0.95, +1) == pytest.approx(262.9, abs=0.1)
    assert q_from_pf(-800, 0.95, -1) == pytest.approx(-262.9, abs=0.1)  # 充电时 |P| 参与计算
    assert q_from_pf(800, 1.0, +1) == pytest.approx(0)
    with pytest.raises(ValueError):
        q_from_pf(800, 0.0, +1)
    with pytest.raises(ValueError):
        q_from_pf(800, 0.95, 0)


def test_pf_signed_keeps_direction():
    assert pf_signed(800, 600) == (pytest.approx(0.8), "发出")
    assert pf_signed(800, -600) == (pytest.approx(0.8), "吸收")


def test_qu_droop_hand_calc():
    cfg = QuDroopConfig(q_max_kvar=500, slope_kvar_per_pu=10_000, deadband_pu=0.01)
    assert qu_droop_kvar(1.005, cfg) == 0.0  # 死区内
    assert qu_droop_kvar(0.97, cfg) == pytest.approx(200)  # (0.03−0.01)×10000
    assert qu_droop_kvar(0.93, cfg) == pytest.approx(500)  # 600 → 限幅 500
    assert qu_droop_kvar(1.04, cfg) == pytest.approx(-300)  # 电压高 → 吸收
    cut = QuDroopConfig(q_max_kvar=500, slope_kvar_per_pu=10_000, deadband_pu=0.01, deadband_mode="cut")
    assert qu_droop_kvar(0.97, cut) == pytest.approx(300)


# ---------------------------------------------------------------- 17.8 手算：S=1000，请求 (900, 600)
def test_naive_clamp_overloads():
    p, q = naive_clamp_each(900, 600, 1000)
    assert math.hypot(p, q) == pytest.approx(1081.7, abs=0.1)  # 超容 8.2%


def test_project_p_priority():
    r = project_pq(900, 600, 1000, "p_priority")
    assert (r.p_kw, r.q_kvar) == (pytest.approx(900), pytest.approx(435.9, abs=0.1))
    assert r.q_unserved_kvar == pytest.approx(164.1, abs=0.1)
    assert r.limited and "有功优先" in r.reasons[0]


def test_project_q_priority():
    r = project_pq(900, 600, 1000, "q_priority")
    assert (r.p_kw, r.q_kvar) == (pytest.approx(800), pytest.approx(600))
    assert r.p_unserved_kw == pytest.approx(100)


def test_project_proportional_keeps_pf():
    r = project_pq(900, 600, 1000, "proportional")
    assert r.p_kw == pytest.approx(832.05, abs=0.01)
    assert r.q_kvar == pytest.approx(554.70, abs=0.01)
    assert r.q_kvar / r.p_kw == pytest.approx(600 / 900)


@pytest.mark.parametrize("mode", ["p_priority", "q_priority", "proportional"])
@pytest.mark.parametrize("p,q", [(900, 600), (-900, 600), (900, -600), (-900, -600), (1200, 0), (0, -1500)])
def test_projection_always_inside_circle(mode, p, q):
    r = project_pq(p, q, 1000, mode)
    assert math.hypot(r.p_kw, r.q_kvar) <= 1000 + 1e-6
    assert r.p_kw * p >= 0 and r.q_kvar * q >= 0  # 不改变方向
    assert r.p_kw + r.p_unserved_kw == pytest.approx(p) and r.q_kvar + r.q_unserved_kvar == pytest.approx(q)


def test_projection_inside_circle_untouched():
    r = project_pq(600, 300, 1000)
    assert (r.p_kw, r.q_kvar, r.limited) == (600, 300, False)


def test_box_limit_before_circle():
    # BMS 只允许放 700 kW：先截到 700，此时 (700, 600) 在圆内，Q 不必压缩
    r = project_pq(900, 600, 1000, "p_priority", p_discharge_max_kw=700)
    assert (r.p_kw, r.q_kvar) == (700, 600)
    assert r.reasons == ["有功超出充/放上限"]

def test_avc_controller_freezes_integral_and_data_invalid():
    """17.5：过压时 Q 顶住能力边界冻结积分；数据无效时不产生新请求。"""
    c = AvcController(u_target_pu=1.0, kp_kvar_per_pu=12_000, ki_kvar_per_pu_s=4_000)
    step0 = c.update(1.03, 1.0, -435.9, 435.9)
    assert step0.q_requested_kvar == pytest.approx(-435.9)
    assert step0.saturated and c.integral_kvar == pytest.approx(0)
    step1 = c.update(1.0126, 1.0, -435.9, 435.9)
    assert step1.q_requested_kvar == pytest.approx(-201.6)
    assert not step1.saturated and c.integral_kvar == pytest.approx(-50.4)
    invalid = c.update(None, 1.0, -435.9, 435.9, valid=False)
    assert (invalid.q_requested_kvar, invalid.enabled, c.integral_kvar) == (0.0, False, pytest.approx(-50.4))


def test_ch17_avc_examples_script():
    """17 章最小闭环：电压灵敏度、Q-U、P-Q 投影与 AVC PI 均可运行。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch17_avc_examples.py"
    runpy.run_path(str(script), run_name="__main__")




def test_self_check_17():
    assert voltage_rise_v(40_000, 10_000, 5, 25, 110) == pytest.approx(4090.9, abs=0.1)
    assert voltage_deviation_pct(9.25, 10) == pytest.approx(-7.5)
    assert q_from_pf(600, 0.9, -1) == pytest.approx(-290.6, abs=0.1)
    cfg = QuDroopConfig(q_max_kvar=800, slope_kvar_per_pu=20_000, deadband_pu=0.02)
    assert qu_droop_kvar(0.95, cfg) == pytest.approx(600)
    assert qu_droop_kvar(1.03, cfg) == pytest.approx(-200)
    assert qu_droop_kvar(0.90, cfg) == pytest.approx(800)
    assert project_pq(400, 400, 500, "p_priority").q_kvar == pytest.approx(300)
    assert project_pq(400, 400, 500, "q_priority").p_kw == pytest.approx(300)
    assert project_pq(400, 400, 500, "proportional").p_kw == pytest.approx(353.55, abs=0.01)


def test_ch17_avc_trace_example():
    """旧的 Q-U 下垂最小闭环仍可运行。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch17_avc_trace.py"
    runpy.run_path(str(script), run_name="__main__")

def test_ch17_modes_examples_script():
    """17章单位与四模式对照示例可运行并通过内置断言。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch17_modes_examples.py"
    runpy.run_path(str(script), run_name="__main__")
