# @AI_GENERATED
"""Shared, standard-library-only foundation for the BESS SOC course.

The module owns units, timing, quality, lookup, simulation, and identification
primitives. Chapter labs import this file instead of copying implementations.
All voltage-model calculations use a representative 314 Ah LFP cell. Site
constants describe 416 cells in series, 12 parallel clusters, and a 2.5 MW PCS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
import random
from typing import Dict, Iterable, Mapping, Optional, Sequence, Tuple

# Site and representative-cell teaching constants. These are examples, not limits.
CELL_CAPACITY_AH = 314.0
SERIES_CELLS = 416
PARALLEL_CLUSTERS = 12
NOMINAL_CELL_V = 3.2
SITE_NOMINAL_ENERGY_KWH = (
    CELL_CAPACITY_AH * NOMINAL_CELL_V * SERIES_CELLS * PARALLEL_CLUSTERS / 1000.0
)
PCS_RATED_KW = 2500.0
# A physical cluster is one 416-series string; 12 clusters form the teaching site.
CLUSTER_NOMINAL_ENERGY_KWH = (
    CELL_CAPACITY_AH * NOMINAL_CELL_V * SERIES_CELLS / 1000.0
)
DEFAULT_DT_S = 1.0
DEFAULT_CHARGE_EFFICIENCY = 0.995

# Compatibility aliases retained for later course chapters.
C_AH = CELL_CAPACITY_AH
DT_S = DEFAULT_DT_S
SOC0_TRUE = 0.50
SOC0_EST = 0.70
PACK_C_AH = CELL_CAPACITY_AH
PACK_SOC0 = (0.60, 0.58, 0.55, 0.45)

# Mean LFP OCV teaching tables, layered by temperature. Values are illustrative.
OCV_SOC = (0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50,
           0.60, 0.70, 0.80, 0.90, 0.95, 1.00)
OCV_V_25C = (2.90, 3.10, 3.20, 3.25, 3.275, 3.29, 3.30,
             3.31, 3.325, 3.33, 3.34, 3.36, 3.45)
OCV_V = OCV_V_25C
OCV_TABLES = {
    -10.0: tuple(v - 0.018 for v in OCV_V_25C),
    25.0: OCV_V_25C,
    45.0: tuple(v + 0.004 for v in OCV_V_25C),
}
HYSTERESIS_HALF_BAND_V = 0.006
RELAXATION_TAU_S = 1800.0


class Quality(str, Enum):
    """Usability of one sample for state estimation."""

    GOOD = "good"
    SUSPECT = "suspect"
    INVALID = "invalid"


@dataclass(frozen=True)
class Sample:
    """One normalized telemetry snapshot.

    monotonic_time_s is the local monotonic clock used for ordering and dt.
    device_time_s and receive_time_s remain available for delay diagnostics.
    Current is positive while discharging and negative while charging.
    """

    seq: int
    device_time_s: float
    receive_time_s: float
    monotonic_time_s: float
    current_a: float
    voltage_v: float
    temperature_c: float
    source_quality: Quality = Quality.GOOD


@dataclass(frozen=True)
class QualityResult:
    sample: Sample
    quality: Quality
    reasons: Tuple[str, ...] = ()

    @property
    def usable(self) -> bool:
        return self.quality is not Quality.INVALID


@dataclass(frozen=True)
class GateConfig:
    expected_period_s: float = 1.0
    gap_factor: float = 1.5
    max_transport_delay_s: float = 2.0
    min_current_a: float = -1000.0
    max_current_a: float = 1000.0
    min_voltage_v: float = 2.0
    max_voltage_v: float = 4.0
    min_temperature_c: float = -40.0
    max_temperature_c: float = 80.0
    frozen_repeat_limit: int = 3


class StreamQualityGate:
    """Stateful ordering, range, gap, delay, and exact-freeze gate."""

    def __init__(self, config: GateConfig = GateConfig()) -> None:
        if config.expected_period_s <= 0 or config.gap_factor <= 1:
            raise ValueError("invalid gate timing configuration")
        self.config = config
        self._previous: Optional[Sample] = None
        self._frozen_repeats = 0

    def check(self, sample: Sample) -> QualityResult:
        reasons = []
        invalid = sample.source_quality is Quality.INVALID
        suspect = sample.source_quality is Quality.SUSPECT
        values = (sample.device_time_s, sample.receive_time_s,
                  sample.monotonic_time_s, sample.current_a,
                  sample.voltage_v, sample.temperature_c)
        if not all(math.isfinite(v) for v in values):
            reasons.append("non_finite")
            invalid = True
        if not invalid:
            c = self.config
            if not c.min_current_a <= sample.current_a <= c.max_current_a:
                reasons.append("current_out_of_range")
                invalid = True
            if not c.min_voltage_v <= sample.voltage_v <= c.max_voltage_v:
                reasons.append("voltage_out_of_range")
                invalid = True
            if not c.min_temperature_c <= sample.temperature_c <= c.max_temperature_c:
                reasons.append("temperature_out_of_range")
                invalid = True
            delay = sample.receive_time_s - sample.device_time_s
            if delay < 0 or delay > c.max_transport_delay_s:
                reasons.append("late_or_clock_mismatch")
                suspect = True

        previous = self._previous
        if previous is not None and not invalid:
            if sample.seq <= previous.seq or sample.device_time_s <= previous.device_time_s:
                reasons.append("duplicate_or_late_device_sample")
                invalid = True
            if sample.monotonic_time_s <= previous.monotonic_time_s:
                reasons.append("non_monotonic_local_time")
                invalid = True
            else:
                gap = sample.monotonic_time_s - previous.monotonic_time_s
                if gap > self.config.expected_period_s * self.config.gap_factor:
                    reasons.append("missing_interval")
                    suspect = True
            if sample.seq > previous.seq + 1:
                reasons.append("missing_sequence")
                suspect = True
            same_payload = (
                sample.current_a == previous.current_a
                and sample.voltage_v == previous.voltage_v
                and sample.temperature_c == previous.temperature_c
            )
            self._frozen_repeats = self._frozen_repeats + 1 if same_payload else 0
            if self._frozen_repeats >= self.config.frozen_repeat_limit:
                reasons.append("frozen_payload")
                suspect = True
        elif previous is None:
            self._frozen_repeats = 0

        # Keep the last finite, ordered arrival as stream context. An out-of-range
        # payload still advances sequence; a duplicate does not.
        if all(math.isfinite(v) for v in values):
            if previous is None or (sample.seq > previous.seq and
                                    sample.monotonic_time_s > previous.monotonic_time_s):
                self._previous = sample
        quality = Quality.INVALID if invalid else Quality.SUSPECT if suspect else Quality.GOOD
        return QualityResult(sample, quality, tuple(dict.fromkeys(reasons)))


@dataclass(frozen=True)
class TimedValue:
    monotonic_time_s: float
    value: float


def align_to_window(channels: Mapping[str, Sequence[TimedValue]], anchor_s: float,
                    max_skew_s: float) -> Dict[str, TimedValue]:
    """Select each channel's nearest finite value within one sample window."""
    if max_skew_s < 0 or not math.isfinite(anchor_s):
        raise ValueError("invalid alignment window")
    aligned: Dict[str, TimedValue] = {}
    for name, values in channels.items():
        finite = [item for item in values
                  if math.isfinite(item.monotonic_time_s) and math.isfinite(item.value)]
        if not finite:
            raise ValueError(f"channel {name} has no finite sample")
        nearest = min(finite, key=lambda item: abs(item.monotonic_time_s - anchor_s))
        if abs(nearest.monotonic_time_s - anchor_s) > max_skew_s:
            raise ValueError(f"channel {name} is outside the sample window")
        aligned[name] = nearest
    return aligned


