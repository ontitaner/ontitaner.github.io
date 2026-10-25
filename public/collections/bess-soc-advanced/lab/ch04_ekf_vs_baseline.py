# @AI_GENERATED
"""ch04 基于 EKF 的 SOC 估计 vs 安时积分基线。自包含、零依赖，手写 2×2 矩阵。
真值电池用 ch01 的 1-RC 模型生成带噪声量测；估计器从错误初值 +20% 启动。"""
import math
import random

# ── 统一示例参数（§4A）─────────────
C_AH = 100.0
R0_OHM = 1.0e-3
R1_OHM = 0.8e-3
C1_F = 20000.0
TAU_S = R1_OHM * C1_F     # 16 s
DT_S = 1.0
SOC0_TRUE = 0.50
SOC0_EST = 0.70           # 错误初值 +20%
OCV_SOC = (0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00)
OCV_V   = (2.90, 3.10, 3.20, 3.25, 3.275, 3.29, 3.30, 3.31, 3.325, 3.33, 3.34, 3.36, 3.45)


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
    v_t = ocv(soc) - i_a * R0_OHM - v1
    return v_t, socn, v1n


def coulomb_step(soc, i_meas):
    """基线：纯安时积分（看到的是带零漂的电流）。"""
    return soc - i_meas * DT_S / (3600.0 * C_AH)


def ekf_step(soc, v1, P, i_a, v_meas, q_soc=1e-10, q_v1=1e-8, r_meas=1e-4):
    """一步 EKF。P 为 2×2 协方差（list of list）。返回 (soc, v1, P)。
    状态转移雅可比 F=[[1,0],[0,A_RC]]；量测雅可比 H=[dOCV/dSOC, −1]。"""
    # —— 预测 ——
    soc_p = soc - i_a * DT_S / (3600.0 * C_AH)
    v1_p = v1 * A_RC + i_a * R1_OHM * (1 - A_RC)
    # P_p = F P Fᵀ + Q（F 对角 [1, A_RC]）
    p00 = P[0][0] + q_soc
    p01 = P[0][1] * A_RC
    p10 = P[1][0] * A_RC
    p11 = P[1][1] * A_RC * A_RC + q_v1
    # —— 更新 ——
    h0, h1 = docv(soc_p), -1.0
    v_pred = ocv(soc_p) - i_a * R0_OHM - v1_p
    y = v_meas - v_pred                      # 残差
    # S = H P Hᵀ + R（标量）
    s = h0 * (p00 * h0 + p01 * h1) + h1 * (p10 * h0 + p11 * h1) + r_meas
    # K = P Hᵀ / S（2×1）
    k0 = (p00 * h0 + p01 * h1) / s
    k1 = (p10 * h0 + p11 * h1) / s
    soc_n = soc_p + k0 * y
    v1_n = v1_p + k1 * y
    # P_n = (I − K H) P_p
    p00n = (1 - k0 * h0) * p00 + (-k0 * h1) * p10
    p01n = (1 - k0 * h0) * p01 + (-k0 * h1) * p11
    p10n = (-k1 * h0) * p00 + (1 - k1 * h1) * p10
    p11n = (-k1 * h0) * p01 + (1 - k1 * h1) * p11
    return soc_n, v1_n, [[p00n, p01n], [p10n, p11n]]


def run(seed=0, bias_a=0.5, v_noise=0.002, n=1800):
    """返回 (soc_true[], soc_base[], soc_ekf[])。bias_a：基线看到的电流零漂（A）。"""
    rng = random.Random(seed)
    # 剖面：充放交替，保证有激励（含经过陡峭区的片段）
    profile = []
    for _ in range(n):
        profile.append(50.0 if (len(profile) // 300) % 2 == 0 else -50.0)
    soc_t, v1_t = SOC0_TRUE, 0.0
    soc_b = SOC0_EST
    soc_e, v1_e, P = SOC0_EST, 0.0, [[1e-2, 0.0], [0.0, 1e-4]]
    out_t, out_b, out_e = [], [], []
    for i_a in profile:
        v_t, soc_t, v1_t = truth_step(soc_t, v1_t, i_a)
        v_meas = v_t + rng.gauss(0.0, v_noise)          # 带噪端电压
        i_meas = i_a + bias_a                           # 带零漂电流（两估计器都用）
        soc_b = coulomb_step(soc_b, i_meas)
        soc_e, v1_e, P = ekf_step(soc_e, v1_e, P, i_meas, v_meas)
        out_t.append(soc_t); out_b.append(soc_b); out_e.append(soc_e)
    return out_t, out_b, out_e


def test_ch04():
    t, b, e = run()
    # EKF 从 +20% 错误初值收敛：后段误差 < 2%
    err_ekf = abs(e[-1] - t[-1])
    assert err_ekf < 0.02, err_ekf
    # 基线带零漂持续发散，末端误差明显大于 EKF
    err_base = abs(b[-1] - t[-1])
    assert err_base > err_ekf * 3, (err_base, err_ekf)


def main():
    t, b, e = run()
    print(f"{'步':>5}{'真值SOC':>9}{'基线SOC':>9}{'EKF SOC':>9}{'EKF误差':>9}")
    for k in (0, 50, 100, 300, 600, 1200, 1799):
        print(f"{k:>5}{t[k]:>9.4f}{b[k]:>9.4f}{e[k]:>9.4f}{e[k]-t[k]:>+9.4f}")
    test_ch04()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
