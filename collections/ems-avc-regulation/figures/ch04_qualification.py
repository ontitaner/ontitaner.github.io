# @AI_GENERATED
"""第 04 章配图：电压合格率两种统计口径对比 + 测点差异 + 响应时序。

参数对齐章节 04.2~04.3：[教学示例]
- 合格率：逐点 vs 移动平均，合格范围 [0.993, 1.007]
- 测点差异：35kV PT vs 110kV PCC，阻抗压降 0.003 pu
- 响应时序：七段分解，总预算 30s
"""
from __future__ import annotations

import numpy as np

from _style import (C_DIS, C_CHG, C_ACC, C_LIMIT, C_GRID, C_OK, C_PURPLE,
                    IMG_DIR, save, note, plt)


def fig_qualification_compare():
    np.random.seed(42)
    hours = np.arange(24)
    u_raw = np.ones(24)
    u_raw[0:8] = 1.000 + np.random.normal(0, 0.002, 8)
    u_raw[8:12] = 1.005 + np.random.normal(0, 0.003, 4)
    u_raw[12:17] = 1.012 + np.random.normal(0, 0.004, 5)
    u_raw[17:24] = 1.000 + np.random.normal(0, 0.002, 7)
    u_raw[2], u_raw[15], u_raw[21] = 1.029, 1.031, 0.991

    ub, lb = 1.007, 0.993
    u_ma = np.convolve(u_raw, np.ones(6) / 6, mode="same")

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)

    ax = axes[0]
    colors = [C_OK if lb <= u <= ub else C_LIMIT for u in u_raw]
    ax.plot(hours, u_raw, "-o", color=C_PURPLE, lw=1.2, ms=4, alpha=0.5)
    for h, u, c in zip(hours, u_raw, colors):
        ax.plot(h, u, "o", color=c, ms=6 if u < lb or u > ub else 4)
    ax.axhline(ub, color=C_LIMIT, ls="--", lw=1.5, label=f"上限 {ub:.3f}")
    ax.axhline(lb, color=C_LIMIT, ls="--", lw=1.5)
    ax.axhline(1.000, color=C_GRID, ls=":", lw=1)
    n_ok = sum(1 for u in u_raw if lb <= u <= ub)
    ax.set_xlabel("时刻 (h)")
    ax.set_ylabel("PCC 电压 (pu)")
    ax.set_title(f"逐点采样间隔 1h\n合格率 {n_ok}/24 = {n_ok/24*100:.1f}%")
    ax.legend(fontsize=8)
    ax.set_ylim(0.988, 1.036)

    ax = axes[1]
    colors = [C_OK if lb <= u <= ub else C_LIMIT for u in u_ma]
    ax.plot(hours, u_ma, "-s", color=C_CHG, lw=2, ms=4)
    for h, u, c in zip(hours, u_ma, colors):
        ax.plot(h, u, "o", color=c, ms=6 if u < lb or u > ub else 4)
    ax.axhline(ub, color=C_LIMIT, ls="--", lw=1.5)
    ax.axhline(lb, color=C_LIMIT, ls="--", lw=1.5)
    ax.axhline(1.000, color=C_GRID, ls=":", lw=1)
    ma_ok = sum(1 for u in u_ma if lb <= u <= ub)
    ax.set_xlabel("时刻 (h)")
    ax.set_title(f"6h 移动平均\n合格率 {ma_ok}/24 = {ma_ok/24*100:.1f}%")
    ax.set_ylim(0.988, 1.036)

    fig.suptitle("同一组数据不同统计口径：移动平均可抹平滑峰 → 合格率虚高  [教学示例]", fontsize=11)
    save(fig, "ch04_qualification_compare")


