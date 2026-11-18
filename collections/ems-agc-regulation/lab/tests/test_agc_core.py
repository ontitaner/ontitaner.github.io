# @AI_GENERATED
"""lab 三层一致性校验：正文手算 = 模块层行为（ems_lab.agc_core）。

直接运行：python lab/tests/test_agc_core.py
或       ：pytest lab/tests/
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from ems_lab.agc_core import (  # noqa: E402
    PN, W_K1, W_K2, W_K3, Region, clamp, ace,
    k1_rating, k2_rating, k3_rating, composite_score, score_card,
    capacity_revenue, mileage_revenue, k2_chain_budget, check_ramp_rate_multilevel,
    should_track, Resource, allocate_by_capacity, allocate_by_available,
    allocate_by_cost, allocate_by_soc, dynamic_supplement,
)

B = 1000.0  # 01 章教学示例频率偏差系数


def test_ace_ch01():
    """01 章唯一业务事件：邻省机组跳闸，ACE = +50 + 1000×(-0.10) = -50 MW。"""
    assert ace(50.0, B, -0.10) == -50.0
    assert B * (-0.10) == -100.0  # 频率项分量


def test_ace_sign_rule():
    """01 章符号规则（模块泛化校验，非正文示例）：ACE 正负对应出力方向。"""
    assert ace(-40.0, B, -0.03) == -70.0   # 两项同负 → ACE 更负
    assert ace(60.0, B, 0.02) == 80.0      # 两项同正 → ACE 更正


def test_clamp():
    assert clamp(-5.0, 0.0, 100.0) == 0.0
    assert clamp(150.0, 0.0, 100.0) == 100.0
    assert clamp(42.0, 0.0, 100.0) == 42.0


def test_k1_k2_k3_ch07():
    """07 章评分卡原始分：85 / 83.3 / 33.3（正文展示保留 1 位，模块返回完整精度）。"""
    assert abs(k1_rating(0.85 * PN / 60, 1.0 * PN / 60) - 85.0) < 0.01
    assert round(k2_rating(5.0, 30.0), 1) == 83.3
    assert round(k3_rating(2.0, 3.0), 1) == 33.3


def test_composite_ch07():
    """07 章综合分 58.9（不合格），权重和为 1。

    口径：先按完整精度加权项各保留 1 位再求和
    （0.30×85=25.5，0.20×250/3=16.7，0.50×100/3=16.7 → 58.9）。
    """
    k1, k2, k3 = 85.0, 250.0 / 3, 100.0 / 3  # 83.333... / 33.333... 完整精度
    assert abs(composite_score(k1, k2, k3) - 58.9) < 0.01
    assert abs(W_K1 + W_K2 + W_K3 - 1.0) < 1e-9


def test_score_card_ch07():
    card = score_card(0.85 * PN / 60, 5.0, 2.0, Region.HUADONG, k2_limit_s=30.0)
    assert abs(card.composite - 58.9) < 0.01
    assert card.passed is False


def test_revenue_ch07():
    """07 章补偿基准：容量 784 元、里程 20000 元。"""
    assert abs(capacity_revenue(80.0) - 784.0) < 0.01
    assert abs(mileage_revenue(80.0, 50000.0) - 20000.0) < 0.01


def test_k2_chain_budget_ch04():
    """04 章 K2 时序预算：4+0.5+0.5+0.5+1+3 = 9.5 s。"""
    r = k2_chain_budget(4.0)
    assert abs(r["total_s"] - 9.5) < 0.01
    assert r["biggest_risk"] == "104轮询（最差=轮询周期）"


def test_ramp_ch02():
    """02 章三级限速：min(1.5, 0.5, 1.2)=0.5 < 目标 1.2，瓶颈 EMS 安全限速。"""
    r = check_ramp_rate_multilevel(1.5, 0.5, 1.2, 1.0)
    assert abs(r["k1_effective"] - 0.5) < 1e-9
    assert r["pass"] is False
    assert r["bottleneck"] == "EMS安全限速"


def test_should_track_ch02():
    """02 章指令死区逐拍追踪：|p_new − p_prev| >= deadband 才跟踪（等于算跟踪）。"""
    # t=0 初始无变化
    assert should_track(100.0, 100.0, 2.0) is False
    # t=1 恰好等于死区边界 → 跟踪
    assert should_track(102.0, 100.0, 2.0) is True
    # t=2 连续小步长 1.2 < 2.0 → 不跟踪（K2 头号杀手）
    assert should_track(101.2, 100.0, 2.0) is False
    # t=3 反向同幅 → 跟踪
    assert should_track(98.0, 100.0, 2.0) is True


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
        except Exception:
            failed += 1
            print(f"  ✗ {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} 通过")
    sys.exit(1 if failed else 0)