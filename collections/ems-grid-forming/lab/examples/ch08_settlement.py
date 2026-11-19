# @AI_GENERATED
"""第 08 章端到端示例：构网型考核与结算（惯量/阻尼拆分计量 + 结算口径 + 考核）。

运行：python examples/ch08_settlement.py
预期输出与章节 08.x 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.settlement import (  # noqa: E402
    SettlementConfig,
    assess,
    completion_rate,
    droop_energy_mws,
    inertia_energy_mws,
    mws_to_mwh,
    penalty_fee,
    settle_droop,
    settle_inertia,
    settle_inertia_as_energy,
    split_power_mw,
)


def main():
    cfg = SettlementConfig()
    print("构网型考核与结算  [主线: 50MW/100MWh 储能电站, J_vsg=13.333s, D=33.333]")
    print()

    # --- 08.3 事件模型：频率 0.6 Hz 跌落 + 稳定段 30 s ---
    t_drop = cfg.df_hz / cfg.rocof_hz
    print("[08.3] 一次频率跌落事件（Δf=0.6 Hz, RoCoF=0.25 Hz/s, T_hold=30 s）:")
    print(f"  跌落段时长 Δt_drop = Δf/RoCoF = {t_drop:.1f} s")

    # --- 08.4 逐拍追踪：第 1 拍（跌落中） vs 第 2 拍（稳定段） ---
    print()
    print("[08.4] 出力拆分逐拍追踪（第 1 拍=跌落中, 第 2 拍=稳定段）:")
    p_i_drop, p_d_drop = split_power_mw(0.6, 0.25, cfg)
    p_i_hold, p_d_hold = split_power_mw(0.6, 0.0, cfg)
    print(f"  第 1 拍（RoCoF=0.25, Δf 涨到 0.6）: 惯量 {p_i_drop:.3f} MW + 阻尼 {p_d_drop:.1f} MW = {p_i_drop + p_d_drop:.3f} MW")
    print(f"  第 2 拍（RoCoF=0,    Δf 恒定 0.6）: 惯量 {p_i_hold:.3f} MW + 阻尼 {p_d_hold:.1f} MW = {p_i_hold + p_d_hold:.1f} MW")
    print("  -> 惯量只在频率变化时「顶一下」，阻尼随频偏持续「扛住」")

    # --- 08.5 电量拆分：惯量一份固定动能 vs 阻尼随时间累积 ---
    print()
    print("[08.5] 支撑电量拆分:")
    w_inertia = inertia_energy_mws(cfg)
    w_droop = droop_energy_mws(cfg)
    print(f"  惯量电量 W_inertia = J·Δf·S_n/f_n = {w_inertia:.1f} MW·s = {mws_to_mwh(w_inertia):.5f} MWh（与 RoCoF/时长无关）")
    print(f"  阻尼电量 W_droop   = 跌落 {cfg.d*cfg.sn_mva/cfg.f_n*(cfg.df_hz**2/(2*cfg.rocof_hz)):.0f} + 稳定 {cfg.d*cfg.sn_mva/cfg.f_n*cfg.df_hz*cfg.t_hold_s:.0f} = {w_droop:.0f} MW·s = {mws_to_mwh(w_droop):.5f} MWh")

    # --- 08.6 结算口径：惯量按容量、阻尼按电量 ---
    print()
    print("[08.6] 结算口径:")
    c_inertia = settle_inertia(cfg)
    c_droop = settle_droop(cfg)
    c_wrong = settle_inertia_as_energy(cfg)
    print(f"  惯量按容量结算: {cfg.c_inertia:.0f} 元/惯量秒 × {cfg.j_vsg:.3f} s = {c_inertia:.0f} 元")
    print(f"  阻尼按电量结算: {cfg.c_energy:.0f} 元/MWh × {mws_to_mwh(w_droop):.5f} MWh = {c_droop:.2f} 元")
    print(f"  错误口径（惯量按电量）: {cfg.c_energy:.0f} × {mws_to_mwh(w_inertia):.5f} = {c_wrong:.2f} 元（比正确口径小 {c_inertia/c_wrong:.0f} 倍）")

    # --- 08.7 考核判定：完成率 + 反向/缺额 ---
    print()
    print("[08.7] 考核判定（完成率阈值 60%）:")
    cases = [
        ("合格", 624.0),
        ("完成率 50%", 312.0),
        ("反向（符号错）", -624.0),
    ]
    for tag, w_actual in cases:
        verdict = assess(624.0, w_actual, cfg.completion_min)
        fee = penalty_fee(624.0, w_actual, cfg)
        rate = completion_rate(w_actual, 624.0)
        print(f"  {tag:<14} 完成率 {rate*100:5.1f}% -> 判定 {verdict:<7} -> 费用 {fee:6.2f} 元")

    # 与正文手算一致的自检
    p_i, p_d = split_power_mw(0.6, 0.25, cfg)
    ok_all = (
        abs(p_i - 3.3333) < 1e-3
        and abs(p_d - 20.0) < 1e-3
        and abs(inertia_energy_mws(cfg) - 8.0) < 1e-3
        and abs(droop_energy_mws(cfg) - 624.0) < 1e-3
        and abs(settle_inertia(cfg) - 4000.0) < 1e-3
        and abs(settle_droop(cfg) - 62.4) < 1e-3
        and abs(penalty_fee(624.0, 312.0, cfg) - 31.2) < 1e-3
        and abs(penalty_fee(624.0, -624.0, cfg) - 124.8) < 1e-3
    )
    print()
    print("自检通过" if ok_all else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end