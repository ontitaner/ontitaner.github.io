# @AI_GENERATED
"""生成 ch03 脉冲辨识图 img/identify_pulse.png。数据取自 lab/ch03。"""
from _figstyle import plt, save
import ch03_identify as m

t, i_log, v_over = m._gen_pulse()

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(t, v_over, color="#1f77b4", lw=1.6, marker="o", ms=2, label="过电位 I·R0+V1")
# R0 瞬跳段：第 4→5 步
ax.annotate("① 瞬跳 → R0", (5, v_over[5]), (8, v_over[5] + 0.02), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="orange"))
# τ 指数拟合段：释放后
ax.axvspan(36, 45, color="green", alpha=.12)
ax.annotate("② 恢复段指数衰减 → τ", (40, v_over[40]), (24, v_over[40] + 0.03), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="green"))
ax.set_xlabel("时间步 (s)")
ax.set_ylabel("过电位 (V)")
ax.set_title("ch03 脉冲辨识：瞬跳定 R0、恢复段指数拟合定 τ（C1=τ/R1）")
ax.legend(loc="upper right")
save(fig, "identify_pulse.png")
# @AI_GENERATED: end