def _validate_table(xs: Sequence[float], ys: Sequence[float]) -> None:
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("lookup axes must have equal length >= 2")
    if any(not math.isfinite(v) for v in tuple(xs) + tuple(ys)):
        raise ValueError("lookup table contains non-finite values")
    if any(b <= a for a, b in zip(xs, xs[1:])):
        raise ValueError("lookup x-axis must be strictly increasing")


def strict_interp(x: float, xs: Sequence[float], ys: Sequence[float]) -> float:
    """Piecewise-linear interpolation that rejects, rather than clamps, OOB input."""
    _validate_table(xs, ys)
    if not math.isfinite(x) or x < xs[0] or x > xs[-1]:
        raise ValueError(f"lookup value {x!r} outside [{xs[0]}, {xs[-1]}]")
    if x == xs[-1]:
        return ys[-1]
    for index in range(1, len(xs)):
        if x <= xs[index]:
            ratio = (x - xs[index - 1]) / (xs[index] - xs[index - 1])
            return ys[index - 1] + ratio * (ys[index] - ys[index - 1])
    raise AssertionError("unreachable interpolation branch")


def _mean_ocv(soc: float, temperature_c: float) -> float:
    temperatures = tuple(sorted(OCV_TABLES))
    if temperature_c < temperatures[0] or temperature_c > temperatures[-1]:
        raise ValueError("temperature outside OCV table")
    layer_values = tuple(strict_interp(soc, OCV_SOC, OCV_TABLES[t]) for t in temperatures)
    return strict_interp(temperature_c, temperatures, layer_values)


