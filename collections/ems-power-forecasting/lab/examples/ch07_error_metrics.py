# @AI_GENERATED
"""第 07 章端到端示例：预测误差指标（bias / MAE / RMSE / MAPE / 准确率 / 合格率）。

运行：python examples/ch07_error_metrics.py
预期输出与章节 07.2 / 07.3 / 07.4 手算完全一致（自检通过）。
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.error_metrics import (  # noqa: E402
    accuracy_rmse,
    error_list,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_error,
    pass_rate,
    root_mean_square_error,
)

P_HAT = [9.0, 9.0, 15.0, 9.0, 6.0, 2.0]
P_MEAS = [6.0, 10.0, 16.0, 10.0, 6.0, 2.0]


def main():
    print("预测误差指标  [主线: 30 MW 光伏; 6 个成对预测/实测]")
    print()

    # --- 07.2 误差三个视角：bias / MAE / RMSE ---
    errs = error_list(P_HAT, P_MEAS)
    bias = mean_error(P_HAT, P_MEAS)
    mae = mean_absolute_error(P_HAT, P_MEAS)
    rmse = root_mean_square_error(P_HAT, P_MEAS)
    print(f"[07.2] 误差序列 e = {errs} MW")
    print(f"[07.2] bias = {bias:.3f} MW（正负抵消）")
    print(f"[07.2] MAE  = {mae:.3f} MW（典型大小）")
    print(f"[07.2] RMSE = {rmse:.6f} MW（= sqrt(2)，大误差 +3 被平方放大）")

    # --- 07.3 MAPE ---
    mape = mean_absolute_percentage_error(P_HAT, P_MEAS)
    print(f"[07.3] MAPE = {mape:.4f}%（相对占比）")

    # 低出力爆炸：加一个傍晚低出力点（误差仅 0.2 MW，占比却 100%）
    mape_low = mean_absolute_percentage_error(P_HAT + [0.4], P_MEAS + [0.2])
    print(f"[07.3] 低出力爆炸: 加 P_meas=0.2 点 -> MAPE = {mape_low:.4f}%（从 12.71% 拉到 25.18%）")

    # 零分母：实测为 0 的点被 drop_zero 剔除
    mape_zero = mean_absolute_percentage_error([0.5], [0.0])
    print(f"[07.3] 零分母: 全零实测 -> MAPE = {mape_zero:.3f}%（无有效样本，记 0）")

    # --- 07.4 准确率 / 合格率 ---
    acc = accuracy_rmse(P_HAT, P_MEAS)
    pr = pass_rate(P_HAT, P_MEAS)
    print(f"[07.4] 准确率 = {acc:.4f}%（= 1 - RMSE/30）")
    print(f"[07.4] 合格率 = {pr:.4f}%（门槛 2 MW，仅 +3 越限）")

    # --- 边界演示：大误差如何被 RMSE 放大 ---
    mae_big = mean_absolute_error([16.0, 9.0, 15.0, 9.0, 6.0, 2.0], P_MEAS)
    rmse_big = root_mean_square_error([16.0, 9.0, 15.0, 9.0, 6.0, 2.0], P_MEAS)
    print(f"[07.2] 大误差放大: 误差 +3 改 +10 -> MAE = {mae_big:.3f}、RMSE = {rmse_big:.3f}（RMSE 涨得更狠）")

    # 与正文手算一致的自检
    ok = (
        errs == [3.0, -1.0, -1.0, -1.0, 0.0, 0.0]
        and abs(bias - 0.0) < 1e-9
        and abs(mae - 1.0) < 1e-9
        and abs(rmse - math.sqrt(2.0)) < 1e-9
        and abs(mape - 12.70833333) < 1e-6
        and abs(mape_low - 25.17857143) < 1e-6
        and abs(mape_zero - 0.0) < 1e-9
        and abs(acc - 95.28595479) < 1e-6
        and abs(pr - 83.33333333) < 1e-6
        and abs(mae_big - (13.0 / 6.0)) < 1e-9
        and abs(rmse_big - math.sqrt(103.0 / 6.0)) < 1e-9
    )
    print()
    print("自检通过" if ok else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end