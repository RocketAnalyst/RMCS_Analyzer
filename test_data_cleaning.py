from pathlib import Path

import numpy as np

from src.rmcs_analyzer.data import RMCSCSVReader
from src.rmcs_analyzer.data.models import TestData
from src.rmcs_analyzer.processing.cleaning import (
    CleaningSettings,
    DataCleaner,
)


PROJECT_ROOT = Path(__file__).resolve().parent
TEST_DATA_FOLDER = PROJECT_ROOT / "test_data"


# =============================================================
# TEST HELPERS
# =============================================================


def build_test_data():
    """
    Create a small predictable dataset for cleaning tests.
    """

    time_s = np.arange(
        0.0,
        10.0,
        1.0,
    )

    thrust_N = np.array(
        [
            0.0,
            1.0,
            2.0,
            10.0,
            20.0,
            30.0,
            20.0,
            10.0,
            2.0,
            0.0,
        ]
    )

    raw_hx711 = np.arange(
        100,
        110,
    )

    delta = np.arange(
        10,
        20,
    )

    state = np.arange(
        0,
        10,
    )

    pressure_kPa = np.arange(
        101,
        111,
    )

    return TestData(
        time_s=time_s,
        thrust_N=thrust_N,
        raw_hx711=raw_hx711,
        delta=delta,
        state=state,
        pressure_kPa=pressure_kPa,
    )


def print_result(
    name,
    result,
):
    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    print(
        f"Start index:             {result.start_index}"
    )

    print(
        f"End index:               {result.end_index}"
    )

    print(
        f"Original samples:        "
        f"{result.original_sample_count}"
    )

    print(
        f"Prepared samples:        "
        f"{result.prepared_sample_count}"
    )

    print(
        f"Prepared start time:     "
        f"{result.data.time_s[0]:.3f} s"
    )

    print(
        f"Prepared end time:       "
        f"{result.data.time_s[-1]:.3f} s"
    )

    print(
        f"Prepared thrust:         "
        f"{result.data.thrust_N}"
    )


# =============================================================
# NO-TRIM TEST
# =============================================================


def test_no_trim():
    """
    No boundaries should return the complete dataset.
    """

    original = build_test_data()

    settings = CleaningSettings()

    result = DataCleaner.prepare(
        original,
        settings,
    )

    print_result(
        "No trimming",
        result,
    )

    assert result.start_index == 0

    assert (
        result.end_index
        == original.sample_count - 1
    )

    assert (
        result.original_sample_count
        == 10
    )

    assert (
        result.prepared_sample_count
        == 10
    )

    assert np.array_equal(
        result.data.time_s,
        original.time_s,
    )

    assert np.array_equal(
        result.data.thrust_N,
        original.thrust_N,
    )


# =============================================================
# START-ONLY TEST
# =============================================================


def test_start_trim():
    """
    A start boundary should remove samples before it.
    """

    original = build_test_data()

    settings = CleaningSettings(
        start_time_s=3.0,
    )

    result = DataCleaner.prepare(
        original,
        settings,
    )

    print_result(
        "Start-only trimming",
        result,
    )

    assert result.start_index == 3

    assert result.end_index == 9

    assert result.prepared_sample_count == 7

    assert (
        result.data.time_s[0]
        == 3.0
    )

    assert (
        result.data.thrust_N[0]
        == 10.0
    )


# =============================================================
# END-ONLY TEST
# =============================================================


def test_end_trim():
    """
    An end boundary should remove samples after it.
    """

    original = build_test_data()

    settings = CleaningSettings(
        end_time_s=6.0,
    )

    result = DataCleaner.prepare(
        original,
        settings,
    )

    print_result(
        "End-only trimming",
        result,
    )

    assert result.start_index == 0

    assert result.end_index == 6

    assert result.prepared_sample_count == 7

    assert (
        result.data.time_s[-1]
        == 6.0
    )

    assert (
        result.data.thrust_N[-1]
        == 20.0
    )