def fig_measure_point():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.5),
                             gridspec_kw={"width_ratios": [1.4, 1]})

    ax = axes[0]
    meas_points = ["调度AVC\n主站考核", "110kV PCC\n关口表", "主变压器\nΔU≈0.003pu", "35kV母线\nPT", "EMS\n自采显示"]
    voltages = [None, 1.008, None, 1.005, None]
    colors_pt = [C_GRID, C_LIMIT, C_GRID, C_OK, C_GRID]

    y = np.arange(len(meas_points))
    for i, (label, v, c) in enumerate(zip(meas_points, voltages, colors_pt)):
        if v is not None:
            ax.barh(i, v - 1.000, left=1.000, height=0.45, color=c, alpha=0.85)
            ax.text(v + 0.0003, i, f"{v:.3f} pu", va="center", fontsize=10.5, fontweight="bold", color=c)
        else:
            ax.barh(i, 0, height=0.02, color=C_GRID, alpha=0.3)
    ax.axvline(1.000, color=C_GRID, ls=":", lw=1.2)
    ax.axvline(1.007, color=C_LIMIT, ls="--", lw=1.8, label="合格上限 1.007 pu")
    ax.set_yticks(y, meas_points)
    ax.set_xlim(1.000, 1.010)
    ax.set_xlabel("电压 (pu)")
    ax.set_title("同一时刻：调度判不合格，EMS 判合格")
    ax.legend(fontsize=8.5, loc="lower right")
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)

    ax = axes[1]
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    note_lines = [
        "调度 AVC 主站",
        "    ↓ 考核依据",
        "PCC 关口表 U=1.008 pu",
        "    ↓ 阻抗压降 ΔU≈0.003 pu",
        "35kV 母线 PT U=1.005 pu",
    ]
    for i, line in enumerate(note_lines):
        c = C_LIMIT if "1.008" in line else (C_OK if "1.005" in line else C_GRID)
        bold = "1.008" in line or "1.005" in line
        ax.text(1, 8.5 - i * 1.5, line, fontsize=10.5, fontweight="bold" if bold else "normal",
                color=c, va="center")

    ax.text(5, 1.5, "[!] 关键结论\nPCC 测点 ≠ 站内测点\nΔU=0.003pu = 判据漂移",
            ha="center", fontsize=10, color=C_LIMIT, fontweight="bold",
            bbox=dict(fc="white", ec=C_LIMIT, alpha=0.95, boxstyle="round,pad=0.4"))

    fig.suptitle("PCC 测点 vs 站内测点：同一时刻判据不同  [教学示例]", fontsize=11)
    save(fig, "ch04_measure_point")


def fig_response_timing():
    stages = ["104轮询", "EMS解析", "控制计算", "协议下发", "PCS爬坡", "电压生效", "反馈上送",
              "——————", "合计"]
    budget = [6, 1, 1, 1.5, 3.5, 5, 1.5, 0, 30]
    actual = [4, 0.8, 0.5, 1.2, 2.8, 3.0, 1.0, 0, 13.3]
    colors_budget = [C_GRID, C_GRID, C_GRID, C_GRID, C_GRID, C_GRID, C_GRID, "none", C_GRID]
    colors_actual = [C_OK, C_OK, C_OK, C_OK, C_OK, C_OK, C_OK, "none", C_OK]

    fig, ax = plt.subplots(figsize=(11, 4))

    y = np.arange(len(stages))
    h = 0.32
    b1 = ax.barh(y + h / 2, budget, h, color=colors_budget, alpha=0.3,
                 label="时间预算", edgecolor="white")
    b2 = ax.barh(y - h / 2, actual, h, color=colors_actual, alpha=0.85,
                 label="实测耗时", edgecolor="white")

    ax.axvline(30, color=C_LIMIT, ls="-", lw=2.2, label="考核限 30 s")

    for i, (b, a) in enumerate(zip(budget, actual)):
        if b > 0:
            ax.text(b + 0.3, i + h / 2 + 0.05, f"{b}s", fontsize=8, color=C_GRID, va="center")
        if a > 0:
            color = "white" if a > 1.5 else "black"
            ax.text(a / 2, i - h / 2, f"{a}s", fontsize=8, color=color,
                    ha="center", va="center", fontweight="bold")

    ax.text(31, len(stages) - 0.5, "30s", fontsize=9.5, color=C_LIMIT, fontweight="bold", va="center")
    ax.set_yticks(y, stages)
    ax.set_xlabel("时间 (s)")
    ax.set_title("AVC 响应时序预算分解  [实测合计 13.3 s < 30 s 考核限]", fontsize=10)
    ax.legend(fontsize=8.5, loc="lower right")
    ax.set_xlim(0, 36)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)

    save(fig, "ch04_response_timing")


def main():
    fig_qualification_compare()
    fig_measure_point()
    fig_response_timing()
    print(f"  ch04: 3 figures saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end