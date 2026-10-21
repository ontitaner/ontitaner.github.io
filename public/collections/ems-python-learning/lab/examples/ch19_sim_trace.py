"""第 19 章最小闭环：负荷突降→仿真对象→防倒送断言→证据。

输入：800→300 kW 负荷突降、储能原请求 600 kW
算法：run 场景仿真；longest_excursion/window/power_balance 断言
输出：倒送持续时间、稳态偏差、平衡残差和 PASS/FAIL
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.sim import (  # noqa: E402
    Scenario, check_le, constant, evidence, longest_excursion_s,
    power_balance_residual_kw, run, step_profile, window,
)


def main():
    scenario = Scenario("教学 S1", t_end_s=30, load_kw=step_profile(15, 800, 300))
    trace = run(scenario)
    checks = [
        check_le("倒送持续时间", longest_excursion_s(trace.t, trace.p_pcc, 0, 10), 2.0, "倒送≤2s"),
        check_le("稳态偏差", max(abs(p + 30) for p in window(trace.t, trace.p_pcc, 20)), 15, "稳态偏差≤15kW"),
        check_le("功率平衡残差", power_balance_residual_kw(trace), 1e-6, "平衡残差≤1e-6kW"),
    ]
    report = evidence(trace, checks)
    print(f"倒送持续：{longest_excursion_s(trace.t, trace.p_pcc, 0, 10):.2f} s")
    print(f"稳态最大偏差：{max(abs(p + 30) for p in window(trace.t, trace.p_pcc, 20)):.2f} kW")
    print(f"功率平衡残差：{power_balance_residual_kw(trace):.2e} kW")
    print(f"结论：{report['verdict']}")
    assert report["verdict"] == "PASS"
    print("自检通过")


if __name__ == "__main__":
    main()

