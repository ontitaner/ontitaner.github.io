# @AI_GENERATED
"""第 10 章端到端演示：预测误差对现货报价的结算影响。

运行：python examples/ch10_settlement.py
锚定正文手算：云团覆盖高估 4 MW x 2h 偏差电量 8 MWh、结算损失 0.8 万元。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.settlement import (  # noqa: E402
    P_SPOT,
    daily_deviation_loss_k,
    deviation_energy_mwh,
    deviation_loss_k,
)


def main():
    print("预测误差对现货报价的结算影响  [主线: 50 MW/100 MWh 储能 + 30 MW 光伏]\n")

    # 10.3 主案例：云团覆盖，申报 16 MW、实际 12 MW，高估 4 MW x 2 h
    energy = deviation_energy_mwh(16.0, 12.0, 2.0)
    loss = deviation_loss_k(16.0, 12.0, 2.0)
    print(f"[10.3] 偏差电量 = {energy:.1f} MWh（|16 - 12| x 2）")
    print(f"[10.3] 结算损失 = {loss:.1f} 千元 = {loss / 10:.2f} 万元（8 x {P_SPOT:.2f}）")

    # 10.4 低估对比：申报 12、实际 16（一阶近似量级对称）
    loss_under = deviation_loss_k(12.0, 16.0, 2.0)
    print(f"[10.4] 低估（多发贱卖）结算损失 = {loss_under:.1f} 千元（一阶近似对称）")

    # 无偏差：申报 = 实际
    loss_zero = deviation_loss_k(16.0, 16.0, 2.0)
    print(f"[10.3] 无偏差结算损失 = {loss_zero:.1f} 千元（申报=实际，偏差 0）")

    # 10.5 单日累积：8 个 15min 结算时段，云团覆盖期间各高估 4 MW
    total = daily_deviation_loss_k([16.0] * 8, [12.0] * 8, [0.25] * 8)
    print(f"[10.5] 8 个 15min 时段累积结算损失 = {total:.1f} 千元 = {total / 10:.2f} 万元")

    ok = (
        abs(energy - 8.0) < 1e-9
        and abs(loss - 8.0) < 1e-9
        and abs(loss_under - 8.0) < 1e-9
        and abs(loss_zero - 0.0) < 1e-9
        and abs(total - 8.0) < 1e-9
    )
    print("\n自检通过" if ok else "\n自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end