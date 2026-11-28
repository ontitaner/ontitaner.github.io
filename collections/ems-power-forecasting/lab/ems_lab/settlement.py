# @AI_GENERATED
"""第 10 章核心模块：预测误差对现货报价的结算影响。

约定（对齐 10.x 手算、附录 B，主线 50 MW/100 MWh 储能 + 30 MW 光伏）：
- 单位：功率 MW、时长 h、能量 MWh、电价 元/kWh、金额 千元。
  （1 MWh x 1 元/kWh = 1000 元 = 1 千元；正文"万元" = 千元 / 10）
- 现货"报量不报价"：新能源单站容量相对市场很小，是价格接受者，
  申报出力 = 预测出力，偏差电量按实时出清价结算。
- 实时出清价 [教学示例]：P_SPOT = 1.00 元/kWh（= 1000 元/MWh，云团覆盖时段现货尖峰，
  承接 09 章"高估 -> 缺电高价补（峰段 1.00 元/kWh）"的口径）。
- 偏差结算（一阶近似）：单时段结算损失 = |申报出力 - 实际出力| x 时长 x 实时出清价。
  高估（申报 > 实际）-> 少发的电按实时价买回；低估（申报 < 实际）-> 多发的电按实时价结算。
  一阶近似两边量级同为 |偏差| x 时长 x 实时价，精确结算见能量调度 07 章。
- 主案例：云团覆盖，申报 16 MW、实际 12 MW，高估 4 MW x 2 h = 8 MWh
  -> 结算损失 8 x 1.00 = 8.0 千元 = 0.8 万元。
"""
from __future__ import annotations

P_SPOT = 1.00   # 现货实时出清价 元/kWh [教学示例]（= 1000 元/MWh）


def deviation_energy_mwh(declared_mw: float, actual_mw: float, hours: float) -> float:
    """偏差电量（MWh）= |申报出力 - 实际出力| x 时长。

    主案例：deviation_energy_mwh(16, 12, 2) -> 4 x 2 = 8.0 MWh。
    """
    if hours < 0.0:
        raise ValueError(f"时长不能为负，实际 {hours}")
    return abs(declared_mw - actual_mw) * hours


def deviation_loss_k(declared_mw: float, actual_mw: float, hours: float,
                     p_spot: float = P_SPOT) -> float:
    """单时段偏差结算损失（千元）= 偏差电量 x 实时出清价（一阶近似）。

    主案例：deviation_loss_k(16, 12, 2) -> 8 x 1.00 = 8.0（千元）= 0.8 万元。
    """
    return deviation_energy_mwh(declared_mw, actual_mw, hours) * p_spot


def daily_deviation_loss_k(declared_mw_list: list[float], actual_mw_list: list[float],
                           hours: list[float], p_spot: float = P_SPOT) -> float:
    """单日偏差结算损失（千元）= 逐时段 |申报 - 实际| x 时长 x 实时价 求和。

    需三个序列等长；对应现货按 15min 结算时段逐段累积。
    """
    if len(declared_mw_list) != len(actual_mw_list) or len(declared_mw_list) != len(hours):
        raise ValueError(
            f"申报/实际/时长序列长度须一致，实际 "
            f"{len(declared_mw_list)} vs {len(actual_mw_list)} vs {len(hours)}"
        )
    return sum(deviation_loss_k(d, a, h, p_spot)
               for d, a, h in zip(declared_mw_list, actual_mw_list, hours))
# @AI_GENERATED: end