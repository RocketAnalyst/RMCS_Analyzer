import os

import numpy as np

from src.rmcs_analyzer.data.csv_reader import RMCSCSVReader
from src.rmcs_analyzer.data.models import TestData
from src.rmcs_analyzer.processing.event_model import EventType
from src.rmcs_analyzer.processing.pipeline import ProcessingPipeline
from src.rmcs_analyzer.processing.settings import ProcessingSettings


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def make_test_data():
    time_s = np.arange(10, dtype=float) / 10.0

    thrust_N = np.array(
        [
            5.0,
            5.0,
            5.0,
            15.0,
            25.0,
            30.0,
            25.0,
            15.0,
            5.0,
            5.0,
        ],
        dtype=float,
    )

    raw_thrust_N = thrust_N.copy()

    return TestData(
        time_s=time_s,
        thrust_N=thrust_N,
        raw_thrust_N=raw_thrust_N,
    )


def make_alignment_test_data():
    time_s = np.arange(10, dtype=float) / 10.0

    thrust_N = np.array(
        [
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
        ],
        dtype=float,
    )

    raw_thrust_N = thrust_N.copy()

    return TestData(
        time_s=time_s,
        thrust_N=thrust_N,
        raw_thrust_N=raw_thrust_N,
    )


def test_default_processing(pipeline):
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
        f"Modified:              "
        f"{'YES' if result.modified else 'NO'}"
    )

    print(
        f"Samples:              "
        f"{result.prepared_data.sample_count}"
    )

    assert result.valid
    assert result.prepared_data.sample_count == 10

    print("Default processing:   PASSED")


