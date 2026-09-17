import numpy as np

from src.rmcs_analyzer.analysis.analyzer import AnalysisEngine
from src.rmcs_analyzer.data.csv_reader import RMCSCSVReader
from src.rmcs_analyzer.processing.event_model import EventSet


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main():
    print("RMCS Analyzer Analysis Engine Tests")
    print("=" * 70)

    # ---------------------------------------------------------
    # Load real test data
    # ---------------------------------------------------------

    print_header("Load TEST_010 sample")

    reader = RMCSCSVReader()

    test_data = reader.read(
        "test_data/TEST_010_SAMPLE_MOTOR.csv"
    )

    print(
        f"Samples:              "
        f"{test_data.sample_count}"
    )

    print(
        f"Duration:             "
        f"{test_data.duration_s:.3f} s"
    )

    print(
        f"Sample rate:          "
        f"{test_data.sample_rate_hz:.3f} Hz"
    )

    assert test_data.sample_count == 435

    print("Data loading:         PASSED")

    # ---------------------------------------------------------
    # Run analysis without supplied events
    # ---------------------------------------------------------

    print_header("AnalysisEngine event fallback")

    engine = AnalysisEngine()

    analysis = engine.analyze(
        test_data
    )

    assert analysis is not None
    assert analysis.events is not None

    print(
        f"Analysis result:      "
        f"{type(analysis).__name__}"
    )

    print(
        f"Events generated:     "
        f"{type(analysis.events).__name__}"
    )

    print("Event fallback:       PASSED")

    # ---------------------------------------------------------
    # Verify detected events
    # ---------------------------------------------------------

    print_header("Detected events")

    events = analysis.events

    assert events.ignition is not None
    assert events.burnout is not None
    assert events.peak_thrust is not None

    print(
        f"Ignition:             "
        f"{events.ignition.time_s:.3f} s"
    )

    print(
        f"Peak:                 "
        f"{events.peak_thrust.time_s:.3f} s"
    )

    print(
        f"Burnout:              "
        f"{events.burnout.time_s:.3f} s"
    )

    assert np.isclose(
        events.ignition.time_s,
        0.035,
    )

    assert np.isclose(
        events.peak_thrust.time_s,
        0.246,
    )

    assert np.isclose(
        events.burnout.time_s,
        4.890,
    )

    print("Event results:        PASSED")

    # ---------------------------------------------------------
    # Supply an authoritative EventSet
    # ---------------------------------------------------------

    print_header("Supplied EventSet")

    supplied_events = EventSet(
        events=list(events.events)
    )

    supplied_analysis = engine.analyze(
        test_data,
        events=supplied_events,
    )

    assert supplied_analysis.events is supplied_events

    print(
        f"Supplied events used: "
        f"{'YES' if supplied_analysis.events is supplied_events else 'NO'}"
    )

    print(
        f"Same event count:     "
        f"{'YES' if len(supplied_analysis.events.events) == len(events.events) else 'NO'}"
    )

    assert len(
        supplied_analysis.events.events
    ) == len(events.events)

    print("Event handoff:        PASSED")

    # ---------------------------------------------------------
    # Thrust results
    # ---------------------------------------------------------

    print_header("Thrust results")

    thrust = supplied_analysis.thrust

    assert thrust is not None

    print(
        f"Peak thrust:          "
        f"{thrust.peak_thrust_N:.3f} N"
    )

    print(
        f"Average thrust:       "
        f"{thrust.average_thrust_N:.3f} N"
    )

    print(
        f"Total impulse:        "
        f"{thrust.total_impulse_Ns:.3f} Ns"
    )

    print(
        f"Burn time:            "
        f"{thrust.burn_time_s:.3f} s"
    )

    print(
        f"Time to peak:         "
        f"{thrust.time_to_peak_s:.3f} s"
    )

    assert thrust.peak_thrust_N is not None
    assert thrust.average_thrust_N is not None
    assert thrust.total_impulse_Ns is not None
    assert thrust.burn_time_s is not None
    assert thrust.time_to_peak_s is not None

    assert np.isclose(
        thrust.peak_thrust_N,
        363.004,
        atol=0.2,
    )

    assert np.isclose(
        thrust.total_impulse_Ns,
        1116.58,
        atol=2.0,
    )

    print("Thrust analysis:      PASSED")

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    print_header("Statistics")

    statistics = supplied_analysis.statistics

    assert statistics is not None

    print(
        f"Statistics result:    "
        f"{type(statistics).__name__}"
    )

    print("Statistics included:  YES")
    print("Statistics:           PASSED")

    # ---------------------------------------------------------
    # Classification
    # ---------------------------------------------------------

    print_header("Motor classification")

    classification = supplied_analysis.classification

    assert classification is not None

    print(
        f"Motor class:          "
        f"{classification.motor_class}"
    )

    assert classification.motor_class == "J"

    print("Classification:       PASSED")

    # ---------------------------------------------------------
    # Combined result
    # ---------------------------------------------------------

    print_header("Combined AnalysisResults")

    assert supplied_analysis.events is supplied_events
    assert supplied_analysis.thrust is thrust
    assert supplied_analysis.statistics is statistics
    assert supplied_analysis.classification is classification

    print("Events included:      YES")
    print("Thrust included:      YES")
    print("Statistics included:  YES")
    print("Classification:       YES")

    print("Combined result:      PASSED")

    # ---------------------------------------------------------
    # Raw data protection
    # ---------------------------------------------------------

    print_header("Raw data protection")

    original_time = test_data.time_s.copy()
    original_thrust = test_data.thrust_N.copy()

    engine.analyze(
        test_data,
        events=supplied_events,
    )

    assert np.array_equal(
        test_data.time_s,
        original_time,
    )

    assert np.array_equal(
        test_data.thrust_N,
        original_thrust,
    )

    print("Time unchanged:       YES")
    print("Thrust unchanged:     YES")
    print("Raw data protection:  PASSED")

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("ALL ANALYSIS ENGINE TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()