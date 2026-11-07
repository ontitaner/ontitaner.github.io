# @AI_GENERATED
"""第 07 章配图：积分电量对账、考核归因路径。

所有参数均为 [教学示例]，不可直接用于现场整定。
"""
from __future__ import annotations

import numpy as np

from _style import (C_DIS, C_CHG, C_GRID, C_LIMIT, C_OK, C_ACC, C_PURPLE,
                    IMG_DIR, manifest, save, deadband_shift, deadband_cut, FN, plt)


def fig_integration_compare():
    """理论积分电量 vs 实际积分电量对比"""
    t = np.linspace(0, 30, 601)
    dt = t[1] - t[0]

    # 模拟一次频率事件
    f_event = np.where(t < 2, 50.0,
                np.where(t < 8, 50.0 - 0.15 * (1 - np.exp(-(t - 2) / 0.5)),
                np.where(t < 15, 49.9 + 0.08 * (1 - np.exp(-(t - 8) / 3.0)),
                50.0 - 0.02 * np.exp(-(t - 15) / 2.0))))

    # 理论出力（按规程参数）
    pn = 100
    delta_pct = 3.0
    db = 0.06
    limit = 10.0
    k = pn / (delta_pct / 100 * 50.0)
    df = f_event - 50.0
    eff = np.where(np.abs(df) <= db, 0, df - np.sign(df) * db)
    p_theory = np.clip(-k * eff, -limit, limit)

    # 实际出力（有延迟 + 偏差：一阶滞后滤波模拟）
    p_actual = np.zeros_like(t)
    alpha = dt / 1.5
    for i in range(1, len(t)):
        p_actual[i] = p_actual[i-1] + (p_theory[i-1] - p_actual[i-1]) * alpha
    p_actual = p_actual + np.random.default_rng(42).normal(0, 0.3, len(t))
    p_actual = np.clip(p_actual, -limit, limit)

    # 积分
    q_theory = np.cumsum(np.maximum(p_theory, 0)) * dt / 3600
    q_actual = np.cumsum(np.maximum(p_actual, 0)) * dt / 3600

    fig, axes = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True,
                              gridspec_kw={"height_ratios": [1.2, 1]})

    # 上图：频率
    ax = axes[0]
    ax.plot(t, f_event, color=C_CHG, lw=2.2)
    ax.axhline(50.0, color="k", lw=0.8)
    ax.axhspan(50.0 - db, 50.0 + db, color=C_GRID, alpha=0.08)
    ax.axhline(50.0 - db, color=C_GRID, ls=":", lw=1)
    ax.axhline(50.0 + db, color=C_GRID, ls=":", lw=1)
    ax.text(0.5, 50.0 - db, f"死区 {50.0-db:.3f} Hz", fontsize=8, color=C_GRID, va="bottom")
    ax.set_ylabel("电网频率 (Hz)")
    ax.set_title("一次频率事件：频率曲线与调频出力  [教学示例]")
    ax.set_ylim(49.78, 50.05)
    ax.legend([ax.plot([], [], color=C_CHG, lw=2.2)[0]], ["电网频率"], loc="lower right", fontsize=8.5)

    # 中图：出力对比
    ax2 = axes[1]
    ax2.plot(t, p_theory, color=C_OK, lw=2.2, label="理论调频出力（按规程参数）")
    ax2.plot(t, p_actual, color=C_DIS, lw=2.2, label="实际调频出力（有延迟/偏差）")
    ax2.fill_between(t, 0, p_theory, color=C_OK, alpha=0.08)
    ax2.fill_between(t, 0, p_actual, color=C_DIS, alpha=0.08)
    ax2.axhline(0, color="k", lw=0.8)
    ax2.set_ylabel("调频出力 (MW)")
    ax2.set_xlabel("时间 (s)")
    ax2.legend(loc="upper right", fontsize=8.5)

    # 积分电量标注
    ax2.annotate(f"理论积分电量\nQ_theory = {q_theory[-1]:.2f} kWh",
                 xy=(25, p_theory[-50]), xytext=(22, 7),
                 arrowprops=dict(arrowstyle="->", color=C_OK),
                 fontsize=9, color=C_OK,
                 bbox=dict(fc="white", ec=C_OK, alpha=0.85))
    ax2.annotate(f"实际积分电量\nQ_actual = {q_actual[-1]:.2f} kWh\n完成率 = {q_actual[-1]/q_theory[-1]*100:.0f}%",
                 xy=(25, p_actual[-50]), xytext=(22, 3.5),
                 arrowprops=dict(arrowstyle="->", color=C_DIS),
                 fontsize=9, color=C_DIS,
                 bbox=dict(fc="white", ec=C_DIS, alpha=0.85))

    fig.text(0.5, -0.02, "阴影面积 = ∫P(t) dt  →  积分电量（kWh）",
             ha="center", fontsize=9, color=C_GRID)

    manifest("ch07_integration_compare",
             [q_theory[-1], q_actual[-1], q_actual[-1] / q_theory[-1] * 100, db, 50, 30])
    save(fig, "ch07_integration_compare")


