# @AI_GENERATED
"""ch07 被动均衡 vs 主动均衡仿真。自包含、零依赖。
被动：泄放电阻耗散高单体多余电荷（能量变热）；主动：高→低单体电荷转移（仅转移损耗）。
两者都把 SOC 极差收敛到阈值以下，被动总能量损耗明显更大。"""

# ── 统一示例参数（§4A）─────────────
PACK_SOC0 = [0.60, 0.58, 0.55, 0.45]
CAP_AH_EACH = 100.0
V_NOMINAL = 3.2
START_THRESHOLD = 0.02     # 极差 > 2% 启动均衡
BAL_CURRENT_A = 5.0        # 均衡电流幅值（A）
DT_H = 0.5                 # 步长 h
ACTIVE_EFF = 0.90          # 主动均衡转移效率


def spread(socs):
    return max(socs) - min(socs)


def passive_step(socs):
    """被动：对高于 (min+阈值) 的单体泄放，电荷变热耗散。返回本步耗散能量 kWh。"""
    lo = min(socs)
    dissipated_kwh = 0.0
    dsoc = BAL_CURRENT_A * DT_H / CAP_AH_EACH    # 本步泄放的 SOC 量
    for i, s in enumerate(socs):
        if s > lo + START_THRESHOLD:
            drop = min(dsoc, s - lo)             # 不低于当前最低
            socs[i] = s - drop
            dissipated_kwh += drop * CAP_AH_EACH * V_NOMINAL / 1000.0
    return dissipated_kwh


def active_step(socs):
    """主动：最高单体电荷转移到最低单体，转移效率 ACTIVE_EFF。返回本步损耗能量 kWh。"""
    hi = max(range(len(socs)), key=lambda i: socs[i])
    lo = min(range(len(socs)), key=lambda i: socs[i])
    if socs[hi] - socs[lo] <= START_THRESHOLD:
        return 0.0
    dsoc = min(BAL_CURRENT_A * DT_H / CAP_AH_EACH, (socs[hi] - socs[lo]) / 2)
    socs[hi] -= dsoc                              # 高单体放出 dsoc
    socs[lo] += dsoc * ACTIVE_EFF                 # 低单体收到 dsoc·η，差额为损耗
    loss_kwh = dsoc * (1 - ACTIVE_EFF) * CAP_AH_EACH * V_NOMINAL / 1000.0
    return loss_kwh


def run(step_fn, max_steps=2000):
    """反复均衡到极差 ≤ 阈值。返回 (步数, 总损耗 kWh, 末态极差)。"""
    socs = list(PACK_SOC0)
    total_loss, steps = 0.0, 0
    while spread(socs) > START_THRESHOLD and steps < max_steps:
        total_loss += step_fn(socs)
        steps += 1
    return steps, total_loss, spread(socs)


def test_ch07():
    s_p, loss_p, rng_p = run(passive_step)
    s_a, loss_a, rng_a = run(active_step)
    # 两者都收敛到阈值以下
    assert rng_p <= START_THRESHOLD + 1e-9 and rng_a <= START_THRESHOLD + 1e-9
    # 被动总损耗 > 主动（能量全耗散 vs 仅转移损耗）
    assert loss_p > loss_a, (loss_p, loss_a)


def main():
    s_p, loss_p, rng_p = run(passive_step)
    s_a, loss_a, rng_a = run(active_step)
    print(f"{'方式':>6}{'步数':>6}{'总损耗(kWh)':>13}{'末态极差':>10}")
    print(f"{'被动':>6}{s_p:>6}{loss_p:>13.5f}{rng_p:>10.2%}")
    print(f"{'主动':>6}{s_a:>6}{loss_a:>13.5f}{rng_a:>10.2%}")
    print(f"被动/主动 损耗比 ≈ {loss_p / max(loss_a, 1e-12):.1f}×")
    test_ch07()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
