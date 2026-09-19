"""Rocket-motor performance extensions.

This module calculates derived performance quantities that require
test metadata and/or auxiliary sensor channels in addition to thrust.

Implemented here:
* Specific impulse (Isp) from measured total impulse and propellant mass.
* Characteristic velocity (C*) from average recorded chamber pressure,
  nozzle throat area, and average propellant mass flow over the
  standardized 5% burn interval.

The calculator never changes TestData or the thrust reduction.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..data.models import TestData


G0_M_PER_S2 = 9.80665
INCH_TO_M = 0.0254
PSI_TO_PA = 6894.757293168


@dataclass(frozen=True)
class PerformanceExtensionResults:
    """Derived performance quantities and availability diagnostics."""

    isp_s: Optional[float] = None
    isp_status: str = "unavailable"

    cstar_m_per_s: Optional[float] = None
    cstar_status: str = "unavailable"

    average_chamber_pressure_psi: Optional[float] = None
    average_mass_flow_kg_per_s: Optional[float] = None


class PerformanceExtensionCalculator:
    """Calculate Isp and average C* from a completed thrust reduction."""

    def calculate(
        self,
        test_data: TestData,
        *,
        total_impulse_Ns: Optional[float],
        burn_start_5pct_time_s: Optional[float],
        burn_end_5pct_time_s: Optional[float],
        burn_time_5pct_s: Optional[float],
    ) -> PerformanceExtensionResults:
        isp, isp_status = self._calculate_isp(
            total_impulse_Ns,
            test_data.metadata.propellant_mass,
        )

        cstar, cstar_status, avg_pressure, avg_mdot = (
            self._calculate_cstar(
                test_data,
                burn_start_5pct_time_s,
                burn_end_5pct_time_s,
                burn_time_5pct_s,
            )
        )

        return PerformanceExtensionResults(
            isp_s=isp,
            isp_status=isp_status,
            cstar_m_per_s=cstar,
            cstar_status=cstar_status,
            average_chamber_pressure_psi=avg_pressure,
            average_mass_flow_kg_per_s=avg_mdot,
        )

    @staticmethod
    def _calculate_isp(
        total_impulse_Ns: Optional[float],
        propellant_mass_g: Optional[float],
    ) -> tuple[Optional[float], str]:
        """Calculate measured specific impulse from total impulse."""

        if total_impulse_Ns is None or not np.isfinite(total_impulse_Ns):
            return None, "Total impulse unavailable."

        if propellant_mass_g is None:
            return None, "Propellant mass required."

        if not np.isfinite(propellant_mass_g) or propellant_mass_g <= 0:
            return None, "Valid propellant mass required."

        propellant_mass_kg = propellant_mass_g / 1000.0

        isp = (
            total_impulse_Ns
            / (propellant_mass_kg * G0_M_PER_S2)
        )

        if not np.isfinite(isp) or isp <= 0:
            return None, "Isp calculation unavailable."

        return float(isp), "available"

    def _calculate_cstar(
        self,
        test_data: TestData,
        burn_start_s: Optional[float],
        burn_end_s: Optional[float],
        burn_time_s: Optional[float],
    ) -> tuple[
        Optional[float],
        str,
        Optional[float],
        Optional[float],
    ]:
        """Calculate average C* over the standardized 5% burn interval."""

        if test_data.pressure_psi is None:
            return None, "Pressure data required.", None, None

        pressure = np.asarray(test_data.pressure_psi, dtype=float)

        if pressure.size == 0:
            return None, "Pressure data required.", None, None

        throat_in = test_data.metadata.nozzle_throat

        if throat_in is None:
            return None, "Nozzle throat diameter required.", None, None

        if not np.isfinite(throat_in) or throat_in <= 0:
            return None, "Valid nozzle throat diameter required.", None, None

        propellant_mass_g = test_data.metadata.propellant_mass

        if propellant_mass_g is None:
            return None, "Propellant mass required.", None, None

        if not np.isfinite(propellant_mass_g) or propellant_mass_g <= 0:
            return None, "Valid propellant mass required.", None, None

        if (
            burn_start_s is None
            or burn_end_s is None
            or burn_time_s is None
            or not np.isfinite(burn_start_s)
            or not np.isfinite(burn_end_s)
            or not np.isfinite(burn_time_s)
            or burn_end_s <= burn_start_s
            or burn_time_s <= 0
        ):
            return None, "Standardized burn interval required.", None, None

        time_s = self._analysis_time(test_data)

        if time_s.size != pressure.size:
            return (
                None,
                "Pressure/time channels have incompatible lengths.",
                None,
                None,
            )

        finite = np.isfinite(time_s) & np.isfinite(pressure)
        time_s = time_s[finite]
        pressure = pressure[finite]

        if time_s.size < 2:
            return None, "Insufficient pressure data.", None, None

        order = np.argsort(time_s, kind="stable")
        time_s = time_s[order]
        pressure = pressure[order]

        unique_time, unique_idx = np.unique(time_s, return_index=True)
        time_s = unique_time
        pressure = pressure[unique_idx]

        if time_s.size < 2:
            return None, "Insufficient pressure data.", None, None

        if burn_start_s < time_s[0] or burn_end_s > time_s[-1]:
            return (
                None,
                "Pressure data does not cover the standardized burn interval.",
                None,
                None,
            )

        # Interpolate pressure at the exact standardized burn boundaries.
        start_pressure = float(np.interp(burn_start_s, time_s, pressure))
        end_pressure = float(np.interp(burn_end_s, time_s, pressure))

        inside = (time_s > burn_start_s) & (time_s < burn_end_s)

        interval_time = np.concatenate(
            ([burn_start_s], time_s[inside], [burn_end_s])
        )
        interval_pressure = np.concatenate(
            ([start_pressure], pressure[inside], [end_pressure])
        )

        if interval_time.size < 2:
            return None, "Insufficient pressure data in burn interval.", None, None

        # Time-weighted average chamber pressure.
        pressure_impulse = np.trapezoid(
            interval_pressure,
            interval_time,
        )

        avg_pressure_psi = pressure_impulse / burn_time_s

        if not np.isfinite(avg_pressure_psi) or avg_pressure_psi <= 0:
            return None, "Valid chamber pressure unavailable.", None, None

        propellant_mass_kg = propellant_mass_g / 1000.0
        avg_mdot = propellant_mass_kg / burn_time_s

        throat_m = throat_in * INCH_TO_M
        throat_area_m2 = np.pi * (throat_m ** 2) / 4.0

        avg_pressure_pa = avg_pressure_psi * PSI_TO_PA

        cstar = avg_pressure_pa * throat_area_m2 / avg_mdot

        if not np.isfinite(cstar) or cstar <= 0:
            return None, "C* calculation unavailable.", None, None

        return (
            float(cstar),
            "available",
            float(avg_pressure_psi),
            float(avg_mdot),
        )

    @staticmethod
    def _analysis_time(test_data: TestData) -> np.ndarray:
        """Return the calibrated analysis timeline when valid."""

        time_s = np.asarray(
            test_data.time_s,
            dtype=float,
        )

        calibrated = test_data.calibrated_time_s

        if calibrated is not None:
            calibrated = np.asarray(
                calibrated,
                dtype=float,
            )

            if (
                calibrated.shape == time_s.shape
                and calibrated.size > 0
                and np.all(np.isfinite(calibrated))
            ):
                return calibrated

        return time_s
