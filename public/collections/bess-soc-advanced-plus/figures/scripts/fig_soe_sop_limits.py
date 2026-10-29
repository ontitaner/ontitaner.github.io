# @AI_GENERATED
"""第17章 30 分钟 SOE/SOP 约束取最小：img/soe_sop_limits.png。"""
from _figstyle import plt, save, C_DIS, C_CHG, C_GRID
import ch07_soe_sop as chapter

result = chapter.assess_capability(chapter.late_peak_input())
name_cn = {"energy_30min": "能量约束", "BMS_DC_to_AC": "BMS 直流→交流",
           "PCS_AC": "PCS 交流额定", "grid_export": "并网出口"}
labels = [name_cn.get(k, k) for k in result.limits_kw]
values = [result.limits_kw[k] for k in result.limits_kw]
colors = [C_DIS if k == result.limiting_reason else C_CHG for k in result.limits_kw]

fig, ax = plt.subplots(figsize=(8.2, 4.6))
bars = ax.bar(labels, values, color=colors, width=0.6)
ax.axhline(result.sop_kw, color=C_DIS, ls="--", lw=1.3,
           label=f"SOP(30 min) = {result.sop_kw:.0f} kW")
for bar, value, k in zip(bars, values, result.limits_kw):
    tag = "  ← 瓶颈" if k == result.limiting_reason else ""
    ax.text(bar.get_x() + bar.get_width() / 2, value + 45, f"{value:.0f}{tag}",
            ha="center", va="bottom", fontsize=9,
            color=C_DIS if k == result.limiting_reason else "k")
ax.annotate(f"SOE={result.soe_ac_kwh:.0f} kWh；按 2 MW 仅可持续 "
            f"{result.duration_at_grid_limit_min:.1f} min",
            (0, result.sop_kw), (0.0, max(values) * 1.02), fontsize=9, color=C_GRID)
ax.set_ylim(0, max(values) * 1.2)
ax.set_ylabel("放电能力 (kW，交流侧)")
ax.legend(loc="upper right")
save(fig, "soe_sop_limits", title="30 min SOP 由最紧约束决定（能量约束为瓶颈）")
# @AI_GENERATED: end