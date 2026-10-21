# @AI_GENERATED
"""第 12 章配图：可行域区间交集、负荷突降时的防倒送动态、SOC 分区。

所有区间和曲线都直接调用 lab/ems_lab/constraints.py 与 control.py 的实现生成，数值为 [教学示例]。
"""
from __future__ import annotations

import json
import math

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.constraints import (
    BoundCorrector,
    Layer,
    SocZoneConfig,
    device_interval,
    export_limit_interval,
    import_limit_interval,
    permission_interval,
    project,
    soc_interval,
)
from ems_lab.control import LowPassFilter, RateLimiter, clamp

LAYER_COLOR = {Layer.HARD_SAFETY: C_LIMIT, Layer.DEVICE: C_CHG, Layer.SITE: C_ACC, Layer.STRATEGY: C_PURPLE}
LAYER_NAME = {Layer.HARD_SAFETY: "① 硬安全许可", Layer.DEVICE: "② 设备能力", Layer.SITE: "③ 站点约束",
              Layer.STRATEGY: "④ 策略"}
XLIM = 1250


def manifest(name: str, numbers: list[float]) -> None:
    payload = {"_comment": "@AI_GENERATED", "figure": f"{name}.png",
               "numbers": sorted(set(float(n) for n in numbers)),
               "_comment_end": "@AI_GENERATED: end"}
    (IMG_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _fmt(v: float) -> str:
    if math.isinf(v):
        return "−∞" if v < 0 else "+∞"
    return f"{v:+.0f}"


def _draw_intervals(ax, constraints, request_kw, title):
    r = project(request_kw, constraints)
    rows = list(constraints)
    n = len(rows)
    for i, c in enumerate(rows):
        y = n - i
        lo = max(c.lower_kw, -XLIM)
        hi = min(c.upper_kw, XLIM)
        ax.barh(y, hi - lo, left=lo, height=0.55, color=LAYER_COLOR[c.layer], alpha=0.55,
                edgecolor=LAYER_COLOR[c.layer])
        ax.text(-XLIM - 40, y, f"{LAYER_NAME[c.layer][:1]} {c.name}", ha="right", va="center", fontsize=9)
        label = f"[{_fmt(c.lower_kw)}, {_fmt(c.upper_kw)}]"
        ax.text((lo + hi) / 2, y, label, ha="center", va="center", fontsize=8.5,
                bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.5))
    # 最终可行域
    if r.conflicts:
        ax.plot([r.lower_kw], [0], "s", color=C_LIMIT, ms=11)
        label = (f"交集为空 → 放松【{r.conflicts[0].name}】\n"
                 f"取 {r.final_kw:+.0f}，缺口 {r.conflicts[0].shortfall_kw:.0f} kW 上报")
        ax.text(r.final_kw - 70, 0, label, ha="right", va="center", fontsize=9, color=C_LIMIT)
    else:
        ax.barh(0, r.upper_kw - r.lower_kw, left=r.lower_kw, height=0.55, color=C_OK, alpha=0.7)
        ax.text((r.lower_kw + r.upper_kw) / 2, 0, f"[{r.lower_kw:+.0f}, {r.upper_kw:+.0f}]",
                ha="center", va="center", fontsize=9, color="k", fontweight="bold")
    ax.text(-XLIM - 40, 0, "最终可行域（交集）", ha="right", va="center", fontsize=9, fontweight="bold")
    # 请求 → 投影结果
    y = -0.85
    ax.plot(request_kw, y, "v", color=C_GRID, ms=9, zorder=5)
    ax.plot(r.final_kw, y, "o", color=C_DIS, ms=9, zorder=5)
    if r.final_kw != request_kw:
        ax.annotate("", xy=(r.final_kw, y), xytext=(request_kw, y),
                    arrowprops=dict(arrowstyle="->", color=C_DIS, lw=1.5))
    ax.text(request_kw + 40, y - 0.1, f"请求 {request_kw:+.0f}", ha="left", va="top", fontsize=9, color=C_GRID)
    reason = r.binding if not r.conflicts else "尽力而为"
    ax.text(r.final_kw - 40, y - 0.1, f"投影后 {r.final_kw:+.0f}（{reason}）", ha="right", va="top",
            fontsize=9, color=C_DIS)
    ax.plot([0, 0], [-0.4, n + 0.4], color="k", lw=0.8)
    ax.set_xlim(-XLIM, XLIM)
    ax.set_ylim(-1.7, n + 0.6)
    ax.set_yticks([])
    ax.set_xlabel("储能功率 P_BESS (kW)   充电 ← 0 → 放电")
    ax.set_title(title, fontsize=10)
    ax.grid(axis="y", visible=False)
    return r


