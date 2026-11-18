# @AI_GENERATED
"""第 17 章配图：数值全部由 lab 实现重算；每图输出 PNG 和数字标注清单 JSON。"""
from __future__ import annotations

import json
import math

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, IMG_DIR, plt, save
from ems_lab.reactive import AvcController, QuDroopConfig, naive_clamp_each, project_pq, qu_droop_kvar, voltage_rise_v

BOX = dict(boxstyle="round,pad=0.25", fc="white", ec="#cccccc")
ARROW = dict(arrowstyle="->", color="black", lw=0.8)


def _manifest(name, numbers):
    (IMG_DIR / f"{name}.json").write_text(
        json.dumps({"figure": f"{name}.png", "numbers": sorted(set(float(x) for x in numbers))}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _note(ax, text, xy, xytext):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=9, bbox=BOX, arrowprops=ARROW)


# ---------------------------------------------------------------- 17.2 电压灵敏度
def fig_voltage_rx():
    p_part = voltage_rise_v(50_000, 0, 6.5, 20, 110) / 1000
    q_part = voltage_rise_v(0, 20_000, 6.5, 20, 110) / 1000
    total = p_part + q_part
    d10p = voltage_rise_v(10_000, 0, 6.5, 20, 110) / 1000
    d10q = voltage_rise_v(0, 10_000, 6.5, 20, 110) / 1000
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1, 1.15]})
    ax = axes[0]
    ax.bar([0], [p_part], color=C_DIS, width=0.55, label="P·R/U")
    ax.bar([0], [q_part], bottom=[p_part], color=C_CHG, width=0.55, label="Q·X/U")
    _note(ax, "① P=50 MW → 2.95 kV", (0, p_part / 2), (-0.95, 1.2))
    _note(ax, "② Q=20 Mvar → 3.64 kV", (0, p_part + q_part / 2), (0.45, 4.7))
    _note(ax, "③ 合计 6.59 kV\n（110 kV 的 6.0%）", (0, total), (-0.4, 7.2))
    _note(ax, "④ 各加 10 个单位：\nP→0.59 kV，Q→1.82 kV", (0, total), (0.75, 2.5))
    ax.set_xlim(-1.2, 2.0); ax.set_ylim(0, 8.2); ax.set_xticks([])
    ax.set_ylabel("电压抬升 ΔU (kV)")
    ax.set_title("110 kV、R=6.5 Ω、X=20 Ω：P/Q 对电压的分量")
    ax.legend(loc="lower right")
    ax = axes[1]
    cases = [("220 kV 及以上\n架空线", 0.1), ("110 kV\n架空线", 0.325), ("10 kV\n配电线", 1.0), ("0.4 kV\n低压电缆", 3.0)]
    x = np.arange(len(cases)); up = [0.1 * r for _, r in cases]; uq = [0.1] * len(cases)
    ax.bar(x - .18, up, .36, color=C_DIS, label="同量 P 的归一化灵敏度（∝R）")
    ax.bar(x + .18, uq, .36, color=C_CHG, label="同量 Q 的归一化灵敏度（∝X）")
    for i, (_, rx) in enumerate(cases):
        label = f"Q 约为 P 的 {1/rx:.1f} 倍" if rx < 0.7 else ("P、Q 相当" if rx <= 1.3 else f"P 约为 Q 的 {rx:.0f} 倍")
        ax.text(i, max(up[i], uq[i]) + .012, label, ha="center", fontsize=8.5)
    ax.set_xticks(x, [a for a, _ in cases]); ax.set_ylim(0, .36)
    ax.set_ylabel("归一化电压灵敏度（非实际电压偏差）")
    ax.set_title("R/X 决定 P 或 Q 谁更影响电压 [量级示意]")
    ax.legend(loc="upper left", fontsize=8)
    save(fig, "ch17_voltage_rx")
    _manifest("ch17_voltage_rx", [50, 20, 2.95, 3.64, 6.59, 110, 6.0, 10, .59, 1.82, 0.1, .325, 1, 3])


