# @AI_GENERATED
"""一键生成储能能量管理与经济调度教材全部插图。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _style
from _style import manifest
import ch01_price_arbitrage
import ch02_shaving
import ch03_pv_smoothing
import ch04_feasible
import ch05_schedule
import ch06_rolling
import ch07_bidding
import ch08_stack
import ch09_attribution

MODULES = {
    "ch01": ch01_price_arbitrage,
    "ch02": ch02_shaving,
    "ch03": ch03_pv_smoothing,
    "ch04": ch04_feasible,
    "ch05": ch05_schedule,
    "ch06": ch06_rolling,
    "ch07": ch07_bidding,
    "ch08": ch08_stack,
    "ch09": ch09_attribution,
}

if __name__ == "__main__":
    for name, mod in MODULES.items():
        mod.main()
    print(f"\nDone. {len(manifest)} figures saved to {_style.IMG_DIR}")
# @AI_GENERATED: end