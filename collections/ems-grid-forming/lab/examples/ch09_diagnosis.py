# @AI_GENERATED
"""第 09 章端到端示例：验收失败根因诊断（反推对表 + 三类根因）。

运行：python examples/ch09_diagnosis.py
预期输出与章节 09.x 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.diagnosis import (  # noqa: E402
    back_calc_D,
    back_calc_station_J,
    diagnose_clock,
    diagnose_direction,
    diagnose_inertia_failure,
    diagnose_pfr_failure,
)


def main():
    print("验收失败根因诊断  [主线: 50MW/100MWh, J_sys0=6.667s, J_vsg=13.333s, D=33.333]")
    print()

    # --- 09.2 反推对表法 ---
    print("[09.2] 反推对表法（结果值 -> 原因值）:")
    d_back = back_calc_D(0.3, -0.6)
    droop = 100.0 / d_back
    print(f"  一次调频: 实测 ΔP=0.3 pu -> 反推 D = 0.3×50/0.6 = {d_back:.1f} pu (δ={droop:.1f}%)，配置 D=33.333 -> param_mismatch")
    j_station = back_calc_station_J(10.0, 6.667)
    print(f"  惯量:     J_eq=10 s -> 本站贡献 J = 10-6.667 = {j_station:.3f} s，配置 13.333 s, SOC 40%<50% -> soc_low")
    print(f"  结算方向: 期望 +0.4 pu / 实测 -0.4 pu -> reversed")
    print(f"  证据链:   最大偏差 15 ms > 10 ms -> clock_drift")
    print()

    # --- 09.3 案例 A：一次调频失败（D 参数误设） ---
    print("[09.3] 案例 A：一次调频失败（D 参数误设）:")
    for measured, tag in ((0.4, "第 1 拍（达标）"), (0.3, "第 2 拍（失败）")):
        r = diagnose_pfr_failure(measured, 0.4, 0.02, 33.333, -0.6)
        bias = abs(measured - 0.4)
        if r == "pass":
            print(f"  {tag}: ΔP={measured:.1f} vs 期望 0.4 -> 偏差 {bias:.2f} <= 0.02 -> {r}")
        else:
            d = back_calc_D(measured, -0.6)
            print(f"  {tag}: ΔP={measured:.1f} vs 期望 0.4 -> 偏差 {bias:.2f} >  0.02 -> 反推 D={d:.1f} != 配置 33.333 -> {r}")
    print()

    # --- 09.4 案例 B：惯量失败（SOC 不足） ---
    print("[09.4] 案例 B：惯量失败（SOC 不足）:")
    for j_eq, soc, tag in ((20.0, 0.60, "第 1 拍（SOC 正常）"), (10.0, 0.40, "第 2 拍（SOC 不足）")):
        r = diagnose_inertia_failure(j_eq, 20.0, 6.667, 13.333, soc, 0.50)
        if r == "pass":
            print(f"  {tag}: J_eq={j_eq:.0f} s >= 20 s -> {r}")
        else:
            j = back_calc_station_J(j_eq, 6.667)
            print(f"  {tag}: J_eq={j_eq:.0f} s <  20 s -> 反推本站 J={j:.3f} s, SOC {soc:.0%}<50% -> {r}")
    print()

    # --- 09.5 案例 C：结算反向（出力方向接反） ---
    print("[09.5] 案例 C：结算反向（出力方向接反）:")
    print(f"  期望 +0.4 / 实测 -0.4 -> {diagnose_direction(0.4, -0.4)}")
    print()

    # --- 09.6 案例 D：证据链失败（时钟未对时） ---
    print("[09.6] 案例 D：证据链失败（时钟未对时）:")
    print(f"  最大偏差 15 ms > 10 ms -> {diagnose_clock(15.0)}")
    print()

    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end