def fig_failure_attribution():
    """三条归因路径：每种路径用一个数据案例说明"""
    pn = 100
    delta_pct = 3.0
    db = 0.06
    limit = 10.0
    k = pn / (delta_pct / 100 * FN)

    f = np.linspace(49.80, 50.20, 501)
    df = f - FN

    t = np.linspace(0, 30, 601)
    dt = t[1] - t[0]

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))

    # ═══ 路径 1：死区类型差异 → 积分电量口径不一致 ═══
    ax = axes[0]
    eff_cont = deadband_shift(df, db)
    eff_cut = deadband_cut(df, db)
    dp_cont = np.clip(-k * eff_cont, -limit, limit)
    dp_cut = np.clip(-k * eff_cut, -limit, limit)
    ax.plot(f, dp_cont, color=C_OK, lw=2.5, label="连续型死区")
    ax.plot(f, dp_cut, color=C_LIMIT, lw=2.5, label="截断型死区")
    ax.axvspan(FN - db, FN + db, color=C_GRID, alpha=0.1)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlim(49.82, 50.18)
    ax.set_ylim(-12, 12)
    ax.set_xlabel("频率 (Hz)")
    ax.set_ylabel("出力 ΔP (MW)")
    ax.set_title("路径 1：考核口径不一致", fontsize=10, color=C_LIMIT)
    ax.legend(fontsize=7.2, loc="lower right")
    # 标注差异
    idx = np.argmin(np.abs(f - 49.88))
    ax.plot(f[idx], dp_cont[idx], "o", color=C_OK, ms=8, zorder=5)
    ax.plot(f[idx], dp_cut[idx], "s", color=C_LIMIT, ms=8, zorder=5)
    ax.annotate(f"同一频点 {f[idx]:.2f} Hz\n连续型={dp_cont[idx]:.1f} MW\n截断型={dp_cut[idx]:.1f} MW",
                xy=(f[idx], (dp_cont[idx] + dp_cut[idx]) / 2),
                xytext=(49.86, -8), fontsize=7.8, color=C_LIMIT,
                arrowprops=dict(arrowstyle="->", color=C_LIMIT),
                bbox=dict(fc="white", ec=C_LIMIT, alpha=0.85))
    ax.text(0.5, -0.18, "死区类型差异 → 理论积分电量本身不同",
            transform=ax.transAxes, ha="center", fontsize=7.5, color=C_GRID)

    # ═══ 路径 2：PCS ramp 限制 → 出力跟踪滞后 ═══
    ax = axes[1]
    p_cmd = np.where(t < 5, 0,
              np.where(t < 8, np.minimum(10, (t - 5) * 3.5),
              10.0))
    p_act = np.zeros_like(t)
    ramp_limit = 1.2  # MW/s
    for i in range(1, len(t)):
        target = p_cmd[i]
        step = np.clip(target - p_act[i-1], -ramp_limit * dt, ramp_limit * dt)
        p_act[i] = p_act[i-1] + step
    ax.step(t, p_cmd, where="post", color=C_GRID, ls="--", lw=1.6, label="指令 ΔP")
    ax.plot(t, p_act, color=C_ACC, lw=2.5, label=f"实际（ramp ≤ {ramp_limit} MW/s）")
    ax.fill_between(t, p_cmd, p_act, alpha=0.15, color=C_LIMIT)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("出力 ΔP (MW)")
    ax.set_title("路径 2：实际能力不足", fontsize=10, color=C_ACC)
    ax.legend(fontsize=7.2, loc="lower right")
    ax.set_xlim(0, 30)
    ax.set_ylim(-1, 12)
    ax.annotate("Ramp 限制导致\n跟踪偏差 → 积分偏小",
                xy=(10, 7), xytext=(18, 8), fontsize=7.8, color=C_LIMIT,
                arrowprops=dict(arrowstyle="->", color=C_LIMIT),
                bbox=dict(fc="white", ec=C_LIMIT, alpha=0.85))
    ax.text(0.5, -0.18, "PCS 速率 / SOC / 空间约束 → 出力跟不上指令",
            transform=ax.transAxes, ha="center", fontsize=7.5, color=C_GRID)

    # ═══ 路径 3：通信延迟 → 频率与出力时间轴偏移 ═══
    ax = axes[2]
    f_true = np.where(t < 3, 50.0,
               np.where(t < 10, 50.0 - 0.15 * (1 - np.exp(-(t - 3) / 1.0)),
               np.where(t < 22, 50.0 - 0.08 + 0.06 * (1 - np.exp(-(t - 10) / 5.0)),
               50.0)))
    delay_s = 1.5
    f_delayed = np.interp(t - delay_s, t, f_true, left=50.0, right=50.0)
    df_true = f_true - FN
    df_del = f_delayed - FN
    eff_true = deadband_shift(df_true, db)
    eff_del = deadband_shift(df_del, db)
    p_true = np.clip(-k * eff_true, -limit, limit)
    p_del = np.clip(-k * eff_del, -limit, limit)
    ax.plot(t, p_true, color=C_OK, lw=2.5, label="无延迟出力")
    ax.plot(t, p_del, color=C_PURPLE, lw=2.5, label=f"延迟 {delay_s}s 出力")
    ax.fill_between(t, p_true, p_del, alpha=0.12, color=C_PURPLE)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("出力 ΔP (MW)")
    ax.set_title("路径 3：数据质量 / 链路故障", fontsize=10, color=C_PURPLE)
    ax.legend(fontsize=7.2, loc="lower right")
    ax.set_xlim(0, 30)
    ax.set_ylim(-1, 12)
    ax.annotate(f"通信延迟 {delay_s}s\n时标错位 → 出力\n时间轴整体偏移",
                xy=(8, 4), xytext=(17, 7), fontsize=7.8, color=C_PURPLE,
                arrowprops=dict(arrowstyle="->", color=C_PURPLE),
                bbox=dict(fc="white", ec=C_PURPLE, alpha=0.85))
    ax.text(0.5, -0.18, "延迟 / 丢点 / 时标错位 → 频率与出力错配",
            transform=ax.transAxes, ha="center", fontsize=7.5, color=C_GRID)

    fig.suptitle("考核不合格的三条归因路径（数据驱动示例）  [教学示例]", fontsize=12, y=1.02)

    manifest("ch07_failure_attribution", [])
    save(fig, "ch07_failure_attribution")


def main():
    fig_integration_compare()
    fig_failure_attribution()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end