# @AI_GENERATED
"""生成 ch07 均衡收敛图 img/balancing_convergence.png。复用 lab/ch07 step 函数逐步记录极差。"""
from _figstyle import plt, save
import ch07_balancing as m


def trace(step_fn):
    """复用 ch07 的单步均衡逻辑，逐步记录极差与累计损耗。"""
    socs = list(m.PACK_SOC0)
    rng_log, loss_log, total = [m.spread(socs)], [0.0], 0.0
    steps = 0
    while m.spread(socs) > m.START_THRESHOLD and steps < 2000:
        total += step_fn(socs)
        rng_log.append(m.spread(socs))
        loss_log.append(total)
        steps += 1
    return rng_log, loss_log


rng_p, loss_p = trace(m.passive_step)
rng_a, loss_a = trace(m.active_step)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
ax1.plot(range(len(rng_p)), [r * 100 for r in rng_p], color="#d62728",
         lw=1.8, marker="o", ms=4, label="被动均衡")
ax1.plot(range(len(rng_a)), [r * 100 for r in rng_a], color="#1f77b4",
         lw=1.8, marker="s", ms=4, label="主动均衡")
ax1.axhline(m.START_THRESHOLD * 100, color="gray", lw=1, ls="--", label="启动阈值 2%")
ax1.set_xlabel("均衡步")
ax1.set_ylabel("单体 SOC 极差 (%)")
ax1.set_title("极差收敛")
ax1.legend()

ax2.bar(["被动", "主动"], [loss_p[-1], loss_a[-1]], color=["#d62728", "#1f77b4"])
ax2.set_ylabel("总能量损耗 (kWh)")
ax2.set_title(f"能量损耗对比（被动/主动 ≈ {loss_p[-1]/max(loss_a[-1],1e-12):.0f}×）")
for i, v in enumerate([loss_p[-1], loss_a[-1]]):
    ax2.text(i, v, f"{v:.4f}", ha="center", va="bottom", fontsize=9)
save(fig, "balancing_convergence.png")
# @AI_GENERATED: end
