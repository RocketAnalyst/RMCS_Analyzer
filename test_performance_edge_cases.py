import numpy as np

from src.rmcs_analyzer.analysis.performance import PerformanceReducer
from src.rmcs_analyzer.data.models import TestData


# ============================================================================
# PerformanceReducer Edge-Case / Mathematical Validation
#
# Purpose:
#   Exercise the authoritative performance-reduction rules with deliberately
#   constructed curves. These tests are independent of any particular motor.
#
# Rules being protected:
#   - Peak thrust is the maximum positive finite thrust.
#   - 5% threshold = 5% of peak.
#   - 5% crossings are linearly interpolated between samples.
#   - Average thrust uses the normalized 5%-to-5% interval.
#   - Total impulse uses the complete finite thrust curve.
#   - Negative thrust is excluded from impulse.
#   - Non-finite samples are ignored.
#   - Irregular sample spacing must be handled using actual timestamps.
#   - Duplicate timestamps must not break reduction.
# ============================================================================


def make_data(time_s, thrust_N):
    return TestData(
        time_s=np.asarray(time_s, dtype=float),
        thrust_N=np.asarray(thrust_N, dtype=float),
    )


def assert_close(actual, expected, atol=1e-9, rtol=1e-9, label="value"):
    assert np.isclose(
        actual,
        expected,
        atol=atol,
        rtol=rtol,
    ), f"{label}: expected {expected}, got {actual}"


def test_linear_crossings():
    """
    Construct a simple triangular curve whose 5% crossings fall exactly
    between samples.

    Curve:
        t = 0, 1, 2, 3, 4
        F = 0, 100, 200, 100, 0

    Peak = 200 N
    Threshold = 10 N

    Rising 5% crossing:
        0 -> 100 N over 1 s
        10 N occurs at t = 0.1 s

    Falling 5% crossing:
        100 -> 0 N over 1 s
        10 N occurs at t = 3.9 s

    Burn = 3.8 s
    """
    data = make_data(
        [0, 1, 2, 3, 4],
        [0, 100, 200, 100, 0],
    )

    result = PerformanceReducer().reduce(data)

    assert_close(result.peak_thrust_N, 200.0, label="peak")
    assert_close(result.threshold_thrust_N, 10.0, label="threshold")
    assert_close(
        result.burn_start_5pct_time_s,
        0.1,
        label="rising crossing",
    )
    assert_close(
        result.burn_end_5pct_time_s,
        3.9,
        label="falling crossing",
    )
    assert_close(
        result.burn_time_5pct_s,
        3.8,
        label="burn time",
    )

    expected_impulse = 399.0

    assert_close(
        result.normalized_impulse_Ns,
        expected_impulse,
        label="normalized impulse",
    )
    assert_close(
        result.average_thrust_N,
        expected_impulse / 3.8,
        label="average thrust",
    )

    print("Linear interpolation crossings: PASSED")


def test_irregular_timestamps():
    """
    Same general physical shape, sampled at irregular intervals.

    The result must be based on timestamps, not sample count or an assumed
    fixed sample rate.
    """
    data = make_data(
        [0.0, 0.25, 1.4, 2.7, 3.25, 4.0],
        [0.0, 25.0, 140.0, 130.0, 75.0, 0.0],
    )

    result = PerformanceReducer().reduce(data)

    assert result.burn_time_5pct_s > 0.0
    assert result.normalized_impulse_Ns > 0.0
    assert result.average_thrust_N > 0.0
    assert result.burn_time_5pct_s < 4.0

    print("Irregular timestamps: PASSED")


def test_negative_thrust_excluded():
    """
    Negative values may occur from load-cell noise or post-test behavior.
    They must not subtract impulse from the motor's thrust integral.
    """
    positive = make_data(
        [0, 1, 2, 3],
        [0, 100, 100, 0],
    )

    negative = make_data(
        [0, 1, 2, 3, 4],
        [0, 100, 100, -500, 0],
    )

    positive_result = PerformanceReducer().reduce(positive)
    negative_result = PerformanceReducer().reduce(negative)

    assert_close(
        positive_result.total_impulse_Ns,
        200.0,
        label="positive total impulse",
    )

    assert_close(
        negative_result.total_impulse_Ns,
        200.0,
        label="negative exclusion",
    )

    print("Negative thrust exclusion: PASSED")


def test_nonfinite_samples():
    """
    NaN and infinity must not contaminate the reduction.
    """
    data = make_data(
        [0, 1, 2, 3, 4],
        [0, 100, np.nan, 100, 0],
    )

    result = PerformanceReducer().reduce(data)

    assert np.isfinite(result.total_impulse_Ns)
    assert np.isfinite(result.average_thrust_N)
    assert result.total_impulse_Ns > 0.0

    print("Non-finite sample handling: PASSED")


