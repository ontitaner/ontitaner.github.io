# @AI_GENERATED
"""第 09 章配图：①各自限幅后相加 vs 合成后统一投影；②AGC 端到端延迟预算。

图①直接调用 lab/ems_lab/pipeline.py；图②的各环节耗时均为 [教学示例]。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.pipeline import Capability, ControlRequest, OperatingState, arbitrate, naive_limit_each_then_sum, project


def manifest(name: str, numbers: list[float]) -> None:
    """为正文图中标注对照表输出数字清单。"""
    payload = {
        "_comment": "@AI_GENERATED",
        "figure": f"{name}.png",
        "numbers": sorted(set(float(n) for n in numbers)),
        "_comment_end": "@AI_GENERATED: end",
    }
    (IMG_DIR / f"{name}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def fig_limit_then_sum():
    cap = Capability(1000, 800, "BMS 降额")
    st = OperatingState(0.0, cap, 0.0, None, 50.0, 0.5, None)
    cases = [
        ("情形一：同向叠加\nAGC +900，一次调频 +70（49.90 Hz）", 900, 70),
        ("情形二：反向叠加\nAGC +900，一次调频 −70（50.10 Hz）", 900, -70),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    for ax, (title, agc, pfr) in zip(axes, cases):
        reqs = [ControlRequest("agc", agc, "base", 20, ""), ControlRequest("pfr", pfr, "delta", 30, "")]
        naive = naive_limit_each_then_sum(reqs, cap)
        combined, _ = arbitrate(reqs)
        right = project(combined, st).p_out_kw
        labels = ["合成请求\n（理想）", "错误：各自限幅\n再相加", "正确：先合成\n再统一投影"]
        vals = [combined, naive, right]
        colors = [C_GRID, C_LIMIT, C_OK]
        bars = ax.bar(labels, vals, color=colors, width=0.55, alpha=0.9)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 15, f"{v:+.0f} kW", ha="center", fontsize=10)
        ax.axhline(800, color=C_LIMIT, ls="--", lw=1.3)
        ax.text(1.0, 1045, "红色虚线：BMS 可放能力 800 kW", color=C_LIMIT, ha="center", fontsize=9)
        diff = naive - 800 if naive > 800 else naive - right
        note = f"超出可放能力\n{diff:.0f} kW" if naive > 800 else f"比可行最优值\n少放 {-diff:.0f} kW"
        ax.text(1, 420, note, color="white", ha="center", va="center", fontsize=10, fontweight="bold")
        ax.set_title(title, fontsize=10)
        ax.set_ylim(0, 1100)
    axes[0].set_ylabel("储能有功指令 (kW)  放电为正")
    fig.suptitle("为什么不能让各服务分别限幅后相加（1 MW 储能，BMS 降额到可放 800 kW）  [教学示例]", fontsize=11)
    save(fig, "ch09_limit_then_sum")
    manifest("ch09_limit_then_sum", [1, -70, 49.9, 50.1, 70, 730, 800, 830, 870, 900, 970])


# AGC 端到端延迟预算：(环节, 典型, 较差) 单位 s，均为 [教学示例]
BUDGET = [
    ("主站计算与下发排队", 0.2, 0.5),
    ("调度数据网 + 纵向加密", 0.1, 0.3),
    ("远动机规约处理与转发", 0.05, 0.2),
    ("EMS 等待控制周期", 0.1, 0.2),
    ("EMS 校验与计算", 0.02, 0.05),
    ("下发 PCS（通信管理机）", 0.2, 1.0),
    ("PCS 响应与功率爬坡", 0.8, 2.0),
    ("测量采样与上送调度", 0.5, 1.0),
]
COLORS = [C_GRID, "#adb5bd", C_PURPLE, C_CHG, "#5fa8d3", C_ACC, C_DIS, C_OK]


def fig_latency_budget():
    fig, ax = plt.subplots(figsize=(11, 3.9))
    rows = [("典型情况", 1), ("较差情况", 2)]
    for y, (label, col) in enumerate(rows[::-1]):
        left = 0.0
        for (name, *vals), c in zip(BUDGET, COLORS):
            v = vals[col - 1]
            ax.barh(y, v, left=left, color=c, edgecolor="white", height=0.55, label=name if y == 0 else None)
            if v >= 0.3:
                ax.text(left + v / 2, y, f"{v:.1f}", ha="center", va="center", fontsize=8.5, color="white")
            left += v
        ax.text(left + 0.05, y, f"合计 {left:.2f} s", va="center", fontsize=10)
    ax.set_yticks([0, 1], [r[0] for r in rows[::-1]])
    ax.axvline(3.0, color=C_LIMIT, ls="--", lw=1.3)
    ax.text(3.03, 1.42, "项目延迟预算 3 s（示例）", color=C_LIMIT, fontsize=9)
    ax.set_xlim(0, 6.6)
    ax.set_ylim(-0.5, 1.6)
    ax.set_xlabel("从调度发出 AGC 指令起的累计时间 (s)")
    ax.set_title("一条 AGC 指令的端到端延迟预算：最大的几段往往不在 EMS 计算里  [教学示例]")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=4, fontsize=8.5)
    ax.text(0.5, -0.34, "分段参数：典型 0.2/0.1/0.05/0.1/0.02/0.2/0.8/0.5 s；较差 0.5/0.3/0.2/0.2/0.05/1.0/2.0/1.0 s",
            transform=ax.transAxes, ha="center", va="top", fontsize=7.2)
    ax.grid(axis="y", visible=False)
    save(fig, "ch09_latency_budget")
    manifest("ch09_latency_budget", [0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.97, 2.0, 3.0, 5.25])


def main():
    fig_limit_then_sum()
    fig_latency_budget()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
