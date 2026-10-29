# @AI_GENERATED
"""ch08 成组一致性与异常检测（标准库、可重复）。
保留木桶效应计算，并以中位数/MAD 对簇级 SOC 偏离评分；连续两帧越限才记录事件。
"""
from dataclasses import dataclass
from statistics import median
from typing import List, Sequence, Tuple

from soc_core import (CLUSTER_NOMINAL_ENERGY_KWH, GateConfig, PACK_SOC0, Quality,
                      Sample, StreamQualityGate, mean)

# [教学示例]：4 个代表性簇的相对 SOC；每簇能量采用统一 416 串对象口径。
SOC_MIN = 0.05
P_EACH_KW = 0.10
DT_H = 0.10
MAD_FLOOR = 0.01          # SOC：避免近乎一致时除以零
SCORE_THRESHOLD = 3.0     # 无量纲：偏离超过 3 个鲁棒尺度
CONFIRM_SAMPLES = 2       # 连续两帧才开事件，抑制单点噪声


@dataclass(frozen=True)
class GroupObservation:
    """一帧簇级 SOC 与同窗遥测；SOC 为 0–1，时间单位为秒。"""
    sample: Sample
    socs: Tuple[float, ...]


@dataclass(frozen=True)
class ScoreResult:
    center_soc: float
    mad_soc: float
    scores: Tuple[float, ...]


@dataclass(frozen=True)
class AnomalyEvent:
    event_id: str
    time_s: float
    cluster_index: int
    soc: float
    center_soc: float
    score: float
    reason: str
    action: str


def spread(socs: Sequence[float]) -> Tuple[float, float, float]:
    """返回极差、总体标准差、均值；用于木桶后果而非告警阈值。"""
    average = mean(socs)
    return max(socs) - min(socs), (
        sum((soc - average) ** 2 for soc in socs) / len(socs)) ** 0.5, average


def usable_by_min(socs: Sequence[float]) -> float:
    """kWh：均分放电的可用能量，由最低簇决定。"""
    return len(socs) * max(0.0, min(socs) - SOC_MIN) * CLUSTER_NOMINAL_ENERGY_KWH


def usable_by_mean(socs: Sequence[float]) -> float:
    """kWh：错误的平均 SOC 口径，用来量化木桶高估。"""
    _, _, average = spread(socs)
    return len(socs) * max(0.0, average - SOC_MIN) * CLUSTER_NOMINAL_ENERGY_KWH


def simulate() -> Tuple[float, List[float]]:
    """均分放电至最低簇触限，返回实际输出 kWh 和末态 SOC。"""
    socs = list(PACK_SOC0)
    delivered = 0.0
    while min(socs) > SOC_MIN + 1e-9:
        socs = [soc - P_EACH_KW * DT_H / CLUSTER_NOMINAL_ENERGY_KWH
                for soc in socs]
        delivered += P_EACH_KW * len(socs) * DT_H
    return delivered, socs


def score_observation(socs: Sequence[float]) -> ScoreResult:
    """以簇中位数为基线，用 |SOC-median| / max(MAD, floor) 评分。"""
    if len(socs) < 3 or any(not 0.0 <= soc <= 1.0 for soc in socs):
        raise ValueError("need at least three finite SOC values in [0, 1]")
    center = median(socs)
    mad = median([abs(soc - center) for soc in socs])
    scale = max(mad, MAD_FLOOR)
    return ScoreResult(center, mad, tuple(abs(soc - center) / scale for soc in socs))


def detect_events(observations: Sequence[GroupObservation]) -> Tuple[Tuple[AnomalyEvent, ...], Tuple[str, ...]]:
    """质量合格的连续越限才开事件；坏数据只留下降级记录，不驱动处置。"""
    gate = StreamQualityGate(GateConfig(expected_period_s=60.0, gap_factor=1.5))
    streaks: List[int] = []
    opened = set()
    events: List[AnomalyEvent] = []
    diagnostics: List[str] = []
    for observation in observations:
        quality = gate.check(observation.sample)
        if not streaks:
            streaks = [0] * len(observation.socs)
        if quality.quality is not Quality.GOOD:
            streaks = [0] * len(observation.socs)
            diagnostics.append(f"t={observation.sample.device_time_s:.0f}s 数据{quality.quality.value}，仅留痕/待复测")
            continue
        result = score_observation(observation.socs)
        for index, score in enumerate(result.scores):
            streaks[index] = streaks[index] + 1 if score >= SCORE_THRESHOLD else 0
            if streaks[index] == CONFIRM_SAMPLES and index not in opened:
                opened.add(index)
                events.append(AnomalyEvent(
                    f"GA-{observation.sample.seq:03d}-C{index + 1}",
                    observation.sample.device_time_s, index + 1, observation.socs[index],
                    result.center_soc, score, "SOC 偏离中位数连续越限",
                    "交 BMS 复核电压/温度；EMS 预留维护窗口并下调能力承诺"))
    return tuple(events), tuple(diagnostics)


def teaching_observations() -> Tuple[GroupObservation, ...]:
    """固定的 [教学示例]：第 4 簇连续偏低，最后一帧是无效遥测。"""
    rows = ((0, (0.60, 0.59, 0.58, 0.57), Quality.GOOD, 3.30),
            (60, (0.60, 0.59, 0.58, 0.51), Quality.GOOD, 3.30),
            (120, (0.60, 0.59, 0.58, 0.50), Quality.GOOD, 3.30),
            (180, (0.60, 0.59, 0.58, 0.49), Quality.INVALID, 4.50))
    return tuple(GroupObservation(
        Sample(index, time_s, time_s + 0.1, time_s + 0.1, 0.0, voltage, 25.0, quality), socs)
        for index, (time_s, socs, quality, voltage) in enumerate(rows))


def test_ch08() -> None:
    assert usable_by_mean(PACK_SOC0) > usable_by_min(PACK_SOC0)
    delivered, _ = simulate()
    assert abs(delivered - usable_by_min(PACK_SOC0)) < 0.05 * usable_by_min(PACK_SOC0)
    rng, _, average = spread(PACK_SOC0)
    assert abs(rng - 0.15) < 1e-9 and abs(average - 0.545) < 1e-9
    events, diagnostics = detect_events(teaching_observations())
    assert len(events) == 1 and events[0].cluster_index == 4 and events[0].score > SCORE_THRESHOLD
    assert len(diagnostics) == 1 and "invalid" in diagnostics[0]


def main() -> None:
    rng, std, average = spread(PACK_SOC0)
    print(f"木桶基线：极差 {rng:.1%}，标准差 {std:.2%}，均值 {average:.1%}")
    print(f"可放：最低簇 {usable_by_min(PACK_SOC0):.3f} kWh；平均口径 {usable_by_mean(PACK_SOC0):.3f} kWh")
    events, diagnostics = detect_events(teaching_observations())
    for event in events:
        print(f"事件 {event.event_id}：簇{event.cluster_index} score={event.score:.1f}，{event.action}")
    for diagnostic in diagnostics:
        print(f"降级：{diagnostic}")
    test_ch08()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
