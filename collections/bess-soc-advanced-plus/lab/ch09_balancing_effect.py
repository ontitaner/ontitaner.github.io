# @AI_GENERATED
"""ch09 均衡效果评估与运维闭环（标准库、可重复）。
BMS 执行均衡与保护；EMS 只预留空闲窗口、消费结论，不能绕过 BMS 单体控制。
"""
from dataclasses import dataclass
from typing import Callable, Sequence, Tuple

from soc_core import CELL_CAPACITY_AH, CLUSTER_NOMINAL_ENERGY_KWH, PACK_SOC0, Quality

SOC_MIN = 0.05
START_THRESHOLD = 0.02
BAL_CURRENT_A = 5.0       # [教学示例] A
DT_H = 0.5                # [教学示例] h
ACTIVE_EFF = 0.90


@dataclass(frozen=True)
class BalancingRun:
    mode: str
    steps: int
    loss_kwh: float
    final_socs: Tuple[float, ...]
    final_spread: float
    converged: bool


@dataclass(frozen=True)
class OperationWindow:
    """冻结的复测工况；SOC 是簇级，温度 °C、电流 A、静置时间 s。"""
    label: str
    socs: Tuple[float, ...]
    temperature_c: float
    current_a: float
    rest_s: float
    bms_parameter_version: str
    ems_window_id: str
    quality: Quality = Quality.GOOD


@dataclass(frozen=True)
class EffectReview:
    comparable: bool
    status: str
    reasons: Tuple[str, ...]
    spread_before: float
    spread_after: float
    capability_before_kwh: float
    capability_after_kwh: float
    capability_gain_kwh: float


@dataclass(frozen=True)
class ClosureStep:
    stage: str
    owner: str
    result: str


def spread(socs: Sequence[float]) -> float:
    return max(socs) - min(socs)


def usable_by_min(socs: Sequence[float]) -> float:
    """kWh：同一放电方向与 SOC 下限下，最低簇决定的可用能量。"""
    return len(socs) * max(0.0, min(socs) - SOC_MIN) * CLUSTER_NOMINAL_ENERGY_KWH


def passive_step(socs: list) -> float:
    """BMS 被动均衡：削高为热；返回本步耗散 kWh。"""
    low = min(socs)
    dsoc = BAL_CURRENT_A * DT_H / CELL_CAPACITY_AH
    loss_kwh = 0.0
    for index, soc in enumerate(socs):
        if soc > low + START_THRESHOLD:
            drop = min(dsoc, soc - low)
            socs[index] = soc - drop
            loss_kwh += drop * CLUSTER_NOMINAL_ENERGY_KWH
    return loss_kwh


def active_step(socs: list) -> float:
    """BMS 主动均衡：最高簇向最低簇转移；返回转换损耗 kWh。"""
    high = max(range(len(socs)), key=lambda index: socs[index])
    low = min(range(len(socs)), key=lambda index: socs[index])
    if socs[high] - socs[low] <= START_THRESHOLD:
        return 0.0
    moved = min(BAL_CURRENT_A * DT_H / CELL_CAPACITY_AH, (socs[high] - socs[low]) / 2)
    socs[high] -= moved
    socs[low] += moved * ACTIVE_EFF
    return moved * (1.0 - ACTIVE_EFF) * CLUSTER_NOMINAL_ENERGY_KWH


def run(mode: str, step_fn: Callable[[list], float], initial_socs: Sequence[float] = PACK_SOC0,
        max_steps: int = 2000) -> BalancingRun:
    """执行至阈值或步数上限；未收敛必须保留为待复核，而不是伪装为成功。"""
    socs = list(initial_socs)
    loss_kwh = 0.0
    steps = 0
    while spread(socs) > START_THRESHOLD and steps < max_steps:
        loss_kwh += step_fn(socs)
        steps += 1
    final_spread = spread(socs)
    return BalancingRun(mode, steps, loss_kwh, tuple(socs), final_spread,
                        final_spread <= START_THRESHOLD + 1e-9)


