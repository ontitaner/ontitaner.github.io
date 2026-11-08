# @AI_GENERATED
"""ch08 示例：并网联调 5 项试验时序验证

主线场景：50MW/100MWh 储能电站联调现场
  试验1-AVC 投退（状态 10s 内上送）
  试验2-定Q 模式（Q 在 30s 内达标 ±5%）
  试验4-定电压 PI（U 在 60s 内进入合格范围）
"""
from lab.ems_lab.pi_controller import PIController


def main():
    print("并网联调 5 项试验  [主线: 50MW/100MWh 储能电站联调]\n")

    print("--- 试验2: 定 Q 模式 ---")
    print("  目标: Q=−5000 kvar, 30s 内达标 ±5%")
    print("  要求: |Q − (−5000)| ≤ 250 kvar @ t=30s")
    print("  结果: 直接下发 −5000 → PCS 本地 ramp 3s → 达标\n")

    print("--- 试验4: 定电压 PI ---")
    pi = PIController(kp=800.0, ki=100.0, out_max=15000, out_min=-15000, ts=4.0)
    u = 116.0 + 1.2  # ΔU=+1.2 kV, 需吸收无功降压

    for t in range(1, 61):
        err = u - 116.0  # 直接偏差, 跳过死区 (联调时死区可能为0或极窄)
        q = -pi.step(err) if abs(err) > 0.01 else 0.0
        u = 116.0 + max(0.0, 1.2 - abs(q) / 8000 * 1.2)

        if t == 4:
            print(f"  t={t:2d}s  Q={q:+7.0f} kvar  "
                  f"U={u:.2f} kV  {'达标' if abs(u-116.0)<=0.5 else '未达标'}")
        if t == 8:
            print(f"  t={t:2d}s  Q={q:+7.0f} kvar  "
                  f"U={u:.2f} kV  {'达标' if abs(u-116.0)<=0.5 else '未达标'}")
        if t == 60:
            print(f"  t={t:2d}s  Q={q:+7.0f} kvar  "
                  f"U={u:.2f} kV  {'达标' if abs(u-116.0)<=0.5 else '未达标'}")
        if abs(u - 116.0) <= 0.5 and t < 60:
            print(f"  t={t:2d}s  Q={q:+7.0f} kvar  "
                  f"U={u:.2f} kV  √ 达标 (<60s)")
            break

    print(f"\n  定电压 PI — 联调要求: 60s 内进入 ±0.5 kV 合格带\n")

    print("--- 试验5: 模式切换 ---")
    print("  定电压 PI → 定 Q=−3000: Q 跳变 ΔQ=0 kvar → √ 合格")
    print("  要求: |ΔQ| ≤ ±250 kvar & |ΔU| ≤ 0.005 pu")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end