# @AI_GENERATED
"""第12章：开环误差分解——左栏理论曲线，右栏关键时点柱状对比。"""
from _figstyle import plt, save, C_DIS, C_GRID, C_LIMIT

hours = list(range(25))
initial_error_pct = [20.0] * len(hours)
bias_error_pct = [0.5 * hour / 314.0 * 100 for hour in hours]
total_error_pct = [a + b for a, b in zip(initial_error_pct, bias_error_pct)]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))

# ── 左栏：理论误差分解 ─────────────────────────────────────────
ax1.fill_between(hours, 0, initial_error_pct, color=C_GRID, alpha=0.22,
                 label="初值误差：固定 +20%")
ax1.plot(hours, initial_error_pct, color=C_GRID, lw=2.0)
ax1.plot(hours, bias_error_pct, color=C_DIS, lw=2.2, label="零漂误差：+0.5 A 累积")
ax1.plot(hours, total_error_pct, color=C_LIMIT, lw=2.4, label="总偏差 = 初值 + 零漂")

for hour in [1, 4, 8, 16, 24]:
    value = bias_error_pct[hour]
    total = total_error_pct[hour]
    ax1.scatter([hour], [total], color=C_LIMIT, zorder=4, s=40)
    ax1.annotate(f"{hour} h\n+{value:.2f}%", (hour, total),
                 (hour + 0.4, total + 1.2), fontsize=7.8,
                 color=C_LIMIT,
                 arrowprops=dict(arrowstyle="->", color=C_LIMIT, lw=0.8))

ax1.text(12, 21.0, "初值错误永不消退",
         color=C_GRID, fontsize=9, fontweight="bold")
ax1.set_xlabel("运行时间 (h)")
ax1.set_ylabel("SOC 误差 (%)")
ax1.set_title("误差分解：初值恒定 + 零漂斜坡 → 总偏差")
ax1.set_ylim(0, 27)
ax1.legend(loc="upper left", fontsize=8)

# ── 右栏：关键时点柱状分解 ─────────────────────────────────────
key_hours = [1, 4, 8, 16, 24]
x_pos = range(len(key_hours))
width = 0.52
init_bars = ax2.bar(x_pos, [20.0] * len(key_hours), width,
                     color=C_GRID, alpha=0.6, label="初值误差 (固定)")
drift_bars = ax2.bar(x_pos, [bias_error_pct[h] for h in key_hours], width,
                     bottom=[20.0] * len(key_hours),
                     color=C_DIS, alpha=0.75, label="零漂累积")

for i, hour in enumerate(key_hours):
    dr = bias_error_pct[hour]
    tot = total_error_pct[hour]
    ax2.text(i, tot + 0.6, f"{tot:.2f}%", ha="center", fontsize=9,
             fontweight="bold", color=C_LIMIT)

ax2.set_xticks(x_pos)
ax2.set_xticklabels([f"{h} h" for h in key_hours])
ax2.set_ylabel("SOC 累积误差 (%)")
ax2.set_title("时点拆解：零漂随时间\"垒积木\"增长")
ax2.set_ylim(0, 27)
ax2.legend(loc="upper left", fontsize=7.8)

save(fig, "open_loop_error_components",
     title="开环漂移的两重来源：初值误差恒定保留 + 电流零漂随时间线性积累")
# @AI_GENERATED: end