def comparable(before: OperationWindow, after: OperationWindow) -> Tuple[bool, Tuple[str, ...]]:
    """只在同一静置/温度/配置与数据质量条件下比较，避免把工况差当效果。"""
    reasons = []
    if before.quality is not Quality.GOOD or after.quality is not Quality.GOOD:
        reasons.append("数据质量非 good")
    if abs(before.temperature_c - after.temperature_c) > 2.0:
        reasons.append("温差超过 2°C")
    if abs(before.current_a) > 5.0 or abs(after.current_a) > 5.0:
        reasons.append("非低负荷/静置复测")
    if min(before.rest_s, after.rest_s) < 1800.0:
        reasons.append("静置不足 1800 s")
    if before.bms_parameter_version != after.bms_parameter_version:
        reasons.append("BMS 参数版本不同")
    if before.ems_window_id != after.ems_window_id:
        reasons.append("EMS 维护窗口不同")
    return not reasons, tuple(reasons)


def evaluate_effect(before: OperationWindow, after: OperationWindow, run_result: BalancingRun) -> EffectReview:
    """输出可关闭、继续观察或待复测的运维判定，不直接下发单体均衡命令。"""
    ok, reasons = comparable(before, after)
    cap_before = usable_by_min(before.socs)
    cap_after = usable_by_min(after.socs)
    if not ok:
        status = "待复测"
    elif not run_result.converged:
        status = "继续处置"
        reasons += ("达到最大均衡步数仍未收敛",)
    elif spread(after.socs) < spread(before.socs) and cap_after > cap_before:
        status = "可关闭"
    else:
        status = "继续处置"
        reasons += ("极差或最低簇能力未改善",)
    return EffectReview(ok, status, reasons, spread(before.socs), spread(after.socs),
                        cap_before, cap_after, cap_after - cap_before)


def build_closure(alarm_id: str, review: EffectReview) -> Tuple[ClosureStep, ...]:
    """告警→BMS 处置→同工况复测→EMS 关闭/保留工单的最小审计链。"""
    close_result = ("关闭 " + alarm_id + "；恢复经批准的能力计划"
                    if review.status == "可关闭" else "保留 " + alarm_id + "；安排复测或升级工单")
    return (
        ClosureStep("告警", "BMS", f"记录 {alarm_id}：簇级离散超过阈值"),
        ClosureStep("处置", "BMS", "仅在保护条件允许时执行均衡；EMS 不直接驱动单体通道"),
        ClosureStep("复测", "BMS", f"同工况复测：极差 {review.spread_before:.1%}→{review.spread_after:.1%}"),
        ClosureStep("关闭", "EMS", close_result),
    )


def teaching_case() -> Tuple[BalancingRun, EffectReview, Tuple[ClosureStep, ...]]:
    """固定 [教学示例]：第 08 章异常 GA-002-C4 的主动均衡闭环。"""
    before = OperationWindow("before", tuple(PACK_SOC0), 25.0, 0.0, 1800.0,
                             "bms-bal-v1", "ems-idle-001")
    result = run("主动", active_step)
    after = OperationWindow("after", result.final_socs, 25.5, 0.0, 1800.0,
                            "bms-bal-v1", "ems-idle-001")
    review = evaluate_effect(before, after, result)
    return result, review, build_closure("GA-002-C4", review)


def test_ch09() -> None:
    passive = run("被动", passive_step)
    active = run("主动", active_step)
    assert passive.converged and active.converged
    assert passive.loss_kwh > active.loss_kwh
    _, review, closure = teaching_case()
    assert review.status == "可关闭" and review.capability_gain_kwh > 0.0
    assert [step.stage for step in closure] == ["告警", "处置", "复测", "关闭"]
    bad_before = OperationWindow("bad", tuple(PACK_SOC0), 20.0, 20.0, 0.0,
                                 "old", "other", Quality.SUSPECT)
    assert evaluate_effect(bad_before, bad_before, active).status == "待复测"
    assert not run("受限", active_step, max_steps=1).converged


def main() -> None:
    passive = run("被动", passive_step)
    active, review, closure = teaching_case()
    print(f"被动：{passive.steps} 步，损耗 {passive.loss_kwh:.5f} kWh，极差 {passive.final_spread:.2%}")
    print(f"主动：{active.steps} 步，损耗 {active.loss_kwh:.5f} kWh，极差 {active.final_spread:.2%}")
    print(f"同工况能力：{review.capability_before_kwh:.3f}→{review.capability_after_kwh:.3f} kWh，判定 {review.status}")
    for step in closure:
        print(f"{step.stage}/{step.owner}：{step.result}")
    test_ch09()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
