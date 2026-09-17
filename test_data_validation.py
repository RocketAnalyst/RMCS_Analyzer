from pathlib import Path

import numpy as np

from src.rmcs_analyzer.data import RMCSCSVReader
from src.rmcs_analyzer.data.models import TestData
from src.rmcs_analyzer.processing.validation import DataValidator


PROJECT_ROOT = Path(__file__).resolve().parent
TEST_DATA_FOLDER = PROJECT_ROOT / "test_data"


def print_report(
    name,
    report,
):
    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    print(
        f"Status:                  {report.status}"
    )

    print(
        f"Valid:                   {report.valid}"
    )

    print(
        f"Sample count:            {report.sample_count}"
    )

    if report.sample_rate_hz is not None:

        print(
            f"Sample rate:             "
            f"{report.sample_rate_hz:.3f} Hz"
        )

    else:

        print(
            "Sample rate:             —"
        )

    print(
        f"Time valid:              {report.time_valid}"
    )

    print(
        f"Thrust valid:            {report.thrust_valid}"
    )

    print(
        f"Time monotonic:          {report.time_monotonic}"
    )

    print(
        f"Duplicate timestamps:    "
        f"{report.duplicate_timestamps}"
    )

    print(
        f"Missing time values:     "
        f"{report.missing_time_values}"
    )

    print(
        f"Missing thrust values:   "
        f"{report.missing_thrust_values}"
    )

    print(
        f"Infinite time values:    "
        f"{report.infinite_time_values}"
    )

    print(
        f"Infinite thrust values:  "
        f"{report.infinite_thrust_values}"
    )

    print(
        f"Sampling gaps:           "
        f"{report.sampling_gap_count}"
    )

    if report.largest_sampling_gap_s is not None:

        print(
            f"Largest sampling gap:    "
            f"{report.largest_sampling_gap_s:.6f} s"
        )

    else:

        print(
            "Largest sampling gap:    —"
        )

    if report.errors:

        print()
        print("ERRORS:")

        for issue in report.errors:

            print(
                f"  [{issue.code}] "
                f"{issue.message}"
            )

    if report.warnings:

        print()
        print("WARNINGS:")

        for issue in report.warnings:

            print(
                f"  [{issue.code}] "
                f"{issue.message}"
            )


def validate_real_csv(
    filename,
):
    """Load and validate a real RMCS CSV file."""

    path = (
        TEST_DATA_FOLDER
        / filename
    )

    if not path.exists():

        print(
            f"\nWARNING: Test file not found: {path}"
        )

        return None

    reader = RMCSCSVReader()

    test_data = reader.read(
        str(path)
    )

    report = DataValidator.validate(
        test_data
    )

    print_report(
        filename,
        report,
    )

    return report


def build_valid_test_data():
    """Create a small valid dataset."""

    time_s = np.array(
        [
            0.000,
            0.010,
            0.020,
            0.030,
            0.040,
        ],
        dtype=float,
    )

    thrust_N = np.array(
        [
            0.0,
            10.0,
            25.0,
            15.0,
            0.0,
        ],
        dtype=float,
    )

    return TestData(
        time_s=time_s,
        thrust_N=thrust_N,
    )


def test_valid_data():
    """A normal dataset should be valid."""

    test_data = build_valid_test_data()

    report = DataValidator.validate(
        test_data
    )

    print_report(
        "Synthetic valid dataset",
        report,
    )

    assert report.valid
    assert report.status == "VALID"
    assert report.sample_count == 5
    assert report.time_valid
    assert report.thrust_valid
    assert report.time_monotonic
    assert report.duplicate_timestamps == 0
    assert report.sampling_gap_count == 0


def test_duplicate_timestamps():
    """Duplicate timestamps should produce an error."""

    test_data = TestData(
        time_s=np.array(
            [
                0.00,
                0.01,
                0.01,
                0.02,
            ]
        ),
        thrust_N=np.array(
            [
                0.0,
                10.0,
                15.0,
                0.0,
            ]
        ),
    )

    report = DataValidator.validate(
        test_data
    )

    print_report(
        "Synthetic duplicate timestamp dataset",
        report,
    )

    assert not report.valid
    assert any(
        issue.code == "DUPLICATE_TIMESTAMPS"
        for issue in report.errors
    )


