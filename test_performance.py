import numpy as np

from src.rmcs_analyzer.analysis.performance import PerformanceReducer
from src.rmcs_analyzer.data.csv_reader import RMCSCSVReader
from src.rmcs_analyzer.data.models import TestData


def main():
    print("RMCS Analyzer Performance Reduction Tests")
    print("=" * 70)

    reader = RMCSCSVReader()
    test_data = reader.read(
        "test_data/Zerox.csv"
    )

    reducer = PerformanceReducer()
    result = reducer.reduce(test_data)

    print(f"Peak thrust:          {result.peak_thrust_N:.6f} N")
    print(f"Peak time:             {result.peak_thrust_time_s:.6f} s")
    print(f"5% threshold:          {result.threshold_thrust_N:.6f} N")
    print(f"5% start:              {result.burn_start_5pct_time_s:.6f} s")
    print(f"5% end:                {result.burn_end_5pct_time_s:.6f} s")
    print(f"5% burn time:          {result.burn_time_5pct_s:.6f} s")
    print(f"Total impulse:         {result.total_impulse_Ns:.6f} Ns")
    print(f"Normalized impulse:    {result.normalized_impulse_Ns:.6f} Ns")
    print(f"Average thrust:        {result.average_thrust_N:.6f} N")
    print(f"Initial thrust:        {result.initial_thrust_average_N:.6f} N")
    print(f"Curve start:           {result.curve_start_time_s:.6f} s")
    print(f"Curve end:             {result.curve_end_time_s:.6f} s")
    print(f"Impulse class:         {result.impulse_class}")
    print(f"Designation:           {result.designation}")

    assert np.isclose(
        result.peak_thrust_N,
        3230.33973,
        atol=1e-6,
    )
    assert np.isclose(
        result.peak_thrust_time_s,
        0.134,
        atol=1e-9,
    )
    assert np.isclose(
        result.threshold_thrust_N,
        161.5169865,
        atol=1e-6,
    )

    assert np.isclose(
        result.burn_start_5pct_time_s,
        0.04420975344518875,
        atol=1e-9,
    )
    assert np.isclose(
        result.burn_end_5pct_time_s,
        7.11732555623781,
        atol=1e-9,
    )
    assert np.isclose(
        result.burn_time_5pct_s,
        7.07311580279262,
        atol=1e-9,
    )

    assert np.isclose(
        result.total_impulse_Ns,
        14471.744319591,
        atol=1e-6,
    )
    assert np.isclose(
        result.normalized_impulse_Ns,
        14367.091390267766,
        atol=1e-6,
    )
    assert np.isclose(
        result.average_thrust_N,
        2031.2252465307192,
        atol=1e-6,
    )
    assert np.isclose(
        result.initial_thrust_average_N,
        2635.8340208356663,
        atol=1e-6,
    )

    assert np.isclose(
        result.curve_start_time_s,
        0.0,
        atol=1e-12,
    )
    assert np.isclose(
        result.curve_end_time_s,
        8.538,
        atol=1e-12,
    )

    assert result.impulse_class == "N"
    assert result.designation == "N2031"

    print()
    print("Zerox reference:      PASSED")
    print("5% crossing:          PASSED")
    print("Impulse reduction:    PASSED")
    print("Average thrust:       PASSED")
    print("Initial thrust:       PASSED")
    print("Curve boundaries:     PASSED")
    print("Classification:       PASSED")

    print()
    print("Negative thrust handling")

    negative_data = TestData(
        time_s=np.array([0.0, 1.0, 2.0]),
        thrust_N=np.array([10.0, -100.0, 10.0]),
    )

    negative_result = reducer.reduce(
        negative_data
    )

    assert np.isclose(
        negative_result.total_impulse_Ns,
        10.0,
        atol=1e-12,
    )

    print("Negative thrust:      PASSED")

    print()
    print("Non-finite sample handling")

    gap_data = TestData(
        time_s=np.array(
            [0.0, 1.0, 2.0, 3.0]
        ),
        thrust_N=np.array(
            [10.0, np.nan, 10.0, 0.0]
        ),
    )

    gap_result = reducer.reduce(
        gap_data
    )

    # Non-finite samples are excluded rather than causing a failure.
    # The remaining finite samples form the valid curve.
    assert np.isfinite(
        gap_result.total_impulse_Ns
    )

    print("Non-finite samples:   PASSED")

    print()
    print("=" * 70)
    print("ALL PERFORMANCE REDUCTION TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
