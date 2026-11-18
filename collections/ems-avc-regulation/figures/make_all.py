# @AI_GENERATED
"""一键生成 AVC 教材全部插图。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _style
from _style import manifest
import ch01_modes_compare
import ch02_deadband_pi
import ch03_multi_resource
import ch04_qualification
import ch05_regional
import ch07_scoring
import ch07b_economics
import ch08_commissioning
import ch09_diagnostics

MODULES = {
    "ch01": ch01_modes_compare,
    "ch02": ch02_deadband_pi,
    "ch03": ch03_multi_resource,
    "ch04": ch04_qualification,
    "ch05": ch05_regional,
    "ch07": ch07_scoring,
    "ch07b": ch07b_economics,
    "ch08": ch08_commissioning,
    "ch09": ch09_diagnostics,
}

if __name__ == "__main__":
    for name, mod in MODULES.items():
        mod.main()
    print(f"\nDone. {len(manifest)} figures saved to {_style.IMG_DIR}")
# @AI_GENERATED: end