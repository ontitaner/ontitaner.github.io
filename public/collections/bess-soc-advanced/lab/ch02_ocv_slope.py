# @AI_GENERATED
"""ch02 OCV-SOC 曲线、斜率与可观测性。自包含、零依赖。"""


# ── 统一示例参数（§4A）─────────────
OCV_SOC = (0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00)
OCV_V   = (2.90, 3.10, 3.20, 3.25, 3.275, 3.29, 3.30, 3.31, 3.325, 3.33, 3.34, 3.36, 3.45)
DV_METER = 0.005   # 电压表测量误差 5 mV


def interp(x, xs, ys):
    if x <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            return ys[i - 1] + (x - xs[i - 1]) / (xs[i] - xs[i - 1]) * (ys[i] - ys[i - 1])
    return ys[-1]


def ocv_from_soc(soc):
    return interp(soc, OCV_SOC, OCV_V)


def soc_from_ocv(v):
    """反查：电压严格递增前提下由电压求 SOC。"""
    return interp(v, OCV_V, OCV_SOC)


def ocv_slope(soc, h=1e-3):
    """OCV 在 soc 处斜率 dV/dSOC（V / 单位 SOC），中心差分。"""
    lo = max(soc - h, OCV_SOC[0])
    hi = min(soc + h, OCV_SOC[-1])
    return (ocv_from_soc(hi) - ocv_from_soc(lo)) / (hi - lo)


def soc_error_from_dv(dv, soc):
    """电压误差 dv 在 soc 处放大成多大 SOC 误差 = |dv| / 斜率。"""
    k = ocv_slope(soc)
    return abs(dv) / k


def test_ch02():
    # 平台区（50%）斜率远小于陡峭区（5%）
    k_plateau = ocv_slope(0.50)
    k_steep = ocv_slope(0.05)
    assert k_plateau < k_steep / 10.0, (k_plateau, k_steep)
    # 同样 5 mV 误差，平台区 SOC 误差 > 陡峭区 10 倍
    assert soc_error_from_dv(DV_METER, 0.50) > 10 * soc_error_from_dv(DV_METER, 0.05)


def main():
    print(f"{'SOC':>6}{'OCV(V)':>9}{'斜率(V/SOC)':>13}{'5mV→SOC误差':>13}")
    for soc in (0.05, 0.10, 0.30, 0.50, 0.70, 0.95):
        print(f"{soc:>6.2f}{ocv_from_soc(soc):>9.4f}{ocv_slope(soc):>13.4f}"
              f"{soc_error_from_dv(DV_METER, soc):>12.3%}")
    test_ch02()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
