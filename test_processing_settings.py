from src.rmcs_analyzer.processing.alignment import (
    AlignmentSettings,
)
from src.rmcs_analyzer.processing.baseline import (
    BaselineSettings,
)
from src.rmcs_analyzer.processing.cleaning import (
    CleaningSettings,
)
from src.rmcs_analyzer.processing.event_model import (
    EventType,
)
from src.rmcs_analyzer.processing.settings import (
    ProcessingSettings,
)


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def test_default_settings():
    print_header("Default processing settings")

    settings = ProcessingSettings()

    assert settings.cleaning.start_time_s is None
    assert settings.cleaning.end_time_s is None

    assert settings.baseline.baseline_start_time_s is None
    assert settings.baseline.baseline_end_time_s is None

    assert settings.alignment.enabled is False
    assert (
        settings.alignment.reference_event
        == EventType.IGNITION
    )
    assert settings.alignment.manual_reference_time_s is None

    print("Cleaning start:       None")
    print("Cleaning end:         None")
    print("Baseline start:       None")
    print("Baseline end:         None")
    print("Alignment enabled:    False")
    print("Reference event:      IGNITION")
    print("Defaults:             PASSED")


def test_custom_settings():
    print_header("Custom processing settings")

    settings = ProcessingSettings(
        cleaning=CleaningSettings(
            start_time_s=0.586,
            end_time_s=4.503,
        ),
        baseline=BaselineSettings(
            baseline_start_time_s=0.0,
            baseline_end_time_s=0.500,
        ),
        alignment=AlignmentSettings(
            enabled=True,
            reference_event=EventType.IGNITION,
        ),
    )

    assert settings.cleaning.start_time_s == 0.586
    assert settings.cleaning.end_time_s == 4.503

    assert settings.baseline.baseline_start_time_s == 0.0
    assert settings.baseline.baseline_end_time_s == 0.500

    assert settings.alignment.enabled is True
    assert (
        settings.alignment.reference_event
        == EventType.IGNITION
    )

    print("Cleaning:             0.586 → 4.503 s")
    print("Baseline:             0.000 → 0.500 s")
    print("Alignment:             ENABLED")
    print("Reference:             IGNITION")
    print("Custom settings:      PASSED")


def test_to_dict():
    print_header("Settings serialization")

    settings = ProcessingSettings(
        cleaning=CleaningSettings(
            start_time_s=0.586,
            end_time_s=4.503,
        ),
        baseline=BaselineSettings(
            baseline_start_time_s=0.0,
            baseline_end_time_s=0.500,
        ),
        alignment=AlignmentSettings(
            enabled=True,
            reference_event=EventType.BURNOUT,
        ),
    )

    data = settings.to_dict()

    assert data == {
        "cleaning": {
            "start_time_s": 0.586,
            "end_time_s": 4.503,
        },
        "baseline": {
            "baseline_start_time_s": 0.0,
            "baseline_end_time_s": 0.500,
        },
        "alignment": {
            "enabled": True,
            "reference_event": "burnout",
            "manual_reference_time_s": None,
        },
    }

    print("Dictionary created:   YES")
    print("JSON-compatible:      YES")
    print("Alignment included:   YES")
    print("Serialization:        PASSED")


def test_from_dict():
    print_header("Settings deserialization")

    data = {
        "cleaning": {
            "start_time_s": 0.586,
            "end_time_s": 4.503,
        },
        "baseline": {
            "baseline_start_time_s": 0.0,
            "baseline_end_time_s": 0.500,
        },
        "alignment": {
            "enabled": True,
            "reference_event": "burnout",
            "manual_reference_time_s": None,
        },
    }

    settings = ProcessingSettings.from_dict(data)

    assert settings.cleaning.start_time_s == 0.586
    assert settings.cleaning.end_time_s == 4.503

    assert settings.baseline.baseline_start_time_s == 0.0
    assert settings.baseline.baseline_end_time_s == 0.500

    assert settings.alignment.enabled is True
    assert (
        settings.alignment.reference_event
        == EventType.BURNOUT
    )

    print("Cleaning restored:    YES")
    print("Baseline restored:    YES")
    print("Alignment restored:   YES")
    print("Deserialization:      PASSED")


def test_round_trip():
    print_header("Settings round trip")

    original = ProcessingSettings(
        cleaning=CleaningSettings(
            start_time_s=0.586,
            end_time_s=4.503,
        ),
        baseline=BaselineSettings(
            baseline_start_time_s=0.125,
            baseline_end_time_s=0.525,
        ),
        alignment=AlignmentSettings(
            enabled=True,
            reference_event=EventType.IGNITION,
        ),
    )

    serialized = original.to_dict()

    restored = ProcessingSettings.from_dict(
        serialized
    )

    assert restored.cleaning.start_time_s == (
        original.cleaning.start_time_s
    )

    assert restored.cleaning.end_time_s == (
        original.cleaning.end_time_s
    )

    assert restored.baseline.baseline_start_time_s == (
        original.baseline.baseline_start_time_s
    )

    assert restored.baseline.baseline_end_time_s == (
        original.baseline.baseline_end_time_s
    )

    assert restored.alignment.enabled == (
        original.alignment.enabled
    )

    assert restored.alignment.reference_event == (
        original.alignment.reference_event
    )

    print("Original → dictionary: YES")
    print("Dictionary → object:  YES")
    print("Alignment preserved:  YES")
    print("Values preserved:     YES")
    print("Round trip:            PASSED")


def test_missing_sections_use_defaults():
    print_header("Missing sections")

    settings = ProcessingSettings.from_dict({})

    assert settings.cleaning.start_time_s is None
    assert settings.cleaning.end_time_s is None

    assert settings.baseline.baseline_start_time_s is None
    assert settings.baseline.baseline_end_time_s is None

    assert settings.alignment.enabled is False
    assert (
        settings.alignment.reference_event
        == EventType.IGNITION
    )

    print("Missing cleaning:     DEFAULTED")
    print("Missing baseline:     DEFAULTED")
    print("Missing alignment:    DEFAULTED")
    print("Default handling:     PASSED")


def test_reset():
    print_header("Reset processing settings")

    settings = ProcessingSettings(
        cleaning=CleaningSettings(
            start_time_s=1.0,
            end_time_s=5.0,
        ),
        baseline=BaselineSettings(
            baseline_start_time_s=0.0,
            baseline_end_time_s=0.750,
        ),
        alignment=AlignmentSettings(
            enabled=True,
            reference_event=EventType.BURNOUT,
            manual_reference_time_s=1.25,
        ),
    )

    settings.reset()

    assert settings.cleaning.start_time_s is None
    assert settings.cleaning.end_time_s is None

    assert settings.baseline.baseline_start_time_s is None
    assert settings.baseline.baseline_end_time_s is None

    assert settings.alignment.enabled is False
    assert (
        settings.alignment.reference_event
        == EventType.IGNITION
    )
    assert settings.alignment.manual_reference_time_s is None

    print("Cleaning reset:      YES")
    print("Baseline reset:      YES")
    print("Alignment reset:     YES")
    print("Reset:                PASSED")


def main():
    print("RMCS Analyzer Processing Settings Tests")
    print("=" * 70)

    test_default_settings()
    test_custom_settings()
    test_to_dict()
    test_from_dict()
    test_round_trip()
    test_missing_sections_use_defaults()
    test_reset()

    print()
    print("=" * 70)
    print("ALL PROCESSING SETTINGS TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()