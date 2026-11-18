# @AI_GENERATED
"""一致性测试：PI 控制器 — 正文 01.6/02.4 手算验证（pu 体系）

教学参数（附录 B）：Kp=8000 kvar/pu, Ki=2000 kvar/(pu·s), Ts=4s,
Q_max=±500 kvar, I_max=±300 kvar。
error = U_target − U_pcc（电压偏高为负）。
"""
from lab.ems_lab.pi_controller import PIController


def make_pi():
    return PIController(kp=8000, ki=2000, ts=4.0,
                        out_max=500, out_min=-500, i_max=300)


def test_pi_step_t0_clamped():
    # 01.6 t0：U=1.035 → error=−0.035，P+I=−560 → 输出被限幅到 −500
    pi = make_pi()
    assert pi.step(-0.035) == -500.0
    assert pi.integral == -280.0


def test_pi_step_t1_saturation():
    # 01.6 t1：U=1.008 → error=−0.008，I 累加到 −344 后被限幅到 −300，Q=−364
    pi = make_pi()
    pi.step(-0.035)  # t0：I=−280
    assert pi.step(-0.008) == -364.0
    assert pi.integral == -300.0


def test_pi_step_t2_steady():
    # 01.6 t2：U 仍 1.008，I 停驻 −300，Q 稳定 −364
    pi = make_pi()
    pi.step(-0.035)
    pi.step(-0.008)
    assert pi.step(-0.008) == -364.0
    assert pi.integral == -300.0


def test_pi_anti_windup():
    # 持续大偏差：积分不应越过 i_max，输出不应越过 out_max
    pi = make_pi()
    for _ in range(80):
        pi.step(-0.05)
    assert pi.integral <= 300.0
    assert pi.last_output == -500.0


def test_pi_reset():
    pi = make_pi()
    pi.step(-0.035)
    pi.reset()
    assert pi.integral == 0.0
    assert pi.last_output == 0.0
# @AI_GENERATED: end