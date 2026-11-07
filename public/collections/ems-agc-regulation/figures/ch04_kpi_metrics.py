# @AI_GENERATED
"""第 04 章配图：K1/K2/K3 三项核心指标可视化。

所有参数均为 [教学示例]，不可直接用于现场整定。
"""
from __future__ import annotations

import numpy as np

from _style import (C_K1, C_K2, C_K3, C_GRID, C_LIMIT, C_OK, C_ACC, C_PURPLE, C_DIS, C_CHG,
                    IMG_DIR, manifest, save, plt)


def fig_k1_ramp_rate():
    """K1 调节速率：阶跃指令 + 快慢两档 ramp rate 对比 + 偏差面积 + K1 公式框"""
    pn = 100.0
    t = np.linspace(0, 28, 1401)
    dt = t[1] - t[0]

    p_cmd = np.where(t < 2, 50.0, 80.0)
    t_cmd_recv = 2.5

    def simulate_ramp(rate):
        p_act = np.full_like(t, 50.0)
        for i in range(1, len(t)):
            if t[i] >= t_cmd_recv:
                step = np.clip(80.0 - p_act[i-1], -rate * dt, rate * dt)
                p_act[i] = p_act[i-1] + step
            else:
                p_act[i] = 50.0
        return p_act

    p_fast = simulate_ramp(1.8)
    p_slow = simulate_ramp(0.7)
    p_mid = simulate_ramp(1.2)

    t_end_fast = t[np.argmax(p_fast >= 79.0)] if np.any(p_fast >= 79.0) else t[-1]
    t_end_slow = t[np.argmax(p_slow >= 79.0)] if np.any(p_slow >= 79.0) else t[-1]
    t_end_mid = t[np.argmax(p_mid >= 79.0)] if np.any(p_mid >= 79.0) else t[-1]

    k1_fast = 29.0 / (t_end_fast - t_cmd_recv)
    k1_slow = 29.0 / (t_end_slow - t_cmd_recv)
    k1_mid = 29.0 / (t_end_mid - t_cmd_recv)

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), width_ratios=[1.4, 1])

    # 左图：三档 ramp rate 对比
    ax = axes[0]
    ax.step(t, p_cmd, where="post", color=C_GRID, lw=2.2, ls="--", label="调度指令 P_target")
    ax.plot(t, p_fast, color=C_OK, lw=2.2, label=f"ramp=1.8 MW/s  K1={k1_fast:.2f}")
    ax.plot(t, p_mid, color=C_ACC, lw=2.2, label=f"ramp=1.2 MW/s  K1={k1_mid:.2f}")
    ax.plot(t, p_slow, color=C_LIMIT, lw=2.2, ls="-.", label=f"ramp=0.7 MW/s  K1={k1_slow:.2f}")

    # 填充指令与实际偏差（取最慢的）
    ax.fill_between(t, p_cmd, p_slow, alpha=0.08, color=C_LIMIT)
    ax.fill_between(t, p_cmd, p_fast, alpha=0.05, color=C_OK)

    # K1 计算区间（快速）
    ax.axvline(t_cmd_recv, color=C_K1, ls=":", lw=1.2, alpha=0.6)
    ax.axvspan(t_cmd_recv, t_end_mid, color=C_K1, alpha=0.06)

    # 标注
    ax.annotate(f"K1=1.8 达标 K1≥1.0",
                xy=(t_end_fast, 79), xytext=(18, 58),
                arrowprops=dict(arrowstyle="->", color=C_OK),
                fontsize=8.5, color=C_OK,
                bbox=dict(fc="white", ec=C_OK, alpha=0.9))
    ax.annotate(f"K1=0.7 不达标",
                xy=(t_end_slow, 79), xytext=(20, 66),
                arrowprops=dict(arrowstyle="->", color=C_LIMIT),
                fontsize=8.5, color=C_LIMIT,
                bbox=dict(fc="white", ec=C_LIMIT, alpha=0.9))

    # 多级限速关键提醒
    ax.text(0.52, 0.22, "EMS安全限速 ≥1.5\n分配限速 ≥1.5\nPCS ramp ≥1.5\n实际 K1 = min(以上)",
            transform=ax.transAxes, fontsize=8, color=C_K1,
            bbox=dict(fc="white", ec=C_K1, alpha=0.9, boxstyle="round"))

    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("有功出力 (MW)")
    ax.set_title("K1 调节速率：三档 ramp rate 的 K1 差异  [Pn=100 MW]", fontsize=11)
    ax.set_xlim(0, 26)
    ax.set_ylim(45, 88)
    ax.legend(loc="lower right", fontsize=8)
    ax.axhline(50, color="k", lw=0.5, alpha=0.3)

    # 右图：K1 得分 vs ramp rate 函数
    ax2 = axes[1]
    ramp_vals = np.linspace(0.3, 2.5, 201)
    k1_scores = np.clip(100 * ramp_vals / 1.0, 0, 100)  # K1_req = 1.0 MW/s

    ax2.plot(ramp_vals, k1_scores, color=C_K1, lw=2.8)
    ax2.fill_between(ramp_vals, 0, k1_scores, alpha=0.1, color=C_K1)
    ax2.axvline(1.0, color=C_LIMIT, ls="--", lw=1.5, label="要求 K1 ≥ 1.0 MW/s")
    ax2.axhline(100, color=C_GRID, ls=":", lw=1)
    ax2.axhspan(-5, 0, color=C_LIMIT, alpha=0.06)

    for r, lbl, c in [(0.7, "0.7 MW/s\n= 70 分", C_LIMIT),
                       (1.0, "1.0 MW/s\n= 100 分", C_OK),
                       (1.2, "1.2 MW/s\n= 100 分", C_ACC),
                       (1.8, "1.8 MW/s\n= 100 分", C_OK)]:
        sc = min(100, 100 * r / 1.0)
        ax2.plot(r, sc, "o", color=c, ms=9, zorder=5)
        ax2.annotate(lbl, xy=(r, sc), xytext=(r + 0.15, sc - 20 if r < 1 else sc + 10),
                    arrowprops=dict(arrowstyle="->", color=c), fontsize=8, color=c)

    ax2.set_xlabel("实际 ramp rate (MW/s)")
    ax2.set_ylabel("K1 得分")
    ax2.set_title("K1 得分函数（K1_req = 1.0 MW/s）", fontsize=11)
    ax2.legend(fontsize=8, loc="lower right")
    ax2.set_xlim(0.2, 2.6)
    ax2.set_ylim(-5, 115)

    fig.suptitle(f"K1 调节速率：响应曲线 + 得分函数  [Pn={pn:.0f} MW, K1_req=1.0 MW/s, 教学示例]",
                 fontsize=12, y=1.02)
    fig.text(0.5, -0.02,
             "阴影区 = 指令与实际偏差  |  公式：K1 = ΔP / ΔT = (P_end − P_start) / (T_end − T_start)",
             ha="center", fontsize=9, color=C_GRID)

    manifest("ch04_k1_ramp",
             [pn, 1.8, 1.2, 0.7, 1.0, k1_fast, k1_mid, k1_slow, 30, 50, 80, 79])
    save(fig, "ch04_k1_ramp")


