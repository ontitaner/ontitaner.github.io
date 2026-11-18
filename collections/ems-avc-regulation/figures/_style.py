# @AI_GENERATED
"""AVC 自动电压控制专项教材配图公共样式。

用法：在 figures/ 目录下运行 `python make_all.py` 重新生成全部插图到 ../img/。
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import warnings

import matplotlib.font_manager as fm  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

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

C_DIS = "#e4572e"
C_CHG = "#2e86ab"
C_ACC = "#f4a261"
C_OK = "#2a9d8f"
C_LIMIT = "#c1121f"
C_GRID = "#6c757d"
C_PURPLE = "#7b2cbf"

C_Q_ABSORB = C_CHG
C_Q_GENERATE = C_DIS
C_VOLTAGE = C_PURPLE
C_TARGET = C_GRID
C_DEADBAND = C_LIMIT
C_PI_P = C_DIS
C_PI_I = C_CHG
C_SVG = C_CHG
C_PCS = C_DIS
C_CAPACITOR = C_OK
C_ENERGY_PRICE = C_CHG
C_CAP_PRICE = "#e9c46a"

BOX_STYLE = dict(boxstyle="round,pad=0.25", fc="white", ec="#cccccc")
ARROW_STYLE = dict(arrowstyle="->", color="black", lw=0.8)

manifest: list[dict] = []


def save(fig: plt.Figure, name: str) -> Path:
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