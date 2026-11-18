# @AI_GENERATED
"""第07章 ECM 脉冲响应图：img/ecm_pulse.png——三层分解展示瞬时/动态/状态演化。"""
from _figstyle import plt, C_CHG, C_DIS, C_OK, C_GRID, C_LIMIT
from pathlib import Path
from soc_core import DEFAULT_MODEL_PARAMS, ModelState, advance_model

profile = [0.0] * 5 + [50.0] * 20 + [0.0] * 25
state = ModelState(0.50)
steps = []

for current_a in profile:
    step = advance_model(state, current_a, 1.0, params=DEFAULT_MODEL_PARAMS)
    steps.append(step)
    state = step.state_after

seconds = list(range(len(profile)))
terminal = [s.terminal_voltage_v for s in steps]
dynamic_v = [s.state_before.dynamic_v for s in steps]
soc_vals = [s.state_before.soc for s in steps]
params = DEFAULT_MODEL_PARAMS

ocv_alone = [3.30] * len(seconds)
ocv_r0 = [ocv_alone[i] - p * params.r0_ohm for i, p in enumerate(profile)]

fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 12))

# ── 上栏：电流激励 ──────────────────────────────────────────────
ax1.fill_between(seconds, 0, profile, color=C_CHG, alpha=0.30)
ax1.step(seconds, profile, where="mid", color=C_CHG, lw=1.8)
ax1.axhline(0, color=C_GRID, lw=0.8)
ax1.set_ylabel("电流 (A)")
ax1.set_title("电流：50 A 放电脉冲（静置 → 放电 → 恢复）")
ax1.set_ylim(-8, 62)
ax1.annotate("0 A 静置", (1.5, 4), (8, 14), fontsize=8.5, color=C_GRID,
             arrowprops=dict(arrowstyle="->", color=C_GRID))
ax1.annotate("50 A 放电", (15, 50), (18, 42), fontsize=8.5, color=C_CHG,
             arrowprops=dict(arrowstyle="->", color=C_CHG))
ax1.annotate("0 A 恢复", (36, 4), (38, 14), fontsize=8.5, color=C_GRID,
             arrowprops=dict(arrowstyle="->", color=C_GRID))

# ── 中栏：电压分解 ──────────────────────────────────────────────
ax2.plot(seconds, terminal, color=C_CHG, lw=2.0, label="端电压 $V_t$ (量测)")
ax2.plot(seconds, ocv_alone, color=C_GRID, lw=1.3, ls="--", label="OCV 参考 (固定 3.30 V)")
ax2.plot(seconds, ocv_r0, color=C_OK, lw=1.3, ls="-.", label="OCV − R0 压降")
ax2.fill_between(seconds, ocv_alone, ocv_r0, color=C_DIS, alpha=0.16)
ax2.fill_between(seconds, ocv_r0, terminal, color=C_OK, alpha=0.14)
ax2.annotate("$I \\times R_0$", (12, 3.287), (13.5, 3.291), fontsize=9,
             color=C_DIS, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=C_DIS))
ax2.annotate("动态支路 $p[k]$\n(极化建立)", (18, 3.268), (19, 3.235),
             fontsize=9, color=C_OK, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=C_OK))
ax2.annotate("① 瞬时 R0 压降\n$\\Delta V = I \\cdot R_0$\n≈ 50×0.00032 = 16 mV",
             (5.3, terminal[5]), (7, terminal[5] - 0.045),
             fontsize=8.5, color=C_DIS,
             arrowprops=dict(arrowstyle="->", color=C_DIS))
ax2.annotate("② 动态支路继续响应\n$\\tau=20$ s 指数衰减",
             (15, terminal[15]), (16, terminal[15] - 0.015),
             fontsize=8.5, color=C_OK,
             arrowprops=dict(arrowstyle="->", color=C_OK))
ax2.annotate("③ 静置恢复\n$V_t$ 回升趋近 OCV",
             (32, terminal[32]), (34, terminal[32] + 0.015),
             fontsize=8.5, color=C_GRID,
             arrowprops=dict(arrowstyle="->", color=C_GRID))
ax2.set_ylabel("电压 (V)")
ax2.set_title("电压分解：$V_t$ = OCV − $I \\cdot R_0$ − $p[k]$")
ax2.legend(loc="lower right", fontsize=8, ncol=3)

# ── 下栏：状态演化 ──────────────────────────────────────────────
ax3_l = ax3
ax3_r = ax3.twinx()
soc_pct = [s * 100 for s in soc_vals]
line_soc = ax3_l.plot(seconds, soc_pct, color=C_CHG, lw=2.0, label="SOC (%)")
line_dyn = ax3_r.plot(seconds, dynamic_v, color=C_DIS, lw=2.0, ls="--",
                      label="动态压降 $p[k]$ (V)")
ax3_l.set_ylabel("SOC (%)", color=C_CHG)
ax3_r.set_ylabel("动态压降 $p[k]$ (V)", color=C_DIS)
ax3_l.tick_params(axis="y", colors=C_CHG)
ax3_r.tick_params(axis="y", colors=C_DIS)
ax3_l.axhline(50, color=C_GRID, lw=0.8, ls=":")
ax3_r.axhline(0, color=C_GRID, lw=0.8, ls=":")

ax3_l.annotate(f"SOC 起点 50.00%",
               (seconds[0], soc_pct[0]), (3, soc_pct[0] + 0.08),
               fontsize=8.5, color=C_CHG,
               arrowprops=dict(arrowstyle="->", color=C_CHG))
ax3_l.annotate(f"SOC 终点 {soc_vals[-1]:.4f} ≈ {soc_pct[-1]:.2f}%\n放电期降 ≈ 0.44%",
               (seconds[-1], soc_pct[-1]), (30, soc_pct[-1] + 0.15),
               fontsize=8.5, color=C_CHG,
               arrowprops=dict(arrowstyle="->", color=C_CHG))
ax3_r.annotate("放电中 $p[k]$ 指数上升\n趋近 $I \\cdot r_d = 10$ mV",
               (15, dynamic_v[15]), (18.5, dynamic_v[15] - 0.004),
               fontsize=8.5, color=C_DIS,
               arrowprops=dict(arrowstyle="->", color=C_DIS))
ax3_r.annotate("静置后 $p[k]$ 指数衰减\n$\\tau=20$ s → 0",
               (32, dynamic_v[32]), (35, dynamic_v[32] - 0.0025),
               fontsize=8.5, color=C_DIS,
               arrowprops=dict(arrowstyle="->", color=C_DIS))
ax3_l.set_xlabel("时间 (s)")
ax3_l.set_title("状态演化：SOC 线性下降 + 动态压降指数响应")
lines = line_soc + line_dyn
labels = [l.get_label() for l in lines]
ax3_l.legend(lines, labels, loc="center right", fontsize=8.5)

fig.suptitle("一阶 RC ECM 脉冲响应：电流激励 → 电压分解 → 状态演化", fontsize=12)
ROOT = Path(__file__).resolve().parent.parent.parent
IMG_DIR = ROOT / "img"
fig.savefig(IMG_DIR / "ecm_pulse.png", bbox_inches="tight")
plt.close(fig)
print("saved img/ecm_pulse.png")