# =============================================================
# START + END TEST
# =============================================================


def test_start_and_end_trim():
    """
    Start and end boundaries should select the requested region.
    """

    original = build_test_data()

    settings = CleaningSettings(
        start_time_s=3.0,
        end_time_s=7.0,
    )

    result = DataCleaner.prepare(
        original,
        settings,
    )

    print_result(
        "Start + end trimming",
        result,
    )

    assert result.start_index == 3

    assert result.end_index == 7

    assert result.prepared_sample_count == 5

    assert np.array_equal(
        result.data.time_s,
        np.array(
            [
                3.0,
                4.0,
                5.0,
                6.0,
                7.0,
            ]
        ),
    )

    assert np.array_equal(
        result.data.thrust_N,
        np.array(
            [
                10.0,
                20.0,
                30.0,
                20.0,
                10.0,
            ]
        ),
    )


# =============================================================
# NON-EXACT TIME TEST
# =============================================================


def test_non_exact_boundaries():
    """
    Non-exact time boundaries should select the nearest valid
    samples according to the documented rules.
    """

    original = build_test_data()

    settings = CleaningSettings(
        start_time_s=3.4,
        end_time_s=6.6,
    )

    result = DataCleaner.prepare(
        original,
        settings,
    )

    print_result(
        "Non-exact time boundaries",
        result,
    )

    # Start uses the first sample at or after 3.4.
    assert result.start_index == 4

    # End uses the last sample at or before 6.6.
    assert result.end_index == 6

    assert np.array_equal(
        result.data.time_s,
        np.array(
            [
                4.0,
                5.0,
                6.0,
            ]
        ),
    )


# =============================================================
# OPTIONAL CHANNEL TEST
# =============================================================


def test_optional_channels_remain_aligned():
    """
    All existing optional channels must receive the same slice.
    """

    original = build_test_data()

    settings = CleaningSettings(
        start_time_s=3.0,
        end_time_s=7.0,
    )

    result = DataCleaner.prepare(
        original,
        settings,
    )

    assert np.array_equal(
        result.data.raw_hx711,
        np.array(
            [
                103,
                104,
                105,
                106,
                107,
            ]
        ),
    )

    assert np.array_equal(
        result.data.delta,
        np.array(
            [
                13,
                14,
                15,
                16,
                17,
            ]
        ),
    )

    assert np.array_equal(
        result.data.state,
        np.array(
            [
                3,
                4,
                5,
                6,
                7,
            ]
        ),
    )

    assert np.array_equal(
        result.data.pressure_kPa,
        np.array(
            [
                104,
                105,
                106,
                107,
                108,
            ]
        ),
    )


# =============================================================
# RAW DATA PRESERVATION TEST
# =============================================================


def test_original_data_is_unchanged():
    """
    The most important test:

    Cleaning must never modify the original dataset.
    """

    original = build_test_data()

    original_time = original.time_s.copy()
    original_thrust = original.thrust_N.copy()
    original_raw = original.raw_hx711.copy()
    original_delta = original.delta.copy()
    original_state = original.state.copy()
    original_pressure = (
        original.pressure_kPa.copy()
    )

    settings = CleaningSettings(
        start_time_s=3.0,
        end_time_s=7.0,
    )

    result = DataCleaner.prepare(
        original,
        settings,
    )

    # ---------------------------------------------------------
    # Verify original arrays are unchanged
    # ---------------------------------------------------------

    assert np.array_equal(
        original.time_s,
        original_time,
    )

    assert np.array_equal(
        original.thrust_N,
        original_thrust,
    )

    assert np.array_equal(
        original.raw_hx711,
        original_raw,
    )

    assert np.array_equal(
        original.delta,
        original_delta,
    )

    assert np.array_equal(
        original.state,
        original_state,
    )

    assert np.array_equal(
        original.pressure_kPa,
        original_pressure,
    )

    # ---------------------------------------------------------
    # Verify prepared arrays are independent copies
    # ---------------------------------------------------------

    result.data.time_s[0] = 999.0

    result.data.thrust_N[0] = 999.0

    assert (
        original.time_s[3]
        == 3.0
    )

    assert (
        original.thrust_N[3]
        == 10.0
    )


