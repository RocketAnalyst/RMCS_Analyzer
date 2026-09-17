from dataclasses import dataclass, field

from ..data.models import TestData
from .baseline import BaselineCorrector, BaselineResult
from .cleaning import CleaningResult, DataCleaner
from .settings import ProcessingSettings
from .validation import DataValidationReport, DataValidator


@dataclass
class ProcessingResult:
    """
    Complete result of processing a test dataset.

    The original raw TestData is never modified.
    """

    raw_data: TestData
    prepared_data: TestData

    raw_validation: DataValidationReport
    prepared_validation: DataValidationReport

    cleaning_result: CleaningResult | None = None
    baseline_result: BaselineResult | None = None

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

        Trimming counts as a modification when the sample count
        changes. Baseline correction counts as a modification when
        the calculated baseline is non-zero.
        """
        if self.cleaning_result is not None:
            if (
                self.raw_data.sample_count
                != self.prepared_data.sample_count
            ):
                return True

        if self.baseline_result is not None:
            if self.baseline_result.baseline_N != 0.0:
                return True

        return False


class ProcessingPipeline:
    """
    Coordinates validation and non-destructive data preparation.

    Processing flow:

        Raw TestData
            ↓
        Validate raw data
            ↓
        Trim / clean
            ↓
        Baseline correction
            ↓
        Validate prepared data
            ↓
        Prepared TestData
    """

    def __init__(
        self,
        validator: DataValidator | None = None,
        cleaner: DataCleaner | None = None,
        baseline_corrector: BaselineCorrector | None = None,
    ):
        self.validator = validator or DataValidator()
        self.cleaner = cleaner or DataCleaner()
        self.baseline_corrector = (
            baseline_corrector
            or BaselineCorrector()
        )

    def process(
        self,
        test_data: TestData,
        settings: ProcessingSettings | None = None,
    ) -> ProcessingResult:
        """
        Validate and prepare a TestData object.

        Processing is performed on copies of the raw data.
        The original test_data is never modified.

        If settings is omitted, default ProcessingSettings are used.

        Raises:
            ValueError: If raw data fails validation.
        """

        # ---------------------------------------------------------
        # 1. Use default settings when none are supplied
        # ---------------------------------------------------------
        if settings is None:
            settings = ProcessingSettings()

        # ---------------------------------------------------------
        # 2. Validate raw data
        # ---------------------------------------------------------
        raw_validation = self.validator.validate(test_data)

        if not raw_validation.valid:
            messages = [
                issue.message
                for issue in raw_validation.issues
                if issue.severity == "ERROR"
            ]

            raise ValueError(
                "Raw test data failed validation:\n"
                + "\n".join(
                    f"- {message}"
                    for message in messages
                )
            )

        # ---------------------------------------------------------
        # 3. Apply trimming / cleaning
        # ---------------------------------------------------------
        cleaning_result = self.cleaner.prepare(
            test_data,
            settings.cleaning,
        )

        prepared_data = cleaning_result.data

        # ---------------------------------------------------------
        # 4. Apply baseline correction
        # ---------------------------------------------------------
        baseline_result = self.baseline_corrector.correct(
            prepared_data,
            settings.baseline,
        )

        prepared_data = baseline_result.data

        # ---------------------------------------------------------
        # 5. Validate prepared data
        # ---------------------------------------------------------
        prepared_validation = self.validator.validate(
            prepared_data
        )

        issues = [
            issue.message
            for issue in prepared_validation.issues
        ]

        # ---------------------------------------------------------
        # 6. Return complete processing result
        # ---------------------------------------------------------
        return ProcessingResult(
            raw_data=test_data,
            prepared_data=prepared_data,
            raw_validation=raw_validation,
            prepared_validation=prepared_validation,
            cleaning_result=cleaning_result,
            baseline_result=baseline_result,
            issues=issues,
        )