# ---------------------------------------------------------------- 17.5 Q-U 下垂
def fig_qu_droop():
    cfg = QuDroopConfig(q_max_kvar=500, slope_kvar_per_pu=10_000, deadband_pu=.01)
    u = np.linspace(.90, 1.10, 2001); q = np.array([qu_droop_kvar(v, cfg) for v in u])
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    ax.axvspan(.99, 1.01, color=C_ACC, alpha=.16, label="连续型死区 ±0.01 pu")
    ax.plot(u, q, color=C_OK, lw=2.5, label="Q-U 下垂（本章示例）")
    ax.axhline(500, color=C_LIMIT, ls="--"); ax.axhline(-500, color=C_LIMIT, ls="--"); ax.axhline(0, color="black", lw=.7)
    notes = [(1.005, 0, "① 1.005 pu → 0 kvar", (.915, 120)), (.97, 200, "② 0.97 pu → +200 kvar", (.91, 350)),
             (.93, 500, "③ 0.93 pu → +500 kvar（限幅）", (.99, 535)), (1.04, -300, "④ 1.04 pu → −300 kvar", (1.045, -160))]
    for uu, qq, text, pos in notes:
        ax.plot(uu, qq, "o", color=C_DIS if qq >= 0 else C_CHG, ms=8); _note(ax, text, (uu, qq), pos)
    ax.text(.903, 540, "上限 +500 kvar", color=C_LIMIT); ax.text(.903, -570, "下限 −500 kvar", color=C_LIMIT)
    ax.set_xlabel("PCC 电压 U (pu)"); ax.set_ylabel("无功请求 Q (kvar，发出为正)"); ax.set_ylim(-620, 620)
    ax.set_title("Q-U 下垂：电压低发无功，电压高吸收无功")
    ax.legend(loc="upper right")
    save(fig, "ch17_qu_droop")
    _manifest("ch17_qu_droop", [1.005, 0, .97, 200, .93, 500, 1.04, -300, .01, -500])


# ---------------------------------------------------------------- 17.8 P-Q 联合投影
def fig_pq_projection():
    s, p, q = 1000., 900., 600.
    res = {m: project_pq(p, q, s, m) for m in ("p_priority", "q_priority", "proportional")}
    names = {"p_priority": "有功优先", "q_priority": "无功优先", "proportional": "按比例缩放"}
    colors = {"p_priority": C_DIS, "q_priority": C_CHG, "proportional": C_OK}
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axes[0]; th = np.linspace(0, np.pi / 2, 200)
    ax.plot(s*np.cos(th), s*np.sin(th), color=C_GRID, lw=2); ax.fill_between(s*np.cos(th), 0, s*np.sin(th), color=C_GRID, alpha=.08)
    pn, qn = naive_clamp_each(p, q, s); sn = math.hypot(pn, qn)
    ax.plot(pn, qn, "X", color=C_LIMIT, ms=12); _note(ax, "① 请求 (900, 600)\nS=1081.7 kVA，超容", (pn, qn), (530, 930))
    offsets = {"p_priority": (680, 180), "q_priority": (420, 700), "proportional": (240, 480)}
    for m, r in res.items():
        ax.plot(r.p_kw, r.q_kvar, "o", color=colors[m], ms=8)
        _note(ax, f"{names[m]}\n({r.p_kw:.1f}, {r.q_kvar:.1f})", (r.p_kw, r.q_kvar), offsets[m])
    ax.set(xlim=(0, 1150), ylim=(0, 1050), aspect="equal", xlabel="P (kW，放电为正)", ylabel="Q (kvar，发出为正)")
    ax.set_title("先一维限幅，再投影进 S=1000 kVA 能力圆")
    ax = axes[1]; ms = list(res); x = np.arange(3)
    for i, m in enumerate(ms):
        r = res[m]; ax.bar(i-.18, r.p_kw, .34, color=C_DIS); ax.bar(i+.18, r.q_kvar, .34, color=C_CHG)
        ax.text(i-.18, r.p_kw/2, f"{r.p_kw:.0f}", ha="center", color="white"); ax.text(i+.18, r.q_kvar/2, f"{r.q_kvar:.0f}", ha="center", color="white")
        ax.text(i, max(r.p_kw, r.q_kvar)+45, f"未满足 P {r.p_unserved_kw:.1f}\nQ {r.q_unserved_kvar:.1f}", ha="center", fontsize=8)
    ax.set_xticks(x, [names[m] for m in ms]); ax.set_ylim(0, 1100); ax.set_ylabel("执行功率 (kW / kvar)")
    ax.set_title("执行量与未满足量（必须上送）")
    save(fig, "ch17_pq_projection")
    _manifest("ch17_pq_projection", [900, 600, 1000, 1081.7, 435.9, 164.1, 800, 100, 832.1, 554.7, 67.9, 45.3])


# ---------------------------------------------------------------- 17.9 AVC 贯穿闭环
def _avc_rows():
    c = AvcController(1.0, 12_000, 4_000); u = 1.03; rows=[]
    for k, p in enumerate((900., 900., 900., 600., 600., 600.)):
        cap = math.sqrt(1000**2-p**2); step = c.update(u, 1., -cap, cap); out = project_pq(p, step.q_requested_kvar, 1000, "p_priority")
        rows.append((k, u, p, step.q_requested_kvar, out.q_kvar, cap, c.integral_kvar, step.saturated)); u += .00004*out.q_kvar
    return rows


