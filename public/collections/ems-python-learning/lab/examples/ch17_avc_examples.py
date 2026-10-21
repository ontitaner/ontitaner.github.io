"""第 17 章示例：用课程真实实现重算电压灵敏度、Q-U 下垂、P-Q 投影和简化 AVC 子站闭环。

运行（在 lab 目录下）：
    python examples/ch17_avc_examples.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.reactive import (  # noqa: E402
    AvcController,
    QuDroopConfig,
    project_pq,
    qu_droop_kvar,
    voltage_rise_v,
)


def voltage_example():
    """17.2：110 kV、R=6.5 Ω、X=20 Ω 时的电压抬升分量（kV）。"""
    p_part = voltage_rise_v(50_000, 0, 6.5, 20, 110) / 1000
    q_part = voltage_rise_v(0, 20_000, 6.5, 20, 110) / 1000
    return p_part, q_part, p_part + q_part


def droop_example():
    """17.5：连续型死区 Q-U 下垂，返回 (U, Q)。"""
    cfg = QuDroopConfig(q_max_kvar=500, slope_kvar_per_pu=10_000, deadband_pu=0.01)
    return [(u, qu_droop_kvar(u, cfg)) for u in (1.005, 0.97, 0.93, 1.04)]


def projection_example():
    """17.8：S=1000 kVA、请求 (900, 600) 的三种投影。"""
    return {mode: project_pq(900, 600, 1000, mode) for mode in ("p_priority", "q_priority", "proportional")}


def avc_cycle_example():
    """17.9：PCC 过压时，AVC PI 请求吸收无功；P=900 kW 使 Q 受能力圆限制。

    简化电网：U[k+1] = U[k] + 0.00004 × Q_executed[k]；Q<0 会降低电压。
    第 0～2 拍 P=900，采用有功优先；第 3 拍起 P=600，释放更多 Q 裕度。
    """
    controller = AvcController(u_target_pu=1.0, kp_kvar_per_pu=12_000, ki_kvar_per_pu_s=4_000)
    u = 1.0300
    rows = []
    for k, p_req in enumerate((900.0, 900.0, 900.0, 600.0, 600.0, 600.0)):
        # 先用当前 P 和 S 算 Q 的可行上下限，避免 PI 请求超出能力后积分累积。
        q_cap = (1000.0**2 - p_req**2) ** 0.5
        pi = controller.update(u, dt_s=1.0, q_min_kvar=-q_cap, q_max_kvar=q_cap)
        projected = project_pq(p_req, pi.q_requested_kvar, 1000.0, "p_priority")
        q_exec = projected.q_kvar
        rows.append((k, u, p_req, pi.q_requested_kvar, q_exec, q_cap, controller.integral_kvar, pi.saturated))
        u += 0.00004 * q_exec
    return rows


def main():
    p_part, q_part, total = voltage_example()
    assert (round(p_part, 2), round(q_part, 2), round(total, 2)) == (2.95, 3.64, 6.59)
    assert [(u, round(q, 1)) for u, q in droop_example()] == [(1.005, 0.0), (0.97, 200.0), (0.93, 500), (1.04, -300.0)]
    p = projection_example()
    assert (round(p["p_priority"].p_kw, 1), round(p["p_priority"].q_kvar, 1)) == (900.0, 435.9)
    print("AVC 闭环：电压目标 1.000 pu；电压高时吸收无功（Q<0）；S=1000 kVA")
    print("拍  U_PCC    P请求  Q请求   Q执行   Q上限   积分   顶住")
    rows = avc_cycle_example()
    for k, u, p_req, q_req, q_exec, q_cap, integ, saturated in rows:
        print(f"{k:>2}  {u:.4f}  {p_req:>5.0f}  {q_req:>6.1f}  {q_exec:>6.1f}  {q_cap:>6.1f}  "
              f"{integ:>6.1f}  {'是' if saturated else '否'}")
    assert round(rows[0][4], 1) == -435.9 and rows[0][7]
    assert rows[3][5] == 800.0 and rows[-1][1] < rows[0][1]
    print("自检通过")


if __name__ == "__main__":
    main()