def test_trim_and_baseline(pipeline):
    print_header("Trim + baseline processing")

    test_data = make_test_data()

    settings = ProcessingSettings()

    settings.cleaning.start_time_s = 0.3
    settings.cleaning.end_time_s = 0.7

    # The baseline window must exist inside the trimmed working
    # dataset because cleaning now occurs before baseline correction.
    settings.baseline.baseline_start_time_s = 0.3
    settings.baseline.baseline_end_time_s = 0.4

    result = pipeline.process(
        test_data,
        settings,
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

    assert result.valid
    assert result.prepared_data.sample_count == 5

    assert np.isclose(
        result.baseline_result.baseline_N,
        20.0,
    )

    print("Processing:            PASSED")


def test_baseline_only(pipeline):
    print_header("Baseline-only processing")

    test_data = make_test_data()

    original_sample_count = test_data.sample_count

    settings = ProcessingSettings()

    settings.baseline.baseline_start_time_s = 0.0
    settings.baseline.baseline_end_time_s = 0.2

    result = pipeline.process(
        test_data,
        settings,
    )

    print(
        f"Original samples:     "
        f"{original_sample_count}"
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
        f"{'YES' if result.prepared_data.sample_count != original_sample_count else 'NO'}"
    )

    assert result.valid

    assert (
        result.prepared_data.sample_count
        == original_sample_count
    )

    assert np.isclose(
        result.baseline_result.baseline_N,
        5.0,
    )

    print("")


def test_raw_data_protection(pipeline):
    print_header("Raw data protection")

    test_data = make_test_data()

    original_time = test_data.time_s.copy()
    original_thrust = test_data.thrust_N.copy()

    settings = ProcessingSettings()

    settings.baseline.baseline_start_time_s = 0.0
    settings.baseline.baseline_end_time_s = 0.2

    result = pipeline.process(
        test_data,
        settings,
    )

    prepared_modified = not np.array_equal(
        result.prepared_data.thrust_N,
        original_thrust,
    )

    raw_time_changed = not np.array_equal(
        test_data.time_s,
        original_time,
    )

    raw_thrust_changed = not np.array_equal(
        test_data.thrust_N,
        original_thrust,
    )

    print(
        f"Prepared data modified: "
        f"{'YES' if prepared_modified else 'NO'}"
    )

    print(
        f"Raw data changed:       "
        f"{'YES' if (raw_time_changed or raw_thrust_changed) else 'NO'}"
    )

    assert result.valid
    assert prepared_modified
    assert not raw_time_changed
    assert not raw_thrust_changed

    print("Raw data protection:    PASSED")


def test_calibrated_time(pipeline):
    print_header("Calibrated time")

    time_s = np.arange(10, dtype=float) / 10.0

    calibrated_time_s = np.array(
        [
            0.00,
            0.11,
            0.22,
            0.33,
            0.44,
            0.55,
            0.66,
            0.77,
            0.88,
            0.99,
        ],
        dtype=float,
    )

    thrust_N = np.ones(10, dtype=float)

    test_data = TestData(
        time_s=time_s,
        thrust_N=thrust_N,
        calibrated_time_s=calibrated_time_s,
    )

    result = pipeline.process(test_data)

    print(
        f"Original first time:  "
        f"{test_data.time_s[0]:.3f} s"
    )

    print(
        f"Analysis first time:  "
        f"{result.prepared_data.time_s[0]:.3f} s"
    )

    print(
        f"Original last time:   "
        f"{test_data.time_s[-1]:.3f} s"
    )

    print(
        f"Analysis last time:   "
        f"{result.prepared_data.time_s[-1]:.3f} s"
    )

    assert result.valid

    assert np.array_equal(
        test_data.time_s,
        time_s,
    )

    assert np.array_equal(
        result.prepared_data.time_s,
        calibrated_time_s,
    )

    assert np.array_equal(
        result.prepared_data.calibrated_time_s,
        calibrated_time_s,
    )

    print("Calibrated time:      PASSED")


def test_calibrated_time_fallback(pipeline):
    print_header("Calibrated time fallback")

    test_data = make_test_data()

    result = pipeline.process(test_data)

    print(
        "Calibrated time:      ABSENT"
    )

    print(
        "Analysis uses Time(s): "
        f"{'YES' if np.array_equal(result.prepared_data.time_s, test_data.time_s) else 'NO'}"
    )

    assert result.valid

    assert np.array_equal(
        result.prepared_data.time_s,
        test_data.time_s,
    )

    print("Fallback:             PASSED")


def test_invalid_raw_data(pipeline):
    print_header("Invalid raw data")

    test_data = TestData(
        time_s=np.array(
            [0.0, 0.2, 0.1],
            dtype=float,
        ),
        thrust_N=np.array(
            [1.0, 2.0, 3.0],
            dtype=float,
        ),
    )

    invalid_detected = False
    pipeline_rejected = False

    try:
        validation = pipeline.validator.validate(
            test_data
        )

        invalid_detected = not validation.valid

        pipeline.process(test_data)

    except ValueError:
        pipeline_rejected = True

    print(
        f"Invalid data detected: "
        f"{'YES' if invalid_detected else 'NO'}"
    )

    print(
        f"Pipeline rejected data: "
        f"{'YES' if pipeline_rejected else 'NO'}"
    )

    assert invalid_detected
    assert pipeline_rejected


def test_prepared_validation(pipeline):
    print_header("Prepared data validation")

    test_data = make_test_data()

    settings = ProcessingSettings()

    settings.cleaning.start_time_s = 0.3
    settings.cleaning.end_time_s = 0.7

    result = pipeline.process(
        test_data,
        settings,
    )

    print(
        f"Prepared samples:     "
        f"{result.prepared_data.sample_count}"
    )

    print(
        f"Prepared rate:        "
        f"{result.prepared_data.sample_rate_hz:.3f} Hz"
    )

    print(
        f"Prepared data:        "
        f"{'VALID' if result.prepared_validation.valid else 'INVALID'}"
    )

    assert result.valid
    assert result.prepared_validation.valid


def test_event_detection(pipeline):
    print_header("Event detection through pipeline")

    test_data = make_alignment_test_data()

    result = pipeline.process(
        test_data
    )

    ignition_detected = (
        result.event_set is not None
        and result.event_set.ignition is not None
    )

    burnout_detected = (
        result.event_set is not None
        and result.event_set.burnout is not None
    )

    peak_detected = (
        result.event_set is not None
        and result.event_set.peak_thrust is not None
    )

    print(
        f"Ignition detected:    "
        f"{'YES' if ignition_detected else 'NO'}"
    )

    print(
        f"Burnout detected:     "
        f"{'YES' if burnout_detected else 'NO'}"
    )

    print(
        f"Peak detected:        "
        f"{'YES' if peak_detected else 'NO'}"
    )

    assert ignition_detected
    assert burnout_detected
    assert peak_detected

    print("Event detection:      PASSED")


def test_alignment_disabled(pipeline):
    print_header("Alignment disabled")

    test_data = make_alignment_test_data()

    settings = ProcessingSettings()

    settings.alignment.enabled = False

    result = pipeline.process(
        test_data,
        settings,
    )

    print(
        f"Alignment enabled:    NO"
    )

    print(
        f"Reference time:       "
        f"{result.alignment_result.reference_time_s:.3f} s"
    )

    print(
        f"Time changed:         "
        f"{'YES' if result.alignment_result.offset_s != 0.0 else 'NO'}"
    )

    assert result.valid

    assert np.isclose(
        result.alignment_result.offset_s,
        0.0,
    )

    assert np.array_equal(
        result.prepared_data.time_s,
        test_data.time_s,
    )

    print("Alignment disabled:   PASSED")


def test_ignition_alignment(pipeline):
    print_header("Ignition alignment")

    test_data = make_alignment_test_data()

    settings = ProcessingSettings()

    settings.alignment.enabled = True
    settings.alignment.reference_event = EventType.IGNITION

    result = pipeline.process(
        test_data,
        settings,
    )

    ignition = result.event_set.ignition

    assert ignition is not None
    assert ignition.sample_index is not None

    print(
        f"Detected ignition:   "
        f"{ignition.time_s:.3f} s"
    )

    print(
        f"Reference time:       "
        f"{result.alignment_result.reference_time_s:.3f} s"
    )

    print(
        f"Aligned ignition:     "
        f"{result.prepared_data.time_s[ignition.sample_index]:.3f} s"
    )

    print(
        f"Alignment offset:     "
        f"{result.alignment_result.offset_s:.3f} s"
    )

    assert np.isclose(
        result.prepared_data.time_s[
            ignition.sample_index
        ],
        0.0,
    )

    assert np.isclose(
        result.alignment_result.offset_s,
        -ignition.time_s,
    )

    print("Ignition alignment:   PASSED")


def test_burnout_alignment(pipeline):
    print_header("Burnout alignment")

    test_data = make_alignment_test_data()

    settings = ProcessingSettings()

    settings.alignment.enabled = True
    settings.alignment.reference_event = EventType.BURNOUT

    result = pipeline.process(
        test_data,
        settings,
    )

    burnout = result.event_set.burnout

    assert burnout is not None
    assert burnout.sample_index is not None

    print(
        f"Detected burnout:     "
        f"{burnout.time_s:.3f} s"
    )

    print(
        f"Reference time:       "
        f"{result.alignment_result.reference_time_s:.3f} s"
    )

    print(
        f"Aligned burnout:      "
        f"{result.prepared_data.time_s[burnout.sample_index]:.3f} s"
    )

    assert np.isclose(
        result.prepared_data.time_s[
            burnout.sample_index
        ],
        0.0,
    )

    print("Burnout alignment:    PASSED")


def test_manual_alignment(pipeline):
    print_header("Manual alignment")

    test_data = make_alignment_test_data()

    settings = ProcessingSettings()

    settings.alignment.enabled = True
    settings.alignment.manual_reference_time_s = 0.4

    result = pipeline.process(
        test_data,
        settings,
    )

    print(
        f"Manual reference:     "
        f"{settings.alignment.manual_reference_time_s:.3f} s"
    )

    print(
        f"Aligned time[4]:      "
        f"{result.prepared_data.time_s[4]:.3f} s"
    )

    assert np.isclose(
        result.prepared_data.time_s[4],
        0.0,
    )

    assert np.isclose(
        result.alignment_result.offset_s,
        -0.4,
    )

    print("Manual alignment:     PASSED")


def test_combined_processing(pipeline):
    print_header("Trim + baseline + alignment")

    test_data = make_alignment_test_data()

    original_time = test_data.time_s.copy()
    original_thrust = test_data.thrust_N.copy()

    settings = ProcessingSettings()

    settings.cleaning.start_time_s = 0.2
    settings.cleaning.end_time_s = 0.9

    settings.baseline.baseline_start_time_s = 0.2
    settings.baseline.baseline_end_time_s = 0.2

    settings.alignment.enabled = True
    settings.alignment.reference_event = EventType.IGNITION

    result = pipeline.process(
        test_data,
        settings,
    )

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

    assert result.valid

    assert result.prepared_data.sample_count == 8

    assert np.isclose(
        result.baseline_result.baseline_N,
        0.0,
    )

    assert np.isclose(
        result.prepared_data.time_s[
            ignition.sample_index
        ],
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


def test_real_zerox_sample(pipeline):
    print_header("Real Zerox Format 1.0 sample")

    filename = os.path.join(
        "test_data",
        "Zerox.csv",
    )

    reader = RMCSCSVReader()

    real_data = reader.read(filename)

    settings = ProcessingSettings()

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
        f"Original time:        "
        f"{real_data.time_s[0]:.3f} → "
        f"{real_data.time_s[-1]:.3f} s"
    )

    print(
        f"Calibrated time:      "
        f"{real_data.calibrated_time_s[0]:.3f} → "
        f"{real_data.calibrated_time_s[-1]:.3f} s"
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
        f"Peak thrust:          "
        f"{peak.value:.3f} N"
    )

    print(
        f"Baseline:             "
        f"{result.baseline_result.baseline_N:.3f} N"
    )

    print(
        f"Aligned ignition:     "
        f"{result.prepared_data.time_s[ignition.sample_index]:.3f} s"
    )

    assert real_data.sample_count == 661

    assert np.isclose(
        real_data.calibrated_time_s[0],
        0.0,
    )

    assert np.isclose(
        real_data.calibrated_time_s[-1],
        8.538,
    )

    assert np.isclose(
        real_data.maximum_thrust_N,
        3230.339730,
    )

    assert np.isclose(
        result.baseline_result.baseline_N,
        53.3190315,
    )

    assert np.isclose(
        ignition.time_s,
        0.034,
    )

    assert np.isclose(
        peak.time_s,
        0.134,
    )

    assert np.isclose(
        peak.value,
        3177.0206985,
    )

    assert np.isclose(
        result.prepared_data.time_s[
            ignition.sample_index
        ],
        0.0,
    )

    print("Real Zerox sample:    PASSED")


def main():
    print("RMCS Analyzer Processing Pipeline Tests")
    print("=" * 70)

    pipeline = ProcessingPipeline()

    test_default_processing(pipeline)
    test_trim_and_baseline(pipeline)
    test_baseline_only(pipeline)
    test_raw_data_protection(pipeline)
    test_calibrated_time(pipeline)
    test_calibrated_time_fallback(pipeline)
    test_invalid_raw_data(pipeline)
    test_prepared_validation(pipeline)
    test_event_detection(pipeline)
    test_alignment_disabled(pipeline)
    test_ignition_alignment(pipeline)
    test_burnout_alignment(pipeline)
    test_manual_alignment(pipeline)
    test_combined_processing(pipeline)
    test_real_zerox_sample(pipeline)

    print()
    print("=" * 70)
    print("ALL PROCESSING PIPELINE TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()