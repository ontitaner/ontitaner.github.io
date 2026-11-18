# @AI_GENERATED
"""第 07 章端到端示例：构网型并网测试与验收（五项验收指标 + 证据链时标对齐）。

运行：python examples/ch07_acceptance.py
预期输出与章节 07.x 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.acceptance import (  # noqa: E402
    EvidenceRecord,
    blackstart_acceptance,
    clock_bias_ms,
    evidence_chain_pass,
    inertia_acceptance,
    inrush_components,
    measure_rocof_hz,
    pfr_acceptance,
    pfr_traditional_pu,
)


def main():
    print("构网型并网测试与验收  [主线: 50MW/100MWh 储能电站, SCR≈1.8]")
    print()

    # --- 07.3 惯量响应 ---
    print("[07.3] 惯量响应验收（制造功率缺口 ΔP=0.1 pu，反推等效惯量 J_eq）:")
    rocof0 = measure_rocof_hz(0.6, 0.8)
    print(f"  频率 0.8 s 跌 0.6 Hz -> 实测 RoCoF = {rocof0:.3f} Hz/s")
    for rocof, tag in ((0.75, "改造前"), (0.25, "改造后")):
        ok, j_eq = inertia_acceptance(0.1, rocof)
        print(f"  {tag} RoCoF={rocof:.2f} -> J_eq={j_eq:.3f} s -> {'达标' if ok else '不达标'}")

    # --- 07.4 一次调频 ---
    print()
    print("[07.4] 一次调频验收（Δf=-0.6 Hz, D=33.333 pu, 期望增发 0.4 pu）:")
    ok, measured = pfr_acceptance(-0.6, 33.333, 0.4)
    print(f"  构网型无死区 -> 实测增发 {measured:.3f} pu = {measured*50:.1f} MW -> {'达标' if ok else '不达标'}")
    trad = pfr_traditional_pu(-0.6, 33.333)
    print(f"  传统死区(±0.06 Hz) -> 只增发 {trad:.3f} pu = {trad*50:.1f} MW（差 {measured - trad:.3f} pu）")

    # --- 07.5 并网冲击 ---
    print()
    print("[07.5] 并网冲击验收（X_s=0.1, I_max=0.1 pu）:")
    i_amp, i_ph = inrush_components(0.01, 0.01)
    print(f"  预同步达标 ΔV=0.01/Δθ=0.01 rad -> 幅值冲击 {i_amp:.2f} pu / 相位冲击 {i_ph:.2f} pu -> 达标")
    _, i_ph_bad = inrush_components(0.0, 0.1)
    print(f"  未预同步 Δθ=0.1 rad -> 相位冲击 {i_ph_bad:.2f} pu -> 越限")

    # --- 07.6 黑启动带载 ---
    print()
    print("[07.6] 黑启动带载验收（ΔV_max=0.05 pu, X_s=0.1）:")
    for dq in (0.5, 0.6):
        ok, dv = blackstart_acceptance(dq)
        print(f"  单次带载 ΔQ={dq:.1f} pu -> 电压跌落 {dv:.2f} pu -> {'达标' if ok else '越限'}")

    # --- 07.7 证据链时标对齐 ---
    print()
    print("[07.7] 证据链时标对齐（跨设备偏差 ≤ 10 ms）:")
    records = [
        EvidenceRecord("T_evt", "调度主站", 0.0),
        EvidenceRecord("T_evt", "EMS", 5.0),
        EvidenceRecord("T_start", "调度主站", 200.0),
        EvidenceRecord("T_start", "EMS", 205.0),
        EvidenceRecord("T_end", "调度主站", 800.0),
        EvidenceRecord("T_end", "PCS 录波", 803.0),
    ]
    for r in records:
        print(f"  {r.event:<7} {r.source:<6} t={r.t_ms:6.0f} ms")
    ok, max_bias = evidence_chain_pass(records)
    print(f"  最大跨设备偏差 = {max_bias:.0f} ms -> {'达标' if ok else '不达标'}")

    # 与正文手算一致的自检
    ok, j_eq_after = inertia_acceptance(0.1, 0.25)
    _, j_eq_before = inertia_acceptance(0.1, 0.75)
    ok_all = (
        abs(measure_rocof_hz(0.6, 0.8) - 0.75) < 1e-9
        and ok and abs(j_eq_after - 20.0) < 1e-9
        and abs(j_eq_before - 6.6667) < 1e-3
        and abs(pfr_acceptance(-0.6, 33.333, 0.4)[1] - 0.4) < 1e-3
        and abs(pfr_traditional_pu(-0.6, 33.333) - 0.36) < 1e-3
        and abs(inrush_components(0.01, 0.01)[1] - 0.1) < 1e-9
        and abs(inrush_components(0.0, 0.1)[1] - 1.0) < 1e-9
        and abs(blackstart_acceptance(0.6)[1] - 0.06) < 1e-9
        and evidence_chain_pass(records)[0] is True
    )
    print()
    print("自检通过" if ok_all else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end