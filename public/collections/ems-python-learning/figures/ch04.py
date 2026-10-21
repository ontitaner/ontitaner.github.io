# @AI_GENERATED
"""第 04 章配图：OCV-SOC 曲线对比、温度-倍率降额、簇间木桶效应。

曲线全部调用 lab/ems_lab/battery.py 的实现和 [教学示例] 表格生成。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.battery import (
    NCM_OCV_TEACHING,
    OCV_SOC_TEACHING,
    ocv_from_soc,
    soc_from_ocv,
    stack_energy,
    temperature_c_limits,
)


def manifest(name: str, numbers: list[float]) -> None:
    (IMG_DIR / f"{name}.json").write_text(
        json.dumps({"figure": f"{name}.png", "numbers": sorted(set(float(n) for n in numbers))}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fig_ocv_curves():
    soc = np.linspace(0, 1, 401)
    lfp = [ocv_from_soc(s) for s in soc]
    ncm = [ocv_from_soc(s, OCV_SOC_TEACHING, NCM_OCV_TEACHING) for s in soc]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3), gridspec_kw={"width_ratios": [1.1, 1]})

    ax = axes[0]
    ax.plot(soc * 100, ncm, color=C_PURPLE, lw=2.3, label="三元 NCM：全程有斜率")
    ax.plot(soc * 100, lfp, color=C_OK, lw=2.3, label="磷酸铁锂 LFP：中段几乎是平的")
    ax.axvspan(30, 90, color=C_ACC, alpha=0.15)
    ax.text(60, 2.98, "LFP 平台区（约 30%～90%）", ha="center", color="#9a5b13", fontsize=9)
    ax.set_xlabel("SOC (%)")
    ax.set_ylabel("单体开路电压 OCV (V)")
    ax.set_title("OCV-SOC 曲线形状对比 [教学示例]", fontsize=10)
    ax.set_ylim(2.85, 4.3)
    ax.legend(loc="upper left")

    ax = axes[1]
    s_zoom = np.linspace(0.2, 0.95, 301)
    ax.plot(s_zoom * 100, [ocv_from_soc(s) * 1000 for s in s_zoom], color=C_OK, lw=2.3, label="LFP OCV")
    v0 = ocv_from_soc(0.45)
    lo, hi = soc_from_ocv(v0 - 0.005), soc_from_ocv(v0 + 0.005)
    ax.axhspan((v0 - 0.005) * 1000, (v0 + 0.005) * 1000, color=C_LIMIT, alpha=0.15, label="电压测量误差 ±5 mV")
    ax.axvspan(lo * 100, hi * 100, color=C_CHG, alpha=0.15, label=f"对应 SOC 范围 {lo*100:.0f}%～{hi*100:.0f}%")
    ax.plot(45, v0 * 1000, "o", color=C_LIMIT)
    ax.annotate(f"SOC≈45%，读到 {v0*1000:.0f} mV，\n可能是 {lo*100:.0f}%～{hi*100:.0f}% 中任意值",
                xy=(45, v0 * 1000), xytext=(52, 3240), arrowprops=dict(arrowstyle="->"), fontsize=9)
    ax.set_xlabel("SOC (%)")
    ax.set_ylabel("OCV (mV)")
    ax.set_title("放大 LFP：±5 mV 的误差约对应 ±5 个百分点 SOC", fontsize=10)
    ax.set_ylim(3230, 3380)
    ax.legend(loc="upper left", fontsize=8.5)
    save(fig, "ch04_ocv_curves")
    manifest("ch04_ocv_curves", [5, 30, 40, 45, 50, 90, 3295])


def fig_temp_derate():
    t = np.linspace(-30, 65, 400)
    chg = [temperature_c_limits(v)[0] for v in t]
    dis = [temperature_c_limits(v)[1] for v in t]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    ax.axvspan(-30, 0, color=C_CHG, alpha=0.08)
    ax.text(-15, 0.56, "0℃ 以下：禁止充电\n（放电仍可降额运行）", ha="center", fontsize=9, color=C_CHG)
    ax.plot(t, dis, color=C_DIS, lw=2.5, label="允许放电倍率")
    ax.plot(t, chg, color=C_CHG, lw=2.5, ls="--", label="允许充电倍率")
    c5, d5 = temperature_c_limits(5)
    ax.plot([5, 5], [c5, d5], "o", color="k", ms=6)
    ax.annotate(f"5℃：放电 {d5:.2f}C，充电只有 {c5:.1f}C", xy=(5, c5), xytext=(12, 0.06),
                arrowprops=dict(arrowstyle="->"), fontsize=9)
    ax.annotate("高温：两个方向都要降额", xy=(51, 0.27), xytext=(24, 0.3), arrowprops=dict(arrowstyle="->"),
                fontsize=9)
    ax.set_xlabel("电芯温度 (℃)")
    ax.set_ylabel("允许倍率 (C)")
    ax.set_title("温度对充放电能力的影响（本例额定 0.5C）[教学示例，以电芯规格书为准]", fontsize=10)
    ax.set_ylim(-0.02, 0.68)
    ax.legend(loc="upper right")
    save(fig, "ch04_temp_derate")
    manifest("ch04_temp_derate", [0, 5, 0.1, 0.45, 0.5])


def fig_barrel():
    socs = [0.60, 0.58, 0.55, 0.45]
    cap, soc_min, soc_max = 400, 0.05, 0.95
    e = stack_energy(socs, cap, soc_min, soc_max)
    names = [f"簇 {i + 1}" for i in range(len(socs))]
    x = np.arange(len(socs))
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True)

    ax = axes[0]
    d = min(socs) - soc_min  # 电流均分：每簇放出同样多
    for i, s in enumerate(socs):
        ax.bar(i, soc_min * 100, color=C_GRID, alpha=0.35, width=0.6)
        ax.bar(i, (s - d - soc_min) * 100, bottom=soc_min * 100, color="white", edgecolor=C_DIS,
               hatch="//", width=0.6)
        ax.bar(i, d * 100, bottom=(s - d) * 100, color=C_DIS, alpha=0.85, width=0.6)
        ax.text(i, s * 100 + 1.5, f"{s*100:.0f}%", ha="center", fontsize=9)
    ax.axhline(soc_min * 100, color=C_LIMIT, ls="--", lw=1.2, label="放电下限 5%")
    ax.annotate("最低簇先到底\n整堆停放", xy=(3, soc_min * 100 + 1), xytext=(2.35, 75),
                arrowprops=dict(arrowstyle="->"), fontsize=9)
    ax.bar(0, 0, color=C_DIS, alpha=0.85, label="实际放出")
    ax.bar(0, 0, color="white", edgecolor=C_DIS, hatch="//", label="被困住、放不出")
    ax.set_xticks(x, names)
    ax.set_ylabel("SOC (%)")
    ax.set_ylim(0, 118)
    ax.set_title(f"放电看最低簇：可放 {e.dischargeable_kwh:.0f} kWh（理想 {e.ideal_dischargeable_kwh:.0f}）",
                 fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=8.5)

    ax = axes[1]
    c = soc_max - max(socs)  # 每簇充入同样多
    for i, s in enumerate(socs):
        ax.bar(i, s * 100, color=C_GRID, alpha=0.35, width=0.6)
        ax.bar(i, c * 100, bottom=s * 100, color=C_CHG, alpha=0.85, width=0.6)
        ax.bar(i, (soc_max - s - c) * 100, bottom=(s + c) * 100, color="white", edgecolor=C_CHG,
               hatch="\\\\", width=0.6)
        ax.text(i, s * 100 - 5, f"{s*100:.0f}%", ha="center", fontsize=9)
    ax.axhline(soc_max * 100, color=C_LIMIT, ls="--", lw=1.2)
    ax.text(3.45, soc_max * 100 + 1.2, "充电上限 95%", color=C_LIMIT, fontsize=8.5, ha="right")
    ax.annotate("最高簇先到顶\n整堆停充", xy=(0.1, soc_max * 100 + 0.5), xytext=(0.55, 104),
                arrowprops=dict(arrowstyle="->"), fontsize=9)
    ax.bar(0, 0, color=C_CHG, alpha=0.85, label="实际充入")
    ax.bar(0, 0, color="white", edgecolor=C_CHG, hatch="\\\\", label="有空间、充不进")
    ax.set_xticks(x, names)
    ax.set_title(f"充电看最高簇：可充 {e.chargeable_kwh:.0f} kWh（理想 {e.ideal_chargeable_kwh:.0f}）",
                 fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=8.5)
    fig.suptitle("簇间 SOC 不一致的木桶效应（4 簇 × 400 kWh，电流均分）[教学示例]", fontsize=11)
    save(fig, "ch04_barrel")
    manifest("ch04_barrel", [4, 5, 11, 45, 55, 58, 60, 95, 150, 1800, 209, 2449, 400, 560, 640, 648, 792])


def main():
    fig_ocv_curves()
    fig_temp_derate()
    fig_barrel()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
