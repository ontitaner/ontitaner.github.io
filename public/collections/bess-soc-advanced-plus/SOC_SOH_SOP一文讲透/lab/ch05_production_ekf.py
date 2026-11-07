# @AI_GENERATED
"""ch05：基于统一 314 Ah LFP 模型的 EKF 与安时积分对比。"""
from __future__ import annotations

import math
from typing import Sequence, Tuple

from soc_core import (
    DEFAULT_DT_S,
    DEFAULT_MODEL_PARAMS,
    InjectionConfig,
    InputPoint,
    ModelState,
    advance_model,
    generate_truth,
    ocv_slope,
    predict_observation,
)

SOC0_TRUE = 0.50
SOC0_EST = 0.70
VOLTAGE_VARIANCE_V2 = 0.002 ** 2
PROCESS_VARIANCE = (1.0e-8, 1.0e-8, 1.0e-10)
Covariance = Tuple[Tuple[float, float, float], ...]


def _diagonal(values: Sequence[float]) -> Covariance:
    return tuple(tuple(value if row == column else 0.0
                       for column, _ in enumerate(values))
                 for row, value in enumerate(values))


def _transition_covariance(covariance: Covariance, dt_s: float) -> Covariance:
    """Apply the core model's diagonal transition Jacobian and process noise."""
    dynamic_a = math.exp(-dt_s / DEFAULT_MODEL_PARAMS.tau_s)
    hysteresis_a = math.exp(-dt_s / DEFAULT_MODEL_PARAMS.hysteresis_tau_s)
    factors = (1.0, dynamic_a, hysteresis_a)
    return tuple(tuple(
        factors[row] * covariance[row][column] * factors[column]
        + (PROCESS_VARIANCE[row] if row == column else 0.0)
        for column in range(3)) for row in range(3))


def _measurement_update(state: ModelState, covariance: Covariance, current_a: float,
                        voltage_v: float, temperature_c: float) -> Tuple[ModelState, Covariance]:
    """Correct [SOC, dynamic voltage, hysteresis voltage] from one voltage sample."""
    slope = ocv_slope(state.soc, temperature_c)
    h = (slope, -1.0, 1.0)
    predicted_v = predict_observation(state, current_a, temperature_c,
                                      DEFAULT_MODEL_PARAMS)
    innovation_v = voltage_v - predicted_v
    projected = tuple(sum(covariance[row][column] * h[column]
                          for column in range(3)) for row in range(3))
    innovation_variance = sum(h[row] * projected[row] for row in range(3)) + VOLTAGE_VARIANCE_V2
    if innovation_variance <= 0.0:
        raise ValueError("EKF innovation variance must be positive")
    gain = tuple(value / innovation_variance for value in projected)
    corrected = (
        min(1.0, max(0.0, state.soc + gain[0] * innovation_v)),
        state.dynamic_v + gain[1] * innovation_v,
        min(DEFAULT_MODEL_PARAMS.hysteresis_limit_v,
            max(-DEFAULT_MODEL_PARAMS.hysteresis_limit_v,
                state.hysteresis_v + gain[2] * innovation_v)),
    )
    # Joseph form preserves a symmetric, non-negative covariance under rounding.
    i_minus_kh = tuple(tuple((1.0 if row == column else 0.0) - gain[row] * h[column]
                              for column in range(3)) for row in range(3))
    corrected_covariance = tuple(tuple(
        sum(i_minus_kh[row][left] * covariance[left][right]
            * i_minus_kh[column][right] for left in range(3) for right in range(3))
        + gain[row] * VOLTAGE_VARIANCE_V2 * gain[column]
        for column in range(3)) for row in range(3))
    return ModelState(*corrected), corrected_covariance


def ekf_step(state: ModelState, covariance: Covariance, current_a: float,
             voltage_v: float, temperature_c: float, dt_s: float = DEFAULT_DT_S
             ) -> Tuple[ModelState, Covariance, ModelState]:
    """Use y[k] to correct x[k], then use the shared model to predict x[k+1]."""
    corrected_state, corrected_covariance = _measurement_update(
        state, covariance, current_a, voltage_v, temperature_c)
    predicted_state = advance_model(
        corrected_state, current_a, dt_s, temperature_c,
        params=DEFAULT_MODEL_PARAMS).state_after
    return predicted_state, _transition_covariance(corrected_covariance, dt_s), corrected_state


def coulomb_step(soc: float, measured_current_a: float,
                 dt_s: float = DEFAULT_DT_S) -> float:
    """Open-loop baseline using the shared 314 Ah capacity and charge efficiency."""
    return advance_model(ModelState(soc), measured_current_a, dt_s,
                         params=DEFAULT_MODEL_PARAMS).state_after.soc


def _profile(n: int) -> Tuple[InputPoint, ...]:
    if n < 2:
        raise ValueError("at least two samples are required")
    return tuple(InputPoint(index * DEFAULT_DT_S,
                            50.0 if (index // 300) % 2 == 0 else -50.0)
                 for index in range(n))


def run(seed: int = 17, bias_a: float = 0.5, v_noise: float = 0.002,
        n: int = 1800) -> Tuple[list[float], list[float], list[float]]:
    """Return deterministic true, biased coulomb-counting, and EKF SOC histories."""
    records = generate_truth(
        _profile(n), ModelState(SOC0_TRUE),
        InjectionConfig(seed=seed, voltage_noise_std_v=v_noise,
                        current_bias_a=bias_a))
    estimate = ModelState(SOC0_EST)
    covariance = _diagonal((1.0e-2, 1.0e-4, 2.5e-5))
    baseline = SOC0_EST
    true_soc, baseline_soc, ekf_soc = [], [], []
    for index, record in enumerate(records):
        sample = record.sample
        # Keep the Chapter 01/02 convention: this transition uses the observed
        # local-monotonic interval, never a hard-coded average sample period.
        dt_s = (records[index + 1].sample.monotonic_time_s - sample.monotonic_time_s
                if index < len(records) - 1 else DEFAULT_DT_S)
        estimate, covariance, corrected = ekf_step(
            estimate, covariance, sample.current_a, sample.voltage_v,
            sample.temperature_c, dt_s)
        true_soc.append(record.state_true.soc)
        baseline_soc.append(baseline)
        ekf_soc.append(corrected.soc)
        if index < len(records) - 1:
            baseline = coulomb_step(baseline, sample.current_a, dt_s)
    return true_soc, baseline_soc, ekf_soc


def test_ch05() -> None:
    true_soc, baseline_soc, ekf_soc = run()
    ekf_error = abs(ekf_soc[-1] - true_soc[-1])
    baseline_error = abs(baseline_soc[-1] - true_soc[-1])
    assert ekf_error < 0.02, ekf_error
    assert baseline_error > ekf_error * 3.0, (baseline_error, ekf_error)


def main() -> None:
    true_soc, baseline_soc, ekf_soc = run()
    print("[教学示例] 314 Ah LFP 单体；放电电流为正；seed=17")
    print(f"{'步':>5}{'真值SOC':>10}{'安时积分':>10}{'EKF SOC':>10}{'EKF误差':>10}")
    for index in (0, 50, 100, 300, 600, 1200, len(true_soc) - 1):
        print(f"{index:>5}{true_soc[index]:>10.4f}{baseline_soc[index]:>10.4f}"
              f"{ekf_soc[index]:>10.4f}{ekf_soc[index] - true_soc[index]:>+10.4f}")
    test_ch05()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
