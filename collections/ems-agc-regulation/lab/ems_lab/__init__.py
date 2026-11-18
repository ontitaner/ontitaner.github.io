# @AI_GENERATED
"""AGC 二次调频教材真实模块层。

各章 examples 通过 `from ems_lab.agc_core import ...` 复用这里的真实接口。
正文概念实现与本层行为由 lab/tests/ 保持一致。
"""
from ems_lab.agc_core import (  # noqa: F401
    CAP_PRICE_YUAN_PER_MW_MONTH,
    MILE_PRICE_YUAN_PER_MW,
    AVAILABILITY_RATE,
    DT_S,
    PN,
    Region,
    REGION_PARAMS,
    ScoreCard,
    W_K1,
    W_K2,
    W_K3,
    ace,
    allocate_by_available,
    capacity_revenue,
    check_ramp_rate_multilevel,
    clamp,
    composite_score,
    k1_rating,
    k2_chain_budget,
    k2_rating,
    k3_rating,
    mileage_revenue,
    score_card,
)

__all__ = [
    "CAP_PRICE_YUAN_PER_MW_MONTH",
    "MILE_PRICE_YUAN_PER_MW",
    "AVAILABILITY_RATE",
    "DT_S",
    "PN",
    "Region",
    "REGION_PARAMS",
    "ScoreCard",
    "W_K1",
    "W_K2",
    "W_K3",
    "ace",
    "allocate_by_available",
    "capacity_revenue",
    "check_ramp_rate_multilevel",
    "clamp",
    "composite_score",
    "k1_rating",
    "k2_chain_budget",
    "k2_rating",
    "k3_rating",
    "mileage_revenue",
    "score_card",
]