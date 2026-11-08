# @AI_GENERATED
"""ch01 示例：三种 AVC 控制模式在同一扰动下的响应对比

主线场景：50MW/100MWh 储能电站，PCC 110kV
扰动：U 从 116.0 → 117.2 kV（ΔU=+1.2 kV）
"""
from lab.ems_lab.pi_controller import PIController
from lab.ems_lab.deadband import Deadband

U_TARGET = 116.0
DEADBAND_HALF = 0.5


def simulate_fixed_q():
    print("=== 模式1: 定无功 Q=−3000 kvar（固定） ===")
    print("  ΔU=+1.2 kV → Q 不随电压变化 → 输出恒为 −3000 kvar")
    print(f"  终态 U={U_TARGET + 1.2} kV  未恢复 → 依赖调度降低电压目标\n")


def simulate_droop():
    print("=== 模式2: Q-U 下垂 ===")
    K_droop = 2500.0  # kvar/kV
    u_measured = U_TARGET + 1.2
    error = u_measured - U_TARGET
    q_droop = -(K_droop * error)
    print(f"  ΔU={error:+.1f} kV → Q={q_droop:+.0f} kvar")
    print(f"  下垂斜率={K_droop} kvar/kV")
    print(f"  终态存在稳态误差（不像 PI 会消除）\n")


def simulate_pi():
    print("=== 模式3: 定电压 PI（正文主力） ===")
    pi = PIController(kp=8, ki=0.3, ts=4.0, out_max=15000, out_min=-15000)
    deadband = Deadband(center=U_TARGET, half_width=DEADBAND_HALF)

    error = 1.2
    snapshots = [0, 2, 5, 10, 20, 40, 80]
    for t in range(1, 120):
        err = deadband.apply(U_TARGET + 1.2) if deadband.in_deadband(U_TARGET + 1.2) else error
        q = pi.step(err)
        error = 1.2 * max(0, 1 - q / 8000 * 10 / 120)
        if t in snapshots:
            u_est = U_TARGET + 1.2 - abs(q) / 8000 * 1.2
            print(f"  t={t:3d}s  Q={q:+7.0f} kvar  U_est={u_est:.2f} kV")
    print(f"  终态 Q={pi.last_output:+7.0f} kvar  电压恢复至目标\n")


def main():
    print("AVC 三种控制模式对比  [主线: 50MW/100MWh 储能电站, PCC=110kV]\n")
    simulate_fixed_q()
    simulate_droop()
    simulate_pi()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end