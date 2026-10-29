# @AI_GENERATED
"""Chapter 01: telemetry contract, ordering, quality gate, and alignment."""
import math

from soc_core import (
    GateConfig,
    Quality,
    Sample,
    StreamQualityGate,
    TimedValue,
    align_to_window,
)


def sample(seq, device_s, receive_s, current_a=50.0, voltage_v=3.25,
           temperature_c=25.0, monotonic_s=None):
    """Small fixture using seconds, amperes, volts, and degrees Celsius."""
    return Sample(
        seq=seq,
        device_time_s=device_s,
        receive_time_s=receive_s,
        monotonic_time_s=receive_s if monotonic_s is None else monotonic_s,
        current_a=current_a,
        voltage_v=voltage_v,
        temperature_c=temperature_c,
    )


def estimate_step_resistance(voltage_before_v, voltage_after_v,
                             current_before_a, current_after_a):
    """Short example showing why y[k] must be paired with u[k]."""
    delta_i = current_after_a - current_before_a
    if abs(delta_i) < 1e-12:
        raise ValueError("current step is required")
    return -(voltage_after_v - voltage_before_v) / delta_i


def test_quality_gate_classifies_common_failures():
    gate = StreamQualityGate(GateConfig(frozen_repeat_limit=2))
    assert gate.check(sample(0, 100.0, 100.05)).quality is Quality.GOOD

    missing = gate.check(sample(2, 102.0, 102.05, voltage_v=3.24))
    assert missing.quality is Quality.SUSPECT
    assert "missing_sequence" in missing.reasons
    assert "missing_interval" in missing.reasons

    duplicate = gate.check(sample(2, 102.0, 102.10, voltage_v=3.24))
    assert duplicate.quality is Quality.INVALID
    assert "duplicate_or_late_device_sample" in duplicate.reasons

    late_gate = StreamQualityGate()
    late = late_gate.check(sample(0, 10.0, 13.0))
    assert late.quality is Quality.SUSPECT
    assert "late_or_clock_mismatch" in late.reasons

    nan_gate = StreamQualityGate()
    invalid = nan_gate.check(sample(0, 0.0, 0.1, voltage_v=math.nan))
    assert invalid.quality is Quality.INVALID
    assert "non_finite" in invalid.reasons


def test_freeze_and_range_detection():
    gate = StreamQualityGate(GateConfig(frozen_repeat_limit=2))
    results = [gate.check(sample(k, float(k), k + 0.05)) for k in range(3)]
    assert results[-1].quality is Quality.SUSPECT
    assert "frozen_payload" in results[-1].reasons

    range_gate = StreamQualityGate()
    result = range_gate.check(sample(0, 0.0, 0.05, voltage_v=4.5))
    assert result.quality is Quality.INVALID
    assert "voltage_out_of_range" in result.reasons


def test_alignment_rejects_cross_window_pairing():
    channels = {
        "current_a": [TimedValue(10.00, 50.0)],
        "voltage_v": [TimedValue(10.04, 3.25)],
        "temperature_c": [TimedValue(10.02, 25.0)],
    }
    aligned = align_to_window(channels, anchor_s=10.02, max_skew_s=0.05)
    assert aligned["current_a"].value == 50.0

    channels["voltage_v"] = [TimedValue(10.20, 3.25)]
    try:
        align_to_window(channels, anchor_s=10.02, max_skew_s=0.05)
    except ValueError as exc:
        assert "outside" in str(exc)
    else:
        raise AssertionError("cross-window voltage must be rejected")


def test_wrong_tick_changes_identified_resistance():
    right = estimate_step_resistance(3.30, 3.25, 0.0, 50.0)
    wrong = estimate_step_resistance(3.30, 3.25, 0.0, 100.0)
    assert abs(right - 1.0e-3) < 1e-12
    assert abs(wrong - 0.5e-3) < 1e-12


def main():
    gate = StreamQualityGate()
    rows = [
        sample(0, 100.0, 100.05),
        sample(2, 102.0, 102.05, voltage_v=3.24),
        sample(2, 102.0, 102.10, voltage_v=3.24),
    ]
    print(f"{'seq':>4} {'quality':>9}  reasons")
    for row in rows:
        result = gate.check(row)
        print(f"{row.seq:>4} {result.quality.value:>9}  {','.join(result.reasons) or '-'}")
    right = estimate_step_resistance(3.30, 3.25, 0.0, 50.0)
    wrong = estimate_step_resistance(3.30, 3.25, 0.0, 100.0)
    print(f"same tick: {right * 1000:.2f} mΩ; wrong tick: {wrong * 1000:.2f} mΩ")
    test_quality_gate_classifies_common_failures()
    test_freeze_and_range_detection()
    test_alignment_rejects_cross_window_pairing()
    test_wrong_tick_changes_identified_resistance()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
