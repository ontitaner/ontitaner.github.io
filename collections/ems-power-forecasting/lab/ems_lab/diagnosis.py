# @AI_GENERATED
"""第 14 章核心模块：预测偏差根因诊断（四类根因反推）。

约定（对齐 04/07/12/13 章手算、附录B/C）：
- 预测考核不合格只是"结果"，不是"原因"。本章把一条偏差序列 + 旁路信号
  （NWP/实测 GHI 变化率、实测 vs 参考、漂移检测）反推成四类根因之一：
    1. 数据污染 data_pollution：孤立尖刺（相邻点正常，坏点命中门控）；
    2. 模型漂移 model_drift   ：持续同号偏差 + 漂移检测触发（复用 12 章）；
    3. 天气骤变 weather_abrupt ：实测变化率骤变而 NWP 平滑（云团/沙尘过境）；
    4. 测点问题 meter_problem  ：持续同号偏差 + 实测相对参考持续偏低（传感器脏污）。
- 核心教学点：模型漂移与测点问题在偏差序列上都是"持续同号"，单看偏差无法区分，
  必须靠旁路信号（drift 触发 vs 实测偏低）交叉验证——这正是"反推"的价值。

教学示例默认值（对齐主线 30 MW 光伏，15 min 网格）：
- 孤立尖刺阈值 SPIKE_THRESHOLD = 10 MW（|e| >= 10 且相邻点都 < 10 判孤立）
- 系统性偏差最少非零点 MIN_SYSTEMATIC = 2（非零点不足 2 个不判系统）
- 天气骤变阈值 WEATHER_STEP_THRESHOLD = 300 W/(m²·15min)（实测变化率比 NWP 多出）
- 测点偏差阈值 METER_BIAS_THRESHOLD = 60 W/m²（实测比参考每点低 >= 60 判脏污）
"""
from __future__ import annotations

SPIKE_THRESHOLD = 10.0             # 孤立尖刺判定阈值 MW [教学示例]
MIN_SYSTEMATIC = 2                 # 系统性偏差最少非零点数 [教学示例]
WEATHER_STEP_THRESHOLD = 300.0     # 天气骤变：实测变化率比 NWP 多出的 W/(m²·15min) [教学示例]
METER_BIAS_THRESHOLD = 60.0        # 测点偏差：实测比参考每点低出的 W/m² [教学示例]


def _systematic_bias(errors: list[float],
                     min_nonzero: int = MIN_SYSTEMATIC) -> bool:
    """模型漂移/测点问题的共性签名：偏差持续同号（系统性高估或低估）。

    取非零偏差的符号，要求非零偏差至少有 min_nonzero 个且符号全部一致。
    主案例：_systematic_bias([2,1,1,2,1,2]) -> 全正 -> True；
            _systematic_bias([-2,-1,-2,-2,-1,-2]) -> 全负 -> True。
    反例：_systematic_bias([2,-1,1,-2,1,0]) -> False（有正有负）；
          _systematic_bias([0,0,12,0,0,0]) -> False（仅 1 个非零点 < 2）。
    """
    signs = [1 if e > 0.0 else (-1 if e < 0.0 else 0) for e in errors]
    nonzero = [s for s in signs if s != 0]
    if len(nonzero) < min_nonzero:
        return False
    return all(s == nonzero[0] for s in nonzero)


def check_data_poison(errors: list[float],
                      threshold: float = SPIKE_THRESHOLD) -> bool:
    """数据污染签名：大幅偏差是"孤立尖刺"（相邻点都正常）。

    |e_i| >= threshold 的点称为坏点；若每个坏点的左右相邻点（存在时）都 < threshold，
    说明偏差是孤立爆发（通信抖动/单点坏数据），而非全段抬高（漂移/脏污）。
    主案例：check_data_poison([0,0,12,0,0,0]) -> 坏点索引2，邻居(1,3)都 0 -> True。
    反例（全段抬高）：check_data_poison([12,12,12,12,12,12]) -> False。
    """
    n = len(errors)
    bad = [i for i in range(n) if abs(errors[i]) >= threshold]
    if not bad:
        return False
    for i in bad:
        if i > 0 and abs(errors[i - 1]) >= threshold:
            return False
        if i < n - 1 and abs(errors[i + 1]) >= threshold:
            return False
    return True


