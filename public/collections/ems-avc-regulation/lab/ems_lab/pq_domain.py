# @AI_GENERATED
"""P-Q 联合可行域计算

对应章节：02 P优先下的Q可用量，03 联合P-Q可行域

教学示例默认值（对齐 02.6 / 03.4 手算）：
  单台 PCS S=1000 kVA：P=900 kW → Q_available=sqrt(1000²−900²)=435.9 kvar
  多台联合：见 joint_q_available 的 details 字段。
"""
from __future__ import annotations
import math
from typing import List, Tuple


def q_available_under_p(p_kw: float, s_max_kva: float) -> float:
    """单台 PCS 在给定有功 P 下的可用无功（幅值，正负对称）。"""
    if abs(p_kw) >= s_max_kva:
        return 0.0
    return math.sqrt(s_max_kva**2 - p_kw**2)


def joint_q_available(pcs: List[dict]) -> dict:
    """多台 PCS 联合 Q 可用量（正负对称，返回 q_pos/q_neg/details）。"""
    q_pos = 0.0
    q_neg = 0.0
    details = []
    for pcs_i in pcs:
        s = pcs_i['s_kva']
        p = pcs_i['p_kw']
        q_i = q_available_under_p(p, s)
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


def pq_circle_points(s_max_kva: float, n: int = 360) -> Tuple[List[float], List[float]]:
    """生成 P-Q 能力圆的 P/Q 坐标对（单位圆参数化，供绘图使用）。

    返回 (p_points, q_points)，长度均为 n+1，首尾闭合。
    """
    p_points: List[float] = []
    q_points: List[float] = []
    for i in range(n + 1):
        angle = 2 * math.pi * i / n
        p_points.append(s_max_kva * math.cos(angle))
        q_points.append(s_max_kva * math.sin(angle))
    return p_points, q_points
# @AI_GENERATED: end