def ocv_from_soc(soc: float, temperature_c: float = 25.0,
                 direction: str = "rest", rest_s: float = math.inf) -> float:
    """Temperature-layered voltage reference with direction history and relaxation."""
    if rest_s < 0:
        raise ValueError("rest_s must be non-negative")
    signs = {"charge": 1.0, "rest": 0.0, "discharge": -1.0}
    if direction not in signs:
        raise ValueError("direction must be charge, discharge, or rest")
    mean_v = _mean_ocv(soc, temperature_c)
    if direction == "rest" or math.isinf(rest_s):
        return mean_v
    temperature_factor = 1.0 + max(0.0, 25.0 - temperature_c) / 100.0
    remaining = math.exp(-rest_s / RELAXATION_TAU_S)
    return mean_v + signs[direction] * HYSTERESIS_HALF_BAND_V * temperature_factor * remaining


def soc_from_ocv(voltage_v: float, temperature_c: float = 25.0,
                 direction: str = "rest", rest_s: float = math.inf) -> float:
    branch = tuple(ocv_from_soc(s, temperature_c, direction, rest_s) for s in OCV_SOC)
    _validate_table(branch, OCV_SOC)
    return strict_interp(voltage_v, branch, OCV_SOC)


def ocv_slope(soc: float, temperature_c: float = 25.0,
              direction: str = "rest", rest_s: float = math.inf,
              h: float = 1e-3) -> float:
    if h <= 0 or soc < OCV_SOC[0] or soc > OCV_SOC[-1]:
        raise ValueError("invalid SOC or derivative step")
    lo = max(OCV_SOC[0], soc - h)
    hi = min(OCV_SOC[-1], soc + h)
    if hi == lo:
        raise ValueError("derivative interval collapsed")
    return (ocv_from_soc(hi, temperature_c, direction, rest_s)
            - ocv_from_soc(lo, temperature_c, direction, rest_s)) / (hi - lo)


def observation_information(soc: float, voltage_variance_v2: float,
                            temperature_c: float = 25.0) -> float:
    """Scalar local SOC information H^2/R, conditional on other states being known."""
    if voltage_variance_v2 <= 0 or not math.isfinite(voltage_variance_v2):
        raise ValueError("voltage variance must be positive and finite")
    h = ocv_slope(soc, temperature_c)
    return h * h / voltage_variance_v2


