# @AI_GENERATED
"""一致性测试：PI 控制器 — 正文 02 章手算验证"""
from lab.ems_lab.pi_controller import PIController


def test_pi_step_response():
    pi = PIController(kp=8, ki=0.3, ts=4.0)
    assert pi.step(1.2) == 11.04


def test_pi_convergence():
    pi = PIController(kp=8, ki=0.3, ts=4.0, out_max=100, out_min=-100)
    for _ in range(80):
        pi.step(5.0)
    assert pi.last_output == 100.0


def test_pi_anti_windup():
    pi = PIController(kp=8, ki=0.3, ts=4.0, out_max=100, out_min=-100)
    for _ in range(80):
        pi.step(5.0)
    assert pi.integral <= 100.0
    assert pi.last_output == 100.0


def test_pi_reset():
    pi = PIController(kp=8, ki=0.3, ts=4.0)
    pi.step(1.2)
    pi.reset()
    assert pi.integral == 0.0
    assert pi.last_output == 0.0
# @AI_GENERATED: end