from src.rmcs_analyzer.processing.baseline import BaselineSettings
from src.rmcs_analyzer.processing.cleaning import CleaningSettings
from src.rmcs_analyzer.processing.settings import ProcessingSettings


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

    print("Cleaning start:       None")
    print("Cleaning end:         None")
    print("Baseline start:       None")
    print("Baseline end:         None")
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
    )

    assert settings.cleaning.start_time_s == 0.586
    assert settings.cleaning.end_time_s == 4.503

    assert settings.baseline.baseline_start_time_s == 0.0
    assert settings.baseline.baseline_end_time_s == 0.500

    print("Cleaning:             0.586 → 4.503 s")
    print("Baseline:             0.000 → 0.500 s")
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
    }

    print("Dictionary created:   YES")
    print("JSON-compatible:      YES")
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
    }

    settings = ProcessingSettings.from_dict(data)

    assert settings.cleaning.start_time_s == 0.586
    assert settings.cleaning.end_time_s == 4.503

    assert settings.baseline.baseline_start_time_s == 0.0
    assert settings.baseline.baseline_end_time_s == 0.500

    print("Cleaning restored:    YES")
    print("Baseline restored:    YES")
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

    print("Original → dictionary: YES")
    print("Dictionary → object:  YES")
    print("Values preserved:     YES")
    print("Round trip:            PASSED")


def test_missing_sections_use_defaults():
    print_header("Missing sections")

    settings = ProcessingSettings.from_dict({})

    assert settings.cleaning.start_time_s is None
    assert settings.cleaning.end_time_s is None

    assert settings.baseline.baseline_start_time_s is None
    assert settings.baseline.baseline_end_time_s is None

    print("Missing cleaning:     DEFAULTED")
    print("Missing baseline:     DEFAULTED")
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
    )

    settings.reset()

    assert settings.cleaning.start_time_s is None
    assert settings.cleaning.end_time_s is None

    assert settings.baseline.baseline_start_time_s is None
    assert settings.baseline.baseline_end_time_s is None

    print("Cleaning reset:      YES")
    print("Baseline reset:      YES")
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