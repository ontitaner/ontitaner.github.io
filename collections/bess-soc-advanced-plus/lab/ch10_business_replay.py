# @AI_GENERATED
"""第 10 章固定教学工况的业务回放与证据报告（仅标准库）。

本模块冻结教学输入、配置/参数版本、算法版本及随机种子；它将第 07 章
“风险化能力下界”的语义，接到一项 2 MW、30 min 晚峰放电计划的计划/实际
对照上。输出只形成教学结论，不构成现场验收或标准符合性声明。
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Tuple

from soc_core import PCS_RATED_KW, SITE_NOMINAL_ENERGY_KWH


@dataclass(frozen=True)
class ReplayConfig:
    """冻结的配置、参数和生成信息；所有数值都是教学示例。"""

    replay_id: str = "ch10-evening-peak-001"
    configuration_version: str = "teaching-dispatch-config-v1.0"
    capability_parameter_version: str = "soe-sop-teaching-params-v1.0"
    algorithm_version: str = "business-replay-v1.0"
    random_seed: int = 20241010
    duration_s: int = 1800
    planned_power_kw: float = 2000.0
    teaching_soc_accuracy_limit: float = 0.05
    convergence_tolerance: float = 0.02


@dataclass(frozen=True)
class ReplaySample:
    """一个冻结的 300 s 教学采样区间；放电功率为正。"""

    start_s: int
    estimated_soc: float
    soc_lower_bound: float
    available_power_kw: float
    available_energy_kwh: float
    actual_power_kw: float
    quality: str = "good"
    limitation: str = "minimum_cluster_energy_bound"


@dataclass(frozen=True)
class ReplayReport:
    """可打印、可比较的教学回放证据。"""

    metadata: Tuple[Tuple[str, object], ...]
    plan_power_kw: float
    plan_energy_kwh: float
    minimum_available_power_kw: float
    minimum_available_energy_kwh: float
    actual_energy_kwh: float
    power_deviation_kw: float
    energy_deviation_kwh: float
    quality_ok: bool
    limitations: Tuple[str, ...]
    teaching_conclusion: str
    rmse: float
    max_error: float
    convergence_step: int
    teaching_accuracy_example_passed: bool


REPLAY_CONFIG = ReplayConfig()
# 六段各 300 s 的冻结输入；并非现场遥测或标准测试数据。
REPLAY_SAMPLES: Tuple[ReplaySample, ...] = (
    ReplaySample(0, 0.465, 0.420, 1850.0, 930.0, 1850.0),
    ReplaySample(300, 0.451, 0.406, 1850.0, 930.0, 1850.0),
    ReplaySample(600, 0.437, 0.392, 1850.0, 930.0, 1850.0),
    ReplaySample(900, 0.423, 0.378, 1850.0, 930.0, 1850.0),
    ReplaySample(1200, 0.409, 0.364, 1850.0, 930.0, 1850.0),
    ReplaySample(1500, 0.395, 0.350, 1850.0, 930.0, 1850.0),
)
# 冻结的合成估计误差（单位 SOC），用于保留初学者的三个指标练习。
ESTIMATION_ERRORS = (0.1269, 0.0710, 0.0310, 0.0190, 0.0080, 0.0080, 0.0080, 0.0070)


def rmse(errors: Tuple[float, ...]) -> float:
    """均方根误差；errors 为无量纲 SOC 误差。"""
    if not errors:
        raise ValueError("误差序列不能为空")
    return (sum(error * error for error in errors) / len(errors)) ** 0.5


def max_error(errors: Tuple[float, ...]) -> float:
    """误差序列的最大绝对误差。"""
    if not errors:
        raise ValueError("误差序列不能为空")
    return max(abs(error) for error in errors)


def convergence_step(errors: Tuple[float, ...], tolerance: float) -> int:
    """首次进入容差带且之后持续保持的下标；不能收敛时返回 -1。"""
    for index in range(len(errors)):
        if all(abs(error) <= tolerance for error in errors[index:]):
            return index
    return -1


def _quality_reasons(samples: Tuple[ReplaySample, ...]) -> Tuple[str, ...]:
    reasons = []
    expected_starts = tuple(range(0, REPLAY_CONFIG.duration_s, 300))
    if tuple(sample.start_s for sample in samples) != expected_starts:
        reasons.append("frozen_input_timebase_mismatch")
    if any(sample.quality != "good" for sample in samples):
        reasons.append("telemetry_quality_not_good")
    if any(sample.actual_power_kw > sample.available_power_kw for sample in samples):
        reasons.append("actual_power_exceeds_capability")
    return tuple(reasons)


def build_replay_report(samples: Tuple[ReplaySample, ...] = REPLAY_SAMPLES) -> ReplayReport:
    """从冻结输入生成计划、能力、实际执行、偏差与教学结论。"""
    reasons = _quality_reasons(samples)
    errors = ESTIMATION_ERRORS
    convergence = convergence_step(errors, REPLAY_CONFIG.convergence_tolerance)
    steady_errors = errors[convergence:] if convergence >= 0 else errors
    plan_energy_kwh = REPLAY_CONFIG.planned_power_kw * REPLAY_CONFIG.duration_s / 3600.0
    actual_energy_kwh = sum(sample.actual_power_kw * 300.0 / 3600.0 for sample in samples)
    minimum_power_kw = min(sample.available_power_kw for sample in samples)
    minimum_energy_kwh = min(sample.available_energy_kwh for sample in samples)
    limitations = tuple(sorted({sample.limitation for sample in samples}))
    if reasons:
        conclusion = "数据质量拒绝：不输出教学履约结论。"
    elif actual_energy_kwh >= plan_energy_kwh and minimum_power_kw >= REPLAY_CONFIG.planned_power_kw:
        conclusion = "教学结论：该冻结工况完成了计划；不构成现场验收或标准符合性结论。"
    else:
        conclusion = (
            "教学结论：该冻结工况未完成 2 MW × 30 min 计划；"
            "最低簇能量下界限制为 1.85 MW、0.93 MWh。"
        )
    metadata = tuple(sorted(asdict(REPLAY_CONFIG).items()))
    return ReplayReport(
        metadata=metadata,
        plan_power_kw=REPLAY_CONFIG.planned_power_kw,
        plan_energy_kwh=plan_energy_kwh,
        minimum_available_power_kw=minimum_power_kw,
        minimum_available_energy_kwh=minimum_energy_kwh,
        actual_energy_kwh=actual_energy_kwh,
        power_deviation_kw=minimum_power_kw - REPLAY_CONFIG.planned_power_kw,
        energy_deviation_kwh=actual_energy_kwh - plan_energy_kwh,
        quality_ok=not reasons,
        limitations=limitations + reasons,
        teaching_conclusion=conclusion,
        rmse=rmse(steady_errors),
        max_error=max_error(steady_errors),
        convergence_step=convergence,
        teaching_accuracy_example_passed=(
            max_error(steady_errors) <= REPLAY_CONFIG.teaching_soc_accuracy_limit
        ),
    )


def print_report(report: ReplayReport) -> None:
    """以固定字段顺序输出可复制的教学证据报告。"""
    print("第10章 教学业务回放报告")
    print("输入与版本:")
    for key, value in report.metadata:
        print(f"  {key} = {value}")
    print("计划与实际/可交付量对比 [教学示例]:")
    print(f"  计划: {report.plan_power_kw:.0f} kW × 30 min = {report.plan_energy_kwh:.0f} kWh")
    print(f"  能力下界: {report.minimum_available_power_kw:.0f} kW, "
          f"{report.minimum_available_energy_kwh:.0f} kWh")
    print(f"  实际: {report.actual_energy_kwh:.0f} kWh")
    print(f"  功率偏差: {report.power_deviation_kw:.0f} kW; "
          f"能量偏差: {report.energy_deviation_kwh:.0f} kWh")
    print(f"数据质量: {'good' if report.quality_ok else 'rejected'}")
    print("限制原因: " + ", ".join(report.limitations))
    print("入门估计指标 [教学示例]:")
    print(f"  收敛步 = {report.convergence_step}（容差带 ±{REPLAY_CONFIG.convergence_tolerance:.0%}）")
    print(f"  收敛后 RMSE = {report.rmse:.4f}; 最大误差 = {report.max_error:.4f}")
    print(f"  5% 门限教学示例: {'通过' if report.teaching_accuracy_example_passed else '未通过'}，非 GB/T 或合同判定")
    print(report.teaching_conclusion)


def test_ch10_fixed_replay_is_repeatable() -> None:
    first = build_replay_report()
    second = build_replay_report()
    assert first == second
    assert dict(first.metadata)["random_seed"] == 20241010


def test_ch10_reports_shortfall_and_limitation() -> None:
    report = build_replay_report()
    assert report.quality_ok
    assert abs(report.actual_energy_kwh - 925.0) < 1e-9
    assert abs(report.energy_deviation_kwh + 75.0) < 1e-9
    assert abs(report.power_deviation_kw + 150.0) < 1e-9
    assert "minimum_cluster_energy_bound" in report.limitations
    assert "未完成" in report.teaching_conclusion


def test_ch10_rejects_invalid_quality() -> None:
    invalid = (replace(REPLAY_SAMPLES[0], quality="invalid"),) + REPLAY_SAMPLES[1:]
    report = build_replay_report(invalid)
    assert not report.quality_ok
    assert "telemetry_quality_not_good" in report.limitations
    assert report.teaching_conclusion.startswith("数据质量拒绝")


def test_ch10_keeps_beginner_error_metrics() -> None:
    report = build_replay_report()
    assert report.convergence_step == 3
    assert round(report.rmse, 5) == 0.01097
    assert report.max_error == 0.019
    assert report.teaching_accuracy_example_passed


def main() -> None:
    report = build_replay_report()
    print_report(report)
    test_ch10_fixed_replay_is_repeatable()
    test_ch10_reports_shortfall_and_limitation()
    test_ch10_rejects_invalid_quality()
    test_ch10_keeps_beginner_error_metrics()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