def scalar_kalman_gain(prior_soc_variance: float, slope_v_per_soc: float,
                       voltage_variance_v2: float) -> float:
    """SOC correction gain P*H/(H^2*P+R); it is not simply proportional to H."""
    if prior_soc_variance < 0 or voltage_variance_v2 <= 0:
        raise ValueError("invalid variance")
    denominator = slope_v_per_soc ** 2 * prior_soc_variance + voltage_variance_v2
    return prior_soc_variance * slope_v_per_soc / denominator


@dataclass(frozen=True)
class ModelParams:
    capacity_ah: float = CELL_CAPACITY_AH
    charge_efficiency: float = DEFAULT_CHARGE_EFFICIENCY
    r0_ohm: float = 3.2e-4
    r_dynamic_ohm: float = 2.0e-4
    tau_s: float = 20.0
    hysteresis_limit_v: float = HYSTERESIS_HALF_BAND_V
    hysteresis_tau_s: float = 600.0


DEFAULT_MODEL_PARAMS = ModelParams()
R0_OHM = DEFAULT_MODEL_PARAMS.r0_ohm
R1_OHM = DEFAULT_MODEL_PARAMS.r_dynamic_ohm
TAU_S = DEFAULT_MODEL_PARAMS.tau_s
C1_F = TAU_S / R1_OHM


@dataclass(frozen=True)
class ModelState:
    soc: float
    dynamic_v: float = 0.0
    hysteresis_v: float = 0.0


@dataclass(frozen=True)
class ModelStep:
    state_before: ModelState
    input_current_a: float
    true_current_a: float
    dt_s: float
    terminal_voltage_v: float
    state_after: ModelState
    params: ModelParams


def parameters_for(soc: float, temperature_c: float, soh: float,
                   base: ModelParams = DEFAULT_MODEL_PARAMS) -> ModelParams:
    """Teaching schedule showing that parameters depend on SOC, T, and SOH."""
    if not 0.0 <= soc <= 1.0 or not 0.5 <= soh <= 1.05:
        raise ValueError("SOC or SOH outside teaching model")
    if not -20.0 <= temperature_c <= 60.0:
        raise ValueError("temperature outside teaching model")
    edge = abs(soc - 0.5) * 2.0
    cold = max(0.0, 25.0 - temperature_c)
    age = max(0.0, 1.0 - soh)
    resistance_factor = 1.0 + 0.25 * edge + 0.012 * cold + 0.8 * age
    dynamic_factor = 1.0 + 0.15 * edge + 0.008 * cold + 0.6 * age
    tau_factor = 1.0 + 0.20 * edge + 0.006 * cold + 0.4 * age
    temperature_capacity = 1.0 - 0.002 * cold
    return ModelParams(
        capacity_ah=base.capacity_ah * soh * temperature_capacity,
        charge_efficiency=base.charge_efficiency,
        r0_ohm=base.r0_ohm * resistance_factor,
        r_dynamic_ohm=base.r_dynamic_ohm * dynamic_factor,
        tau_s=base.tau_s * tau_factor,
        hysteresis_limit_v=base.hysteresis_limit_v,
        hysteresis_tau_s=base.hysteresis_tau_s,
    )


def predict_observation(state: ModelState, true_current_a: float,
                        temperature_c: float, params: ModelParams) -> float:
    if not 0.0 <= state.soc <= 1.0:
        raise ValueError("SOC outside OCV table")
    return (_mean_ocv(state.soc, temperature_c) + state.hysteresis_v
            - true_current_a * params.r0_ohm - state.dynamic_v)


