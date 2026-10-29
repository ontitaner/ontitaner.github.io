# @AI_GENERATED
"""第12章：初值误差与电流零漂构成开环SOC总偏差。"""
from _figstyle import plt, save, C_CHG, C_DIS, C_PURPLE, C_GRID

hours = list(range(25))
initial_error_pct = [20.0] * len(hours)
bias_error_pct = [0.5 * hour / 314.0 * 100 for hour in hours]
total_error_pct = [a+b for a, b in zip(initial_error_pct, bias_error_pct)]

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(hours, initial_error_pct, color=C_GRID, lw=2, label="初值误差：固定 +20%")
ax.plot(hours, bias_error_pct, color=C_DIS, lw=2, label="零漂误差：+0.5 A 累积")
ax.plot(hours, total_error_pct, color=C_PURPLE, lw=2.4, label="总偏差")
for hour in [1, 8, 24]:
    value = bias_error_pct[hour]
    ax.scatter([hour], [value], color=C_DIS, zorder=3)
    ax.annotate(f"{hour} h：零漂 +{value:.2f}%", (hour, value), (hour+0.6, value+1.4), fontsize=8.8,
                arrowprops=dict(arrowstyle="->", color=C_DIS))
ax.text(12, 20.7, "初值错误不会自行消失", color=C_GRID, fontsize=9)
ax.set(xlabel="运行时间 (h)", ylabel="SOC 误差 (%)", title="开环误差分解：初值误差恒定，电流零漂持续增长")
ax.set_ylim(0, 26)
ax.legend(loc="lower right")

save(fig, "open_loop_error_components", title="17:30 不应只相信开环 SOC：初值与零漂都会改变晚峰能量判断")
# @AI_GENERATED: end