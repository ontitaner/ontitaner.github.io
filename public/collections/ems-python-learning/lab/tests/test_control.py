import math

import pytest

from ems_lab.control import (
    Hysteresis,
    LowPassFilter,
    PIController,
    RateLimiter,
    clamp,
    clamp_power,
    deadband_cut,
    deadband_shift,
    interp_table,
    limit_then_ramp,
)


# ---------------- clamp
@pytest.mark.parametrize("x, expected", [(300, 300), (1000, 800), (-700, -500), (-500, -500), (800, 800)])
def test_clamp_power_asymmetric(x, expected):
    # 第 11 章手算：可放 800、可充 500
    assert clamp_power(x, available_charge_kw=500, available_discharge_kw=800) == expected


def test_clamp_rejects_nan_and_empty_domain():
    with pytest.raises(ValueError):
        clamp(math.nan, 0, 1)
    with pytest.raises(ValueError, match="可行域为空"):
        clamp(250, 300, 200)
    with pytest.raises(ValueError):
        clamp_power(100, -1, 100)


def test_python_max_nan_is_order_dependent():
    # 这就是 clamp 必须显式拦截 NaN 的原因
    assert math.isnan(max(math.nan, 1.0))
    assert max(1.0, math.nan) == 1.0


# ---------------- 死区
def test_deadband_two_types():
    assert deadband_cut(0.02, 0.03) == 0.0
    assert deadband_cut(-0.05, 0.03) == -0.05
    assert deadband_shift(0.02, 0.03) == 0.0
    assert deadband_shift(-0.05, 0.03) == pytest.approx(-0.02)
    assert deadband_shift(0.05, 0.03) == pytest.approx(0.02)
    # 边界连续性：连续型在 0.0300001 附近接近 0，截断型直接跳到 0.03
    assert deadband_shift(0.0300001, 0.03) == pytest.approx(0.0, abs=1e-6)
    assert deadband_cut(0.0300001, 0.03) == pytest.approx(0.03, abs=1e-6)


# ---------------- 滞回
def test_hysteresis_soc_self_charge():
    h = Hysteresis(on_below=15, off_above=25)
    seq = [30, 20, 14.9, 18, 24, 25, 25.1, 20]
    out = [h.update(x) for x in seq]
    assert out == [False, False, True, True, True, True, False, False]
    with pytest.raises(ValueError):
        Hysteresis(20, 20)


# ---------------- Ramp
def test_rate_limiter_hand_calc():
    # 第 11 章手算：0 → 1000 kW，限速 100 kW/s，dt=1 s
    r = RateLimiter(up_rate=100, down_rate=100)
    outs = [r.update(1000, 1.0) for _ in range(12)]
    assert outs[0] == 100
    assert outs[9] == 1000
    assert outs[11] == 1000


def test_limit_then_ramp_follows_sudden_derate():
    r = RateLimiter(up_rate=100, down_rate=100, initial=800)
    # BMS 突然把可放能力降到 300：输出必须当周期就降到 300，而不是按 Ramp 慢慢降
    out = limit_then_ramp(800, r, 1.0, available_charge_kw=500, available_discharge_kw=300)
    assert out == 300
    assert r.output == 300  # 状态已同步


# ---------------- 低通
def test_low_pass_time_constant_63_percent():
    f = LowPassFilter(tau_s=1.0)
    f.update(0.0, 0.01)
    y = 0.0
    for _ in range(100):  # 1 秒
        y = f.update(1.0, 0.01)
    assert y == pytest.approx(1 - math.exp(-1), abs=0.01)  # ≈ 63.2%


# ---------------- 插值
def test_interp_temperature_derating():
    temps = [-10, 0, 10, 30, 45, 55]
    ratio = [0.0, 0.3, 1.0, 1.0, 0.5, 0.0]
    assert interp_table(38, temps, ratio) == pytest.approx(1.0 - 0.5 * 8 / 15)
    assert interp_table(60, temps, ratio) == 0.0
    assert interp_table(20, temps, ratio) == 1.0


