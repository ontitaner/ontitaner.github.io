# @AI_GENERATED
"""第08章 动态参数辨识图：img/identify_pulse.png。"""
import math

from _figstyle import plt, save, C_CHG, C_DIS, C_GRID, C_OK
import ch04_identification as m

times_s, currents_a, voltage_drop_v = m.generate_noisy_dynamic_data(seed=41)
result = m.run_dynamic_identification()
dynamic_v = 0.0
fit_v = []
for index, current_a in enumerate(currents_a):
    fit_v.append(result.r0_ohm * current_a + result.r_dynamic_ohm * dynamic_v
                 + result.offset_v)
    if index < len(currents_a) - 1:
        recovery = math.exp(-(times_s[index + 1] - times_s[index]) / result.tau_s)
        dynamic_v = recovery * dynamic_v + (1.0 - recovery) * current_a

fig, (ax_current, ax_voltage) = plt.subplots(2, 1, figsize=(8, 5.6), sharex=True)
ax_current.step(times_s, currents_a, where="post", color=C_GRID, lw=1.4, label="脉冲电流")
ax_current.set_ylabel("电流 (A，放电为正)")
ax_current.legend(loc="upper right")

ax_voltage.plot(times_s, voltage_drop_v, color=C_CHG, lw=1.2, label="合成过电压（含噪声）")
ax_voltage.plot(times_s, fit_v, color=C_DIS, lw=1.3, ls="--",
                label=f"完整动态拟合  $R_0$={result.r0_ohm*1e3:.3f} mΩ, $\\tau$={result.tau_s:.0f} s")
ax_voltage.annotate(f"验证 RMSE={result.validation.rmse*1e3:.2f} mV",
                    (times_s[len(times_s)//2], max(voltage_drop_v)*.7),
                    (times_s[len(times_s)//3], max(voltage_drop_v)*.95), fontsize=9,
                    arrowprops=dict(arrowstyle="->", color=C_OK))
ax_voltage.set_xlabel("时间 (s)")
ax_voltage.set_ylabel("过电压 (V)")
ax_voltage.legend(loc="upper right")
save(fig, "identify_pulse", title="带噪多点脉冲：受界 $R_0$、$R_1$、$\\tau$ 辨识")
# @AI_GENERATED: end