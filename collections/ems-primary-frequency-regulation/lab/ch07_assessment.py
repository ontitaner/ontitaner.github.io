# @AI_GENERATED
"""第七章实验：积分电量计算与考核判定。

模拟一次完整调频事件：频率阶跃 → 死区穿越 → 动作维持 → 频率恢复。
用梯形法与矩形法对比积分电量，判定 F1/F2。
"""
import math
from freq_core import (
    DeadbandMode, FreqSample, PrimaryFreqConfig,
    integral_energy, assess_event, primary_freq_delta,
    simulate_pcs_response, print_summary,
)


def _simulate_full_event(delay_s: float = 0.2, tau_s: float = 0.3,
                          ramp_rate: float = 50.0) -> dict:
    """生成一次完整调频事件数据（频率阶跃）。"""
    cfg = PrimaryFreqConfig(deadband_hz=0.05, droop_ratio=0.03,
                            p_rated_mw=100.0, limit_up_ratio=0.10,
                            limit_down_ratio=0.10,
                            deadband_mode=DeadbandMode.SHIFT)

    dt_s = 0.1
    t_steady = 5.0
    total_s = 20.0
    n = int(total_s / dt_s)

    # 频率场景：50.00 → (2s)阶跃至 49.88 → 维持 8s → 恢复 50.00
    freq_pts = []
    p_theory = []
    for i in range(n):
        t = i * dt_s
        if t < 2.0:
            f = 50.00
        elif t < 10.0:
            f = 49.88
        else:
            f = 50.00
        fs = FreqSample(ts=t, f_hz=f)
        freq_pts.append(fs)
        th, _ = primary_freq_delta(f, 30.0, 100.0, cfg)
        p_theory.append(th)

    p_actual = simulate_pcs_response(p_theory, delay_s, tau_s, ramp_rate)

    # 积分
    w_rect_t, w_rect_a = integral_energy(p_theory, p_actual, dt_s, method="rect")
    w_trap_t, w_trap_a = integral_energy(p_theory, p_actual, dt_s, method="trapezoid")

    # 考核
    assess_rect = assess_event(w_rect_t, w_rect_a)
    assess_trap = assess_event(w_trap_t, w_trap_a)

    return {
        "W_theory_rect (MWh)": w_rect_t,
        "W_actual_rect (MWh)": w_rect_a,
        "W_theory_trap (MWh)": w_trap_t,
        "W_actual_trap (MWh)": w_trap_a,
        "完成率_rect": assess_rect["completion_rate"],
        "完成率_trap": assess_trap["completion_rate"],
        "考核结果_rect": "合格" if assess_rect["passed"] else f"不合格({assess_rect['reason']})",
        "考核结果_trap": "合格" if assess_trap["passed"] else f"不合格({assess_trap['reason']})",
    }


def _test_assessment():
    result = _simulate_full_event()
    cr = result["完成率_trap"]
    assert 0.5 < cr < 1.5, f"完成率应在合理范围，实际 {cr:.2%}"

    # 符号不匹配应判定不合格
    mismatch = assess_event(10.0, -5.0)
    assert not mismatch["passed"]
    assert mismatch["symbol_match"] is False


def main():
    result = _simulate_full_event()
    print_summary("积分电量与考核判定", result)
    _test_assessment()
    print("\n✓ 第七章实验自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end