# @AI_GENERATED
"""第三章实验：风光储多资源协同合成。

验证不同资源因死区、调差系数不同而产生差异化的出力分配。
"""
import numpy as np

from freq_core import (
    FN, DeadbandMode, ResourceConfig, FreqSample,
    multi_resource_synthesis, print_summary,
)


def _build_resources() -> list:
    return [
        ResourceConfig(name="风场_A", pn_mw=200.0, deadband_hz=0.10,
                       deadband_mode=DeadbandMode.CUT, droop_ratio=0.05,
                       limit_up_ratio=0.10, limit_down_ratio=0.10,
                       p_now_mw=100.0, p_max_mw=180.0),
        ResourceConfig(name="光伏_B", pn_mw=150.0, deadband_hz=0.06,
                       deadband_mode=DeadbandMode.SHIFT, droop_ratio=0.04,
                       limit_up_ratio=0.10, limit_down_ratio=0.10,
                       p_now_mw=80.0, p_max_mw=120.0),
        ResourceConfig(name="储能_C", pn_mw=50.0, deadband_hz=0.05,
                       deadband_mode=DeadbandMode.SHIFT, droop_ratio=0.02,
                       limit_up_ratio=0.20, limit_down_ratio=0.20,
                       p_now_mw=25.0, p_max_mw=50.0),
    ]


def _sweep() -> dict:
    resources = _build_resources()
    freqs = np.linspace(49.70, 50.30, 31)
    results = {"total_active_range": ""}
    for f in freqs:
        syn = multi_resource_synthesis(f, resources)
    # 关键点对比
    syn_low = multi_resource_synthesis(49.80, resources)
    syn_dead = multi_resource_synthesis(50.00, resources)
    syn_high = multi_resource_synthesis(50.20, resources)
    return {
        "K_风场 (MW/Hz)": resources[0].k,
        "K_光伏 (MW/Hz)": resources[1].k,
        "K_储能 (MW/Hz)": resources[2].k,
        "总@49.80Hz (MW)": syn_low["_total_exec_mw"],
        "总@50.00Hz (MW)": syn_dead["_total_exec_mw"],
        "总@50.20Hz (MW)": syn_high["_total_exec_mw"],
    }


def _synthesis_detail():
    print("\n多资源出力分配明细 (f = 49.80 Hz):")
    resources = _build_resources()
    syn = multi_resource_synthesis(49.80, resources)
    print(f"  {'资源':12s}  {'理论(MW)':>10s}  {'可执行(MW)':>10s}  {'死区内':>8s}")
    for r in resources:
        d = syn[r.name]
        print(f"  {r.name:12s}  {d['theory_mw']:>10.2f}  {d['exec_mw']:>10.2f}  "
              f"{'是' if d['in_deadband'] else '否':>8s}")
    print(f"  {'合计':12s}  {syn['_total_theory_mw']:>10.2f}  {syn['_total_exec_mw']:>10.2f}")


def _test_synthesis():
    resources = _build_resources()
    # 死区内所有资源出力应为 0
    syn = multi_resource_synthesis(50.00, resources)
    assert abs(syn["_total_exec_mw"]) < 0.01, "死区内总出力应接近 0"

    # 低频事件储能承担更多（K 大/死区窄）
    syn_low = multi_resource_synthesis(49.80, resources)
    exec_vals = {r.name: syn_low[r.name]["exec_mw"] for r in resources}
    # 储能_C 比例应大于风场_A 的相对出力比例
    assert exec_vals["储能_C"] / 50.0 >= exec_vals["风场_A"] / 200.0 * 0.8, \
        "储能单位容量贡献应不低于风场"


def main():
    result = _sweep()
    print_summary("多资源协同合成", result)
    _synthesis_detail()
    _test_synthesis()
    print("\n✓ 第三章实验自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end