# @AI_GENERATED
"""第 05 章端到端示例：并离网切换与黑启动。

运行：python examples/ch05_switch_blackstart.py
预期输出与章节 05.x 手算完全一致（自检通过）。
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.grid_switch import (  # noqa: E402
    amplitude_threshold_pu,
    inrush_from_amplitude,
    inrush_from_phase,
    max_load_step_pu,
    phase_threshold_rad,
    pre_sync_time,
    unload_time,
    voltage_drop_pu,
)


def main():
    print("并离网切换与黑启动  [主线: 50MW/100MWh 储能电站, SCR≈1.8]")
    print()

    # --- 05.2 冲击电流边界 ---
    print("[05.2] 冲击电流边界（I = ΔU/X_s, X_s=0.1 pu）:")
    i_amp = inrush_from_amplitude(0.02)
    i_ph = inrush_from_phase(0.1)
    print(f"  幅值差 0.02 pu -> I = {i_amp:.2f} pu（{i_amp*100:.0f}%，越限）")
    print(f"  相位差 0.10 rad -> I = {i_ph:.2f} pu（{i_ph*100:.0f}%，越限）")

    # --- 05.3 预同步阈值 ---
    dv_max = amplitude_threshold_pu()
    dt_max = phase_threshold_rad()
    i_ok = inrush_from_phase(dt_max)
    print()
    print("[05.3] 预同步阈值（I_max=0.1 pu）:")
    print(f"  幅值差阈值 ΔV_max = {dv_max:.2f} pu（{dv_max*100:.0f}%）")
    print(f"  相位差阈值 Δθ_max = {dt_max:.3f} rad（{math.degrees(dt_max):.2f}°）")
    print(f"  预同步达标 Δθ={dt_max:.2f} rad -> I = {i_ok:.2f} pu（{i_ok*100:.0f}%，合格）")

    # --- 05.4 无缝切换时序 ---
    t_sync = pre_sync_time(0.1, 0.05)
    t_unload = unload_time(0.2)
    print()
    print("[05.4] 无缝切换时序:")
    print(f"  预同步追赶（Δθ0=0.1 rad, Δf=0.05 Hz）-> t = {t_sync:.3f} s")
    print(f"  解列功率回零（P=0.2 pu, 爬坡 0.5 pu/s）-> t = {t_unload:.2f} s")

    # --- 05.5 黑启动带载次序 ---
    print()
    print("[05.5] 黑启动带载次序（ΔV≈ΔQ·X_s, X_s=0.1 pu, 允许跌落 0.05 pu）:")
    for name, dq in (("批1 站用电", 0.05), ("批2 照明", 0.15), ("批3 电机", 0.40)):
        dv = voltage_drop_pu(dq)
        print(f"  {name} {dq:.2f} pu -> ΔV = {dv:.3f} pu（{dv*100:.1f}%）")
    q_max = max_load_step_pu()
    dv_bad = voltage_drop_pu(0.6)
    print(f"  单次最大无功阶跃 ΔQ_max = {q_max:.2f} pu")
    print(f"  一次性带载 0.60 pu -> ΔV = {dv_bad:.3f} pu（{dv_bad*100:.1f}%，越限）")

    # 与正文手算一致的自检
    ok = (
        abs(inrush_from_amplitude(0.02) - 0.2) < 1e-9
        and abs(inrush_from_phase(0.1) - 1.0) < 1e-9
        and abs(inrush_from_phase(0.01) - 0.1) < 1e-9
        and abs(amplitude_threshold_pu() - 0.01) < 1e-9
        and abs(phase_threshold_rad() - 0.01) < 1e-9
        and abs(pre_sync_time(0.1, 0.05) - 0.3183) < 1e-3
        and abs(unload_time(0.2) - 0.4) < 1e-9
        and abs(voltage_drop_pu(0.6) - 0.06) < 1e-9
        and abs(max_load_step_pu() - 0.5) < 1e-9
    )
    print()
    print("自检通过" if ok else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end