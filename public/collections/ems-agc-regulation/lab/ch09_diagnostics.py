# @AI_GENERATED
"""ch09 AGC 离线纠偏与根因定位 — 自诊断 lab。

模拟 EMS 采集→调度下发→104 回送全链路数据逆推分析。
运行方式: python lab/ch09_diagnostics.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, ".")
from dataclasses import dataclass
from typing import List


@dataclass
class Record:
    timestamp: str
    dispatch_target_mw: float
    ems_issued_mw: float
    pcs_feedback_mw: float


@dataclass
class DiagResult:
    verdict: str
    root_cause: str
    recommendation: str


def diagnose(rec: Record) -> DiagResult:
    """单条记录的离线自诊断。"""
    # 链：调度目标 → EMS 接收并限制 → 下发 → PCS 采集回
    diff_dispatch_ems = abs(rec.ems_issued_mw - rec.dispatch_target_mw)
    diff_ems_pcs = abs(rec.pcs_feedback_mw - rec.ems_issued_mw)
    diff_dispatch_pcs = abs(rec.pcs_feedback_mw - rec.dispatch_target_mw)

    if diff_dispatch_ems > 1.0:
        return DiagResult("EMS 阶段异常",
                          f"EMS 发出({rec.ems_issued_mw:.1f})与调度要求({rec.dispatch_target_mw:.1f})偏差{diff_dispatch_ems:.1f}MW",
                          "检查 ramp 限速/死区参数是否被意外修改")
    if diff_ems_pcs > 0.5:
        return DiagResult("PCS 响应偏差",
                          f"PCS 反馈({rec.pcs_feedback_mw:.1f})与 EMS 下发({rec.ems_issued_mw:.1f})偏差{diff_ems_pcs:.1f}MW",
                          "检查 PCS 通信丢包、Ramp 设置或限流保护触发")
    if diff_dispatch_pcs < 0.3:
        return DiagResult("正常",
                          f"全链路偏差 {diff_dispatch_pcs:.2f}MW 在阈值内",
                          "无需处置")
    return DiagResult("端到端偏差",
                      f"调度目标({rec.dispatch_target_mw:.1f})→采集({rec.pcs_feedback_mw:.1f})偏差{diff_dispatch_pcs:.1f}MW",
                      "逐级排查 104→EMS→PCS 各级延迟与损耗")


def batch_diagnose(records: List[Record]) -> List[tuple]:
    return [(rec, diagnose(rec)) for rec in records]


def test():
    rec = Record("14:00:00", 50.0, 49.8, 50.1)
    d = diagnose(rec)
    assert d.verdict == "正常"

    rec2 = Record("14:05:00", 50.0, 52.0, 50.1)
    d2 = diagnose(rec2)
    assert d2.verdict == "EMS 阶段异常"

    rec3 = Record("14:10:00", 50.0, 49.9, 53.0)
    d3 = diagnose(rec3)
    assert d3.verdict == "PCS 响应偏差"

    rec4 = Record("14:15:00", 50.0, 49.9, 50.4)
    d4 = diagnose(rec4)
    assert d4.verdict == "端到端偏差"
    print("  ✓ 根因定位自测通过")


def main():
    print("=" * 60)
    print("ch09 AGC 离线纠偏与根因定位 — diagnose()")
    print("=" * 60)

    test_records = [
        Record("14:00:00", 50.0, 49.8, 50.1),
        Record("14:01:00", 50.0, 52.0, 50.1),
        Record("14:02:00", 50.0, 49.9, 53.0),
        Record("14:03:00", 50.0, 49.9, 50.4),
    ]

    for rec, d in batch_diagnose(test_records):
        print(f"\n  [{rec.timestamp}] {d.verdict}")
        print(f"    调度={rec.dispatch_target_mw:.1f} → "
              f"EMS={rec.ems_issued_mw:.1f} → "
              f"PCS={rec.pcs_feedback_mw:.1f}")
        print(f"    根因: {d.root_cause}")
        print(f"    建议: {d.recommendation}")

    print(f"\n结论：离线自诊断通过逐段对齐调度目标/EMS下发/PCS采集三份数据，")
    print(f"  快速定位偏差发生在 EMS 侧还是 PCS 侧，避免盲目排查。")

    print("\n" + "=" * 60)
    test()
    print("=" * 60)


if __name__ == "__main__":
    main()