# @AI_GENERATED
"""第 04 章配图：响应时序图、端到端延迟预算。

所有参数均为 [教学示例]，不可直接用于现场整定。
"""
from __future__ import annotations

import numpy as np

from _style import (C_DIS, C_CHG, C_GRID, C_LIMIT, C_OK, C_ACC, C_PURPLE,
                    IMG_DIR, manifest, save, plt)


def fig_timing_diagram():
    """阶跃响应时序：t0.1 / t0.9 / ts 的定义"""
    t = np.linspace(0, 18, 1801)
    dt = t[1] - t[0]

    # 模拟阶跃响应：一阶系统 + 时延
    tau = 2.5          # 时间常数
    delay = 0.8        # 时延
    target = 8.0       # 目标变化量 MW
    noise_std = 0.15   # 稳态噪声

    resp = target * (1 - np.exp(-np.maximum(0, t - delay) / tau))
    rng = np.random.default_rng(42)
    resp += rng.normal(0, noise_std, len(t))

    # 90% 点
    t09_idx = np.argmax(resp >= target * 0.9)
    t09 = t[t09_idx] if t09_idx > 0 else t[-1]

    # 10% 点
    t01_idx = np.argmax(resp >= target * 0.1)
    t01 = t[t01_idx] if t01_idx > 0 else t[-1]

    # ts: 进入 ±1% Pn（假设 Pn=100 MW，1%=1 MW）不再出来
    stable_band = 1.0
    ts = t[-1]
    for i in range(t09_idx + 100, len(t)):
        if np.all(np.abs(resp[i:] - target) < stable_band):
            ts = t[i]
            break

    fig, ax = plt.subplots(figsize=(10, 5.5))

    ax.plot(t, resp, color=C_OK, lw=2.2, label="实际出力响应")
    ax.axhline(target, color=C_GRID, ls="--", lw=1.2, label=f"目标变化量 {target} MW")
    ax.axhline(target * 0.9, color=C_ACC, ls=":", lw=1.2)
    ax.axhline(target * 0.1, color=C_ACC, ls=":", lw=1.2)
    ax.axhline(0, color="k", lw=0.8)

    # 死区阴影（频率刚越死区）
    ax.axvspan(0, 0.1, color=C_GRID, alpha=0.06)
    ax.annotate("频率越过死区\n（计时起点）", xy=(0.05, -0.5), xytext=(0.5, -1.5),
                arrowprops=dict(arrowstyle="->"), fontsize=8.5, ha="center")

    # t0.1 标注
    ax.axvline(t01, color=C_DIS, ls="--", lw=1.2)
    ax.plot(t01, target * 0.1, "o", color=C_DIS, ms=7, zorder=5)
    ax.annotate(f"t0.1 = {t01:.2f} s\n出力开始可靠变化\n（达到 10% 目标）",
                xy=(t01, target * 0.1), xytext=(t01 + 0.8, target * 0.25),
                arrowprops=dict(arrowstyle="->", color=C_DIS),
                fontsize=8.5, color=C_DIS,
                bbox=dict(fc="white", ec=C_DIS, alpha=0.85))

    # t0.9 标注
    ax.axvline(t09, color=C_ACC, ls="--", lw=1.2)
    ax.plot(t09, target * 0.9, "s", color=C_ACC, ms=8, zorder=5)
    ax.annotate(f"t0.9 = {t09:.2f} s\n达到 90% 目标",
                xy=(t09, target * 0.9), xytext=(t09 - 3.5, target * 1.05),
                arrowprops=dict(arrowstyle="->", color=C_ACC),
                fontsize=8.5, color=C_ACC,
                bbox=dict(fc="white", ec=C_ACC, alpha=0.85))

    # ts 标注
    ax.axvline(ts, color=C_PURPLE, ls="--", lw=1.2)
    ax.axhspan(target - stable_band, target + stable_band, xmin=(ts - t[0]) / (t[-1] - t[0]),
               color=C_OK, alpha=0.08)
    ax.annotate(f"ts = {ts:.1f} s\n出力稳定\n（波动 ≤ ±1% Pn）",
                xy=(ts, target), xytext=(ts + 0.5, target - 1.5),
                arrowprops=dict(arrowstyle="->", color=C_PURPLE),
                fontsize=8.5, color=C_PURPLE,
                bbox=dict(fc="white", ec=C_PURPLE, alpha=0.85))

    # 时间预算标注
    ax.axvspan(0, 2, ymin=1.02, ymax=1.08, color=C_LIMIT, alpha=0.1, transform=ax.get_xaxis_transform())
    ax.text(1, 9.0, "t0.1 限值 2 s（风电/光伏）", fontsize=8, color=C_LIMIT, ha="center",
            bbox=dict(fc="white", ec=C_LIMIT, alpha=0.85))
    ax.axvspan(0, 5, ymin=1.09, ymax=1.15, color=C_GRID, alpha=0.08, transform=ax.get_xaxis_transform())
    ax.text(2.5, 9.8, "t0.9 限值 5 s（光伏）", fontsize=8, color=C_GRID, ha="center")

    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("出力变化量 ΔP (MW)")
    ax.set_title("一次调频阶跃响应的三个时间指标  [教学示例，非实测数据]")
    ax.set_xlim(0, 16)
    ax.set_ylim(-2.5, 10.5)
    ax.legend(loc="lower right", fontsize=8)

    manifest("ch04_timing_diagram",
             [t01, t09, ts, target, 0.1, 0.9, 2, 5, 12, 15, 1.0, delay])
    save(fig, "ch04_timing_diagram")


def fig_latency_budget():
    """端到端延迟预算：EMS 方案 vs 本地方案"""
    fig, ax = plt.subplots(figsize=(9, 4.5))

    labels = ["频率采样", "测频算法", "暂态防护", "控制计算", "通信下行", "PCS 响应", "出力爬坡"]
    ems_delays = [0.05, 0.06, 0.20, 0.80, 0.30, 0.20, 0.40]
    local_delays = [0.05, 0.06, 0.15, 0.05, 0.05, 0.20, 0.40]

    ems_cum = np.cumsum([0] + ems_delays)
    local_cum = np.cumsum([0] + local_delays)

    y = np.arange(len(labels))

    ax.barh(y, ems_delays, left=ems_cum[:-1], height=0.35, color=C_ACC, alpha=0.85,
            label=f"EMS 集中计算：累计 {sum(ems_delays):.2f} s")
    ax.barh(y + 0.35, local_delays, left=local_cum[:-1], height=0.35, color=C_OK, alpha=0.85,
            label=f"本地快速控制：累计 {sum(local_delays):.2f} s")

    ax.axvline(2.0, color=C_LIMIT, ls="--", lw=2)
    ax.text(2.02, len(labels) - 0.3, "t0.1 限值 2 s", fontsize=9, color=C_LIMIT,
            bbox=dict(fc="white", ec=C_LIMIT, alpha=0.9))

    ax.set_yticks(y + 0.175)
    ax.set_yticklabels(labels)
    ax.set_xlabel("累计延迟 (s)")
    ax.set_title("端到端延迟预算对比：EMS 集中计算 vs 本地快速控制  [教学示例]")
    ax.legend(loc="lower right", fontsize=8.5)
    ax.set_xlim(0, 2.8)
    ax.invert_yaxis()

    manifest("ch04_latency_budget",
             list(ems_cum[1:]) + list(local_cum[1:]) + [2.0])
    save(fig, "ch04_latency_budget")


def main():
    fig_timing_diagram()
    fig_latency_budget()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end