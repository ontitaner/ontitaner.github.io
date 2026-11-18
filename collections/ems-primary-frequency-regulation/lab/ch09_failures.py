# @AI_GENERATED
"""第九章实验：常见误区复现验证。

用代码复现第 09 章中讨论的几个典型坑：
1. 死区类型选错的出力差异
2. 冻结数据导致状态机误闭锁
3. 方向约定不一致导致考核不合格
"""
from freq_core import (
    DeadbandMode, FreqRegStateMachine, FreqSample, FreqRegStatus,
    PrimaryFreqConfig, primary_freq_delta, detect_frozen, assess_event,
    print_summary,
)


def _mistake_1_deadband_mode() -> dict:
    """坑1：死区类型选错——用截断型替代连续型。"""
    target_cfg = PrimaryFreqConfig(deadband_mode=DeadbandMode.SHIFT,
                                    deadband_hz=0.06, droop_ratio=0.03,
                                    p_rated_mw=100.0)
    actual_cfg = PrimaryFreqConfig(deadband_mode=DeadbandMode.CUT,
                                    deadband_hz=0.06, droop_ratio=0.03,
                                    p_rated_mw=100.0)
    f_check = 49.90
    th_target, _ = primary_freq_delta(f_check, 50.0, 100.0, target_cfg)
    th_actual, _ = primary_freq_delta(f_check, 50.0, 100.0, actual_cfg)

    return {
        "频率 (Hz)": f_check,
        "期望出力_连续型 (MW)": th_target,
        "实际出力_截断型 (MW)": th_actual,
        "少发 (MW)": th_target - th_actual,
        "后果": "考核不合格" if th_actual < th_target * 0.6 else "可勉强通过",
    }


def _mistake_2_data_frozen() -> dict:
    """坑2：频率数据冻结导致误闭锁。"""
    cfg = PrimaryFreqConfig(deadband_hz=0.05, droop_ratio=0.03,
                            p_rated_mw=100.0)
    sm = FreqRegStateMachine(cfg)
    sm.arm()

    events = []
    # 正常波动
    normal = [50.00, 50.01, 49.99, 50.00, 49.92, 49.92]
    for i, f in enumerate(normal):
        events.append(sm.step(FreqSample(ts=float(i), f_hz=f)))

    status_before = events[-1][0]
    # 冻结 5 帧
    for i in range(5):
        fs = FreqSample(ts=float(len(normal) + i), f_hz=49.92)
        events.append(sm.step(fs))
    status_after = events[-1][0]

    return {
        "冻结前状态": status_before.value,
        "冻结后状态": status_after.value,
        "后果": "正确检测并闭锁" if status_after is FreqRegStatus.BLOCKED else "未检测到冻结",
    }


def _mistake_3_direction_reversal() -> dict:
    """坑3：方向约定不一致——PCS 把"正值=放电"理解为"正值=充电"。"""
    # 低频事件理论出力应为正
    w_theory = 50.0  # MWh
    # PCS 反向执行
    w_actual = -40.0  # MWh

    result = assess_event(w_theory, w_actual)
    return {
        "理论积分 (MWh)": w_theory,
        "实际积分 (MWh)": w_actual,
        "符号匹配": result["symbol_match"],
        "完成率": result["completion_rate"],
        "通过": result["passed"],
        "后果": "符号不匹配 → 直接不合格" if not result["passed"] else "通过",
    }


def _mistake_4_hardcoded_k() -> dict:
    """坑4：K 值硬编码——Pn 变更后 K 未同步更新。"""
    old_k = 100.0 / (0.03 * 50.0)
    new_pn = 120.0
    new_k_correct = new_pn / (0.03 * 50.0)

    delta_f = -0.10
    delta_p_wrong = -old_k * delta_f
    delta_p_correct = -new_k_correct * delta_f

    return {
        "旧K (MW/Hz)": old_k,
        "正确K (MW/Hz)": new_k_correct,
        "错误出力 (MW)": delta_p_wrong,
        "正确出力 (MW)": delta_p_correct,
        "偏差率": abs(delta_p_wrong - delta_p_correct) / abs(delta_p_correct),
    }


def _test_all():
    m1 = _mistake_1_deadband_mode()
    assert abs(m1["少发 (MW)"]) > 3.0, "死区类型差异量应与死区×K 一致"

    m2 = _mistake_2_data_frozen()
    assert m2["冻结后状态"] == "blocked", "冻结应触发闭锁"

    m3 = _mistake_3_direction_reversal()
    assert not m3["通过"], "符号不匹配应判定不合格"

    m4 = _mistake_4_hardcoded_k()
    assert m4["偏差率"] > 0.1, "Pn 变更 20% K 偏差应明显"


def main():
    print_summary("坑1：死区类型选错", _mistake_1_deadband_mode())
    print_summary("坑2：频率数据冻结", _mistake_2_data_frozen())
    print_summary("坑3：方向约定反转", _mistake_3_direction_reversal())
    print_summary("坑4：K 值硬编码", _mistake_4_hardcoded_k())
    _test_all()
    print("\n✓ 第九章实验自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end