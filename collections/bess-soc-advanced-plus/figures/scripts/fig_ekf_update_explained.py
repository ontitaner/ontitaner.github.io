# @AI_GENERATED
"""第13章：一次EKF更新如何将电压残差转换为SOC修正。"""
from _figstyle import plt, save, C_CHG, C_DIS, C_OK, C_GRID

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.4))

voltage_labels = ["预测电压", "实测电压"]
voltage_values = [3.309, 3.284]
bars = ax1.bar(voltage_labels, voltage_values, color=[C_GRID, C_CHG], width=.55)
ax1.set_ylim(3.24, 3.34)
ax1.set_ylabel("端电压 (V)")
ax1.set_title("电压层：预测高于实测，残差 r=−25 mV")
for bar, value in zip(bars, voltage_values):
    ax1.text(bar.get_x()+bar.get_width()/2, value+.003, f"{value:.3f} V", ha="center", fontsize=9)
ax1.annotate("r = 3.284 − 3.309 = −0.025 V", (.5, 3.285), (.10, 3.255), fontsize=9,
             arrowprops=dict(arrowstyle="->", color=C_DIS))

soc_labels = ["预测 SOC", "量测修正", "修正后 SOC", "下一拍 SOC"]
soc_values = [70.0, -16.4, 53.6, 53.596]
colors = [C_GRID, C_DIS, C_OK, C_CHG]
bars = ax2.bar(soc_labels, soc_values, color=colors, width=.6)
ax2.axhline(0, color=C_GRID, lw=1)
ax2.set_ylabel("SOC (%) / 修正量 (%)")
ax2.set_title("状态层：K=6.55 SOC/V 将残差映射为 SOC 修正")
for bar, value in zip(bars, soc_values):
    y = value + 1.2 if value >= 0 else value - 3.2
    ax2.text(bar.get_x()+bar.get_width()/2, y, f"{value:+.3f}%", ha="center", fontsize=8.6)
ax2.set_ylim(-25, 80)

save(fig, "ekf_update_explained", title="一次 EKF 更新：电压预测偏高 → SOC 下调 → 进入下一拍状态预测")
# @AI_GENERATED: end