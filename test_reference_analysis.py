import numpy as np

from src.rmcs_analyzer.analysis.performance import PerformanceReducer
from src.rmcs_analyzer.data.csv_reader import RMCSCSVReader


# ============================================================================
# Zerox Reference Analysis
#
# Purpose:
#   Document and regression-test the current Zerox reduction using the
#   authoritative PerformanceReducer.
#
# Source clarification:
#   Source clarification established that the "N2300" label in the source
#   video was an informal visual estimate and was not calculated from the
#   measured firing. Therefore this test does not attempt to reverse-engineer
#   or validate that label.
# ============================================================================


def integrate_positive(time_s, thrust_N):
    """Integrate positive finite thrust over the complete valid curve."""
    time_s = np.asarray(time_s, dtype=float)
    thrust_N = np.asarray(thrust_N, dtype=float)

    mask = np.isfinite(time_s) & np.isfinite(thrust_N)

    time_s = time_s[mask]
    thrust_N = thrust_N[mask]

    if len(time_s) < 2:
        return 0.0

    order = np.argsort(time_s)
    time_s = time_s[order]
    thrust_N = thrust_N[order]

    keep = np.concatenate(([True], np.diff(time_s) > 0))
    time_s = time_s[keep]
    thrust_N = thrust_N[keep]

    return float(np.trapezoid(np.maximum(thrust_N, 0.0), time_s))


def _script_regression():
    print("RMCS Analyzer Zerox Reference Analysis")
    print("=" * 78)

    reader = RMCSCSVReader()
    data = reader.read("test_data/Zerox.csv")

    reducer = PerformanceReducer()
    result = reducer.reduce(data)

    time_s = data.time_s
    thrust_N = data.thrust_N

    curve_start = float(time_s[0])
    curve_end = float(time_s[-1])
    curve_duration = curve_end - curve_start

    print()
    print("RAW ZER0X CURVE")
    print("-" * 78)
    print(f"Curve start:             {curve_start:.6f} s")
    print(f"Curve end:               {curve_end:.6f} s")
    print(f"Curve duration:          {curve_duration:.6f} s")
    print(f"Peak thrust:             {np.max(thrust_N):.6f} N")
    print(f"Peak time:               {time_s[np.argmax(thrust_N)]:.6f} s")

    print()
    print("STANDARDIZED 5% REDUCTION")
    print("-" * 78)
    print(f"5% threshold:            {result.threshold_thrust_N:.6f} N")
    print(f"5% start:                {result.burn_start_5pct_time_s:.6f} s")
    print(f"5% end:                  {result.burn_end_5pct_time_s:.6f} s")
    print(f"5% burn time:            {result.burn_time_5pct_s:.6f} s")
    print(f"Normalized impulse:      {result.normalized_impulse_Ns:.6f} Ns")
    print(f"Average thrust:          {result.average_thrust_N:.6f} N")
    print(f"Initial thrust average:  {result.initial_thrust_average_N:.6f} N")
    print(f"Class from total impulse:{result.impulse_class}")
    print(f"Designation:             {result.designation}")

    full_impulse = integrate_positive(time_s, thrust_N)

    print()
    print("FULL POSITIVE CURVE")
    print("-" * 78)
    print(f"Positive-curve impulse:  {full_impulse:.6f} Ns")
    print(
        "Note: this is the complete finite positive curve in Zerox.csv; "
        "it is not the standardized average-thrust interval."
    )

    # Regression facts.
    assert len(time_s) == 661
    assert np.isclose(curve_duration, 8.538, atol=1e-9)
    assert np.isclose(np.max(thrust_N), 3230.339730, atol=1e-6)

    assert np.isclose(
        result.total_impulse_Ns,
        full_impulse,
        atol=1e-6,
    )

    assert np.isclose(
        result.average_thrust_N * result.burn_time_5pct_s,
        result.normalized_impulse_Ns,
        atol=1e-6,
    )

    print()
    print("VALIDATION CHECKS")
    print("-" * 78)
    print("Zerox sample count:                  PASSED")
    print("Zerox duration:                      PASSED")
    print("Zerox peak thrust:                   PASSED")
    print("Current total impulse consistency:   PASSED")
    print("Current 5% average consistency:      PASSED")
    print("N2300 reverse-engineering:            NOT USED")

    print()
    print("=" * 78)
    print("ALL ZER0X REFERENCE ANALYSIS TESTS PASSED")
    print("=" * 78)



def test_script_regression():
    _script_regression()


if __name__ == "__main__":
    _script_regression()