# =============================================================
# RESET SETTINGS TEST
# =============================================================


def test_reset_settings():
    """
    Reset should remove both cleaning boundaries.
    """

    settings = CleaningSettings(
        start_time_s=3.0,
        end_time_s=7.0,
    )

    settings.reset()

    assert settings.start_time_s is None

    assert settings.end_time_s is None


# =============================================================
# INVALID BOUNDARY TEST
# =============================================================


def test_invalid_boundary_order():
    """
    End before start should raise an error.
    """

    original = build_test_data()

    settings = CleaningSettings(
        start_time_s=7.0,
        end_time_s=3.0,
    )

    try:

        DataCleaner.prepare(
            original,
            settings,
        )

    except ValueError as error:

        assert (
            "start time must occur before"
            in str(error)
        )

    else:

        raise AssertionError(
            "Expected ValueError for invalid "
            "cleaning boundary order."
        )


def test_non_finite_boundary():
    """
    Infinite or NaN boundaries should raise an error.
    """

    original = build_test_data()

    invalid_settings = [
        CleaningSettings(
            start_time_s=np.nan,
        ),
        CleaningSettings(
            start_time_s=np.inf,
        ),
        CleaningSettings(
            end_time_s=np.nan,
        ),
        CleaningSettings(
            end_time_s=-np.inf,
        ),
    ]

    for settings in invalid_settings:

        try:

            DataCleaner.prepare(
                original,
                settings,
            )

        except ValueError:

            pass

        else:

            raise AssertionError(
                "Expected ValueError for non-finite "
                "cleaning boundary."
            )


# =============================================================
# REAL RMCS DATA TEST
# =============================================================


def test_real_rmcs_data():
    """
    Confirm the cleaner works with an actual RMCS CSV.
    """

    path = (
        TEST_DATA_FOLDER
        / "TEST_010_SAMPLE_MOTOR.csv"
    )

    if not path.exists():

        print(
            f"\nWARNING: Test file not found: {path}"
        )

        return

    reader = RMCSCSVReader()

    original = reader.read(
        str(path)
    )

    original_count = (
        original.sample_count
    )

    original_time = (
        original.time_s.copy()
    )

    original_thrust = (
        original.thrust_N.copy()
    )

    # Select an interior region.
    start_time = float(
        original.time_s[50]
    )

    end_time = float(
        original.time_s[-51]
    )

    settings = CleaningSettings(
        start_time_s=start_time,
        end_time_s=end_time,
    )

    result = DataCleaner.prepare(
        original,
        settings,
    )

    print_result(
        "Real TEST_010_SAMPLE_MOTOR.csv",
        result,
    )

    assert (
        result.original_sample_count
        == original_count
    )

    assert (
        result.prepared_sample_count
        < result.original_sample_count
    )

    assert (
        result.data.time_s[0]
        >= start_time
    )

    assert (
        result.data.time_s[-1]
        <= end_time
    )

    # ---------------------------------------------------------
    # Original data must remain unchanged.
    # ---------------------------------------------------------

    assert np.array_equal(
        original.time_s,
        original_time,
    )

    assert np.array_equal(
        original.thrust_N,
        original_thrust,
    )


# =============================================================
# MAIN
# =============================================================


def main():
    print(
        "RMCS Analyzer Data Cleaning Tests"
    )

    print(
        "=" * 70
    )

    test_no_trim()

    test_start_trim()

    test_end_trim()

    test_start_and_end_trim()

    test_non_exact_boundaries()

    test_optional_channels_remain_aligned()

    test_original_data_is_unchanged()

    test_reset_settings()

    test_invalid_boundary_order()

    test_non_finite_boundary()

    test_real_rmcs_data()

    print()
    print("=" * 70)
    print("ALL DATA CLEANING TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()