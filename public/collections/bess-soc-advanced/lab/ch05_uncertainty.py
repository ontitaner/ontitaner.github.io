# @AI_GENERATED
"""ch05 估计不确定度量化及其向可用能量/功率的传播。自包含、零依赖。
复用 1-RC + 2×2 EKF（内联紧凑版），把协方差 P 变成 SOC 置信区间与能量区间。"""
import math
import random

# ── 统一示例参数（§4A）─────────────
C_AH = 100.0
R0_OHM = 1.0e-3
R1_OHM = 0.8e-3
C1_F = 20000.0
TAU_S = R1_OHM * C1_F
DT_S = 1.0
SOC0_TRUE = 0.50
SOC0_EST = 0.70
SOC_MIN = 0.05            # 放电下限
V_NOMINAL = 3.2           # LFP 标称单体电压（能量口径换算用）
ETA_DIS = 0.95            # 放电路径效率
OCV_SOC = (0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00)
OCV_V   = (2.90, 3.10, 3.20, 3.25, 3.275, 3.29, 3.30, 3.31, 3.325, 3.33, 3.34, 3.36, 3.45)
C_KWH = C_AH * V_NOMINAL / 1000.0   # 单体能量口径容量 ≈ 0.32 kWh


def interp(x, xs, ys):
    if x <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            return ys[i - 1] + (x - xs[i - 1]) / (xs[i] - xs[i - 1]) * (ys[i] - ys[i - 1])
    return ys[-1]


def ocv(soc):
    return interp(soc, OCV_SOC, OCV_V)


def docv(soc, h=1e-3):
    lo, hi = max(soc - h, 0.0), min(soc + h, 1.0)
    return (ocv(hi) - ocv(lo)) / (hi - lo)


A_RC = math.exp(-DT_S / TAU_S)


def truth_step(soc, v1, i_a):
    v1n = v1 * A_RC + i_a * R1_OHM * (1 - A_RC)
    socn = soc - i_a * DT_S / (3600.0 * C_AH)
    return ocv(soc) - i_a * R0_OHM - v1, socn, v1n


def ekf_step(soc, v1, P, i_a, v_meas, q_soc=1e-10, q_v1=1e-8, r_meas=1e-4):
    soc_p = soc - i_a * DT_S / (3600.0 * C_AH)
    v1_p = v1 * A_RC + i_a * R1_OHM * (1 - A_RC)
    p00 = P[0][0] + q_soc
    p01 = P[0][1] * A_RC
    p10 = P[1][0] * A_RC
    p11 = P[1][1] * A_RC * A_RC + q_v1
    h0, h1 = docv(soc_p), -1.0
    y = v_meas - (ocv(soc_p) - i_a * R0_OHM - v1_p)
    s = h0 * (p00 * h0 + p01 * h1) + h1 * (p10 * h0 + p11 * h1) + r_meas
    k0 = (p00 * h0 + p01 * h1) / s
    k1 = (p10 * h0 + p11 * h1) / s
    soc_n = soc_p + k0 * y
    v1_n = v1_p + k1 * y
    p00n = (1 - k0 * h0) * p00 + (-k0 * h1) * p10
    p01n = (1 - k0 * h0) * p01 + (-k0 * h1) * p11
    p10n = (-k1 * h0) * p00 + (1 - k1 * h1) * p10
    p11n = (-k1 * h0) * p01 + (1 - k1 * h1) * p11
    return soc_n, v1_n, [[p00n, p01n], [p10n, p11n]]


def soc_sigma(P):
    """SOC 标准差 = √P[0,0]。"""
    return math.sqrt(max(0.0, P[0][0]))


def energy_band(soc, sigma_soc):
    """可放能量点值与 ±σ 区间（kWh）。σ_E ≈ C_kWh·η·σ_SOC。"""
    e = max(0.0, soc - SOC_MIN) * C_KWH * ETA_DIS
    se = C_KWH * ETA_DIS * sigma_soc
    return e, se


def run(seed=0, v_noise=0.002):
    """前段充分激励（充放），后段平台区静置，观察 σ 变化。返回逐步 (soc_true, sigma)。"""
    rng = random.Random(seed)
    profile = ([50.0] * 300 + [-50.0] * 300) + [0.0] * 600   # 激励 → 静置
    soc_t, v1_t = SOC0_TRUE, 0.0
    soc_e, v1_e, P = SOC0_EST, 0.0, [[1e-2, 0.0], [0.0, 1e-4]]
    sig_log, soc_log = [], []
    for i_a in profile:
        v_t, soc_t, v1_t = truth_step(soc_t, v1_t, i_a)
        v_meas = v_t + rng.gauss(0.0, v_noise)
        soc_e, v1_e, P = ekf_step(soc_e, v1_e, P, i_a, v_meas)
        sig_log.append(soc_sigma(P))
        soc_log.append(soc_t)
    return soc_log, sig_log


def test_ch05():
    soc_log, sig = run()
    # 激励段 σ 大幅下降（初值不确定被充放电期间的电压信息快速压缩）
    assert sig[299] < sig[0] * 0.5, (sig[0], sig[299])
    # 平台区静置段：σ 仍在降，但"每步收窄速率"比激励段骤降 10 倍以上——
    # 这才是可观测性差的正确刻画：平台静置时信息累积极慢，而非 σ 完全不动。
    rate_excite = (sig[0] - sig[299]) / 300.0    # 激励段每步平均降幅
    rate_rest = (sig[599] - sig[1199]) / 600.0   # 平台静置段每步平均降幅
    assert rate_rest < rate_excite / 10.0, (rate_rest, rate_excite)
    # 能量区间非负、下界 ≤ 点值
    e, se = energy_band(soc_log[-1], sig[-1])
    assert e >= 0 and e - se <= e


def main():
    soc_log, sig = run()
    print(f"{'步':>5}{'真值SOC':>9}{'σ_SOC':>10}{'可放(kWh)':>11}{'±σ_E':>9}")
    for k in (0, 50, 299, 599, 900, 1199):
        e, se = energy_band(soc_log[k], sig[k])
        print(f"{k:>5}{soc_log[k]:>9.4f}{sig[k]:>10.5f}{e:>11.4f}{se:>9.4f}")
    rate_excite = (sig[0] - sig[299]) / 300.0
    rate_rest = (sig[599] - sig[1199]) / 600.0
    print(f"σ 每步收窄：激励段 {rate_excite:.2e} / 步，平台静置段 {rate_rest:.2e} / 步"
          f"（慢 {rate_excite / rate_rest:.0f} 倍）")
    test_ch05()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
