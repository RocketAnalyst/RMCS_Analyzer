import numpy as np

from src.rmcs_analyzer.analysis.analyzer import AnalysisEngine
from src.rmcs_analyzer.data.csv_reader import RMCSCSVReader
from src.rmcs_analyzer.processing.event_model import EventSet


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def _script_regression():
    print("RMCS Analyzer Analysis Engine Tests")
    print("=" * 70)

    print_header("Load Zerox reference")

    reader = RMCSCSVReader()
    test_data = reader.read("test_data/Zerox.csv")

    print(f"Samples:              {test_data.sample_count}")
    print(f"Duration:             {test_data.duration_s:.3f} s")
    print(f"Sample rate:          {test_data.sample_rate_hz:.3f} Hz")

    assert test_data.sample_count == 661
    assert np.isclose(test_data.duration_s, 8.538)
    assert np.isclose(test_data.sample_rate_hz, 77.3014757554)

    print("Data loading:         PASSED")

    print_header("AnalysisEngine event fallback")

    engine = AnalysisEngine()
    analysis = engine.analyze(test_data)

    assert analysis is not None
    assert analysis.events is not None

    print(f"Analysis result:      {type(analysis).__name__}")
    print(f"Events generated:     {type(analysis.events).__name__}")
    print("Event fallback:       PASSED")

    print_header("Detected events")

    events = analysis.events

    assert events.ignition is not None
    assert events.burnout is not None
    assert events.peak_thrust is not None

    print(f"Ignition:             {events.ignition.time_s:.3f} s")
    print(f"Peak:                 {events.peak_thrust.time_s:.3f} s")
    print(f"Burnout:              {events.burnout.time_s:.3f} s")

    assert np.isclose(events.ignition.time_s, 0.215)
    assert np.isclose(events.peak_thrust.time_s, 0.349)
    assert np.isclose(events.burnout.time_s, 8.753)

    print("Event results:        PASSED")

    print_header("Supplied EventSet")

    supplied_events = EventSet(events=list(events.events))

    supplied_analysis = engine.analyze(
        test_data,
        events=supplied_events,
    )

    assert supplied_analysis.events is supplied_events

    print("Supplied events used: YES")
    print("Event handoff:        PASSED")

    print_header("Authoritative core performance results")

    thrust = supplied_analysis.thrust

    print(f"Peak thrust:          {thrust.peak_thrust_N:.3f} N")
    print(f"Average thrust:       {thrust.average_thrust_N:.3f} N")
    print(f"Total impulse:        {thrust.total_impulse_Ns:.3f} Ns")
    print(f"Burn time:            {thrust.burn_time_s:.3f} s")

    assert np.isclose(thrust.peak_thrust_N, 3230.33973, atol=0.001)
    assert np.isclose(thrust.average_thrust_N, 2031.225247, atol=0.001)
    assert np.isclose(thrust.total_impulse_Ns, 14471.744320, atol=0.001)
    assert np.isclose(thrust.burn_time_s, 7.073116, atol=0.001)

    print("Core performance results: PASSED")

    print_header("Standardized performance results")

    thrust = supplied_analysis.thrust

    print(
        f"5% burn start:        "
        f"{thrust.burn_start_5pct_time_s:.6f} s"
    )
    print(
        f"5% burn end:          "
        f"{thrust.burn_end_5pct_time_s:.6f} s"
    )
    print(
        f"5% burn time:         "
        f"{thrust.burn_time_5pct_s:.6f} s"
    )
    print(
        f"5% average thrust:    "
        f"{thrust.average_thrust_5pct_N:.6f} N"
    )
    print(
        f"Initial thrust:        "
        f"{thrust.initial_thrust_average_N:.6f} N"
    )
    print(
        f"Valid-curve impulse:   "
        f"{thrust.total_impulse_valid_curve_Ns:.6f} Ns"
    )
    print(f"Impulse class:         {thrust.impulse_class}")
    print(f"Designation:           {thrust.designation}")

    assert np.isclose(
        thrust.burn_start_5pct_time_s,
        0.04420975344518875,
        atol=1e-9,
    )
    assert np.isclose(
        thrust.burn_end_5pct_time_s,
        7.11732555623781,
        atol=1e-9,
    )
    assert np.isclose(
        thrust.burn_time_5pct_s,
        7.07311580279262,
        atol=1e-9,
    )
    assert np.isclose(
        thrust.average_thrust_5pct_N,
        2031.2252465307192,
        atol=1e-6,
    )
    assert np.isclose(
        thrust.initial_thrust_average_N,
        2635.8340208356663,
        atol=1e-6,
    )
    assert np.isclose(
        thrust.total_impulse_valid_curve_Ns,
        14471.744319591,
        atol=1e-6,
    )
    assert thrust.impulse_class == "N"
    assert thrust.designation == "N2031"

    print("Standardized results: PASSED")

    print_header("Statistics and classification")

    statistics = supplied_analysis.statistics
    classification = supplied_analysis.classification

    assert statistics.sample_count == 661
    assert np.isclose(statistics.maximum_thrust_N, 3230.33973, atol=0.001)
    assert classification.motor_class == "N"

    print(f"Sample count:         {statistics.sample_count}")
    print(f"Maximum thrust:       {statistics.maximum_thrust_N:.3f} N")
    print(f"Motor class:          {classification.motor_class}")
    print("Statistics:           PASSED")
    print("Classification:       PASSED")

    print_header("Raw data protection")

    original_time = test_data.time_s.copy()
    original_thrust = test_data.thrust_N.copy()

    engine.analyze(test_data, events=supplied_events)

    assert np.array_equal(test_data.time_s, original_time)
    assert np.array_equal(test_data.thrust_N, original_thrust)

    print("Time unchanged:       YES")
    print("Thrust unchanged:     YES")
    print("Raw data protection:  PASSED")

    print()
    print("=" * 70)
    print("ALL ANALYSIS ENGINE TESTS PASSED")
    print("=" * 70)


def test_script_regression():
    _script_regression()


if __name__ == "__main__":
    _script_regression()
