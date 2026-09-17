import numpy as np

from src.rmcs_analyzer.analysis.events import EventDetector
from src.rmcs_analyzer.data.csv_reader import RMCSCSVReader
from src.rmcs_analyzer.data.models import TestData
from src.rmcs_analyzer.processing.event_model import EventType


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def build_threshold_test_data():
    time = np.arange(
        10,
        dtype=float,
    )

    thrust = np.array(
        [0, 0, 1, 6, 20, 30, 20, 6, 1, 0],
        dtype=float,
    )

    return TestData(
        time_s=time,
        thrust_N=thrust,
    )


def build_rmcs_state_test_data():
    time = np.arange(
        10,
        dtype=float,
    )

    thrust = np.array(
        [0, 0, 5, 20, 30, 25, 10, 3, 0, 0],
        dtype=float,
    )

    state = np.array(
        [
            "WAITING_FOR_IGNITION",
            "WAITING_FOR_IGNITION",
            "BURNING",
            "BURNING",
            "BURNING",
            "BURNING",
            "BURNING",
            "POST_BURN",
            "POST_BURN",
            "POST_BURN",
        ],
        dtype=str,
    )

    return TestData(
        time_s=time,
        thrust_N=thrust,
        state=state,
    )


def test_threshold_detection():
    print_header("Threshold event detection")

    data = build_threshold_test_data()

    detector = EventDetector(
        threshold_N=5.0
    )

    events = detector.detect_events(data)

    assert events.ignition is not None
    assert events.burnout is not None
    assert events.peak_thrust is not None

    assert (
        events.ignition.event_type
        == EventType.IGNITION
    )

    assert (
        events.burnout.event_type
        == EventType.BURNOUT
    )

    assert (
        events.peak_thrust.event_type
        == EventType.PEAK_THRUST
    )

    assert events.ignition.sample_index == 3
    assert events.burnout.sample_index == 7
    assert events.peak_thrust.sample_index == 5

    assert events.ignition.time_s == 3.0
    assert events.burnout.time_s == 7.0
    assert events.peak_thrust.time_s == 5.0

    assert events.ignition.value == 6.0
    assert events.burnout.value == 6.0
    assert events.peak_thrust.value == 30.0

    print("Ignition:              3.000 s")
    print("Burnout:               7.000 s")
    print("Peak thrust:           5.000 s")
    print("Peak value:            30.000 N")
    print("Detection:             PASSED")


def test_rmcs_state_detection():
    print_header("RMCS state detection")

    data = build_rmcs_state_test_data()

    detector = EventDetector()

    events = detector.detect_events(data)

    assert events.ignition is not None
    assert events.burnout is not None
    assert events.peak_thrust is not None

    assert events.ignition.sample_index == 2
    assert events.burnout.sample_index == 7
    assert events.peak_thrust.sample_index == 4

    assert events.ignition.time_s == 2.0
    assert events.burnout.time_s == 7.0
    assert events.peak_thrust.time_s == 4.0

    assert events.ignition.value == 5.0
    assert events.burnout.value == 3.0
    assert events.peak_thrust.value == 30.0

    assert (
        "RMCS state data"
        in events.ignition.notes
    )

    print("Ignition:              2.000 s")
    print("Burnout:               7.000 s")
    print("Peak thrust:           4.000 s")
    print("Detection:             RMCS state data")
    print("Detection:             PASSED")


def test_automatic_flag():
    print_header("Automatic detection flag")

    data = build_threshold_test_data()

    detector = EventDetector()

    events = detector.detect_events(data)

    assert events.ignition is not None
    assert events.burnout is not None
    assert events.peak_thrust is not None

    assert events.ignition.automatically_detected
    assert events.burnout.automatically_detected
    assert events.peak_thrust.automatically_detected

    print("Ignition:              AUTOMATIC")
    print("Burnout:               AUTOMATIC")
    print("Peak thrust:           AUTOMATIC")


def test_original_detect_api_preserved():
    print_header("Existing EventResults API")

    data = build_threshold_test_data()

    detector = EventDetector(
        threshold_N=5.0
    )

    results = detector.detect(data)

    assert results.ignition_time_s == 3.0
    assert results.burnout_time_s == 7.0
    assert results.peak_time_s == 5.0

    assert results.ignition_index == 3
    assert results.burnout_index == 7
    assert results.peak_index == 5

    print("Existing detect():    PRESERVED")
    print("EventResults:          PASSED")


def test_empty_data():
    print_header("Empty data")

    data = TestData(
        time_s=np.array([], dtype=float),
        thrust_N=np.array([], dtype=float),
    )

    detector = EventDetector()

    events = detector.detect_events(data)

    assert len(events.events) == 0

    print("Event count:           0")
    print("Empty handling:        PASSED")


def test_no_threshold_crossing():
    print_header("No threshold crossing")

    data = TestData(
        time_s=np.arange(
            5,
            dtype=float,
        ),
        thrust_N=np.array(
            [0, 1, 2, 3, 4],
            dtype=float,
        ),
    )

    detector = EventDetector(
        threshold_N=5.0
    )

    events = detector.detect_events(data)

    assert len(events.events) == 0

    print("Events detected:       0")
    print("No-event handling:     PASSED")


def test_real_test_file():
    print_header("Real TEST_010_SAMPLE_MOTOR.csv")

    reader = RMCSCSVReader()

    data = reader.read(
        "test_data/TEST_010_SAMPLE_MOTOR.csv"
    )

    detector = EventDetector()

    events = detector.detect_events(data)

    assert events.ignition is not None
    assert events.burnout is not None
    assert events.peak_thrust is not None

    print(
        f"Ignition:              "
        f"{events.ignition.time_s:.3f} s"
    )

    print(
        f"Burnout:               "
        f"{events.burnout.time_s:.3f} s"
    )

    print(
        f"Peak thrust:           "
        f"{events.peak_thrust.time_s:.3f} s"
    )

    print(
        f"Peak value:            "
        f"{events.peak_thrust.value:.3f} N"
    )

    print(
        f"Ignition sample:       "
        f"{events.ignition.sample_index}"
    )

    print(
        f"Burnout sample:        "
        f"{events.burnout.sample_index}"
    )

    print(
        f"Peak sample:           "
        f"{events.peak_thrust.sample_index}"
    )

    print("Real-file detection:   PASSED")


def main():
    print("RMCS Analyzer Event Detection Tests")
    print("=" * 70)

    test_threshold_detection()
    test_rmcs_state_detection()
    test_automatic_flag()
    test_original_detect_api_preserved()
    test_empty_data()
    test_no_threshold_crossing()
    test_real_test_file()

    print()
    print("=" * 70)
    print("ALL EVENT DETECTION TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()