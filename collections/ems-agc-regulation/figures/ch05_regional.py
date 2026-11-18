# @AI_GENERATED
"""第 05 章配图：华东/东北/山西三区域 AGC 细则差异。

所有参数均为 [教学示例]，不可直接用于现场整定。
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Patch

from _style import (C_K1, C_K2, C_K3, C_GRID, C_LIMIT, C_OK, C_ACC, C_PURPLE,
                    C_CHG, manifest, save, plt)

REGIONS = ["华东", "东北", "山西"]
# 与正文 05 章参数对照表 / lab/agc_core.py REGION_PARAMS 逐项一致
K1_PN_PER_MIN = [1.0, 1.5, 1.0]
K2_MAX_S = [60.0, 30.0, 60.0]
K3_MAX_PCT = [3.0, 3.0, 2.0]
DEADBAND_MW = [0.3, 0.1, 0.3]
MIN_STEP_MW = [1.0, 0.5, 1.0]
POLL_S = [8.0, 4.0, 8.0]
PASS_LINE = [80.0, 75.0, 80.0]
PN = 100.0
CHAIN_EXTRA_S = 5.5   # 解析 0.5 + 分配 0.5 + 下发 0.5 + PCS 1.0 + 到达阈值 3.0


def _k1_score(ramp_mw_s: float, req_pn_per_min: float) -> float:
    req_mw_s = req_pn_per_min * PN / 60.0
    return min(100.0, ramp_mw_s / req_mw_s * 100.0)


def _k2_score(poll_s: float, limit_s: float) -> float:
    total = poll_s + CHAIN_EXTRA_S
    return max(0.0, 100.0 * (1.0 - total / limit_s))


def _k3_score(actual_pct: float, limit_pct: float) -> float:
    return max(0.0, 100.0 * (1.0 - actual_pct / limit_pct))


def _composite(k1: float, k2: float, k3: float) -> float:
    return round(round(0.30 * k1, 1) + round(0.20 * k2, 1) + round(0.50 * k3, 1), 1)


def fig_region_params():
    """三区域参数差异：三子图——K1/K2/K3 限值 + 死区合规带 + 链路延时预算"""
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.4))
    x = np.arange(len(REGIONS))
    w = 0.26

    # ── 左图：三项限值并列（各自归一化到三区域最大值，柱顶写真实值）──
    ax = axes[0]
    norm = [np.array(v) / max(v) for v in (K1_PN_PER_MIN, K2_MAX_S, K3_MAX_PCT)]
    ax.bar(x - w, norm[0], w, color=C_K1, alpha=0.88)
    ax.bar(x, norm[1], w, color=C_K2, alpha=0.88)
    ax.bar(x + w, norm[2], w, color=C_K3, alpha=0.88)

    for xi, v in zip(x - w, K1_PN_PER_MIN):
        ax.text(xi, v / max(K1_PN_PER_MIN) + 0.04, f"{v:.1f}", ha="center",
                fontsize=9, color=C_K1, fontweight="bold")
    for xi, v in zip(x, K2_MAX_S):
        ax.text(xi, v / max(K2_MAX_S) + 0.04, f"{v:.0f}", ha="center",
                fontsize=9, color=C_K2, fontweight="bold")
    for xi, v in zip(x + w, K3_MAX_PCT):
        ax.text(xi, v / max(K3_MAX_PCT) + 0.04, f"{v:.1f}", ha="center",
                fontsize=9, color=C_K3, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{r}\n轮询{p:.0f}s" for r, p in zip(REGIONS, POLL_S)], fontsize=9)
    ax.set_ylabel("相对严格度（各指标按三区域最大值归一化）")
    ax.set_ylim(0, 1.55)
    ax.set_yticks([0, 0.5, 1.0])
    ax.set_yticklabels(["0", "50%", "100%"])
    ax.set_title("三项限值：东北最快要命，山西精度最严", fontsize=10)
    handles = [Patch(color=C_K1, alpha=0.88, label="K1 要求 (Pn/min)"),
               Patch(color=C_K2, alpha=0.88, label="K2 上限 (s)"),
               Patch(color=C_K3, alpha=0.88, label="K3 上限 (% Pn)")]
    ax.legend(handles=handles, fontsize=7.5, ncol=1, loc="upper center", frameon=True)

    # ── 中图：死区合规带（允许上限 = 最小指令步长 ÷ 2）──
    ax = axes[1]
    upper = [s / 2 for s in MIN_STEP_MW]
    ax.bar(x, upper, 0.52, color=C_GRID, alpha=0.28, label="死区允许上限 = 步长÷2")
    ax.bar(x, DEADBAND_MW, 0.24, color=C_OK, alpha=0.95, label="本地细则死区")
    ax.plot(x, DEADBAND_MW, "s", color=C_LIMIT, ms=7,
            label="照搬华东配置 0.3 MW")
    for xi, u, d in zip(x, upper, DEADBAND_MW):
        ax.text(xi, u + 0.025, f"上限 {u:.2f}", ha="center", fontsize=8, color=C_GRID)
        ax.text(xi - 0.16, d, f"{d:.1f}", ha="right", va="center", fontsize=9,
                color=C_OK, fontweight="bold")
    ax.annotate("东北：0.3 > 0.25 → 违规\n小步长指令被死区吞掉",
                xy=(1.0, 0.30), xytext=(1.45, 0.58),
                arrowprops=dict(arrowstyle="->", color=C_LIMIT),
                fontsize=8, color=C_LIMIT,
                bbox=dict(fc="white", ec=C_LIMIT, alpha=0.95))
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r}\n步长{s:.1f} MW" for r, s in zip(REGIONS, MIN_STEP_MW)], fontsize=9)
    ax.set_ylabel("指令死区 (MW)")
    ax.set_xlim(-0.62, 2.78)
    ax.set_ylim(0, 0.95)
    ax.set_title("死区合规：照搬华东配置在东北违规", fontsize=10)
    ax.legend(fontsize=7.5, loc="upper left")

    # ── 右图：K2 链路延时预算（六段累加）──
    ax = axes[2]
    seg_labels = ["104轮询", "EMS解析", "死区判定", "EMS→PCS", "PCS响应", "到达阈值"]
    seg_fixed = [0.5, 0.5, 0.5, 1.0, 3.0]
    colors = [C_GRID, C_CHG, C_ACC, C_PURPLE, C_K1, C_K3]
    bottoms = np.zeros(len(REGIONS))
    for i, (lbl, c) in enumerate(zip(seg_labels, colors)):
        vals = np.array([POLL_S[j] if i == 0 else seg_fixed[i - 1] for j in range(len(REGIONS))])
        ax.bar(x, vals, 0.46, bottom=bottoms, color=c, alpha=0.9, label=lbl)
        bottoms += vals
    for xi, tot, lim in zip(x, bottoms, K2_MAX_S):
        ax.text(xi, tot + 0.6, f"{tot:.1f} s", ha="center", fontsize=9,
                color=C_OK, fontweight="bold")
        ax.text(xi, tot + 3.1, f"限 {lim:.0f} s", ha="center", fontsize=8, color=C_LIMIT)
    ax.plot([0.75, 1.25], [30, 30], color=C_LIMIT, lw=2.4)
    ax.text(1.0, 31.4, "东北 K2 上限 30 s", ha="center", fontsize=8, color=C_LIMIT)
    ax.set_xticks(x)
    ax.set_xticklabels(REGIONS, fontsize=9)
    ax.set_ylabel("累计延时 (s)")
    ax.set_ylim(0, 38)
    ax.set_title("K2 链路预算：东北限值减半，余量也减半", fontsize=10)
    ax.legend(fontsize=7, ncol=2, loc="upper left")

    fig.suptitle("三区域 AGC 细则差异：限值 / 死区 / 延时预算  [Pn=100 MW，教学示例]",
                 fontsize=12, y=1.03)
    fig.text(0.5, -0.03,
             "K1 要求换算：1.0 Pn/min = 100 MW/min = 1.67 MW/s；1.5 Pn/min = 2.5 MW/s",
             ha="center", fontsize=8.5, color=C_GRID)

    manifest("ch05_region_params",
             K1_PN_PER_MIN + K2_MAX_S + K3_MAX_PCT + DEADBAND_MW + MIN_STEP_MW
             + POLL_S + PASS_LINE + [PN, CHAIN_EXTRA_S] + [round(t, 1) for t in bottoms])
    save(fig, "ch05_region_params")


def fig_same_device():
    """同一台设备在三套细则下的得分：设备A 合格 / 设备B 偏弱"""
    devices = [
        ("设备A 合格设备", 1.8, 0.5),
        ("设备B 偏弱设备", 1.0, 1.5),
    ]
    scores = []
    for _, ramp, k3 in devices:
        rows = []
        for j in range(len(REGIONS)):
            k1 = _k1_score(ramp, K1_PN_PER_MIN[j])
            k2 = _k2_score(POLL_S[j], K2_MAX_S[j])
            k3s = _k3_score(k3, K3_MAX_PCT[j])
            rows.append((k1, k2, k3s, _composite(k1, k2, k3s)))
        scores.append(rows)

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.6))
    legend_handles = None
    for ax, (name, ramp, k3), rows in zip(axes, devices, scores):
        x = np.arange(len(REGIONS))
        w = 0.2
        b1 = ax.bar(x - 1.5 * w, [r[0] for r in rows], w, color=C_K1, label="K1 分")
        b2 = ax.bar(x - 0.5 * w, [r[1] for r in rows], w, color=C_K2, label="K2 分")
        b3 = ax.bar(x + 0.5 * w, [r[2] for r in rows], w, color=C_K3, label="K3 分")
        b4 = ax.bar(x + 1.5 * w, [r[3] for r in rows], w, color=C_PURPLE, label="综合分")

        for bars in (b1, b2, b3, b4):
            for bar in bars:
                h = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, h + 1.0, f"{h:.1f}",
                        ha="center", fontsize=7.5)

        for xi, line, tot in zip(x, PASS_LINE, [r[3] for r in rows]):
            ax.plot([xi - 0.44, xi + 0.44], [line, line], color=C_LIMIT, ls="--", lw=1.6)
            ax.text(xi + 0.52, line, f"合格线\n{line:.0f}", ha="left", va="center",
                    fontsize=7.5, color=C_LIMIT)
            ok = tot >= line
            ax.text(xi, 110, "合格" if ok else "不合格", ha="center", fontsize=9,
                    color=C_OK if ok else C_LIMIT, fontweight="bold")

        ax.set_xticks(x)
        ax.set_xticklabels(REGIONS, fontsize=10)
        ax.set_xlim(-0.62, 2.92)
        ax.set_ylim(0, 120)
        ax.set_yticks([0, 20, 40, 60, 80, 100])
        ax.set_ylabel("得分")
        ax.set_title(f"{name}（PCS {ramp:.1f} MW/s，K3 {k3:.1f}%）", fontsize=10)
        if legend_handles is None:
            legend_handles = [b1[0], b2[0], b3[0], b4[0]]

    fig.legend(legend_handles, ["K1 分", "K2 分", "K3 分", "综合分"],
               loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.02), frameon=False,
               fontsize=9)
    fig.suptitle("同一台设备换一套细则，分数就变  [Pn=100 MW，教学示例]", fontsize=12, y=1.02)
    fig.text(0.5, -0.10,
             "综合分 = 0.30×K1 + 0.20×K2 + 0.50×K3（分项先保留 1 位小数再求和）",
             ha="center", fontsize=8.5, color=C_GRID)

    flat = [v for rows in scores for r in rows for v in r]
    manifest("ch05_same_device", flat + PASS_LINE + [1.8, 1.0, 0.5, 1.5])
    save(fig, "ch05_same_device")


def main():
    print("[ch05]")
    fig_region_params()
    fig_same_device()


if __name__ == "__main__":
    main()