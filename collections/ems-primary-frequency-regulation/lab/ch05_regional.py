# @AI_GENERATED
"""第五章实验：不同区域细则参数对比。

统一用 100MW 储能，跑华东→东北→山西三套参数，
对比频差-出力曲线差异。
"""
from freq_core import (
    DeadbandMode, IntegrationMode, PrimaryFreqConfig,
    primary_freq_delta, print_summary,
)


def _build_regional() -> dict:
    return {
        "华东": PrimaryFreqConfig(
            deadband_hz=0.06, droop_ratio=0.03,
            deadband_mode=DeadbandMode.SHIFT,
            limit_up_ratio=0.10, limit_down_ratio=0.10,
            p_rated_mw=100.0, region="华东",
            integration_mode=IntegrationMode.EVENT,
        ),
        "东北": PrimaryFreqConfig(
            deadband_hz=0.05, droop_ratio=0.02,
            deadband_mode=DeadbandMode.CUT,
            limit_up_ratio=0.10, limit_down_ratio=0.10,
            p_rated_mw=100.0, region="东北",
            integration_mode=IntegrationMode.PERIOD,
        ),
        "山西": PrimaryFreqConfig(
            deadband_hz=0.05, droop_ratio=0.025,
            deadband_mode=DeadbandMode.SHIFT,
            limit_up_ratio=0.08, limit_down_ratio=0.15,
            p_rated_mw=100.0, region="山西",
            integration_mode=IntegrationMode.EVENT,
        ),
    }


def _compare_at_point(f_hz: float) -> dict:
    configs = _build_regional()
    result = {}
    for region, cfg in configs.items():
        theory, exec_p = primary_freq_delta(f_hz, 50.0, 100.0, cfg)
        result[f"{region} 理论 (MW)"] = theory
        result[f"{region} 可执行 (MW)"] = exec_p
    return result


def _test_regional():
    configs = _build_regional()
    # 华东用连续型、东北用截断型 → 49.90Hz 东北出力 > 华东
    th_east, _ = primary_freq_delta(49.90, 50.0, 100.0, configs["华东"])
    th_ne, _ = primary_freq_delta(49.90, 50.0, 100.0, configs["东北"])
    # 东北 δ=2%(K更大) 且用截断型 → 理论上出力应更大
    assert th_ne >= th_east, f"东北理论出力({th_ne:.2f})应≥华东({th_east:.2f})"


def main():
    configs = _build_regional()
    print("区域细则参数对比:")
    for region, cfg in configs.items():
        print(f"  {region}: deadband={cfg.deadband_hz}Hz, droop={cfg.droop_ratio:.1%}, "
              f"K={cfg.k:.1f}MW/Hz, mode={cfg.deadband_mode.value}, "
              f"integration={cfg.integration_mode.value}")

    result = _compare_at_point(49.90)
    print_summary("49.90 Hz 出力对比", result)

    _test_regional()
    print("\n✓ 第五章实验自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end