# @AI_GENERATED
"""生成 ch01 脉冲响应图 img/ecm_pulse_response.png。数据取自 lab/ch01，保证一致。"""
from _figstyle import plt, save
import ch01_ecm_pulse as m

profile = [0.0] * 5 + [50.0] * 20 + [0.0] * 25
soc_log, i_log, v_log = m.simulate(profile, soc0=0.50)
ts = list(range(len(profile)))

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(ts, v_log, color="#1f77b4", lw=1.8, label="端电压 V_t")
ax.axvspan(5, 6, color="orange", alpha=.25)      # R0 瞬跳区
ax.axvspan(6, 25, color="green", alpha=.12)      # RC 下垂区
ax.axvspan(25, 50, color="gray", alpha=.08)      # 静置恢复区
ax.annotate("① R0 瞬时跌落", (5, v_log[5]), (7, 3.27), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="orange"))
ax.annotate("② RC 缓慢下垂", (15, v_log[15]), (16, 3.235), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="green"))
ax.annotate("③ 静置恢复", (30, v_log[30]), (33, 3.26), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="gray"))
ax.set_xlabel("时间步 (s)")
ax.set_ylabel("端电压 V_t (V)")
ax.set_title("ch01 1-RC 脉冲响应：R0 瞬跳 + RC 下垂 + 恢复（0.5C 放电，SOC≈50%）")
ax.legend(loc="lower right")
save(fig, "ecm_pulse_response.png")
# @AI_GENERATED: end
