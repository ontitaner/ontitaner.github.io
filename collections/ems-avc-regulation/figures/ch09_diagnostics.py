# @AI_GENERATED
"""第 09 章配图：AVC 异常诊断六步法 + 故障分类。

参数对齐章节 09.2~09.3：[教学示例]
- 六步诊断：数据冻结→站内排查→调度通信→控制逻辑→参数检查→启示
- 故障分类：通信 35% + 参数 25% + 控制 18% + 模型 12% + 一次设备 6% + 其他 4%
"""
from __future__ import annotations

import numpy as np

from _style import (C_DIS, C_CHG, C_ACC, C_LIMIT, C_GRID, C_OK, C_PURPLE,
                    IMG_DIR, save, note, plt)


def fig_diagnostic_steps():
    steps = [
        "步骤1\n数据冻结",
        "步骤2\n站内排查",
        "步骤3\n调度通信",
        "步骤4\n控制逻辑",
        "步骤5\n参数检查",
        "步骤6\n经验启示",
    ]
    durations = [0.1, 0.15, 0.12, 0.1, 0.18, 0.05]
    durations_ratio = [d / sum(durations) for d in durations]
    colors = [C_GRID, C_CHG, C_ACC, C_DIS, C_LIMIT, C_OK]
    descriptions = [
        "冻结异常时刻\n断面数据", "先排除设备\nPT/CT/PCS自身",
        "104/101协议\n连接状态", "死区/限幅/PI\n逆向验证",
        "档位/死区/KpKi\n逐一检查", "归档案例\n防重复出现",
    ]
    focuses = [
        "异常的AVC指令Q\n是合理≠故障", "PCS本地的Q余量\n与控制指令对比",
        "通信中断的\n时间戳比对", "如果Kp=-8000\n则电压反向调节",
        "多组参数交叉\n验证一致性", "同类故障的\n根因聚类",
    ]

    fig, ax = plt.subplots(figsize=(12, 4.5))

    y = np.arange(len(steps))
    bar_width = 0.7
    ax.barh(y, durations_ratio, bar_width, color=colors, alpha=0.85, zorder=3)

    ax.set_xlim(0, 0.35)
    ax.set_yticks(y, steps)
    ax.set_xlabel("排查时间占比")
    ax.set_title("AVC 异常诊断六步法：由外到内逐层排查")
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)

    for i, (d, desc, foc, c) in enumerate(zip(durations_ratio, descriptions, focuses, colors)):
        ax.text(d + 0.003, i, desc, fontsize=7.5, color=c, va="center",
                bbox=dict(fc="white", ec=c, alpha=0.9, boxstyle="round,pad=0.12"))
        ax.text(d + 0.003, i - 0.32, foc, fontsize=7, color=C_GRID, va="center", alpha=0.85,
                bbox=dict(fc="white", ec=C_GRID, alpha=0.7, boxstyle="round,pad=0.1"))

    save(fig, "ch09_diagnostic_steps")


def fig_fault_pie():
    faults = ["通信中断", "参数偏移", "控制逻辑", "模型不准", "一次设备", "其他"]
    sizes = [35, 21, 18, 14, 8, 4]
    colors_fault = [C_LIMIT, C_DIS, C_ACC, C_OK, C_CHG, C_GRID]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4),
                             gridspec_kw={"width_ratios": [1, 1.2]})

    ax = axes[0]
    wedges, texts, autotexts = ax.pie(sizes, labels=faults, autopct="%1.0f%%",
                                      colors=colors_fault, textprops={"fontsize": 8},
                                      pctdistance=0.82)
    for at in autotexts:
        at.set_fontsize(8.5)
        at.set_fontweight("bold")
    ax.set_title("故障类型分布")

    ax = axes[1]
    fault_types = ["通信中断", "参数偏移\n(死区/KpKi/档位)", "控制逻辑",
                   "模型不准\n(阻抗/LTC)", "一次设备\n(PT断线/PCS)", "其他"]
    solutions = [
        "检查104/101状态、主备切换",
        "逐参数回查、取消死区验证",
        "逆向推演PI运算、限幅全放开",
        "校准变压器阻抗、LTC延迟",
        "PT熔断器、PCS单机放电",
        "归档复盘、纳入巡检",
    ]
    seq_colors = [C_LIMIT, C_DIS, C_ACC, C_OK, C_CHG, C_GRID]
    y_pos = np.arange(len(fault_types))

    ax.barh(y_pos, sizes, color=seq_colors, alpha=0.85, height=0.55)
    for i, (ft, sol, sz, c) in enumerate(zip(fault_types, solutions, sizes, seq_colors)):
        ax.text(sz + 0.6, i, f"{ft}\n→ {sol}", fontsize=8, color=c, va="center")

    ax.set_yticks([])
    ax.set_xlim(0, 42)
    ax.set_xlabel("占比 (%)")
    ax.set_title("分类 + 排查思路")
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)

    fig.suptitle("AVC 异常故障分类：通信类排第一，参数类多应逐项验证  [教学示例]", fontsize=11)
    save(fig, "ch09_diagnostic_faults")


def main():
    fig_diagnostic_steps()
    fig_fault_pie()
    print(f"  ch09: 2 figures saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end