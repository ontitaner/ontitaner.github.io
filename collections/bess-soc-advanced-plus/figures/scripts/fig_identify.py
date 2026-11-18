# @AI_GENERATED
"""第08章 动态参数辨识图：img/identify_pulse.png。三栏分解展示激励→分解→选参全过程。"""
import math

from _figstyle import plt, C_CHG, C_DIS, C_GRID, C_OK, C_LIMIT
from soc_core import (
    _dynamic_feature,
    ResidualMetrics,
    residual_metrics,
    least_squares,
)
import ch04_identification as m

times_s, currents_a, voltage_drop_v = m.generate_noisy_dynamic_data(seed=41)
result = m.run_dynamic_identification()

n = len(times_s)
split = int(n * 0.67)

best_r0, best_rd, best_tau = result.r0_ohm, result.r_dynamic_ohm, result.tau_s
best_offset = result.offset_v

dynamic_best = _dynamic_feature(times_s, currents_a, best_tau)
fit_total = []
comp_r0 = []
comp_rd = []
comp_bv = []
for k, current_a in enumerate(currents_a):
    r0_part = best_r0 * current_a
    rd_part = best_rd * dynamic_best[k]
    bv_part = best_offset
    comp_r0.append(r0_part)
    comp_rd.append(rd_part)
    comp_bv.append(bv_part)
    fit_total.append(r0_part + rd_part + bv_part)

grid = []
for t in (5.0 + 0.5 * idx for idx in range(111)):
    dyn = _dynamic_feature(times_s, currents_a, t)
    val_x = [[currents_a[k], dyn[k], 1.0] for k in range(split, n)]
    try:
        r0, r1, bo = least_squares(
            [[currents_a[k], dyn[k], 1.0] for k in range(split)],
            voltage_drop_v[:split])
    except ValueError:
        continue
    if not (1e-4 <= r0 <= 8e-4):
        continue
    if not (5e-5 <= r1 <= 6e-4):
        continue
    val_res = [voltage_drop_v[k] - (r0 * currents_a[k] + r1 * dyn[k] + bo)
               for k in range(split, n)]
    grid.append((t, residual_metrics(val_res).rmse))

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 12))

# ── 上栏：脉冲电流激励 ────────────────────────────────────────
ax1.fill_between(times_s, 0, currents_a, color=C_CHG, alpha=0.20)
ax1.step(times_s, currents_a, where="post", color=C_CHG, lw=1.6)
ax1.axhline(0, color=C_GRID, lw=0.8)
ax1.set_ylabel("电流 $I[k]$ (A)")
ax1.set_title("输入：不规则采样脉冲电流（120 A 放电 / −80 A 充电）")
ax1.annotate("120 A 放电", (times_s[20], 120), (times_s[25], 105),
             fontsize=8.5, color=C_CHG,
             arrowprops=dict(arrowstyle="->", color=C_CHG))
ax1.annotate("−80 A 充电", (times_s[80], -80), (times_s[85], -55),
             fontsize=8.5, color=C_DIS,
             arrowprops=dict(arrowstyle="->", color=C_DIS))
ax1.annotate(f"总样本 {n} 点，训练 {split} 点，验证 {n - split} 点",
             (times_s[-1] * 0.05, max(currents_a) * 0.85), fontsize=8.8,
             color=C_GRID)

# ── 中栏：过电压分量分解 ──────────────────────────────────────
ax2.scatter(times_s, voltage_drop_v, s=10, color=C_GRID, alpha=0.55,
            label="合成过电压 $d[k]$（含噪声）")
ax2.plot(times_s, fit_total, color=C_LIMIT, lw=2.2, label="完整拟合 $r_0 I + r_d q + b_v$")
ax2.plot(times_s, comp_r0, color=C_CHG, lw=1.4, ls="--",
         label=f"解析分量：$r_0 I[k]$ ({best_r0*1e3:.3f} mΩ)")
ax2.plot(times_s, comp_rd, color=C_DIS, lw=1.4, ls="-.",
         label=f"解析分量：$r_d q[k]$ ({best_rd*1e3:.3f} mΩ)")
