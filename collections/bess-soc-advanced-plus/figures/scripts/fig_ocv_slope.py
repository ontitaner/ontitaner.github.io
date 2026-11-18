# @AI_GENERATED
"""第06章 OCV 与斜率图：img/ocv_curve_slope.png。"""
from _figstyle import plt, save, C_CHG, C_OK, C_GRID
from soc_core import ocv_from_soc, ocv_slope

socs = [index / 200 for index in range(201)]
ocv = [ocv_from_soc(soc) for soc in socs]
slope = [ocv_slope(soc) for soc in socs]

fig, (ax_ocv, ax_slope) = plt.subplots(2, 1, figsize=(8, 6.2), sharex=True)

ax_ocv.plot(socs, ocv, color=C_CHG, lw=2, label="统一 25°C LFP OCV 表")
ax_ocv.axvspan(.30, .80, color=C_OK, alpha=.12, label="平台区 30%–80%")
ax_ocv.set_ylabel("开路电压 OCV (V)")
ax_ocv.legend(loc="center right")

ax_slope.plot(socs, slope, color=C_OK, lw=2, label="$dOCV/dSOC$")
ax_slope.axvspan(.30, .80, color=C_OK, alpha=.12)
ax_slope.annotate(f"平台区 50%：斜率≈{ocv_slope(.50):.2f} V/SOC，信息少",
                  (.50, ocv_slope(.50)), (.34, 1.1), fontsize=9,
                  arrowprops=dict(arrowstyle="->", color=C_OK))
ax_slope.annotate(f"边部 5%：斜率≈{ocv_slope(.05):.2f} V/SOC，修正强",
                  (.05, ocv_slope(.05)), (.12, 2.4), fontsize=9,
                  arrowprops=dict(arrowstyle="->", color=C_CHG))
ax_slope.set_xlabel("SOC (0–1)")
ax_slope.set_ylabel("斜率 (V/SOC)")
ax_slope.legend(loc="upper right")

save(fig, "ocv_curve_slope.png",
     title="OCV 与斜率：平台区斜率低、电压对 SOC 信息弱")
# @AI_GENERATED: end