def check_weather_spike(nwp_step: float, meas_step: float,
                        threshold: float = WEATHER_STEP_THRESHOLD) -> bool:
    """天气骤变签名：实测变化率骤变，而 NWP 变化率平滑（未预报到）。

    nwp_step 为 NWP 预报的相邻 15min 辐照变化（W/m²），meas_step 为实测变化。
    当 |meas_step| - |nwp_step| >= threshold，说明天气突变（云团/沙尘过境）
    没被 NWP 捕捉，导致预测大幅偏离。等号算触发（>=）。
    主案例：check_weather_spike(-80, -400) -> 400-80=320 >= 300 -> True。
    反例：check_weather_spike(-80, -100) -> 20 < 300 -> False。
    """
    return abs(meas_step) - abs(nwp_step) >= threshold


def check_model_drift(errors: list[float], drift: bool,
                      min_nonzero: int = MIN_SYSTEMATIC) -> bool:
    """模型漂移签名：持续同号偏差 + 漂移检测触发（复用 12 章 detect_drift）。

    单看偏差只能确认"持续同号"（_systematic_bias），还必须靠旁路信号 drift=True
    （近期偏差相对训练基准系统性偏移，12 章 detect_drift 触发）才能定位到模型。
    主案例：check_model_drift([2,1,1,2,1,2], True) -> True。
    反例：check_model_drift([2,1,1,2,1,2], False) -> False（持续同号但漂移未触发）。
    """
    return _systematic_bias(errors, min_nonzero) and drift


def check_sensor_anomaly(errors: list[float], meas_ghi: list[float],
                         ref_ghi: list[float],
                         min_nonzero: int = MIN_SYSTEMATIC,
                         threshold: float = METER_BIAS_THRESHOLD) -> bool:
    """测点问题签名：持续同号偏差 + 实测相对参考持续偏低（传感器脏污）。

    持续同号偏差（_systematic_bias）说明偏差是系统性的；再叠加实测 GHI 比参考
    （晴空模型/邻近站）每点都低 >= threshold，且门控会放行，则指向辐照计脏污/失准。
    主案例：check_sensor_anomaly([-2,-1,-2,-2,-1,-2],
                                  [720,700,680,660,640,620], [800,780,760,740,720,700])
           -> 持续同号 True 且每点低 80 >= 60 -> True。
    反例：实测与参考一致 -> False；长度不一致/空序列 -> False。
    """
    if len(meas_ghi) != len(ref_ghi) or len(meas_ghi) == 0:
        return False
    return (_systematic_bias(errors, min_nonzero)
            and all(m - r <= -threshold for m, r in zip(meas_ghi, ref_ghi)))


def diagnose_root_cause(errors: list[float], nwp_step: float, meas_step: float,
                        meas_ghi: list[float], ref_ghi: list[float],
                        drift: bool) -> tuple[str, str]:
    """四类根因逐一反推，返回 (根因标签, 处置动作)。

    排查顺序（成本从低到高）：
      1) 孤立尖刺                     -> data_pollution（门控一跑就有，最快）
      2) 实测骤变、NWP 平滑           -> weather_abrupt（查天气变化率，次快）
      3) 持续同号 + 漂移触发          -> model_drift（查模型，复用 12 章 detect_drift）
      4) 持续同号 + 实测持续偏低      -> meter_problem（查传感器，需现场巡检，最慢）
      无匹配 -> unknown（人工复核，扩大旁路信号）。
    主案例四组：
      diagnose_root_cause([0,0,12,0,0,0], -80, -100, [800]*6, [800]*6, False)
          -> ("data_pollution", ...)
      diagnose_root_cause([0,0,8,-4,5,0], -80, -400, [800]*6, [800]*6, False)
          -> ("weather_abrupt", ...)
      diagnose_root_cause([2,1,1,2,1,2], -80, -100, [800]*6, [800]*6, True)
          -> ("model_drift", ...)
      diagnose_root_cause([-2,-1,-2,-2,-1,-2], -80, -100,
                          [720,700,680,660,640,620], [800,780,760,740,720,700], False)
          -> ("meter_problem", ...)
    """
    if check_data_poison(errors):
        return ("data_pollution", "门控剔除坏点 + 回填重发 + 补传原始数据")
    if check_weather_spike(nwp_step, meas_step):
        return ("weather_abrupt", "切换超短期滚动外推 + 告警 + 引入高分辨率 NWP/卫星云图")
    if _systematic_bias(errors):
        if check_model_drift(errors, drift):
            return ("model_drift", "再训练新版本 + 发布卡校验 + 回滚卡兜底")
        if check_sensor_anomaly(errors, meas_ghi, ref_ghi):
            return ("meter_problem", "现场巡检清洗/校准辐照计 + 更换传感器")
        return ("unknown", "系统性偏差但旁路无异常，人工复核")
    return ("unknown", "无匹配签名，扩大旁路信号再定位")
# @AI_GENERATED: end