def fig_feasible_domain():
    fig, axes = plt.subplots(2, 1, figsize=(10, 7.6))
    normal = [
        permission_interval(True, True),
        device_interval(available_charge_kw=500, available_discharge_kw=800),
        soc_interval(0.50, 1000),
        export_limit_interval(p_load_kw=600, p_pv_kw=400, p_export_limit_kw=0, p_aux_kw=30, p_loss_kw=10),
        import_limit_interval(p_load_kw=600, p_pv_kw=400, p_import_limit_kw=1800, p_aux_kw=30, p_loss_kw=10),
    ]
    _draw_intervals(axes[0], normal, 800,
                    "例 1：负荷 600、辅助 30、损耗 10、光伏 400、零倒送 —— 请求放电 800，被防倒送截到 240")
    conflict = [
        permission_interval(True, True),
        device_interval(available_charge_kw=500, available_discharge_kw=800),
        soc_interval(0.60, 1000),
        export_limit_interval(p_load_kw=600, p_pv_kw=1500, p_export_limit_kw=0, p_aux_kw=30, p_loss_kw=10),
        import_limit_interval(p_load_kw=600, p_pv_kw=1500, p_import_limit_kw=1800, p_aux_kw=30, p_loss_kw=10),
    ]
    _draw_intervals(axes[1], conflict, 0,
                    "例 2：中午光伏 1500 —— 防倒送要求至少充 860，BMS 只允许充 500：可行域为空")
    handles = [plt.Rectangle((0, 0), 1, 1, color=LAYER_COLOR[k], alpha=0.55) for k in LAYER_COLOR]
    axes[0].legend(handles, [LAYER_NAME[k] for k in LAYER_COLOR], loc="upper right", ncol=4, fontsize=8,
                   bbox_to_anchor=(1.0, 1.0))
    axes[0].set_ylim(-1.7, len(normal) + 1.3)
    save(fig, "ch12_feasible_domain")
    manifest("ch12_feasible_domain", [-1560, -1000, -860, -500, 240, 360, 800, 1000])


def simulate_load_drop(mode: str):
    """负荷在 t=10 s 从 1000 kW 突降到 300 kW。储能策略请求放电 900 kW，零倒送，控制裕度 20 kW。

    mode:
      "ramp_blocks": 约束在 Ramp 之前、Ramp 之后没有兜底（错误）；
      "ff_only":     前馈约束 + Ramp 后兜底，但没有并网点闭环（有 40 kW 未计量光伏）；
      "ff_fb":       前馈约束 + Ramp 后兜底 + 并网点闭环修正（推荐）。
    """
    dt, t_end = 0.05, 30.0
    t = np.arange(0, t_end, dt)
    load = np.where(t < 10, 1000.0, 300.0)
    aux, loss_true, pv_unmetered = 20.0, 10.0, 40.0  # 未计量的小光伏：前馈公式看不到它
    target_pcc = -20.0  # 控制目标：P_PCC ≤ −20 kW（给 0 kW 出口上限留 20 kW 裕度）
    request = 900.0
    delay = int(0.2 / dt)  # 负荷和并网点测量的延迟 0.2 s
    ramp = RateLimiter(up_rate=50, down_rate=50, initial=request)
    pcs = LowPassFilter(tau_s=0.15)  # PCS 功率响应
    pcs.update(request, dt)
    # 闭环只负责修正前馈“看不到”的慢变误差，所以调得慢、修正量有上限；快速收缩靠前馈
    corr = BoundCorrector(kp=0.05, ki=0.15, max_correction_kw=100)
    p_bess_hist, p_pcc_hist = [], []
    p_actual = request
    correction = 0.0
    for k in range(t.size):
        load_meas = load[max(0, k - delay)]
        pcc_meas = p_pcc_hist[k - delay] if k - delay >= 0 else pv_unmetered + p_actual - load[0] - aux - loss_true
        # 前馈：用测量到的负荷和辅助用电推出放电上限（损耗、未计量光伏不在公式里）
        ff_upper = export_limit_interval(load_meas, 0.0, 0.0, p_aux_kw=aux).upper_kw + target_pcc
        if mode == "ff_fb":
            active = request >= ff_upper + correction
            correction = corr.update(target_pcc - pcc_meas, dt, active)
        upper = ff_upper + correction
        if mode == "ramp_blocks":
            cmd = ramp.update(clamp(request, -1000, upper), dt)
        else:
            ramped = ramp.update(clamp(request, -1000, upper), dt)
            cmd = clamp(ramped, -1000, upper)
            if cmd != ramped:
                ramp.reset(cmd)
        p_actual = pcs.update(cmd, dt)
        p_bess_hist.append(p_actual)
        p_pcc_hist.append(pv_unmetered + p_actual - load[k] - aux - loss_true)
    return t, load, np.array(p_bess_hist), np.array(p_pcc_hist)


