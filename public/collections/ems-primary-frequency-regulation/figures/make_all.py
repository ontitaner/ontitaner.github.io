# @AI_GENERATED
"""一键重新生成一次调频专项教材全部配图。

在 figures/ 目录执行 `python make_all.py`。
"""
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
modules = sorted(p.stem for p in HERE.glob("ch[0-9][0-9]_*.py"))

selected = sys.argv[1:] or modules

for name in selected:
    print(f"[{name}]")
    importlib.import_module(name).main()
# @AI_GENERATED: end