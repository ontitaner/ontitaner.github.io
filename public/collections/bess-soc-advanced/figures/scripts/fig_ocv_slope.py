# @AI_GENERATED
"""生成 ch02 OCV 曲线与斜率图 img/ocv_curve_slope.png。数据取自 lab/ch02。"""
from _figstyle import plt, save
import ch02_ocv_slope as m

# NCM 对比示意曲线（仅用于显示"有斜率"的对照，非本教程统一电芯）
NCM_V = (3.00, 3.40, 3.52, 3.60, 3.64, 3.68, 3.73, 3.80, 3.89, 3.98, 4.08, 4.13, 4.18)

socs = [i / 200 for i in range(201)]            # 0..1 细网格
lfp = [m.ocv_from_soc(s) for s in socs]
slope = [m.ocv_slope(s) for s in socs]
ncm = [m.interp(s, m.OCV_SOC, NCM_V) for s in socs]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6), sharex=True)
ax1.plot(socs, lfp, color="#1f77b4", lw=2, label="LFP（本教程电芯）")
ax1.plot(socs, ncm, color="#d62728", lw=1.3, ls="--", label="NCM（对比示意）")
ax1.axvspan(0.30, 0.80, color="green", alpha=.10)
ax1.set_ylabel("开路电压 OCV (V)")
ax1.set_title("ch02 OCV-SOC 特性：LFP 平台区（阴影）几乎看不出 SOC")
ax1.legend(loc="center right")

ax2.plot(socs, slope, color="#2ca02c", lw=2)
ax2.axvspan(0.30, 0.80, color="green", alpha=.10)
ax2.annotate("平台区 ≈0.1 V/SOC\n5 mV→5% SOC 误差", (0.55, 0.1), (0.4, 1.2), fontsize=9,
             arrowprops=dict(arrowstyle="->", color="green"))
ax2.annotate("陡峭区 ≈3 V/SOC\n5 mV→0.17% 误差", (0.05, 3.0), (0.12, 2.4), fontsize=9,
             arrowprops=dict(arrowstyle="->", color="#1f77b4"))
ax2.set_xlabel("SOC")
ax2.set_ylabel("斜率 dOCV/dSOC (V/SOC)")
save(fig, "ocv_curve_slope.png")
# @AI_GENERATED: end
