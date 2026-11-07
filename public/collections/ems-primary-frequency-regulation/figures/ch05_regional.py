# @AI_GENERATED
"""第 05 章配图：区域细则差异对照、积分电量判定流程。

所有参数均为 [教学示例]，不可直接用于现场整定。
"""
from __future__ import annotations

import numpy as np

from _style import (C_DIS, C_CHG, C_GRID, C_LIMIT, C_OK, C_ACC, C_PURPLE,
                    C_WIND, C_SOLAR, FN, IMG_DIR, manifest, save, deadband_shift, plt)


def fig_regional_droop():
    """三区域下垂特性对比"""
    regions = [
        ("华东", 5.0, 0.033, 6.0, C_OK),
        ("东北", 3.0, 0.05, 10.0, C_ACC),
        ("山西", 3.0, 0.05, 10.0, C_PURPLE),
        # 东北分段调差简化为单段
    ]

    f = np.linspace(49.60, 50.40, 801)
    pn = 100

    fig, ax = plt.subplots(figsize=(9, 5.8))

    for name, delta_pct, db_hz, limit_pct, color in regions:
        k = pn / (delta_pct / 100 * FN)
        df = f - FN
        eff = deadband_shift(df, db_hz)
        dp = np.clip(-k * eff, -limit_pct / 100 * pn, limit_pct / 100 * pn)
        ax.plot(f, dp, color=color, lw=2.5, label=f"{name}  δ={delta_pct}% 死区 ±{int(db_hz*1000)} mHz 限幅 ±{limit_pct}% Pn")

        # 标注死区
        ax.axvline(FN - db_hz, color=color, ls=":", lw=0.8, alpha=0.5)
        ax.axvline(FN + db_hz, color=color, ls=":", lw=0.8, alpha=0.5)

    # 东北分段调差标注
    ax.annotate("东北细则实际为分段调差\n大频差时更陡（此处简化）",
                xy=(49.82, 0), xytext=(49.68, -5),
                arrowprops=dict(arrowstyle="->", color=C_ACC),
                fontsize=8, color=C_ACC,
                bbox=dict(fc="white", ec=C_ACC, alpha=0.85))

    # 华东 vs 东北/山西 对比
    ax.annotate("华东 δ=5%（温和）\n限幅仅 6% Pn\n同一频差下出力最小",
                xy=(49.92, 0.4), xytext=(50.12, -6),
                arrowprops=dict(arrowstyle="->", color=C_OK),
                fontsize=8, color=C_OK,
                bbox=dict(fc="white", ec=C_OK, alpha=0.85))
    ax.annotate("东北/山西 δ=3%（较激）\n限幅 10% Pn\n同一频差下出力更大",
                xy=(49.92, 2.5), xytext=(50.12, 6),
                arrowprops=dict(arrowstyle="->", color=C_ACC),
                fontsize=8, color=C_ACC,
                bbox=dict(fc="white", ec=C_ACC, alpha=0.85))

    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(FN, color="k", lw=0.5, alpha=0.3)
    ax.set_xlabel("电网频率 (Hz)")
    ax.set_ylabel("一次调频出力增量 ΔP (MW)")
    ax.set_title("三区域一次调频下垂特性对比  [教学示例参数，以项目适用细则为准]")
    ax.set_xlim(49.62, 50.38)
    ax.set_ylim(-11, 11)
    ax.legend(loc="lower right", fontsize=7.8)

    manifest("ch05_regional_droop",
             [FN, 3, 5, 0.033, 0.05, 6, 10, 49.60, 50.40, 100])
    save(fig, "ch05_regional_droop")