def test_non_monotonic_time():
    """Time moving backward should produce an error."""

    test_data = TestData(
        time_s=np.array(
            [
                0.00,
                0.01,
                0.005,
                0.02,
            ]
        ),
        thrust_N=np.array(
            [
                0.0,
                10.0,
                15.0,
                0.0,
            ]
        ),
    )

    report = DataValidator.validate(
        test_data
    )

    print_report(
        "Synthetic non-monotonic time dataset",
        report,
    )

    assert not report.valid
    assert any(
        issue.code == "TIME_NOT_MONOTONIC"
        for issue in report.errors
    )


def test_missing_values():
    """NaN values should produce errors."""

    test_data = TestData(
        time_s=np.array(
            [
                0.00,
                0.01,
                np.nan,
                0.03,
            ]
        ),
        thrust_N=np.array(
            [
                0.0,
                10.0,
                15.0,
                np.nan,
            ]
        ),
    )

    report = DataValidator.validate(
        test_data
    )

    print_report(
        "Synthetic missing-value dataset",
        report,
    )

    assert not report.valid
    assert report.missing_time_values == 1
    assert report.missing_thrust_values == 1

    assert any(
        issue.code == "TIME_MISSING_VALUES"
        for issue in report.errors
    )

    assert any(
        issue.code == "THRUST_MISSING_VALUES"
        for issue in report.errors
    )


def test_infinite_values():
    """Infinite values should produce errors."""

    test_data = TestData(
        time_s=np.array(
            [
                0.00,
                0.01,
                0.02,
                np.inf,
            ]
        ),
        thrust_N=np.array(
            [
                0.0,
                10.0,
                -np.inf,
                0.0,
            ]
        ),
    )

    report = DataValidator.validate(
        test_data
    )

    print_report(
        "Synthetic infinite-value dataset",
        report,
    )

    assert not report.valid
    assert report.infinite_time_values == 1
    assert report.infinite_thrust_values == 1


def test_array_length_mismatch():
    """Mismatched primary channel lengths should produce an error."""

    test_data = TestData(
        time_s=np.array(
            [
                0.00,
                0.01,
                0.02,
            ]
        ),
        thrust_N=np.array(
            [
                0.0,
                10.0,
            ]
        ),
    )

    report = DataValidator.validate(
        test_data
    )

    print_report(
        "Synthetic array-length mismatch dataset",
        report,
    )

    assert not report.valid

    assert any(
        issue.code == "ARRAY_LENGTH_MISMATCH"
        for issue in report.errors
    )


def test_optional_channel_length_mismatch():
    """Optional channels must match the primary sample count."""

    test_data = TestData(
        time_s=np.array(
            [
                0.00,
                0.01,
                0.02,
                0.03,
            ]
        ),
        thrust_N=np.array(
            [
                0.0,
                10.0,
                15.0,
                0.0,
            ]
        ),
        pressure_kPa=np.array(
            [
                100.0,
                101.0,
                102.0,
            ]
        ),
    )

    report = DataValidator.validate(
        test_data
    )

    print_report(
        "Synthetic optional-channel mismatch dataset",
        report,
    )

    assert not report.valid

    assert any(
        issue.code == "OPTIONAL_CHANNEL_LENGTH_MISMATCH"
        for issue in report.errors
    )


def test_sampling_gap():
    """An unusually large time gap should produce a warning."""

    test_data = TestData(
        time_s=np.array(
            [
                0.00,
                0.01,
                0.02,
                0.03,
                0.20,
                0.21,
            ]
        ),
        thrust_N=np.array(
            [
                0.0,
                10.0,
                25.0,
                20.0,
                10.0,
                0.0,
            ]
        ),
    )

    report = DataValidator.validate(
        test_data
    )

    print_report(
        "Synthetic sampling-gap dataset",
        report,
    )

    assert report.valid
    assert report.has_warnings

    assert any(
        issue.code == "SAMPLING_GAPS"
        for issue in report.warnings
    )


def main():
    print(
        "RMCS Analyzer Data Validation Tests"
    )

    print(
        "=" * 70
    )

    # ---------------------------------------------------------
    # Real RMCS CSV files
    # ---------------------------------------------------------

    validate_real_csv(
        "TEST_008.CSV"
    )

    validate_real_csv(
        "TEST_010_SAMPLE_MOTOR.csv"
    )

    # ---------------------------------------------------------
    # Synthetic validation tests
    # ---------------------------------------------------------

    test_valid_data()
    test_duplicate_timestamps()
    test_non_monotonic_time()
    test_missing_values()
    test_infinite_values()
    test_array_length_mismatch()
    test_optional_channel_length_mismatch()
    test_sampling_gap()

    print()
    print("=" * 70)
    print("ALL DATA VALIDATION TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()