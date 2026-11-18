"""第17章模式对照：同一PCC过压场景，以统一时间轴比较定Q、定PF、Q-U和定电压AVC。

约定：Q>0 发出无功，Q<0 吸收无功。t2、t3 的当前电压同为 1.010 pu，
用于证明Q-U只看当前电压，而带积分的AVC还受历史误差影响。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.reactive import AvcController, QuDroopConfig, q_from_pf, qu_droop_kvar  # noqa: E402

TIMES = ("t0", "t1", "t2", "t3")
U_PU = (1.030, 1.020, 1.010, 1.010)
P_KW = (800.0, 800.0, 400.0, 400.0)


def pu_example():
    """110 kV PCC 的 (实际kV, 基准kV, 标幺值)。"""
    return [(u, 110.0, u / 110.0) for u in (107.8, 110.0, 112.2)]


def modes_example():
    """共同 t0～t3 场景的四种Q请求及“同U、不同历史”对照。"""
    fixed_q = [-300.0] * len(TIMES)  # 调度固定要求吸收 300 kvar
    pf_q = [q_from_pf(p, 0.95, -1) for p in P_KW]
    droop = QuDroopConfig(q_max_kvar=500, slope_kvar_per_pu=10_000, deadband_pu=0.01)
    droop_q = [qu_droop_kvar(u, droop) for u in U_PU]
    avc = AvcController(1.0, 8_000, 2_000)
    avc_q = [avc.update(u, 1.0, -500, 500).q_requested_kvar for u in U_PU]
    fresh = AvcController(1.0, 8_000, 2_000).update(1.010, 1.0, -500, 500).q_requested_kvar
    return fixed_q, pf_q, droop_q, avc_q, fresh


def main():
    assert [round(pu, 3) for _, _, pu in pu_example()] == [0.98, 1.0, 1.02]
    fixed_q, pf_q, droop_q, avc_q, fresh = modes_example()
    assert fixed_q == [-300.0] * 4
    assert [round(q, 1) for q in pf_q] == [-262.9, -262.9, -131.5, -131.5]
    assert [round(q, 1) for q in droop_q] == [-200.0, -100.0, 0.0, 0.0]
    assert [round(q, 1) for q in avc_q] == [-300.0, -260.0, -200.0, -220.0]
    assert round(fresh, 1) == -100.0
    print("共同场景：PCC过压，Q<0表示吸收无功")
    print("时刻  U(pu)  P(kW)  定Q     定PF    Q-U     AVC")
    for t, u, p, q0, qpf, qd, qa in zip(TIMES, U_PU, P_KW, fixed_q, pf_q, droop_q, avc_q):
        print(f"{t:>2}   {u:.3f}  {p:>5.0f}  {q0:>6.1f}  {qpf:>6.1f}  {qd:>6.1f}  {qa:>6.1f}")
    print(f"同为 U=1.010 pu：刚启动AVC输出 {fresh:.1f} kvar；经历t0/t1过压后，t2输出 {avc_q[2]:.1f} kvar")
    print("自检通过")


if __name__ == "__main__":
    main()

