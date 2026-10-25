# @AI_GENERATED
"""生成 ch08 验证记分卡 img/validation_scorecard.png。数据取自 lab/ch08。"""
from _figstyle import plt, save
import ch08_validation as m

# 不同工况（随机种子代表不同噪声实现）下 EKF 收敛后 RMSE
labels, rmses = [], []
for seed in range(5):
    errs = m._ekf_errors(seed=seed)
    kc = m.convergence_step(errs)
    labels.append(f"工况{seed+1}")
    rmses.append(m.rmse(errs[kc:]) * 100)   # 以 % 显示

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar(labels, rmses, color="#1f77b4")
ax.axhline(m.ACCURACY_LIMIT * 100, color="#d62728", lw=1.6, ls="--",
           label=f"精度判据（教学口径）{m.ACCURACY_LIMIT:.0%}")
for b, v in zip(bars, rmses):
    ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}%",
            ha="center", va="bottom", fontsize=9)
ax.set_ylabel("收敛后 SOC RMSE (%)")
ax.set_title("ch08 各工况 EKF 收敛后精度 vs 判据红线")
ax.set_ylim(0, m.ACCURACY_LIMIT * 100 * 1.3)
ax.legend(loc="upper right")
save(fig, "validation_scorecard.png")
# @AI_GENERATED: end
