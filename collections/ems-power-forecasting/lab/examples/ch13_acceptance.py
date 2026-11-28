# @AI_GENERATED
"""第 13 章端到端演示：功率预测并网验收与证据链。

运行：python examples/ch13_acceptance.py
锚定正文手算：跨时标对齐（660/727.5/750 -> 对齐率 66.67%）、
证据链与剔除凭证（无凭证 -> 76.67% 不合格；补齐 -> 95.92% 合格）、
验收判定五道门槛（accepted=False -> True）。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.acceptance import (  # noqa: E402
    acceptance_check,
    align_mask,
    alignment_rate,
    build_evidence,
    evidence_rate,
)
from ems_lab.assessment import (  # noqa: E402
    monthly_accuracy,
    monthly_accuracy_excluding,
    monthly_pass_rate,
)

TIMES = [660.0, 675.0, 690.0, 705.0, 720.0, 735.0]
P_HAT = [20.0, 25.0, 22.0, 18.0, 24.0, 26.0]
P_MEAS = [18.0, 24.0, 21.0, 18.0, 12.0, 14.0]
EXCLUDE = [False, False, False, False, True, True]
REASONS_NONE = ["", "", "", "", "", ""]
REASONS_FULL = ["", "", "", "", "限电指令 D3-10:00", "检修票 M-041"]


def main():
    print("功率预测并网验收与证据链  [主线: 50 MW/100 MWh 储能 + 30 MW 光伏]\n")

    # 13.3 跨时标对齐
    t_demo = [660.0, 727.5, 750.0]
    print("[13.3] 时标对齐：660/727.5/750 ->", align_mask(t_demo))
    print(f"       对齐率 = {alignment_rate(t_demo):.2f}%")

    # 13.4 证据链（无凭证 -> 剔除无效 -> 6 点全计）
    ev_none = build_evidence(TIMES, P_HAT, P_MEAS, EXCLUDE, REASONS_NONE)
    er_none = evidence_rate(EXCLUDE, REASONS_NONE)
    acc_none = monthly_accuracy(P_HAT, P_MEAS)
    pass_none = monthly_pass_rate(P_HAT, P_MEAS, [False] * 6)
    print(f"\n[13.4] 无凭证：凭证完整率 = {er_none:.1f}% -> 剔除无效")
    print(f"       6 点全计：准确率 = {acc_none:.2f}%、合格率 = {pass_none:.2f}%")

    # 补齐凭证 -> 剔除有效 -> 4 点计
    er_full = evidence_rate(EXCLUDE, REASONS_FULL)
    acc_full = monthly_accuracy_excluding(P_HAT, P_MEAS, EXCLUDE)
    pass_full = monthly_pass_rate(P_HAT, P_MEAS, EXCLUDE)
    print(f"\n[13.4] 补齐凭证：凭证完整率 = {er_full:.1f}% -> 剔除有效")
    print(f"       4 点计：准确率 = {acc_full:.2f}%、合格率 = {pass_full:.2f}%")

    # 13.5 验收判定：五道门槛
    check_none = acceptance_check(acc_none, pass_none, 99.5, 100.0, er_none)
    check_full = acceptance_check(acc_full, pass_full, 99.5, 100.0, er_full)
    print(f"\n[13.5] 验收判定（无凭证）：accepted={check_none['accepted']}")
    print(f"       {check_none}")
    print(f"\n[13.5] 验收判定（补齐凭证）：accepted={check_full['accepted']}")
    print(f"       {check_full}")

    # 自检：锚定正文手算数值
    ok = (
        align_mask(t_demo) == [True, False, True]              # 13.3 对齐掩码
        and abs(alignment_rate(t_demo) - 66.6666667) < 1e-4    # 13.3 对齐率
        and [r["error"] for r in ev_none] == [2, 1, 1, 0, 12, 12]  # 13.4 误差
        and [r["valid"] for r in ev_none] == [True, True, True, True, False, False]
        and er_none == 0.0                                     # 13.4 凭证完整率 0%
        and abs(acc_none - 76.6666667) < 1e-4                  # 13.4 无凭证准确率
        and abs(acc_full - 95.9175) < 1e-3                     # 13.4 补齐准确率
        and er_full == 100.0                                   # 13.4 凭证完整率 100%
        and check_none["accepted"] is False                    # 13.5 无凭证不过
        and check_full["accepted"] is True                     # 13.5 补齐通过
    )
    print("\n自检通过" if ok else "\n自检失败")


if __name__ == "__main__":
    main()