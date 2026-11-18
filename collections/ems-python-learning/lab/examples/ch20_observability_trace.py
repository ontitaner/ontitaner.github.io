"""第 20 章最小闭环：告警生命周期、决策审计和 KPI。

输入：温度越限序列、限制链和运行统计
算法：延时/滞回/确认/自动关闭；约束审计；可用率/跟踪误差
输出：告警事件、可读审计、KPI
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.observability import (  # noqa: E402
    AlarmManager, AlarmRule, AlarmState, DecisionAudit, Limit, Severity,
    apply_limit_chain, availability, tracking_error,
)


def main():
    rule = AlarmRule("CELL_T_HIGH", "电芯温度高", Severity.MINOR,
                     raise_at=45, clear_at=42, on_delay_s=5, off_delay_s=10)
    alarms = AlarmManager([rule])
    for t in range(6):
        alarms.update(t, "舱1", "CELL_T_HIGH", 47)
    rec = alarms.active()[0]
    alarms.ack(8, rec.alarm_id, "值班员A")
    for t in range(10, 21):
        alarms.update(t, "舱1", "CELL_T_HIGH", 41)
    print(f"告警：产生={rec.t_raised}s，确认=8s，关闭={rec.t_closed}s，状态={rec.state.name}")
    assert rec.state is AlarmState.CLOSED and rec.t_raised == 5 and rec.t_closed == 20

    final, steps = apply_limit_chain(100, [Limit("BMS", -500, 80), Limit("防倒送", -500, 60)])
    audit = DecisionAudit(1, 1, 1.0, "10:00", "计划", [("计划", 100)], 100, steps, final,
                         0.35, 500, 80, {"pcc": "GOOD"}, "cfg-1", "ems-1", "接受", 58)
    print(audit.explain())
    assert final == 60 and audit.binding() == ["BMS", "防倒送"]

    avail = availability(86400, [(3600, 7200), (5400, 9000)])
    err = tracking_error([100, 100, 100], [98, 101, 80], tol_kw=5)
    print(f"可用率={avail:.2%}，最大跟踪误差={err.max_abs_kw:.0f} kW")
    assert abs(avail - (1 - 5400 / 86400)) < 1e-9 and err.max_abs_kw == 20
    print("自检通过")


if __name__ == "__main__":
    main()

