# @AI_GENERATED
"""储能能量管理与经济调度教材配图公共样式。

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

# 颜色语义（能量调度）
C_DIS = "#e4572e"      # 放电
C_CHG = "#2e86ab"      # 充电
C_PRICE = "#e9c46a"    # 电价
C_LOAD = "#6c757d"     # 负荷
C_PV = "#2a9d8f"       # 光伏
C_SOC = "#7b2cbf"      # SOC
C_TARGET = "#c1121f"   # 目标/需量线
C_PROFIT = "#2a9d8f"   # 收益
C_COST = "#c1121f"     # 成本
C_GRID = "#6c757d"     # 电网/中性
C_ACC = "#f4a261"      # 强调/平滑

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