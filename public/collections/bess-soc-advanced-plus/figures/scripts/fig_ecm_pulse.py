# @AI_GENERATED
"""第07章 ECM 脉冲响应图：img/ecm_pulse.png。"""
from _figstyle import plt, save, C_CHG, C_DIS, C_OK, C_GRID
from soc_core import DEFAULT_MODEL_PARAMS, ModelState, advance_model

profile = [0.0] * 5 + [50.0] * 20 + [0.0] * 25
state = ModelState(0.50)
voltages = []
for current_a in profile:
    step = advance_model(state, current_a, 1.0, params=DEFAULT_MODEL_PARAMS)
    voltages.append(step.terminal_voltage_v)
    state = step.state_after
seconds = list(range(len(profile)))

fig, ax = plt.subplots(figsize=(8, 4.4))
ax.plot(seconds, voltages, color=C_CHG, lw=1.8, label="314 Ah LFP 单体端电压")
ax.axvspan(5, 6, color=C_DIS, alpha=.18, label="R0 瞬时压降")
ax.axvspan(6, 25, color=C_OK, alpha=.12, label="动态支路响应")
ax.axvspan(25, 50, color=C_GRID, alpha=.10, label="静置恢复")
ax.annotate("① R0 瞬时压降", (5, voltages[5]), (7, voltages[5] + .006), fontsize=9,
            arrowprops=dict(arrowstyle="->", color=C_DIS))
ax.annotate("② 动态支路继续响应", (15, voltages[15]), (16, voltages[15] - .008), fontsize=9,
            arrowprops=dict(arrowstyle="->", color=C_OK))
ax.annotate("③ 静置后动态压降恢复", (30, voltages[30]), (32, voltages[30] + .006), fontsize=9,
            arrowprops=dict(arrowstyle="->", color=C_GRID))
ax.set_xlabel("时间 (s)")
ax.set_ylabel("端电压 $V_t$ (V)")
ax.legend(loc="lower right")
save(fig, "ecm_pulse", title="314 Ah LFP 的 ECM 脉冲响应（50 A 放电）")
# @AI_GENERATED: end