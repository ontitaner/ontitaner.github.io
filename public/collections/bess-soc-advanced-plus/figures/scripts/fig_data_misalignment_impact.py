# @AI_GENERATED
"""第04章：错拍如何从样本配对误差演变为能力误判。"""
from _figstyle import plt, save, C_CHG, C_DIS, C_GRID, C_LIMIT

fig, axes = plt.subplots(3, 1, figsize=(9, 7.2), sharex=True)
time_s = [0, 1, 2]
voltage_v = [3.300, 3.250, 3.200]
current_a = [0, 50, 100]

axes[0].plot(time_s, voltage_v, "o-", color=C_CHG, label="单体电压")
axes[0].set_ylabel("电压 (V)")
axes[0].set_title("原始遥测：电压在 t=1 s 已降至 3.250 V")
axes[0].annotate("V[1]=3.250 V", (1, 3.250), (1.18, 3.285), fontsize=9,
                 arrowprops=dict(arrowstyle="->", color=C_CHG))
axes[0].legend(loc="upper right")

axes[1].step(time_s, current_a, where="post", color=C_DIS, lw=2, label="电流")
axes[1].set_ylabel("电流 (A)")
axes[1].set_title("正确同窗电流为 I[1]=50 A，下一拍才升至 100 A")
axes[1].annotate("I[1]=50 A", (1, 50), (0.18, 78), fontsize=9,
                 arrowprops=dict(arrowstyle="->", color=C_DIS))
axes[1].annotate("I[2]=100 A", (2, 100), (1.35, 78), fontsize=9,
                 arrowprops=dict(arrowstyle="->", color=C_DIS))
axes[1].legend(loc="upper left")

labels = ["正确同窗\nV[1]配I[1]", "错误错拍\nV[1]配I[2]"]
r0_mohm = [1.0, 0.5]
bars = axes[2].bar(labels, r0_mohm, color=[C_CHG, C_LIMIT], width=.55)
axes[2].set_ylabel("估计 R0 (mΩ)")
axes[2].set_title("同一电压下降，错拍使 R0 从 1.00 mΩ 低估为 0.50 mΩ")
for bar, value, note in zip(bars, r0_mohm, ["正确", "−50%"]):
    axes[2].text(bar.get_x()+bar.get_width()/2, value+.04, f"{value:.2f} mΩ\n{note}",
                 ha="center", va="bottom", fontsize=9)
axes[2].set_ylim(0, 1.25)
axes[2].set_xlabel("样本配对方式")

save(fig, "data_misalignment_impact", title="错拍不是小误差：参数低估会继续污染 SOC 与晚峰能力")
# @AI_GENERATED: end