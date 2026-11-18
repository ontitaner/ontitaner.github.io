# @AI_GENERATED
"""一键生成本课程全部插图。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _style
from _style import manifest
import ch00_paradigm
import ch01_paradigm
import ch02_swing
import ch02_qv
import ch03_inertia
import ch03_droop

MODULES = {
    "ch00": ch00_paradigm,
    "ch01": ch01_paradigm,
    "ch02_swing": ch02_swing,
    "ch02_qv": ch02_qv,
    "ch03_inertia": ch03_inertia,
    "ch03_droop": ch03_droop,
}

if __name__ == "__main__":
    for name, mod in MODULES.items():
        mod.main()
    print(f"\nDone. {len(manifest)} figures saved to {_style.IMG_DIR}")
# @AI_GENERATED: end