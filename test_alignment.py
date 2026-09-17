import numpy as np

from src.rmcs_analyzer.data.models import TestData
from src.rmcs_analyzer.processing.alignment import (
    AlignmentSettings,
    TimeAligner,
)
from src.rmcs_analyzer.processing.event_model import (
    DetectedEvent,
    EventSet,
    EventType,
)


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def build_test_data():
    time = np.array(
        [
            0.0,
            0.1,
            0.2,
            0.3,
            0.4,
            0.5,
        ],
        dtype=float,
    )

    thrust = np.array(
        [
            5.0,
            5.0,
            6.0,
            20.0,
            30.0,
            10.0,
        ],
        dtype=float,
    )

    raw_hx711 = np.arange(
        100,
        106,
        dtype=float,
    )

    delta = np.arange(
        10,
        16,
        dtype=float,
    )

    state = np.array(
        [
            "WAITING",
            "WAITING",
            "BURNING",
            "BURNING",
            "BURNING",
            "POST_BURN",
        ],
        dtype=str,
    )

    pressure = np.arange(
        101,
        107,
        dtype=float,
    )

    return TestData(
        time_s=time,
        thrust_N=thrust,
        raw_hx711=raw_hx711,
        delta=delta,
        state=state,
        pressure_kPa=pressure,
    )


def build_events():
    events = EventSet()

    events.add(
        DetectedEvent(
            event_type=EventType.IGNITION,
            time_s=0.2,
            sample_index=2,
            value=6.0,
        )
    )

    events.add(
        DetectedEvent(
            event_type=EventType.BURNOUT,
            time_s=0.5,
            sample_index=5,
            value=10.0,
        )
    )

    events.add(
        DetectedEvent(
            event_type=EventType.PEAK_THRUST,
            time_s=0.4,
            sample_index=4,
            value=30.0,
        )
    )

    return events


def test_alignment_disabled():
    print_header("Alignment disabled")

    data = build_test_data()

    settings = AlignmentSettings(
        enabled=False,
    )

    result = TimeAligner.align(
        data,
        settings,
    )

    np.testing.assert_array_equal(
        result.data.time_s,
        data.time_s,
    )

    assert result.offset_s == 0.0
    assert result.reference_time_s == 0.0
    assert result.reference_event is None

    print("Alignment enabled:    NO")
    print("Time changed:         NO")
    print("Offset:               0.000 s")
    print("Disabled handling:    PASSED")


def test_ignition_alignment():
    print_header("Ignition alignment")

    data = build_test_data()
    events = build_events()

    settings = AlignmentSettings(
        enabled=True,
        reference_event=EventType.IGNITION,
    )

    result = TimeAligner.align(
        data,
        settings,
        events,
    )

    expected_time = np.array(
        [
            -0.2,
            -0.1,
            0.0,
            0.1,
            0.2,
            0.3,
        ],
        dtype=float,
    )

    np.testing.assert_allclose(
        result.data.time_s,
        expected_time,
    )

    assert result.reference_time_s == 0.2
    assert result.offset_s == -0.2

    assert result.reference_event is not None
    assert (
        result.reference_event.event_type
        == EventType.IGNITION
    )

    print("Reference event:      IGNITION")
    print("Original time:        0.200 s")
    print("Aligned time:         0.000 s")
    print("Offset:               -0.200 s")
    print("Alignment:            PASSED")


def test_burnout_alignment():
    print_header("Burnout alignment")

    data = build_test_data()
    events = build_events()

    settings = AlignmentSettings(
        enabled=True,
        reference_event=EventType.BURNOUT,
    )

    result = TimeAligner.align(
        data,
        settings,
        events,
    )

    expected_time = np.array(
        [
            -0.5,
            -0.4,
            -0.3,
            -0.2,
            -0.1,
            0.0,
        ],
        dtype=float,
    )

    np.testing.assert_allclose(
        result.data.time_s,
        expected_time,
    )

    assert result.reference_time_s == 0.5
    assert result.reference_event is not None

    print("Reference event:      BURNOUT")
    print("Original time:        0.500 s")
    print("Aligned time:         0.000 s")
    print("Offset:               -0.500 s")
    print("Alignment:            PASSED")


