"""
RMCS Analyzer - Zerox Reference Validation

This test validates the Analyzer against the standardized Zerox reference
dataset and documents the relationship between the source video label and
the measured values contained in the CSV.

The source-video label is retained only as source context. It is not treated
as an independent calculated validation target.
"""

from pathlib import Path

from src.rmcs_analyzer.analysis.analyzer import AnalysisEngine
from src.rmcs_analyzer.data.csv_reader import RMCSCSVReader


PROJECT_ROOT = Path(__file__).resolve().parent
ZER0X_FILE = PROJECT_ROOT / "test_data" / "Zerox.csv"


EXPECTED_SAMPLE_COUNT = 661
EXPECTED_DURATION_S = 8.538000
EXPECTED_PEAK_THRUST_N = 3230.339730

EXPECTED_BURN_START_S = 0.044210
EXPECTED_BURN_END_S = 7.117326
EXPECTED_BURN_TIME_S = 7.073116

EXPECTED_TOTAL_IMPULSE_NS = 14471.744320
EXPECTED_AVERAGE_THRUST_N = 2031.225247
EXPECTED_DESIGNATION = "N2031"


def assert_close(actual, expected, tolerance=1e-6, label="value"):
    if abs(actual - expected) > tolerance:
        raise AssertionError(
            f"{label}: expected {expected}, got {actual}"
        )


def _script_regression():
    print("RMCS Analyzer Zerox Reference Validation")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Load standardized reference data
    # ------------------------------------------------------------------

    reader = RMCSCSVReader()
    test_data = reader.read(ZER0X_FILE)

    # ------------------------------------------------------------------
    # Source evidence
    # ------------------------------------------------------------------

    print()
    print("SOURCE EVIDENCE")
    print("-" * 70)

    video_label = "N2300"

    duration = test_data.duration_s
    maximum_thrust = float(test_data.thrust_N.max())

    print(f"Video label:             {video_label}")
    print(f"CSV curve duration:      {duration:.6f} s")
    print(f"CSV maximum thrust:      {maximum_thrust:.6f} N")

    assert test_data.sample_count == EXPECTED_SAMPLE_COUNT

    assert_close(
        duration,
        EXPECTED_DURATION_S,
        tolerance=1e-9,
        label="CSV duration",
    )

    assert_close(
        maximum_thrust,
        EXPECTED_PEAK_THRUST_N,
        tolerance=1e-6,
        label="CSV maximum thrust",
    )

    print()
    print("Direct video/CSV agreement: PASSED")
    print(
        "  Video reaches 08.538 s at the end of the displayed test."
    )
    print(
        "  Video graph peak is labeled 3230 N."
    )
    print(
        "  Zerox.csv contains the same duration and peak."
    )

    # ------------------------------------------------------------------
    # Authoritative Analyzer regression
    # ------------------------------------------------------------------

    results = AnalysisEngine().analyze(test_data)
    thrust = results.thrust

    assert_close(
        thrust.burn_start_5pct_time_s,
        EXPECTED_BURN_START_S,
        tolerance=1e-6,
        label="5% start",
    )

    assert_close(
        thrust.burn_end_5pct_time_s,
        EXPECTED_BURN_END_S,
        tolerance=1e-6,
        label="5% end",
    )

    assert_close(
        thrust.burn_time_5pct_s,
        EXPECTED_BURN_TIME_S,
        tolerance=1e-6,
        label="5% burn time",
    )

    assert_close(
        thrust.total_impulse_valid_curve_Ns,
        EXPECTED_TOTAL_IMPULSE_NS,
        tolerance=1e-6,
        label="total impulse",
    )

    assert_close(
        thrust.average_thrust_5pct_N,
        EXPECTED_AVERAGE_THRUST_N,
        tolerance=1e-6,
        label="average thrust",
    )

    if thrust.designation != EXPECTED_DESIGNATION:
        raise AssertionError(
            f"designation: expected {EXPECTED_DESIGNATION}, "
            f"got {thrust.designation}"
        )

    print()
    print("Current reduction regression: PASSED")
    print(
        f"  5% start:               "
        f"{thrust.burn_start_5pct_time_s:.6f} s"
    )
    print(
        f"  5% end:                 "
        f"{thrust.burn_end_5pct_time_s:.6f} s"
    )
    print(
        f"  5% burn time:           "
        f"{thrust.burn_time_5pct_s:.6f} s"
    )
    print(
        f"  Total impulse:          "
        f"{thrust.total_impulse_valid_curve_Ns:.6f} Ns"
    )
    print(
        f"  Current average:        "
        f"{thrust.average_thrust_5pct_N:.6f} N"
    )
    print(
        f"  Current designation:    "
        f"{thrust.designation}"
    )

    # ------------------------------------------------------------------
    # Source label clarification
    # ------------------------------------------------------------------

    print()
    print("SOURCE LABEL CLARIFICATION")
    print("-" * 70)

    print(
        "N2300 source label:      INFORMAL VISUAL ESTIMATE"
    )
    print(
        "Measured calculation:    NOT PROVIDED"
    )
    print(
        "Average thrust value:    NOT USED AS A VALIDATION TARGET"
    )

    print()
    print(
        "The N2300 label is retained only as source-video context "
        "and is not used as an independent validation target."
    )

    print()
    print("=" * 70)
    print("ALL ZER0X REFERENCE VALIDATION TESTS PASSED")
    print("=" * 70)


def test_script_regression():
    _script_regression()


if __name__ == "__main__":
    _script_regression()