# ---------------- PI 抗饱和
def _simulate_pi(anti_windup: bool) -> list[float]:
    """被控对象：一阶惯性 y' = (u - y)/τ，τ=2 s。目标 1000，但输出上限 600 持续 20 s 后放开到 1500。"""
    pi = PIController(kp=0.5, ki=0.5, out_min=0, out_max=600, anti_windup=anti_windup)
    y, dt, ys = 0.0, 0.1, []
    for k in range(600):
        if k == 200:
            pi.out_max = 1500
        u = pi.update(1000 - y, dt)
        y += (u - y) / 2.0 * dt
        ys.append(y)
    return ys


def test_pi_anti_windup_reduces_overshoot():
    with_aw = max(_simulate_pi(True))
    without_aw = max(_simulate_pi(False))
    assert with_aw < without_aw
    assert with_aw < 1100  # 抗饱和版本超调很小
def test_ramp_trace_and_reset_11_4():
    """11.4 逐拍追踪：能力突降时输出立即兜底并同步状态。"""
    r = RateLimiter(100, 100, initial=800)
    assert r.update(800, 1.0) == 800
    assert limit_then_ramp(800, r, 1.0, 500, 300) == 300
    assert r.output == 300
    assert limit_then_ramp(800, r, 1.0, 500, 300) == 300


