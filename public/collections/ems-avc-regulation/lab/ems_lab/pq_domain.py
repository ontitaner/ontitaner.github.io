# @AI_GENERATED
"""P-Q 联合可行域计算

对应章节：02 P优先下的Q可用量，03 联合P-Q可行域

教学示例默认值（对齐 02.4 / 03.4 手算）：
  PCS 3×5000 kVA, P=[4500,4500,4000] kW → Q_available=6.2 Mvar
"""
from __future__ import annotations
import math
from typing import List


def q_available_under_p(p_kw: float, s_max_kva: float) -> float:
    if abs(p_kw) >= s_max_kva:
        return 0.0
    return math.sqrt(s_max_kva**2 - p_kw**2)


def joint_q_available(pcs: List[dict]) -> dict:
    q_pos = 0.0
    q_neg = 0.0
    details = []
    for pcs_i in pcs:
        s = pcs_i['s_kva']
        p = pcs_i['p_kw']
        if abs(p) >= s:
            q_i = 0.0
        else:
            q_i = math.sqrt(s**2 - p**2)
        q_pos += q_i
        q_neg += q_i
        details.append({
            'id': pcs_i['id'],
            'q_avail_kvar': q_i,
            'p_ratio': abs(p) / s,
        })
    return {
        'q_pos_kvar': q_pos,
        'q_neg_kvar': q_neg,
        'details': details,
    }
# @AI_GENERATED: end