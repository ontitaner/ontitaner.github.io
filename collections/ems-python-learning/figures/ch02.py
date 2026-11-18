# @AI_GENERATED
"""第02章配图：功率与电量、交流有效值、三相、P/Q波形、功率三角形和P-Q能力圆。

所有数据均为 [教学示例]；每张图同时输出 JSON 数字清单，供正文图文一致性检查。
"""
from __future__ import annotations

import json

import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save

F = 50.0
W = 2 * np.pi * F


def manifest(name: str, numbers: list[float]) -> None:
    (IMG_DIR / f"{name}.json").write_text(
        json.dumps({"figure": f"{name}.png", "numbers": sorted(set(float(n) for n in numbers))}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fig_ac_waveform():
    t = np.linspace(0, 0.04, 2000)
    u = 311 * np.sin(W * t)
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.plot(t * 1000, u, color=C_CHG, lw=2, label="瞬时电压 u(t)")
    ax.axhline(311, color=C_LIMIT, ls="--", lw=1)
    ax.axhline(220, color=C_OK, ls="--", lw=1.2)
    ax.axhline(-311, color=C_LIMIT, ls="--", lw=1)
    ax.text(40.5, 311, "峰值 311 V", va="center", color=C_LIMIT)
    ax.text(40.5, 220, "有效值 220 V\n(=311/√2)", va="center", color=C_OK)
    ax.annotate("", xy=(20, -350), xytext=(0, -350), arrowprops=dict(arrowstyle="<->", color=C_GRID))
    ax.text(10, -370, "一个周期 20 ms（每秒 50 个周期 = 50 Hz）", ha="center", va="top", color=C_GRID)
    ax.set_xlim(0, 40); ax.set_ylim(-470, 380)
    ax.set_xlabel("时间 (ms)"); ax.set_ylabel("电压 (V)")
    ax.set_title("交流电压峰值、有效值与周期 [教学示例]")
    ax.legend(loc="upper right")
    save(fig, "ch02_ac_waveform")
    manifest("ch02_ac_waveform", [20, 50, 220, 311])


def fig_three_phase():
    t = np.linspace(0, 0.02, 1000)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    colors = [C_ACC, C_OK, C_DIS]
    total = np.zeros_like(t)
    for k, (name, c) in enumerate(zip("ABC", colors)):
        v = np.sin(W * t - k * 2 * np.pi / 3)
        total += v
        ax.plot(t * 1000, v, color=c, lw=2, label=f"{name} 相")
    ax.plot(t * 1000, total, color="k", lw=1.5, ls=":", label="三相之和约为 0")
    ax.set_xlabel("时间 (ms)"); ax.set_ylabel("电压（标幺）")
    ax.set_title("平衡三相：相位依次相差 120°（1/3 周期）")
    ax.legend(ncol=4, loc="upper right")
    ax.set_ylim(-1.3, 1.5)
    ax.text(1, 1.25, "A/B/C 为归一化波形，不代表实际 kV", fontsize=8.5, color=C_GRID)
    save(fig, "ch02_three_phase")
    manifest("ch02_three_phase", [0, 1, 3, 120])


def fig_pq_waveforms():
    t = np.linspace(0, 0.04, 2000)
    cases = [
        ("① 同相：电阻负载，φ=0°", 0.0),
        ("② 电流滞后 90°：纯电感", np.pi / 2),
        ("③ 电流滞后 36.87°：实际负载示例", np.deg2rad(36.87)),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(8.5, 8), sharex=True)
    for ax, (title, phi) in zip(axes, cases):
        u = np.sqrt(2) * np.sin(W * t)
        i = np.sqrt(2) * np.sin(W * t - phi)
        p = u * i
        p_avg = np.cos(phi)
        ax.plot(t * 1000, u, color=C_CHG, lw=1.3, label="电压 u（有效值=1）")
        ax.plot(t * 1000, i, color=C_ACC, lw=1.3, label="电流 i（有效值=1）")
        ax.fill_between(t * 1000, 0, p, where=p >= 0, color=C_DIS, alpha=0.35, label="p>0：能量送往负载")
        ax.fill_between(t * 1000, 0, p, where=p < 0, color=C_PURPLE, alpha=0.35, label="p<0：能量退回电源")
        ax.axhline(p_avg, color="k", ls="--", lw=1.2)
        ax.text(40.3, p_avg, f"平均 P = cosφ = {p_avg:.2f}", va="center", fontsize=9)
        ax.set_title(title, loc="left"); ax.set_ylim(-1.6, 2.2); ax.set_xlim(0, 40)
    axes[0].legend(ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.12), fontsize=8.5)
    axes[-1].set_xlabel("时间 (ms)")
    fig.suptitle("瞬时功率 p=u×i：平均值为 P，能量往返交换不等于平均消耗", y=1.04, fontsize=11.5)
    save(fig, "ch02_pq_waveforms")
    manifest("ch02_pq_waveforms", [0, 0.8, 1, 36.87, 90])


def fig_power_triangle():
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    p, q = 80, 60
    ax.add_patch(FancyArrowPatch((0, 0), (p, 0), arrowstyle="-|>", mutation_scale=18, color=C_DIS, lw=2.5))
    ax.add_patch(FancyArrowPatch((p, 0), (p, q), arrowstyle="-|>", mutation_scale=18, color=C_PURPLE, lw=2.5))
    ax.add_patch(FancyArrowPatch((0, 0), (p, q), arrowstyle="-|>", mutation_scale=18, color=C_CHG, lw=2.5))
    ax.text(40, -7, "有功 P = 80 kW\n真正做功", ha="center", va="top", color=C_DIS)
    ax.text(83, 30, "无功 Q = 60 kvar\n占用电流", va="center", color=C_PURPLE)
    ax.text(30, 36, "视在 S = 100 kVA", ha="center", rotation=36.87, color=C_CHG)
    arc = np.linspace(0, np.deg2rad(36.87), 30)
    ax.plot(18 * np.cos(arc), 18 * np.sin(arc), color="k", lw=1)
    ax.text(21, 5, "φ=36.87°", fontsize=10)
    ax.text(0, 72, "S²=P²+Q²，PF=|P|/S=0.8", fontsize=10)
    ax.set_xlim(-5, 135); ax.set_ylim(-25, 80); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("功率三角形：P=80 kW、Q=60 kvar [教学示例]")
    save(fig, "ch02_power_triangle")
    manifest("ch02_power_triangle", [0.8, 36.87, 60, 80, 100])


def fig_pq_circle():
    s = 100
    fig, ax = plt.subplots(figsize=(5.6, 5.4))
    ax.add_patch(Circle((0, 0), s, fill=True, color=C_OK, alpha=0.12))
    ax.add_patch(Circle((0, 0), s, fill=False, color=C_OK, lw=2))
    ax.axhline(0, color="k", lw=0.8); ax.axvline(0, color="k", lw=0.8)
    q_req = 60; p_max = np.sqrt(s**2 - q_req**2)
    ax.plot([-p_max, p_max], [q_req, q_req], color=C_PURPLE, lw=2)
    ax.plot([p_max], [q_req], "o", color=C_DIS, ms=8)
    ax.annotate(f"Q=60 kvar 时\nP最大={p_max:.0f} kW", xy=(p_max, q_req), xytext=(62, 105), arrowprops=dict(arrowstyle="->"))
    ax.plot([100], [0], "s", color=C_DIS, ms=7)
    ax.annotate("Q=0 时 P=100 kW", xy=(100, 0), xytext=(40, -40), arrowprops=dict(arrowstyle="->"))
    ax.text(55, -95, "放电 P>0", color=C_DIS, ha="center"); ax.text(-55, -95, "充电 P<0", color=C_CHG, ha="center")
    ax.text(-120, 88, "发出无功 Q>0", color=C_PURPLE); ax.text(-120, -75, "吸收无功 Q<0", color=C_PURPLE)
    ax.set_xlim(-125, 125); ax.set_ylim(-125, 125); ax.set_aspect("equal")
    ax.set_xlabel("有功 P (kW)"); ax.set_ylabel("无功 Q (kvar)")
    ax.set_title("100 kVA PCS 的 P-Q 能力圆（理想模型）")
    save(fig, "ch02_pq_circle")
    manifest("ch02_pq_circle", [-60, 0, 60, 80, 100])


def fig_power_energy():
    t = np.linspace(0, 4, 400)
    p = np.where(t < 1, 1000 * t, np.where(t < 3, 1000, 1000 * (4 - t)))
    fig, ax = plt.subplots(figsize=(7.5, 3.3))
    ax.plot(t, p, color=C_DIS, lw=2, label="放电功率 P(t)")
    ax.fill_between(t, 0, p, color=C_DIS, alpha=0.2, label="曲线下面积 = 电量")
    ax.text(2, 450, "电量 = 0.5 + 2 + 0.5 = 3 MWh", ha="center", fontsize=11)
    ax.set_xlabel("时间 (h)"); ax.set_ylabel("功率 (kW)")
    ax.set_title("功率与电量：电量等于功率曲线下面积 [教学示例]")
    ax.legend(loc="upper right")
    save(fig, "ch02_power_energy")
    manifest("ch02_power_energy", [0.5, 2, 3, 1000])


def main():
    fig_ac_waveform(); fig_three_phase(); fig_pq_waveforms(); fig_power_triangle(); fig_pq_circle(); fig_power_energy()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
