"""Regression test for the application's default processing/analysis path."""

from pathlib import Path

import numpy as np

from src.rmcs_analyzer.analysis.analyzer import AnalysisEngine
from src.rmcs_analyzer.data.csv_reader import RMCSCSVReader
from src.rmcs_analyzer.processing.pipeline import ProcessingPipeline
from src.rmcs_analyzer.processing.settings import ProcessingSettings


PROJECT_ROOT = Path(__file__).resolve().parent
ZER0X_FILE = PROJECT_ROOT / "test_data" / "Zerox.csv"

EXPECTED_PEAK_N = 3230.339730
EXPECTED_AVERAGE_N = 2031.225247
EXPECTED_IMPULSE_NS = 14471.744320
EXPECTED_BURN_S = 7.073116
EXPECTED_INITIAL_N = 2635.834021
EXPECTED_DESIGNATION = "N2031"


def assert_close(actual, expected, tolerance=1e-6, label="value"):
    if abs(actual - expected) > tolerance:
        raise AssertionError(
            f"{label}: expected {expected}, got {actual}"
        )


def _script_regression():
    print("RMCS Analyzer Application Analysis Path Regression")
    print("=" * 70)

    reader = RMCSCSVReader()
    test_data = reader.read(ZER0X_FILE)

    # Direct authoritative analysis is the reference path.
    direct = AnalysisEngine().analyze(test_data)

    # This is the same default processing path used by the application.
    processing = ProcessingPipeline().process(
        test_data,
        ProcessingSettings(),
    )

    if processing.baseline_result is not None:
        raise AssertionError(
            "Default processing unexpectedly applied baseline correction."
        )

    if processing.alignment_result.offset_s != 0.0:
        raise AssertionError(
            "Default processing unexpectedly aligned the time axis."
        )

    prepared = processing.prepared_data
    application = AnalysisEngine().analyze(
        prepared,
        events=processing.event_set,
    )

    print()
    print("DEFAULT PROCESSING")
    print("-" * 70)
    print(f"Samples:                 {prepared.sample_count}")
    print(f"Time start:              {prepared.time_s[0]:.6f} s")
    print(f"Time end:                {prepared.time_s[-1]:.6f} s")
    print(f"Baseline correction:     NOT APPLIED")
    print(f"Time alignment:          NOT APPLIED")

    print()
    print("AUTHORITATIVE RESULTS")
    print("-" * 70)

    direct_thrust = direct.thrust
    application_thrust = application.thrust

    assert_close(
        application_thrust.peak_thrust_N,
        EXPECTED_PEAK_N,
        label="peak thrust",
    )
    assert_close(
        application_thrust.average_thrust_5pct_N,
        EXPECTED_AVERAGE_N,
        label="average thrust",
    )
    assert_close(
        application_thrust.total_impulse_valid_curve_Ns,
        EXPECTED_IMPULSE_NS,
        label="total impulse",
    )
    assert_close(
        application_thrust.burn_time_5pct_s,
        EXPECTED_BURN_S,
        label="5% burn time",
    )
    assert_close(
        application_thrust.initial_thrust_average_N,
        EXPECTED_INITIAL_N,
        label="initial thrust average",
    )

    if application_thrust.designation != EXPECTED_DESIGNATION:
        raise AssertionError(
            f"designation: expected {EXPECTED_DESIGNATION}, "
            f"got {application_thrust.designation}"
        )

    # Verify the application path agrees with direct authoritative analysis.
    assert_close(
        application_thrust.peak_thrust_N,
        direct_thrust.peak_thrust_N,
        label="direct/application peak agreement",
    )
    assert_close(
        application_thrust.average_thrust_5pct_N,
        direct_thrust.average_thrust_5pct_N,
        label="direct/application average agreement",
    )
    assert_close(
        application_thrust.total_impulse_valid_curve_Ns,
        direct_thrust.total_impulse_valid_curve_Ns,
        label="direct/application impulse agreement",
    )
    assert_close(
        application_thrust.burn_time_5pct_s,
        direct_thrust.burn_time_5pct_s,
        label="direct/application burn agreement",
    )

    if application_thrust.designation != direct_thrust.designation:
        raise AssertionError(
            "Direct and application designations do not agree."
        )

    if not np.array_equal(
        prepared.thrust_N,
        test_data.thrust_N,
    ):
        raise AssertionError(
            "Default processing changed the authoritative thrust samples."
        )

    if not np.array_equal(
        prepared.calibrated_time_s,
        test_data.calibrated_time_s,
    ):
        raise AssertionError(
            "Default processing changed the calibrated time samples."
        )

    print(f"Peak thrust:             {application_thrust.peak_thrust_N:.6f} N")
    print(f"Average thrust:          {application_thrust.average_thrust_5pct_N:.6f} N")
    print(f"Total impulse:           {application_thrust.total_impulse_valid_curve_Ns:.6f} Ns")
    print(f"5% burn time:            {application_thrust.burn_time_5pct_s:.6f} s")
    print(f"Initial thrust average:  {application_thrust.initial_thrust_average_N:.6f} N")
    print(f"Designation:             {application_thrust.designation}")

    print()
    print("Direct/application agreement: PASSED")
    print("Raw thrust preserved:          PASSED")
    print("Calibrated time preserved:     PASSED")
    print()
    print("=" * 70)
    print("APPLICATION ANALYSIS PATH REGRESSION PASSED")
    print("=" * 70)



def test_script_regression():
    _script_regression()


if __name__ == "__main__":
    _script_regression()
