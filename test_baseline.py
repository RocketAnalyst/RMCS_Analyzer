import numpy as np

from src.rmcs_analyzer.data.models import TestData
from src.rmcs_analyzer.processing.baseline import (
    BaselineCorrector,
    BaselineSettings,
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


def test_full_dataset_baseline():
    print_header("Full dataset baseline")

    data = build_test_data()

    result = BaselineCorrector.correct(data)

    expected_baseline = np.mean(data.thrust_N)

    assert np.isclose(
        result.baseline_N,
        expected_baseline,
    )

    expected = data.thrust_N - expected_baseline

    np.testing.assert_allclose(
        result.data.thrust_N,
        expected,
    )

    assert result.sample_count == 10

    print(
        f"Calculated baseline:  {result.baseline_N:.3f} N"
    )

    print(
        "Corrected thrust:     ",
        result.data.thrust_N,
    )


def test_selected_baseline_window():
    print_header("Selected baseline window")

    data = build_test_data()

    settings = BaselineSettings(
        baseline_start_time_s=0.0,
        baseline_end_time_s=3.0,
    )

    result = BaselineCorrector.correct(
        data,
        settings,
    )

    # Samples 0 through 3 are:
    # 5, 6, 5, 5
    # Mean = 5.25
    expected_baseline = 5.25

    assert np.isclose(
        result.baseline_N,
        expected_baseline,
    )

    assert result.baseline_start_index == 0
    assert result.baseline_end_index == 3

    expected = data.thrust_N - expected_baseline

    np.testing.assert_allclose(
        result.data.thrust_N,
        expected,
    )

    print(
        f"Baseline window:      0.000 → 3.000 s"
    )

    print(
        f"Calculated baseline:  {result.baseline_N:.3f} N"
    )


def test_non_exact_baseline_window():
    print_header("Non-exact baseline window")

    data = build_test_data()

    settings = BaselineSettings(
        baseline_start_time_s=1.2,
        baseline_end_time_s=3.8,
    )

    result = BaselineCorrector.correct(
        data,
        settings,
    )

    # Actual selected samples:
    # times 2 and 3
    # thrust 5 and 5
    expected_baseline = 5.0

    assert result.baseline_start_index == 2
    assert result.baseline_end_index == 3

    assert np.isclose(
        result.baseline_N,
        expected_baseline,
    )

    print(
        "Requested window:    1.2 → 3.8 s"
    )

    print(
        "Actual samples:       2 → 3"
    )

    print(
        f"Calculated baseline:  {result.baseline_N:.3f} N"
    )


def test_optional_channels_preserved():
    print_header("Optional channels preserved")

    data = build_test_data()

    result = BaselineCorrector.correct(data)

    np.testing.assert_array_equal(
        result.data.raw_hx711,
        data.raw_hx711,
    )

    np.testing.assert_array_equal(
        result.data.delta,
        data.delta,
    )

    np.testing.assert_array_equal(
        result.data.state,
        data.state,
    )

    np.testing.assert_array_equal(
        result.data.pressure_kPa,
        data.pressure_kPa,
    )

    print("HX711 channel:         PRESERVED")
    print("Delta channel:         PRESERVED")
    print("State channel:         PRESERVED")
    print("Pressure channel:      PRESERVED")


def test_raw_data_unchanged():
    print_header("Raw data protection")

    data = build_test_data()

    original_thrust = data.thrust_N.copy()
    original_time = data.time_s.copy()

    result = BaselineCorrector.correct(data)

    # Modify prepared data.
    result.data.thrust_N[:] = -999

    # Raw data must remain unchanged.
    np.testing.assert_array_equal(
        data.thrust_N,
        original_thrust,
    )

    np.testing.assert_array_equal(
        data.time_s,
        original_time,
    )

    print("Corrected data modified: YES")
    print("Raw thrust changed:      NO")
    print("Raw data protection:     PASSED")


def test_reset_settings():
    print_header("Settings reset")

    settings = BaselineSettings(
        baseline_start_time_s=1.0,
        baseline_end_time_s=3.0,
    )

    settings.reset()

    assert settings.baseline_start_time_s is None
    assert settings.baseline_end_time_s is None

    print("Baseline start:       RESET")
    print("Baseline end:         RESET")


def test_invalid_time_order():
    print_header("Invalid baseline range")

    data = build_test_data()

    settings = BaselineSettings(
        baseline_start_time_s=7.0,
        baseline_end_time_s=3.0,
    )

    try:
        BaselineCorrector.correct(
            data,
            settings,
        )
    except ValueError as exc:
        print("Invalid range detected: YES")
        print("Correction rejected:    YES")
        print()
        print(str(exc))
        return

    raise AssertionError(
        "Invalid baseline range should have been rejected."
    )


def test_non_finite_boundary():
    print_header("Non-finite baseline boundary")

    data = build_test_data()

    settings = BaselineSettings(
        baseline_start_time_s=np.nan,
    )

    try:
        BaselineCorrector.correct(
            data,
            settings,
        )
    except ValueError as exc:
        print("Invalid boundary detected: YES")
        print("Correction rejected:     YES")
        print()
        print(str(exc))
        return

    raise AssertionError(
        "Non-finite baseline boundary should have been rejected."
    )


def main():
    print("RMCS Analyzer Baseline Correction Tests")
    print("=" * 70)

    test_full_dataset_baseline()
    test_selected_baseline_window()
    test_non_exact_baseline_window()
    test_optional_channels_preserved()
    test_raw_data_unchanged()
    test_reset_settings()
    test_invalid_time_order()
    test_non_finite_boundary()

    print()
    print("=" * 70)
    print("ALL BASELINE CORRECTION TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()