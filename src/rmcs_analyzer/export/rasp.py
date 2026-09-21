"""RASP/ENG motor-curve export for RMCS Analyzer.

The exporter produces a RASP-format motor entry suitable for flight
simulation programs that consume standard .eng motor data.  A single
loaded test exports its standardized measured thrust curve.  Multiple
tests export a single campaign curve built from the selected campaign
population using the same absolute-time population basis used by RMCS
Campaign Analysis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import numpy as np

from ..analysis.motor_class import MotorClassCalculator


MAX_DATA_POINTS = 32


def _finite_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) else None


def _metadata_value(tests: list[Any], attribute: str) -> float | None:
    values = []
    for test in tests:
        value = _finite_float(getattr(test, attribute, None))
        if value is not None and value > 0:
            values.append(value)
    if not values:
        return None
    return float(np.mean(values))


def _common_text(tests: list[Any], attribute: str, fallback: str) -> str:
    values = {
        str(getattr(test, attribute, "")).strip()
        for test in tests
        if str(getattr(test, attribute, "")).strip()
    }
    if len(values) == 1:
        return next(iter(values))
    return fallback


def _test_standardized_curve(test: Any) -> tuple[np.ndarray, np.ndarray]:
    """Return one test's standardized measured curve in relative seconds."""
    if test.analysis_results is None:
        raise ValueError(f"{test.display_name} has not been analyzed.")

    thrust_results = test.analysis_results.thrust
    start = _finite_float(thrust_results.burn_start_5pct_time_s)
    end = _finite_float(thrust_results.burn_end_5pct_time_s)
    if start is None or end is None or end <= start:
        raise ValueError(
            f"{test.display_name} does not have a valid standardized burn interval."
        )

    raw_time = np.asarray(test.data.time_s, dtype=float)
    calibrated = getattr(test.data, "calibrated_time_s", None)
    if calibrated is not None:
        calibrated = np.asarray(calibrated, dtype=float)
    if (
        calibrated is not None
        and calibrated.shape == raw_time.shape
        and calibrated.size > 0
        and np.all(np.isfinite(calibrated))
    ):
        time = calibrated
    else:
        time = raw_time

    values = np.asarray(test.data.thrust_N, dtype=float)
    if time.size != values.size or time.size < 2:
        raise ValueError(f"{test.display_name} does not contain a valid thrust curve.")

    finite = np.isfinite(time) & np.isfinite(values)
    time = time[finite]
    values = values[finite]
    order = np.argsort(time, kind="stable")
    time = time[order]
    values = values[order]
    time, unique_idx = np.unique(time, return_index=True)
    values = values[unique_idx]

    if start < time[0] or end > time[-1]:
        raise ValueError(f"{test.display_name} standardized burn interval is outside its data range.")

    interior = (time > start) & (time < end)
    start_value = float(np.interp(start, time, values))
    end_value = float(np.interp(end, time, values))

    local_time = np.concatenate(([start], time[interior], [end])) - start
    local_thrust = np.concatenate(([start_value], values[interior], [end_value]))
    return local_time, np.maximum(local_thrust, 0.0)


def _reduce_curve(time: np.ndarray, thrust: np.ndarray, max_points: int = MAX_DATA_POINTS) -> tuple[np.ndarray, np.ndarray]:
    """Reduce a dense curve while preserving shape and integrated impulse.

    RASP historically allowed 32 data points including the final zero point.
    We therefore emit at most 31 data rows because the implicit (0,0) start
    is not written. Points are distributed by cumulative impulse so the dense
    portions of the motor curve receive more representation than long low-
    thrust tails. The peak and final zero point are always retained.
    """
    if max_points < 3:
        raise ValueError("max_points must be at least 3")

    time = np.asarray(time, dtype=float)
    thrust = np.asarray(thrust, dtype=float)
    finite = np.isfinite(time) & np.isfinite(thrust)
    time = time[finite]
    thrust = thrust[finite]

    order = np.argsort(time, kind="stable")
    time = time[order]
    thrust = thrust[order]
    time, unique_idx = np.unique(time, return_index=True)
    thrust = thrust[unique_idx]

    if time.size < 2:
        raise ValueError("At least two curve points are required.")

    time = time - float(time[0])
    thrust = np.maximum(thrust, 0.0)
    thrust[-1] = 0.0

    if time[0] == 0.0:
        time = time[1:]
        thrust = thrust[1:]

    if time.size == 0:
        raise ValueError("The curve contains no writable data points.")

    writable_limit = max(2, max_points - 1)
    target_count = min(writable_limit, time.size)
    if time.size <= target_count:
        selected = np.arange(time.size)
    else:
        # Allocate samples by cumulative impulse. This gives much better
        # impulse preservation than uniform time sampling for motors with a
        # short ignition transient followed by a long burn.
        segment_area = np.diff(time) * (thrust[:-1] + thrust[1:]) / 2.0
        cumulative = np.concatenate(([0.0], np.cumsum(segment_area)))
        total = float(cumulative[-1])

        if total > 0:
            targets = np.linspace(0.0, total, target_count)
            selected = np.searchsorted(cumulative, targets, side="left")
        else:
            selected = np.linspace(0, time.size - 1, target_count, dtype=int)

        selected = np.clip(selected, 0, time.size - 1)
        selected = np.unique(selected)
        selected = set(int(index) for index in selected)
        selected.add(int(np.argmax(thrust)))
        selected.add(time.size - 1)

        # If adding the peak produced one extra point, remove the least
        # important non-endpoint/non-peak point using local triangle area.
        peak_index = int(np.argmax(thrust))
        while len(selected) > target_count:
            ordered_selected = sorted(selected)
            removable = [
                index for index in ordered_selected
                if index not in {peak_index, time.size - 1}
            ]
            if not removable:
                break

            def triangle_area(index: int) -> float:
                position = ordered_selected.index(index)
                left = ordered_selected[position - 1]
                right = ordered_selected[position + 1]
                return abs(float(np.trapezoid(
                    thrust[[left, index, right]],
                    time[[left, index, right]],
                )))

            selected.remove(min(removable, key=triangle_area))

        selected = np.asarray(sorted(selected), dtype=int)

    reduced_time = time[selected]
    reduced_thrust = thrust[selected]
    reduced_thrust[-1] = 0.0

    unique_time, unique_idx = np.unique(reduced_time, return_index=True)
    reduced_time = unique_time
    reduced_thrust = reduced_thrust[unique_idx]
    reduced_thrust[-1] = 0.0
    return reduced_time, reduced_thrust

