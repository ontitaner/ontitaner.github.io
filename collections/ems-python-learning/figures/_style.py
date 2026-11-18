# @AI_GENERATED
"""配图公共样式：中文字体、统一配色、输出路径。

用法：在 figures/ 目录下运行 `python make_all.py` 重新生成全部插图到 ../img/。
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "img"
IMG_DIR.mkdir(exist_ok=True)

# 让配图脚本直接复用课程实验代码，保证“图里的曲线 = 代码算出来的曲线”
sys.path.insert(0, str(ROOT / "lab"))

plt.rcParams.update(
    {
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
    }
)

# 统一配色：放电/发出=橙红，充电/吸收=蓝，电网/参考=灰，限值=红虚线
C_DIS = "#e4572e"
C_CHG = "#2e86ab"
C_GRID = "#6c757d"
C_LIMIT = "#c1121f"
C_OK = "#2a9d8f"
C_ACC = "#f4a261"
C_PURPLE = "#7b2cbf"


def save(fig, name: str) -> Path:
    path = IMG_DIR / f"{name}.png"
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {path.relative_to(ROOT)}")
    return path
# @AI_GENERATED: end
