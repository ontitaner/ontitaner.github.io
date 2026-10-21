"""第03章配套示例：单次套利收益分解、盈亏平衡价差和需量节省。

从 lab 目录运行：
    python examples/ch03_economics_trace.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.economics import (  # noqa: E402
    arbitrage_cycle,
    breakeven_spread,
    demand_charge_saving,
)


def main() -> None:
    result = arbitrage_cycle(1800, 1.10, 0.30, 0.85, 0.10)
    threshold = breakeven_spread(0.30, 0.85, 0.10)
    demand = demand_charge_saving(500, 40, months=12)
    print("单次套利收益分解")
    print(f"充入电量：{result.e_ch_kwh:.2f} kWh")
    print(f"效率损失成本：{result.efficiency_loss_cost:.2f} 元")
    print(f"电费差：{result.gross_profit:.2f} 元")
    print(f"退化成本：{result.degradation_cost:.2f} 元")
    print(f"净收益：{result.net_profit:.2f} 元")
    print(f"盈亏平衡价差：{threshold:.4f} 元/kWh")
    print(f"年度需量节省：{demand:.0f} 元")
    assert round(result.e_ch_kwh, 2) == 2117.65
    assert round(result.net_profit, 2) == 1164.71
    assert round(threshold, 4) == 0.1529
    assert demand == 240000
    print("自检通过")


if __name__ == "__main__":
    main()

