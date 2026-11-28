# @AI_GENERATED
"""第 11 章端到端演示：预测 EMS 流水线与数据契约。

运行：python examples/ch11_pipeline.py
锚定正文手算：气象入站 → 门控 → 回填 → 推理 → 发布 → 契约校验，
单点 GHI=800 -> P_hat=18.154；坏点回填 810 -> P_hat=18.394；时标错位 727.5 -> 校验拦截。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.pipeline import (  # noqa: E402
    ForecastRecord,
    run_forecast_pipeline,
    validate_contract,
)


def main():
    print("预测 EMS 流水线与数据契约  [主线: 50 MW/100 MWh 储能 + 30 MW 光伏]\n")

    # 11.4 主案例：11:00/11:15/11:30 三点，第二点 GHI 缺测（NaN）
    ghi_seq = [800.0, float("nan"), 820.0]
    t_amb_seq = [20.0, 20.0, 20.0]
    times_min = [660.0, 675.0, 690.0]  # 11:00 / 11:15 / 11:30

    records = run_forecast_pipeline(ghi_seq, t_amb_seq, times_min)
    print("[11.4] 流水线四段：气象入站 -> 门控 -> 回填 -> 推理 -> 发布")
    for r in records:
        print(f"  时标={r.timestamp_min:5.0f} min  P_hat={r.p_hat:7.3f} MW  status={r.status}")

    # 11.3 契约校验：对齐点全部通过
    report = validate_contract(records)
    print("\n[11.3] 数据契约校验（15min 网格 ±2.5min）：")
    for item in report:
        print(f"  {item['timestamp_min']:5.0f} min -> aligned={item['aligned']}, ok={item['ok']}")

    # 11.3 时标错位：12:07:30 = 727.5 分钟，偏移 7.5 > 2.5 -> 拦截
    bad_record = ForecastRecord(timestamp_min=727.5, p_hat=18.154, status="valid")
    bad_report = validate_contract([bad_record])[0]
    print(f"\n[11.3] 时标错位示例：727.5 min -> aligned={bad_report['aligned']}, ok={bad_report['ok']}")

    # 自检：锚定正文手算数值
    ok = (
        abs(records[0].p_hat - 18.154) < 1e-9        # 11:00 GHI=800 -> 18.154（复用 05 章）
        and records[0].status == "valid"
        and abs(records[1].p_hat - 18.394) < 1e-3     # 回填 810 -> 18.394
        and records[1].status == "filled"
        and abs(records[2].p_hat - 18.633) < 1e-3     # 11:30 GHI=820 -> 18.633
        and all(r["ok"] for r in report)              # 三点时标均对齐
        and not bad_report["aligned"]                 # 727.5 错位拦截
    )
    print("\n自检通过" if ok else "\n自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end