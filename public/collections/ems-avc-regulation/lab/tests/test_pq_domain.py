# @AI_GENERATED
"""一致性测试：P-Q 可行域 — 正文 02.6 / 03.4 手算验证

02.6 手算（单台 S=1000 kVA，P 优先）：
  P=0    → Q_available = 1000 kvar
  P=600  → Q_available = 800 kvar
  P=800  → Q_available = 600 kvar
  P=900  → Q_available = 435.9 kvar（正文四舍五入 436）
  P=1000 → Q_available = 0

03.4 手算（3×5000 kVA 联合，P=[4500,4500,4000] kW）：
  Q_available = 2×sqrt(5000²−4500²) + sqrt(5000²−4000²) = 7358.9 kvar
"""
from lab.ems_lab.pq_domain import q_available_under_p, joint_q_available


def test_q_available_single():
    assert abs(q_available_under_p(0, 1000) - 1000.0) < 0.5
    assert abs(q_available_under_p(600, 1000) - 800.0) < 0.5
    assert abs(q_available_under_p(800, 1000) - 600.0) < 0.5
    assert abs(q_available_under_p(900, 1000) - 435.9) < 0.5
    assert q_available_under_p(1000, 1000) == 0.0


def test_joint_q_agc_full():
    pcs = [
        {"id": "PCS1", "s_kva": 5000, "p_kw": 4500},
        {"id": "PCS2", "s_kva": 5000, "p_kw": 4500},
        {"id": "PCS3", "s_kva": 5000, "p_kw": 4000},
    ]
    r = joint_q_available(pcs)
    assert abs(r['q_pos_kvar'] - 7358.9) < 0.5
    assert abs(r['q_neg_kvar'] - 7358.9) < 0.5
    assert len(r['details']) == 3
# @AI_GENERATED: end