# @AI_GENERATED
"""生成 ch06 单体发散图 img/cell_divergence.png。复用 lab/ch06 常量与放电逻辑逐步记录。"""
from _figstyle import plt, save
import ch06_inconsistency as m

# 复用 ch06 的放电逻辑，逐步记录各簇 SOC 轨迹
socs = list(m.PACK_SOC0)
traj = [list(socs)]
while min(socs) > m.SOC_MIN + 1e-9:
    socs = [s - m.P_EACH_KW * m.DT_H / m.CAP_KWH_EACH for s in socs]
    traj.append(list(socs))
ks = [i * m.DT_H for i in range(len(traj))]
n = len(m.PACK_SOC0)
series = [[traj[t][c] for t in range(len(traj))] for c in range(n)]

fig, ax = plt.subplots(figsize=(7, 4.2))
colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728"]
for c in range(n):
    ax.plot(ks, series[c], color=colors[c], lw=1.6,
            label=f"簇{c+1} 初始 {m.PACK_SOC0[c]:.0%}")
ax.axhline(m.SOC_MIN, color="gray", lw=1, ls="--")
ax.annotate("最低簇（簇4）先触下限 → 整组停", (ks[-1], m.SOC_MIN),
            (ks[-1] * 0.35, 0.12), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="#d62728"))
ax.annotate("其余三簇仍有余电放不出\n（木桶效应锁住容量）", (ks[-1], series[0][-1]),
            (ks[-1] * 0.3, 0.28), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="#1f77b4"))
ax.set_xlabel("放电时间 (h)")
ax.set_ylabel("各簇 SOC")
ax.set_title("ch06 均分放电下的簇间发散与木桶效应")
ax.legend(loc="upper right", ncol=2, fontsize=8)
save(fig, "cell_divergence.png")
# @AI_GENERATED: end
