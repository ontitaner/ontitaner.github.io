# @AI_GENERATED
"""构网型储能教材配图公共样式。

用法：在 figures/ 目录下运行 `python make_all.py` 重新生成全部插图到 ../img/。
"""
from __future__ import annotations

import warnings

import matplotlib
matplotlib.use("Agg")

import matplotlib.font_manager as fm  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from pathlib import Path  # noqa: E402

fm._load_fontmanager(try_read_cache=False)

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "img"
IMG_DIR.mkdir(exist_ok=True)

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

# 颜色语义（构网型储能）
C_GFM = "#2a9d8f"      # 构网型（合格/支撑）
C_GFL = "#6c757d"      # 跟网型（中性/跟随）
C_TRIP = "#c1121f"     # 保护阈值/脱网（越限）
C_DB = "#f4a261"       # 一次调频死区（过渡）
C_INERTIA = "#7b2cbf"  # 虚拟惯量/强调

BOX_STYLE = dict(boxstyle="round,pad=0.25", fc="white", ec="#cccccc")
ARROW_STYLE = dict(arrowstyle="->", color="black", lw=0.8)

manifest: list[dict] = []


def save(fig: plt.Figure, name: str):
    path = IMG_DIR / f"{name}.png"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    manifest.append({"file": f"{name}.png"})
    return path


def note(ax, text, xy, xytext, **kw):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=kw.pop("fontsize", 9.5),
                arrowprops=ARROW_STYLE, bbox=BOX_STYLE, **kw)


def main():
    pass
# @AI_GENERATED: end