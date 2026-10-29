# @AI_GENERATED
"""Chapter 06: propagate SOC covariance and make a minimal online diagnosis.

The lab is deterministic and standard-library-only.  It reuses site constants and
quality vocabulary from soc_core; it deliberately does not claim to be a BMS
protection implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Sequence, Tuple

from soc_core import Quality, SITE_NOMINAL_ENERGY_KWH


class DiagnosticState(str, Enum):
    """Usability state consumed by the Chapter 07 capability calculation."""

    NORMAL = "normal"
    DEGRADED = "degraded"
    INVALID = "invalid"


@dataclass(frozen=True)
class DiagnosticResult:
    quality: Quality
    residual_v: float
    standardized_residual: float
    nis: float
    continuous_bad: int
    state: DiagnosticState
    action: str


def energy_band(soc: float, sigma_soc: float, minimum_soc: float = 0.10,
                capacity_soh: float = 0.92, discharge_efficiency: float = 0.931
                ) -> Tuple[float, float]:
    """Return internal-to-AC available energy and its 1-sigma uncertainty in kWh.

    This is the local linear propagation sigma_E = C_eff * eta * sigma_SOC.
    It applies only while capacity, efficiency, and the active SOC window are fixed.
    """
    if not 0.0 <= soc <= 1.0 or sigma_soc < 0.0:
        raise ValueError("SOC and its standard deviation must be valid")
    if not 0.0 <= minimum_soc < 1.0 or not 0.0 < capacity_soh <= 1.0:
        raise ValueError("invalid operating-window parameters")
    if not 0.0 < discharge_efficiency <= 1.0:
        raise ValueError("invalid discharge efficiency")
    effective_capacity_kwh = SITE_NOMINAL_ENERGY_KWH * capacity_soh
    energy_kwh = max(0.0, soc - minimum_soc) * effective_capacity_kwh * discharge_efficiency
    sigma_energy_kwh = effective_capacity_kwh * discharge_efficiency * sigma_soc
    return energy_kwh, sigma_energy_kwh


def diagnose(quality: Quality, residual_v: float, innovation_std_v: float,
             previous_bad: int = 0, threshold_sigma: float = 3.0,
             required_consecutive: int = 2) -> DiagnosticResult:
    """Classify one update using input quality plus standardized innovation/NIS.

    A residual is r = V_measured - V_predicted, z = r / sqrt(S), and NIS = z^2.
    Two consecutive |z| >= threshold_sigma observations enter degraded mode;
    invalid input immediately rejects the update and capability refresh.
    """
    if innovation_std_v <= 0.0 or threshold_sigma <= 0.0 or required_consecutive < 1:
        raise ValueError("diagnostic thresholds must be positive")
    if quality is Quality.INVALID:
        # An invalid sample breaks consecutiveness; never confirm an anomaly by
        # combining residuals separated by unusable telemetry.
        return DiagnosticResult(quality, residual_v, math.nan, math.nan, 0,
                                DiagnosticState.INVALID,
                                "reject sample; freeze capability and request fresh aligned data")
    z = residual_v / innovation_std_v
    nis = z * z
    bad = abs(z) >= threshold_sigma
    continuous_bad = previous_bad + 1 if bad else 0
    if quality is Quality.SUSPECT or continuous_bad >= required_consecutive:
        action = "hold measurement correction; widen margin, derate and raise diagnostic event"
        return DiagnosticResult(quality, residual_v, z, nis, continuous_bad,
                                DiagnosticState.DEGRADED, action)
    action = "accept update and publish normal uncertainty" if not bad else "record residual; await consecutive confirmation"
    return DiagnosticResult(quality, residual_v, z, nis, continuous_bad,
                            DiagnosticState.NORMAL, action)


def uncertainty_trace() -> Tuple[float, ...]:
    """Deterministic covariance trace: excitation contracts faster than plateau rest."""
    excitation = [0.079 * math.exp(-0.004 * step) for step in range(600)]
    rest_start = excitation[-1]
    rest = [rest_start * math.exp(-0.000035 * step) for step in range(600)]
    return tuple(excitation + rest)


def run() -> Tuple[DiagnosticResult, ...]:
    """Use a [teaching example] residual stream with two persistent anomalies."""
    innovation_std_v = math.sqrt(0.002 ** 2 + 0.003 ** 2)
    samples = (
        (Quality.GOOD, 0.001),
        (Quality.GOOD, 0.012),
        (Quality.GOOD, 0.011),
        (Quality.SUSPECT, 0.001),
        (Quality.INVALID, 0.000),
    )
    results = []
    previous_bad = 0
    for quality, residual_v in samples:
        result = diagnose(quality, residual_v, innovation_std_v, previous_bad)
        results.append(result)
        previous_bad = result.continuous_bad
    return tuple(results)


def test_ch06() -> None:
    energy_kwh, sigma_kwh = energy_band(0.30, 0.03)
    assert round(energy_kwh, 1) == 859.3, energy_kwh
    assert round(sigma_kwh, 1) == 128.9, sigma_kwh
    results = run()
    assert results[1].continuous_bad == 1 and results[1].state is DiagnosticState.NORMAL
    assert results[2].state is DiagnosticState.DEGRADED
    assert results[3].state is DiagnosticState.DEGRADED
    assert results[4].state is DiagnosticState.INVALID
    assert results[4].continuous_bad == 0
    # An invalid frame must break, not bridge, a consecutive residual alarm.
    after_invalid = diagnose(Quality.GOOD, 0.012, 0.00361, results[4].continuous_bad)
    assert after_invalid.continuous_bad == 1 and after_invalid.state is DiagnosticState.NORMAL
    trace = uncertainty_trace()
    excite_rate = (trace[0] - trace[599]) / 600.0
    rest_rate = (trace[599] - trace[-1]) / 600.0
    assert rest_rate < excite_rate / 20.0, (excite_rate, rest_rate)


def main() -> None:
    energy_kwh, sigma_kwh = energy_band(0.30, 0.015)
    print(f"[教学示例] SOE 点值={energy_kwh:.3f} kWh, ±1σ={sigma_kwh:.3f} kWh, "
          f"1.96σ下界={energy_kwh - 1.96 * sigma_kwh:.3f} kWh")
    print(f"{'步':>2} {'质量':>8} {'r(V)':>8} {'z':>7} {'NIS':>7} {'连续':>4} {'状态':>10} 动作")
    for index, item in enumerate(run()):
        z = f"{item.standardized_residual:.2f}" if math.isfinite(item.standardized_residual) else "--"
        nis = f"{item.nis:.2f}" if math.isfinite(item.nis) else "--"
        print(f"{index:>2} {item.quality.value:>8} {item.residual_v:>8.3f} {z:>7} {nis:>7} "
              f"{item.continuous_bad:>4} {item.state.value:>10} {item.action}")
    test_ch06()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
