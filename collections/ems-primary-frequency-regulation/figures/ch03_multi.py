# @AI_GENERATED
"""第 03 章配图：多资源协同下垂特性曲线。

所有参数均为 [教学示例]，不可直接用于现场整定。
"""
from __future__ import annotations

import numpy as np

from _style import (C_WIND, C_SOLAR, C_BESS, C_THERMAL, C_HYDRO, C_GRID, C_LIMIT,
                    C_OK, C_ACC, C_DIS, C_CHG, FN, IMG_DIR, manifest, save,
                    deadband_shift, deadband_cut, plt)


def fig_multi_resource():
    """四类资源的下垂特性同图对比"""
    fig, ax = plt.subplots(figsize=(10, 6))

    resources = [
        ("光伏", 100.0, 3.0, 0.06, 10.0, C_SOLAR, deadband_shift),
        ("风电", 100.0, 2.0, 0.10, 10.0, C_WIND, deadband_shift),
        ("火电", 100.0, 5.0, 0.033, 6.0, C_THERMAL, deadband_shift),
        ("水电", 100.0, 3.0, 0.05, 10.0, C_HYDRO, deadband_shift),
    ]

    f = np.linspace(49.50, 50.50, 2001)
    for name, pn_mw, delta_pct, db_hz, limit_pct, color, db_func in resources:
        k = pn_mw / (delta_pct / 100 * FN)
        df = f - FN
        eff = db_func(df, db_hz)
        dp = np.clip(-k * eff, -limit_pct / 100 * pn_mw, limit_pct / 100 * pn_mw)
        # 标幺化
        dp_pu = dp / pn_mw * 100
        ax.plot(f, dp_pu, color=color, lw=2.3, label=f"{name}  δ={delta_pct}% 死区±{int(db_hz*1000)} mHz")

    # 死区阴影（各资源不同，只画最宽的风电和最窄的）
    for name, _, _, db_hz, _, color, _ in [("风电", 100, 2, 0.10, 10, C_WIND, deadband_shift),
                                             ("光伏", 100, 3, 0.06, 10, C_SOLAR, deadband_shift)]:
        ax.axvline(FN - db_hz, color=color, ls=":", lw=1, alpha=0.5)
        ax.axvline(FN + db_hz, color=color, ls=":", lw=1, alpha=0.5)

    ax.axvspan(FN - 0.033, FN + 0.033, color=C_THERMAL, alpha=0.04)
    ax.axvspan(FN - 0.06, FN + 0.06, color=C_SOLAR, alpha=0.04)

    # 限幅标注
    for y_val, label in [(10, "+10% Pn（风光水）"), (6, "+6% Pn（火电）"),
                          (-10, "−10% Pn"), (-6, "−6% Pn")]:
        ax.axhline(y_val, color=C_GRID, ls="--", lw=0.8, alpha=0.5)
    ax.text(50.36, 10.4, "限幅 +10% Pn\n（风光水）", fontsize=8, color=C_GRID)
    ax.text(50.36, 6.4, "限幅 +6% Pn\n（火电）", fontsize=8, color=C_GRID)

    # 标注各资源"起跳点"差异
    for name, _, _, db_hz, _, color, _ in resources:
        ax.annotate(f"{name}\n{int(db_hz*1000)} mHz", xy=(FN + db_hz, 0),
                    xytext=(FN + db_hz + 0.03, -6), fontsize=7.5, color=color,
                    arrowprops=dict(arrowstyle="->", color=color, lw=0.8))

    # 协同理由标注
    ax.annotate("死区不同 → 小扰动时\n仅光伏/火电响应\n风电不动（保护机械）",
                xy=(49.94, 3), xytext=(49.58, -2),
                arrowprops=dict(arrowstyle="->", color=C_DIS),
                fontsize=8.5, bbox=dict(fc="white", ec=C_GRID, alpha=0.85))
    ax.annotate("大扰动时所有资源\n按各自斜率出力\n风电 δ小 → 增出力猛",
                xy=(49.80, 7.5), xytext=(49.58, 4),
                arrowprops=dict(arrowstyle="->", color=C_DIS),
                fontsize=8.5, bbox=dict(fc="white", ec=C_GRID, alpha=0.85))

    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(FN, color="k", lw=0.5, alpha=0.3)
    ax.set_xlabel("电网频率 (Hz)")
    ax.set_ylabel("一次调频出力增量 (% Pn)")
    ax.set_title("多调频资源协同下垂特性  [教学示例参数，不直接用于整定]")
    ax.set_xlim(49.55, 50.45)
    ax.set_ylim(-12, 12)
    ax.legend(loc="lower right", fontsize=8, ncol=2)

    manifest("ch03_multi_resource",
             [FN, 0.033, 0.05, 0.06, 0.10, 2, 3, 5, 6, 10, 49.50, 50.50])
    save(fig, "ch03_multi_resource")


