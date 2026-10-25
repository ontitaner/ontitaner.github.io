# @AI_GENERATED
"""ch06 电池组单体不一致性机理与量化。自包含、零依赖。
4 单体均分放电，最低单体触限即整组停，量化木桶效应对可用容量的影响。"""

# ── 统一示例参数（§4A）─────────────
PACK_SOC0 = [0.60, 0.58, 0.55, 0.45]   # 4 单体初始 SOC（与木桶效应示例呼应）
CAP_KWH_EACH = 0.32                     # 每簇能量口径容量（100 Ah × 3.2 V）
SOC_MIN = 0.05
P_EACH_KW = 0.1                         # 每簇放电功率（均分）
DT_H = 0.1                              # 仿真步长 h


def spread(socs):
    """极差与标准差。"""
    n = len(socs)
    mean = sum(socs) / n
    rng = max(socs) - min(socs)
    std = (sum((s - mean) ** 2 for s in socs) / n) ** 0.5
    return rng, std, mean


def usable_by_min(socs):
    """木桶效应：电流均分时整组可放 = 最低簇决定。"""
    return len(socs) * max(0.0, min(socs) - SOC_MIN) * CAP_KWH_EACH


def usable_by_mean(socs):
    """错误口径：按平均 SOC 估（高估）。"""
    _, _, mean = spread(socs)
    return len(socs) * max(0.0, mean - SOC_MIN) * CAP_KWH_EACH


def simulate():
    """均分放电到最低单体触限。返回 (delivered_kwh, 停机时各簇 SOC)。"""
    socs = list(PACK_SOC0)
    delivered = 0.0
    while min(socs) > SOC_MIN + 1e-9:
        socs = [s - P_EACH_KW * DT_H / CAP_KWH_EACH for s in socs]
        delivered += P_EACH_KW * len(socs) * DT_H
    return delivered, socs


def test_ch06():
    # 木桶效应：按平均估 > 按最低簇估（高估）
    assert usable_by_mean(PACK_SOC0) > usable_by_min(PACK_SOC0)
    # 实际放出 ≈ 按最低簇估（电流均分，最低簇先到下限）
    delivered, _ = simulate()
    assert abs(delivered - usable_by_min(PACK_SOC0)) < 0.05 * usable_by_min(PACK_SOC0)
    # 极差与均值正确
    rng, std, mean = spread(PACK_SOC0)
    assert abs(rng - 0.15) < 1e-9 and abs(mean - 0.545) < 1e-9


def main():
    rng, std, mean = spread(PACK_SOC0)
    print(f"初始：极差 {rng:.1%}  标准差 {std:.2%}  平均 {mean:.1%}")
    print(f"按最低簇可放 {usable_by_min(PACK_SOC0):.3f} kWh"
          f" | 按平均可放 {usable_by_mean(PACK_SOC0):.3f} kWh（高估）")
    delivered, socs_stop = simulate()
    print(f"实际放出 {delivered:.3f} kWh，停机时各簇 SOC = "
          f"{[round(s, 3) for s in socs_stop]}")
    test_ch06()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
