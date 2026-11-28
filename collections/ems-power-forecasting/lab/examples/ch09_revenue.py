# @AI_GENERATED
"""第 09 章端到端演示：预测误差对日前排程的收益影响。

运行：python examples/ch09_revenue.py
锚定正文手算：完美日套利 8.5 万元、低估 6 MW x 2h 损失 1.02 万元、外推 6.7 万元。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.revenue import (  # noqa: E402
    SPREAD,
    arbitrage_gain_k,
    daily_loss_k,
    error_energy_mwh,
    schedule_loss_k,
)


def main():
    print("预测误差对日前排程的收益影响  [主线: 50 MW/100 MWh 储能 + 30 MW 光伏]\n")

    # 09.2 完美预测日：谷段充 100 MWh、峰段放 100 MWh
    gain = arbitrage_gain_k(100.0, 100.0)
    print(f"[09.2] 完美日套利 = {gain:.1f} 千元 = {gain / 10:.1f} 万元（100x1.00 - 100x0.15）")

    # 09.3 主案例：正午低估 6 MW x 2 h
    energy = error_energy_mwh(-6.0, 2.0)
    loss = schedule_loss_k(-6.0, 2.0)
    print(f"[09.3] 低估误差电量 = {energy:.1f} MWh（|-6| x 2）")
    print(f"[09.3] 单时段损失 = {loss:.1f} 千元 = {loss / 10:.2f} 万元（12 x 0.85）")
    print(f"[09.3] 低估后套利 = {gain - loss:.1f} 千元 = {(gain - loss) / 10:.2f} 万元（85 - 10.2）")

    # 09.5 外推：00.1 的"单日 6.7 万元"对应的全天误差电量
    daily_error_mwh = 67.0 / SPREAD
    print(f"[09.5] 6.7 万元 对应全天误差电量 = {daily_error_mwh:.1f} MWh（67 千元 / 0.85）")

    # 全天多时段累积示例：4 个低估时段（各 -6 MW x 2h）
    total = daily_loss_k([-6.0, -6.0, -6.0, -6.0], [2.0, 2.0, 2.0, 2.0])
    print(f"[09.5] 4 个低估时段累积损失 = {total:.1f} 千元 = {total / 10:.2f} 万元")

    ok = (
        abs(gain - 85.0) < 1e-9
        and abs(energy - 12.0) < 1e-9
        and abs(loss - 10.2) < 1e-9
        and abs(gain - loss - 74.8) < 1e-9
        and abs(daily_error_mwh - 78.823529) < 1e-4
        and abs(total - 40.8) < 1e-9
    )
    print("\n自检通过" if ok else "\n自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end