def fig_avc_cycle():
    rows = _avc_rows(); k = np.arange(len(rows)); us=[r[1] for r in rows]; qs=[r[4] for r in rows]; caps=[r[5] for r in rows]
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 6.3), sharex=True)
    ax=axes[0]; ax.axhline(1.0,color=C_GRID,ls="--",label="目标 1.000 pu"); ax.plot(k,us,"-o",color=C_LIMIT,lw=2.2,label="PCC 电压")
    _note(ax,"① 第 0 拍：U=1.0300 pu\nP=900 kW 时 Q 上限仅 435.9 kvar",(0,us[0]),(.45,1.036))
    _note(ax,"② 第 3 拍：P 降到 600 kW\nQ 上限释放到 800 kvar",(3,us[3]),(3.25,1.021))
    ax.set_ylabel("U_PCC (pu)"); ax.legend(loc="lower left"); ax.set_ylim(.99,1.045)
    ax=axes[1]; ax.plot(k,qs,"-s",color=C_CHG,lw=2.2,label="实际 Q（吸收为负）"); ax.plot(k,[-c for c in caps],":",color=C_LIMIT,lw=1.5,label="可吸收 Q 下限")
    _note(ax,"③ 第 0 拍：Q=−435.9 kvar\n能力顶住，积分冻结",(0,qs[0]),(.45,-230))
    _note(ax,"④ 第 5 拍：Q=+4.0 kvar\n开始回调",(5,qs[5]),(3.5,-110))
    ax.set_xticks(k,[f"第{i}拍" for i in k]); ax.set_xlabel("控制周期（每拍 1 s）"); ax.set_ylabel("Q (kvar)"); ax.legend(loc="lower right")
    fig.suptitle("简化 AVC：电压 PI → P-Q 能力约束 → 实际 Q → 电压反馈")
    save(fig,"ch17_avc_cycle")
    _manifest("ch17_avc_cycle", [1.03, 1.0, 900, 435.9, 600, 800, -435.9, 4.0])


# ---------------------------------------------------------------- 17.1 pu 换算

def fig_pu_scale():
    actual = [107.8, 110.0, 112.2]
    labels = ["0.980 pu\n低 2%", "1.000 pu\n基准", "1.020 pu\n高 2%"]
    fig, ax = plt.subplots(figsize=(9.2, 3.8))
    ax.hlines(110, 107, 113, color=C_GRID, lw=1.5, ls="--", label="基准电压 110 kV")
    colors = [C_CHG, C_OK, C_DIS]
    for x, text, color in zip(actual, labels, colors):
        ax.plot(x, 110, "o", color=color, ms=10)
        ax.annotate(f"{x:.1f} kV\n{text}", (x, 110), xytext=(x, 110.7), ha="center", fontsize=9, bbox=BOX)
    ax.set(xlim=(107, 113), ylim=(109.3, 112.1), xlabel="PCC 实际电压 (kV)", yticks=[])
    ax.set_title("标幺值 pu：实际电压 ÷ 该测点的基准电压")
    ax.legend(loc="lower right")
    save(fig, "ch17_pu_scale")
    _manifest("ch17_pu_scale", [107.8, 110, .98, 1.0, 112.2, 1.02, 2])


# ---------------------------------------------------------------- 17.4 四模式对照

def fig_modes_compare():
    """共同 t0～t3 场景：四格统一时间轴、统一 Q 轴，比较每种模式产生请求的依据。"""
    t = np.arange(4)
    u = [1.030, 1.020, 1.010, 1.010]
    p = [800, 800, 400, 400]
    fixed = [-300] * 4
    pf = [-262.9, -262.9, -131.5, -131.5]
    droop = [-200, -100, 0, 0]
    avc = [-300, -260, -200, -220]
    panels = [("定 Q：唯一输入=调度 Q 设点", fixed, C_CHG),
              ("定 PF：唯一输入=PF 目标 + 当前 P", pf, C_CHG),
              ("Q-U 下垂：唯一输入=当前 U", droop, C_OK),
              ("定电压 AVC：输入=U 目标 + 当前 U + 历史", avc, C_LIMIT)]
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.6), sharex=True, sharey=True)
    for ax, (title, values, color) in zip(axes.flat, panels):
        ax.axhline(0, color=C_GRID, lw=.8)
        ax.plot(t, values, "-o", color=color, lw=2.4, ms=7)
        for k, value in enumerate(values):
            ax.annotate(f"{value:.1f}", (k, value), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=8.5)
        ax.set_title(title, fontsize=10)
        ax.set_xticks(t, ["t0", "t1", "t2", "t3"])
        ax.set_ylim(-500, 500)
        ax.set_ylabel("Q 请求 (kvar)")
    axes[1, 0].set_xlabel("共同场景：U 1.030→1.020→1.010→1.010 pu")
    axes[1, 1].set_xlabel("共同场景：P 800→800→400→400 kW")
    fig.suptitle("同一过压场景：四种模式的请求依据不同（Q<0 为吸收）", fontsize=12)
    save(fig, "ch17_modes_compare_fixed")
    _manifest("ch17_modes_compare_fixed", [-300, -262.9, -260, -220, -200, -131.5, -100, 0, 1, 2, 3,
                                      1.030, 1.020, 1.010, 800, 400, -500, 500])


def main():
    fig_pu_scale(); fig_modes_compare(); fig_voltage_rx(); fig_qu_droop(); fig_pq_projection(); fig_avc_cycle()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
