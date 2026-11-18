# @AI_GENERATED
"""Chapter 04: noisy bounded dynamic fitting and effective-capacity fitting."""
import math
import random

from soc_core import (
    DEFAULT_MODEL_PARAMS,
    identify_dynamic_parameters,
    identify_effective_capacity,
)


def generate_noisy_dynamic_data(seed=41):
    """Generate aligned y[k]=R0*u[k]+R1*z[k]+noise without exposing truth to fit."""
    rng = random.Random(seed)
    segment = [0.0] * 20 + [120.0] * 20 + [0.0] * 20 + [-80.0] * 20
    currents = tuple(segment * 3)
    times = [0.0]
    for index in range(1, len(currents)):
        dt_s = (0.8, 1.0, 1.2)[index % 3]
        times.append(times[-1] + dt_s)

    dynamic_v = 0.0
    drops = []
    for index, current in enumerate(currents):
        drops.append(
            DEFAULT_MODEL_PARAMS.r0_ohm * current
            + dynamic_v
            + 0.0007
            + rng.gauss(0.0, 0.0006)
        )
        if index < len(currents) - 1:
            dt_s = times[index + 1] - times[index]
            a = math.exp(-dt_s / DEFAULT_MODEL_PARAMS.tau_s)
            dynamic_v = (
                a * dynamic_v
                + (1.0 - a) * current * DEFAULT_MODEL_PARAMS.r_dynamic_ohm
            )
    return tuple(times), currents, tuple(drops)


def run_dynamic_identification():
    times, currents, drops = generate_noisy_dynamic_data()
    # Bounds and candidate grid are configuration. No hidden truth parameter is
    # passed to the fitting function or copied from the generator.
    return identify_dynamic_parameters(
        times,
        currents,
        drops,
        train_fraction=0.67,
        tau_candidates_s=(5.0 + 0.5 * index for index in range(111)),
        r0_bounds=(1.0e-4, 8.0e-4),
        r_dynamic_bounds=(5.0e-5, 6.0e-4),
        min_current_span_a=100.0,
    )


def generate_capacity_cycle(seed=9):
    """Accepted 95%->5% discharge with interval-average current telemetry."""
    rng = random.Random(seed)
    intervals = 90
    dt_s = 36.0
    times = tuple(index * dt_s for index in range(intervals + 1))
    currents = tuple(314.0 + rng.gauss(0.0, 1.0) for _ in range(intervals))
    return times, currents


def test_noisy_multi_point_fit_with_validation():
    result = run_dynamic_identification()
    assert abs(result.r0_ohm / DEFAULT_MODEL_PARAMS.r0_ohm - 1.0) < 0.08
    assert abs(result.r_dynamic_ohm /
               DEFAULT_MODEL_PARAMS.r_dynamic_ohm - 1.0) < 0.15
    assert abs(result.tau_s / DEFAULT_MODEL_PARAMS.tau_s - 1.0) < 0.15
    assert result.validation.rmse < 0.0012
    assert abs(result.validation.mean) < 0.0005
    assert 0.0 < result.recovery_factor_at_median_dt < 1.0


def test_identification_rejects_insufficient_excitation():
    times = tuple(float(k) for k in range(30))
    currents = (10.0,) * 30
    drops = (0.004,) * 30
    try:
        identify_dynamic_parameters(times, currents, drops)
    except ValueError as exc:
        assert "excitation" in str(exc)
    else:
        raise AssertionError("flat current must not produce trusted parameters")


def test_complete_cycle_effective_capacity():
    times, currents = generate_capacity_cycle()
    result = identify_effective_capacity(
        times,
        currents,
        soc_start=0.95,
        soc_end=0.05,
        direction="discharge",
    )
    assert abs(result.effective_capacity_ah / 314.0 - 1.0) < 0.01
    assert abs(result.soc_span - 0.90) < 1e-12
    assert result.reverse_charge_fraction == 0.0


def test_capacity_rejects_partial_cycle():
    times = (0.0, 3600.0)
    currents = (100.0,)
    try:
        identify_effective_capacity(times, currents, 0.60, 0.20)
    except ValueError as exc:
        assert "span" in str(exc)
    else:
        raise AssertionError("partial cycle must be rejected")


def main():
    result = run_dynamic_identification()
    print(f"R0={result.r0_ohm * 1000:.4f} mΩ, "
          f"Rdyn={result.r_dynamic_ohm * 1000:.4f} mΩ, "
          f"tau={result.tau_s:.2f} s, a={result.recovery_factor_at_median_dt:.5f}")
    print(f"train RMSE={result.train.rmse * 1000:.3f} mV, "
          f"validation RMSE={result.validation.rmse * 1000:.3f} mV, "
          f"validation mean={result.validation.mean * 1000:+.3f} mV")
    times, currents = generate_capacity_cycle()
    capacity = identify_effective_capacity(times, currents, 0.95, 0.05)
    print(f"cycle charge={capacity.integrated_charge_ah:.2f} Ah, "
          f"C_eff={capacity.effective_capacity_ah:.2f} Ah")
    test_noisy_multi_point_fit_with_validation()
    test_identification_rejects_insufficient_excitation()
    test_complete_cycle_effective_capacity()
    test_capacity_rejects_partial_cycle()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