def advance_model(state: ModelState, measured_current_a: float, dt_s: float,
                  temperature_c: float = 25.0, soh: float = 1.0,
                  current_bias_a: float = 0.0,
                  params: Optional[ModelParams] = None) -> ModelStep:
    """Apply y[k]=h(x[k],u[k]), then x[k+1]=f(x[k],u[k],dt[k])."""
    if dt_s <= 0 or not math.isfinite(dt_s):
        raise ValueError("dt_s must be positive and finite")
    true_current = measured_current_a - current_bias_a
    used = params if params is not None else parameters_for(
        state.soc, temperature_c, soh)
    if used.capacity_ah <= 0 or used.tau_s <= 0 or used.hysteresis_tau_s <= 0:
        raise ValueError("invalid model parameters")
    terminal_v = predict_observation(state, true_current, temperature_c, used)
    charge_weighted_i = (true_current if true_current >= 0
                         else true_current * used.charge_efficiency)
    next_soc = state.soc - charge_weighted_i * dt_s / (3600.0 * used.capacity_ah)
    dynamic_a = math.exp(-dt_s / used.tau_s)
    next_dynamic = (dynamic_a * state.dynamic_v
                    + (1.0 - dynamic_a) * true_current * used.r_dynamic_ohm)
    if abs(true_current) < 1e-12:
        target_h = 0.0
    else:
        target_h = -math.copysign(used.hysteresis_limit_v, true_current)
    hyst_a = math.exp(-dt_s / used.hysteresis_tau_s)
    next_hyst = hyst_a * state.hysteresis_v + (1.0 - hyst_a) * target_h
    next_state = ModelState(next_soc, next_dynamic, next_hyst)
    return ModelStep(state, measured_current_a, true_current, dt_s,
                     terminal_v, next_state, used)


@dataclass(frozen=True)
class InputPoint:
    time_s: float
    current_a: float
    temperature_c: float = 25.0


@dataclass(frozen=True)
class InjectionConfig:
    seed: int = 7
    voltage_noise_std_v: float = 0.0
    current_noise_std_a: float = 0.0
    current_bias_a: float = 0.0
    drop_indices: Tuple[int, ...] = ()
    receive_delay_s: float = 0.05
    delay_by_index_s: Tuple[float, ...] = ()
    parameter_scale: float = 1.0


@dataclass(frozen=True)
class TruthRecord:
    sample: Sample
    state_true: ModelState
    current_true_a: float
    params_true: ModelParams


def _scaled_params(base: ModelParams, scale: float) -> ModelParams:
    if scale <= 0:
        raise ValueError("parameter scale must be positive")
    return ModelParams(base.capacity_ah, base.charge_efficiency,
                       base.r0_ohm * scale, base.r_dynamic_ohm * scale,
                       base.tau_s * scale, base.hysteresis_limit_v,
                       base.hysteresis_tau_s)


def generate_truth(profile: Sequence[InputPoint], initial_state: ModelState,
                   injection: InjectionConfig = InjectionConfig(),
                   truth_base_params: ModelParams = DEFAULT_MODEL_PARAMS,
                   soh: float = 1.0) -> Tuple[TruthRecord, ...]:
    """Create reproducible truth plus noisy, biased, delayed, or missing telemetry."""
    if not profile:
        return ()
    if any(b.time_s <= a.time_s for a, b in zip(profile, profile[1:])):
        raise ValueError("profile time must be strictly increasing")
    if injection.delay_by_index_s and len(injection.delay_by_index_s) != len(profile):
        raise ValueError("delay vector length must match profile")
    rng = random.Random(injection.seed)
    state = initial_state
    records = []
    dropped = set(injection.drop_indices)
    for index, point in enumerate(profile):
        scheduled = parameters_for(state.soc, point.temperature_c, soh, truth_base_params)
        truth_params = _scaled_params(scheduled, injection.parameter_scale)
        voltage = predict_observation(state, point.current_a, point.temperature_c, truth_params)
        measured_i = point.current_a + injection.current_bias_a + rng.gauss(
            0.0, injection.current_noise_std_a)
        measured_v = voltage + rng.gauss(0.0, injection.voltage_noise_std_v)
        delay = (injection.delay_by_index_s[index]
                 if injection.delay_by_index_s else injection.receive_delay_s)
        sample = Sample(index, point.time_s, point.time_s + delay,
                        point.time_s + delay, measured_i, measured_v,
                        point.temperature_c)
        if index not in dropped:
            records.append(TruthRecord(sample, state, point.current_a, truth_params))
        if index < len(profile) - 1:
            dt_s = profile[index + 1].time_s - point.time_s
            state = advance_model(state, point.current_a, dt_s,
                                  point.temperature_c, soh, 0.0,
                                  truth_params).state_after
    return tuple(records)


def mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean requires data")
    return sum(values) / len(values)


@dataclass(frozen=True)
class ResidualMetrics:
    rmse: float
    mean: float
    count: int


def residual_metrics(residuals: Sequence[float]) -> ResidualMetrics:
    if not residuals:
        raise ValueError("residual metrics require data")
    return ResidualMetrics(math.sqrt(mean([r * r for r in residuals])),
                           mean(residuals), len(residuals))


def solve_linear_system(matrix: Sequence[Sequence[float]],
                        vector: Sequence[float]) -> Tuple[float, ...]:
    """Small dense solve with partial pivoting for teaching regressions."""
    n = len(vector)
    if n == 0 or len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValueError("square matrix required")
    augmented = [list(map(float, row)) + [float(vector[i])]
                 for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(augmented[row][col]))
        if abs(augmented[pivot][col]) < 1e-12:
            raise ValueError("singular regression")
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        scale = augmented[col][col]
        augmented[col] = [value / scale for value in augmented[col]]
        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            augmented[row] = [a - factor * b
                              for a, b in zip(augmented[row], augmented[col])]
    return tuple(augmented[row][-1] for row in range(n))


def least_squares(features: Sequence[Sequence[float]],
                  targets: Sequence[float]) -> Tuple[float, ...]:
    if len(features) != len(targets) or not features:
        raise ValueError("features and targets must be non-empty and aligned")
    width = len(features[0])
    if width == 0 or any(len(row) != width for row in features):
        raise ValueError("inconsistent feature width")
    gram = [[sum(row[i] * row[j] for row in features)
             for j in range(width)] for i in range(width)]
    rhs = [sum(row[i] * target for row, target in zip(features, targets))
           for i in range(width)]
    return solve_linear_system(gram, rhs)


@dataclass(frozen=True)
class IdentificationResult:
    r0_ohm: float
    r_dynamic_ohm: float
    tau_s: float
    recovery_factor_at_median_dt: float
    offset_v: float
    train: ResidualMetrics
    validation: ResidualMetrics


def _dynamic_feature(times_s: Sequence[float], currents_a: Sequence[float],
                     tau_s: float) -> Tuple[float, ...]:
    z = 0.0
    values = []
    for index, current in enumerate(currents_a):
        values.append(z)
        if index < len(currents_a) - 1:
            dt_s = times_s[index + 1] - times_s[index]
            a = math.exp(-dt_s / tau_s)
            z = a * z + (1.0 - a) * current
    return tuple(values)