def fig_assessment_flow():
    """积分电量考核两级判定：通过 vs 不通过 两例对比"""
    pn = 100
    delta_pct = 3.0
    db = 0.06
    limit = 10.0
    k = pn / (delta_pct / 100 * FN)

    t = np.linspace(0, 45, 901)
    dt = t[1] - t[0]

    def simulate_response(tau):  # tau=跟踪延迟，秒
        f = np.where(t < 5, 50.0,
              np.where(t < 12, 50.0 - 0.18 * (1 - np.exp(-(t - 5) / 1.2)),
              np.where(t < 25, 50.0 - 0.04 + 0.10 * (1 - np.exp(-(t - 12) / 10.0)),
              50.0)))
        df = f - FN
        eff = deadband_shift(df, db)
        p_theory = np.clip(-k * eff, -limit, limit)
        p_actual = np.zeros_like(t)
        alpha = dt / tau
        for i in range(1, len(t)):
            p_actual[i] = p_actual[i-1] + (p_theory[i-1] - p_actual[i-1]) * alpha
        w_theory = np.cumsum(np.maximum(p_theory, 0)) * dt / 3600
        w_actual = np.cumsum(np.maximum(p_actual, 0)) * dt / 3600
        return f, p_theory, p_actual, w_theory, w_actual

    f_pass, pt_pass, pa_pass, wt_pass, wa_pass = simulate_response(tau=1.0)
    f_fail, pt_fail, pa_fail, wt_fail, wa_fail = simulate_response(tau=5.0)

    ratio_pass = wa_pass[-1] / wt_pass[-1] * 100
    ratio_fail = wa_fail[-1] / wt_fail[-1] * 100

    fig, axes = plt.subplots(3, 2, figsize=(12, 9),
                              gridspec_kw={"height_ratios": [1, 1.2, 1]})

    cases = [
        ("A：正常响应（考核通过）", f_pass, pt_pass, pa_pass, wt_pass, wa_pass, ratio_pass, C_OK),
        ("B：响应滞后（考核不通过）", f_fail, pt_fail, pa_fail, wt_fail, wa_fail, ratio_fail, C_LIMIT),
    ]

    for col, (title, f_arr, pt, pa, wt, wa, ratio, color) in enumerate(cases):
        # 行 0：频率曲线
        ax = axes[0, col]
        ax.plot(t, f_arr, color=C_CHG, lw=2.2)
        ax.axhline(FN, color="k", lw=0.8)
        ax.axhspan(FN - db, FN + db, color=C_GRID, alpha=0.1)
        ax.axhline(FN - db, color=C_GRID, ls=":", lw=0.8)
        ax.axhline(FN + db, color=C_GRID, ls=":", lw=0.8)
        ax.set_ylim(49.81, 50.04)
        ax.set_ylabel("频率 (Hz)")
        ax.set_title(title, fontsize=10.5, color=color)

        # 行 1：理论 vs 实际出力 + 积分面积
        ax = axes[1, col]
        ax.fill_between(t, 0, pt, color=C_OK, alpha=0.15, label="W_theory（理论积分）")
        ax.fill_between(t, 0, pa, color=C_ACC, alpha=0.18, label="W_actual（实际积分）")
        ax.plot(t, pt, color=C_OK, lw=2.2, label="理论出力")
        ax.plot(t, pa, color=C_ACC, lw=2.2, label="实际出力")
        ax.axhline(0, color="k", lw=0.8)
        ax.set_ylabel("出力 ΔP (MW)")
        ax.legend(loc="upper right", fontsize=7.5, ncol=2)
        ax.set_ylim(-2, 12)

        # 行 2：累积积分电量
        ax = axes[2, col]
        ax.plot(t, wt, color=C_OK, lw=2.2, label=f"W_theory = {wt[-1]:.2f} kWh")
        ax.plot(t, wa, color=color, lw=2.2, label=f"W_actual = {wa[-1]:.2f} kWh")
        ax.axhline(wt[-1] * 0.6, color=C_LIMIT, ls="--", lw=1.3)
        ax.text(t[-1] * 0.45, wt[-1] * 0.6 + wt[-1] * 0.02, "60% 及格线",
                fontsize=8, color=C_LIMIT, va="bottom")
        ax.set_ylabel("积分电量 (kWh)")
        ax.set_xlabel("时间 (s)")
        ax.legend(loc="upper left", fontsize=8)

        # 两级判定结果标注
        pct_text = f"完成率 = {ratio:.0f}%"
        verdict = "[通过] 考核通过" if ratio >= 60 else "[不通过] 考核不通过"
        ax.annotate(f"{pct_text}\n{verdict}",
                    xy=(t[-1], wa[-1]), xytext=(t[-1] * 0.62, wa[-1] * 0.65),
                    fontsize=10, fontweight="bold", color=color, ha="center",
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.5),
                    bbox=dict(fc="white", ec=color, alpha=0.9, pad=5, boxstyle="round"))

    fig.suptitle("积分电量考核两级判定：符号一致 | 完成率 >= 60%  [教学示例]",
                 fontsize=12, y=1.01)
    fig.text(0.5, -0.01, "F1 = 考核电量×单价（完成率不足）  |  F2 = F1×2（方向错误加罚）",
             ha="center", fontsize=8.5, color=C_GRID)

    manifest("ch05_assessment_flow", [60, 100, ratio_pass, ratio_fail])
    save(fig, "ch05_assessment_flow")


def main():
    fig_regional_droop()
    fig_assessment_flow()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end