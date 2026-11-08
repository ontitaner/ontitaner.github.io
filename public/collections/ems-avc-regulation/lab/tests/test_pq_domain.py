# @AI_GENERATED
"""一致性测试：P-Q 可行域 — 正文 02/03 章手算验证

正文 03.4 手算：3×5000 kVA PCS
P=[4500,4500,4000] kW → Q_available ≈ 6.2 Mvar
"""
from lab.ems_lab.pq_domain import q_available_under_p, joint_q_available


def test_q_available_single():
    assert abs(q_available_under_p(0, 1000) - 1000.0) < 1.0
    assert abs(q_available_under_p(800, 1000) - 600.0) < 1.0
    assert abs(q_available_under_p(900, 1000) - 435.89) < 1.0
    assert q_available_under_p(1000, 1000) == 0.0


def test_joint_q_agc_full():
    pcs = [
        {"id": "PCS1", "s_kva": 5000, "p_kw": 4500},
        {"id": "PCS2", "s_kva": 5000, "p_kw": 4500},
        {"id": "PCS3", "s_kva": 5000, "p_kw": 4000},
    ]
    r = joint_q_available(pcs)
    assert abs(r['q_neg_kvar'] - 7359.0) < 100.0
# @AI_GENERATED: end