# @AI_GENERATED
"""第20章 均衡收敛、损耗与同工况能力改善：img/balancing_convergence.png。"""
from _figstyle import plt, save, C_DIS, C_CHG, C_OK, C_GRID
import ch09_balancing_effect as m


def trace(step_fn):
    """复用 BMS 教学均衡步，记录极差与累计损耗。"""
    socs = list(m.PACK_SOC0)
    ranges, losses, total, steps = [m.spread(socs)], [0.0], 0.0, 0
    while m.spread(socs) > m.START_THRESHOLD and steps < 2000:
        total += step_fn(socs)
        ranges.append(m.spread(socs))
        losses.append(total)
        steps += 1
    return ranges, losses


range_passive, loss_passive = trace(m.passive_step)
range_active, loss_active = trace(m.active_step)
_, review, _ = m.teaching_case()

fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2))

axes[0].plot(range(len(range_passive)), [v * 100 for v in range_passive], "o-",
             color=C_DIS, ms=4, label="被动")
axes[0].plot(range(len(range_active)), [v * 100 for v in range_active], "s-",
             color=C_CHG, ms=4, label="主动")
axes[0].axhline(m.START_THRESHOLD * 100, color=C_GRID, lw=1, ls="--", label="阈值 2%")
axes[0].set(xlabel="均衡步", ylabel="簇级 SOC 极差 (%)", title="BMS 均衡使极差收敛")
axes[0].legend(fontsize=8.5)

bars = axes[1].bar(["被动", "主动"], [loss_passive[-1], loss_active[-1]], color=[C_DIS, C_CHG])
axes[1].set(ylabel="均衡损耗 (kWh)", title="主动转移少耗散")
for index, value in enumerate((loss_passive[-1], loss_active[-1])):
    axes[1].text(index, value, f"{value:.4f}", ha="center", va="bottom", fontsize=8.5)

axes[2].bar(["均衡前", "同工况复测"], [review.capability_before_kwh, review.capability_after_kwh],
            color=[C_GRID, C_OK])
axes[2].set(ylabel="最低簇口径可用能量 (kWh)", title=f"能力改善：{review.status}")
for index, value in enumerate((review.capability_before_kwh, review.capability_after_kwh)):
    axes[2].text(index, value, f"{value:.3f}", ha="center", va="bottom", fontsize=8.5)
axes[2].annotate(f"极差 {review.spread_before:.1%} → {review.spread_after:.1%}",
                 (0.5, review.capability_after_kwh * 0.55), ha="center", fontsize=8.5, color=C_GRID)
save(fig, "balancing_convergence",
     title="均衡收敛、损耗与同工况最低簇能力改善")
# @AI_GENERATED: end