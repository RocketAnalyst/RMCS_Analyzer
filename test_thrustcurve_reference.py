import numpy as np

from src.rmcs_analyzer.analysis.performance import PerformanceReducer
from src.rmcs_analyzer.data.models import TestData


# ============================================================================
# Independent ThrustCurve/NFPA reference validation
#
# Reference:
#   ThrustCurve.org AeroTech G73C certification RASP data
#
# Published reference values on the ThrustCurve page:
#   Total impulse:      128.64 Ns
#   Max thrust:          96.00 N
#   5% threshold:         4.80 N
#   5% start:             0.003 s
#   5% end:               1.818 s
#   NFPA burn time:       1.814 s
#   NFPA average thrust:  70.90 N
#
# The raw RASP points are reproduced below exactly as published. Because
# published points are rounded, small numerical differences are expected
# compared with the underlying certification curve.
#
# This test is important because it is independent of the Zerox/BPS data.
# ============================================================================


TIME_S = np.array([
    0.003, 0.006, 0.019, 0.023, 0.058, 0.094, 0.129, 0.210,
    0.632, 0.742, 0.916, 0.945, 0.974, 1.245, 1.432, 1.474,
    1.523, 1.558, 1.574, 1.639, 1.661, 1.713, 1.748, 1.771,
    1.806, 1.842, 1.858, 2.000,
], dtype=float)

THRUST_N = np.array([
    0.421, 36.212, 29.053, 96.003, 82.950, 81.687, 80.845, 82.530,
    93.056, 92.214, 93.898, 93.477, 91.371, 66.108, 50.949, 47.160,
    46.317, 47.160, 44.212, 20.211, 16.843, 13.474, 12.211, 10.526,
    5.894, 2.526, 0.842, 0.000,
], dtype=float)


def _script_regression():
    print("RMCS Analyzer Independent ThrustCurve Reference Validation")
    print("=" * 78)

    data = TestData(
        time_s=TIME_S.copy(),
        thrust_N=THRUST_N.copy(),
    )

    reducer = PerformanceReducer()
    result = reducer.reduce(data)

    print()
    print("THRUSTCURVE / G73C REFERENCE")
    print("-" * 78)
    print("Published total impulse:       128.64 Ns")
    print("Published maximum thrust:       96.00 N")
    print("Published 5% threshold:         4.80 N")
    print("Published 5% start:              0.003 s")
    print("Published 5% end:                1.818 s")
    print("Published NFPA burn time:        1.814 s")
    print("Published NFPA average thrust:  70.90 N")

    print()
    print("RMCS ANALYZER")
    print("-" * 78)
    print(f"Total impulse:                  {result.total_impulse_Ns:.6f} Ns")
    print(f"Peak thrust:                    {result.peak_thrust_N:.6f} N")
    print(f"5% threshold:                   {result.threshold_thrust_N:.6f} N")
    print(f"5% start:                       {result.burn_start_5pct_time_s:.6f} s")
    print(f"5% end:                         {result.burn_end_5pct_time_s:.6f} s")
    print(f"5% burn time:                   {result.burn_time_5pct_s:.6f} s")
    print(f"Normalized impulse:             {result.normalized_impulse_Ns:.6f} Ns")
    print(f"Average thrust:                 {result.average_thrust_N:.6f} N")

    # ------------------------------------------------------------------
    # Published values are rounded. Use tolerances appropriate to the
    # published precision rather than falsely requiring exact equality.
    # ------------------------------------------------------------------

    assert np.isclose(
        result.total_impulse_Ns,
        128.64,
        rtol=0.001,
    ), "Total impulse differs from published reference by >0.1%"

    assert np.isclose(
        result.peak_thrust_N,
        96.00,
        atol=0.01,
    ), "Peak thrust differs from published reference"

    assert np.isclose(
        result.threshold_thrust_N,
        4.80,
        atol=0.01,
    ), "5% threshold differs from published reference"

    assert np.isclose(
        result.burn_start_5pct_time_s,
        0.003,
        atol=0.001,
    ), "5% start differs from published reference"

    assert np.isclose(
        result.burn_end_5pct_time_s,
        1.818,
        atol=0.001,
    ), "5% end differs from published reference"

    assert np.isclose(
        result.burn_time_5pct_s,
        1.814,
        atol=0.002,
    ), "NFPA burn time differs from published reference"

    assert np.isclose(
        result.average_thrust_N,
        70.90,
        rtol=0.003,
    ), "Average thrust differs from published reference by >0.3%"

    print()
    print("VALIDATION")
    print("-" * 78)
    print("Total impulse:        PASSED")
    print("Peak thrust:          PASSED")
    print("5% threshold:         PASSED")
    print("5% start:             PASSED")
    print("5% end:               PASSED")
    print("NFPA burn time:       PASSED")
    print("NFPA average thrust:  PASSED")

    print()
    print(
        "RESULT: The current 5% performance-reduction method agrees with "
        "the independently published ThrustCurve G73C reference within "
        "the precision of its published/rounded data."
    )
    print()
    print("=" * 78)
    print("ALL THRUSTCURVE REFERENCE TESTS PASSED")
    print("=" * 78)



def test_script_regression():
    _script_regression()


if __name__ == "__main__":
    _script_regression()