ax2.plot(times_s, comp_bv, color=C_OK, lw=1.4, ls=":",
         label=f"解析分量：截距 {best_offset*1e3:.3f} mV")
ax2.fill_between(times_s, 0, comp_r0, color=C_CHG, alpha=0.08)
ax2.fill_between(times_s, [comp_r0[i] + comp_bv[i] for i in range(n)],
                 [comp_r0[i] + comp_bv[i] + comp_rd[i] for i in range(n)],
                 color=C_DIS, alpha=0.08)

res_train = [voltage_drop_v[k] - fit_total[k] for k in range(split)]
res_val = [voltage_drop_v[k] - fit_total[k] for k in range(split, n)]
rmse_train = math.sqrt(sum(r*r for r in res_train) / len(res_train))
rmse_val = math.sqrt(sum(r*r for r in res_val) / len(res_val))
mid_t = times_s[len(times_s) // 2]
ax2.annotate(f"训练 RMSE={rmse_train*1e3:.2f} mV\n验证 RMSE={rmse_val*1e3:.2f} mV",
             (mid_t, max(voltage_drop_v) * 0.82),
             (mid_t * 0.5, max(voltage_drop_v) * 0.92),
             fontsize=8.5, color=C_LIMIT,
             arrowprops=dict(arrowstyle="->", color=C_LIMIT))
ax2.annotate(r"$d[k] = r_0 I[k] + r_d q[k] + b_v + \varepsilon[k]$",
             (times_s[-1] * 0.05, min(voltage_drop_v) * 1.15), fontsize=9.5,
             color=C_GRID)
ax2.set_ylabel("过电压 $d[k]$ (V)")
ax2.set_title("过电压分解：最小二乘回归 → 三个解析分量")
ax2.legend(loc="upper right", fontsize=7.2, ncol=2)

# ── 下栏：网格搜索 τ  → 验证 RMSE ────────────────────────────
tau_list = [g[0] for g in grid]
rmse_list = [g[1] * 1000 for g in grid]
best_rmse_val = min(rmse_list)
best_tau_idx = rmse_list.index(best_rmse_val)
best_tau_val = tau_list[best_tau_idx]

ax3.plot(tau_list, rmse_list, color=C_CHG, lw=1.6)
ax3.scatter(tau_list, rmse_list, s=16, color=C_CHG, alpha=0.5, zorder=3)
ax3.axvline(best_tau_val, color=C_LIMIT, lw=1.5, ls="--")
ax3.scatter([best_tau_val], [best_rmse_val], s=80, color=C_LIMIT, zorder=5,
            edgecolors="white", linewidths=1.2)
ax3.annotate(f"最优 $\\tau$={best_tau_val:.1f} s\n验证 RMSE={best_rmse_val:.2f} mV\n"
             f"→ $a=e^{{-dt/\\tau}}=e^{{-1/{best_tau_val:.1f}}}={math.exp(-1/best_tau_val):.4f}$",
             (best_tau_val, best_rmse_val),
             (best_tau_val + 8, best_rmse_val + 0.03),
             fontsize=8.5, color=C_LIMIT, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=C_LIMIT))

rmse_max = max(rmse_list)
rmse_min = min(rmse_list)
ax3.set_ylim(rmse_min - 0.02, rmse_max + 0.04)

ax3.axhline(rmse_val * 1000, color=C_GRID, lw=0.8, ls=":")
ax3.text(tau_list[0] + 2, rmse_val * 1000 + 0.008,
         f"选定 τ 验证 RMSE={rmse_val*1e3:.2f} mV",
         fontsize=8.2, color=C_GRID)

ax3.set_xlabel("候选时间常数 $\\tau$ (s)")
ax3.set_ylabel("验证 RMSE (mV)")
ax3.set_title("网格搜索：候选 τ 的验证 RMSE 曲线 → 选最小者")

fig.suptitle("动态参数辨识：脉冲激励 → 过电压分解 → 网格搜索选 τ", fontsize=12)
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
IMG_DIR = ROOT / "img"
fig.savefig(IMG_DIR / "identify_pulse.png", bbox_inches="tight")
plt.close(fig)
print("saved img/identify_pulse.png")