def _header_values(
    test: Any,
    time: np.ndarray,
    thrust: np.ndarray,
    *,
    designation_override: str | None = None,
) -> tuple[str, float, float, str, float, float, str]:
    """Build one RASP header from one measured test."""
    diameter_in = _finite_float(getattr(test, "motor_diameter_in", None))
    length_in = _finite_float(getattr(test, "motor_length_in", None))
    propellant_g = _finite_float(getattr(test, "propellant_mass_g", None))
    initial_mass_g = _finite_float(getattr(test, "initial_mass_g", None))

    diameter_mm = (diameter_in * 25.4) if diameter_in is not None and diameter_in > 0 else 0.0
    length_mm = (length_in * 25.4) if length_in is not None and length_in > 0 else 0.0
    propellant_kg = (propellant_g / 1000.0) if propellant_g is not None and propellant_g > 0 else 0.0
    initial_mass_kg = (initial_mass_g / 1000.0) if initial_mass_g is not None and initial_mass_g > 0 else 0.0

    impulse = float(np.trapezoid(thrust, time)) if time.size > 1 else 0.0
    average = impulse / float(time[-1]) if time[-1] > 0 else 0.0
    classification = MotorClassCalculator().classify(impulse)
    motor_class = classification.motor_class or "U"

    designation = designation_override or str(getattr(test, "motor_designation", "")).strip()
    if not designation:
        designation = f"{motor_class}{round(average):d}"

    manufacturer = str(getattr(test, "manufacturer", "")).strip() or "RMCS"
    manufacturer = "".join(ch for ch in manufacturer if not ch.isspace()) or "RMCS"

    return (
        designation.replace(" ", "_")[:32],
        diameter_mm,
        length_mm,
        "P",
        propellant_kg,
        initial_mass_kg,
        manufacturer[:24],
    )


def _unique_campaign_designations(tests: list[Any]) -> list[str | None]:
    """Return unique motor names for a multi-entry campaign file."""
    bases = [str(getattr(test, "motor_designation", "")).strip() for test in tests]
    counts: dict[str, int] = {}
    for base in bases:
        if base:
            counts[base] = counts.get(base, 0) + 1

    used: set[str] = set()
    overrides: list[str | None] = []
    for index, (test, base) in enumerate(zip(tests, bases), start=1):
        if not base or counts.get(base, 0) == 1:
            candidate = base or None
        else:
            number = str(getattr(test, "test_number", "")).strip()
            suffix = number if number else f"{index:02d}"
            candidate = f"{base}-T{suffix}"

        if candidate and candidate in used:
            candidate = f"{candidate}-{index:02d}"
        if candidate:
            used.add(candidate)
        overrides.append(candidate)

    return overrides


def export_rasp_eng(tests: Iterable[Any], output_path: str | Path) -> Path:
    """Export one test or a selected campaign as a RASP .ENG file.

    A single selected test produces one RASP motor entry. A multi-test
    campaign produces a multi-entry RASP file containing one measured motor
    curve per selected test. This preserves the real variation across a
    campaign instead of collapsing materially different firings into a mean
    curve that no individual motor actually produced.

    Each entry uses RMCS's authoritative standardized 5%-burn interval and
    is independently reduced to the original RASP-compatible 32-point limit.
    """
    tests = list(tests)
    if not tests:
        raise ValueError("Select at least one test for RASP / .ENG export.")

    for test in tests:
        if test.analysis_results is None:
            raise ValueError(f"{test.display_name} has not been analyzed.")

    curves = []
    for test in tests:
        time, thrust = _test_standardized_curve(test)
        time, thrust = _reduce_curve(time, thrust)
        curves.append((test, time, thrust))

    designation_overrides = _unique_campaign_designations(tests)
    entries = []
    for index, (test, time, thrust) in enumerate(curves):
        entries.append(
            (
                test,
                time,
                thrust,
                _header_values(
                    test,
                    time,
                    thrust,
                    designation_override=designation_overrides[index],
                ),
            )
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    mode = "single-test" if len(tests) == 1 else "campaign (one entry per selected test)"
    source_names = ", ".join(test.display_name for test in tests)

    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("; RMCS Analyzer RASP / ENG motor curve\n")
        handle.write(f"; Source: {mode}\n")
        handle.write(f"; Tests: {source_names}\n")
        handle.write("; Delay: P (no ejection charge; static-test curve)\n")
        handle.write(";\n")

        for test, time, thrust, header in entries:
            designation, diameter_mm, length_mm, delay, propellant_kg, initial_mass_kg, manufacturer = header
            handle.write(f"; Test: {test.display_name}\n")
            handle.write(
                f"{designation} {diameter_mm:.0f} {length_mm:.0f} {delay} "
                f"{propellant_kg:.6f} {initial_mass_kg:.6f} {manufacturer}\n"
            )
            for time_s, thrust_n in zip(time, thrust):
                handle.write(f"{time_s:.6f} {thrust_n:.6f}\n")
            handle.write(";\n")

    return output
