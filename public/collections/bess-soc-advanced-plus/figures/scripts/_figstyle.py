# @AI_GENERATED
"""配图公共样式（对齐 ems-python-learning 的 _style.py 工艺）。

要点：
- 自动布局用 tight_layout + bbox_inches="tight"，不手动 subplots_adjust；
- 标题用 ax.set_title / fig.suptitle 默认居中，不手动定位坐标；
- 白底、细网格、顶右无边框、克制配色；
- 中文字体 Microsoft YaHei / SimHei 优先。

用法：from _figstyle import plt, save, C_DIS, ... ；在脚本结尾 save(fig, "name")。
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
IMG_DIR = ROOT / "img"
LAB_DIR = ROOT / "lab"
IMG_DIR.mkdir(exist_ok=True)

# 让配图脚本直接复用课程实验代码，保证“图里的曲线 = 代码算出来的曲线”
sys.path.insert(0, str(LAB_DIR))

plt.rcParams.update(
    {
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
                            "Source Han Sans SC", "DengXian", "DejaVu Sans"],
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

# 兼容现有脚本使用的 BRAND/CYCLE/style_axes（映射到上面的命名配色）
BRAND = {
    "text": "#1A2433", "muted": "#6c757d", "grid": "#d5dbe3",
    "primary": C_CHG, "accent": C_CHG, "deep": "#1E3A8A",
    "warn": C_ACC, "alert": C_LIMIT, "ok": C_OK, "neutral": C_GRID,
}
CYCLE = [C_CHG, C_DIS, C_OK, C_ACC, C_PURPLE, C_GRID]


def style_axes(ax):
    """保留接口；rcParams 已隐藏顶右边框，这里无需额外处理。"""
    return ax


def save(fig, name: str, *, title: str = None, **_ignored):
    """ems 同款保存：自动紧凑布局 + 去白边。title 用居中 suptitle。

    额外关键字（chapter/subtitle/data/version 等）被忽略，保持向后兼容。
    """
    if title is not None:
        fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    stem = name[:-4] if name.endswith(".png") else name   # 兼容带/不带 .png
    path = IMG_DIR / f"{stem}.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"saved img/{stem}.png")
    return path
# @AI_GENERATED: end