# @AI_GENERATED
"""第 02 章端到端示例：VSG 摇摆方程离散迭代 + 三参数扫描。

运行：python examples/ch02_vsg_trace.py
预期输出与章节 02.5 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.vsg import VSGConfig, q_v_droop, rocof_hz, swing_step

F_N = 50.0


def trace(cfg: VSGConfig, p_e: float, n_steps: int = 30):
    """从额定 ω=1.0 起，按摇摆方程推进 n_steps 拍，返回 ω 轨迹。"""
    omega = 1.0
    out = [omega]
    for _ in range(n_steps):
        omega = swing_step(omega, p_e, cfg)
        out.append(omega)
    return out


def main():
    print("VSG 摇摆方程离散迭代  [主线: 50MW/100MWh 储能电站]")
    print()
    print("J 扫描（D=20 pu 固定）：J 决定初始 RoCoF")
    for J in (4.0, 8.0):
        cfg = VSGConfig(J=J)
        r = rocof_hz(0.6, cfg.p_ref, J, F_N)
        f_ss = F_N * trace(cfg, 0.6)[-1]
        print(f"  J={J:.0f}s  -> 初始 RoCoF = {r:+.3f} Hz/s, 稳态 f = {f_ss:.3f} Hz")
    print("D 扫描（J=4 s 固定）：D 决定稳态频率")
    for D in (20.0, 40.0):
        cfg = VSGConfig(D=D)
        r = rocof_hz(0.6, cfg.p_ref, cfg.J, F_N)
        f_ss = F_N * trace(cfg, 0.6)[-1]
        print(f"  D={D:.0f}pu -> 初始 RoCoF = {r:+.3f} Hz/s, 稳态 f = {f_ss:.3f} Hz")
    print()
    print("Q-V 下垂（V_ref=1.0, k_q=0.05）:")
    qv = VSGConfig()
    print(f"  Q=+0.2pu -> V={q_v_droop(0.2, qv):.3f} pu")
    print(f"  Q=-0.2pu -> V={q_v_droop(-0.2, qv):.3f} pu")

    ok = (
        abs(rocof_hz(0.6, 0.5, 4.0, F_N) + 1.25) < 1e-9
        and abs(q_v_droop(0.2, qv) - 0.99) < 1e-9
        and abs(q_v_droop(-0.2, qv) - 1.01) < 1e-9
    )
    print()
    print("自检通过" if ok else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end