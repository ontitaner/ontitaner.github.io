# @AI_GENERATED
"""第 09 章核心模块：预测误差对日前排程的收益影响。

约定（对齐 09.x 手算、附录 B，主线 50 MW/100 MWh 储能 + 30 MW 光伏）：
- 单位：功率 MW、时长 h、能量 MWh、电价 元/kWh、金额 千元。
  （1 MWh x 1 元/kWh = 1000 元 = 1 千元；正文"万元" = 千元 / 10）
- 分时电价 [教学示例]：谷 0.15 / 平 0.55 / 峰 1.00 元/kWh，峰谷价差 = 0.85 元/kWh。
- 储能套利：谷段充电、峰段放电，充放等量、忽略效率 eta（教学简化，效率影响见能量调度课程）。
- 预测误差传导（一阶近似）：单时段收益损失 = |误差| x 时长 x 峰谷价差。
  低估（预测<实际）-> 储能错峰/弃光；高估（预测>实际）-> 缺电高价补。损失量级同为 |e| x dt x 价差。
- 主案例：正午低估 6 MW x 2 h = 12 MWh -> 损失 12 x 0.85 = 10.2 千元 = 1.02 万元。
  完美日套利 100 MWh -> 100x1.00 - 100x0.15 = 85 千元 = 8.5 万元；低估后套利 85-10.2 = 74.8 千元。
  00.1 的"单日 6.7 万元"= 全天误差电量约 78.8 MWh（67 千元 / 0.85）在 0.85 价差下的累积。
"""
from __future__ import annotations

P_VALLEY = 0.15   # 谷段电价 元/kWh [教学示例]
P_FLAT = 0.55     # 平段电价 元/kWh [教学示例]
P_PEAK = 1.00     # 峰段电价 元/kWh [教学示例]
SPREAD = 0.85     # 峰谷价差 = 峰价 - 谷价 元/kWh [教学示例]


def arbitrage_gain_k(discharge_mwh: float, charge_mwh: float,
                     p_peak: float = P_PEAK, p_valley: float = P_VALLEY) -> float:
    """储能套利收益（千元）= 放电量 x 峰价 - 充电量 x 谷价。

    完美日：arbitrage_gain_k(100, 100) -> 100x1.00 - 100x0.15 = 85.0（千元）= 8.5 万元。
    充放等量时等价于 放电量 x 峰谷价差。
    """
    if discharge_mwh < 0.0 or charge_mwh < 0.0:
        raise ValueError(f"充/放电量不能为负，实际放电 {discharge_mwh}、充电 {charge_mwh}")
    return discharge_mwh * p_peak - charge_mwh * p_valley


def error_energy_mwh(error_mw: float, hours: float) -> float:
    """误差电量（MWh）= |预测误差| x 时长。

    主案例：error_energy_mwh(-6, 2) -> 12.0 MWh。
    """
    if hours < 0.0:
        raise ValueError(f"时长不能为负，实际 {hours}")
    return abs(error_mw) * hours


def schedule_loss_k(error_mw: float, hours: float, spread: float = SPREAD) -> float:
    """单时段收益损失（千元）= |误差| x 时长 x 峰谷价差（一阶近似）。

    主案例：schedule_loss_k(-6, 2) -> 12 x 0.85 = 10.2（千元）= 1.02 万元。
    """
    return error_energy_mwh(error_mw, hours) * spread


def daily_loss_k(errors_mw: list[float], hours: list[float],
                 spread: float = SPREAD) -> float:
    """单日收益损失（千元）= 逐时段 |e| x dt x 价差 求和。

    需 errors_mw 与 hours 等长；对应 00.1"全天多时段误差累积"。
    """
    if len(errors_mw) != len(hours):
        raise ValueError(f"误差与时长序列长度须一致，实际 {len(errors_mw)} vs {len(hours)}")
    return sum(schedule_loss_k(e, h, spread) for e, h in zip(errors_mw, hours))
# @AI_GENERATED: end