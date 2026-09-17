from dataclasses import dataclass, field

import numpy as np

from ..analysis.events import EventDetector
from ..data.models import TestData
from .alignment import AlignmentResult, TimeAligner
from .baseline import BaselineCorrector, BaselineResult
from .cleaning import CleaningResult, DataCleaner
from .event_model import EventSet
from .settings import ProcessingSettings
from .validation import DataValidationReport, DataValidator


@dataclass
class ProcessingResult:
    """
    Complete result of the data-processing pipeline.

    The pipeline preserves the original imported data and produces
    a separate prepared dataset for analysis.
    """

    raw_data: TestData
    prepared_data: TestData

    raw_validation: DataValidationReport
    prepared_validation: DataValidationReport

    cleaning_result: CleaningResult | None = None
    baseline_result: BaselineResult | None = None
    event_set: EventSet | None = None
    alignment_result: AlignmentResult | None = None

    issues: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        """Return True when both raw and prepared data are valid."""

        return (
            self.raw_validation.valid
            and self.prepared_validation.valid
        )

    @property
    def modified(self) -> bool:
        """
        Return True when processing changed the prepared dataset.

        Trimming, baseline correction, or time alignment all count
        as processing modifications.
        """

        if self.cleaning_result is not None:
            if (
                self.cleaning_result.prepared_sample_count
                != self.cleaning_result.original_sample_count
            ):
                return True

        if self.baseline_result is not None:
            if self.baseline_result.baseline_N != 0.0:
                return True

        if self.alignment_result is not None:
            if self.alignment_result.offset_s != 0.0:
                return True

        return False


class ProcessingPipeline:
    """
    Unified processing pipeline.

    Processing order:

        Raw
          ↓
        Validate
          ↓
        Select Analysis Timeline
          ↓
        Clean / Trim
          ↓
        Baseline Correction
          ↓
        Detect Events
          ↓
        Align Time
          ↓
        Validate Prepared Data

    When a valid Time Cal (s) source column is available, it is used
    as the working analysis timeline before any time-based processing.

    When Time Cal (s) is unavailable or contains no usable values,
    the original Time(s) timeline is used instead.

    The original imported TestData is never modified.
    """

    def __init__(
        self,
        validator: DataValidator | None = None,
        cleaner: DataCleaner | None = None,
        baseline_corrector: BaselineCorrector | None = None,
        event_detector: EventDetector | None = None,
        time_aligner: TimeAligner | None = None,
    ):
        self.validator = validator or DataValidator()
        self.cleaner = cleaner or DataCleaner()
        self.baseline_corrector = (
            baseline_corrector or BaselineCorrector()
        )
        self.event_detector = event_detector or EventDetector()
        self.time_aligner = time_aligner or TimeAligner()

    def process(
        self,
        test_data: TestData,
        settings: ProcessingSettings | None = None,
    ) -> ProcessingResult:
        """
        Process test data according to the supplied settings.

        Raw imported data is never modified.

        If the imported file contains a valid Time Cal (s) column,
        that timeline becomes the working analysis timeline before
        cleaning and baseline correction.

        The original Time(s) remains preserved in raw_data.
        """

        if settings is None:
            settings = ProcessingSettings()

        # ---------------------------------------------------------
        # 1. Validate raw data
        # ---------------------------------------------------------

        raw_validation = self.validator.validate(
            test_data
        )

        if not raw_validation.valid:
            error_messages = [
                issue.message
                for issue in raw_validation.issues
                if issue.severity == "ERROR"
            ]

            detail = "\n".join(
                f"- {message}" for message in error_messages
            )

            if not detail:
                detail = "- Unknown validation error."

            raise ValueError(
                "Raw test data failed validation:\n"
                + detail
            )

        # ---------------------------------------------------------
        # 2. Select analysis timeline
        # ---------------------------------------------------------
        #
        # This MUST happen before cleaning and baseline correction.
        #
        # Time Cal (s), when valid, becomes the working time axis.
        #
        # The original imported Time(s) remains untouched inside
        # test_data and is returned as ProcessingResult.raw_data.
        #

        working_data = self._apply_calibrated_time(
            test_data
        )

        # ---------------------------------------------------------
        # 3. Clean / trim
        # ---------------------------------------------------------

        cleaning_result = self.cleaner.prepare(
            working_data,
            settings.cleaning,
        )

        prepared_data = cleaning_result.data

        # ---------------------------------------------------------
        # 4. Baseline correction
        # ---------------------------------------------------------

        baseline_result = self.baseline_corrector.correct(
            prepared_data,
            settings.baseline,
        )

        prepared_data = baseline_result.data

        # ---------------------------------------------------------
        # 5. Detect events
        # ---------------------------------------------------------

        event_set = self.event_detector.detect_events(
            prepared_data
        )

        # ---------------------------------------------------------
        # 6. Align time
        # ---------------------------------------------------------

        alignment_result = self.time_aligner.align(
            prepared_data,
            settings.alignment,
            event_set,
        )

        prepared_data = alignment_result.data

        # ---------------------------------------------------------
        # 7. Validate prepared data
        # ---------------------------------------------------------

        prepared_validation = self.validator.validate(
            prepared_data
        )

        issues = [
            issue.message
            for issue in prepared_validation.issues
        ]

        return ProcessingResult(
            raw_data=test_data,
            prepared_data=prepared_data,
            raw_validation=raw_validation,
            prepared_validation=prepared_validation,
            cleaning_result=cleaning_result,
            baseline_result=baseline_result,
            event_set=event_set,
            alignment_result=alignment_result,
            issues=issues,
        )

    @staticmethod
    def _apply_calibrated_time(
        test_data: TestData,
    ) -> TestData:
        """
        Use the source-provided calibrated time as the working
        analysis timeline when usable data is available.

        The original TestData object is never modified.

        If calibrated_time_s is:

            - missing
            - empty
            - the wrong length
            - entirely non-finite
            - contains any non-finite values

        the original Time(s) timeline is retained.

        The calibrated timeline is preserved in calibrated_time_s
        for traceability.
        """

        calibrated_time = test_data.calibrated_time_s

        if calibrated_time is None:
            return test_data

        calibrated_time = np.asarray(
            calibrated_time,
            dtype=float,
        )

        if calibrated_time.size == 0:
            return test_data

        if calibrated_time.shape != test_data.time_s.shape:
            return test_data

        if not np.any(np.isfinite(calibrated_time)):
            return test_data

        if not np.all(np.isfinite(calibrated_time)):
            return test_data

        return TestData(
            time_s=calibrated_time.copy(),

            thrust_N=test_data.thrust_N.copy(),

            calibrated_time_s=calibrated_time.copy(),

            raw_thrust_N=(
                None
                if test_data.raw_thrust_N is None
                else test_data.raw_thrust_N.copy()
            ),

            prop_loss_kg=(
                None
                if test_data.prop_loss_kg is None
                else test_data.prop_loss_kg.copy()
            ),

            pressure_psi=(
                None
                if test_data.pressure_psi is None
                else test_data.pressure_psi.copy()
            ),

            delta=(
                None
                if test_data.delta is None
                else test_data.delta.copy()
            ),

            state=(
                None
                if test_data.state is None
                else test_data.state.copy()
            ),

            metadata=test_data.metadata,
        )