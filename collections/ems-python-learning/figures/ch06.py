# @AI_GENERATED
"""第 06 章配图：PWM 与滤波、真实 PCS 能力边界、电压穿越示意。

能力边界由 lab/ems_lab/pcs.py 计算；PCS 参数和穿越曲线均为 [教学示例]。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.pcs import PcsRating, apply_pcs_limits, available_apparent_kva, pq_boundary

RATING = PcsRating(s_rated_kva=1000, u_rated_v=690, p_discharge_max_kw=1000, p_charge_max_kw=750)


def manifest(name: str, numbers: list[float]) -> None:
    """为正文图中标注对照表输出数字清单。"""
    payload = {
        "_comment": "@AI_GENERATED",
        "figure": f"{name}.png",
        "numbers": sorted(set(float(n) for n in numbers)),
        "_comment_end": "@AI_GENERATED: end",
    }
    (IMG_DIR / f"{name}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def fig_pwm():
    f_grid, f_carrier, m = 50.0, 1000.0, 0.8  # 载波频率为了看清画得很低，真实 PCS 高得多
    n_per = 4000
    t = np.linspace(0, 0.02, n_per, endpoint=False)
    ref = m * np.sin(2 * np.pi * f_grid * t)
    # 三角载波：-1~+1
    phase = (t * f_carrier) % 1.0
    carrier = 4 * np.abs(phase - 0.5) - 1
    pulse = np.where(ref >= carrier, 1.0, -1.0)
    # 滤波：对一个载波周期做滑动平均（周期延拓避免边缘效应），得到的就是“平均电压”
    win = int(n_per * f_grid / f_carrier)
    ext = np.concatenate([pulse, pulse, pulse])
    kernel = np.ones(win) / win
    # 两级滑动平均（对称核、无相移），近似 LC 滤波器的效果，残留少量高频纹波
    filt = np.convolve(np.convolve(ext, kernel, mode="same"), kernel, mode="same")[n_per : 2 * n_per]

    ms = t * 1000
    fig, axes = plt.subplots(3, 1, figsize=(8.5, 6.8), sharex=True)
    axes[0].plot(ms, carrier, color=C_GRID, lw=0.8, label="三角载波（决定开关节奏）")
    axes[0].plot(ms, ref, color=C_DIS, lw=2, label="目标正弦（控制器给出）")
    axes[0].set_title("① 比较：目标正弦高于载波时开关接‘+’，低于载波时接‘−’（m=0.8）", loc="left")
    axes[0].legend(loc="upper right", ncol=2, fontsize=8.5)
    axes[0].set_ylim(-1.25, 1.6)

    axes[1].fill_between(ms, 0, pulse, step="mid", color=C_CHG, alpha=0.55)
    axes[1].set_title("② 开关输出：只有 +U_dc/2 和 −U_dc/2 两种电平，靠“通断时间长短”编码", loc="left")
    axes[1].set_ylim(-1.3, 1.3)
    axes[1].set_yticks([-1, 0, 1])
    axes[1].set_yticklabels(["−U_dc/2", "0", "+U_dc/2"])

    axes[2].plot(ms, filt, color=C_OK, lw=2.2, label="滤波后的输出电压")
    axes[2].plot(ms, ref, color=C_DIS, lw=1.2, ls="--", label="目标正弦")
    axes[2].set_title("③ 滤波：电感/电容把高频脉冲‘抹平’，剩下 50 Hz 正弦（m=0.8；实际还会残留少量高频纹波，即谐波）", loc="left", fontsize=9.5)
    axes[2].legend(loc="upper right", ncol=2, fontsize=8.5)
    axes[2].set_ylim(-1.25, 1.6)
    axes[2].set_xlabel("时间 (ms)，一个 50 Hz 周期")
    for ax in axes:
        ax.set_xlim(0, 20)
    fig.suptitle("PWM 逆变原理示意：用高速通断的方波“拼”出正弦  [教学示意，载波频率刻意画低]", y=1.01)
    save(fig, "ch06_pwm")
    manifest("ch06_pwm", [0.8, 50, 1000])


def fig_pq_capability():
    fig, ax = plt.subplots(figsize=(7.6, 6.8))
    cases = [
        (1000, None, "理想圆：1000 kVA（铭牌）", C_GRID, "--", 1.6),
        (available_apparent_kva(RATING, 621, 25), 750, "电压 0.9 pu：900 kVA，充电上限 750 kW", C_ACC, "-", 2.0),
        (available_apparent_kva(RATING, 621, 50), 750, "0.9 pu 且 50 °C 降额：810 kVA", C_LIMIT, "-", 2.4),
    ]
    for s, p_chg, label, color, ls, lw in cases:
        ps, qs = pq_boundary(s, p_charge_max_kw=p_chg, p_discharge_max_kw=1000)
        ax.plot(ps, qs, color=color, ls=ls, lw=lw, label=label)
    ps, qs = pq_boundary(810, 750, 1000)
    ax.fill(ps, qs, color=C_LIMIT, alpha=0.08)

    # 6.5 手算：EMS 请求 (800, 300)，PCS 按 P 优先 / Q 优先修正
    req = (800, 300)
    rp = apply_pcs_limits(*req, RATING, 621, 50, priority="P")
    rq = apply_pcs_limits(*req, RATING, 621, 50, priority="Q")
    ax.plot(*req, "x", color="k", ms=10, mew=2.5)
    box = dict(fc="white", ec="none", alpha=0.85)
    ax.annotate("EMS 请求\nP=800, Q=300", xy=req, xytext=(1000, 640), ha="center", bbox=box,
                arrowprops=dict(arrowstyle="->"))
    ax.plot(rp.p_kw, rp.q_kvar, "o", color=C_DIS, ms=8)
    ax.annotate(f"P 优先：\nQ 压到 {rp.q_kvar:.0f}", xy=(rp.p_kw, rp.q_kvar), xytext=(1030, -250),
                ha="center", color=C_DIS, bbox=box, arrowprops=dict(arrowstyle="->", color=C_DIS))
    ax.plot(rq.p_kw, rq.q_kvar, "s", color=C_PURPLE, ms=7)
    ax.annotate(f"Q 优先：P 压到 {rq.p_kw:.0f}", xy=(rq.p_kw, rq.q_kvar), xytext=(420, 420),
                ha="center", color=C_PURPLE, arrowprops=dict(arrowstyle="->", color=C_PURPLE))
    ax.annotate("充电侧被 750 kW\n上限“削平”", xy=(-750, 150), xytext=(-1080, 520),
                arrowprops=dict(arrowstyle="->"))

    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(0, color="k", lw=0.8)
    ax.text(950, -1000, "放电 (P>0)", color=C_DIS, ha="center")
    ax.text(-950, -1000, "充电 (P<0)", color=C_CHG, ha="center")
    ax.text(-1140, 960, "发出无功 (Q>0)", color=C_PURPLE)
    ax.text(-1140, -820, "吸收无功 (Q<0)", color=C_PURPLE)
    ax.set_xlim(-1180, 1180)
    ax.set_ylim(-1080, 1080)
    ax.set_aspect("equal")
    ax.set_xlabel("有功 P (kW)")
    ax.set_ylabel("无功 Q (kvar)")
    ax.set_title("真实 PCS 能力边界会随电压、温度缩小，而且充放电不对称\n1000 kVA / 690 V PCS  [教学示例参数，现场以厂商能力曲线为准]")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.30), ncol=1, fontsize=9)
    save(fig, "ch06_pq_capability")
    manifest("ch06_pq_capability", [127, 300, 690, 750, 752, 800, 810, 900, 1000])


def fig_ride_through():
    t = np.linspace(-0.5, 3.0, 3501)
    # [教学示例] 低电压穿越边界：0.2 pu 保持 0.625 s，随后线性回升到 2 s 时 0.9 pu
    lvrt = np.where(t < 0, np.nan, np.where(t < 0.625, 0.2, np.where(t < 2.0, 0.2 + 0.7 * (t - 0.625) / 1.375, 0.9)))
    hvrt = np.where(t < 0, np.nan, 1.2)
    # 一次故障：电压跌到 0.35 pu，0.5 s 后故障切除，电压恢复
    u = np.where(t < 0, 1.0, np.where(t < 0.5, 0.35, np.minimum(1.0, 0.35 + (t - 0.5) * 6.0)))

    # PCS 自主响应（示意）：穿越期间限有功、发无功电流支撑电压；恢复后有功按一定速率爬回
    p_set = 0.8
    in_fault = (t >= 0) & (t < 0.5)
    recover_rate = 0.8  # pu/s [教学示例]，实际恢复速率以标准和并网要求为准
    t_rec = 0.55
    p = np.where(t < 0, p_set, np.where(in_fault, 0.15, np.minimum(p_set, 0.15 + np.clip(t - t_rec, 0, None) * recover_rate)))
    p = np.where((t >= 0.5) & (t < t_rec), 0.15, p)
    q = np.where(in_fault, 0.6, 0.0)

    fig, axes = plt.subplots(2, 1, figsize=(9, 7.2), sharex=True, gridspec_kw={"height_ratios": [1.3, 1]})
    ax = axes[0]
    ax.fill_between(t, 0, lvrt, color=C_LIMIT, alpha=0.12)
    ax.plot(t, lvrt, color=C_LIMIT, lw=2, label="低电压穿越边界（示意）")
    ax.plot(t, hvrt, color=C_PURPLE, lw=1.6, ls="--", label="高电压穿越边界（示意）")
    ax.plot(t, u, color=C_CHG, lw=2.4, label="并网点电压（一次故障）")
    ax.text(-0.45, 1.40, "边界参数：LVRT 0.2 pu、0.625 s、2 s；HVRT 1.2 pu", fontsize=8)
    ax.text(1.55, 0.18, "电压落在曲线下方：允许脱网", color=C_LIMIT, fontsize=9)
    ax.text(1.0, 1.06, "两条边界之间：必须保持并网，不得脱网", fontsize=9.5)
    ax.annotate("故障：电压\n跌到 0.35 pu", xy=(0.25, 0.35), xytext=(-0.45, 0.55), arrowprops=dict(arrowstyle="->"))
    ax.annotate("故障切除，电压恢复", xy=(0.562, 0.72), xytext=(0.75, 0.70), va="center",
                arrowprops=dict(arrowstyle="->"))
    ax.set_ylabel("电压 (pu)")
    ax.set_ylim(0, 1.5)
    ax.set_title("低/高电压穿越示意：电网故障时 PCS 要“扛住”而不是跳机  [教学示例曲线，以 GB/T 36547 及并网要求为准]",
                 loc="left", fontsize=10)
    ax.legend(loc="upper center", fontsize=8.5, ncol=3)

    ax = axes[1]
    ax.axvspan(0, t_rec, color=C_ACC, alpha=0.18)
    ax.text(0.02, 1.08, "穿越期间：PCS 自主控制\nEMS 不改指令、不重发、不判故障", fontsize=8.8, va="top")
    ax.text(0.02, 0.96, "故障 0.35 pu / 0.5 s；穿越 P=0.15 pu、Q=0.6 pu；恢复速率 0.8 pu/s", fontsize=7.7, va="top")
    ax.plot(t, np.full_like(t, p_set), color=C_GRID, lw=1.2, ls=":", label="EMS 有功设定值（保持不变）")
    ax.plot(t, p, color=C_DIS, lw=2.3, label="PCS 实际有功 P")
    ax.plot(t, q, color=C_PURPLE, lw=2.3, label="PCS 实际无功 Q（向电网发出）")
    ax.annotate("穿越结束后有功\n按规定速率恢复", xy=(1.1, 0.15 + (1.1 - t_rec) * recover_rate), xytext=(1.6, 0.3),
                arrowprops=dict(arrowstyle="->"))
    ax.set_ylabel("功率 (pu)")
    ax.set_xlabel("时间 (s)，t=0 电网发生故障")
    ax.set_ylim(-0.05, 1.12)
    ax.legend(loc="lower right", fontsize=8.5)
    save(fig, "ch06_ride_through")
    manifest("ch06_ride_through", [0.15, 0.2, 0.35, 0.5, 0.6, 0.625, 0.8, 1.2, 2.0])


def main():
    fig_pwm()
    fig_pq_capability()
    fig_ride_through()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
