# @AI_GENERATED
"""第 03 章配图：光伏功率平滑与储能补偿。

参数对齐章节 03.2/03.3：[教学示例]
- 光伏峰值 30 MW，6:00–18:00 半正弦 + 随机波动
- 滑动平均窗口 5，储能补偿 = 平滑 − 原始（+放/−充）
"""
from __future__ import annotations

import numpy as np

from _style import C_PV, C_ACC, C_DIS, C_CHG, save, note, plt

PEAK = 30.0
WINDOW = 5


def _pv_noisy():
    t = np.linspace(6, 18, 121)
    rng = np.random.default_rng(7)
    base = PEAK * np.sin(np.pi * (t - 6.0) / 12.0)
    noise = rng.normal(0, 1.2, size=t.shape)
    return t, base + noise


def fig_smoothing():
    t, pv = _pv_noisy()
    smooth = _moving_average(pv, WINDOW)
    bess = smooth - pv

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10.5, 7.2), sharex=True)

    ax1.plot(t, pv, color=C_PV, lw=1.4, alpha=0.7, label="原始光伏")
    ax1.plot(t, smooth, color=C_ACC, lw=2.2, label=f"平滑后（窗口 {WINDOW}）")
    ax1.set_ylabel("功率 (MW)")
    ax1.legend(fontsize=8.5)
    ax1.set_title("光伏功率平滑：储能补偿抹平高频波动  [教学示例]")
    ax1.set_ylim(-4, 36)

    ax2.fill_between(t, bess, 0, where=bess >= 0, color=C_DIS, alpha=0.4, label="放电补偿")
    ax2.fill_between(t, bess, 0, where=bess < 0, color=C_CHG, alpha=0.4, label="充电吸收")
    ax2.axhline(0, color="black", lw=0.7)
    note(ax2, "补偿功率峰值\n约 ±1.5 MW", (12, max(bess)), (14.5, 2.5))
    ax2.set_xlabel("小时 (h)")
    ax2.set_ylabel("储能补偿 (MW)")
    ax2.legend(fontsize=8.5)
    ax2.set_ylim(-3.5, 3.5)

    save(fig, "ch03_pv_smoothing")


def _moving_average(series, window):
    out = []
    half = window // 2
    n = len(series)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        out.append(sum(series[lo:hi]) / (hi - lo))
    return np.array(out)


def main():
    fig_smoothing()
    print("  ch03: 1 figure saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end