def fig_k2_response_time():
    """K2 响应时间：多资源类型延迟对比 + 链路瓶颈热力图"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), width_ratios=[1.2, 1])

    # 左图：各资源 K2 链路对比
    stages = ["调度下发", "104 传输", "EMS 处理", "死区/分配", "PCS 启机", "出力启动"]
    delays_storage = [0, 0.20, 0.15, 0.20, 0.30, 0.15]
    delays_pv = [0, 0.20, 0.15, 0.20, 0.80, 0.65]
    delays_wind = [0, 0.20, 0.15, 0.20, 1.50, 0.95]
    delays_hydro = [0, 0.20, 0.15, 0.20, 0.50, 0.45]

    cum_storage = np.cumsum([0] + delays_storage)
    cum_pv = np.cumsum([0] + delays_pv)
    cum_wind = np.cumsum([0] + delays_wind)
    cum_hydro = np.cumsum([0] + delays_hydro)

    y = np.arange(len(stages))
    ax = axes[0]
    height = 0.18

    for i, (cum, color, label, limit) in enumerate([
        (cum_storage, C_OK, f"储能 K2={cum_storage[-1]:.1f}s（限3s）", 3.0),
        (cum_pv, C_ACC, f"光伏 K2={cum_pv[-1]:.1f}s（限5s）", 5.0),
        (cum_wind, C_K1, f"风电 K2={cum_wind[-1]:.1f}s（限5s）", 5.0),
        (cum_hydro, C_CHG, f"水电 K2={cum_hydro[-1]:.1f}s（限5s）", 5.0),
    ]):
        delays = [delays_storage, delays_pv, delays_wind, delays_hydro][i]
        ax.barh(y[1:] + (i - 1.5) * height, delays[1:], left=cum[1:-1], height=height,
                color=color, alpha=0.85, label=label)

    for cum, limit, color in [(cum_storage, 3.0, C_OK), (cum_pv, 5.0, C_ACC),
                               (cum_wind, 5.0, C_K1), (cum_hydro, 5.0, C_CHG)]:
        ax.axvline(cum[-1], color=color, ls="--", lw=1.2, alpha=0.7)

    ax.axvline(3.0, color=C_LIMIT, ls="-", lw=2)
    ax.text(3.05, len(stages) - 0.2, "储能限 3 s", fontsize=8.5, color=C_LIMIT)
    ax.axvline(5.0, color=C_GRID, ls=":", lw=1.5)
    ax.text(5.05, len(stages) - 1.2, "其它限 5 s", fontsize=8, color=C_GRID)

    ax.set_yticks(y)
    ax.set_yticklabels(stages, fontsize=8.5)
    ax.set_xlabel("累计时间 (s)")
    ax.set_title("四种资源 K2 链路延迟预算对比", fontsize=11)
    ax.legend(fontsize=7, loc="lower right", ncol=2)
    ax.set_xlim(0, 7.5)
    ax.invert_yaxis()

    # 右图：K2 得分函数（30 s 限值 + 各资源标注 + 实际分布）
    ax2 = axes[1]
    k2_vals = np.linspace(0, 45, 451)
    k2_scores = np.clip(100 * (1 - k2_vals / 30.0), 0, 100)
    ax2.plot(k2_vals, k2_scores, color=C_K2, lw=2.8)
    ax2.fill_between(k2_vals, 0, k2_scores, alpha=0.1, color=C_K2)
    ax2.axvline(30, color=C_LIMIT, ls="--", lw=1.5)

    # 工作点标注
    points = [
        (1.0, "储能\n1 s ≈ 97 分", C_OK),
        (2.0, "光伏\n2 s ≈ 93 分", C_ACC),
        (3.0, "水电\n3 s ≈ 90 分", C_CHG),
        (4.0, "风电\n4 s ≈ 87 分", C_K1),
        (31.0, "超限\n31 s = 0 分", C_LIMIT),
        (5.0, "5 s = 83.3 分\n(章节示例)", C_PURPLE),
    ]
    for k2v, lbl, c in points:
        sc = max(0, 100 * (1 - k2v / 30.0))
        ax2.plot(k2v, sc, "o", color=c, ms=8, zorder=5)
        ax2.annotate(lbl, xy=(k2v, sc),
                     xytext=(k2v + 3 if k2v < 20 else k2v - 8, sc + 8 if k2v < 20 else sc - 12),
                     arrowprops=dict(arrowstyle="->", color=c), fontsize=7.5, color=c)

    ax2.set_xlabel("实际 K2 响应时间 (s)")
    ax2.set_ylabel("K2 得分")
    ax2.set_title("K2 得分函数（限值 30 s，储能限 3 s）", fontsize=11)
    ax2.set_xlim(0, 45)
    ax2.set_ylim(-5, 110)

    fig.suptitle("K2 响应时间：链路预算 + 得分函数  [教学示例]", fontsize=12, y=1.02)
    fig.text(0.5, -0.02,
             "公式：K2_score = max(0, 100×(1 − K2_actual / 30))  |  K2 = T_start − T_cmd",
             ha="center", fontsize=8.5, color=C_GRID)

    manifest("ch04_k2_response",
             cum_storage.tolist() + cum_pv.tolist() + cum_wind.tolist() + cum_hydro.tolist() + [3, 5, 30, 1, 2, 3, 4, 31])
    save(fig, "ch04_k2_response")


def fig_k3_precision():
    """K3 调节精度：三子图——偏差分布 + 得分函数 + 口径差异"""
    pn = 100.0
    target = 70.0
    k3_limit_pct = 3.0
    k3_limit = pn * k3_limit_pct / 100

    rng = np.random.default_rng(42)
    n = 30
    # 系统性偏差：均值为 0.8 MW（模拟 PCS 固定偏置）
    errors_sys_bias = rng.normal(0.8, 0.5, n)
    errors_normal = rng.normal(0.2, 0.5, n)
    # 调度口径瞬时值（末段抖动大）
    errors_dispatch = rng.normal(0.3, 1.0, n)

    sys_k3 = np.mean(np.abs(errors_sys_bias)) / pn * 100
    nor_k3 = np.mean(np.abs(errors_normal)) / pn * 100
    dis_k3 = np.mean(np.abs(errors_dispatch)) / pn * 100

    fig, axes = plt.subplots(2, 2, figsize=(13, 8), gridspec_kw={"height_ratios": [1, 1.1]})

    # 左上：三种场景的偏差分布
    ax = axes[0, 0]
    x = np.arange(1, n + 1)
    ax.bar(x - 0.25, errors_sys_bias, 0.25, color=C_LIMIT, alpha=0.7, label=f"系统性偏差 K3={sys_k3:.1f}%")
    ax.bar(x, errors_normal, 0.25, color=C_OK, alpha=0.7, label=f"正常 K3={nor_k3:.1f}%")
    ax.bar(x + 0.25, errors_dispatch, 0.25, color=C_ACC, alpha=0.7, label=f"调度口径 K3={dis_k3:.1f}%")
    ax.axhline(k3_limit, color=C_LIMIT, ls="--", lw=1.5, label=f"限值 ±{k3_limit_pct:.0f}% Pn = ±{k3_limit:.0f} MW")
    ax.axhline(-k3_limit, color=C_LIMIT, ls="--", lw=1.5)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("控制周期")
    ax.set_ylabel("稳态偏差 (MW)")
    ax.set_title(f"三种统计口径的 K3 差异  [Pn={pn:.0f} MW]", fontsize=10)
    ax.legend(fontsize=7, loc="upper right")
    ax.set_xlim(0, n + 1)

    # 右上：K3 得分函数（多限值对比）
    ax2 = axes[0, 1]
    k3_range = np.linspace(0, 6, 301)
    for limit_pct, color, label in [(2.0, C_PURPLE, "限 2%（山西）"), (3.0, C_K3, "限 3%（华东）")]:
        scores = np.clip(100 * (1 - k3_range / limit_pct), 0, 100)
        ax2.plot(k3_range, scores, color=color, lw=2.5, label=label)
        ax2.axvline(limit_pct, color=color, ls="--", lw=1, alpha=0.5)

    # 工作点
    for k3v, lbl, c in [(2.0, "K3=2%→33分\n(华东)", C_PURPLE),
                         (1.0, "K3=1%→67分\n(华东)", C_OK),
                         (0.5, "K3=0.5%→83分\n(华东)", C_OK)]:
        sc = max(0, 100 * (1 - k3v / 3.0))
        ax2.plot(k3v, sc, "o", color=c, ms=9, zorder=5)
        ax2.annotate(lbl, xy=(k3v, sc),
                     xytext=(k3v + 0.8, sc - 10 if k3v > 1 else sc + 8),
                     arrowprops=dict(arrowstyle="->", color=c), fontsize=8, color=c)

    ax2.set_xlabel("K3 调节精度 (%)")
    ax2.set_ylabel("K3 得分")
    ax2.set_title("K3 得分函数（限值 2% / 3% 对比）", fontsize=10)
    ax2.legend(fontsize=8)
    ax2.set_xlim(0, 6)
    ax2.set_ylim(-5, 110)

    # 左下：瞬时值 vs 滚动平均值的时间序列（模拟一次指令后的 60 s）
    t60 = np.linspace(0, 60, 301)
    n60 = len(t60)
    # 出力曲线：前段爬坡，后段稳态有小抖动
    ramp_phase = 50 + (target - 50) * (1 - np.exp(-(t60 - 2) / 3))
    steady_noise = target + rng.normal(0, 0.6, n60) * np.clip((t60 - 10) / 5, 0.2, 1)
    p_60s = np.where(t60 < 10, ramp_phase, steady_noise)
    p_60s = np.clip(p_60s, 49, 72)
    # 滚动平均（5 s 窗口）
    window = 25
    p_rolling = np.array([np.mean(p_60s[max(0, i - window):i + window]) for i in range(len(p_60s))])

    ax3 = axes[1, 0]
    ax3.plot(t60, p_60s, color=C_ACC, lw=1.5, alpha=0.7, label="瞬时出力值")
    ax3.plot(t60, p_rolling, color=C_K3, lw=2.5, label="5s 滚动平均值")
    ax3.axhline(target, color=C_OK, ls="--", lw=1.2, label=f"目标 {target:.0f} MW")
    ax3.axhspan(target - k3_limit, target + k3_limit, color=C_OK, alpha=0.06)
    ax3.axhline(target + k3_limit, color=C_LIMIT, ls=":", lw=1)
    ax3.axhline(target - k3_limit, color=C_LIMIT, ls=":", lw=1)

    # 标注瞬时值 vs 滚动平均的差异
    idx_40s = np.argmin(np.abs(t60 - 40))
    ax3.annotate(f"t=40 s\n瞬时={p_60s[idx_40s]:.1f} MW\n滚动={p_rolling[idx_40s]:.1f} MW\n差={abs(p_60s[idx_40s]-p_rolling[idx_40s]):.1f} MW",
                 xy=(40, p_60s[idx_40s]),
                 xytext=(20, 65),
                 arrowprops=dict(arrowstyle="->", color=C_PURPLE),
                 fontsize=8, color=C_PURPLE,
                 bbox=dict(fc="white", ec=C_PURPLE, alpha=0.9))

    # 调度采样时刻标记
    ax3.axvline(60, color=C_LIMIT, ls="--", lw=1.5)
    ax3.text(60.5, 53, "调度采样 t=60s\n取瞬时值", fontsize=7.5, color=C_LIMIT)

    ax3.set_xlabel("时间 (s)")
    ax3.set_ylabel("出力 (MW)")
    ax3.set_title("K3 口径差异：瞬时值 vs 滚动平均值", fontsize=10)
    ax3.legend(fontsize=7.5, loc="upper left")
    ax3.set_xlim(0, 60)
    ax3.set_ylim(49, 73)

    # 右下：达标率累积对比
    ax4 = axes[1, 1]
    n_total = 60
    rng2 = np.random.default_rng(99)
    # 系统偏差场景
    err_bias = rng2.normal(0.8, 0.6, n_total)
    # 正常场景
    err_ok = rng2.normal(0.1, 0.4, n_total)

    cum_pass_bias = np.cumsum(np.abs(err_bias) <= k3_limit) / np.arange(1, n_total + 1) * 100
    cum_pass_ok = np.cumsum(np.abs(err_ok) <= k3_limit) / np.arange(1, n_total + 1) * 100

    ax4.plot(range(1, n_total + 1), cum_pass_ok, color=C_OK, lw=2.5, label=f"正常 达标率={cum_pass_ok[-1]:.0f}%")
    ax4.plot(range(1, n_total + 1), cum_pass_bias, color=C_LIMIT, lw=2.5, label=f"系统偏差 达标率={cum_pass_bias[-1]:.0f}%")
    ax4.axhline(85, color=C_ACC, ls="--", lw=1.2, alpha=0.7)
    ax4.text(30, 86, "85% 及格参考", fontsize=7.5, color=C_ACC)

    ax4.set_xlabel("控制周期数")
    ax4.set_ylabel("累积达标率 (%)")
    ax4.set_title("K3 月度累积达标率收敛曲线", fontsize=10)
    ax4.legend(fontsize=8)
    ax4.set_xlim(0, n_total)
    ax4.set_ylim(40, 105)

    fig.suptitle(f"K3 调节精度：偏差 + 得分 + 口径 + 达标率  [Pn={pn:.0f} MW, K3_limit={k3_limit_pct:.0f}% Pn, 教学示例]",
                 fontsize=12, y=1.01)
    fig.text(0.5, 0.01,
             "K3 = |P_actual − P_target| / Pn × 100%  |  K3_score = 100 × (1 − K3_actual / K3_limit)",
             ha="center", fontsize=9, color=C_GRID)

    manifest("ch04_k3_precision",
             [pn, k3_limit_pct, k3_limit, sys_k3, nor_k3, dis_k3, 2.0, 1.0, 0.5, 60, 70, 30] +
             list(errors_sys_bias) + list(errors_normal) + list(errors_dispatch))
    save(fig, "ch04_k3_precision")


def main():
    fig_k1_ramp_rate()
    fig_k2_response_time()
    fig_k3_precision()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end