def _ch11_examples():
    """导入 lab/examples/ch11_control_examples.py（各节示例的真实实现版本）。"""
    import importlib.util
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "examples" / "ch11_control_examples.py"
    spec = importlib.util.spec_from_file_location("ch11_control_examples", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_clamp_example_table_11_1():
    """11.1 逐项表：可充 500、可放 800。"""
    rows = _ch11_examples().clamp_example()
    assert rows == [(1000, 800, 200), (-700, -500, -200), (300, 300, 0)]


def test_deadband_example_table_11_2():
    """11.2 逐项表：w=0.03 Hz、K=1000 kW/Hz，截断型/连续型 ΔP。"""
    rows = _ch11_examples().deadband_example()
    assert [(r[1], r[2]) for r in rows] == pytest.approx([(0, 0), (40, 10), (100, 70), (-50, -20)])


def test_hysteresis_example_trace_11_3():
    """11.3 逐拍表：14.8% 开启，25.3% 停止。"""
    assert _ch11_examples().hysteresis_example() == [False, False, True, True, True, True, False, False, False]


def test_low_pass_trace_11_5():
    """11.5 逐拍表：τ=1 s、dt=0.2 s、输入 50→49.9 Hz，第 0～10 拍。"""
    ys = _ch11_examples().lowpass_example()
    assert [round(y, 4) for y in ys] == [50.0, 49.9833, 49.9694, 49.9579, 49.9482, 49.9402,
                                         49.9335, 49.9279, 49.9233, 49.9194, 49.9162]
    done = [round((50.0 - y) / 0.1 * 100, 1) for y in ys]
    assert (done[1], done[5], done[10]) == (16.7, 59.8, 83.8)


def test_interp_example_table_11_6():
    """11.6 逐项表：5/38/50/60 ℃ → 650/733.3/250/0 kW。"""
    rows = _ch11_examples().interp_example()
    assert [round(r[1], 3) for r in rows] == [0.65, 0.733, 0.25, 0.0]
    assert [round(r[2], 1) for r in rows] == [650.0, 733.3, 250.0, 0.0]


def test_pi_example_a_trace_11_7():
    """11.7 示例 A 逐拍表：光伏富余 300 kW，P_PCC 与 u 每拍一致。"""
    rows = _ch11_examples().pi_example([300.0] * 10, u_min=-1000.0)
    assert [round(r[0], 1) for r in rows] == [300.0, 120.0, 108.0, 67.2, 48.5, 32.8, 22.8, 15.7, 10.8, 7.5]
    assert [round(r[1], 1) for r in rows] == [-180.0, -192.0, -232.8, -251.5, -267.2,
                                              -277.2, -284.3, -289.2, -292.5, -294.8]


def test_pi_example_b_antiwindup_11_7():
    """11.7 示例 B 逐拍表：可充 400 kW，第 2～4 拍顶住、积分冻结在 −336，云遮后收敛。"""
    rows = _ch11_examples().pi_example([600.0] * 5 + [100.0] * 7, u_min=-400.0)
    assert [round(r[0], 1) for r in rows] == [600.0, 240.0, 216.0, 200.0, 200.0, -300.0,
                                              -56.0, -82.4, -44.2, -34.1, -22.5, -15.8]
    assert [round(r[1], 1) for r in rows] == [-360.0, -384.0, -400.0, -400.0, -400.0, -156.0,
                                              -182.4, -144.2, -134.1, -122.5, -115.8, -110.8]
    assert [round(r[2], 1) for r in rows[1:5]] == [-336.0] * 4
    assert [r[3] for r in rows] == [False, False, True, True, True] + [False] * 7


def test_mode_machine_trace_11_8():
    """11.8 逐秒表：降额恢复需连续 3 s；故障需人工复归。"""
    rows = _ch11_examples().state_machine_example()
    assert [(s, o) for s, o, _ in rows] == [("待机", 0), ("运行", 500), ("降额", 300), ("降额", 500),
                                            ("降额", 500), ("运行", 500), ("故障", 0), ("故障", 0),
                                            ("待机", 0), ("运行", 500)]
    assert [why for _, _, why in rows][3:6] == ["能力恢复计时 1 s", "能力恢复计时 2 s", "能力恢复已持续 3 s"]
    assert rows[7][2] == "未复归，拒绝指令"


def test_mode_machine_fault_has_priority():
    """任一状态下保护动作都直接进入故障，且未复归前一直拒绝指令。"""
    m = _ch11_examples().ModeMachine(hold_s=3.0, initial="降额")
    assert m.update(500, 1000, fault=True, ack=False) == 0 and m.state == "故障"
    assert m.update(500, 1000, fault=False, ack=False) == 0 and m.state == "故障"
    assert m.update(500, 1000, fault=False, ack=True) == 0 and m.state == "待机"


@pytest.mark.parametrize("k, cap, expected_out, expected_delta", [
    (1, 1000, 0, 200), (2, 1000, 200, 200), (3, 1000, 400, 200), (4, 100, 100, -300),
    (5, 1000, 300, 200), (6, 1000, 500, 200), (7, 1000, 600, 100), (8, 1000, 600, 0),
])
def test_ramp_example_table_11_4(k, cap, expected_out, expected_delta):
    """11.4 示例逐拍表：−200 → +600 kW，200 kW/s，第 4 拍 BMS 降额到 100 kW。"""
    caps = [1000, 1000, 1000, 100, 1000, 1000, 1000, 1000]
    r = RateLimiter(200, 200, initial=-200)
    prev = out = -200.0
    for i in range(k):
        prev = r.output
        out = limit_then_ramp(600, r, 1.0, 1000, caps[i])
    assert caps[k - 1] == cap
    assert out == pytest.approx(expected_out)
    assert out - prev == pytest.approx(expected_delta)


def test_ch11_ramp_example_script():
    """lab/examples/ch11_ramp_example.py 可运行且自检通过。"""
    import runpy
    from pathlib import Path
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples" / "ch11_ramp_example.py"),
                   run_name="__main__")


def test_ch11_control_examples_script():
    """lab/examples/ch11_control_examples.py 可运行且自检通过。"""
    import runpy
    from pathlib import Path
    script = Path(__file__).resolve().parents[1] / "examples" / "ch11_control_examples.py"
    runpy.run_path(str(script), run_name="__main__")

