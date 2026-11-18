"""第 05 章 5.5 最小闭环：用 ems_lab.battery.update_soc 重跑一次充放循环的能量账本。

输入：先充 200 kW × 1 h，再放 200 kW × 1 h
算法：update_soc（放电除效率、充电乘效率）
输出：每步内部储能变化和 SOC

运行（在 lab 目录下）：
    python examples/ch05_soc_efficiency.py
"""
import sys
from pathlib import Path

# 直接运行脚本时 Python 只把 examples/ 放进搜索路径，这里补上 lab/ 以便导入 ems_lab
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.battery import update_soc  # noqa: E402

CAPACITY_KWH = 1000.0
ETA = 0.95
STEPS_KW = [-200, 200]     # 放电为正、充电为负，每步 1 h


def main():
    soc = 0.50
    for p_kw in STEPS_KW:
        r = update_soc(soc, p_kw, 3600, CAPACITY_KWH, eta_charge=ETA, eta_discharge=ETA)
        soc = r.soc
        print(f"{'充电' if p_kw < 0 else '放电'} 200 kWh：内部 {r.stored_delta_kwh:+.2f} kWh → SOC {soc:.2%}")
    loss = (0.50 - soc) * CAPACITY_KWH
    print(f"一个循环后内部少了 {loss:.2f} kWh")
    assert abs(soc - 0.479474) < 1e-6 and abs(loss - (200 / ETA - 200 * ETA)) < 1e-9
    # 越界保留：SOC 92% 充 200 kW × 1 h，上限 95%
    r = update_soc(0.92, -200, 3600, CAPACITY_KWH, eta_charge=ETA, soc_max=0.95)
    print(f"越界示例：soc_raw {r.soc_raw:.0%} → soc {r.soc:.0%}，reason={r.reason}")
    assert r.reason == "above_max" and abs(r.soc_raw - 1.11) < 1e-9
    print("自检通过")

if __name__ == "__main__":
    main()

