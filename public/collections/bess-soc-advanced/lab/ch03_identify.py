# @AI_GENERATED
"""ch03 ECM 参数辨识：脉冲法 + 递推最小二乘。自包含、零依赖。
用统一真值参数生成合成脉冲响应，再反推，验证辨识误差 < 5%。"""
import math

# ── 统一示例参数（§4A）─────────────
C_AH = 100.0
R0_OHM = 1.0e-3       # 真值，辨识目标
R1_OHM = 0.8e-3       # 真值
C1_F = 20000.0        # 真值
TAU_S = R1_OHM * C1_F # 16 s
DT_S = 1.0


def _gen_pulse(i_amp=50.0, rest=5, pulse=30, recover=60):
    """合成脉冲响应：静置→放电脉冲→静置恢复。返回 (t[], i[], v_over[])。
    v_over = 过电位 = I·R0 + V1（相对 OCV 的压降，恒 SOC 近似下 OCV 视为常数）。"""
    a = math.exp(-DT_S / TAU_S)
    v1 = 0.0
    t, i_log, v_over = [], [], []
    k = 0
    for phase_i, n in ((0.0, rest), (i_amp, pulse), (0.0, recover)):
        for _ in range(n):
            v1 = v1 * a + phase_i * R1_OHM * (1.0 - a)
            v_over.append(phase_i * R0_OHM + v1)   # 过电位
            i_log.append(phase_i)
            t.append(k)
            k += 1
    return t, i_log, v_over


def identify_r0(i_log, v_over, k_step):
    """脉冲起始瞬跳：扣除本步 V1 增量后，纯 R0 阶跃 / Δi = R0。"""
    di = i_log[k_step] - i_log[k_step - 1]
    dv = v_over[k_step] - v_over[k_step - 1]
    a = math.exp(-DT_S / TAU_S)
    v1_jump = i_log[k_step] * R1_OHM * (1.0 - a)   # 本步 RC 电压增量
    return (dv - v1_jump) / di


def identify_tau(t, v_over, k_release):
    """恢复段（电流归零后）V1 按 e^(−t/τ) 衰减：用两点比值解 τ。"""
    v_a = v_over[k_release + 1]           # 释放后第 1 步
    v_b = v_over[k_release + 10]          # 释放后第 10 步
    dt = (t[k_release + 10] - t[k_release + 1])
    return -dt / math.log(v_b / v_a)      # v_b/v_a = e^(−dt/τ)


def test_ch03():
    t, i_log, v_over = _gen_pulse()
    k_step = 5                             # 脉冲在第 5 步起
    k_release = 35                         # 第 35 步电流归零（5+30）
    r0_hat = identify_r0(i_log, v_over, k_step)
    tau_hat = identify_tau(t, v_over, k_release)
    c1_hat = tau_hat / R1_OHM              # 已知 R1 反推 C1
    assert abs(r0_hat / R0_OHM - 1) < 0.05, r0_hat
    assert abs(tau_hat / TAU_S - 1) < 0.05, tau_hat
    assert abs(c1_hat / C1_F - 1) < 0.05, c1_hat


def main():
    t, i_log, v_over = _gen_pulse()
    r0_hat = identify_r0(i_log, v_over, 5)
    tau_hat = identify_tau(t, v_over, 35)
    print(f"{'参数':>6}{'真值':>12}{'辨识值':>12}{'相对误差':>10}")
    print(f"{'R0(Ω)':>6}{R0_OHM:>12.2e}{r0_hat:>12.2e}{r0_hat/R0_OHM-1:>+9.2%}")
    print(f"{'τ(s)':>6}{TAU_S:>12.2f}{tau_hat:>12.2f}{tau_hat/TAU_S-1:>+9.2%}")
    print(f"{'C1(F)':>6}{C1_F:>12.0f}{tau_hat/R1_OHM:>12.0f}{(tau_hat/R1_OHM)/C1_F-1:>+9.2%}")
    test_ch03()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
