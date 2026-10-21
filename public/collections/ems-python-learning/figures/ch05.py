# @AI_GENERATED
"""第 05 章配图：安时积分误差与校准、SOC 分区与滞回、能力瓶颈、SOP 与持续时间。

曲线全部调用 lab/ems_lab/battery.py 的实现生成，参数均为 [教学示例]。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.battery import (
    CoulombCounter,
    SocPermissionGate,
    SocZones,
    ac_limits_from_dc,
    actual_capacity_kwh,
    combine_capability,
    dischargeable_energy_kwh,
    ocv_from_soc,
    soc_from_ocv,
    soc_window_limits_kw,
    sop_for_duration,
)

CAP_AH = 314.0
I_025C = 0.25 * CAP_AH   # 78.5 A
BIAS_A = 0.5             # 电流传感器零点偏差 [教学示例]
DV_OCV = 0.005           # 电压测量误差 5 mV [教学示例]


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


def _profile():
    """72 小时电流曲线：(持续小时, 电流 A，放电为正, 结束时的事件)。"""
    return [
        (1.6, -I_025C, None), (15.4, 0.0, None),            # 第 1 天：充到 90%，静置
        (3.4, I_025C, None), (1.6, 0.0, "ocv_steep"),       # 放到 5%，静置后在陡峭区做 OCV 校准
        (2.0, 0.0, None),
        (2.0, -I_025C, None), (7.0, 0.0, None),             # 第 2 天：浅充浅放，一直在平台区
        (1.0, I_025C, None), (4.0, 0.0, None),
        (0.8, -I_025C, None), (5.2, 0.0, "ocv_flat"),       # 在 50% 静置：平台区，放弃校准
        (2.0, 0.0, None),
        (2.0, -I_025C, "full"),                              # 第 3 天：满充，触发满充校准
        (14.0, 0.0, None), (3.0, I_025C, None), (7.0, 0.0, None),
    ]


def fig_ah_drift():
    dt = 60.0
    truth = CoulombCounter(CAP_AH, 0.50)
    est = CoulombCounter(CAP_AH, 0.50)
    t, s_true, s_est = [0.0], [truth.soc], [est.soc]
    events = []
    now = 0.0
    for hours, current, event in _profile():
        for _ in range(int(round(hours * 3600 / dt))):
            truth.update(current, dt)
            est.update(current + BIAS_A, dt)
            now += dt / 3600
            t.append(now)
            s_true.append(truth.soc)
            s_est.append(est.soc)
        if event == "ocv_steep":
            measured = soc_from_ocv(ocv_from_soc(truth.soc) + DV_OCV)
            events.append((now, "OCV 校准\n（低 SOC 陡峭区）", est.soc - truth.soc, measured - truth.soc))
            est.calibrate(measured)
        elif event == "ocv_flat":
            would_be = soc_from_ocv(ocv_from_soc(truth.soc) + DV_OCV)
            events.append((now, "平台区静置：放弃校准", est.soc - truth.soc, None))
            flat_marker = (now, (would_be - truth.soc) * 100)
        elif event == "full":
            events.append((now, "满充校准\n（到达充电截止）", est.soc - truth.soc, 0.0))
            est.calibrate(truth.soc)
        s_est[-1] = est.soc
    t = np.array(t)
    s_true, s_est = np.array(s_true) * 100, np.array(s_est) * 100
    err = s_est - s_true

    fig, axes = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True, gridspec_kw={"height_ratios": [1.5, 1.2]})
    ax = axes[0]
    ax.plot(t, s_true, color="k", lw=1.8, label="真实 SOC")
    ax.plot(t, s_est, color=C_DIS, lw=1.8, ls="--", label=f"安时积分估计（电流零偏 +{BIAS_A} A）")
    ax.set_ylabel("SOC (%)")
    ax.set_ylim(-5, 112)
    ax.legend(loc="upper center", ncol=2, fontsize=8.5)
    ax.set_title("安时积分：误差随时间累积，只有校准能把它拉回来 [教学示例：314 Ah 簇，0.25C 充放]", fontsize=10)

    ax = axes[1]
    ax.plot(t, err, color=C_DIS, lw=2, label="估计误差 = 估计 − 真实")
    ax.axhline(0, color=C_GRID, lw=1)
    offsets = {0: (-19, -5.6), 1: (-14, 2.2), 2: (3, 2.6)}
    for k, (te, label, before, after) in enumerate(events):
        ax.axvline(te, color=C_GRID, ls=":", lw=1)
        dx, y_txt = offsets[k]
        ax.annotate(label, xy=(te, before * 100), xytext=(te + dx, y_txt), fontsize=8.5,
                    arrowprops=dict(arrowstyle="->", color=C_GRID))
    ax.plot(*flat_marker, "x", color=C_LIMIT, ms=9, mew=2, label="若在平台区强行校准（±5 mV）")
    ax.set_xlabel("时间 (h)")
    ax.set_ylabel("SOC 误差 (%)")
    ax.set_ylim(-6.5, 6.5)
    ax.set_xticks(range(0, 73, 12))
    ax.legend(loc="lower right", fontsize=8.5)
    save(fig, "ch05_ah_drift")
    manifest("ch05_ah_drift", [0.25, 0.5, 314])


def fig_soc_zones():
    z = SocZones()
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.0), gridspec_kw={"width_ratios": [0.9, 1.6]})
    ax = axes[0]
    bands = [
        (0, z.hard_min, C_LIMIT, 0.55, "硬保护区：BMS 可能已动作"),
        (z.hard_min, z.op_min, C_LIMIT, 0.25, "禁放区：EMS 停止放电"),
        (z.op_min, z.warn_min, C_ACC, 0.45, "预警区：告警 + 放电降额"),
        (z.warn_min, z.target_low, C_OK, 0.15, "正常运行"),
        (z.target_low, z.target_high, C_OK, 0.45, "目标区间（备用 / 自恢复目标）"),
        (z.target_high, z.warn_max, C_OK, 0.15, "正常运行"),
        (z.warn_max, z.op_max, C_ACC, 0.45, "预警区：告警 + 充电降额"),
        (z.op_max, z.hard_max, C_CHG, 0.30, "禁充区：EMS 停止充电"),
        (z.hard_max, 1.0, C_LIMIT, 0.55, "硬保护区：BMS 可能已动作"),
    ]
    for lo, hi, color, alpha, text in bands:
        ax.bar(0, (hi - lo) * 100, bottom=lo * 100, width=0.5, color=color, alpha=alpha, edgecolor="white")
        ax.text(0.33, (lo + hi) / 2 * 100, text, va="center", fontsize=8.5)
    for v in [z.hard_min, z.op_min, z.warn_min, z.target_low, z.target_high, z.warn_max, z.op_max, z.hard_max]:
        ax.text(-0.3, v * 100, f"{v*100:.0f}%", ha="right", va="center", fontsize=8.5)
    ax.set_xlim(-0.55, 2.3)
    ax.set_ylim(0, 100)
    ax.set_xticks([])
    ax.set_ylabel("SOC (%)")
    ax.grid(False)
    ax.set_title("SOC 分区 [教学示例]", fontsize=10)

    # 右图：SOC 在运行下限附近来回波动时，有无滞回的差别
    t = np.linspace(0, 60, 601)
    soc = np.where(t < 20, 0.20 - 0.105 * t / 20, 0.095)
    wobble = 0.012 * np.sin(2 * np.pi * (t - 20) / 8) * (t >= 20) * (t < 44)
    soc = soc + wobble + np.where(t >= 44, 0.07 * (t - 44) / 16, 0)
    gate = SocPermissionGate(z, band=0.02)
    with_gate = [soc_window_limits_kw(s, z, 2500, 2500, gate)[1] for s in soc]
    no_gate = [soc_window_limits_kw(s, z, 2500, 2500)[1] for s in soc]
    ax = axes[1]
    ax.plot(t, soc * 100, color="k", lw=1.8, label="SOC")
    ax.axhline(z.op_min * 100, color=C_LIMIT, ls="--", lw=1)
    ax.axhline((z.op_min + 0.02) * 100, color=C_OK, ls="--", lw=1)
    ax.text(0.5, z.op_min * 100 - 0.9, "运行下限 10%：禁放", color=C_LIMIT, fontsize=8.5)
    ax.text(0.5, (z.op_min + 0.02) * 100 + 0.3, "恢复阈值 12%", color=C_OK, fontsize=8.5)
    ax.set_ylabel("SOC (%)")
    ax.set_xlabel("时间 (min)")
    ax.set_ylim(6, 22)
    ax2 = ax.twinx()
    ax2.plot(t, no_gate, color=C_GRID, lw=1.5, label="只按比例降额：反复小功率启停")
    ax2.plot(t, with_gate, color=C_DIS, lw=2.2, label="比例降额 + 滞回：稳定禁放")
    ax2.set_ylabel("EMS SOC 窗口给出的可放功率 (kW)")
    ax2.set_ylim(-50, 2600)
    ax2.grid(False)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.52, 0.99), fontsize=8.5)
    ax.set_title("运行下限附近：滞回防止启停抖动", fontsize=10)
    save(fig, "ch05_soc_zones")
    manifest("ch05_soc_zones", [3, 10, 12, 15, 45, 55, 85, 90, 97])


def fig_bottleneck():
    chg_bms, dis_bms = ac_limits_from_dc(1470, 2500, 0.98)
    charge = {"BMS（折算到交流侧）": chg_bms, "PCS": 2500, "EMS SOC 窗口": 2500, "并网点需量": 4000 - 2000 - 50}
    discharge = {"BMS（折算到交流侧）": dis_bms, "PCS": 2500, "EMS SOC 窗口": 2500, "并网点防倒送": 2000 + 50 - 0}
    cap = combine_capability(charge, discharge)
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 3.9))
    for ax, limits, value, by, color, title in [
        (axes[0], discharge, cap.available_discharge_kw, cap.discharge_limited_by, C_DIS, "可放"),
        (axes[1], charge, cap.available_charge_kw, cap.charge_limited_by, C_CHG, "可充"),
    ]:
        names = list(limits)
        vals = [limits[n] for n in names]
        y = np.arange(len(names))[::-1]
        colors = [C_LIMIT if n == by else color for n in names]
        ax.barh(y, vals, color=colors, alpha=0.85, height=0.55)
        for yi, v, n in zip(y, vals, names):
            ax.text(v + 40 if v < 2350 else 2540, yi, f"{v:.0f}" + ("  ← 瓶颈" if n == by else ""), va="center", fontsize=9,
                    color=C_LIMIT if n == by else "k")
        ax.axvline(2500, color=C_GRID, ls="--", lw=1)
        ax.text(2500, len(names) - 0.45, "额定 2500", ha="center", fontsize=8.5, color=C_GRID)
        ax.set_yticks(y, names)
        ax.set_xlim(0, 3300)
        ax.set_ylim(-0.6, len(names) - 0.2)
        ax.set_xlabel("功率幅值 (kW，交流侧)")
        ax.set_title(f"{title} = {value:.0f} kW，瓶颈是 {by}", fontsize=10)
    fig.suptitle("能力取最小值：谁最小谁是瓶颈，并把原因一起上报 [教学示例]", fontsize=11)
    save(fig, "ch05_bottleneck")
    manifest("ch05_bottleneck", [1500, 1950, 2050, 2450, 2500])


def fig_sop_duration():
    cap = actual_capacity_kwh(5016, 0.92)
    eta = 0.95 * 0.98
    d_min = np.linspace(1, 240, 480)
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    for soc, color in [(0.50, C_OK), (0.20, C_DIS)]:
        e = dischargeable_energy_kwh(soc, cap, 0.05, eta)
        p = [sop_for_duration(2450, e, m * 60) for m in d_min]
        ax.plot(d_min, p, color=color, lw=2.3, label=f"SOC {soc*100:.0f}%（可放 {e:.0f} kWh）")
    e20 = dischargeable_energy_kwh(0.20, cap, 0.05, eta)
    p30 = sop_for_duration(2450, e20, 1800)
    ax.plot(30, p30, "o", color=C_LIMIT, ms=7)
    ax.annotate(f"要持续 30 min，只能承诺 {p30:.0f} kW", xy=(30, p30), xytext=(45, 1700),
                arrowprops=dict(arrowstyle="->"), fontsize=9)
    ax.axhline(2450, color=C_GRID, ls="--", lw=1)
    ax.text(238, 2500, "瞬时能力 2450 kW（BMS/PCS 等取最小）", ha="right", fontsize=8.5, color=C_GRID)
    ax.set_xlabel("要求持续时间 (min)")
    ax.set_ylabel("可承诺的放电功率 (kW)")
    ax.set_ylim(0, 2750)
    ax.set_title("SOP 与持续时间相关：P = min(瞬时能力, 可放电量 / 时长) [教学示例]", fontsize=10)
    ax.legend(loc="upper right", bbox_to_anchor=(1, 0.88))
    save(fig, "ch05_sop_duration")
    manifest("ch05_sop_duration", [20, 30, 50, 644, 1289, 1933, 2450])


def main():
    fig_ah_drift()
    fig_soc_zones()
    fig_bottleneck()
    fig_sop_duration()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