def test_duplicate_timestamps():
    """
    Duplicate timestamps are removed before integration. The first value
    at the duplicate timestamp is retained.

    Therefore this input:
        t = 0, 1, 1, 2, 3
        F = 0, 100, 500, 100, 0

    becomes:
        t = 0, 1, 2, 3
        F = 0, 100, 100, 0

    The 500 N duplicate is intentionally NOT used.
    """
    data = make_data(
        [0, 1, 1, 2, 3],
        [0, 100, 500, 100, 0],
    )

    result = PerformanceReducer().reduce(data)

    assert np.isfinite(result.total_impulse_Ns)
    assert np.isfinite(result.average_thrust_N)

    # This is the important assertion: it verifies the documented
    # first-occurrence duplicate-timestamp policy.
    assert_close(
        result.peak_thrust_N,
        100.0,
        label="duplicate timestamp peak",
    )

    print("Duplicate timestamps: PASSED")


def test_full_curve_impulse_vs_normalized_impulse():
    """
    A long low-thrust tail should contribute to total impulse while not
    extending the standardized 5% burn interval.
    """
    data = make_data(
        [0, 1, 2, 3, 4, 5],
        [0, 100, 100, 0, 1, 1],
    )

    result = PerformanceReducer().reduce(data)

    assert_close(
        result.burn_start_5pct_time_s,
        0.05,
        label="tail test start",
    )
    assert_close(
        result.burn_end_5pct_time_s,
        2.95,
        label="tail test end",
    )

    # Trapezoidal integration using the actual timestamps:
    # 0-1 s: 50 Ns
    # 1-2 s: 100 Ns
    # 2-3 s: 50 Ns
    # 3-4 s: 0.5 Ns
    # 4-5 s: 1 Ns
    # Total = 201.5 Ns
    #
    # The 1 N tail therefore contributes 1.5 Ns, while the falling
    # segment from 0 to 1 N contributes another 0.5 Ns.
    assert_close(
        result.total_impulse_Ns,
        201.5,
        label="full-curve impulse",
    )

    assert result.burn_end_5pct_time_s < 3.0

    print("Full curve vs normalized interval: PASSED")


def test_peak_uses_positive_thrust():
    """
    Negative values must never become the peak, and the reducer should not
    use absolute thrust.
    """
    data = make_data(
        [0, 1, 2, 3],
        [-500, -100, 50, 0],
    )

    result = PerformanceReducer().reduce(data)

    assert_close(
        result.peak_thrust_N,
        50.0,
        label="positive peak",
    )

    print("Positive-only peak selection: PASSED")


def test_exact_threshold_sample():
    """
    A sample exactly at 5% must be accepted as the boundary of the
    standardized interval.

    Curve:
        t = 0, 1, 2, 3, 4, 5
        F = 0, 5, 100, 100, 5, 0

    Peak = 100 N
    Threshold = 5 N

    The exact threshold samples occur at t=1 and t=4, so the standardized
    interval should begin and end at those samples without interpolation.
    """
    data = make_data(
        [0, 1, 2, 3, 4, 5],
        [0, 5, 100, 100, 5, 0],
    )

    result = PerformanceReducer().reduce(data)

    assert_close(
        result.threshold_thrust_N,
        5.0,
        label="exact threshold",
    )
    assert_close(
        result.burn_start_5pct_time_s,
        1.0,
        label="exact-threshold start",
    )
    assert_close(
        result.burn_end_5pct_time_s,
        4.0,
        label="exact-threshold end",
    )
    assert_close(
        result.burn_time_5pct_s,
        3.0,
        label="exact-threshold burn time",
    )

    print("Exact threshold samples: PASSED")


def test_unsorted_timestamps():
    """
    Input ordering should not change the result because reduction sorts by
    actual timestamp.
    """
    ordered = make_data(
        [0, 1, 2, 3],
        [0, 100, 100, 0],
    )

    shuffled = make_data(
        [2, 0, 3, 1],
        [100, 0, 0, 100],
    )

    expected = PerformanceReducer().reduce(ordered)
    actual = PerformanceReducer().reduce(shuffled)

    assert_close(
        actual.total_impulse_Ns,
        expected.total_impulse_Ns,
        label="sorted total impulse",
    )
    assert_close(
        actual.average_thrust_N,
        expected.average_thrust_N,
        label="sorted average",
    )

    print("Unsorted timestamps: PASSED")


def main():
    print("RMCS Analyzer Performance Edge-Case Validation")
    print("=" * 78)

    test_linear_crossings()
    test_irregular_timestamps()
    test_negative_thrust_excluded()
    test_nonfinite_samples()
    test_duplicate_timestamps()
    test_full_curve_impulse_vs_normalized_impulse()
    test_peak_uses_positive_thrust()
    test_exact_threshold_sample()
    test_unsorted_timestamps()

    print()
    print("=" * 78)
    print("ALL PERFORMANCE EDGE-CASE TESTS PASSED")
    print("=" * 78)


if __name__ == "__main__":
    main()
