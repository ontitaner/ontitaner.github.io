# @AI_GENERATED
"""第 03 章端到端示例：惯量支撑折算 + 一次调频融合（D↔δ 与死区对比）。

运行：python examples/ch03_inertia_trace.py
预期输出与章节 03.x 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.inertia import (  # noqa: E402
    D_to_droop_pct,
    droop_to_D,
    gridforming_delta_p_pu,
    inertia_power_pu,
    pfr_delta_p_pu,
    support_duration_h,
    system_inertia_s,
    system_rocof_hz,
)

F_N = 50.0
DP_PU = 0.1  # 系统功率缺口 0.1 pu = 5 MW（02 统一参数）


def main():
    print("惯量支撑与一次调频融合  [主线: 50MW/100MWh 储能电站, SCR≈1.8]")
    print()

    # --- 03.2 惯量折算：RoCoF 反比于等效惯量 ---
    j0 = system_inertia_s(DP_PU, 0.75, F_N)       # 系统原等效惯量（00.1: RoCoF=0.75）
    j_eq = 3.0 * j0                                # 本站虚拟惯量叠加后总惯量 3 倍
    r_new = system_rocof_hz(DP_PU, j_eq, F_N)      # 新 RoCoF
    j_vsg = j_eq - j0                              # 本站虚拟惯量贡献
    print(f"[03.2] 系统原等效惯量 J0 = {j0:.3f} s  ->  RoCoF = 0.750 Hz/s")
    print(f"[03.2] 叠加虚拟惯量后 J_eq = {j_eq:.1f} s（3 倍） ->  RoCoF = {r_new:.3f} Hz/s")
    print(f"[03.2] 本站需提供虚拟惯量 J_vsg = {j_vsg:.3f} s")

    # --- 03.3 惯量支撑功率分摊 ---
    p_sys = inertia_power_pu(j0, r_new, F_N)       # 系统自身惯量顶的功率
    p_vsg = inertia_power_pu(j_vsg, r_new, F_N)    # 本站惯量顶的功率
    print(f"[03.3] 惯量功率分摊（RoCoF={r_new:.3f} Hz/s）：系统 {p_sys*50:.2f} MW + "
          f"本站 {p_vsg*50:.2f} MW = {(p_sys+p_vsg)*50:.2f} MW")
    print(f"[03.3] 惯量支撑能量（{p_vsg*50:.2f} MW x 4 s）= {p_vsg*50*4/3.6:.2f} kWh "
          f"（100 MWh 的 {p_vsg*50*4/3.6/100000*100:.4f}%）")

    # --- 03.3 SOC 可持续时间 ---
    t = support_duration_h(20_000.0, 5_000.0)      # 20 MWh / 5 MW
    print(f"[03.3] SOC 剩 20 MWh、持续支撑 5 MW -> 可持续 {t:.1f} h")

    # --- 03.4 一次调频融合：D↔δ 与死区对比 ---
    D = droop_to_D(3.0)                            # δ=3% -> D
    print()
    print(f"[03.4] 调差率 δ=3% -> D = {D:.3f} pu")
    print(f"[03.4] 反查：D=20 -> δ={D_to_droop_pct(20.0):.1f}%，D=40 -> δ={D_to_droop_pct(40.0):.1f}%")

    print("[03.4] 死区对比（D=33.333 pu，Δf 为频率跌落，增发为正）:")
    for df in (-0.04, -0.60):
        g = gridforming_delta_p_pu(df, D, F_N)
        p = pfr_delta_p_pu(df, D, 0.06, F_N)
        print(f"  Δf={df:+.2f} Hz -> 构网型 {g*50:+5.2f} MW | 传统(死区) {p*50:+5.2f} MW")

    # 与正文手算一致的自检
    ok = (
        abs(j0 - 6.667) < 1e-3
        and abs(r_new - 0.25) < 1e-9
        and abs(j_vsg - 13.333) < 1e-3
        and abs(p_vsg * 50 - 3.333) < 1e-3
        and abs(droop_to_D(3.0) - 33.333) < 1e-3
        and abs(gridforming_delta_p_pu(-0.6, D, F_N) * 50 - 20.0) < 1e-9
        and abs(pfr_delta_p_pu(-0.6, D, 0.06, F_N) * 50 - 18.0) < 1e-9
    )
    print()
    print("自检通过" if ok else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end