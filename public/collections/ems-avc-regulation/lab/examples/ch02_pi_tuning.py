# @AI_GENERATED
"""ch02 示例：PI 参数敏感度扫参 —— Kp×Ki 网格下的收敛行为

主线场景：50MW/100MWh 储能电站，阶跃 ΔU=+1.2 kV, 死区 ±0.5 kV
正文默认 Kp=8, Ki=0.3
"""
from lab.ems_lab.pi_controller import PIController
from lab.ems_lab.deadband import Deadband

U_TARGET = 116.0
DEADBAND_HALF = 0.5


def run_pi(kp, ki, steps=200):
    pi = PIController(kp=kp, ki=ki, ts=4.0, out_max=15000, out_min=-15000)
    deadband = Deadband(center=U_TARGET, half_width=DEADBAND_HALF)
    u = U_TARGET + 1.2
    history = []
    for _ in range(steps):
        err = deadband.apply(u)
        q = pi.step(err)
        history.append((u, q))
        if abs(err) < 0.01:
            break
        u = U_TARGET + 1.2 - abs(q) / 8000 * 1.2
        u = max(u, U_TARGET - 0.3)
    return history


def main():
    params = [(3, 0.1, "欠阻尼"), (8, 0.3, "正文默认"), (15, 0.6, "偏激进")]
    print(f"PI 参数敏感度扫参  [主线: 50MW, PCC=110kV, ΔU=+1.2kV]\n")

    for kp, ki, label in params:
        hist = run_pi(kp, ki)
        final_u = hist[-1][0]
        final_q = hist[-1][1]
        converge_steps = len(hist)
        print(f"  Kp={kp:2d}, Ki={ki:.1f} [{label:6s}]: "
              f"收敛{converge_steps:3d}拍, U_final={final_u:.3f}, Q_final={final_q:+7.0f}")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end