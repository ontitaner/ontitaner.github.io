# @AI_GENERATED
"""一次调频专项教材配图公共样式。

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

FN = 50.0  # 额定频率 (Hz)

C_DIS = "#e4572e"       # 放电/增出力
C_CHG = "#2e86ab"       # 充电/减出力
C_GRID = "#6c757d"      # 电网/参考
C_LIMIT = "#c1121f"     # 限值/警告
C_OK = "#2a9d8f"        # 合格/达标
C_ACC = "#f4a261"       # 辅助/过渡
C_PURPLE = "#7b2cbf"    # 强调
C_WIND = "#2e86ab"      # 风电
C_SOLAR = "#e9c46a"     # 光伏
C_BESS = "#e4572e"      # 储能
C_THERMAL = "#6c757d"   # 火电
C_HYDRO = "#2a9d8f"     # 水电


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


# 死区处理函数（供各图共用）
def deadband_shift(delta_f, width):
    """连续型/平移型死区：sign(Δf) × max(0, |Δf| − width)"""
    return np.sign(delta_f) * np.maximum(0, np.abs(delta_f) - width)


def deadband_cut(delta_f, width):
    """截断型/削平型死区：|Δf| ≤ width → 0，否则 Δf"""
    return np.where(np.abs(delta_f) <= width, 0, delta_f)
# @AI_GENERATED: end