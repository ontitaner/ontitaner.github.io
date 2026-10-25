# @AI_GENERATED
"""图表脚本共享样式与 lab 导入路径。仅构建时用（需 matplotlib）。"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# 中文字体（构建环境需装 Noto Sans CJK；缺失时回退默认、仅影响中文显示）
plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

_HERE = os.path.dirname(os.path.abspath(__file__))
LAB_DIR = os.path.normpath(os.path.join(_HERE, "..", "..", "lab"))
IMG_DIR = os.path.normpath(os.path.join(_HERE, "..", "..", "img"))
sys.path.insert(0, LAB_DIR)


def save(fig, name):
    fig.tight_layout()
    path = os.path.join(IMG_DIR, name)
    fig.savefig(path, dpi=150)
    print(f"saved img/{name}")
# @AI_GENERATED: end
