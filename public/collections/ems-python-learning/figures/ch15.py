# @AI_GENERATED
"""第 15 章配图：频率事故曲线、调频分层、下垂特性、RoCoF 估计。

频率曲线由 lab/ems_lab/grid_sim.py 的教学模型算出，参数均为 [教学示例]。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.frequency import PrimaryFrequencyConfig, RocofEstimator, primary_frequency_power
from ems_lab.grid_sim import BessParams, GridParams, simulate_trip

TRIP = 0.04  # 失去 4% 的发电（例：100 GW 系统跳开 4 GW）


def manifest(name: str, numbers: list[float]) -> None:
    payload = {"_comment": "@AI_GENERATED", "figure": f"{name}.png",
               "numbers": sorted(set(float(n) for n in numbers)),
               "_comment_end": "@AI_GENERATED: end"}
    (IMG_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def fig_event():
    g = GridParams()
    cases = [
        ("无储能", BessParams(), C_GRID),
        ("储能调频，但响应慢（τ=5 s）", BessParams(rating_pu=0.03, tau_s=5.0), C_ACC),
        ("储能调频，快速响应（τ=0.2 s）", BessParams(rating_pu=0.03, tau_s=0.2), C_OK),
    ]
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1.6]})
    ax = axes[0]
    for name, b, c in cases:
        r = simulate_trip(TRIP, g, b, t_end_s=40)
        ax.plot(r.t, r.f_hz, color=c, lw=2.2, label=f"{name}：最低 {r.nadir_hz:.2f} Hz")
        axes[1].plot(r.t, r.p_bess * 100, color=c, lw=2)
        if name == "无储能":
            ax.plot(r.nadir_time_s, r.nadir_hz, "v", color=C_LIMIT, ms=9)
            ax.annotate("② 频率最低点（Nadir）\n越低越危险", xy=(r.nadir_time_s, r.nadir_hz),
                        xytext=(12, 49.36), arrowprops=dict(arrowstyle="->"))
            ax.annotate("③ 准稳态：一次调频稳住，\n但回不到 50 Hz", xy=(35, r.f_hz[3500]), xytext=(22, 49.6),
                        arrowprops=dict(arrowstyle="->"))
    # 初始 RoCoF 切线
    rocof0 = 50 * (-TRIP) / (2 * g.h_s)
    tt = np.array([1.0, 2.2])
    ax.plot(tt, 50 + rocof0 * (tt - 1.0), color=C_LIMIT, ls="--", lw=1.5)
    ax.annotate(f"① 初始跌速 RoCoF = {rocof0:.2f} Hz/s\n（此刻只有转子动能在补缺口）", xy=(1.6, 50 + rocof0 * 0.6),
                xytext=(3.5, 49.97), color=C_LIMIT, arrowprops=dict(arrowstyle="->", color=C_LIMIT))
    ax.axhline(50, color="k", lw=0.8)
    ax.axhline(49.0, color=C_LIMIT, ls=":", lw=1)
    ax.text(0.3, 49.03, "低频减载风险线（示意）", color=C_LIMIT, fontsize=9)
    ax.set_ylabel("电网频率 (Hz)")
    ax.set_ylim(48.9, 50.1)
    ax.set_title("t=1 s 一台大机组跳闸（失去 4% 发电）后的频率变化  [教学模型]")
    ax.legend(loc="lower right")
    axes[1].set_ylabel("储能出力\n(% 系统容量)")
    axes[1].set_xlabel("时间 (s)")
    axes[1].set_title("储能出力：快速响应的储能在最低点之前就顶上去了", loc="left", fontsize=10)
    manifest("ch15_frequency_event", [-0.25, 0.2, 1, 4, 5, 49, 49.41, 49.53, 49.68, 50])
    save(fig, "ch15_frequency_event")


def fig_layers():
    g = GridParams(agc_ki=0.2)
    r = simulate_trip(TRIP, g, BessParams(rating_pu=0.03), t_end_s=320, dt=0.01)
    mask = r.t > 1.0
    ts = r.t[mask] - 1.0
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True, gridspec_kw={"height_ratios": [1.3, 2]})
    axes[0].plot(ts, r.f_hz[mask], color=C_CHG, lw=2)
    axes[0].axhline(50, color="k", lw=0.8)
    axes[0].set_ylabel("频率 (Hz)")
    axes[0].set_title("同一次事故，谁在什么时候补上了这 4% 的缺口  [教学模型，横轴为对数]")

    parts = [
        (np.clip(r.p_inertia[mask], 0, None), "转子动能（惯量）", C_PURPLE),
        (r.p_damping[mask], "负荷自然减少（阻尼）", C_GRID),
        (r.p_bess[mask], "储能一次调频", C_OK),
        (r.p_gov[mask], "火电/水电一次调频", C_ACC),
        (r.p_agc[mask], "AGC 二次调频", C_DIS),
    ]
    stack = np.vstack([p * 100 for p, _, _ in parts])
    axes[1].stackplot(ts, stack, labels=[n for _, n, _ in parts], colors=[c for _, _, c in parts], alpha=0.85)
    axes[1].axhline(TRIP * 100, color="k", ls="--", lw=1)
    axes[1].text(0.012, TRIP * 100 + 0.08, "缺口 4%", fontsize=9)
    axes[1].annotate("高出 4% 的部分：多发的功率\n在给转子重新加速（频率回升）", xy=(6, 4.3), xytext=(12, 4.7),
                     fontsize=8.5, arrowprops=dict(arrowstyle="->"))
    axes[1].set_xscale("log")
    axes[1].set_xlim(0.01, 320)
    axes[1].set_ylim(0, 6.2)
    axes[1].set_ylabel("补缺口的功率 (% 系统容量)")
    axes[1].set_xlabel("事故后时间 (s，对数刻度)")
    axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), fontsize=8.5, ncol=5)
    for x, label in [(0.1, "惯量：0~数秒"), (3.0, "一次调频：数秒~数十秒"), (120, "AGC：分钟级")]:
        axes[1].text(x, 5.8, label, ha="center", fontsize=9, bbox=dict(fc="white", ec=C_GRID, alpha=0.9))
    manifest("ch15_frequency_layers", [0.1, 3, 4, 120, 320, 50])
    save(fig, "ch15_frequency_layers")


def fig_droop():
    f = np.linspace(49.5, 50.5, 2001)
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    for mode, c, name in [("shift", C_OK, "连续型死区"), ("cut", C_ACC, "截断型死区")]:
        cfg = PrimaryFrequencyConfig(p_rated_kw=100_000, droop_ratio=0.02, deadband_hz=0.03, limit_ratio=0.10,
                                     deadband_mode=mode)
        p = np.array([primary_frequency_power(v, cfg) for v in f]) / 1000
        jump = np.where(np.abs(np.diff(p)) > 0.5)[0]
        p_plot = p.copy()
        p_plot[jump] = np.nan
        ax.plot(f, p_plot, color=c, lw=2.3, label=name)
    ax.axvspan(49.97, 50.03, color=C_ACC, alpha=0.15)
    ax.text(50, -3, "死区\n±0.03 Hz", ha="center", fontsize=9)
    ax.axhline(10, color=C_LIMIT, ls="--", lw=1)
    ax.axhline(-10, color=C_LIMIT, ls="--", lw=1)
    ax.text(50.3, 10.4, "限幅 +10% Pn", color=C_LIMIT, fontsize=9)
    ax.text(49.52, -10.9, "限幅 −10% Pn", color=C_LIMIT, fontsize=9)
    ax.plot(49.9, 7, "o", color=C_DIS, ms=8)
    ax.annotate("49.90 Hz → 放电 7 MW\n（连续型）", xy=(49.9, 7), xytext=(49.55, 3), arrowprops=dict(arrowstyle="->"))
    ax.text(49.55, -6, "频率低 → 放电（P>0）", color=C_DIS)
    ax.text(50.18, 5, "频率高 → 充电（P<0）", color=C_CHG)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("电网频率 (Hz)")
    ax.set_ylabel("一次调频功率增量 ΔP (MW)")
    ax.set_title("100 MW 储能的下垂特性：δ=2%，死区 ±0.03 Hz，限幅 ±10%  [教学示例参数]")
    ax.legend(loc="center right", bbox_to_anchor=(1, 0.62))
    manifest("ch15_droop", [0.03, 2, 7, 10, 49.5, 49.9, 50, 50.5, 100])
    save(fig, "ch15_droop")


def fig_rocof():
    rng = np.random.default_rng(3)
    dt = 0.02
    t = np.arange(0, 4, dt)
    f_true = np.where(t < 1, 50.0, 50.0 - 0.25 * (t - 1))
    f_meas = f_true + rng.normal(0, 0.004, t.size)
    raw = np.r_[np.nan, np.diff(f_meas) / dt]
    est = RocofEstimator(window_s=0.2)
    win = np.array([np.nan if (v := est.update(tt, ff)) is None else v for tt, ff in zip(t, f_meas)])
    fig, axes = plt.subplots(2, 1, figsize=(8.5, 5.6), sharex=True)
    axes[0].plot(t, f_meas, color=C_GRID, lw=1, label="频率测量（含 ±4 mHz 噪声）")
    axes[0].plot(t, f_true, color=C_CHG, lw=1.8, ls="--", label="真实频率")
    axes[0].set_ylabel("频率 (Hz)")
    axes[0].legend(loc="lower left")
    axes[1].plot(t, raw, color=C_LIMIT, lw=0.9, alpha=0.7, label="相邻两点相减：噪声被放大")
    axes[1].plot(t, win, color=C_OK, lw=2.2, label="200 ms 窗口直线拟合：平滑，约慢 100 ms")
    axes[1].axhline(-0.25, color=C_CHG, ls="--", lw=1.2, label="真实 RoCoF = −0.25 Hz/s")
    axes[1].set_ylim(-1.2, 0.8)
    axes[1].set_ylabel("RoCoF (Hz/s)")
    axes[1].set_xlabel("时间 (s)")
    axes[1].legend(loc="lower left", fontsize=8.5)
    axes[0].set_title("RoCoF 的难点：微分会放大噪声，滤波又会带来延迟")
    manifest("ch15_rocof", [0.004, 0.02, 0.2, -0.25, 4, 20, 50, 200])
    save(fig, "ch15_rocof")


def main():
    fig_event()
    fig_layers()
    fig_droop()
    fig_rocof()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
