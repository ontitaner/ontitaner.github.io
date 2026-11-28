# @AI_GENERATED
"""第 12 章端到端演示：预测模型版本治理与再训练。

运行：python examples/ch12_versioning.py
锚定正文手算：漂移检测 -> 时间隔离 -> 再训练 -> 发布卡 -> 回滚卡，
箱3 偏差 -2.25 -> -3.25 漂移触发，v2=[+0.5,-0.9,-3.25]，验证集 v1 RMSE=1.25 / v2 RMSE=0.25。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.versioning import (  # noqa: E402
    detect_drift,
    release_check,
    retrain_bias,
    rmse_of,
    should_rollback,
    time_split,
)

# 12.5 主案例：近期 11 点（按时间升序），前 7 训练 / 后 4 验证
P_PHYS = [2, 3, 10, 15, 20, 22, 24, 20, 21, 22, 23]
P_MEAS = [2.5, 3.5, 9.1, 14.1, 16.75, 18.75, 20.75, 16.5, 17.5, 18.5, 19.5]
BIAS_V1 = [0.5, -0.9, -2.25]   # v1 上线时分箱偏差（05 章锚定）


def main():
    print("预测模型版本治理与再训练  [主线: 50 MW/100 MWh 储能 + 30 MW 光伏]\n")

    # 12.4 漂移检测：箱3 bias -2.25 -> -3.25
    drift = detect_drift(-3.25, -2.25)
    print("[12.4] 漂移检测：bias_train=-2.25, bias_recent=-3.25 -> "
          f"drift=1.0 >= 1.0 -> {drift}")

    # 12.5 时间隔离：11 点切前 7 训练 / 后 4 验证
    (tr_p, tr_m), (va_p, va_m) = time_split(P_PHYS, P_MEAS, split_idx=7)
    print("\n[12.5] 时间隔离：split_idx=7")
    print(f"  训练集 {len(tr_p)} 点: P_phys={tr_p}")
    print(f"  验证集 {len(va_p)} 点: P_phys={va_p}")

    # 12.6 再训练：训练集 7 点重估三箱偏差 -> v2
    bias_v2 = retrain_bias(tr_p, tr_m)
    print(f"\n[12.6] 再训练：v2 = {[round(b, 2) for b in bias_v2]}（仅箱3 更新）")

    # 12.7 发布卡：验证集 4 点上 v1 vs v2 RMSE
    rmse_v1 = rmse_of(va_p, va_m, BIAS_V1)
    rmse_v2 = rmse_of(va_p, va_m, bias_v2)
    check = release_check(rmse_v2, rmse_v1)
    print(f"\n[12.7] 发布卡：v1 RMSE={rmse_v1:.2f}, v2 RMSE={rmse_v2:.2f}")
    print(f"  improved={check['improved']}, accuracy={check['accuracy']:.2f}%, "
          f"release={check['release']}")

    # 12.8 回滚卡：高温季线上 RMSE 1.5 > 基线 1.25
    rollback = should_rollback(1.5, 1.25)
    print(f"\n[12.8] 回滚卡：线上 1.5 > 基线 1.25 -> {rollback}")

    # 自检：锚定正文手算数值
    ok = (
        drift is True                                      # 12.4 漂移触发
        and len(tr_p) == 7 and len(va_p) == 4              # 12.5 切分
        and tr_p == [2, 3, 10, 15, 20, 22, 24]
        and va_p == [20, 21, 22, 23]
        and all(abs(a - b) < 1e-9 for a, b in
                zip(bias_v2, [0.5, -0.9, -3.25]))          # 12.6 v2
        and abs(rmse_v1 - 1.25) < 1e-9                     # 12.7 v1 RMSE
        and abs(rmse_v2 - 0.25) < 1e-9                     # 12.7 v2 RMSE
        and check["release"] is True                       # 12.7 发布
        and rollback is True                               # 12.8 回滚
    )
    print("\n自检通过" if ok else "\n自检失败")


if __name__ == "__main__":
    main()