# @AI_GENERATED
"""Chapter 07: risk-aware station SOE and 30-minute SOP [teaching example].

The module is deterministic and standard-library-only.  It consumes Chapter 06
quality state and shared site constants; it does not replace BMS protection.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from ch06_uncertainty_diagnostics import DiagnosticState
from soc_core import PCS_RATED_KW, SITE_NOMINAL_ENERGY_KWH


@dataclass(frozen=True)
class CapabilityInput:
    soc: float
    estimate_margin_soc: float
    lowest_cluster_gap_soc: float
    capacity_soh: float
    discharge_efficiency: float
    minimum_soc: float
    duration_s: float
    bms_discharge_limit_kw: float
    grid_export_limit_kw: float
    diagnostic_state: DiagnosticState = DiagnosticState.NORMAL


@dataclass(frozen=True)
class CapabilityResult:
    conservative_lowest_soc: float
    effective_capacity_kwh: float
    soe_ac_kwh: float
    energy_limit_kw: float
    sop_kw: float
    requested_duration_min: float
    duration_at_grid_limit_min: float
    limiting_reason: str
    action: str
    limits_kw: Dict[str, float]


def assess_capability(data: CapabilityInput) -> CapabilityResult:
    """Calculate discharge-direction SOE and SOP(T) on the AC measurement plane."""
    if not 0.0 <= data.soc <= 1.0 or data.estimate_margin_soc < 0.0:
        raise ValueError("invalid SOC input")
    if data.lowest_cluster_gap_soc < 0.0 or not 0.0 <= data.minimum_soc < 1.0:
        raise ValueError("invalid SOC reserve")
    if not 0.0 < data.capacity_soh <= 1.0 or not 0.0 < data.discharge_efficiency <= 1.0:
        raise ValueError("invalid SOH or efficiency")
    if data.duration_s <= 0.0 or data.bms_discharge_limit_kw < 0.0 or data.grid_export_limit_kw < 0.0:
        raise ValueError("invalid duration or power limit")
    if data.diagnostic_state is DiagnosticState.INVALID:
        return CapabilityResult(0.0, 0.0, 0.0, 0.0, 0.0, data.duration_s / 60.0, 0.0,
                                "invalid telemetry", "do not issue dispatch; obtain fresh aligned data", {})
    margin_factor = 1.5 if data.diagnostic_state is DiagnosticState.DEGRADED else 1.0
    lowest_soc = max(0.0, data.soc - margin_factor * data.estimate_margin_soc
                     - data.lowest_cluster_gap_soc)
    effective_capacity_kwh = SITE_NOMINAL_ENERGY_KWH * data.capacity_soh
    soe_ac_kwh = max(0.0, lowest_soc - data.minimum_soc) * effective_capacity_kwh * data.discharge_efficiency
    energy_limit_kw = soe_ac_kwh / (data.duration_s / 3600.0)
    limits = {
        "energy_30min": energy_limit_kw,
        "BMS_DC_to_AC": data.bms_discharge_limit_kw,
        "PCS_AC": PCS_RATED_KW,
        "grid_export": data.grid_export_limit_kw,
    }
    sop_kw = min(limits.values())
    limiting_reason = min(limits, key=limits.get)
    duration_at_grid_limit = (soe_ac_kwh / data.grid_export_limit_kw * 60.0
                              if data.grid_export_limit_kw > 0.0 else 0.0)
    action = ("derate and replan; capability is degraded" if data.diagnostic_state is DiagnosticState.DEGRADED
              else "publish bounded capability with bottleneck reason")
    return CapabilityResult(lowest_soc, effective_capacity_kwh, soe_ac_kwh, energy_limit_kw,
                            sop_kw, data.duration_s / 60.0, duration_at_grid_limit,
                            limiting_reason, action, limits)


def late_peak_input(state: DiagnosticState = DiagnosticState.NORMAL) -> CapabilityInput:
    """Return the Chapter 00 17:30/18:00 late-peak case, all values [teaching example]."""
    return CapabilityInput(
        soc=0.30, estimate_margin_soc=0.03, lowest_cluster_gap_soc=0.02,
        capacity_soh=0.92, discharge_efficiency=0.931, minimum_soc=0.10,
        duration_s=30.0 * 60.0, bms_discharge_limit_kw=2200.0,
        grid_export_limit_kw=2000.0, diagnostic_state=state,
    )


def test_ch07() -> None:
    normal = assess_capability(late_peak_input())
    assert round(normal.conservative_lowest_soc, 2) == 0.25
    assert round(normal.effective_capacity_kwh, 1) == 4614.7
    assert round(normal.soe_ac_kwh, 1) == 644.4
    assert round(normal.sop_kw, 1) == round(normal.energy_limit_kw, 1)
    assert 19.0 < normal.duration_at_grid_limit_min < 19.5
    degraded = assess_capability(late_peak_input(DiagnosticState.DEGRADED))
    assert degraded.soe_ac_kwh < normal.soe_ac_kwh and degraded.action.startswith("derate")
    invalid = assess_capability(late_peak_input(DiagnosticState.INVALID))
    assert invalid.sop_kw == 0.0 and invalid.limiting_reason == "invalid telemetry"


def main() -> None:
    normal = assess_capability(late_peak_input())
    print("[教学示例] 18:00 晚峰，放电方向、AC测量平面、30 min窗口")
    print(f"保守最低簇SOC={normal.conservative_lowest_soc:.3f}; 有效容量={normal.effective_capacity_kwh:.1f} kWh")
    print(f"SOE={normal.soe_ac_kwh:.1f} kWh; 30 min 能量限值={normal.energy_limit_kw:.1f} kW")
    print("约束(kW): " + ", ".join(f"{name}={value:.1f}" for name, value in normal.limits_kw.items()))
    print(f"SOP(30 min)={normal.sop_kw:.1f} kW; 瓶颈={normal.limiting_reason}; "
          f"按2 MW可持续={normal.duration_at_grid_limit_min:.1f} min")
    degraded = assess_capability(late_peak_input(DiagnosticState.DEGRADED))
    print(f"degraded: SOE={degraded.soe_ac_kwh:.1f} kWh, SOP={degraded.sop_kw:.1f} kW, {degraded.action}")
    test_ch07()
    print("自检通过")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
