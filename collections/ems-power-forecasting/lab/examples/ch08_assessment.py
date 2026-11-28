# @AI_GENERATED
"""第 08 章端到端示例：预测考核口径与统计窗口。

运行：python examples/ch08_assessment.py
预期输出与章节 08.2 / 08.3 / 08.4 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.assessment import (  # noqa: E402
    assess,
    filter_valid,
    monthly_accuracy,
    monthly_accuracy_excluding,
    monthly_pass_rate,
    report_rate,
)
from ems_lab.error_metrics import root_mean_square_error  # noqa: E402

P_HAT = [20.0, 25.0, 22.0, 18.0, 24.0, 26.0]
P_MEAS = [18.0, 24.0, 21.0, 18.0, 12.0, 14.0]
EXCLUDE = [False, False, False, False, True, True]


def main():
    print("预测考核口径与统计窗口  [主线: 30 MW 光伏; 6 个成对预测/实测]")
    print()

    # --- 08.2 统计窗口：整月一起算 vs 分日平均 ---
    acc_month = monthly_accuracy(P_HAT, P_MEAS)
    print(f"[08.2] 整月一起算 RMSE -> 月准确率 = {acc_month:.4f}%（= (1-7/30)*100，不合格）")

    # 口径 B：分日准确率再平均（仅作对比，考核不用）
    acc_daily = []
    for a, b in [(0, 2), (2, 4), (4, 6)]:
        rmse_d = root_mean_square_error(P_HAT[a:b], P_MEAS[a:b])
        acc_daily.append((1.0 - rmse_d / 30.0) * 100.0)
    acc_daily_avg = sum(acc_daily) / len(acc_daily)
    print(f"[08.2] 分日准确率 = {[f'{a:.4f}' for a in acc_daily]}%")
    print(f"[08.2] 分日平均 = {acc_daily_avg:.4f}%（与整月 76.67% 结论相反）")

    # --- 08.3 剔除规则：剔除限电/检修后 ---
    pv, mv = filter_valid(P_HAT, P_MEAS, EXCLUDE)
    print(f"[08.3] 剔除后有效点: P_hat={pv}, P_meas={mv}")
    acc_excl = monthly_accuracy_excluding(P_HAT, P_MEAS, EXCLUDE)
    pr = monthly_pass_rate(P_HAT, P_MEAS, EXCLUDE)
    print(f"[08.3] 剔除后月准确率 = {acc_excl:.4f}%（= (1-sqrt(1.5)/30)*100，合格）")
    print(f"[08.3] 有效点合格率 = {pr:.4f}%（门槛 2 MW，4/4 全合格）")

    # --- 08.4 上报率与考核判定 ---
    rr = report_rate(2784, 2880)
    verdict = assess(acc_excl, pr, rr)
    print(f"[08.4] 上报率 = {rr:.4f}%（2784/2880，漏报 1 天）")
    print(f"[08.4] 考核判定 = {verdict}（准确率✅ 合格率✅ 上报率❌）")

    # 与正文手算一致的自检
    ok = (
        abs(acc_month - 76.66666667) < 1e-6
        and abs(acc_daily_avg - 84.12417154) < 1e-6
        and abs(acc_excl - 95.91751709) < 1e-6
        and abs(pr - 100.0) < 1e-9
        and abs(rr - 96.66666667) < 1e-6
        and verdict == {"accuracy_ok": True, "pass_rate_ok": True, "report_rate_ok": False}
    )
    print()
    print("自检通过" if ok else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end