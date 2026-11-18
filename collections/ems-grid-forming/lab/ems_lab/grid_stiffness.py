# @AI_GENERATED
"""电网强弱与相位偏移（pu 体系）

对应章节：01 跟网与构网：范式边界（01.5 弱电网 PLL 失稳机理）

约定（附录 B / 00.6）：
  SCR      短路比（无量纲），SCR = S_sc / S_n
  Z_g(pu)  站在并网点看进去的电网等值阻抗 = 1/SCR
  Δθ       有功电流扰动 Δi_d 流过感抗 X_g 引起的并网点电压相位偏移
           高压电网阻抗以感抗为主，本课程取 X_g ≈ Z_g

教学示例默认值（对齐 01.5 手算）：
  SCR=1.8 → Z_g≈0.556 pu → Δθ(0.2 pu)≈6.4°（极弱电网）
  SCR=3.0 → Z_g≈0.333 pu → Δθ(0.2 pu)≈3.8°（强电网）
"""
from __future__ import annotations

import math


def z_grid(scr: float) -> float:
    """电网等值阻抗 Z_g(pu) = 1/SCR。"""
    if scr <= 0:
        raise ValueError("SCR 必须为正")
    return 1.0 / scr


def phase_offset_rad(i_d: float, scr: float) -> float:
    """相位偏移 Δθ(rad) = Δi_d · Z_g。

    小信号近似：压降相对 1 pu 电压很小，角度 θ ≈ tan θ = 压降/电压。
    """
    return i_d * z_grid(scr)


def phase_offset_deg(i_d: float, scr: float) -> float:
    """相位偏移 Δθ(°) = degrees(Δθ rad)。"""
    return math.degrees(phase_offset_rad(i_d, scr))


def grid_category(scr: float) -> str:
    """按短路比判定电网强弱（对齐 01.5 判定口径表）。"""
    if scr <= 0:
        raise ValueError("SCR 必须为正")
    if scr >= 3.0:
        return "强电网"
    if scr >= 2.0:
        return "弱电网"
    return "极弱电网"