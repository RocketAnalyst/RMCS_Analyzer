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


def test_event_types():
    print_header("Event types")

    assert EventType.IGNITION.value == "ignition"
    assert EventType.BURNOUT.value == "burnout"
    assert EventType.PEAK_THRUST.value == "peak_thrust"
    assert EventType.CUSTOM.value == "custom"

    print("Ignition:              PASSED")
    print("Burnout:               PASSED")
    print("Peak thrust:           PASSED")
    print("Custom:                PASSED")


def test_detected_event():
    print_header("Detected event")

    event = DetectedEvent(
        event_type=EventType.IGNITION,
        time_s=0.586,
        sample_index=49,
        value=5.2,
        confidence=0.97,
        label="Ignition",
        notes="Detected from thrust threshold.",
        automatically_detected=True,
    )

    assert event.event_type == EventType.IGNITION
    assert event.time_s == 0.586
    assert event.sample_index == 49
    assert event.value == 5.2
    assert event.confidence == 0.97
    assert event.label == "Ignition"
    assert event.notes == "Detected from thrust threshold."
    assert event.automatically_detected is True

    print("Type:                  IGNITION")
    print("Time:                  0.586 s")
    print("Sample:                49")
    print("Value:                 5.200")
    print("Confidence:            0.970")
    print("Event model:           PASSED")


def test_event_set():
    print_header("Event set")

    events = EventSet()

    ignition = DetectedEvent(
        event_type=EventType.IGNITION,
        time_s=0.586,
        sample_index=49,
        value=5.2,
    )

    burnout = DetectedEvent(
        event_type=EventType.BURNOUT,
        time_s=4.503,
        sample_index=384,
        value=3.1,
    )

    peak = DetectedEvent(
        event_type=EventType.PEAK_THRUST,
        time_s=1.732,
        sample_index=144,
        value=363.4,
    )

    events.add(ignition)
    events.add(burnout)
    events.add(peak)

    assert len(events.events) == 3

    assert events.ignition is ignition
    assert events.burnout is burnout
    assert events.peak_thrust is peak

    assert events.get(EventType.IGNITION) is ignition
    assert events.get(EventType.BURNOUT) is burnout
    assert events.get(EventType.PEAK_THRUST) is peak

    print("Ignition stored:       YES")
    print("Burnout stored:        YES")
    print("Peak thrust stored:    YES")
    print("Event count:           3")


def test_get_all():
    print_header("Multiple events")

    events = EventSet()

    events.add(
        DetectedEvent(
            event_type=EventType.CUSTOM,
            time_s=1.0,
            label="Marker 1",
        )
    )

    events.add(
        DetectedEvent(
            event_type=EventType.CUSTOM,
            time_s=2.0,
            label="Marker 2",
        )
    )

    events.add(
        DetectedEvent(
            event_type=EventType.CUSTOM,
            time_s=3.0,
            label="Marker 3",
        )
    )

    custom_events = events.get_all(
        EventType.CUSTOM
    )

    assert len(custom_events) == 3
    assert custom_events[0].label == "Marker 1"
    assert custom_events[1].label == "Marker 2"
    assert custom_events[2].label == "Marker 3"

    print("Custom events:        3")
    print("All events retrieved: YES")


def test_missing_event():
    print_header("Missing event")

    events = EventSet()

    assert events.ignition is None
    assert events.burnout is None
    assert events.peak_thrust is None

    print("Missing ignition:     None")
    print("Missing burnout:      None")
    print("Missing peak thrust:  None")
    print("Missing handling:     PASSED")


def test_event_serialization():
    print_header("Event serialization")

    event = DetectedEvent(
        event_type=EventType.BURNOUT,
        time_s=4.503,
        sample_index=384,
        value=3.1,
        confidence=0.91,
        label="Burnout",
        notes="Detected from falling thrust.",
        automatically_detected=True,
    )

    data = event.to_dict()

    assert data == {
        "event_type": "burnout",
        "time_s": 4.503,
        "sample_index": 384,
        "value": 3.1,
        "confidence": 0.91,
        "label": "Burnout",
        "notes": "Detected from falling thrust.",
        "automatically_detected": True,
    }

    restored = DetectedEvent.from_dict(data)

    assert restored.event_type == event.event_type
    assert restored.time_s == event.time_s
    assert restored.sample_index == event.sample_index
    assert restored.value == event.value
    assert restored.confidence == event.confidence
    assert restored.label == event.label
    assert restored.notes == event.notes
    assert (
        restored.automatically_detected
        == event.automatically_detected
    )

    print("Dictionary created:   YES")
    print("Event restored:       YES")
    print("Values preserved:     YES")
    print("Serialization:        PASSED")


def test_event_set_serialization():
    print_header("Event set serialization")

    original = EventSet()

    original.add(
        DetectedEvent(
            event_type=EventType.IGNITION,
            time_s=0.586,
            sample_index=49,
            value=5.2,
        )
    )

    original.add(
        DetectedEvent(
            event_type=EventType.BURNOUT,
            time_s=4.503,
            sample_index=384,
            value=3.1,
        )
    )

    original.add(
        DetectedEvent(
            event_type=EventType.PEAK_THRUST,
            time_s=1.732,
            sample_index=144,
            value=363.4,
        )
    )

    data = original.to_dict()

    restored = EventSet.from_dict(data)

    assert len(restored.events) == 3

    assert restored.ignition is not None
    assert restored.burnout is not None
    assert restored.peak_thrust is not None

    assert restored.ignition.time_s == 0.586
    assert restored.burnout.time_s == 4.503
    assert restored.peak_thrust.value == 363.4

    print("Events serialized:   3")
    print("Events restored:     3")
    print("Values preserved:    YES")
    print("Round trip:           PASSED")


def test_clear():
    print_header("Clear event set")

    events = EventSet()

    events.add(
        DetectedEvent(
            event_type=EventType.IGNITION,
            time_s=0.5,
        )
    )

    events.add(
        DetectedEvent(
            event_type=EventType.BURNOUT,
            time_s=4.5,
        )
    )

    assert len(events.events) == 2

    events.clear()

    assert len(events.events) == 0
    assert events.ignition is None
    assert events.burnout is None

    print("Events before clear:  2")
    print("Events after clear:   0")
    print("Clear:                 PASSED")


def test_manual_event():
    print_header("Manual event")

    event = DetectedEvent(
        event_type=EventType.CUSTOM,
        time_s=2.250,
        label="User Marker",
        notes="User-selected event.",
        automatically_detected=False,
    )

    assert event.automatically_detected is False
    assert event.label == "User Marker"
    assert event.time_s == 2.250

    print("Event type:            CUSTOM")
    print("Time:                  2.250 s")
    print("Automatic detection:  NO")
    print("Manual event:          PASSED")


def main():
    print("RMCS Analyzer Event Model Tests")
    print("=" * 70)

    test_event_types()
    test_detected_event()
    test_event_set()
    test_get_all()
    test_missing_event()
    test_event_serialization()
    test_event_set_serialization()
    test_clear()
    test_manual_event()

    print()
    print("=" * 70)
    print("ALL EVENT MODEL TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()