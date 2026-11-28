# @AI_GENERATED
"""第 13 章核心模块：功率预测并网验收与证据链。

约定（对齐 08/11 章手算、附录B/C）：
- 验收不是"算一个准确率够高就过"，而是"从原始预测 -> 原始实测 -> 对齐 -> 剔除 -> 指标 -> 凭证"
  每一步可复算、可溯源。在 08 章考核三道门槛之外，新增两个关卡：
  1. 跨时标对齐：预测与实测必须落到同一 15 min 网格（±2.5 min 容差，复用 04 章 offset 口径），
     错位点不计入考核但必须留痕（aligned=False）。
  2. 剔除凭证：被剔除的限电/检修/异常点必须有凭证（限电指令/检修票/异常日志，reason 非空），
     凭证缺失 = 剔除无效，该点必须计入考核。
- 验收判定 = 复用 08 章 assess 三道门槛 + 新增对齐率、凭证完整率两道，五道全过才放行。

教学示例默认值（对齐 08 章，主线 30 MW 光伏）：
- P_nom=30 MW、准确率门槛 80%、合格率门槛 90%、上报率门槛 99%（复用 08 章）
- 对齐率门槛 99%、凭证完整率门槛 100%
- 主案例 6 点：P_hat=[20,25,22,18,24,26]、P_meas=[18,24,21,18,12,14]
  后两点为限电/检修（exclude=[F,F,F,F,T,T]）。若无凭证 -> 凭证完整率 0% -> 剔除无效
  -> 6 点全计入 RMSE=7.0 -> 76.67%（不合格）；补齐凭证 -> 4 点 RMSE=sqrt(1.5)≈1.2247
  -> 95.92%（合格）。
"""
from __future__ import annotations

from ems_lab.assessment import assess
from ems_lab.nwp_quality import timestamp_mask

DT_MINUTES = 15.0             # 验收统一网格：15 min 一点（复用 04/11 章）
TOL_MINUTES = 2.5             # 时标容差：±2.5 min（复用 04/11 章）
ALIGN_RATE_THRESHOLD = 99.0   # 对齐率门槛 % [教学示例]
EVIDENCE_RATE_THRESHOLD = 100.0  # 剔除凭证完整率门槛 % [教学示例]


def align_mask(times_min: list, dt: float = DT_MINUTES,
               tol: float = TOL_MINUTES) -> list[bool]:
    """时标对齐掩码：True=对齐（落在 dt 网格 ±tol 内）。

    复用 04 章 timestamp_mask 的 offset 口径并取反：
      offset = min(t mod dt, dt - t mod dt)，offset <= tol 判对齐（等号算对齐）。
    主案例：align_mask([660.0, 727.5, 750.0]) -> [True, False, True]。
    """
    return [not bad for bad in timestamp_mask(list(times_min), dt, tol)]


def alignment_rate(times_min: list, dt: float = DT_MINUTES,
                   tol: float = TOL_MINUTES) -> float:
    """对齐率 = 对齐点数 / 总点数 × 100（百分数）。

    主案例：alignment_rate([660.0, 727.5, 750.0]) -> 2/3×100 ≈ 66.67%。
    """
    if len(times_min) == 0:
        raise ValueError("时标序列不能为空")
    aligned = align_mask(times_min, dt, tol)
    return sum(1 for a in aligned if a) / len(aligned) * 100.0


def build_evidence(times_min: list, p_hat: list, p_meas: list,
                   exclude: list[bool], reasons: list,
                   dt: float = DT_MINUTES, tol: float = TOL_MINUTES) -> list[dict]:
    """构建证据链：逐点记录对齐/误差/剔除/凭证/有效，验收复核的最小单元。

    返回 list[dict]，每项 = {timestamp_min, aligned, p_hat, p_meas, error,
    exclude, reason, valid}。valid = aligned 且 not exclude（参与考核统计的点）。
    主案例 6 点：误差 = [+2,+1,+1,0,+12,+12]；点5/6 exclude -> valid=False。
    """
    if not (len(times_min) == len(p_hat) == len(p_meas)
            == len(exclude) == len(reasons)):
        raise ValueError(
            f"时标/预测/实测/剔除/原因五列长度须一致，实际 "
            f"{len(times_min)} vs {len(p_hat)} vs {len(p_meas)} vs "
            f"{len(exclude)} vs {len(reasons)}"
        )
    aligned = align_mask(times_min, dt, tol)
    records = []
    for t, h, m, x, r, a in zip(times_min, p_hat, p_meas, exclude, reasons, aligned):
        records.append({
            "timestamp_min": t,
            "aligned": a,
            "p_hat": h,
            "p_meas": m,
            "error": h - m,
            "exclude": x,
            "reason": r,
            "valid": a and not x,
        })
    return records


def evidence_rate(exclude: list[bool], reasons: list) -> float:
    """剔除凭证完整率 = 被剔除点中有凭证（reason 非空）的比例 × 100。

    无剔除点时返回 100.0（空集边界：没有剔除就没有凭证需求）。
    主案例：exclude=[F,F,F,F,T,T]、reasons 全空 -> 0.0；
            补齐 reasons 后 -> 2/2×100 = 100.0。
    """
    if len(exclude) != len(reasons):
        raise ValueError(
            f"剔除掩码与原因长度须一致，实际 {len(exclude)} vs {len(reasons)}"
        )
    excluded_reasons = [r for x, r in zip(exclude, reasons) if x]
    if not excluded_reasons:
        return 100.0
    has_reason = sum(1 for r in excluded_reasons if r)
    return has_reason / len(excluded_reasons) * 100.0


def acceptance_check(accuracy: float, pass_rate_val: float, report_rate_val: float,
                     alignment_rate_val: float, evidence_rate_val: float) -> dict:
    """验收判定：08 章三道门槛 + 对齐率/凭证完整率两道，五道全过才验收通过。

    返回 {accuracy_ok, pass_rate_ok, report_rate_ok, alignment_ok, evidence_ok, accepted}。
    主案例（补齐凭证）：acceptance_check(95.92, 100.0, 99.5, 100.0, 100.0)
        -> accepted=True。
    主案例（无凭证）：acceptance_check(76.67, 66.67, 99.5, 100.0, 0.0)
        -> accepted=False（accuracy_ok/pass_rate_ok/evidence_ok 均 False）。
    """
    base = assess(accuracy, pass_rate_val, report_rate_val)
    result = {
        "accuracy_ok": base["accuracy_ok"],
        "pass_rate_ok": base["pass_rate_ok"],
        "report_rate_ok": base["report_rate_ok"],
        "alignment_ok": alignment_rate_val >= ALIGN_RATE_THRESHOLD,
        "evidence_ok": evidence_rate_val >= EVIDENCE_RATE_THRESHOLD,
    }
    result["accepted"] = all(result.values())
    return result
# @AI_GENERATED: end