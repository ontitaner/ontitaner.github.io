# @AI_GENERATED
"""ch01 示例：四种 AVC 控制模式在同一过压场景下的 Q 请求对比（pu 体系）

主线场景：50MW/100MWh 储能电站，PCC 110 kV（教学示例按附录 B 取标幺值）
输入（对齐 01.2 表格）：
  t0: U=1.035 pu, P=800 kW
  t1: U=1.008 pu, P=400 kW
  t2: U=1.008 pu, P=400 kW
参数：PF=0.95（吸收），K=10000 kvar/pu，死区 ±0.01 pu，
      Kp=8000 kvar/pu, Ki=2000 kvar/(pu·s), Ts=4s, Q_max=±500 kvar, I_max=±300 kvar。
"""
import math

from lab.ems_lab.pi_controller import PIController
from lab.ems_lab.deadband import Deadband

U_REF = 1.000
U_TARGET = 1.000
DB_HALF = 0.01
K_DROOP = 10000.0
Q_MAX = 500.0
Q_SETPOINT = -300.0
PF_TARGET = 0.95
DIRECTION = -1  # 吸收（感性）

# 场景输入
SCENE = [
    ("t0", 1.035, 800),
    ("t1", 1.008, 400),
    ("t2", 1.008, 400),
]


def fixed_q(q_setpoint: float) -> float:
    return q_setpoint


def fixed_pf(p_kw: float) -> float:
    # 与正文 01.4 一致：tan(arccos(0.95)) 取 4 位小数 = 0.3287
    tan_phi = round(math.tan(math.acos(PF_TARGET)), 4)
    return DIRECTION * abs(p_kw) * tan_phi


def q_u_droop(u_pcc_pu: float) -> float:
    deadband = Deadband(center=U_REF, half_width=DB_HALF)
    delta_u_db = deadband.apply(u_pcc_pu)
    q = -K_DROOP * delta_u_db
    return max(-Q_MAX, min(Q_MAX, q))


def voltage_pi(u_series: list[float]) -> list[float]:
    pi = PIController(kp=8000, ki=2000, ts=4.0,
                      out_max=500, out_min=-500, i_max=300)
    outputs = []
    for u_pcc in u_series:
        error = U_TARGET - u_pcc  # 电压偏高为负
        outputs.append(pi.step(error))
    return outputs


def main():
    print("AVC 四种控制模式对比  [主线: 50MW/100MWh 储能电站, PCC=110kV]\n")

    u_series = [u for _, u, _ in SCENE]
    pi_outputs = voltage_pi(u_series)

    print(f"{'时刻':<6}{'U(pu)':>8}{'P(kW)':>8}{'定Q':>9}{'定PF':>9}{'下垂':>9}{'定电压PI':>11}")
    for i, (tag, u, p) in enumerate(SCENE):
        q_fixed = fixed_q(Q_SETPOINT)
        q_pf = fixed_pf(p)
        q_droop = q_u_droop(u)
        q_pi = pi_outputs[i]
        print(f"{tag:<6}{u:>8.3f}{p:>8d}{q_fixed:>9.0f}{q_pf:>9.1f}"
              f"{q_droop:>9.0f}{q_pi:>11.0f}")

    print("\n关键观察：")
    print("  t0（U=1.035 过压）→ 定Q=−300、定PF=−263.0、下垂=−250、PI=−500（被限幅）")
    print("  t1/t2（U=1.008 落死区）→ 下垂=0（只看此刻），PI=−364（I 记住历史偏差）")
    print("  差异根源：定Q看设点，定PF看当前P，下垂看当前U，PI看 U+历史积分。")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end