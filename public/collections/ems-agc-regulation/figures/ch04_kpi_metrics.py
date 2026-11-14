# @AI_GENERATED
"""第 04 章配图：K1/K2/K3 三项核心指标可视化。

构图原则：每张图只转译正文对应小节的显式手算数字（单一数据源），
不额外引入多场景/随机数据，图内每个数字都能在正文或 lab 找到唯一出处，
从而把核对成本降到最低。所有参数均为 [教学示例]。
"""
from __future__ import annotations

import numpy as np

from _style import (C_K1, C_K2, C_K3, C_GRID, C_LIMIT, C_OK, C_ACC, C_PURPLE,
                    IMG_DIR, manifest, save, plt)


def fig_k2_response_time():
    """K2 时间预算：6 环节水平条 + 30s 限值线。

    数据逐字来自正文「K2 的时间预算」代码示例：
    104轮询=4、EMS解析=0.5、死区+分配=0.5、EMS→PCS=0.5、PCS响应=1、到达阈值=3
    → 合计 9.5s，限值 30s，余量 20.5s（68.3%），最大贡献项=104轮询。
    """
    names = ["104轮询", "EMS解析+校验", "死区+分配", "EMS→PCS下发", "PCS内部响应", "出力到达阈值"]
    dur = [4.0, 0.5, 0.5, 0.5, 1.0, 3.0]
    limit = 30.0
    total = sum(dur)          # 9.5
    margin = limit - total    # 20.5

    fig, ax = plt.subplots(figsize=(9, 5.5))
    y = np.arange(len(names))[::-1]
    colors = [C_K2 if i == 0 else C_ACC for i in range(len(names))]
    ax.barh(y, dur, color=colors, alpha=0.85, edgecolor="white")
    for yi, d in zip(y, dur):
        ax.text(d + 0.15, yi, f"{d:.1f}s", va="center", fontsize=10,
                color=C_K2 if d == dur[0] else C_GRID)
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel("耗时 (s)")
    ax.set_xlim(0, 34)
    ax.set_title("K2 时间预算：6 环节合计 9.5s（东北：轮询 4s、限值 30s）", fontsize=11)

    ax.axvline(limit, color=C_LIMIT, ls="--", lw=1.5)
    ax.text(limit, len(names) - 0.1, f"限值 {limit:.0f}s", color=C_LIMIT,
            fontsize=9, ha="right", va="bottom")
    ax.axvline(total, color=C_K2, ls=":", lw=1.2)
    ax.text(total, -0.7, f"合计 {total:.1f}s", color=C_K2, fontsize=9, ha="center")
    ax.annotate(f"余量 {margin:.1f}s（68.3%）\n最大贡献项 = 104轮询（唯一不可控大头）",
                xy=(dur[0], y[0]), xytext=(dur[0] + 2.0, y[0] - 1.2),
                arrowprops=dict(arrowstyle="->", color=C_K2),
                fontsize=9, color=C_K2, bbox=dict(fc="white", ec=C_K2, alpha=0.9))

    fig.text(0.5, 0.01, "K2 = T_start_move − T_cmd_issued   |   合计 = 4+0.5+0.5+0.5+1+3 = 9.5s",
             ha="center", fontsize=9, color=C_GRID)
    manifest("ch04_k2_response", [*dur, limit, total, margin])
    save(fig, "ch04_k2_response")


def fig_k1_ramp_rate():
    """K1 多级限速取最小值：调度要求 + 三级限速。

    数据来自正文「影响 K1 的瓶颈链」+ 02 章手算：
    调度要求 1.0 Pn/min = 1.67 MW/s；EMS 安全/分配/PCS 各留 20% 余量 → 2.0 MW/s。
    """
    pn = 100.0
    req = 1.0 * pn / 60.0        # 1.67 MW/s = 1.0 Pn/min
    with_margin = req * 1.2      # 2.0 MW/s = 1.2 Pn/min（留 20% 余量）

    levels = ["调度要求 K1", "EMS 安全限速", "分配模块限速", "PCS ramp"]
    vals = [req, with_margin, with_margin, with_margin]
    units = ["1.0 Pn/min", "1.2 Pn/min", "1.2 Pn/min", "1.2 Pn/min"]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    y = np.arange(len(levels))[::-1]
    colors = [C_K1, C_ACC, C_ACC, C_ACC]
    ax.barh(y, vals, color=colors, alpha=0.85, edgecolor="white")
    for yi, v, u in zip(y, vals, units):
        ax.text(v + 0.05, yi, f"{v:.2f} MW/s（{u}）", va="center", fontsize=10)
    ax.axvline(req, color=C_LIMIT, ls="--", lw=1.5)
    ax.text(req, len(levels) - 0.1, f"达标线 {req:.2f} MW/s", color=C_LIMIT,
            fontsize=9, ha="right", va="bottom")
    ax.set_yticks(y)
    ax.set_yticklabels(levels)
    ax.invert_yaxis()
    ax.set_xlabel("限速 (MW/s)")
    ax.set_xlim(0, 2.7)
    ax.set_title("K1 多级限速：三级都 ≥2.0 MW/s 才达标", fontsize=11)
    ax.annotate("实际 K1 = min(以上)\n每层留 20% 余量 → 1.67×1.2 = 2.0",
                xy=(with_margin, y[1]), xytext=(2.15, y[1] + 0.7),
                arrowprops=dict(arrowstyle="->", color=C_K1),
                fontsize=9, color=C_K1, bbox=dict(fc="white", ec=C_K1, alpha=0.9))

    fig.text(0.5, 0.01, "K1 = ΔP / ΔT   |   调度要求 ≥1.0 Pn/min = 1.67 MW/s（100 MW 场站）",
             ha="center", fontsize=9, color=C_GRID)
    manifest("ch04_k1_ramp", [pn, req, with_margin, 1.0, 1.2])
    save(fig, "ch04_k1_ramp")


