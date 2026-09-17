import numpy as np

from src.rmcs_analyzer.data.models import TestData
from src.rmcs_analyzer.processing.baseline import (
    BaselineSettings,
)
from src.rmcs_analyzer.processing.cleaning import (
    CleaningSettings,
)
from src.rmcs_analyzer.processing.pipeline import (
    ProcessingPipeline,
)
from src.rmcs_analyzer.processing.settings import (
    ProcessingSettings,
)


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def build_test_data():
    time = np.arange(10, dtype=float)

    thrust = np.array(
        [5, 6, 5, 5, 15, 25, 20, 10, 5, 5],
        dtype=float,
    )

    raw_hx711 = np.arange(100, 110, dtype=float)
    delta = np.arange(10, 20, dtype=float)
    state = np.arange(10, dtype=float)
    pressure = np.arange(101, 111, dtype=float)

    return TestData(
        time_s=time,
        thrust_N=thrust,
        raw_hx711=raw_hx711,
        delta=delta,
        state=state,
        pressure_kPa=pressure,
    )


def test_no_processing():
    print_header("No processing")

    data = build_test_data()

    settings = ProcessingSettings(
        baseline=BaselineSettings(
            baseline_start_time_s=0.0,
            baseline_end_time_s=0.0,
        ),
    )

    pipeline = ProcessingPipeline()

    result = pipeline.process(
        data,
        settings,
    )

    assert result.valid
    assert result.modified

    assert result.baseline_result is not None

    assert np.isclose(
        result.baseline_result.baseline_N,
        5.0,
    )

    assert result.prepared_data.sample_count == 10

    expected = data.thrust_N - 5.0

    np.testing.assert_allclose(
        result.prepared_data.thrust_N,
        expected,
    )

    print("Raw validation:       VALID")
    print("Prepared validation:  VALID")
    print("Baseline:             5.000 N")
    print("Modified:             YES")
    print("Samples:              10")


def test_trim_and_baseline():
    print_header("Trim + baseline processing")

    data = build_test_data()

    settings = ProcessingSettings(
        cleaning=CleaningSettings(
            start_time_s=3.0,
            end_time_s=7.0,
        ),
        baseline=BaselineSettings(
            baseline_start_time_s=3.0,
            baseline_end_time_s=4.0,
        ),
    )

    pipeline = ProcessingPipeline()

    result = pipeline.process(
        data,
        settings,
    )

    assert result.valid
    assert result.modified

    assert result.cleaning_result is not None
    assert result.baseline_result is not None

    assert result.prepared_data.sample_count == 5

    # After trimming 3.0 -> 7.0:
    #
    # Time:    3   4   5   6   7
    # Thrust:  5  15  25  20  10
    #
    # Baseline window uses times 3 and 4:
    #
    # 5, 15
    #
    # Baseline = 10.0 N
    expected_baseline = 10.0

    assert np.isclose(
        result.baseline_result.baseline_N,
        expected_baseline,
    )

    expected = np.array(
        [-5, 5, 15, 10, 0],
        dtype=float,
    )

    np.testing.assert_allclose(
        result.prepared_data.thrust_N,
        expected,
    )

    print("Raw validation:       VALID")
    print("Trimmed samples:      5")
    print("Baseline:             10.000 N")
    print("Prepared validation:  VALID")
    print("Processing:            PASSED")


def test_baseline_only_preserves_sample_count():
    print_header("Baseline-only processing")

    data = build_test_data()

    settings = ProcessingSettings(
        baseline=BaselineSettings(
            baseline_start_time_s=0.0,
            baseline_end_time_s=3.0,
        ),
    )

    pipeline = ProcessingPipeline()

    result = pipeline.process(
        data,
        settings,
    )

    assert result.prepared_data.sample_count == 10
    assert result.baseline_result is not None

    print("Original samples:     10")
    print("Prepared samples:     10")
    print(
        f"Baseline:             "
        f"{result.baseline_result.baseline_N:.3f} N"
    )
    print("Sample count changed: NO")


def test_default_processing_settings():
    print_header("Default ProcessingSettings")

    data = build_test_data()

    pipeline = ProcessingPipeline()

    result = pipeline.process(data)

    assert result.valid
    assert result.prepared_data.sample_count == 10

    # With no explicit baseline window, the current baseline
    # implementation uses the entire dataset.
    assert result.baseline_result is not None

    expected_baseline = np.mean(data.thrust_N)

    assert np.isclose(
        result.baseline_result.baseline_N,
        expected_baseline,
    )

    print("Settings omitted:     YES")
    print("Defaults applied:     YES")
    print(
        f"Baseline:             "
        f"{result.baseline_result.baseline_N:.3f} N"
    )
    print("Default processing:   PASSED")


def test_raw_data_is_unchanged():
    print_header("Raw data protection")

    data = build_test_data()

    original_time = data.time_s.copy()
    original_thrust = data.thrust_N.copy()
    original_hx711 = data.raw_hx711.copy()

    settings = ProcessingSettings(
        cleaning=CleaningSettings(
            start_time_s=3.0,
            end_time_s=7.0,
        ),
        baseline=BaselineSettings(
            baseline_start_time_s=3.0,
            baseline_end_time_s=4.0,
        ),
    )

    pipeline = ProcessingPipeline()

    result = pipeline.process(
        data,
        settings,
    )

    result.prepared_data.time_s[:] = -999
    result.prepared_data.thrust_N[:] = -999
    result.prepared_data.raw_hx711[:] = -999

    np.testing.assert_array_equal(
        data.time_s,
        original_time,
    )

    np.testing.assert_array_equal(
        data.thrust_N,
        original_thrust,
    )

    np.testing.assert_array_equal(
        data.raw_hx711,
        original_hx711,
    )

    print("Prepared data modified: YES")
    print("Raw data changed:       NO")
    print("Raw data protection:    PASSED")


def test_invalid_raw_data():
    print_header("Invalid raw data")

    data = build_test_data()

    data.time_s[5] = np.nan

    pipeline = ProcessingPipeline()

    try:
        pipeline.process(data)
    except ValueError as exc:
        print("Invalid data detected: YES")
        print("Pipeline rejected data: YES")
        print()
        print(str(exc))
        return

    raise AssertionError(
        "Pipeline should have rejected invalid raw data."
    )


def test_prepared_data_validation():
    print_header("Prepared data validation")

    data = build_test_data()

    settings = ProcessingSettings(
        cleaning=CleaningSettings(
            start_time_s=3.0,
            end_time_s=7.0,
        ),
        baseline=BaselineSettings(
            baseline_start_time_s=3.0,
            baseline_end_time_s=4.0,
        ),
    )

    pipeline = ProcessingPipeline()

    result = pipeline.process(
        data,
        settings,
    )

    assert result.prepared_validation.valid

    print(
        "Prepared samples:",
        result.prepared_data.sample_count,
    )

    print(
        "Prepared rate:   "
        f"{result.prepared_validation.sample_rate_hz:.3f} Hz"
    )

    print("Prepared data:   VALID")


def main():
    print("RMCS Analyzer Processing Pipeline Tests")
    print("=" * 70)

    test_no_processing()
    test_trim_and_baseline()
    test_baseline_only_preserves_sample_count()
    test_default_processing_settings()
    test_raw_data_is_unchanged()
    test_invalid_raw_data()
    test_prepared_data_validation()

    print()
    print("=" * 70)
    print("ALL PROCESSING PIPELINE TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()