def test_manual_alignment():
    print_header("Manual time alignment")

    data = build_test_data()

    settings = AlignmentSettings(
        enabled=True,
        manual_reference_time_s=0.3,
    )

    result = TimeAligner.align(
        data,
        settings,
    )

    expected_time = np.array(
        [
            -0.3,
            -0.2,
            -0.1,
            0.0,
            0.1,
            0.2,
        ],
        dtype=float,
    )

    np.testing.assert_allclose(
        result.data.time_s,
        expected_time,
    )

    assert result.reference_time_s == 0.3
    assert result.offset_s == -0.3
    assert result.reference_event is None

    print("Manual reference:     0.300 s")
    print("Aligned reference:    0.000 s")
    print("Offset:               -0.300 s")
    print("Manual alignment:     PASSED")


def test_thrust_unchanged():
    print_header("Thrust protection")

    data = build_test_data()
    events = build_events()

    original_thrust = data.thrust_N.copy()

    settings = AlignmentSettings(
        enabled=True,
        reference_event=EventType.IGNITION,
    )

    result = TimeAligner.align(
        data,
        settings,
        events,
    )

    np.testing.assert_array_equal(
        result.data.thrust_N,
        original_thrust,
    )

    print("Time changed:         YES")
    print("Thrust changed:       NO")
    print("Thrust protection:    PASSED")


def test_optional_channels_preserved():
    print_header("Optional channels preserved")

    data = build_test_data()
    events = build_events()

    settings = AlignmentSettings(
        enabled=True,
        reference_event=EventType.IGNITION,
    )

    result = TimeAligner.align(
        data,
        settings,
        events,
    )

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
    events = build_events()

    original_time = data.time_s.copy()
    original_thrust = data.thrust_N.copy()

    settings = AlignmentSettings(
        enabled=True,
        reference_event=EventType.IGNITION,
    )

    result = TimeAligner.align(
        data,
        settings,
        events,
    )

    result.data.time_s[:] = -999
    result.data.thrust_N[:] = -999

    np.testing.assert_array_equal(
        data.time_s,
        original_time,
    )

    np.testing.assert_array_equal(
        data.thrust_N,
        original_thrust,
    )

    print("Aligned data modified: YES")
    print("Raw time changed:      NO")
    print("Raw thrust changed:    NO")
    print("Raw protection:        PASSED")


def test_missing_reference_event():
    print_header("Missing reference event")

    data = build_test_data()

    events = EventSet()

    settings = AlignmentSettings(
        enabled=True,
        reference_event=EventType.IGNITION,
    )

    try:
        TimeAligner.align(
            data,
            settings,
            events,
        )
    except ValueError as exc:
        print("Reference missing:     YES")
        print("Alignment rejected:    YES")
        print()
        print(str(exc))
        return

    raise AssertionError(
        "Alignment should reject a missing reference event."
    )


def test_manual_reference_without_events():
    print_header("Manual reference without events")

    data = build_test_data()

    settings = AlignmentSettings(
        enabled=True,
        manual_reference_time_s=0.2,
    )

    result = TimeAligner.align(
        data,
        settings,
    )

    assert result.reference_event is None
    assert result.reference_time_s == 0.2

    print("Events supplied:       NO")
    print("Manual reference:      0.200 s")
    print("Alignment:             PASSED")


def test_invalid_manual_reference():
    print_header("Invalid manual reference")

    data = build_test_data()

    settings = AlignmentSettings(
        enabled=True,
        manual_reference_time_s=np.nan,
    )

    try:
        TimeAligner.align(
            data,
            settings,
        )
    except ValueError as exc:
        print("Invalid reference:     YES")
        print("Alignment rejected:    YES")
        print()
        print(str(exc))
        return

    raise AssertionError(
        "Non-finite manual reference should be rejected."
    )


def test_reset():
    print_header("Alignment settings reset")

    settings = AlignmentSettings(
        enabled=True,
        reference_event=EventType.BURNOUT,
        manual_reference_time_s=1.25,
    )

    settings.reset()

    assert settings.enabled is False
    assert (
        settings.reference_event
        == EventType.IGNITION
    )
    assert settings.manual_reference_time_s is None

    print("Enabled:               RESET")
    print("Reference event:       IGNITION")
    print("Manual reference:      RESET")
    print("Reset:                 PASSED")


def main():
    print("RMCS Analyzer Time Alignment Tests")
    print("=" * 70)

    test_alignment_disabled()
    test_ignition_alignment()
    test_burnout_alignment()
    test_manual_alignment()
    test_thrust_unchanged()
    test_optional_channels_preserved()
    test_raw_data_unchanged()
    test_missing_reference_event()
    test_manual_reference_without_events()
    test_invalid_manual_reference()
    test_reset()

    print()
    print("=" * 70)
    print("ALL TIME ALIGNMENT TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()