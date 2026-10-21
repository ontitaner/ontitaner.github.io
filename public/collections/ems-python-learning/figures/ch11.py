# @AI_GENERATED
"""第 11 章配图：每张图对应正文一个示例，只画正确行为，正文引用的数字都在图上标注。

所有数值都直接调用 lab/ems_lab/control.py 中的实现算出；每张图同时输出 img/<名称>.json
标注清单，供 check_figure_numbers.py 与正文“图中标注对照表”比对。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.control import (
    Hysteresis,
    LowPassFilter,
    PIController,
    RateLimiter,
    clamp_power,
    deadband_cut,
    deadband_shift,
    interp_table,
    limit_then_ramp,
)

BOX = dict(boxstyle="round,pad=0.25", fc="white", ec="#cccccc")
ARROW = dict(arrowstyle="->", color="black", lw=0.8)


def _save_manifest(name, numbers):
    """输出图中标注的数值清单（与正文“图中标注对照表”的“标注”列一一对应）。"""
    path = IMG_DIR / f"{name}.json"
    path.write_text(json.dumps({"figure": f"{name}.png", "numbers": sorted(set(float(x) for x in numbers))},
                               ensure_ascii=False, indent=2), encoding="utf-8")


def _note(ax, text, xy, xytext, **kw):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=kw.pop("fontsize", 9.5), arrowprops=ARROW, bbox=BOX, **kw)


# ================================================================ 11.1 clamp
def fig_clamp():
    """可放 800 kW、可充 500 kW 时，三个请求各被压到多少？"""
    x = np.linspace(-1200, 1200, 481)
    y = [clamp_power(v, available_charge_kw=500, available_discharge_kw=800) for v in x]
    outs = {req: clamp_power(req, 500, 800) for req in (1000, -700, 300)}
    assert outs == {1000: 800, -700: -500, 300: 300}

    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    ax.plot(x, x, color=C_GRID, ls=":", lw=1.2, label="请求 = 输出（未限幅时）")
    ax.plot(x, y, color=C_DIS, lw=2.6, label="clamp 后的输出")
    ax.axhline(800, color=C_LIMIT, ls="--", lw=1.2)
    ax.axhline(-500, color=C_LIMIT, ls="--", lw=1.2)
    ax.axhline(0, color="black", lw=0.6)
    ax.axvline(0, color="black", lw=0.6)
    ax.text(-1180, 840, "④ 上限 +800 kW（= 可放能力）", color=C_LIMIT, fontsize=9.5)
    ax.text(-1180, -470, "⑤ 下限 −500 kW（= −可充能力）", color=C_LIMIT, fontsize=9.5)
    for req, color in [(1000, C_DIS), (-700, C_CHG), (300, C_OK)]:
        ax.plot(req, outs[req], "o", color=color, ms=9, zorder=5)
    _note(ax, "① 请求 +1000 → 输出 +800\n   截掉 200 kW", (1000, 800), (720, 330))
    _note(ax, "② 请求 −700 → 输出 −500\n   截掉 200 kW", (-700, -500), (-650, -930))
    _note(ax, "③ 请求 +300 → 输出 +300（不变）", (300, 300), (-350, 560))
    ax.set_xlabel("策略请求功率 (kW)，放电为正")
    ax.set_ylabel("限幅后输出功率 (kW)")
    ax.set_title("可放 800 kW、可充 500 kW 时，请求被压到允许区间 [−500, +800]", fontsize=10.5)
    ax.set_xlim(-1250, 1250)
    ax.set_ylim(-1100, 1100)
    ax.legend(loc="lower right", fontsize=9)
    save(fig, "ch11_clamp")
    _save_manifest("ch11_clamp", [1000, 800, 200, -700, -500, 300])


# ================================================================ 11.2 死区
DB_WIDTH = 0.03
DB_K = 1000.0  # 下垂系数 kW/Hz
DB_POINTS = [0.02, -0.04, -0.10, 0.05]  # 频率偏差 Δf（Hz）


def fig_deadband():
    """同一组频率偏差，两种死区算出的一次调频功率各是多少？"""
    x = np.linspace(-0.12, 0.12, 2401)
    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.8), sharey=True)
    offsets = {0.02: (0.035, 45), -0.04: (-0.118, 15), -0.10: (-0.118, 128), 0.05: (0.02, -112)}
    nums = [DB_WIDTH]
    for ax, fn, title in [(axes[0], deadband_cut, "截断型：死区外按原偏差计算"),
                          (axes[1], deadband_shift, "连续型：死区外先减去死区宽度")]:
        p = np.array([-DB_K * fn(v, DB_WIDTH) for v in x])
        jump = np.where(np.abs(np.diff(p)) > 5)[0]
        p_plot = p.copy()
        p_plot[jump] = np.nan
        ax.axvspan(-DB_WIDTH, DB_WIDTH, color=C_ACC, alpha=0.2, label="死区 ±0.03 Hz")
        ax.plot(x, p_plot, color=C_PURPLE, lw=2.4, label="一次调频功率 ΔP")
        ax.axhline(0, color="black", lw=0.6)
        for i, d in enumerate(DB_POINTS):
            dp = -DB_K * fn(d, DB_WIDTH)
            dp = 0.0 if abs(dp) < 1e-9 else round(dp, 6)
            ax.plot(d, dp, "o", color=C_DIS, ms=8, zorder=5)
            p_txt = "0 kW" if dp == 0 else f"{dp:+.0f} kW"
            _note(ax, f"{'①②③④'[i]} Δf {d:+.2f} Hz → {p_txt}", (d, dp), offsets[d], fontsize=9)
            nums += [d, dp]
        ax.set_title(title, fontsize=10.5)
        ax.set_xlabel("频率偏差 Δf = f − 50 (Hz)")
        ax.set_xlim(-0.125, 0.125)
        ax.set_ylim(-140, 160)
        ax.legend(loc="lower left", fontsize=9)
    axes[0].set_ylabel("一次调频功率 ΔP (kW)，放电为正")
    fig.suptitle("死区 0.03 Hz、下垂系数 1000 kW/Hz：两种死区对同一偏差的输出", fontsize=11)
    save(fig, "ch11_deadband")
    _save_manifest("ch11_deadband", nums)


# ================================================================ 11.3 滞回
HY_SOC = [18, 16, 14.8, 16.5, 19, 23, 25.3, 24, 20]


def fig_hysteresis():
    """SOC 在 15%～25% 附近变化时，低 SOC 自充开关怎么动作？"""
    h = Hysteresis(on_below=15, off_above=25)
    state = [h.update(v) for v in HY_SOC]
    assert state == [False, False, True, True, True, True, False, False, False]
    k = np.arange(len(HY_SOC))
    fig, axes = plt.subplots(2, 1, figsize=(9.4, 5.6), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
    ax = axes[0]
    ax.axhspan(15, 25, color=C_ACC, alpha=0.15, label="保持区（两阈值之间）")
    ax.axhline(15, color=C_OK, ls="--", lw=1.4, label="开启阈值 15%")
    ax.axhline(25, color=C_LIMIT, ls="--", lw=1.4, label="关闭阈值 25%")
    ax.plot(k, HY_SOC, "-o", color=C_CHG, lw=2, ms=6, label="SOC")
    _note(ax, "① 14.8% 低于 15% → 开启自充", (2, 14.8), (2.3, 11.2))
    _note(ax, "② 16.5%～23% 在保持区 → 保持开启", (3, 16.5), (0.2, 21.5))
    _note(ax, "③ 25.3% 高于 25% → 停止自充", (6, 25.3), (4.6, 29.5))
    _note(ax, "④ 24%、20% 在保持区 → 保持停止", (8, 20), (5.6, 13.0))
    ax.set_ylabel("SOC (%)")
    ax.set_ylim(9, 32)
    ax.legend(loc="upper left", fontsize=8.5, ncol=2)
    ax = axes[1]
    ax.step(k, [1 if s else 0 for s in state], where="post", color=C_DIS, lw=2.2)
    ax.set_yticks([0, 1], ["停止", "自充"])
    ax.set_ylim(-0.3, 1.4)
    ax.set_ylabel("自充开关")
    ax.set_xticks(k, [f"{10 * i} min" for i in k])
    ax.set_xlabel("采样时刻（每 10 min 一次）")
    fig.suptitle("低 SOC 自充：低于 15% 开启，高于 25% 才停止", fontsize=11)
    save(fig, "ch11_hysteresis")
    _save_manifest("ch11_hysteresis", [14.8, 15, 16.5, 23, 25.3, 25, 24, 20])


# ================================================================ 11.4 Ramp
RAMP_EXAMPLE = {
    # 11.4 示例的已知条件，与正文“已知条件”表一致 [教学示例]
    "rate_kw_s": 200.0,
    "dt_s": 1.0,
    "p_charge_max_kw": 1000.0,
    "p0_kw": -200.0,
    "requests_kw": [600.0] * 8,
    "dis_max_kw": [1000.0, 1000.0, 1000.0, 100.0, 1000.0, 1000.0, 1000.0, 1000.0],
}


def ramp_example_trace(ex=RAMP_EXAMPLE):
    """用 lab 的真实实现（RateLimiter + limit_then_ramp）逐拍计算 11.4 示例，返回每拍下发值。"""
    r = RateLimiter(up_rate=ex["rate_kw_s"], down_rate=ex["rate_kw_s"], initial=ex["p0_kw"])
    return [limit_then_ramp(req, r, ex["dt_s"], ex["p_charge_max_kw"], cap)
            for req, cap in zip(ex["requests_kw"], ex["dis_max_kw"])]


def fig_ramp():
    """调度改设点、中途 BMS 降额时，下发功率怎么走？"""
    ex = RAMP_EXAMPLE
    out = ramp_example_trace(ex)
    assert out == [0, 200, 400, 100, 300, 500, 600, 600]  # 与正文逐拍表一致
    k = np.arange(0, 9)                                   # 第 0 拍为改设点之前
    p = [ex["p0_kw"]] + out
    req = [ex["p0_kw"]] + ex["requests_kw"]
    cap = [ex["dis_max_kw"][0]] + ex["dis_max_kw"]

    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    ax.step(k, req, where="post", color=C_GRID, ls=":", lw=1.8, label="调度请求（设点）")
    ax.step(k, p, where="post", color=C_DIS, lw=2.4, label="每拍下发值（保持到下一拍）")
    ax.plot(k, p, "o", color=C_DIS, ms=7, zorder=5)
    # 上限线画在下发值之上，第 4 拍“上限 100 kW”与下发值重合时仍可见
    ax.step(k, cap, where="post", color=C_LIMIT, ls="--", lw=1.8, label="BMS 可放上限", zorder=6)
    ax.axhline(0, color="black", lw=0.8)
    notes = [
        (0, -200, "① 第 0 拍：−200 kW（充电）", (0.15, -330)),
        (1, 0, "② 第 1 拍：0 kW\n   每拍 +200 kW", (-0.25, 150)),
        (3, 400, "③ 第 3 拍：400 kW", (1.6, 520)),
        (4, 100, "④ 第 4 拍：可放上限降到 100 kW\n   下发 100 kW，变化 −300 kW\n   （安全收缩当拍生效）", (4.25, -320)),
        (5, 300, "⑤ 第 5 拍：300 kW\n   （从 100 kW 出发）", (5.3, 120)),
        (7, 600, "⑥ 第 7 拍：600 kW（到达设点）", (5.6, 760)),
    ]
    for kk, v, text, xytext in notes:
        _note(ax, text, (kk, v), xytext)
    ax.annotate("", xy=(4, 100), xytext=(4, 400), arrowprops=dict(arrowstyle="->", color=C_LIMIT, lw=1.6))
    ax.set_xticks(k, [f"第{i}拍" for i in k])
    ax.set_xlim(-0.3, 8.6)
    ax.set_ylim(-450, 1150)
    ax.set_xlabel("控制周期（每拍 1 s）")
    ax.set_ylabel("功率 (kW)，放电为正、充电为负")
    ax.set_title("调度改设点 −200 → +600 kW，Ramp 200 kW/s；第 4 拍 BMS 降额到 100 kW", fontsize=10.5)
    ax.legend(loc="lower right", fontsize=9)
    save(fig, "ch11_ramp")
    _save_manifest("ch11_ramp", [-200, 0, 200, 400, 100, -300, 300, 600])


# ================================================================ 11.5 低通
def lowpass_example_trace():
    """τ=1 s、dt=0.2 s，频率测量在第 1 拍从 50.00 Hz 跳到 49.90 Hz，返回第 0～10 拍输出。"""
    f = LowPassFilter(1.0)
    return [f.update(50.0, 0.2)] + [f.update(49.9, 0.2) for _ in range(10)]


def fig_lowpass():
    """频率测量突变 0.1 Hz 后，τ=1 s 的低通输出每拍走到哪里？"""
    ys = lowpass_example_trace()
    k = np.arange(len(ys))
    x_in = [50.0] + [49.9] * 10
    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    ax.step(k, x_in, where="post", color=C_GRID, ls=":", lw=1.8, label="原始测量 x")
    ax.plot(k, ys, "-o", color=C_CHG, lw=2.2, ms=6, label="滤波输出 y（τ = 1 s，dt = 0.2 s）")
    marks = {1: (1.3, 49.995), 5: (5.4, 49.975), 10: (6.9, 49.945)}
    labels = {1: "① 第 1 拍：49.9833 Hz（已走 16.7%）", 5: "② 第 5 拍（t = 1 s）：49.9402 Hz（已走 59.8%）",
              10: "③ 第 10 拍（t = 2 s）：49.9162 Hz（已走 83.8%）"}
    for kk, xytext in marks.items():
        _note(ax, labels[kk], (kk, ys[kk]), xytext)
    _note(ax, "④ 输入：50.00 → 49.90 Hz", (1, 49.9), (1.6, 49.905))
    ax.set_xticks(k, [f"{i}\n{0.2 * i:.1f} s" for i in k])
    ax.set_xlabel("拍号 / 时间")
    ax.set_ylabel("频率 (Hz)")
    ax.set_ylim(49.89, 50.01)
    ax.set_title("频率测量突变 0.1 Hz：低通输出每拍只走剩余差值的 1/6", fontsize=10.5)
    ax.legend(loc="upper right", fontsize=9)
    save(fig, "ch11_lowpass")
    _save_manifest("ch11_lowpass", [49.9833, 16.7, 49.9402, 59.8, 49.9162, 83.8, 50.00, 49.90])


# ================================================================ 11.6 查表插值
INTERP_T = [-10, 0, 10, 30, 45, 55]
INTERP_R = [0.0, 0.3, 1.0, 1.0, 0.5, 0.0]
INTERP_QUERY = [5, 38, 50, 60]


def fig_interp():
    """厂家给的放电降额表：5、38、50、60 ℃ 时允许放多少？"""
    x = np.linspace(-15, 70, 400)
    y = [interp_table(v, INTERP_T, INTERP_R) for v in x]
    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    ax.plot(x, y, color=C_DIS, lw=2.3, label="插值得到的允许比例")
    ax.plot(INTERP_T, INTERP_R, "s", color="k", ms=7, label="厂家表格点")
    texts = {5: ("① 5 ℃ → 0.65 → 650 kW", (-13, 0.88)),
             38: ("② 38 ℃ → 0.733 → 733 kW", (36, 1.05)),
             50: ("③ 50 ℃ → 0.25 → 250 kW", (21, 0.30)),
             60: ("④ 60 ℃（表外）→ 0 → 0 kW", (55.5, 0.24))}
    for t in INTERP_QUERY:
        r = interp_table(t, INTERP_T, INTERP_R)
        ax.plot(t, r, "o", color=C_CHG, ms=9, zorder=5)
        _note(ax, texts[t][0], (t, r), texts[t][1])
    ax.set_xlabel("电芯温度 (℃)")
    ax.set_ylabel("允许放电功率比例")
    ax.set_ylim(-0.08, 1.18)
    ax.set_xlim(-16, 72)
    ax.set_title("放电温度降额表（额定 1000 kW）：表格点之间按直线插值，表外取端点", fontsize=10.5)
    ax.legend(loc="lower center", fontsize=9)
    save(fig, "ch11_interp")
    _save_manifest("ch11_interp", [5, 0.65, 650, 38, 0.733, 733, 50, 0.25, 250, 60, 0])


# ================================================================ 11.7 PI
def pi_example_trace(rest_kw, u_min, u_max=1000.0, kp=0.2, ki=0.4, dt=1.0):
    """防倒送闭环：P_PCC[k] = 其余功率[k] + u[k−1]，目标 P_PCC = 0。返回每拍 (P_PCC, u, 积分, 是否顶住)。"""
    pi = PIController(kp, ki, u_min, u_max, anti_windup=True)
    u, rows = 0.0, []
    for r in rest_kw:
        p_pcc = r + u
        u = pi.update(0.0 - p_pcc, dt)
        rows.append((p_pcc, u, pi.integral, pi.saturated))
    return rows


def fig_pi_converge():
    """光伏富余 300 kW、目标零倒送时，PI 怎样一拍拍把并网点拉回 0？"""
    rows = pi_example_trace([300.0] * 10, -1000.0)
    k = np.arange(len(rows))
    p_pcc = [r[0] for r in rows]
    u = [r[1] for r in rows]
    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    ax.axhline(0, color=C_GRID, ls="--", lw=1.4, label="目标：并网点 0 kW")
    ax.plot(k, p_pcc, "-o", color=C_LIMIT, lw=2.2, ms=6, label="并网点功率 P_PCC（送电为正）")
    ax.plot(k, u, "-s", color=C_CHG, lw=2.2, ms=6, label="储能指令 u（充电为负）")
    _note(ax, "① 第 0 拍：P_PCC 300 kW → u −180 kW", (0, 300), (0.6, 250))
    _note(ax, "② 第 3 拍：P_PCC 67.2 kW", (3, 67.2), (3.5, 140))
    _note(ax, "③ 第 9 拍：P_PCC 7.5 kW，u −294.8 kW\n   （趋近 −300 kW）", (9, -294.8), (5.6, -180))
    ax.set_xticks(k, [f"第{i}拍" for i in k])
    ax.set_xlabel("控制周期（每拍 1 s）")
    ax.set_ylabel("功率 (kW)")
    ax.set_ylim(-360, 360)
    ax.set_title("防倒送 PI：Kp = 0.2、Ki = 0.4 /s，光伏富余 300 kW", fontsize=10.5)
    ax.legend(loc="lower left", fontsize=9)
    save(fig, "ch11_pi_converge")
    _save_manifest("ch11_pi_converge", [0, 300, -180, 67.2, 7.5, -294.8, -300])


def fig_pi_antiwindup():
    """可充能力只有 400 kW 时，PI 顶住上限、积分冻结，云遮后怎样恢复？"""
    rows = pi_example_trace([600.0] * 5 + [100.0] * 7, -400.0)
    k = np.arange(len(rows))
    p_pcc = [r[0] for r in rows]
    u = [r[1] for r in rows]
    integ = [r[2] for r in rows]
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 6.6), sharex=True)
    ax = axes[0]
    ax.axhline(0, color=C_GRID, ls="--", lw=1.2, label="目标 0 kW")
    ax.axvspan(-0.4, 4.5, color=C_ACC, alpha=0.12, label="光伏富余 600 kW")
    ax.axvspan(4.5, 11.4, color=C_CHG, alpha=0.06, label="云遮后富余 100 kW")
    ax.plot(k, p_pcc, "-o", color=C_LIMIT, lw=2.2, ms=6, label="并网点功率 P_PCC")
    _note(ax, "① 第 4 拍：P_PCC 200 kW\n   （储能已充满能力，余量需光伏限发）", (4, 200), (5.0, 420))
    _note(ax, "② 第 5 拍：云遮，P_PCC −300 kW\n   （指令还停在上一拍）", (5, -300), (6.1, -250))
    _note(ax, "③ 第 6 拍：P_PCC −56 kW", (6, -56), (7.6, 150))
    ax.set_ylabel("P_PCC (kW)")
    ax.set_ylim(-400, 700)
    ax.legend(loc="upper right", fontsize=8.5)
    ax = axes[1]
    ax.axhline(-400, color=C_LIMIT, ls="--", lw=1.2, label="可充能力下限 −400 kW")
    ax.plot(k, u, "-s", color=C_CHG, lw=2.2, ms=6, label="储能指令 u")
    ax.plot(k, integ, ":", color=C_PURPLE, lw=1.8, label="积分项")
    _note(ax, "④ 第 2～4 拍：u 顶在 −400 kW\n   积分冻结在 −336 kW", (3, -400), (0.2, -120))
    _note(ax, "⑤ 第 6 拍：u −182.4 kW", (6, -182.4), (6.6, -330))
    _note(ax, "⑥ 第 11 拍：u −110.8 kW，P_PCC −15.8 kW\n   （趋近 −100 kW）", (11, -110.8), (7.3, -20))
    ax.set_ylabel("功率 (kW)")
    ax.set_ylim(-460, 40)
    ax.set_xticks(k, [f"{i}" for i in k])
    ax.set_xlabel("拍号（每拍 1 s）")
    ax.legend(loc="lower right", fontsize=8.5)
    fig.suptitle("可充能力 400 kW、光伏富余 600 kW → 云遮后 100 kW：带条件积分的 PI", fontsize=11)
    save(fig, "ch11_pi_antiwindup")
    _save_manifest("ch11_pi_antiwindup", [200, -300, -56, -400, -336, -182.4, -110.8, -15.8, -100])


def main():
    fig_clamp()
    fig_deadband()
    fig_hysteresis()
    fig_ramp()
    fig_lowpass()
    fig_interp()
    fig_pi_converge()
    fig_pi_antiwindup()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