def fig_load_drop():
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.8), sharex=True, gridspec_kw={"height_ratios": [1.1, 1]})
    cases = [
        ("ramp_blocks", C_GRID, "错误：约束放在 Ramp 之前，Ramp 拦住了约束收缩"),
        ("ff_only", C_ACC, "前馈 + Ramp 后兜底，无闭环（未计量光伏 40 kW）"),
        ("ff_fb", C_OK, "前馈 + Ramp 后兜底 + 并网点闭环修正"),
    ]
    ax = axes[0]
    t = load = None
    for mode, color, label in cases:
        t, load, p_bess, p_pcc = simulate_load_drop(mode)
        ax.plot(t, p_bess, color=color, lw=2.2, label=label)
        axes[1].plot(t, p_pcc, color=color, lw=2.2, label=label)
        if mode == "ramp_blocks":
            axes[1].fill_between(t, 0, p_pcc, where=p_pcc > 0, color=C_LIMIT, alpha=0.18)
            peak = p_pcc.max()
            dur = (p_pcc > 100).sum() * (t[1] - t[0])
    ax.plot(t, load, color="k", lw=1.4, ls="--", label="负荷（t=10 s 从 1000 突降到 300）")
    ax.set_ylabel("功率 (kW)")
    ax.set_ylim(0, 1250)
    ax.legend(loc="upper right", fontsize=8.5)
    ax.set_title("负荷突降时的防倒送：安全约束的收缩必须立即生效  [教学示例]", fontsize=10)

    ax = axes[1]
    ax.axhline(0, color=C_LIMIT, ls="--", lw=1.2)
    ax.text(0.3, 25, "出口上限 0 kW（零倒送）", color=C_LIMIT, fontsize=9)
    ax.axhline(-20, color=C_GRID, ls=":", lw=1)
    ax.text(0.3, -55, "控制目标 −20 kW（裕度）", color=C_GRID, fontsize=9)
    ax.annotate(f"倒送最高约 {peak:.0f} kW，超过 100 kW 持续约 {dur:.0f} s", xy=(11.0, peak * 0.9),
                xytext=(15.5, 520), arrowprops=dict(arrowstyle="->", color=C_LIMIT), color=C_LIMIT, fontsize=9)
    ax.annotate("所有方案都有约 0.3 s 的尖峰：\n测量延迟 0.2 s + PCS 响应", xy=(10.05, 450), xytext=(3.2, 380),
                arrowprops=dict(arrowstyle="->", color="k"), fontsize=9)
    ax.annotate("稳态仍倒送约 10 kW\n（前馈看不到的光伏）", xy=(25, 10), xytext=(22, 250),
                arrowprops=dict(arrowstyle="->", color=C_ACC), color=C_ACC, fontsize=9)
    ax.set_ylabel("并网点 P_PCC (kW)\n送电为正")
    ax.set_xlabel("时间 (s)")
    ax.set_ylim(-200, 750)
    save(fig, "ch12_load_drop")
    manifest("ch12_load_drop", [-20, -0.0, 0.15, 0.2, 10, 40, 50, 100, 300, 610, 900, 1000])


def fig_soc_zones():
    cfg = SocZoneConfig()
    soc = np.linspace(0, 1, 501)
    lower = np.array([soc_interval(s, 1000, cfg).lower_kw for s in soc])
    upper = np.array([soc_interval(s, 1000, cfg).upper_kw for s in soc])
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.fill_between(soc * 100, 0, upper, color=C_DIS, alpha=0.35, label="允许放电上限")
    ax.fill_between(soc * 100, lower, 0, color=C_CHG, alpha=0.35, label="允许充电上限（负）")
    ax.plot(soc * 100, upper, color=C_DIS, lw=2)
    ax.plot(soc * 100, lower, color=C_CHG, lw=2)
    for x in (cfg.stop_discharge_at, cfg.full_discharge_from, cfg.full_charge_until, cfg.stop_charge_at):
        ax.axvline(x * 100, color=C_GRID, ls=":", lw=1)
    ax.text(5, 1080, "禁止放电", ha="center", fontsize=9, color=C_LIMIT)
    ax.text(12.5, 1080, "降额", ha="center", fontsize=9)
    ax.text(50, 1080, "正常运行区", ha="center", fontsize=9, color=C_OK)
    ax.text(87.5, 1080, "降额", ha="center", fontsize=9)
    ax.text(95, 1080, "禁止充电", ha="center", fontsize=9, color=C_LIMIT)
    ax.axvspan(0, 8, ymin=0, ymax=0.5, color=C_PURPLE, alpha=0.08)
    ax.annotate("SOC 低于 8% 发出自充请求\n高于 15% 才停止（滞回）", xy=(8, -600), xytext=(22, -800),
                arrowprops=dict(arrowstyle="->", color=C_PURPLE), color=C_PURPLE, fontsize=9)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("SOC (%)")
    ax.set_ylabel("P_BESS 允许区间 (kW)")
    ax.set_ylim(-1200, 1200)
    ax.set_xlim(0, 100)
    ax.set_title("SOC 分区保护：SOC 越低放电上限越小，越高充电上限越小  [教学示例阈值]", fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=8.5, frameon=False)
    save(fig, "ch12_soc_zones")
    manifest("ch12_soc_zones", [0, 8, 10, 15, 85, 90, 1000])


def main():
    fig_feasible_domain()
    fig_load_drop()
    fig_soc_zones()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
