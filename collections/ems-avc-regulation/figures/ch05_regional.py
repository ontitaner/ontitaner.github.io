# @AI_GENERATED
"""第 05 章配图：三大区域 AVC 调度细则参数对比。

参数对齐章节 05.2~05.3：[教学示例]
- 四维参数：死区/响应时间/合格带宽/调节速率
- 华东最严、山西带宽最窄、东北响应宽松但里程补偿不同
"""
from __future__ import annotations

import numpy as np

from _style import (C_OK, C_ACC, C_TARGET, C_LIMIT, C_Q_ABSORB,
                    IMG_DIR, save, note, plt)


def fig_regional_compare():
    params = ["死区宽度 ±(pu)", "响应时间 (s)", "合格带宽 ±(pu)", "调节速率 (kvar/s)"]
    ref_vals = [0.010, 60, 0.010, 500]
    ref_label = "通用参考"
    regions = ["华东", "东北", "山西"]
    data = {
        "华东": [0.007, 30, 0.007, 500],
        "东北": [0.010, 60, 0.010, 300],
        "山西": [0.008, 45, 0.005, 400],
    }
    notes = {
        0: "华东最窄\n必须快速响应",
        1: "华东最严 30s\n东北宽松 60s",
        2: "山西极窄\n留给死区空间极小",
        3: "东北最慢\n必须保证容量",
    }

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7), sharex=False)
    for idx, (ax, param) in enumerate(zip(axes.flat, params)):
        ref = ref_vals[idx]
        x = np.arange(3)
        vals = [data[r][idx] for r in regions]
        better_if_less = idx in (0, 1)
        colors = []
        for v in vals:
            if better_if_less:
                colors.append(C_OK if v <= ref else C_LIMIT)
            else:
                colors.append(C_OK if v >= ref else C_LIMIT)

        ax.bar(x, vals, color=colors, alpha=0.85, width=0.45)
        ax.axhline(ref, color=C_TARGET, ls="--", lw=2, label=f"{ref_label} {ref}")
        ax.set_xticks(x, regions)
        for bar, val, col in zip(ax.containers[0], vals, colors):
            offset = ref * 0.04 if val > 0 else -0.3
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + offset,
                    str(val), ha="center", fontsize=10, fontweight="bold", color=col)
        ax.set_title(param, fontsize=10)
        if idx >= 2:
            ax.legend(fontsize=7.5, loc="upper right")
        # 区域标注
        if idx in notes:
            ax.text(0.5, 0.85, notes[idx], transform=ax.transAxes,
                    ha="center", fontsize=8.5, color=C_TARGET, style="italic",
                    bbox=dict(fc="white", ec=C_TARGET, alpha=0.9, boxstyle="round,pad=0.2"))

    fig.suptitle("三大区域 AVC 调度细则参数对比：四维差异  [教学示例]", fontsize=11)
    save(fig, "ch05_regional_compare")


def main():
    fig_regional_compare()
    print(f"  ch05: saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end