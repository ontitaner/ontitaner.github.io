# @AI_GENERATED
"""一键重新生成全部课程插图：在 figures/ 目录执行 `python make_all.py`。

自动发现 figures/ 下所有 chNN.py 脚本并依次调用其 main()；也可以只生成部分章节：
    python make_all.py ch15 ch21
"""
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
modules = sorted(p.stem for p in HERE.glob("ch[0-9][0-9].py"))
selected = sys.argv[1:] or modules

for name in selected:
    print(f"[{name}]")
    importlib.import_module(name).main()
# @AI_GENERATED: end
