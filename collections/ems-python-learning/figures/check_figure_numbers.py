# @AI_GENERATED
"""图文数字一致性检查：正文“图中标注对照表”里的每个数字，必须出现在图的标注清单中，反之亦然。

约定：
- 画图脚本在输出 img/<名称>.png 的同时输出 img/<名称>.json：{"figure": ..., "numbers": [...]}；
- Markdown 中图片引用之后的第一张、表头含“编号”和“标注”的表格，就是该图的“图中标注对照表”；
- 只比对表格“标注”列中的数字（带单位的数值，正负号可用 − 或 -）。
没有 json 清单的图不检查（老图尚未迁移到新规范）。

用法：python check_figure_numbers.py [文件名.md ...]，不带参数时检查全部章节。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "img"
NUM = re.compile(r"[−-]?\d+(?:\.\d+)?")
IMG_REF = re.compile(r"!\[[^\]]*\]\(img/([^)]+)\.png\)")


def _table_after(lines: list[str], start: int) -> list[list[str]] | None:
    """返回 start 行之后第一张表头含“编号”“标注”的表格的数据行（单元格列表）。"""
    for i in range(start, min(start + 40, len(lines))):
        if lines[i].startswith("|") and "编号" in lines[i] and "标注" in lines[i]:
            header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows = []
            for line in lines[i + 2:]:
                if not line.startswith("|"):
                    break
                rows.append(dict(zip(header, [c.strip() for c in line.strip().strip("|").split("|")])))
            return rows
        if lines[i].startswith("## "):
            return None
    return None


def _numbers(text: str) -> set[float]:
    return {float(x.replace("−", "-")) for x in NUM.findall(text)}


def check_file(md: Path) -> list[str]:
    problems = []
    lines = md.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines):
        for name in IMG_REF.findall(line):
            manifest = IMG / f"{name}.json"
            if not manifest.exists():
                continue
            fig_nums = set(json.loads(manifest.read_text(encoding="utf-8"))["numbers"])
            rows = _table_after(lines, idx + 1)
            if rows is None:
                problems.append(f"{md.name}: {name}.png 有标注清单，但正文缺少“图中标注对照表”")
                continue
            text_nums = set()
            for row in rows:
                text_nums |= _numbers(row.get("标注", ""))
            missing_in_fig = sorted(text_nums - fig_nums)
            missing_in_text = sorted(fig_nums - text_nums)
            if missing_in_fig:
                problems.append(f"{md.name}: {name}.png 正文对照表中的数字 {missing_in_fig} 在图上没有标注")
            if missing_in_text:
                problems.append(f"{md.name}: {name}.png 图上标注的数字 {missing_in_text} 在对照表中没有说明")
    return problems


def main(argv: list[str]) -> int:
    files = [ROOT / a for a in argv] if argv else sorted(ROOT.glob("[0-2][0-9]*_*.md"))
    problems = [p for f in files for p in check_file(f)]
    for p in problems:
        print("FAIL", p)
    print(f"检查 {len(files)} 个文件，问题 {len(problems)} 个")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
# @AI_GENERATED: end
