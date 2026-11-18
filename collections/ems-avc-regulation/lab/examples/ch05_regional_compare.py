# @AI_GENERATED
"""ch05 示例：同一 AVC 在江苏 vs 山西的考核差异

主线场景：50MW/100MWh 储能电站，假设两地各投一个项目
"""
from lab.ems_lab.regional import get_rule
from lab.ems_lab.deadband import Deadband


def main():
    print("跨省 AVC 细则差异  [主线: 50MW/100MWh 储能电站]\n")

    for province in ["江苏", "山西"]:
        rule = get_rule(province)
        deadband = Deadband(center=116.0, half_width=rule.voltage_deadband_kv)

        test_u = 116.6
        err = deadband.apply(test_u)

        print(f"--- {province} ---")
        print(f"  死区:        ±{rule.voltage_deadband_kv} kV")
        print(f"  合格范围:    ±{rule.voltage_band_kv} kV")
        print(f"  采样间隔:    {rule.sample_interval_s}s")
        print(f"  测量点:      {rule.measure_point}")
        print(f"  含无功电量考核: {'是' if rule.include_reactive_energy else '否'}")
        print(f"  U={test_u} kV → 死区误差={err:.2f} kV → {'动作' if err != 0 else '不动作'}")

        compatible = rule.voltage_deadband_kv <= rule.voltage_band_kv
        print(f"  死区 ≤ 合格范围: {'√ 合规链完整' if compatible else '⚠ 合规链断裂'}")
        print()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end