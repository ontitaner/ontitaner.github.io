# @AI_GENERATED
"""第 08 章配图：控制时间尺度分层（对数时间轴）。

时间范围均为 [行业典型量级] 的示意，用于说明“谁负责哪一段时间”，不是任何标准的限值。
"""
from __future__ import annotations

import json

from matplotlib.patches import Patch

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_PURPLE, IMG_DIR, plt, save

# (功能, 起, 止[s], 执行主体)
LAYERS = [
    ("硬件保护\n（BMS/PCS 保护、继电保护）", 1e-6, 5e-2, "local"),
    ("快速功率控制 / 稳控\n（协调控制器、稳控装置）", 2e-3, 2e-1, "fast"),
    ("快速频率响应、虚拟惯量", 2e-2, 2.0, "fast"),
    ("一次调频", 0.5, 60.0, "fast_or_ems"),
    ("防倒送 / 防超容闭环", 0.2, 10.0, "ems_fast"),
    ("AGC 跟踪", 2.0, 900.0, "ems_fast"),
    ("AVC 电压无功", 5.0, 900.0, "ems_fast"),
    ("需量控制\n（秒级计算，15 min 窗口）", 1.0, 900.0, "ems_slow"),
    ("峰谷套利、计划曲线", 900.0, 86400.0 * 2, "ems_slow"),
    ("SOH 评估、运维、对账", 86400.0, 3.2e7, "ops"),
]
OWNERS = {
    "local": ("设备本地（BMS/PCS/保护装置）", C_DIS),
    "fast": ("快速控制装置 / PCS 本地", C_PURPLE),
    "fast_or_ems": ("本地快速装置或 EMS（按项目）", C_ACC),
    "ems_fast": ("EMS 快环", C_CHG),
    "ems_slow": ("EMS 慢环 / 计划优化", "#5fa8d3"),
    "ops": ("运维与管理系统", C_GRID),
}
TICKS = [(1e-6, "1 μs"), (1e-3, "1 ms"), (1.0, "1 s"), (60.0, "1 min"), (3600.0, "1 h"),
         (86400.0, "1 天"), (2.6e6, "1 月"), (3.15e7, "1 年")]


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


def fig_timescales():
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    n = len(LAYERS)
    for i, (name, t0, t1, owner) in enumerate(LAYERS):
        y = n - 1 - i
        ax.barh(y, t1 - t0, left=t0, height=0.62, color=OWNERS[owner][1], alpha=0.9, edgecolor="white")
        ax.text(t1 * 1.35, y, name.replace("\n", " "), va="center", fontsize=8.8)
    # EMS 常规控制周期区间
    ax.axvspan(0.1, 1.0, color=C_CHG, alpha=0.08)
    ax.text(0.32, n - 0.35, "EMS 常规控制周期\n约 0.1～1 s", ha="center", va="bottom", fontsize=8.5, color=C_CHG,
            bbox=dict(fc="white", ec=C_CHG, alpha=0.95))
    ax.axvline(0.1, color=C_CHG, ls=":", lw=1)
    ax.axvline(1.0, color=C_CHG, ls=":", lw=1)
    ax.annotate("比 EMS 周期更快的，\n必须在设备或专用装置本地完成", xy=(0.08, n - 2.0), xytext=(2e-6, n - 4.3),
                fontsize=9, color=C_DIS, arrowprops=dict(arrowstyle="->", color=C_DIS))
    ax.set_xscale("log")
    ax.set_xlim(5e-7, 1e10)
    ax.set_ylim(-0.7, n + 0.6)
    ax.set_yticks([])
    ax.set_xticks([t for t, _ in TICKS], [s for _, s in TICKS])
    ax.minorticks_off()
    ax.set_xlabel("响应或决策的时间尺度（对数刻度）")
    ax.set_title("控制时间尺度分层：从微秒级保护到月级运维  [行业典型量级，示意]")
    ax.spines["left"].set_visible(False)
    handles = [Patch(color=c, label=label) for label, c in OWNERS.values()]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3, fontsize=8.5,
              title="主要执行主体", title_fontsize=9)
    save(fig, "ch08_timescales")
    manifest("ch08_timescales", [0.1, 1.0])


def main():
    fig_timescales()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
