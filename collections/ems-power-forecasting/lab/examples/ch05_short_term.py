# @AI_GENERATED
"""第 05 章端到端示例：短期功率预测（物理基值 + 分箱偏差修正）。

运行：python examples/ch05_short_term.py
预期输出与章节 05.5 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.shortterm import (  # noqa: E402
    bias_correct,
    fit_bin_bias,
    physical_forecast,
    short_term_forecast,
)


def main():
    print("短期功率预测  [主线: 30 MW 光伏; 0-72h 日前预测]")
    print()

    # --- 05.3 物理基值：NWP -> 并网点物理预测（复用 03 章光伏链） ---
    p_phys = physical_forecast(800.0, 20.0)
    print(f"[05.3] NWP GHI=800、T_amb=20 -> 物理预测 P_phys = {p_phys:.3f} MW")

    # --- 05.4/05.5 分箱偏差修正 ---
    p_phys_list = [2.0, 3.0, 10.0, 15.0, 24.0, 26.0]
    p_meas_list = [2.6, 3.4, 9.2, 14.0, 22.0, 23.5]
    bin_edges = [5.0, 20.0]
    bias = fit_bin_bias(p_phys_list, p_meas_list, bin_edges)
    print(f"[05.5] 历史 6 样本分 3 箱 [0,5)/[5,20)/[20,∞) -> 箱偏差 bias = {[round(b, 3) for b in bias]} MW")

    global_mean = sum(m - p for m, p in zip(p_meas_list, p_phys_list)) / len(p_phys_list)
    print(f"[05.5] 对比：全局单一修正 = {global_mean:.3f} MW（不能反映偏差随出力段变化）")

    p_hat = bias_correct(p_phys, bin_edges, bias)
    print(f"[05.5] 新预测 P_hat = {p_phys:.3f} + ({bias[2]:.2f}) = {p_hat:.3f} MW")

    p_hat2 = short_term_forecast(800.0, 20.0, bin_edges, bias)
    print(f"[05.5] 端到端 short_term_forecast(800, 20, ...) = {p_hat2:.3f} MW")

    # --- 逐拍追踪 ---
    p_hat_t0 = bias_correct(3.0, bin_edges, bias)
    print(f"[2拍] t=0 低出力 P_phys=3.0 -> 箱1 -> {p_hat_t0:.1f} MW（物理略低估，往上修）")
    p_hat_t1 = bias_correct(20.404, bin_edges, bias)
    print(f"[2拍] t=1 正午 P_phys=20.404 -> 箱3 -> {p_hat_t1:.3f} MW（物理高估，往下修）")

    # 与正文手算一致的自检
    ok = (
        abs(p_phys - 20.404) < 1e-6
        and abs(bias[0] - 0.5) < 1e-9
        and abs(bias[1] - (-0.9)) < 1e-9
        and abs(bias[2] - (-2.25)) < 1e-9
        and abs(p_hat - 18.154) < 1e-6
        and abs(p_hat_t0 - 3.5) < 1e-9
        and abs(p_hat_t1 - 18.154) < 1e-6
    )
    print()
    print("自检通过" if ok else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end