def fig_k3_precision():
    """K3 稳态偏差 vs 三级限值带。

    数据逐字来自正文「定义与限值」限值表：
    ≤±3% Pn = ±3 MW、≤±2% Pn = ±2 MW、≤±1% Pn = ±1 MW（100 MW 场站）。
    """
    pn = 100.0
    limits_pct = [3.0, 2.0, 1.0]
    limits_mw = [pn * p / 100 for p in limits_pct]   # 3 / 2 / 1 MW

    rng = np.random.default_rng(7)
    n = 30
    err = rng.normal(0.2, 0.6, n)
    err[5] = 3.5     # 教学示例：3 个点超过 ±3% 限值
    err[14] = -3.8
    err[26] = 4.1

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(1, n + 1)
    over = np.abs(err) > limits_mw[0]

    # 三级限值带：由内向外逐级变浅，±3% 之外为越限警示区
    ax.axhspan(-1, 1, color=C_K3, alpha=0.10, zorder=0)
    ax.axhspan(-2, -1, color=C_PURPLE, alpha=0.05, zorder=0)
    ax.axhspan(1, 2, color=C_PURPLE, alpha=0.05, zorder=0)
    ax.axhspan(-3, -2, color=C_LIMIT, alpha=0.04, zorder=0)
    ax.axhspan(2, 3, color=C_LIMIT, alpha=0.04, zorder=0)
    ax.axhspan(-6, -3, color=C_LIMIT, alpha=0.025, zorder=0)
    ax.axhspan(3, 6, color=C_LIMIT, alpha=0.025, zorder=0)

    # 时序连线 + 散点（时序数据用散点而非柱状）
    ax.plot(x, err, color=C_GRID, lw=1, alpha=0.35, zorder=2)
    ax.scatter(x[~over], err[~over], s=48, color=C_OK, edgecolor="white",
               linewidth=0.9, zorder=3, label="稳态偏差（合格）")
    ax.scatter(x[over], err[over], s=120, color=C_LIMIT, edgecolor="white",
               linewidth=1.3, zorder=4, label="越限点（> ±3% Pn）")

    # 三级限值线
    for pct, mw, c, ls in [(3.0, 3.0, C_LIMIT, "--"),
                           (2.0, 2.0, C_PURPLE, "-."),
                           (1.0, 1.0, C_K3, ":")]:
        ax.axhline(mw, color=c, ls=ls, lw=1.7, zorder=1)
        ax.axhline(-mw, color=c, ls=ls, lw=1.7, zorder=1)
        ax.text(n + 0.8, mw, f"±{pct:.0f}% Pn", va="center", ha="left",
                fontsize=8.5, color=c, fontweight="bold")

    ax.axhline(0, color="#9aa0a8", lw=0.9, zorder=1)

    # 越限点标注
    anns = [(6, 3.5, 9.5, 4.7), (15, -3.8, 18.5, -5.3), (27, 4.1, 22.5, 5.4)]
    for xi, yi, tx, ty in anns:
        ax.annotate(f"{yi:+.1f} MW", xy=(xi, yi), xytext=(tx, ty),
                    arrowprops=dict(arrowstyle="->", color=C_LIMIT, lw=1.1),
                    fontsize=8.5, color=C_LIMIT, fontweight="bold",
                    bbox=dict(fc="white", ec=C_LIMIT, alpha=0.92, boxstyle="round,pad=0.35"))

    ax.set_xlabel("控制周期", fontsize=11)
    ax.set_ylabel("稳态偏差 (MW)", fontsize=11)
    ax.set_title(f"K3 稳态偏差时序 vs 三级限值带（Pn={pn:.0f} MW）", fontsize=13, pad=14)
    ax.legend(fontsize=8.5, loc="upper right", framealpha=0.92)
    ax.set_xlim(1, n + 1)
    ax.set_ylim(-6, 6)

    fig.text(0.5, 0.01, "K3 = |P_actual_ss − P_target| / Pn × 100%（限值 ±3% / ±2% / ±1% Pn）",
             ha="center", fontsize=9, color=C_GRID)
    manifest("ch04_k3_precision", [pn, *limits_mw, *limits_pct])
    save(fig, "ch04_k3_precision")


def main():
    fig_k2_response_time()
    fig_k1_ramp_rate()
    fig_k3_precision()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end