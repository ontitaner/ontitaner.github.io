# @AI_GENERATED
"""ch01 示例：弱电网 PLL 失稳的定量根因（pu 体系）

主线场景：50MW/100MWh 储能电站，SCR≈1.8（极弱电网）
对齐 01.5 手算：
  SCR=1.8 → Z_g≈0.556 pu → Δθ(0.2 pu)≈6.4°
  SCR=3.0 → Z_g≈0.333 pu → Δθ(0.2 pu)≈3.8°
  本站相位偏移是强电网的 1.67 倍
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.grid_stiffness import grid_category, phase_offset_deg, z_grid  # noqa: E402


def main():
    i_d = 0.2          # 一次有功电流扰动（pu）
    scr_weak = 1.8     # 本站短路比（极弱电网）
    scr_strong = 3.0   # 强电网对照

    zg_w = z_grid(scr_weak)
    zg_s = z_grid(scr_strong)
    th_w = phase_offset_deg(i_d, scr_weak)
    th_s = phase_offset_deg(i_d, scr_strong)
    ratio = zg_w / zg_s

    print("弱电网 PLL 失稳定量根因  [主线: 50MW/100MWh 储能电站, SCR≈1.8]\n")
    print(f"{'电网':<12}{'SCR':>8}{'Z_g(pu)':>10}{'Δθ(deg)':>10}")
    print(f"{'本站(极弱)':<12}{scr_weak:>8.1f}{zg_w:>10.3f}{th_w:>10.1f}")
    print(f"{'强电网':<12}{scr_strong:>8.1f}{zg_s:>10.3f}{th_s:>10.1f}")

    print(f"\n同一 Δi_d={i_d} pu 扰动，本站相位偏移是强电网的 {ratio:.2f} 倍")
    print(f"本站 SCR={scr_weak} -> {grid_category(scr_weak)}，PLL 极易失稳（对应 00.1 场景）")

    # 与正文手算一致的自检
    assert abs(zg_w - 0.556) < 1e-3
    assert abs(zg_s - 0.333) < 1e-3
    assert abs(th_w - 6.4) < 0.1
    assert abs(th_s - 3.8) < 0.1
    assert abs(ratio - 1.67) < 0.01
    print("\n自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end