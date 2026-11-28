# @AI_GENERATED
"""第 06 章端到端示例：超短期功率预测（持续法 + 滚动外推）。

运行：python examples/ch06_ultra_short.py
预期输出与章节 06.3 / 06.5 / 06.6 手算完全一致（自检通过）。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.ultraterm import (  # noqa: E402
    persistence_forecast,
    roll_window,
    rolling_extrapolate,
)


def main():
    print("超短期功率预测  [主线: 30 MW 光伏; 15min-4h 滚动外推]")
    print()

    # --- 06.3 持续法 ---
    pers = persistence_forecast(18.0, 4)
    print(f"[06.3] 持续法 P_meas(t)=18.0, 未来4步 -> {pers} MW")

    # --- 06.4/06.5 滚动外推 ---
    hist = [16.0, 17.0, 18.0]
    ext = rolling_extrapolate(hist, 4)
    print(f"[06.5] 历史 {hist} -> 变化率 delta=+1.0 -> 外推(未来4步) = {ext} MW")

    # 滚动更新：新实测 18.5 到来，窗口右移、斜率重估
    hist2 = roll_window(hist, 18.5)
    ext2 = rolling_extrapolate(hist2, 4)
    print(f"[06.5] 滚动更新: 新实测 18.5 -> 窗口 {hist2} -> delta=+0.5 -> 外推 = {ext2} MW")

    # --- 06.6 边界语义 ---
    clamp = rolling_extrapolate([22.0, 24.0], 4)
    print(f"[06.6] 触顶 clamp: 历史 [22, 24] -> delta=+2.0 -> 外推截到 {clamp} MW")
    low = rolling_extrapolate([5.0, 3.0], 3)
    print(f"[06.6] 触底 clamp: 历史 [5, 3] -> delta=-2.0 -> 外推 = {low} MW（负值截到 0）")
    degen = rolling_extrapolate([18.0], 4)
    print(f"[06.6] 退化: 历史仅1点 [18] -> delta=0.0 -> 退化为持续法 {degen} MW")

    # 与正文手算一致的自检
    ok = (
        pers == [18.0, 18.0, 18.0, 18.0]
        and ext == [19.0, 20.0, 21.0, 22.0]
        and hist2 == [17.0, 18.0, 18.5]
        and ext2 == [19.0, 19.5, 20.0, 20.5]
        and clamp == [25.0, 25.0, 25.0, 25.0]
        and low == [1.0, 0.0, 0.0]
        and degen == [18.0, 18.0, 18.0, 18.0]
    )
    print()
    print("自检通过" if ok else "自检失败")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end