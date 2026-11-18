"""第 05 章 5.3 最小闭环：用 lab 里真实的 CoulombCounter 重跑正文追踪表。

输入：6 小时电流序列（放电 2 h → 静置 2 h → 充电 2 h）
算法：CoulombCounter.update，即 SOC[k] = SOC[k-1] − I[k]·Δt / (3600·C)
输出：真实 SOC、零点偏差 +0.5 A 估计、增益误差 +1% 估计的逐时段追踪表

运行（在 lab 目录下）：
    python examples/ch05_coulomb_counting.py
"""
import sys
from pathlib import Path

# 直接运行脚本时 Python 只把 examples/ 放进搜索路径，这里补上 lab/ 以便导入 ems_lab
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.battery import CoulombCounter  # noqa: E402

CAPACITY_AH = 314.0   # C：当前实际容量（Ah）
SOC0 = 0.50           # SOC[0]：初始 SOC
DT_S = 3600.0         # Δt：每步时长（s），取 1 小时方便与正文逐行对照
BIAS_A = 0.5          # 零点偏差：读数总是多 0.5 A
GAIN = 1.01           # 增益误差：读数偏大 1%

# ---- 输入：真实电流序列（A），放电为正、充电为负 ----
TRUE_CURRENT_A = [60, 60, 0, 0, -60, -60]
LABELS = ["放电", "放电", "静置", "静置", "充电", "充电"]


def run_trace():
    """逐步积分，返回每个时段的 (电流, 真实 SOC, 零点偏差 SOC, 增益误差 SOC)。"""
    # 三个估计器从同一个初值出发，只有“看到的电流”不同
    truth = CoulombCounter(CAPACITY_AH, SOC0)
    biased = CoulombCounter(CAPACITY_AH, SOC0)
    gained = CoulombCounter(CAPACITY_AH, SOC0)
    rows = []
    for i_true in TRUE_CURRENT_A:
        truth.update(i_true, DT_S)            # 理想传感器
        biased.update(i_true + BIAS_A, DT_S)  # 零点偏差
        gained.update(i_true * GAIN, DT_S)    # 增益误差
        rows.append((i_true, truth.soc, biased.soc, gained.soc))
    return rows


def main():
    rows = run_trace()

    # ---- 输出：与正文 5.3 追踪表同格式（百分比） ----
    print(f"{'时段':<4}{'电流(A)':>8}{'真实SOC':>10}{'零点偏差':>10}{'误差':>9}{'增益误差':>10}{'误差':>9}")
    for k, ((i, s_t, s_b, s_g), lab) in enumerate(zip(rows, LABELS), start=1):
        print(f"{k}h {lab}{i:>8}{s_t*100:>9.3f}%{s_b*100:>9.3f}%"
              f"{(s_b-s_t)*100:>+8.3f}%{s_g*100:>9.3f}%{(s_g-s_t)*100:>+8.3f}%")

    # ---- 自检：正文读出的两个结论 ----
    _, s_t, s_b, s_g = rows[-1]
    hours = len(TRUE_CURRENT_A) * DT_S / 3600.0
    # 结论 1：零点偏差误差 = 偏差 × 总时长 / 容量，与充放电无关
    assert abs((s_b - s_t) - (-BIAS_A * hours / CAPACITY_AH)) < 1e-12
    # 结论 2：增益误差在一个完整充放循环后抵消
    assert abs(s_g - s_t) < 1e-12
    print("自检通过")


if __name__ == "__main__":
    main()

