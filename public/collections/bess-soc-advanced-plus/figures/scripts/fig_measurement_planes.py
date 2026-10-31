# @AI_GENERATED
"""第03章：四个测量平面——单体→直流→交流→并网的层级换算。"""
from _figstyle import plt, save, C_CHG, C_DIS, C_OK, C_GRID, C_LIMIT

fig, ax = plt.subplots(figsize=(8.5, 5.5))

planes = ["并网点 PCC\nP_pcc · 调度限制", "交流侧 PCS\nP_pcs_ac · Q_pcs · 效率",
          "直流侧 BMS\nV_stack · I_stack · P_batt_dc", "单体 Cell\nV_cell · I_branch · T_cell"]
colors = [C_LIMIT, C_OK, C_CHG, C_GRID]
usages = ["调度履约", "PCS 执行", "BMS 保护", "OCV/RC/SOC 模型"]
y_positions = [3.5, 2.5, 1.5, 0.5]

bars = ax.barh(y_positions, [5.5] * 4, height=0.55, color=colors, alpha=0.22,
               edgecolor=colors, linewidth=1.3)

for y, plane, usage, c in zip(y_positions, planes, usages, colors):
    ax.text(0.15, y, plane, va="center", fontsize=10, color=c, fontweight="bold")
    ax.text(5.7, y, usage, va="center", fontsize=9, color=c, style="italic", ha="left")

# 换算箭头
conversions = [
    (3.2, 2.8, "− 站用电"),
    (2.2, 1.8, "× η_PCS (DC→AC)"),
    (1.2, 0.8, "× N_s 串联 · × N_p 并联"),
]
for y_top, y_bot, label in conversions:
    ax.annotate("", xy=(2.75, y_bot), xytext=(2.75, y_top),
                arrowprops=dict(arrowstyle="->", color=C_GRID, lw=1.5))
    ax.text(3.05, (y_top + y_bot) / 2, label, va="center", fontsize=9.5, color=C_LIMIT)

ax.set_xlim(0, 7.2)
ax.set_ylim(-0.1, 4.1)
ax.set_yticks([])
ax.set_xticks([])
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.tick_params(left=False, bottom=False)

# 右侧用途虚线
for y, usage, c in zip(y_positions, usages, colors):
    ax.plot([5.5, 6.8], [y, y], color=c, lw=0.8, ls=":", alpha=0.6)

ax.set_title("四个测量平面：数值相同不代表含义相同，跨平面换算必须显式处理", fontsize=11)

save(fig, "measurement_planes",
     title="测量平面与换算：单体 → 直流 → 交流 → 并网，每层各有用途与换算因子")
# @AI_GENERATED: end