# @AI_GENERATED
"""校验课程 Markdown 中所有 Mermaid 代码块能否被 mmdc 正常渲染。

用法：python check_mermaid.py [文件名 ...]（默认检查课程根目录下全部 .md，跳过 _原稿备份_v1）
依赖：@mermaid-js/mermaid-cli 11+（mmdc 命令，支持直接读取 .md）。

提速策略：
- 按文件批量渲染：mmdc -i xxx.md 一次启动浏览器渲染该文件的全部图块；
- 多个文件并行（默认 4 路）；
- 每次调用都有超时，避免残留的无头浏览器把脚本挂住；
- 只有文件级渲染失败时，才逐块渲染定位出错的图块。
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK = re.compile(r"```mermaid\n(.*?)```", re.S)
FILE_TIMEOUT_S = 180
BLOCK_TIMEOUT_S = 45
WORKERS = 4


def _run(mmdc: str, src: Path, out: Path, timeout: int) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            [mmdc, "-i", str(src), "-o", str(out), "-q"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
        return r.returncode == 0, (r.stderr or r.stdout).strip()
    except subprocess.TimeoutExpired:
        return False, f"超时（>{timeout}s）"


def check_file(mmdc: str, md: Path) -> tuple[str, int, list[str]]:
    blocks = BLOCK.findall(md.read_text(encoding="utf-8"))
    if not blocks:
        return md.name, 0, []
    with tempfile.TemporaryDirectory() as tmp:
        ok, err = _run(mmdc, md, Path(tmp) / "out.md", FILE_TIMEOUT_S)
        if ok:
            return md.name, len(blocks), []
        # 文件级失败：逐块定位
        errors = []
        for n, block in enumerate(blocks, 1):
            src = Path(tmp) / f"b{n}.mmd"
            src.write_text(block, encoding="utf-8")
            b_ok, b_err = _run(mmdc, src, Path(tmp) / f"b{n}.svg", BLOCK_TIMEOUT_S)
            if not b_ok:
                first = block.strip().splitlines()[0] if block.strip() else ""
                errors.append(f"#{n} ({first}): {b_err[:400]}")
        if not errors:  # 逐块都过了，说明是文件级问题
            errors.append(f"文件级渲染失败：{err[:400]}")
        return md.name, len(blocks), errors


def main() -> int:
    mmdc = shutil.which("mmdc")
    if not mmdc:
        print("未找到 mmdc，跳过 Mermaid 校验")
        return 0
    files = [ROOT / f for f in sys.argv[1:]] or sorted(ROOT.glob("*.md"))
    total = failed = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for name, count, errors in pool.map(lambda p: check_file(mmdc, p), files):
            if count == 0:
                continue
            total += count
            if errors:
                failed += len(errors)
                print(f"ERR {name}（{count} 块）")
                for e in errors:
                    print(f"    {e}")
            else:
                print(f"OK  {name}（{count} 块）")
    print(f"合计 {total} 块，失败 {failed} 块")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
# @AI_GENERATED: end