def identify_dynamic_parameters(times_s: Sequence[float], currents_a: Sequence[float],
                                voltage_drop_v: Sequence[float], train_fraction: float = 0.7,
                                tau_candidates_s: Iterable[float] = tuple(range(5, 61)),
                                r0_bounds: Tuple[float, float] = (5e-5, 2e-3),
                                r_dynamic_bounds: Tuple[float, float] = (2e-5, 2e-3),
                                min_current_span_a: float = 50.0) -> IdentificationResult:
    """Bounded grid search for tau plus multi-point least squares for R0 and R1."""
    n = len(times_s)
    if n != len(currents_a) or n != len(voltage_drop_v) or n < 20:
        raise ValueError("at least 20 aligned points are required")
    if any(b <= a for a, b in zip(times_s, times_s[1:])):
        raise ValueError("times must be strictly increasing")
    if max(currents_a) - min(currents_a) < min_current_span_a:
        raise ValueError("insufficient current excitation")
    split = int(n * train_fraction)
    if not 10 <= split <= n - 5:
        raise ValueError("train/validation split is too small")
    candidates = [float(tau) for tau in tau_candidates_s if tau > 0]
    if not candidates:
        raise ValueError("no positive tau candidate")
    best = None
    dt_sorted = sorted(b - a for a, b in zip(times_s, times_s[1:]))
    median_dt = dt_sorted[len(dt_sorted) // 2]
    for tau_s in candidates:
        dynamic = _dynamic_feature(times_s, currents_a, tau_s)
        train_x = [[currents_a[k], dynamic[k], 1.0] for k in range(split)]
        try:
            r0, r_dynamic, offset = least_squares(train_x, voltage_drop_v[:split])
        except ValueError:
            continue
        if not r0_bounds[0] <= r0 <= r0_bounds[1]:
            continue
        if not r_dynamic_bounds[0] <= r_dynamic <= r_dynamic_bounds[1]:
            continue
        train_res = [voltage_drop_v[k]
                     - (r0 * currents_a[k] + r_dynamic * dynamic[k] + offset)
                     for k in range(split)]
        val_res = [voltage_drop_v[k]
                   - (r0 * currents_a[k] + r_dynamic * dynamic[k] + offset)
                   for k in range(split, n)]
        score = residual_metrics(val_res).rmse
        candidate = (score, tau_s, r0, r_dynamic, offset,
                     residual_metrics(train_res), residual_metrics(val_res))
        if best is None or candidate[0] < best[0]:
            best = candidate
    if best is None:
        raise ValueError("no parameter set satisfied bounds")
    _, tau_s, r0, r_dynamic, offset, train_metric, val_metric = best
    return IdentificationResult(r0, r_dynamic, tau_s,
                                math.exp(-median_dt / tau_s), offset,
                                train_metric, val_metric)


@dataclass(frozen=True)
class CapacityResult:
    effective_capacity_ah: float
    integrated_charge_ah: float
    soc_span: float
    reverse_charge_fraction: float


def identify_effective_capacity(interval_times_s: Sequence[float],
                                interval_currents_a: Sequence[float],
                                soc_start: float, soc_end: float,
                                direction: str = "discharge",
                                charge_efficiency: float = DEFAULT_CHARGE_EFFICIENCY,
                                min_soc_span: float = 0.8,
                                max_reverse_fraction: float = 0.05) -> CapacityResult:
    """Identify C_eff from accepted cycle endpoints and interval-average current."""
    if len(interval_times_s) != len(interval_currents_a) + 1:
        raise ValueError("N interval currents require N+1 boundary times")
    if any(b <= a for a, b in zip(interval_times_s, interval_times_s[1:])):
        raise ValueError("cycle times must be strictly increasing")
    if direction not in ("discharge", "charge"):
        raise ValueError("direction must be discharge or charge")
    if not 0 < charge_efficiency <= 1:
        raise ValueError("invalid charge efficiency")
    soc_span = soc_start - soc_end if direction == "discharge" else soc_end - soc_start
    if soc_span < min_soc_span:
        raise ValueError("cycle SOC span is insufficient")
    wanted_ah = reverse_ah = 0.0
    for index, current in enumerate(interval_currents_a):
        dt_h = (interval_times_s[index + 1] - interval_times_s[index]) / 3600.0
        signed = current if direction == "discharge" else -current * charge_efficiency
        if signed >= 0:
            wanted_ah += signed * dt_h
        else:
            reverse_ah += -signed * dt_h
    total = wanted_ah + reverse_ah
    reverse_fraction = reverse_ah / total if total else 1.0
    if total == 0 or reverse_fraction > max_reverse_fraction:
        raise ValueError("cycle direction is invalid or too fragmented")
    net_ah = wanted_ah - reverse_ah
    return CapacityResult(net_ah / soc_span, net_ah, soc_span, reverse_fraction)
# @AI_GENERATED: end
