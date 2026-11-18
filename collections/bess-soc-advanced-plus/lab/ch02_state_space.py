# @AI_GENERATED
"""Chapter 02: irregular-dt software state model and injectable truth data."""
from soc_core import (
    CELL_CAPACITY_AH,
    DEFAULT_MODEL_PARAMS,
    InjectionConfig,
    InputPoint,
    ModelState,
    advance_model,
    generate_truth,
    ocv_from_soc,
)


def build_profile():
    """Rest, discharge pulse, irregular sample gap, charge pulse, recovery."""
    times = (0.0, 1.0, 2.0, 3.5, 5.0, 7.0, 8.0, 10.0)
    currents = (0.0, 120.0, 120.0, 120.0, -80.0, -80.0, 0.0, 0.0)
    temperatures = (25.0, 25.0, 25.0, 20.0, 20.0, 20.0, 20.0, 20.0)
    return tuple(InputPoint(t, i, temp) for t, i, temp in
                 zip(times, currents, temperatures))


def test_irregular_dt_capacity_efficiency_and_bias():
    state = ModelState(0.50)
    # The input sensor says 315 A, but its known +1 A bias is removed before use.
    step = advance_model(state, measured_current_a=315.0, current_bias_a=1.0,
                         dt_s=360.0, temperature_c=25.0,
                         params=DEFAULT_MODEL_PARAMS)
    expected = 0.50 - 314.0 * 360.0 / (3600.0 * CELL_CAPACITY_AH)
    assert abs(step.state_after.soc - expected) < 1e-12
    assert step.true_current_a == 314.0

    charge = advance_model(step.state_after, measured_current_a=-314.0,
                           dt_s=360.0, temperature_c=25.0,
                           params=DEFAULT_MODEL_PARAMS)
    # Charge efficiency is below one, so equal external Ah does not restore SOC.
    assert charge.state_after.soc < state.soc


def test_measurement_uses_xk_uk_before_advancing():
    state = ModelState(0.50)
    step = advance_model(state, 314.0, 360.0, params=DEFAULT_MODEL_PARAMS)
    expected_yk = ocv_from_soc(0.50) - 314.0 * DEFAULT_MODEL_PARAMS.r0_ohm
    assert abs(step.terminal_voltage_v - expected_yk) < 1e-12
    assert abs(step.state_after.soc - 0.40) < 1e-12
    # A wrong implementation would have used OCV(0.40) in y[k].
    assert abs(step.terminal_voltage_v
               - (ocv_from_soc(step.state_after.soc)
                  - 314.0 * DEFAULT_MODEL_PARAMS.r0_ohm)) > 1e-3


def test_truth_generator_fault_injection_is_reproducible():
    profile = build_profile()
    injection = InjectionConfig(
        seed=23,
        voltage_noise_std_v=0.001,
        current_noise_std_a=0.2,
        current_bias_a=0.8,
        drop_indices=(3,),
        delay_by_index_s=(0.05, 0.05, 0.05, 0.8, 0.05, 0.05, 0.05, 0.05),
        parameter_scale=1.20,
    )
    first = generate_truth(profile, ModelState(0.55), injection)
    second = generate_truth(profile, ModelState(0.55), injection)
    assert first == second
    assert [row.sample.seq for row in first] == [0, 1, 2, 4, 5, 6, 7]
    assert abs(first[1].sample.current_a - first[1].current_true_a) > 0.1
    # Truth parameters are retained only for scoring. An estimator must use its
    # independently configured defaults, not copy these hidden values back in.
    assert first[1].params_true.r0_ohm != DEFAULT_MODEL_PARAMS.r0_ohm


def test_parameter_schedule_changes_with_context():
    warm = advance_model(ModelState(0.50), 10.0, 1.0,
                         temperature_c=25.0, soh=1.0)
    cold_old = advance_model(ModelState(0.10), 10.0, 1.0,
                             temperature_c=0.0, soh=0.8)
    assert cold_old.params.r0_ohm > warm.params.r0_ohm
    assert cold_old.params.capacity_ah < warm.params.capacity_ah


def main():
    records = generate_truth(
        build_profile(),
        ModelState(0.55),
        InjectionConfig(seed=23, voltage_noise_std_v=0.001,
                        current_bias_a=0.8, drop_indices=(3,),
                        parameter_scale=1.10),
    )
    print(f"{'k':>2} {'t(s)':>6} {'I_true':>8} {'I_meas':>8} {'SOC[k]':>9} {'y[k](V)':>9}")
    for row in records:
        print(f"{row.sample.seq:>2} {row.sample.device_time_s:>6.1f} "
              f"{row.current_true_a:>8.1f} {row.sample.current_a:>8.2f} "
              f"{row.state_true.soc:>9.5f} {row.sample.voltage_v:>9.4f}")
    test_irregular_dt_capacity_efficiency_and_bias()
    test_measurement_uses_xk_uk_before_advancing()
    test_truth_generator_fault_injection_is_reproducible()
    test_parameter_schedule_changes_with_context()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
