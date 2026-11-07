# @AI_GENERATED
"""Chapter 03: temperature OCV, hysteresis, relaxation, and information."""
import math

from soc_core import (
    HYSTERESIS_HALF_BAND_V,
    observation_information,
    ocv_from_soc,
    ocv_slope,
    scalar_kalman_gain,
    soc_from_ocv,
)

VOLTAGE_STD_V = 0.005
VOLTAGE_VARIANCE_V2 = VOLTAGE_STD_V ** 2
PRIOR_SOC_VARIANCE = 0.02 ** 2


def observability_row(soc, temperature_c=25.0):
    slope = ocv_slope(soc, temperature_c)
    information = observation_information(soc, VOLTAGE_VARIANCE_V2,
                                          temperature_c)
    gain = scalar_kalman_gain(PRIOR_SOC_VARIANCE, slope,
                              VOLTAGE_VARIANCE_V2)
    return slope, information, gain, gain * slope


def test_temperature_hysteresis_and_relaxation():
    cold = ocv_from_soc(0.50, -10.0)
    warm = ocv_from_soc(0.50, 25.0)
    assert cold < warm

    charge = ocv_from_soc(0.50, 25.0, "charge", rest_s=0.0)
    discharge = ocv_from_soc(0.50, 25.0, "discharge", rest_s=0.0)
    assert abs((charge - discharge) - 2 * HYSTERESIS_HALF_BAND_V) < 1e-12
    relaxed = ocv_from_soc(0.50, 25.0, "charge", rest_s=7200.0)
    assert abs(relaxed - warm) < abs(charge - warm)


def test_out_of_table_is_rejected_not_clamped():
    for operation in (
        lambda: ocv_from_soc(1.01, 25.0),
        lambda: ocv_from_soc(0.50, -30.0),
        lambda: soc_from_ocv(3.60, 25.0),
    ):
        try:
            operation()
        except ValueError:
            pass
        else:
            raise AssertionError("out-of-table input must be rejected")


def test_information_and_gain_are_not_the_same_statement():
    h_flat, info_flat, gain_flat, fraction_flat = observability_row(0.50)
    h_steep, info_steep, gain_steep, fraction_steep = observability_row(0.05)
    assert h_steep > 10 * h_flat
    assert info_steep > 100 * info_flat
    # K has units SOC/V and includes H in both numerator and denominator.
    # It need not grow with H; the dimensionless correction fraction K*H does.
    assert gain_steep < gain_flat
    assert fraction_steep > fraction_flat
    assert fraction_steep < 1.0


def test_inverse_lookup_uses_selected_layer_and_branch():
    soc = 0.20
    voltage = ocv_from_soc(soc, 45.0, "discharge", rest_s=600.0)
    recovered = soc_from_ocv(voltage, 45.0, "discharge", rest_s=600.0)
    assert abs(recovered - soc) < 1e-12


def main():
    print(f"{'SOC':>6} {'H(V/SOC)':>10} {'H^2/R':>12} {'K(SOC/V)':>11} {'K*H':>8}")
    for soc in (0.05, 0.30, 0.50, 0.70, 0.95):
        h, info, gain, fraction = observability_row(soc)
        print(f"{soc:>6.0%} {h:>10.3f} {info:>12.0f} {gain:>11.3f} {fraction:>8.1%}")
    charge = ocv_from_soc(0.50, 25.0, "charge", 0.0)
    discharge = ocv_from_soc(0.50, 25.0, "discharge", 0.0)
    relaxed = ocv_from_soc(0.50, 25.0, "charge", 7200.0)
    print(f"50%: charge={charge:.4f} V, discharge={discharge:.4f} V, "
          f"charge after 2 h rest={relaxed:.4f} V")
    test_temperature_hysteresis_and_relaxation()
    test_out_of_table_is_rejected_not_clamped()
    test_information_and_gain_are_not_the_same_statement()
    test_inverse_lookup_uses_selected_layer_and_branch()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end