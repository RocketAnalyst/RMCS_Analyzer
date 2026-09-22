"""Engineering summary CSV export for RMCS Analyzer.

The Analysis CSV is intentionally different from the BurnSim experimental
trace export and the RASP motor-curve export. It contains one row per
selected test, combining project/test metadata with authoritative
AnalysisResults metrics so the resulting file can be used for campaign-level
analysis in Excel, Python, or other data-analysis tools.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable


# Keep the schema explicit and stable. Units are part of the column names so
# exported values remain unambiguous when the CSV is used outside RMCS.
COLUMNS = [
    ("Test Number", "test_number"),
    ("Test Name", "test_name"),
    ("Source File", "source_file"),
    ("Test Date", "test_date"),
    ("Test Stand", "test_stand"),
    ("Test Operator", "test_operator"),
    ("Location", "location"),
    ("Motor Designation", "motor_designation"),
    ("Calculated Designation", "calculated_designation"),
    ("Motor Type", "motor_type"),
    ("Manufacturer", "manufacturer"),
    ("Builder", "builder"),
    ("Case Material", "case_material"),
    ("Motor Diameter (mm)", "motor_diameter_mm"),
    ("Motor Length (mm)", "motor_length_mm"),
    ("Initial Mass (g)", "initial_mass_g"),
    ("Propellant Mass (g)", "propellant_mass_g"),
    ("Propellant Type", "propellant_type"),
    ("Nozzle Throat (in)", "nozzle_throat_in"),
    ("Nozzle Exit (in)", "nozzle_exit_in"),
    ("Nozzle Material", "nozzle_material"),
    ("Load Cell", "load_cell"),
    ("Load Cell Calibration", "load_cell_calibration"),
    ("Pressure Sensor", "pressure_sensor"),
    ("Pressure Sensor Calibration", "pressure_sensor_calibration"),
    ("Sample Rate (Hz)", "sample_rate_hz"),
    ("Case Pressure Limit (psi)", "case_pressure_limit_psi"),
    ("Sample Count", "sample_count"),
    ("Recording Duration (s)", "recording_duration_s"),
    ("Peak Thrust (N)", "peak_thrust_N"),
    ("Peak Thrust Time (s)", "peak_thrust_time_s"),
    ("Average Thrust (N)", "average_thrust_N"),
    ("Average Thrust (5% Burn Curve) (N)", "average_thrust_5pct_N"),
    ("Burn Time (s)", "burn_time_s"),
    ("Time to Peak (s)", "time_to_peak_s"),
    ("Total Impulse (N·s)", "total_impulse_Ns"),
    ("Normalized Impulse (N·s)", "normalized_impulse_Ns"),
    ("Initial Thrust Average (N)", "initial_thrust_average_N"),
    ("Initial Thrust Window (s)", "initial_thrust_window_s"),
    ("Thrust Rise Rate (N/s)", "thrust_rise_rate_N_per_s"),
    ("Thrust Decay Rate (N/s)", "thrust_decay_rate_N_per_s"),
    ("Average Chamber Pressure (psi)", "average_chamber_pressure_psi"),
    ("Average Mass Flow (kg/s)", "average_mass_flow_kg_per_s"),
    ("Isp (s)", "isp_s"),
    ("Isp Status", "isp_status"),
    ("C* (m/s)", "cstar_m_per_s"),
    ("C* Status", "cstar_status"),
    ("Motor Class", "motor_class"),
    ("Class Lower Limit (N·s)", "class_lower_limit_Ns"),
    ("Class Upper Limit (N·s)", "class_upper_limit_Ns"),
    ("Ignition Time (s)", "ignition_time_s"),
    ("Burnout Time (s)", "burnout_time_s"),
    ("Notes", "notes"),
]


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _number(value: Any) -> float | int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and abs(result) != float("inf") else None


def _test_value(test: Any, key: str) -> Any:
    analysis = getattr(test, "analysis_results", None)
    thrust = getattr(analysis, "thrust", None) if analysis is not None else None
    classification = getattr(analysis, "classification", None) if analysis is not None else None
    events = getattr(analysis, "events", None) if analysis is not None else None
    data = getattr(test, "data", None)

    if key == "test_number":
        return _clean_text(getattr(test, "test_number", ""))
    if key == "test_name":
        return getattr(test, "display_name", "")
    if key == "source_file":
        return getattr(test, "filename", "")

    test_fields = {
        "test_date", "test_stand", "test_operator", "location",
        "motor_designation", "motor_type", "manufacturer", "builder",
        "case_material", "motor_diameter_mm", "motor_length_mm",
        "initial_mass_g", "propellant_mass_g", "propellant_type",
        "nozzle_throat_in", "nozzle_exit_in", "nozzle_material", "load_cell",
        "load_cell_calibration", "pressure_sensor", "pressure_sensor_calibration",
        "sample_rate_hz", "case_pressure_limit_psi", "notes",
    }
    if key in test_fields:
        return getattr(test, key, None)

    if key == "calculated_designation":
        return getattr(thrust, "designation", None)
    if key == "sample_count":
        return getattr(data, "sample_count", None)
    if key == "recording_duration_s":
        return getattr(data, "duration_s", None)

    thrust_fields = {
        "peak_thrust_N", "peak_thrust_time_s", "average_thrust_N",
        "average_thrust_5pct_N", "time_to_peak_s", "normalized_impulse_Ns",
        "initial_thrust_average_N", "initial_thrust_window_s",
        "thrust_rise_rate_N_per_s", "thrust_decay_rate_N_per_s",
        "average_chamber_pressure_psi", "average_mass_flow_kg_per_s", "isp_s",
        "isp_status", "cstar_m_per_s", "cstar_status",
    }
    if key == "average_thrust_N":
        value = getattr(thrust, "average_thrust_5pct_N", None)
        return value if value is not None else getattr(thrust, "average_thrust_N", None)

    if key in thrust_fields:
        return getattr(thrust, key, None)

    if key == "burn_time_s":
        return getattr(thrust, "burn_time_5pct_s", None) or getattr(thrust, "burn_time_s", None)

    if key == "total_impulse_Ns":
        value = getattr(thrust, "total_impulse_valid_curve_Ns", None)
        if value is None:
            value = getattr(thrust, "total_impulse_Ns", None)
        return value

    if key == "motor_class":
        return getattr(classification, "motor_class", None)
    if key == "class_lower_limit_Ns":
        return getattr(classification, "lower_limit_Ns", None)
    if key == "class_upper_limit_Ns":
        return getattr(classification, "upper_limit_Ns", None)

    if key == "ignition_time_s":
        event = getattr(events, "ignition", None) if events is not None else None
        return getattr(event, "time_s", None) if event is not None else None
    if key == "burnout_time_s":
        event = getattr(events, "burnout", None) if events is not None else None
        return getattr(event, "time_s", None) if event is not None else None

    return None


def _format_value(value: Any, key: str) -> str | int | float:
    if isinstance(value, str):
        return value
    if value is None:
        return ""

    numeric = _number(value)
    if numeric is not None:
        # Keep CSV numeric cells numeric. Six decimal places is enough to
        # preserve the precision used by the existing RMCS analysis/export
        # workflows while remaining Excel-friendly.
        return f"{numeric:.6f}".rstrip("0").rstrip(".")

    return _clean_text(value)


def _row_for_test(test: Any) -> list[Any]:
    if getattr(test, "analysis_results", None) is None:
        raise ValueError(f"{test.display_name} has not been analyzed.")

    return [
        _format_value(_test_value(test, key), key)
        for _, key in COLUMNS
    ]


def export_analysis_csv(tests: Iterable[Any], output_path: str | Path) -> Path:
    """Export authoritative analysis results for one or more tests.

    The export contains one row per supplied test. All tests must have
    completed analysis results; a partially analyzed campaign is rejected so
    the resulting dataset cannot silently mix complete and incomplete rows.
    """
    test_list = list(tests)
    if not test_list:
        raise ValueError("At least one test is required for Analysis CSV export.")

    missing = [
        getattr(test, "display_name", "Unnamed Test")
        for test in test_list
        if getattr(test, "analysis_results", None) is None
    ]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"The following tests have not been analyzed: {names}")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow([label for label, _ in COLUMNS])
        for test in test_list:
            writer.writerow(_row_for_test(test))

    return output
