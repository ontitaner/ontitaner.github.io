# @AI_GENERATED
"""第 04 章端到端示例：电压源特性与弱电网稳定性。

运行：python examples/ch04_voltage_support.py
预期输出与章节 04.x 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.voltage_support import (  # noqa: E402
    circ_current_pu,
    q_from_voltage,
    share_q,
    voltage_deviation_pu,
)

S_N = 50.0  # MVA 基准


def main():
    print("电压源特性与弱电网稳定性  [主线: 50MW/100MWh 储能电站, SCR≈1.8]")
    print()

    # --- 04.2 电压支撑：Q-V 下垂反读 ---
    print("[04.2] 电压支撑（Q-V 下垂反读）: V_ref=1.0, k_q=0.05")
    for v in (1.00, 0.98):
        q = q_from_voltage(v)
        print(f"  电压 V={v:.2f} pu -> Q = {q:.2f} pu（{q*S_N:g} Mvar）")

    # --- 04.3 弱电网电压-无功敏感度 ---
    dq = 0.2
    dv_weak = voltage_deviation_pu(dq, 1.8)
    dv_strong = voltage_deviation_pu(dq, 3.0)
    print()
    print("[04.3] 弱电网电压-无功敏感度 ΔV ≈ ΔQ·X_g:")
    print(f"  ΔQ={dq:.1f} pu -> 本站 ΔV = {dv_weak:.3f} pu（{dv_weak*100:.1f}%）"
          f" | 强电网 ΔV = {dv_strong:.3f} pu（{dv_strong*100:.1f}%）")
    print(f"  本站电压敏感度是强电网的 {dv_weak/dv_strong:.2f} 倍")

    # --- 04.4 多机均流 ---
    q1, q2 = share_q(0.3, 0.05, 0.10)
    print()
    print("[04.4] 多机均流（k_q 反比分配）:")
    print(f"  k_q1=0.05, k_q2=0.10, 总无功 0.3 pu（15 Mvar）")
    print(f"  -> Q1 = {q1:.2f} pu（{q1*S_N:g} Mvar），Q2 = {q2:.2f} pu（{q2*S_N:g} Mvar）"
          f"，分配比 {q1/q2:.0f}:1")

    # --- 04.5 环流 ---
    ic = circ_current_pu(0.02, 0.1, 0.1)
    print()
    print("[04.5] 环流（幅值差 0.02 pu，设备侧感抗各 0.1 pu）:")
    print(f"  I_circ = 0.02/(0.1+0.1) = {ic:.2f} pu = {ic*S_N:g} Mvar（无功环流对灌）")

    # 与正文手算一致的自检
    ok = (
        abs(q_from_voltage(0.98) - 0.4) < 1e-9
        and abs(dv_weak - 0.1111) < 1e-3
        and abs(dv_strong - 0.0667) < 1e-3
        and abs(q1 - 0.2) < 1e-9
        and abs(q2 - 0.1) < 1e-9
        and abs(ic - 0.1) < 1e-9
    )
    print()
    print("自检通过" if ok else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end