def fig_wind_solar_contrast():
    """风电 vs 光伏：参数差异的物理根因"""
    pn_wind, pn_solar = 100, 100
    db_wind, db_solar = 0.10, 0.06
    delta_wind, delta_solar = 2.0, 3.0
    limit_wind, limit_solar = 10.0, 10.0

    k_wind = pn_wind / (delta_wind / 100 * FN)
    k_solar = pn_solar / (delta_solar / 100 * FN)

    f = np.linspace(49.50, 50.50, 1001)
    df = f - FN
    dp_wind = np.clip(-k_wind * deadband_shift(df, db_wind), -limit_wind/100*pn_wind, limit_wind/100*pn_wind)
    dp_solar = np.clip(-k_solar * deadband_shift(df, db_solar), -limit_solar/100*pn_solar, limit_solar/100*pn_solar)

    fig, ax = plt.subplots(figsize=(9, 5.2))

    ax.plot(f, dp_wind, color=C_WIND, lw=2.5, label=f"风电  δ={delta_wind}%  死区±{int(db_wind*1000)} mHz")
    ax.plot(f, dp_solar, color=C_SOLAR, lw=2.5, label=f"光伏  δ={delta_solar}%  死区±{int(db_solar*1000)} mHz")

    # 死区
    ax.axvspan(FN - db_wind, FN + db_wind, color=C_WIND, alpha=0.06)
    ax.axvspan(FN - db_solar, FN + db_solar, color=C_SOLAR, alpha=0.06)
    for db, c, label in [(db_wind, C_WIND, "风电死区"), (db_solar, C_SOLAR, "光伏死区")]:
        ax.axvline(FN - db, color=c, ls="--", lw=1)
        ax.axvline(FN + db, color=c, ls="--", lw=1)

    # 对比标注
    ax.annotate(f"风电死区更宽（±{int(db_wind*1000)} mHz）\n小扰动 → 不响应，保护桨叶",
                xy=(FN + db_wind + 0.005, 1.5), xytext=(50.22, 4),
                arrowprops=dict(arrowstyle="->", color=C_WIND),
                fontsize=8.5, color=C_WIND,
                bbox=dict(fc="white", ec=C_WIND, alpha=0.85))
    ax.annotate(f"光伏死区更窄（±{int(db_solar*1000)} mHz）\n小扰动 → 响应，发挥电子快优势",
                xy=(FN + db_solar + 0.005, 3.2), xytext=(50.22, -3),
                arrowprops=dict(arrowstyle="->", color=C_SOLAR),
                fontsize=8.5, color="olive",
                bbox=dict(fc="white", ec=C_SOLAR, alpha=0.85))

    # 陡峭程度对比
    ax.annotate(f"风电 δ小（{delta_wind}%）→ 斜率大\n大扰动时出力猛",
                xy=(49.80, dp_wind[np.argmin(np.abs(f - 49.80))]),
                xytext=(49.58, -6),
                arrowprops=dict(arrowstyle="->", color=C_WIND),
                fontsize=8.5, color=C_WIND,
                bbox=dict(fc="white", ec=C_WIND, alpha=0.85))

    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("电网频率 (Hz)")
    ax.set_ylabel("一次调频出力增量 ΔP (MW)")
    ax.set_title("风电 vs 光伏：参数差异来自执行机构物理特性  [Pn=100 MW，教学示例]")
    ax.set_xlim(49.58, 50.42)
    ax.set_ylim(-11, 11)
    ax.legend(loc="lower right", fontsize=8.5)

    manifest("ch03_wind_solar_contrast",
             [FN, db_wind, db_solar, delta_wind, delta_solar, 100, 10, 49.80, 49.90, 50.10])
    save(fig, "ch03_wind_solar_contrast")


def main():
    fig_multi_resource()
    fig_wind_solar_contrast()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end