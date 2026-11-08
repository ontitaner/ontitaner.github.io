# @AI_GENERATED
"""AGC 二次调频教材共享工具库。

提供 clamp、评分函数、区域配置常量等各章 lab 通用的辅助工具。
各章 lab 中的业务函数直接复制自教材代码块，保持原样。
所有参数均为教学示例值。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Sequence


class Region(str, Enum):
    HUADONG = "华东"
    DONGBEI = "东北"
    SHANXI = "山西"


PN = 100.0  # 教学用额定容量 (MW)
DT_S = 4.0  # 默认 AGC 分配间隔 (s)


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(value, hi))


def k1_rating(actual_mw_per_min: float, required_mw_per_min: float) -> float:
    """K1 调节速率评分（0-100）。"""
    if required_mw_per_min <= 0:
        return 0.0
    return clamp(actual_mw_per_min / required_mw_per_min * 100.0, 0.0, 100.0)


def k2_rating(actual_s: float, required_s: float) -> float:
    """K2 响应时间评分（0-100）。"""
    if required_s <= 0:
        return 0.0
    return clamp((1.0 - max(0.0, actual_s - required_s) / required_s) * 100.0, 0.0, 100.0)


def k3_rating(actual_pct: float, required_pct: float) -> float:
    """K3 调节精度评分（0-100）。"""
    if required_pct <= 0:
        return 0.0
    return clamp((1.0 - max(0.0, actual_pct - required_pct) / required_pct) * 100.0, 0.0, 100.0)


def composite_score(k1: float, k2: float, k3: float,
                    w1: float = 0.4, w2: float = 0.3, w3: float = 0.3) -> float:
    return w1 * k1 + w2 * k2 + w3 * k3


REGION_PARAMS = {
    Region.HUADONG: {
        "k1_min_pn_per_min": 1.0,
        "k2_max_s": 30.0,
        "k3_max_pct": 3.0,
        "ace_deadband_mw": 5.0,
        "kp_yuan_per_mwh": 10.0,
    },
    Region.DONGBEI: {
        "k1_min_pn_per_min": 0.75,
        "k2_max_s": 45.0,
        "k3_max_pct": 5.0,
        "ace_deadband_mw": 8.0,
        "kp_yuan_per_mwh": 6.0,
    },
    Region.SHANXI: {
        "k1_min_pn_per_min": 1.2,
        "k2_max_s": 25.0,
        "k3_max_pct": 2.5,
        "ace_deadband_mw": 3.0,
        "kp_yuan_per_mwh": 15.0,
    },
}