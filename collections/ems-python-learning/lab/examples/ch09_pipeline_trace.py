"""第 09 章最小闭环：一个 EMS 控制周期的对象追踪。

输入：BMS 能力 800 kW、AGC 900 kW、49.90 Hz、初始输出 700 kW
算法：采集→状态→策略→仲裁→约束→Ramp→下发→反馈
输出：每个阶段的关键字段和最终命令
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.datapoint import Measurement, Quality  # noqa: E402
from ems_lab.frequency import PrimaryFrequencyConfig  # noqa: E402
from ems_lab.pipeline import (  # noqa: E402
    AGC_TARGET, BMS_CHG, BMS_DIS, BMS_SOC, METER_F, METER_P, PCS_P,
    AgcStrategy, Capability, ControlPipeline, PipelineConfig,
    PrimaryFrequencyStrategy,
)


def good(name, value, t, unit="kW"):
    return Measurement(name, value, unit, Quality.GOOD, t, t)


def site(t):
    return {
        BMS_CHG: good(BMS_CHG, 1000, t), BMS_DIS: good(BMS_DIS, 800, t),
        BMS_SOC: good(BMS_SOC, 0.5, t, ""), PCS_P: good(PCS_P, 0, t),
        METER_P: good(METER_P, -500, t), METER_F: good(METER_F, 49.90, t, "Hz"),
        AGC_TARGET: good(AGC_TARGET, 900, t),
    }


def main():
    pfr = PrimaryFrequencyConfig(1000, 0.02, 0.03, 0.10)
    pcs = __import__("ems_lab.pipeline", fromlist=["MockPcs"]).MockPcs(1000)
    pipe = ControlPipeline(PipelineConfig(p_rated_kw=1000, dt_s=0.2, ramp_kw_per_s=1000),
                           [AgcStrategy(), PrimaryFrequencyStrategy(pfr)], pcs,
                           clock=iter([0.0, 0.02]).__next__, p_initial_kw=700)
    rec = pipe.run_cycle(site(100), now=100)
    log = rec.as_log()
    print("①采集/校验：GOOD")
    print(f"②策略：AGC=900 kW，PFR=70 kW")
    print(f"③合成：{log['combined_kw']:.0f} kW")
    print(f"④约束：{log['constrained_kw']:.0f} kW，原因={log['active_constraints']}")
    print(f"⑤Ramp/下发：{log['final_kw']:.0f} kW，实际={log['p_actual_kw']:.0f} kW")
    assert abs(float(log['combined_kw']) - 970) < 1e-6
    assert abs(float(log['constrained_kw']) - 800) < 1e-6
    assert abs(float(log['final_kw']) - 800) < 1e-6
    assert log['accepted']
    print("自检通过")


if __name__ == "__main__":
    main()

