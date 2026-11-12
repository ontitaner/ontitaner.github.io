# @AI_GENERATED
"""AGC 二次调频教材共享工具库。

提供 clamp、K1/K2/K3 评分函数、综合评分、区域配置常量、补偿模型等各章 lab 通用工具。
所有评分公式与正文 07 章「K1/K2/K3 单项评分公式」逐字对齐：
    K1_score = min(100, 100 × K1_actual / K1_required)
    K2_score = 100 × (1 − K2_actual / K2_limit)
    K3_score = 100 × (1 − K3_actual / K3_limit)
    综合评分 = 0.30×K1 + 0.20×K2 + 0.50×K3
所有参数均为教学示例值，现场以项目适用调度细则与合同为准。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List


class Region(str, Enum):
    HUADONG = "华东"
    DONGBEI = "东北"
    SHANXI = "山西"


PN = 100.0   # 教学用额定容量 (MW)
DT_S = 4.0   # 默认 AGC 分配间隔 (s)

# 综合评分权重（正文 07 章表：华东/东北/山西均为 30%/20%/50%）
W_K1 = 0.30
W_K2 = 0.20
W_K3 = 0.50

# 补偿单价（正文 07 章：容量 10 元/MW·月，里程 0.5 元/MW）
CAP_PRICE_YUAN_PER_MW_MONTH = 10.0
MILE_PRICE_YUAN_PER_MW = 0.5
AVAILABILITY_RATE = 0.98          # 投运率（华东/山西要求 ≥98%）


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(value, hi))


def ace(dp_tie_mw: float, bias_mw_per_hz: float, df_hz: float) -> float:
    """区域控制偏差 ACE（正文 01 章）。

    正文公式：ACE = ΔP_tie + B × Δf
    dp_tie_mw：联络线交换功率与计划值的偏差（送出为正），单位 MW
    bias_mw_per_hz：区域频率偏差系数 B（自然频率响应特性），单位 MW/Hz
    df_hz：频率偏差 f − fn（fn = 50 Hz），单位 Hz
    """
    return dp_tie_mw + bias_mw_per_hz * df_hz


def k1_rating(actual_mw_per_min: float, required_mw_per_min: float) -> float:
    """K1 调节速率评分（0-100）。

    正文公式：K1_score = min(100, 100 × K1_actual / K1_required)
    超额部分不加分（cap 100），低于要求按比例扣分。
    """
    if required_mw_per_min <= 0:
        return 0.0
    return clamp(actual_mw_per_min / required_mw_per_min * 100.0, 0.0, 100.0)


def k2_rating(actual_s: float, required_s: float) -> float:
    """K2 响应时间评分（0-100）。

    正文公式：K2_score = 100 × (1 − K2_actual / K2_limit)
    注意：分母是**限值**而非超额量——K2=5 s、限值 30 s 时得 83.3 分，
    不是"未超限即满分"。超过限值得 0 分。
    """
    if required_s <= 0:
        return 0.0
    return clamp((1.0 - max(0.0, actual_s) / required_s) * 100.0, 0.0, 100.0)


def k3_rating(actual_pct: float, required_pct: float) -> float:
    """K3 调节精度评分（0-100）。

    正文公式：K3_score = 100 × (1 − K3_actual / K3_limit)
    K3=2%、限值 3% 时得 33.3 分——这是 07 章「58.9 分不合格」的根因。
    """
    if required_pct <= 0:
        return 0.0
    return clamp((1.0 - max(0.0, actual_pct) / required_pct) * 100.0, 0.0, 100.0)


def composite_score(k1: float, k2: float, k3: float,
                    w1: float = W_K1, w2: float = W_K2, w3: float = W_K3) -> float:
    """综合评分 = 0.30×K1 + 0.20×K2 + 0.50×K3（正文 07 章默认权重）。

    口径说明：与考核月报一致，先把每个加权项保留 1 位小数再求和，
    因此 85/83.3/33.3 得 25.5 + 16.7 + 16.7 = 58.9（不取整则 58.8）。
    0.1 分的口径差异不改变「不合格」结论。
    """
    return round(round(w1 * k1, 1) + round(w2 * k2, 1) + round(w3 * k3, 1), 1)


# 区域参数（与正文 05 章「三份细则的 AGC 参数对照」表逐项一致）
REGION_PARAMS = {
    Region.HUADONG: {
        "k1_min_pn_per_min": 1.0,
        "k2_max_s": 60.0,
        "k3_max_pct": 3.0,
        "poll_period_s": 8.0,
        "cmd_deadband_mw": 0.3,
        "availability_min": 0.98,
        "compensation_mode": "capacity",
        "score_pass": 80.0,
    },
    Region.DONGBEI: {
        "k1_min_pn_per_min": 1.5,
        "k2_max_s": 30.0,
        "k3_max_pct": 3.0,
        "poll_period_s": 4.0,
        "cmd_deadband_mw": 0.1,
        "availability_min": 0.95,
        "compensation_mode": "mileage",
        "score_pass": 75.0,
    },
    Region.SHANXI: {
        "k1_min_pn_per_min": 1.0,
        "k2_max_s": 60.0,
        "k3_max_pct": 2.0,
        "poll_period_s": 8.0,
        "cmd_deadband_mw": 0.3,
        "availability_min": 0.98,
        "compensation_mode": "capacity",
        "score_pass": 80.0,
    },
}


@dataclass
class ScoreCard:
    """一次考核的 K1/K2/K3 单项分与综合分（可跨章复用）。"""
    region: str
    k1: float
    k2: float
    k3: float
    composite: float
    passed: bool


def score_card(k1_mw_per_s: float, k2_s: float, k3_pct: float,
               region: Region = Region.HUADONG,
               pn_mw: float = PN,
               k2_limit_s: float | None = None,
               k3_limit_pct: float | None = None) -> ScoreCard:
    """按正文 07 章公式算一张完整评分卡。

    k1_mw_per_s 以 MW/s 输入，内部换算为 Pn/min 后与区域要求比较。
    k2_limit_s / k3_limit_pct 为 None 时取区域细则值；显式传入可复现
    07 章「按储能通用 30 s 考核」的口径（细则上限 60 s，实际按 30 s 严考）。
    """
    p = REGION_PARAMS[region]
    k2_limit = p["k2_max_s"] if k2_limit_s is None else k2_limit_s
    k3_limit = p["k3_max_pct"] if k3_limit_pct is None else k3_limit_pct
    k1_required_mw_per_s = p["k1_min_pn_per_min"] * pn_mw / 60.0
    k1 = k1_rating(k1_mw_per_s, k1_required_mw_per_s)
    k2 = k2_rating(k2_s, k2_limit)
    k3 = k3_rating(k3_pct, k3_limit)
    comp = composite_score(k1, k2, k3)
    return ScoreCard(
        region=region.value,
        k1=round(k1, 1),
        k2=round(k2, 1),
        k3=round(k3, 1),
        composite=round(comp, 1),
        passed=comp >= p["score_pass"],
    )


def capacity_revenue(score: float, p_avail_mw: float = PN,
                     price_yuan_per_mw_month: float = CAP_PRICE_YUAN_PER_MW_MONTH,
                     availability: float = AVAILABILITY_RATE) -> float:
    """容量补偿月收入（正文 07 章）。

    月收入 = 可调容量 × 补偿单价 × 投运率 × 评分系数（评分系数 = score/100）
    基准示例：100 MW × 10 元/MW·月 × 0.98 × 0.80 = 784 元
    """
    return p_avail_mw * price_yuan_per_mw_month * availability * (score / 100.0)


def mileage_revenue(score: float, mileage_mw: float,
                    price_yuan_per_mw: float = MILE_PRICE_YUAN_PER_MW) -> float:
    """里程补偿月收入（正文 07 章）。

    月收入 = 累计调节里程 × 里程单价 × 评分系数（评分系数 = score/100）
    基准示例：50000 MW × 0.5 元/MW × 0.80 = 20000 元
    """
    return mileage_mw * price_yuan_per_mw * (score / 100.0)


def k2_chain_budget(poll_period_s: float = 4.0,
                    ems_parse_s: float = 0.5,
                    alloc_calc_s: float = 0.5,
                    ems_to_pcs_s: float = 0.5,
                    pcs_response_s: float = 1.0,
                    reach_threshold_s: float = 3.0,
                    k2_limit_s: float = 30.0) -> dict:
    """K2 端到端时序预算（正文 04 章「K2 的时间预算」表逐项对应）。

    默认轮询 4s（东北配置）、K2 限值 30s：
    合计 = 4+0.5+0.5+0.5+1+3 = 9.5s，余量 20.5s（68.3%），pass=True。
    返回 margin_s/margin_pct/pass 供 04 章 example 与 tests 复用，
    避免 example 层自复制一套 k2_budget_check。
    """
    chain = {
        "104轮询（最差=轮询周期）": poll_period_s,
        "EMS解析+校验": ems_parse_s,
        "死区判定+分配计算": alloc_calc_s,
        "EMS→PCS下发": ems_to_pcs_s,
        "PCS内部响应": pcs_response_s,
        "出力到达阈值": reach_threshold_s,
    }
    total = sum(chain.values())
    margin = k2_limit_s - total
    return {
        "chain_detail": chain,
        "total_s": round(total, 2),
        "k2_limit_s": k2_limit_s,
        "margin_s": round(margin, 2),
        "margin_pct": round((1 - total / k2_limit_s) * 100, 1),
        "pass": total <= k2_limit_s,
        "biggest_risk": max(chain, key=chain.get),
    }


def check_ramp_rate_multilevel(pcs_ramp: float, ems_safety_limit: float,
                               alloc_synthesis: float, k1_required: float,
                               margin: float = 1.2) -> dict:
    """三级限速校验（正文 02 章）。

    实际可用 K1 = min(PCS 硬件, EMS 安全限速, 分配模块合成)，逐层定位瓶颈。
    """
    effective = min(pcs_ramp, ems_safety_limit, alloc_synthesis)
    target = k1_required * margin
    bottleneck = None
    if effective < target:
        if pcs_ramp < target:
            bottleneck = "PCS硬件"
        elif ems_safety_limit < target:
            bottleneck = "EMS安全限速"
        else:
            bottleneck = "分配模块合成"
    return {
        "k1_effective": round(effective, 3),
        "target_with_margin": round(target, 3),
        "pass": effective >= target,
        "bottleneck": bottleneck,
    }


def should_track(p_new: float, p_prev: float, deadband_mw: float) -> bool:
    """指令死区判定（正文 02 章「指令死区——K2 的头号杀手」）。

    变化量 |p_new − p_prev| ≥ deadband_mw 才跟踪；小于死区判为
    "变化太小不跟踪"，导致 K2 被统计为超时不合格。
    """
    return abs(p_new - p_prev) >= deadband_mw


@dataclass
class Resource:
    """AGC 受控资源（正文 03 章四种分配策略）。

    soc：储能 SOC ∈ [0,1]；非储能填 -1.0（无 SOC，哨兵值，用于区分储能）。
    """
    name: str
    pn: float            # 额定功率 (MW)
    p_current: float     # 当前出力 (MW)
    p_max: float         # 出力上限 (MW)
    p_min: float         # 出力下限（含 SOC 约束）(MW)
    ramp_rate: float     # 爬坡速率 (MW/s)
    cost_up: float       # 上调边际成本 (元/MW)
    cost_down: float     # 下调边际成本 (元/MW)
    soc: float = -1.0    # 储能 SOC（非储能 -1.0）


def allocate_by_capacity(resources: List, dp: float) -> dict:
    """按额定容量等比例分配（正文 03 章策略一）。

    边界：总额定容量为 0 时返回零分配（不抛异常）。
    """
    total_pn = sum(r.pn for r in resources)
    if total_pn <= 0:
        return {r.name: 0.0 for r in resources}
    return {r.name: dp * r.pn / total_pn for r in resources}


def allocate_by_available(resources: List, dp: float) -> dict:
    """按实时可调容量分配（正文 03 章策略二，方向感知）。

    dp > 0：按上调空间（p_max − p_current）；
    dp < 0：按下调空间（p_current − p_min）。
    边界：总可调空间为 0 时返回零分配（不抛异常，由调用方告警）。
    """
    if dp > 0:
        avail = {r.name: max(0.0, r.p_max - r.p_current) for r in resources}
    else:
        avail = {r.name: max(0.0, r.p_current - r.p_min) for r in resources}
    total = sum(avail.values())
    if total <= 0:
        return {r.name: 0.0 for r in resources}
    return {r.name: dp * avail[r.name] / total for r in resources}


def allocate_by_cost(resources: List, dp: float) -> dict:
    """按边际成本分配（正文 03 章策略三，上调场景：cost_up 低的优先）。

    边界：cost_up 并列时按传入顺序；总可调容量不足时按可调容量截断；
    dp <= 0（下调）不在本函数范围，直接返回零分配。
    """
    result = {r.name: 0.0 for r in resources}
    if dp <= 0:
        return result
    remaining = dp
    for r in sorted(resources, key=lambda r: r.cost_up):
        avail = max(0.0, r.p_max - r.p_current)
        alloc = min(avail, remaining)
        result[r.name] = alloc
        remaining -= alloc
        if remaining <= 0:
            break
    return result


def allocate_by_soc(resources: List, dp: float,
                    soc_low: float = 0.2, soc_high: float = 0.8) -> dict:
    """SOC 优先分配（正文 03 章策略四）。

    上调（dp>0）：SOC > soc_low 的储能优先放电；不足时风光按可调容量承担。
    下调（dp<0）：SOC < soc_high 的储能优先充电；不足时风光按可调空间承担。
    多个储能按 |soc − 0.5| 由近及远排序（中位回归偏好）。
    """
    storage = [r for r in resources if r.soc >= 0.0]
    others = [r for r in resources if r.soc < 0.0]
    result = {r.name: 0.0 for r in resources}
    remaining = dp

    if dp > 0:
        active = [s for s in storage if s.soc > soc_low]
    else:
        active = [s for s in storage if s.soc < soc_high]

    for s in sorted(active, key=lambda r: abs(r.soc - 0.5)):
        if dp > 0:
            avail = max(0.0, s.p_max - s.p_current)
            alloc = min(avail, remaining)
        else:
            avail = max(0.0, s.p_current - s.p_min)
            alloc = max(-avail, remaining)
        result[s.name] = alloc
        remaining -= alloc
        done = remaining <= 0.0 if dp > 0 else remaining >= 0.0
        if done:
            return result

    # 储能不够/不可用 → 风光按可调空间承担
    for name, v in allocate_by_available(others, remaining).items():
        result[name] = v
    return result


def dynamic_supplement(target_mw: dict, actual_mw: dict, resources: List,
                       threshold_mw: float = 0.5) -> dict:
    """动态补差（正文 03 章「动态补差逻辑」）。

    偏差 = Σ(目标 − 实际)；|偏差| >= threshold_mw 才触发补差，
    缺口按实时可调容量重分配（调用 allocate_by_available，方向由偏差正负决定）。
    低于门槛返回全零（不触发，避免频繁微调振荡）。
    threshold_mw 对应正文「补差门槛 <0.5% Pn」：100 MW 场站即 0.5 MW。
    """
    total_dev = sum(target_mw.get(r.name, 0.0) - actual_mw.get(r.name, 0.0)
                    for r in resources)
    if abs(total_dev) < threshold_mw:
        return {r.name: 0.0 for r in resources}
    return allocate_by_available(resources, total_dev)