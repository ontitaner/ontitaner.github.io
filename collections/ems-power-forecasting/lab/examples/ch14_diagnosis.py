# @AI_GENERATED
"""第 14 章端到端演示：预测偏差根因诊断（四类根因反推）。

运行：python examples/ch14_diagnosis.py
锚定正文手算：四类根因签名（孤立尖刺/持续同号/实测骤变/实测偏低）与
综合判定 diagnose_root_cause 逐类反推（数据污染/模型漂移/天气骤变/测点问题）。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.diagnosis import (  # noqa: E402
    check_data_poison,
    check_model_drift,
    check_sensor_anomaly,
    check_weather_spike,
    diagnose_root_cause,
)
from ems_lab.versioning import detect_drift  # noqa: E402


def main():
    print("预测偏差根因诊断  [主线: 50 MW/100 MWh 储能 + 30 MW 光伏]\n")

    # 四类根因的偏差签名（14.3~14.5）
    e_pollution = [0.0, 0.0, 12.0, 0.0, 0.0, 0.0]
    e_weather = [0.0, 0.0, 8.0, -4.0, 5.0, 0.0]
    e_drift = [2.0, 1.0, 1.0, 2.0, 1.0, 2.0]
    e_meter = [-2.0, -1.0, -2.0, -2.0, -1.0, -2.0]

    print("[14.3] 数据污染：孤立尖刺 [0,0,12,0,0,0] ->", check_data_poison(e_pollution))
    print(f"[14.5] 天气骤变：实测骤变 NWP 平滑（-80 vs -400）-> "
          f"{check_weather_spike(-80.0, -400.0)}")

    # 旁路信号：模型漂移 vs 测点问题的区分（14.4）
    drift = detect_drift(-3.25, -2.25)          # 复用 12 章：正午箱3 bias 漂移
    ref_ghi = [800.0, 780.0, 760.0, 740.0, 720.0, 700.0]
    meas_ghi = [720.0, 700.0, 680.0, 660.0, 640.0, 620.0]  # 辐照计脏污，每点低 80
    print(f"\n[14.4] 旁路① 漂移检测 detect_drift(-3.25, -2.25) -> {drift}")
    print(f"[14.4] 模型漂移 check_model_drift(持续同号+, {drift}) -> "
          f"{check_model_drift(e_drift, drift)}")
    print(f"[14.4] 测点问题 check_sensor_anomaly(持续同号-, 每点低80) -> "
          f"{check_sensor_anomaly(e_meter, meas_ghi, ref_ghi)}")

    # 综合判定（14.6）
    cases = [
        ("数据污染", diagnose_root_cause(e_pollution, -80.0, -100.0,
                                         [800.0] * 6, [800.0] * 6, False)),
        ("天气骤变", diagnose_root_cause(e_weather, -80.0, -400.0,
                                         [800.0] * 6, [800.0] * 6, False)),
        ("模型漂移", diagnose_root_cause(e_drift, -80.0, -100.0,
                                         [800.0] * 6, [800.0] * 6, True)),
        ("测点问题", diagnose_root_cause(e_meter, -80.0, -100.0,
                                         meas_ghi, ref_ghi, False)),
    ]
    print("\n[14.6] 综合判定 diagnose_root_cause：")
    for name, (cause, action) in cases:
        print(f"  {name} -> {cause} | 处置：{action}")

    # 自检：锚定正文手算
    ok = (
        check_data_poison(e_pollution) is True
        and check_data_poison(e_drift) is False
        and check_weather_spike(-80.0, -400.0) is True
        and check_weather_spike(-80.0, -100.0) is False
        and check_model_drift(e_drift, True) is True
        and check_model_drift(e_drift, False) is False
        and check_sensor_anomaly(e_meter, meas_ghi, ref_ghi) is True
        and check_sensor_anomaly(e_meter, [800.0] * 6, [800.0] * 6) is False
        and cases[0][1][0] == "data_pollution"
        and cases[1][1][0] == "weather_abrupt"
        and cases[2][1][0] == "model_drift"
        and cases[3][1][0] == "meter_problem"
    )
    print("\n自检通过" if ok else "\n自检失败")


if __name__ == "__main__":
    main()