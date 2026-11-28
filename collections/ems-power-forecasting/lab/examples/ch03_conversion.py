# @AI_GENERATED
"""第 03 章端到端示例：辐照 -> 光伏出力（含温度/削峰）+ 风速 -> 风机出力（功率曲线）。

运行：python examples/ch03_conversion.py
预期输出与章节 03.x 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.irradiance import (  # noqa: E402
    cell_temperature,
    ghi_to_poa,
    inverter_ac,
    pv_dc_power,
    pv_pcc_power,
    temperature_factor,
)
from ems_lab.power_curve import wind_power  # noqa: E402


def main():
    print("光伏风电出力转换模型  [主线: 30 MWp 光伏; 教学示例: 2.5 MW 单机风电]")
    print()

    # --- 03.2 辐照->光伏：温度降额 ---
    ghi, t_amb, p_rated = 800.0, 20.0, 30.0
    poa = ghi_to_poa(ghi, 1.0)
    t_cell = cell_temperature(t_amb, poa)
    dc = pv_dc_power(p_rated, poa, t_cell)
    print(f"[03.2] GHI={ghi:.0f} -> POA={poa:.0f} W/m²；T_amb={t_amb:.0f}°C -> T_cell={t_cell:.1f}°C")
    print(f"[03.2] 温度系数 = {temperature_factor(t_cell):.4f}（降额 {1 - temperature_factor(t_cell):.1%}）")
    print(f"[03.2] P_module = {p_rated:.0f}×(800/1000)×{temperature_factor(t_cell):.2f} = {dc:.2f} MW")
    print(f"[03.2] 对比 02 章忽略温度的 24 MW，温度降额 {24.0 - dc:.2f} MW")

    # --- 03.3 逆变效率 + 削峰 ---
    ac = inverter_ac(dc, 0.95, 25.0)
    pv = pv_pcc_power(ac, 0.8)   # 02 章限电 0.8 MW
    print(f"[03.3] P_ac = {dc:.2f}×0.95 = {inverter_ac(dc, 0.95):.3f} MW（未超 25 MW，不削峰）")
    print(f"[03.3] 并网点 P_pv = {ac:.3f} − 0.8 = {pv:.3f} MW（衔接 02 章跨平面换算）")

    dc_peak = pv_dc_power(30.0, 1000.0, 25.0)          # 最强辐照 STC
    ac_peak = inverter_ac(dc_peak, 0.95, 25.0)
    print(f"[03.3] 最强辐照 G=1000、冻结温度(25°C)：P_module={dc_peak:.0f} MW -> "
          f"{dc_peak:.0f}×0.95={dc_peak * 0.95:.1f} MW -> 削到 {ac_peak:.0f} MW"
          f"（削 {dc_peak * 0.95 - ac_peak:.1f} MW）")

    # 真实叠加态：G=1000 时温度随辐照一起涨，不再冻结在 STC
    t_cell_peak = cell_temperature(20.0, 1000.0)        # = 51.25 °C
    dc_peak_real = pv_dc_power(30.0, 1000.0, t_cell_peak)
    ac_peak_real = inverter_ac(dc_peak_real, 0.95, 25.0)
    print(f"[03.3] 最强辐照 G=1000、真实叠加态：T_cell={t_cell_peak:.2f}°C -> "
          f"P_module={dc_peak_real:.2f} MW -> {dc_peak_real:.2f}×0.95={dc_peak_real * 0.95:.2f} MW"
          f" -> 削到 {ac_peak_real:.0f} MW（削 {dc_peak_real * 0.95 - ac_peak_real:.2f} MW）")

    # --- 03.4 风速->风机：功率曲线 ---
    print()
    print("[03.4] 风速->风机出力（教学示例 2.5 MW 单机，v_ci=3 / v_r=12 / v_co=25）:")
    for v in (2.0, 3.0, 6.0, 9.0, 12.0, 18.0, 25.0, 26.0):
        print(f"  v={v:4.1f} m/s -> P = {wind_power(v):.3f} MW")

    # 与正文手算一致的自检
    ok = (
        abs(poa - 800.0) < 1e-9
        and abs(t_cell - 45.0) < 1e-9
        and abs(dc - 22.32) < 1e-9
        and abs(ac - 21.204) < 1e-9
        and abs(pv - 20.404) < 1e-9
        and abs(ac_peak - 25.0) < 1e-9
        and abs(t_cell_peak - 51.25) < 1e-9
        and abs(dc_peak_real - 27.24375) < 1e-9
        and abs(ac_peak_real - 25.0) < 1e-9
        and abs(wind_power(6.0) - 2.5 / 9.0) < 1e-9
        and abs(wind_power(12.0) - 2.5) < 1e-9
        and abs(wind_power(26.0) - 0.0) < 1e-9
    )
    print()
    print("自检通过" if ok else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end