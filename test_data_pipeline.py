import numpy as np

from src.rmcs_analyzer.data.csv_reader import RMCSCSVReader
from src.rmcs_analyzer.data.models import TestData
from src.rmcs_analyzer.processing.event_model import EventType
from src.rmcs_analyzer.processing.pipeline import ProcessingPipeline
from src.rmcs_analyzer.processing.settings import ProcessingSettings


def make_test_data():
    """Create a small synthetic test dataset."""
    time_s = np.arange(0.0, 1.0, 0.1)

    thrust_N = np.array([
        5.0,
        5.0,
        5.0,
        10.0,
        20.0,
        30.0,
        20.0,
        10.0,
        5.0,
        5.0,
    ])

    raw_hx711 = np.arange(1000, 1010, dtype=float)

    return TestData(
        time_s=time_s,
        thrust_N=thrust_N,
        raw_hx711=raw_hx711,
    )


def make_alignment_test_data():
    """Create synthetic data with clear ignition and burnout events."""
    time_s = np.arange(0.0, 1.0, 0.1)

    thrust_N = np.array([
        0.0,
        0.0,
        0.0,
        10.0,
        20.0,
        30.0,
        20.0,
        10.0,
        0.0,
        0.0,
    ])

    raw_hx711 = np.arange(2000, 2010, dtype=float)

    return TestData(
        time_s=time_s,
        thrust_N=thrust_N,
        raw_hx711=raw_hx711,
    )


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main():
    print("RMCS Analyzer Processing Pipeline Tests")
    print("=" * 70)

    pipeline = ProcessingPipeline()

    # ---------------------------------------------------------
    # Default processing
    # ---------------------------------------------------------

    print_header("Default processing")

    test_data = make_test_data()

    result = pipeline.process(test_data)

    print(
        f"Raw validation:       "
        f"{'VALID' if result.raw_validation.valid else 'INVALID'}"
    )

    print(
        f"Prepared validation:  "
        f"{'VALID' if result.prepared_validation.valid else 'INVALID'}"
    )

    print(
        f"Baseline:             "
        f"{result.baseline_result.baseline_N:.3f} N"
    )

    print(
        f"Modified:             "
        f"{'YES' if result.modified else 'NO'}"
    )

    print(
        f"Samples:              "
        f"{result.prepared_data.sample_count}"
    )

    assert np.isclose(
        result.baseline_result.baseline_N,
        11.5,
    )

    assert result.valid
    assert result.prepared_data.sample_count == 10
    assert result.modified

    print("Default processing:   PASSED")

    # ---------------------------------------------------------
    # Trim + baseline processing
    # ---------------------------------------------------------

    print_header("Trim + baseline processing")

    test_data = make_test_data()

    settings = ProcessingSettings()

    settings.cleaning.start_time_s = 0.2
    settings.cleaning.end_time_s = 0.61

    settings.baseline.baseline_start_time_s = 0.2
    settings.baseline.baseline_end_time_s = 0.31

    result = pipeline.process(
        test_data,
        settings,
    )

    print(
        f"Raw validation:       "
        f"{'VALID' if result.raw_validation.valid else 'INVALID'}"
    )

    print(
        f"Trimmed samples:      "
        f"{result.prepared_data.sample_count}"
    )

    print(
        f"Baseline:             "
        f"{result.baseline_result.baseline_N:.3f} N"
    )

    print(
        f"Prepared validation:  "
        f"{'VALID' if result.prepared_validation.valid else 'INVALID'}"
    )

    assert result.prepared_data.sample_count == 5
    assert np.isclose(
        result.baseline_result.baseline_N,
        7.5,
    )
    assert result.valid

    print("Processing:            PASSED")

    # ---------------------------------------------------------
    # Baseline-only processing
    # ---------------------------------------------------------

    print_header("Baseline-only processing")

    test_data = make_test_data()

    settings = ProcessingSettings()

    settings.baseline.baseline_start_time_s = 0.0
    settings.baseline.baseline_end_time_s = 0.21

    result = pipeline.process(
        test_data,
        settings,
    )

    print(
        f"Original samples:     "
        f"{result.raw_data.sample_count}"
    )

    print(
        f"Prepared samples:     "
        f"{result.prepared_data.sample_count}"
    )

    print(
        f"Baseline:             "
        f"{result.baseline_result.baseline_N:.3f} N"
    )

    print(
        f"Sample count changed: "
        f"{'YES' if result.prepared_data.sample_count != result.raw_data.sample_count else 'NO'}"
    )

    assert np.isclose(
        result.baseline_result.baseline_N,
        5.0,
    )

    assert result.raw_data.sample_count == 10
    assert result.prepared_data.sample_count == 10
    assert result.valid

    # ---------------------------------------------------------
    # Raw data protection
    # ---------------------------------------------------------

    print_header("Raw data protection")

    test_data = make_test_data()

    original_time = test_data.time_s.copy()
    original_thrust = test_data.thrust_N.copy()
    original_raw = test_data.raw_hx711.copy()

    settings = ProcessingSettings()

    settings.baseline.baseline_start_time_s = 0.0
    settings.baseline.baseline_end_time_s = 0.21

    result = pipeline.process(
        test_data,
        settings,
    )

    prepared_changed = not np.array_equal(
        result.prepared_data.thrust_N,
        original_thrust,
    )

    raw_changed = (
        not np.array_equal(test_data.time_s, original_time)
        or not np.array_equal(test_data.thrust_N, original_thrust)
        or not np.array_equal(test_data.raw_hx711, original_raw)
    )

    print(
        f"Prepared data modified: "
        f"{'YES' if prepared_changed else 'NO'}"
    )

    print(
        f"Raw data changed:       "
        f"{'YES' if raw_changed else 'NO'}"
    )

    assert prepared_changed
    assert not raw_changed

    print("Raw data protection:    PASSED")

    # ---------------------------------------------------------
    # Invalid raw data
    # ---------------------------------------------------------

    print_header("Invalid raw data")

    invalid_data = TestData(
        time_s=np.array([
            0.0,
            0.1,
            0.2,
            0.15,
            0.4,
        ]),
        thrust_N=np.array([
            1.0,
            2.0,
            3.0,
            4.0,
            5.0,
        ]),
    )

    rejected = False

    try:
        pipeline.process(invalid_data)
    except ValueError:
        rejected = True

    print(
        f"Invalid data detected: "
        f"{'YES' if rejected else 'NO'}"
    )

    print(
        f"Pipeline rejected data: "
        f"{'YES' if rejected else 'NO'}"
    )

    assert rejected

    # ---------------------------------------------------------
    # Prepared data validation
    # ---------------------------------------------------------

    print_header("Prepared data validation")

    test_data = make_test_data()

    settings = ProcessingSettings()

    settings.cleaning.start_time_s = 0.2
    settings.cleaning.end_time_s = 0.61

    result = pipeline.process(
        test_data,
        settings,
    )

    print(
        f"Prepared samples: "
        f"{result.prepared_data.sample_count}"
    )

    print(
        f"Prepared rate:   "
        f"{result.prepared_data.sample_rate_hz:.3f} Hz"
    )

    print(
        f"Prepared data:   "
        f"{'VALID' if result.prepared_validation.valid else 'INVALID'}"
    )

    assert result.prepared_validation.valid

    # ---------------------------------------------------------
    # Event detection through pipeline
    # ---------------------------------------------------------

    print_header("Event detection through pipeline")

    test_data = make_alignment_test_data()

    settings = ProcessingSettings()

    settings.baseline.baseline_start_time_s = 0.0
    settings.baseline.baseline_end_time_s = 0.21

    result = pipeline.process(
        test_data,
        settings,
    )

    assert result.event_set is not None

    ignition = result.event_set.ignition
    burnout = result.event_set.burnout
    peak = result.event_set.peak_thrust

    print(
        f"Ignition detected:    "
        f"{'YES' if ignition is not None else 'NO'}"
    )

    print(
        f"Burnout detected:     "
        f"{'YES' if burnout is not None else 'NO'}"
    )

    print(
        f"Peak detected:        "
        f"{'YES' if peak is not None else 'NO'}"
    )

    assert ignition is not None
    assert burnout is not None
    assert peak is not None

    assert np.isclose(ignition.time_s, 0.3)
    assert np.isclose(burnout.time_s, 0.7)
    assert np.isclose(peak.time_s, 0.5)
    assert np.isclose(peak.value, 30.0)

    print("Event detection:      PASSED")

    # ---------------------------------------------------------
    # Alignment disabled
    # ---------------------------------------------------------

    print_header("Alignment disabled")

    test_data = make_alignment_test_data()

    original_time = test_data.time_s.copy()

    settings = ProcessingSettings()

    settings.baseline.baseline_start_time_s = 0.0
    settings.baseline.baseline_end_time_s = 0.21

    settings.alignment.enabled = False

    result = pipeline.process(
        test_data,
        settings,
    )

    print(
        f"Alignment enabled:    "
        f"{'YES' if settings.alignment.enabled else 'NO'}"
    )

    print(
        f"Reference time:       "
        f"{result.alignment_result.reference_time_s:.3f} s"
    )

    print(
        f"Time changed:         "
        f"{'YES' if not np.array_equal(result.prepared_data.time_s, original_time) else 'NO'}"
    )

    assert result.alignment_result is not None

    assert np.isclose(
        result.alignment_result.reference_time_s,
        0.0,
    )

    assert np.array_equal(
        result.prepared_data.time_s,
        original_time,
    )

    print("Alignment disabled:   PASSED")

    # ---------------------------------------------------------
    # Ignition alignment
    # ---------------------------------------------------------

    print_header("Ignition alignment")

    test_data = make_alignment_test_data()

    original_time = test_data.time_s.copy()
    original_thrust = test_data.thrust_N.copy()

    settings = ProcessingSettings()

    settings.baseline.baseline_start_time_s = 0.0
    settings.baseline.baseline_end_time_s = 0.21

    settings.alignment.enabled = True
    settings.alignment.reference_event = EventType.IGNITION

    result = pipeline.process(
        test_data,
        settings,
    )

    alignment = result.alignment_result
    ignition = result.event_set.ignition

    assert alignment is not None
    assert ignition is not None
    assert ignition.sample_index is not None

    print(
        f"Detected ignition:   "
        f"{ignition.time_s:.3f} s"
    )

    print(
        f"Reference time:       "
        f"{alignment.reference_time_s:.3f} s"
    )

    print(
        f"Aligned ignition:     "
        f"{result.prepared_data.time_s[ignition.sample_index]:.3f} s"
    )

    print(
        f"Alignment offset:     "
        f"{alignment.offset_s:.3f} s"
    )

    assert np.isclose(
        alignment.reference_time_s,
        0.3,
    )

    assert np.isclose(
        alignment.offset_s,
        -0.3,
    )

    assert np.isclose(
        result.prepared_data.time_s[ignition.sample_index],
        0.0,
    )

    assert np.array_equal(
        result.prepared_data.thrust_N,
        original_thrust,
    )

    assert np.array_equal(
        test_data.time_s,
        original_time,
    )

    print("Ignition alignment:   PASSED")

    # ---------------------------------------------------------
    # Burnout alignment
    # ---------------------------------------------------------

    print_header("Burnout alignment")

    test_data = make_alignment_test_data()

    settings = ProcessingSettings()

    settings.baseline.baseline_start_time_s = 0.0
    settings.baseline.baseline_end_time_s = 0.21

    settings.alignment.enabled = True
    settings.alignment.reference_event = EventType.BURNOUT

    result = pipeline.process(
        test_data,
        settings,
    )

    alignment = result.alignment_result
    burnout = result.event_set.burnout

    assert alignment is not None
    assert burnout is not None
    assert burnout.sample_index is not None

    print(
        f"Detected burnout:     "
        f"{burnout.time_s:.3f} s"
    )

    print(
        f"Reference time:       "
        f"{alignment.reference_time_s:.3f} s"
    )

    print(
        f"Aligned burnout:      "
        f"{result.prepared_data.time_s[burnout.sample_index]:.3f} s"
    )

    assert np.isclose(
        alignment.reference_time_s,
        0.7,
    )

    assert np.isclose(
        result.prepared_data.time_s[burnout.sample_index],
        0.0,
    )

    print("Burnout alignment:    PASSED")

    # ---------------------------------------------------------
    # Manual alignment
    # ---------------------------------------------------------

    print_header("Manual alignment")

    test_data = make_alignment_test_data()

    settings = ProcessingSettings()

    settings.baseline.baseline_start_time_s = 0.0
    settings.baseline.baseline_end_time_s = 0.21

    settings.alignment.enabled = True
    settings.alignment.manual_reference_time_s = 0.4

    result = pipeline.process(
        test_data,
        settings,
    )

    alignment = result.alignment_result

    assert alignment is not None

    print(
        f"Manual reference:     "
        f"{alignment.reference_time_s:.3f} s"
    )

    print(
        f"Aligned time[4]:      "
        f"{result.prepared_data.time_s[4]:.3f} s"
    )

    assert np.isclose(
        alignment.reference_time_s,
        0.4,
    )

    assert np.isclose(
        result.prepared_data.time_s[4],
        0.0,
    )

    print("Manual alignment:     PASSED")

    # ---------------------------------------------------------
    # Combined trim + baseline + alignment
    # ---------------------------------------------------------

    print_header("Trim + baseline + alignment")

    test_data = make_alignment_test_data()

    original_time = test_data.time_s.copy()
    original_thrust = test_data.thrust_N.copy()

    settings = ProcessingSettings()

    settings.cleaning.start_time_s = 0.1
    settings.cleaning.end_time_s = 0.81

    settings.baseline.baseline_start_time_s = 0.1
    settings.baseline.baseline_end_time_s = 0.21

    settings.alignment.enabled = True
    settings.alignment.reference_event = EventType.IGNITION

    result = pipeline.process(
        test_data,
        settings,
    )

    assert result.valid
    assert result.cleaning_result is not None
    assert result.baseline_result is not None
    assert result.event_set is not None
    assert result.alignment_result is not None

    ignition = result.event_set.ignition

    assert ignition is not None
    assert ignition.sample_index is not None

    print(
        f"Prepared samples:     "
        f"{result.prepared_data.sample_count}"
    )

    print(
        f"Baseline:              "
        f"{result.baseline_result.baseline_N:.3f} N"
    )

    print(
        f"Detected ignition:     "
        f"{ignition.time_s:.3f} s"
    )

    print(
        f"Aligned ignition:      "
        f"{result.prepared_data.time_s[ignition.sample_index]:.3f} s"
    )

    assert result.prepared_data.sample_count == 8

    assert np.isclose(
        result.baseline_result.baseline_N,
        0.0,
    )

    assert np.isclose(
        result.prepared_data.time_s[ignition.sample_index],
        0.0,
    )

    assert np.array_equal(
        test_data.time_s,
        original_time,
    )

    assert np.array_equal(
        test_data.thrust_N,
        original_thrust,
    )

    print("Combined processing:  PASSED")

    # ---------------------------------------------------------
    # Real TEST_010 sample
    # ---------------------------------------------------------

    print_header("Real TEST_010 sample")

    reader = RMCSCSVReader()

    real_data = reader.read(
        "test_data/TEST_010_SAMPLE_MOTOR.csv"
    )

    settings = ProcessingSettings()

    # Use the known pre-ignition portion of the sample as the
    # baseline. The resulting processed peak is therefore
    # expected to be slightly lower than the raw 363.004 N peak.
    settings.baseline.baseline_start_time_s = 0.0
    settings.baseline.baseline_end_time_s = 0.025

    settings.alignment.enabled = True
    settings.alignment.reference_event = EventType.IGNITION

    result = pipeline.process(
        real_data,
        settings,
    )

    assert result.valid
    assert result.event_set is not None
    assert result.alignment_result is not None

    ignition = result.event_set.ignition
    burnout = result.event_set.burnout
    peak = result.event_set.peak_thrust

    assert ignition is not None
    assert burnout is not None
    assert peak is not None

    assert ignition.sample_index is not None
    assert burnout.sample_index is not None
    assert peak.sample_index is not None

    print(
        f"Samples:              "
        f"{real_data.sample_count}"
    )

    print(
        f"Detected ignition:    "
        f"{ignition.time_s:.3f} s"
    )

    print(
        f"Detected burnout:     "
        f"{burnout.time_s:.3f} s"
    )

    print(
        f"Detected peak:        "
        f"{peak.time_s:.3f} s"
    )

    print(
        f"Peak thrust:           "
        f"{peak.value:.3f} N"
    )

    print(
        f"Aligned ignition:     "
        f"{result.prepared_data.time_s[ignition.sample_index]:.3f} s"
    )

    assert np.isclose(
        ignition.time_s,
        0.035,
    )

    assert np.isclose(
        burnout.time_s,
        4.890,
    )

    assert np.isclose(
        peak.time_s,
        0.246,
    )

    # Baseline correction changes the peak from the original
    # raw value of 363.004 N to the processed value 362.907 N.
    assert np.isclose(
        peak.value,
        362.907,
    )

    assert np.isclose(
        result.prepared_data.time_s[ignition.sample_index],
        0.0,
    )

    print("Real sample:          PASSED")

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("ALL PROCESSING PIPELINE TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()