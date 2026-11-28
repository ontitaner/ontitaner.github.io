# @AI_GENERATED
"""第 04 章端到端示例：NWP 气象数据质量门控（五类坏点 + 综合掩码 + 缺测回填）。

运行：python examples/ch04_nwp_quality.py
预期输出与章节 04.4 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.nwp_quality import (  # noqa: E402
    fill_missing,
    missing_mask,
    quality_mask,
    range_mask,
    step_mask,
    stuck_mask,
    timestamp_mask,
)


def main():
    print("NWP 气象数据质量门控  [主线: 30 MW 光伏; GHI 15 min 网格, 96 点/日]")
    print()

    # --- 04.4 手算主案例：10 点 GHI 序列 ---
    ghi = [800.0, 810.0, float("nan"), 820.0, 820.0, 820.0, 820.0, 300.0, 1200.0, 1300.0]
    times = ["08:00", "08:15", "08:30", "08:45", "09:00", "09:15", "09:30", "09:45", "10:00", "10:15"]

    m_miss = missing_mask(ghi)
    m_range = range_mask(ghi, 0.0, 1200.0)
    m_step = step_mask(ghi, 600.0)
    m_stuck = stuck_mask(ghi, 4, 0.0)
    m_all = quality_mask(ghi, 0.0, 1200.0, 600.0, 4, 0.0)

    def show(name, mask):
        print(f"[04.4] {name:<6} " + " ".join("T" if x else "." for x in mask))

    print("[04.4] 主案例 GHI = [800, 810, NaN, 820, 820, 820, 820, 300, 1200, 1300]")
    print(f"[04.4] 索引   " + " ".join(f"{i:>2}" for i in range(len(ghi))))
    print(f"[04.4] 时刻   " + " ".join(times))
    show("缺测", m_miss)
    show("超限", m_range)
    show("跳变", m_step)
    show("卡死", m_stuck)
    show("综合", m_all)

    n_bad = sum(m_all)
    n_good = len(ghi) - n_bad
    print(f"[04.4] 坏点 {n_bad} 个、有效点 {n_good} 个、有效点率 {n_good / len(ghi):.0%}")

    # --- 缺测回填 ---
    filled = fill_missing(ghi)
    print(f"[04.4] 回填索引 2（前 810 后 820）= {filled[2]:.1f} W/m²")

    # --- 时标错位 ---
    m_ts_ok = timestamp_mask([660.0])     # 11:00 -> 对齐
    m_ts_bad = timestamp_mask([727.5])    # 12:07:30 -> 错位
    print(f"[04.3] 时标 11:00(660min) -> 错位 = {m_ts_ok[0]}；12:07:30(727.5min) -> 错位 = {m_ts_bad[0]}")

    # --- 逐拍追踪 t=0：全好点 ---
    ghi0 = [800.0, 810.0, 820.0]
    m_all0 = quality_mask(ghi0, 0.0, 1200.0, 600.0, 4, 0.0)
    print(f"[2拍] t=0 全好点 GHI=[800, 810, 820] -> 坏点 {sum(m_all0)} 个、有效点率 100%")

    # 与正文手算一致的自检
    ok = (
        m_miss == [False, False, True, False, False, False, False, False, False, False]
        and m_range == [False, False, False, False, False, False, False, False, False, True]
        and m_step == [False, False, False, False, False, False, False, False, True, False]
        and m_stuck == [False, False, False, True, True, True, True, False, False, False]
        and m_all == [False, False, True, True, True, True, True, False, True, True]
        and n_bad == 7
        and n_good == 3
        and abs(filled[2] - 815.0) < 1e-9
        and m_ts_ok == [False]
        and m_ts_bad == [True]
        and m_all0 == [False, False, False]
    )
    print()
    print("自检通过" if ok else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end