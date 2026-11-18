# @AI_GENERATED
"""第01章：EMS 能力计算——多系统约束如何汇入最终计划。"""
from _figstyle import plt, save, C_CHG, C_DIS, C_OK, C_GRID, C_LIMIT

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.6))

# ── 左栏：各系统提供的事实 ──────────────────────────────────────
groups = ["BMS", "PCS", "PCC"]
items = ["SOC · SOH · 告警\n直流可放功率", "交流实际功率\n效率 · 设备限值", "并网出口限制\n调度约束"]
colors_left = [C_CHG, C_OK, C_GRID]
bars = ax1.bar(groups, [3, 3, 3], color=colors_left, width=0.55, alpha=0.18)
for i, (g, item, c) in enumerate(zip(groups, items, colors_left)):
    ax1.text(i, 1.5, item, ha="center", va="center", fontsize=9.5, color=c, fontweight="bold")
ax1.set_ylim(0, 3.6)
ax1.set_ylabel("")
ax1.set_title("各系统上送的事实")
ax1.tick_params(left=False, labelleft=False)
ax1.spines["left"].set_visible(False)

# 箭头：数据 → EMS
for i, c in enumerate(colors_left):
    ax1.annotate("", xy=(i, -0.35), xytext=(i, -0.05),
                 arrowprops=dict(arrowstyle="->", color=c, lw=1.8),
                 annotation_clip=False)
ax1.text(1.0, -0.75, "EMS 统一口径 · 校验 · 计算", ha="center", fontsize=10,
         color=C_CHG, fontweight="bold")

# ── 右栏：EMS 取最紧约束 ────────────────────────────────────────
limits = ["能量约束\nSOE → SOP", "BMS\n直流限值", "PCS\n交流限值", "PCC\n并网限值"]
values = [1289, 2200, 2500, 2000]
colors_right = [C_DIS, C_CHG, C_OK, C_GRID]
bars = ax2.bar(limits, values, color=colors_right, width=0.55, alpha=0.85)
ax2.axhline(y=1289, color=C_LIMIT, ls="--", lw=1.5, label=f"MIN = 1289 kW")

for bar, v, label in zip(bars, values, limits):
    tag = "  ← 瓶颈" if v == 1289 else ""
    ax2.text(bar.get_x() + bar.get_width() / 2, v + 55, f"{v}{tag}",
             ha="center", fontsize=9, color=C_LIMIT if v == 1289 else "#555")
ax2.set_ylim(0, max(values) * 1.22)
ax2.set_ylabel("功率 (kW，交流侧)")
ax2.set_title("EMS 取所有约束的最小值")
ax2.legend(loc="upper right", fontsize=8.5)

# 箭头：MIN → 计划
ax2.annotate("发布计划\n功率 · 时长 · 限制原因", xy=(0, 1289), xytext=(1.5, 1289 + 380),
             fontsize=9, color=C_LIMIT, fontweight="bold", ha="center",
             arrowprops=dict(arrowstyle="->", color=C_LIMIT, lw=1.5))

save(fig, "arch_decision",
     title="EMS 能力计算：BMS / PCS / PCC 各有事实边界，EMS 校验后取最紧约束发布计划")
# @AI_GENERATED: end