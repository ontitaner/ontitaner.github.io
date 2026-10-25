# @AI_GENERATED
"""ch01 等效电路模型（1-RC Thevenin）合成真值电池。

自包含、零依赖：python3 ch01_ecm_pulse.py 直跑看追踪表与"自检通过"；
pytest lab/ 收集 test_ch01。
"""
import math

# ── 统一示例参数（§4A，全教程通用，每篇照抄）─────────────
C_AH = 100.0          # 额定容量 Ah
R0_OHM = 1.0e-3       # 欧姆内阻 Ω
R1_OHM = 0.8e-3       # 极化电阻 Ω
C1_F = 20000.0        # 极化电容 F
TAU_S = R1_OHM * C1_F # τ = 16 s
DT_S = 1.0            # 采样周期 s
OCV_SOC = (0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00)
OCV_V   = (2.90, 3.10, 3.20, 3.25, 3.275, 3.29, 3.30, 3.31, 3.325, 3.33, 3.34, 3.36, 3.45)


def interp(x, xs, ys):
    """分段线性插值；表外取端点。"""
    if x <= xs[0]:
        return ys[0]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            return ys[i - 1] + (x - xs[i - 1]) / (xs[i] - xs[i - 1]) * (ys[i] - ys[i - 1])
    return ys[-1]


def ocv_from_soc(soc):
    return interp(soc, OCV_SOC, OCV_V)


def ecm_step(soc, v1, current_a, dt_s=DT_S,
             c_ah=C_AH, r0=R0_OHM, r1=R1_OHM, tau_s=TAU_S):
    """推进一步 1-RC 模型。current_a 放电为正。返回 (v_terminal, soc_next, v1_next)。"""
    a = math.exp(-dt_s / tau_s)
    v1_next = v1 * a + current_a * r1 * (1.0 - a)        # RC 极化电压递推
    soc_next = soc - current_a * dt_s / (3600.0 * c_ah)  # 安时积分
    v_terminal = ocv_from_soc(soc) - current_a * r0 - v1 # 端电压（用本步 soc/v1）
    return v_terminal, soc_next, v1_next


def simulate(current_profile, soc0, dt_s=DT_S):
    """给定电流序列，输出真值轨迹 (soc_true[], i[], v_terminal[])。"""
    soc, v1 = soc0, 0.0
    soc_log, v_log = [], []
    for i_a in current_profile:
        v_t, soc, v1 = ecm_step(soc, v1, i_a, dt_s)
        soc_log.append(soc)
        v_log.append(v_t)
    return soc_log, list(current_profile), v_log


def test_ch01():
    # 结论 1：对恒定放电阶跃，经 τ 秒（16 步）V1 达稳态 I·R1 的 63.2%
    i_step = 50.0  # 0.5C 放电（50 A on 100 Ah）
    v1 = 0.0
    for _ in range(int(TAU_S / DT_S)):           # 16 步 = 1 个 τ
        _, _, v1 = ecm_step(0.5, v1, i_step)
    v1_steady = i_step * R1_OHM                   # = 0.04 V
    assert abs(v1 / v1_steady - 0.632) < 0.01, (v1, v1_steady)
    # 结论 2：静置（I=0）时端电压 = OCV（无 R0 压降、V1 衰减）
    v_t, _, _ = ecm_step(0.5, 0.0, 0.0)
    assert abs(v_t - ocv_from_soc(0.5)) < 1e-12


def main():
    # 教学剖面：静置 5 s → 0.5C 放电脉冲 20 s → 静置恢复
    profile = [0.0] * 5 + [50.0] * 20 + [0.0] * 20
    soc_log, i_log, v_log = simulate(profile, soc0=0.50)
    print(f"{'步':>3}{'I(A)':>7}{'SOC':>9}{'V_t(V)':>9}")
    for k in (0, 4, 5, 6, 10, 24, 25, 30, 44):
        print(f"{k:>3}{i_log[k]:>7.1f}{soc_log[k]:>9.4f}{v_log[k]:>9.4f}")
    test_ch01()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
