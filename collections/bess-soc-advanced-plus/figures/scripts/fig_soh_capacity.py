# @AI_GENERATED
"""第09章 完整放电循环电量积分与 C_eff/SOH 标定 img/soh_capacity.png。"""
from _figstyle import plt, save, C_CHG, C_OK, C_GRID, C_LIMIT, C_ACC

# 95%→5% 完整放电，314 A 恒流，90 段×36 s
C_RATED = 314.0
SOC_START, SOC_END = 0.95, 0.05
SEGMENTS, DT_S, CURRENT = 90, 36.0, 314.0

times_h = [i * DT_S / 3600.0 for i in range(SEGMENTS + 1)]
soc = [SOC_START]
cum_ah = [0.0]
for i in range(SEGMENTS):
    dq = CURRENT * DT_S / 3600.0
    cum_ah.append(cum_ah[-1] + dq)
    soc.append(soc[-1] - dq / C_RATED)

net_ah = cum_ah[-1]
span = SOC_START - SOC_END
c_eff = net_ah / span
soh = c_eff / C_RATED

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.6))

ax1.plot(times_h, [s * 100 for s in soc], color=C_CHG, lw=2.2, label="簇 SOC")
ax1.axhline(SOC_END * 100, color=C_LIMIT, ls="--", lw=1.2, label="放电下限 5%")
ax1.fill_between(times_h, [SOC_END * 100] * len(times_h), [s * 100 for s in soc],
                 color=C_CHG, alpha=0.12)
ax1.set_xlabel("时间 (h)")
ax1.set_ylabel("SOC (%)")
ax1.set_title(f"完整放电 95%→5%：积分净电量 {net_ah:.1f} Ah")
ax1.legend()

labels = ["完整循环\n跨度 90%", "部分循环\n跨度 40%（拒绝）"]
spans = [0.90, 0.40]
bars = ax2.bar(labels, [s * 100 for s in spans], color=[C_OK, C_GRID], width=0.55)
ax2.axhline(80, color=C_ACC, ls="--", lw=1.2, label="最小跨度 80%")
for b, s in zip(bars, spans):
    ax2.text(b.get_x() + b.get_width() / 2, s * 100 + 2, f"{s*100:.0f}%",
             ha="center", fontsize=9)
ax2.set_ylabel("SOC 跨度 (%)")
ax2.set_ylim(0, 105)
ax2.set_title(f"C_eff = {c_eff:.1f} Ah，SOH = {soh*100:.2f}%")
ax2.legend()

save(fig, "soh_capacity",
     title="有效容量 C_eff 与 SOH 标定：只有端点明确、跨度达标的完整循环才被接受")
# @AI_GENERATED: end