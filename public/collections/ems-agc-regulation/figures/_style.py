# @AI_GENERATED
"""AGC 二次调频专项教材配图公共样式。

用法：在 figures/ 目录下运行 `python make_all.py` 重新生成全部插图到 ../img/。
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "img"
IMG_DIR.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans SC", "DengXian"],
    "axes.unicode_minus": False,
    "figure.dpi": 110,
    "savefig.dpi": 150,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 10,
    "axes.titlesize": 11,
    "legend.fontsize": 9,
})

# AGC 专用配色
C_DIS = "#e4572e"       # 放电/增出力
C_CHG = "#2e86ab"       # 充电/减出力
C_GRID = "#6c757d"      # 电网/参考/调度
C_LIMIT = "#c1121f"     # 限值/警告/不合格
C_OK = "#2a9d8f"        # 合格/达标
C_ACC = "#f4a261"       # 辅助/过渡
C_PURPLE = "#7b2cbf"    # 强调/对比
C_CAPACITY = "#2e86ab"  # 容量补偿蓝色
C_MILEAGE = "#e9c46a"   # 里程补偿金色
C_K1 = "#e4572e"        # K1 红色
C_K2 = "#f4a261"        # K2 橙色
C_K3 = "#2a9d8f"        # K3 绿色
C_BESS = "#e4572e"      # 储能
C_TBC = "#2e86ab"       # TBC 模式
C_FFC = "#e4572e"       # FFC 模式
C_FTC = "#2a9d8f"       # FTC 模式


def save(fig, name: str) -> Path:
    path = IMG_DIR / f"{name}.png"
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {path.relative_to(ROOT)}")
    return path


def manifest(name: str, numbers: list[float]) -> None:
    payload = {
        "_comment": "@AI_GENERATED",
        "figure": f"{name}.png",
        "numbers": sorted(set(float(n) for n in numbers)),
        "_comment_end": "@AI_GENERATED: end",
    }
    (IMG_DIR / f"{name}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
# @AI_GENERATED: end