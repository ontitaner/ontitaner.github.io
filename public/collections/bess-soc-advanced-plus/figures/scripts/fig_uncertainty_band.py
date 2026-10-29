# @AI_GENERATED
"""第14章 协方差传播 + 在线诊断证据图 img/uncertainty_band.png。
"诊断序列"用图内可读的状态时间线呈现：标 z 值、阈值线、连续计数与状态颜色，
所有用到的示例数据直接标注在图上。"""
import math

from _figstyle import plt, save, C_CHG, C_OK, C_ACC, C_LIMIT, C_GRID
import ch06_uncertainty_diagnostics as chapter

sigmas = chapter.uncertainty_trace()
steps = list(range(len(sigmas)))
energy = [chapter.energy_band(0.30, s)[0] for s in sigmas]
spread = [chapter.energy_band(0.30, s)[1] for s in sigmas]
results = chapter.run()                      # 5 个诊断样本
THRESH = 3.0
STATE_COLOR = {"normal": C_OK, "degraded": C_ACC, "invalid": C_LIMIT}

fig, (ax1, ax2, ax3) = plt.subplots(
    3, 1, figsize=(9, 9), gridspec_kw={"height_ratios": [2.0, 2.0, 1.5]})

# ── 上栏：σ_SOC 收敛 ──────────────────────────────────────────────
ax1.plot(steps, sigmas, color=C_CHG, lw=2.0, label="SOC 标准差 σ_SOC")
ax1.axvline(600, color=C_GRID, lw=1.0, ls="--")
ax1.annotate(f"起点 σ={sigmas[0]:.3f}", (steps[0], sigmas[0]), (40, sigmas[0] - 0.013),
             fontsize=9, arrowprops=dict(arrowstyle="->", color=C_GRID))
ax1.annotate(f"末点 σ≈{sigmas[-1]:.3f}", (steps[-1], sigmas[-1]),
             (len(steps) - 360, sigmas[-1] + 0.018), fontsize=9,
             arrowprops=dict(arrowstyle="->", color=C_GRID))
ax1.text(300, 0.070, "激励段：σ 快速收窄", ha="center", fontsize=9, color=C_CHG)
ax1.text(830, 0.045, "平台静置：收窄变慢", ha="center", fontsize=9, color=C_ACC)
ax1.set_ylabel("σ_SOC (-)")
ax1.set_title("协方差收敛：激励段快、平台静置段慢")
ax1.legend(loc="upper right")

# ── 中栏：交流侧 SOE 点值与 ±1.96σ 能量带 ─────────────────────────
lower = [e - 1.96 * s for e, s in zip(energy, spread)]
upper = [e + 1.96 * s for e, s in zip(energy, spread)]
ax2.plot(steps, energy, color=C_CHG, lw=2.0, label="SOE 点值")
ax2.fill_between(steps, lower, upper, color=C_CHG, alpha=.16, label="±1.96σ_E 能量带")
ax2.annotate(f"点值 {energy[0]:.0f} kWh，带宽 ±{1.96*spread[0]:.0f} kWh",
             (steps[0], energy[0]), (120, energy[0] + 60), fontsize=9,
             arrowprops=dict(arrowstyle="->", color=C_GRID))
ax2.annotate(f"末端带宽收窄到 ±{1.96*spread[-1]:.0f} kWh",
             (steps[-1], upper[-1]), (len(steps) - 520, upper[-1] + 45), fontsize=9,
             arrowprops=dict(arrowstyle="->", color=C_GRID))
ax2.set_ylabel("交流侧可用能量 (kWh)")
ax2.set_title("σ 经 C_eff·η 传播为 ±1.96σ 能量带")
ax2.legend(loc="lower right")

# ── 下栏：诊断时间线 ──────────────────────────────────────────────
xs = list(range(len(results)))
zvals = [r.standardized_residual if math.isfinite(r.standardized_residual) else 0.0
         for r in results]
ax3.axhline(THRESH, color=C_LIMIT, lw=1.1, ls="--")
ax3.text(0.02, THRESH + 0.4, "阈值 |z|=3", ha="left", color=C_LIMIT, fontsize=8.5)
for x, r in zip(xs, results):
    c = STATE_COLOR[r.state.value]
    y = r.standardized_residual if math.isfinite(r.standardized_residual) else 0.0
    ax3.scatter([x], [y], s=130, color=c, zorder=3, edgecolor="white", linewidth=1.3)
    ztxt = f"z={r.standardized_residual:.2f}" if math.isfinite(r.standardized_residual) else "z=—"
    ax3.annotate(f"{ztxt} · {r.state.value}\n连续 {r.continuous_bad}",
                 (x, y), (x, y - 2.8), ha="center", fontsize=8.2, color=c, fontweight="bold")
ax3.plot(xs, zvals, color=C_GRID, lw=1.0, ls=":", zorder=1)
ax3.annotate("首次越限→仅记录", (1, zvals[1]), (1.0, 9.4), fontsize=8.2, ha="center",
             color=C_ACC, arrowprops=dict(arrowstyle="->", color=C_ACC))
ax3.annotate("连续第 2 次→降级", (2, zvals[2]), (2.1, 7.4), fontsize=8.2, ha="center",
             color=C_ACC, arrowprops=dict(arrowstyle="->", color=C_ACC))
ax3.annotate("数据 suspect→降级", (3, zvals[3]), (3.0, 5.0), fontsize=8.2, ha="center",
             color=C_ACC, arrowprops=dict(arrowstyle="->", color=C_ACC))
ax3.annotate("无效输入→拒绝更新", (4, 0.3), (4.0, 7.6), fontsize=8.2, ha="center",
             color=C_LIMIT, arrowprops=dict(arrowstyle="->", color=C_LIMIT))
ax3.set_xticks(xs)
ax3.set_xticklabels([f"样本{i}" for i in xs])
ax3.set_ylim(-4.0, 12.5)
ax3.set_xlim(-0.5, 4.5)
ax3.set_ylabel("标准化残差 z")
ax3.set_title("在线诊断时间线（绿=normal 橙=degraded 红=invalid）：连续 2 次越限进入 degraded")

save(fig, "uncertainty_band",
     title="协方差收敛 → 能量区间 → 在线诊断：σ、z 与状态全部标在图内")
# @AI_GENERATED: end