# @AI_GENERATED
"""第 13 章一致性测试：锚定正文手算数值与边界语义。

主案例：时标对齐 660/727.5/750 -> [True,False,True]、对齐率 66.67%；
6 点证据链误差 [+2,+1,+1,0,+12,+12]、valid=[T,T,T,T,F,F]；
凭证完整率 无凭证 0% / 补齐 100%；验收判定无凭证 accepted=False、补齐 accepted=True。
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.acceptance import (  # noqa: E402
    acceptance_check,
    align_mask,
    alignment_rate,
    build_evidence,
    evidence_rate,
)

TIMES = [660.0, 675.0, 690.0, 705.0, 720.0, 735.0]
P_HAT = [20.0, 25.0, 22.0, 18.0, 24.0, 26.0]
P_MEAS = [18.0, 24.0, 21.0, 18.0, 12.0, 14.0]
EXCLUDE = [False, False, False, False, True, True]
REASONS_NONE = ["", "", "", "", "", ""]
REASONS_FULL = ["", "", "", "", "限电指令 D3-10:00", "检修票 M-041"]


def test_align_mask_main():
    # 13.3 主案例：660 对齐、727.5 错位、750 对齐
    assert align_mask([660.0, 727.5, 750.0]) == [True, False, True]


def test_align_mask_boundary_equal():
    # 边界语义：offset 恰好等于容差 2.5 算对齐（timestamp_mask 用 > tol 判错位）
    assert align_mask([662.5]) == [True]


def test_alignment_rate_main():
    # 13.3 主案例：2/3×100 ≈ 66.67%
    assert alignment_rate([660.0, 727.5, 750.0]) == pytest.approx(66.6666667)


def test_alignment_rate_empty():
    with pytest.raises(ValueError):
        alignment_rate([])


def test_build_evidence_main():
    # 13.4 主案例：误差 [+2,+1,+1,0,+12,+12]、valid=[T,T,T,T,F,F]、全部对齐
    recs = build_evidence(TIMES, P_HAT, P_MEAS, EXCLUDE, REASONS_NONE)
    assert [r["error"] for r in recs] == [2.0, 1.0, 1.0, 0.0, 12.0, 12.0]
    assert [r["valid"] for r in recs] == [True, True, True, True, False, False]
    assert all(r["aligned"] for r in recs)


def test_build_evidence_length_mismatch():
    with pytest.raises(ValueError):
        build_evidence([660.0], [20.0], [18.0], [False], [])


def test_evidence_rate_none():
    # 13.4 主案例：2 个剔除点都无凭证 -> 0%
    assert evidence_rate(EXCLUDE, REASONS_NONE) == 0.0


def test_evidence_rate_full():
    # 补齐凭证 -> 100%
    assert evidence_rate(EXCLUDE, REASONS_FULL) == 100.0


def test_evidence_rate_no_exclude():
    # 空集边界：无剔除点返回 100%（没有剔除就没有凭证需求）
    assert evidence_rate([False] * 6, [""] * 6) == 100.0


def test_evidence_rate_partial():
    # 2 个剔除点只有 1 个有凭证 -> 50%
    reasons = ["", "", "", "", "限电指令 D3-10:00", ""]
    assert evidence_rate(EXCLUDE, reasons) == 50.0


def test_acceptance_check_pass():
    # 13.5 主案例（补齐凭证）：五道全过 -> accepted=True
    c = acceptance_check(95.92, 100.0, 99.5, 100.0, 100.0)
    assert c["accuracy_ok"] is True
    assert c["pass_rate_ok"] is True
    assert c["report_rate_ok"] is True
    assert c["alignment_ok"] is True
    assert c["evidence_ok"] is True
    assert c["accepted"] is True


def test_acceptance_check_fail_no_evidence():
    # 13.5 主案例（无凭证）：accuracy/pass_rate/evidence 三道不过 -> accepted=False
    c = acceptance_check(76.67, 66.67, 99.5, 100.0, 0.0)
    assert c["accuracy_ok"] is False
    assert c["pass_rate_ok"] is False
    assert c["report_rate_ok"] is True
    assert c["alignment_ok"] is True
    assert c["evidence_ok"] is False
    assert c["accepted"] is False


def test_acceptance_check_alignment_boundary():
    # 边界语义：对齐率恰好等于门槛 99% 算达标（>=）
    c = acceptance_check(95.92, 100.0, 99.5, 99.0, 100.0)
    assert c["alignment_ok"] is True