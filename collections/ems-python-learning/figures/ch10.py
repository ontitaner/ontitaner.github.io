# @AI_GENERATED
"""第 10 章配图：①32 位数据的四种字节排列；②一个频率测点的质量位时间线。

两张图都直接调用 lab/ems_lab/datapoint.py 的实现生成。
"""
from __future__ import annotations

import json

import numpy as np
from matplotlib.patches import Rectangle

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.datapoint import PointDef, PointMonitor, Quality, raw_to_registers, registers_to_raw, to_engineering

RAW = -100000  # PCS 有功 −1000.00 kW，int32，×0.01
BYTE_COLORS = {"A": C_DIS, "B": C_ACC, "C": C_CHG, "D": C_PURPLE}


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


def fig_word_order():
    true_bytes = (RAW & 0xFFFFFFFF).to_bytes(4, "big")
    names = dict(zip("ABCD", true_bytes))
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.set_xlim(0, 11)
    ax.set_ylim(-0.6, 4.9)
    ax.axis("off")
    ax.text(0.1, 4.55, f"要传的数：int32  {RAW}（0x{RAW & 0xFFFFFFFF:08X}），×0.01 → −1000.00 kW", fontsize=10.5)
    ax.text(0.1, 4.1, "线上字节顺序（每格 1 字节）", fontsize=9, color=C_GRID)
    ax.text(4.55, 4.1, "寄存器 0 / 寄存器 1", fontsize=9, color=C_GRID)
    ax.text(7.35, 4.1, "EMS 若一律按 ABCD 解读 → 工程值", fontsize=9, color=C_GRID)
    for row, layout in enumerate(["ABCD", "CDAB", "BADC", "DCBA"]):
        y = 3.3 - row * 0.95
        regs = raw_to_registers(RAW, "int32", layout)
        ax.text(0.1, y + 0.2, layout, fontsize=11, fontweight="bold", va="center")
        for i, letter in enumerate(layout):
            x = 1.0 + i * 0.8
            ax.add_patch(Rectangle((x, y), 0.72, 0.42, color=BYTE_COLORS[letter], alpha=0.85))
            ax.text(x + 0.36, y + 0.21, f"{letter}\n{names[letter]:02X}", ha="center", va="center", color="white",
                    fontsize=8.5, linespacing=1.0)
        ax.text(4.55, y + 0.2, f"0x{regs[0]:04X}  0x{regs[1]:04X}", fontsize=10, va="center", family="monospace")
        wrong = to_engineering(registers_to_raw(regs, "int32", "ABCD"), 0.01)
        ok = layout == "ABCD"
        ax.text(7.35, y + 0.2, f"{wrong:,.2f} kW" + ("（正确）" if ok else "（错误）"), fontsize=10, va="center",
                color=C_OK if ok else C_LIMIT)
    ax.text(0.1, -0.45, "A 为最高字节。Modbus 规定寄存器内部高字节在前，但 32 位数据用哪个寄存器放高字，协议没有规定，"
                        "以厂家点表为准。", fontsize=9, color=C_GRID)
    ax.set_title("32 位数据的四种字节排列：同一个 −1000 kW，排错一种就面目全非", fontsize=11)
    save(fig, "ch10_word_order")
    manifest("ch10_word_order", [-168180.55, -100000, -1000, 60, 79, 6079, 7960, 16186078.71, 20364001.26])


def fig_quality_timeline():
    """频率测点 40 s：正常 → 设备冻结 → 通信中断 → 时间戳停滞（过期）→ 恢复。"""
    point = PointDef("meter.f_hz", 0x0200, "uint16", "Hz", scale=0.01, valid_min=45, valid_max=55,
                     stale_after_s=2.0, frozen_after_s=5.0, frozen_tolerance=1e-9)
    mon = PointMonitor(point)
    rng = np.random.default_rng(5)
    dt = 0.2
    t = np.arange(0, 40, dt)
    f_true = 50.0 - 0.08 * (t > 8) + 0.02 * np.sin(t / 2.5) + rng.normal(0, 0.004, t.size)
    values, quals, cached = [], [], None
    for tk, fk in zip(t, f_true):
        sample = tk
        regs = [int(round(fk * 100))]
        if 10 <= tk < 20:  # 设备内部采集卡死：还在应答，但数值不变
            regs = [4992]
        elif 20 <= tk < 25:  # 通信中断
            regs = None
        elif 25 <= tk < 32:  # 通信恢复，但网关一直转发 25 s 时缓存的那一帧（值和采样时间都停住）
            if cached is None:
                cached = regs
            regs, sample = cached, 25.0
        m = mon.evaluate(regs, receive_time=tk, now=tk + 0.05, sample_time=sample)
        values.append(np.nan if m.value is None else m.value)
        quals.append(m.quality)

    colors = {Quality.GOOD: C_OK, Quality.FROZEN: C_ACC, Quality.COMM_FAILED: C_LIMIT, Quality.STALE: C_PURPLE,
              Quality.OUT_OF_RANGE: C_DIS, Quality.INVALID: "k"}
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.2), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax = axes[0]
    ax.plot(t, f_true, color=C_GRID, lw=1, ls=":", label="真实频率")
    ax.plot(t, values, color=C_CHG, lw=1.8, label="EMS 收到的值")
    ax.axhspan(49.97, 50.03, color=C_ACC, alpha=0.12)
    ax.text(0.3, 50.035, "一次调频死区 ±0.03 Hz（示例）", fontsize=8.5, color=C_GRID, va="bottom")
    for x0, x1, text in [(10, 20, "设备冻结在 49.92\n5 s 后判 FROZEN"), (20, 25, "通信中断\nCOMM_FAILED"),
                         (25, 32, "网关转发缓存旧帧\n采样时间停在 25 s\n2 s 后判 STALE")]:
        ax.axvspan(x0, x1, color=C_GRID, alpha=0.07)
        ax.text((x0 + x1) / 2, 50.075, text, ha="center", va="top", fontsize=8.5)
    ax.set_ylabel("频率 (Hz)")
    ax.set_ylim(49.85, 50.08)
    ax.legend(loc="lower left", fontsize=8.5)
    ax.set_title("一个频率测点的质量位时间线（PointMonitor 实际判定结果）  [教学示例]")

    ax = axes[1]
    for tk, q in zip(t, quals):
        ax.add_patch(Rectangle((tk, 0), dt, 1, color=colors[q], lw=0))
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_ylabel("质量位")
    ax.set_xlabel("时间 (s)")
    ax.grid(False)
    handles = [Rectangle((0, 0), 1, 1, color=colors[q]) for q in (Quality.GOOD, Quality.FROZEN, Quality.COMM_FAILED,
                                                                   Quality.STALE)]
    ax.legend(handles, ["GOOD", "FROZEN", "COMM_FAILED", "STALE"], loc="upper center", bbox_to_anchor=(0.5, -0.55),
              ncol=4, fontsize=8.5)
    ax.set_xlim(0, 40)
    save(fig, "ch10_quality_timeline")
    manifest("ch10_quality_timeline", [0, 0.03, 2, 5, 10, 20, 25, 32, 40, 49.92])


def main():
    fig_word_order()
    fig_quality_timeline()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
