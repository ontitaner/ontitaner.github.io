# @AI_GENERATED
"""ch08 验证指标与标准符合性。自包含、零依赖。
对估计误差序列算 RMSE / 最大误差 / 收敛步，与教学口径精度判据对照。
误差序列由内联紧凑 EKF 现跑产生（与 ch04 同一真值电池、同一循环顺序），保证可复现。"""
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
TOL = 0.02                 # 收敛容差带 2%
ACCURACY_LIMIT = 0.05      # 教学口径 SOC 精度判据 5%（落稿前据 GB/T 核实，[标准依据] 待填）
OCV_SOC = (0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00)
OCV_V   = (2.90, 3.10, 3.20, 3.25, 3.275, 3.29, 3.30, 3.31, 3.325, 3.33, 3.34, 3.36, 3.45)
A_RC = math.exp(-DT_S / TAU_S)


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


def _ekf_errors(seed=0, v_noise=0.002, n=1200):
    """现跑 EKF（循环顺序与 ch04 一致），返回逐步 |估计−真值| 误差序列。"""
    rng = random.Random(seed)
    profile = [50.0 if (k // 300) % 2 == 0 else -50.0 for k in range(n)]
    soc_t, v1_t = SOC0_TRUE, 0.0
    soc_e, v1_e = SOC0_EST, 0.0
    P = [[1e-2, 0.0], [0.0, 1e-4]]
    errs = []
    for i_a in profile:
        # —— 真值电池：先用当前状态算端电压，再推进 ——
        v_t = ocv(soc_t) - i_a * R0_OHM - v1_t
        soc_t = soc_t - i_a * DT_S / (3600.0 * C_AH)
        v1_t = v1_t * A_RC + i_a * R1_OHM * (1 - A_RC)
        v_meas = v_t + rng.gauss(0.0, v_noise)
        # —— EKF 预测 ——
        soc_p = soc_e - i_a * DT_S / (3600.0 * C_AH)
        v1_p = v1_e * A_RC + i_a * R1_OHM * (1 - A_RC)
        p00 = P[0][0] + 1e-10
        p01 = P[0][1] * A_RC
        p10 = P[1][0] * A_RC
        p11 = P[1][1] * A_RC * A_RC + 1e-8
        # —— EKF 更新 ——
        h0, h1 = docv(soc_p), -1.0
        y = v_meas - (ocv(soc_p) - i_a * R0_OHM - v1_p)
        s = h0 * (p00 * h0 + p01 * h1) + h1 * (p10 * h0 + p11 * h1) + 1e-4
        k0 = (p00 * h0 + p01 * h1) / s
        k1 = (p10 * h0 + p11 * h1) / s
        soc_e = soc_p + k0 * y
        v1_e = v1_p + k1 * y
        P = [[(1 - k0 * h0) * p00 + (-k0 * h1) * p10, (1 - k0 * h0) * p01 + (-k0 * h1) * p11],
             [(-k1 * h0) * p00 + (1 - k1 * h1) * p10, (-k1 * h0) * p01 + (1 - k1 * h1) * p11]]
        errs.append(abs(soc_e - soc_t))
    return errs


def rmse(errs):
    return (sum(e * e for e in errs) / len(errs)) ** 0.5


def max_error(errs):
    return max(errs)


def convergence_step(errs, tol=TOL):
    """首次进入容差带且此后持续保持的步号；永不收敛返回 -1。"""
    for k in range(len(errs)):
        if all(e <= tol for e in errs[k:]):
            return k
    return -1


def test_ch08():
    errs = _ekf_errors()
    # 收敛后段 RMSE 在判据内
    kc = convergence_step(errs)
    assert kc >= 0, "EKF 未收敛"
    assert rmse(errs[kc:]) <= ACCURACY_LIMIT
    # 稳态最大误差也在判据内
    assert max_error(errs[kc:]) <= ACCURACY_LIMIT


def main():
    errs = _ekf_errors()
    kc = convergence_step(errs)
    print(f"收敛步 = {kc}（容差带 ±{TOL:.0%}）")
    print(f"全程 RMSE = {rmse(errs):.4f}  最大误差 = {max_error(errs):.4f}")
    print(f"收敛后 RMSE = {rmse(errs[kc:]):.4f}  最大误差 = {max_error(errs[kc:]):.4f}")
    print(f"精度判据（教学口径）= {ACCURACY_LIMIT:.0%} → "
          f"{'符合' if rmse(errs[kc:]) <= ACCURACY_LIMIT else '不符合'}")
    test_ch08()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
