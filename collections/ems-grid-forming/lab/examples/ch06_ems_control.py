# @AI_GENERATED
"""第 06 章端到端示例：构网型 EMS 控制链路（五级流水线 + 状态机）。

运行：python examples/ch06_ems_control.py
预期输出与章节 06.x 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.ems_control import (  # noqa: E402
    EV_BLACKOUT,
    EV_LOADED,
    EV_RESYNC,
    EV_UNLOAD,
    GridMode,
    resync_duration_s,
    transition,
    unload_duration_s,
    validate_vsg_params,
)
from ems_lab.inertia import D_to_droop_pct  # noqa: E402


def main():
    print("构网型 EMS 控制链路  [主线: 50MW/100MWh 储能电站, SCR≈1.8]")
    print()

    # --- 06.3 参数一致性校验 ---
    print("[06.3] 参数一致性校验（跟网: 死区/调差率 -> 构网: J/D/V_ref）:")
    errs = validate_vsg_params(4.0, 20.0, 1.0)
    print(f"  J=4.0, D=20, V_ref=1.0 -> {'合法' if not errs else '非法: ' + '; '.join(errs)}")
    print(f"  D=20 -> 折算调差率 δ = {D_to_droop_pct(20.0):.1f}%")
    for J, D, v in ((0.0, 20.0, 1.0), (4.0, 0.0, 1.0), (4.0, 200.0, 1.0), (4.0, 20.0, 1.2)):
        errs = validate_vsg_params(J, D, v)
        tag = "非法: " + "; ".join(errs) if errs else "合法"
        print(f"  J={J}, D={D}, V_ref={v} -> {tag}")

    # --- 06.4 状态机 ---
    print()
    print("[06.4] 并离网状态机（三状态 + 迁移）:")
    s = GridMode.ON_GRID
    print(f"  初始状态: {s.value}")
    s = transition(s, EV_UNLOAD)
    print(f"  事件「{EV_UNLOAD}」-> {s.value}（解列 {unload_duration_s():.1f} s）")
    s = transition(s, EV_RESYNC)
    print(f"  事件「{EV_RESYNC}」-> {s.value}（再并网 {resync_duration_s():.2f} s）")
    s = transition(s, EV_BLACKOUT)
    print(f"  事件「{EV_BLACKOUT}」-> {s.value}")
    s = transition(s, EV_LOADED)
    print(f"  事件「{EV_LOADED}」-> {s.value}")

    # 与正文手算一致的自检
    ok = (
        validate_vsg_params(4.0, 20.0, 1.0) == []
        and abs(D_to_droop_pct(20.0) - 5.0) < 1e-9
        and abs(unload_duration_s() - 0.5) < 1e-9
        and abs(resync_duration_s() - 0.9183) < 1e-3
        and transition(GridMode.ON_GRID, EV_UNLOAD) is GridMode.ISLAND
        and transition(GridMode.ISLAND, EV_RESYNC) is GridMode.ON_GRID
        and transition(GridMode.ON_GRID, EV_BLACKOUT) is GridMode.BLACK_START
        and transition(GridMode.BLACK_START, EV_LOADED) is GridMode.ISLAND
    )
    print()
    print("自检通过" if ok else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end