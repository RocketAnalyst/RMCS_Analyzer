from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from ..data.models import TestData


@dataclass
class ValidationIssue:
    """Describes a single data-quality issue."""

    severity: str
    code: str
    message: str


@dataclass
class DataValidationReport:
    """Complete validation report for a TestData object."""

    valid: bool = True
    sample_count: int = 0
    sample_rate_hz: Optional[float] = None

    time_valid: bool = False
    thrust_valid: bool = False
    time_monotonic: bool = False
    duplicate_timestamps: int = 0

    missing_time_values: int = 0
    missing_thrust_values: int = 0
    infinite_time_values: int = 0
    infinite_thrust_values: int = 0

    sampling_gap_count: int = 0
    largest_sampling_gap_s: Optional[float] = None

    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    @property
    def status(self) -> str:
        if self.has_errors:
            return "INVALID"
        if self.has_warnings:
            return "VALID WITH WARNINGS"
        return "VALID"


class DataValidator:
    """
    Validate normalized TestData without modifying it.

    This layer checks structural and numerical suitability for
    downstream processing. It does not clean, filter, baseline
    correct, align, or analyze motor performance.
    """

    DEFAULT_GAP_MULTIPLIER = 3.0
    MIN_GAP_SECONDS = 0.001

    @classmethod
    def validate(
        cls,
        test_data: TestData,
        gap_multiplier: float = DEFAULT_GAP_MULTIPLIER,
    ) -> DataValidationReport:
        report = DataValidationReport()

        if test_data is None:
            cls._add_error(report, "NO_DATA", "No test data was provided.")
            report.valid = False
            return report

        time_s = np.asarray(test_data.time_s)
        thrust_N = np.asarray(test_data.thrust_N)

        report.sample_count = len(time_s)

        if report.sample_count == 0:
            cls._add_error(
                report,
                "EMPTY_DATASET",
                "The dataset contains no samples.",
            )
            report.valid = False
            return report

        if len(time_s) != len(thrust_N):
            cls._add_error(
                report,
                "ARRAY_LENGTH_MISMATCH",
                "Time and thrust channels contain different numbers of samples.",
            )
            report.valid = False
            return report

        if report.sample_count < 2:
            cls._add_error(
                report,
                "INSUFFICIENT_SAMPLES",
                "At least two samples are required for time-series analysis.",
            )
            report.valid = False
            return report

        cls._validate_time(time_s, report)
        cls._validate_thrust(thrust_N, report)

        # Current TestData optional channels.
        optional_channels = {
            "calibrated_time_s": test_data.calibrated_time_s,
            "raw_thrust_N": test_data.raw_thrust_N,
            "prop_loss_kg": test_data.prop_loss_kg,
            "pressure_psi": test_data.pressure_psi,
            "delta": test_data.delta,
            "state": test_data.state,
        }

        for channel_name, channel in optional_channels.items():
            cls._validate_optional_channel(
                channel_name,
                channel,
                report.sample_count,
                report,
            )

        if report.time_valid:
            cls._analyze_sampling(time_s, report, gap_multiplier)

        report.valid = not report.has_errors
        return report

    @staticmethod
    def _validate_time(time_s: np.ndarray, report: DataValidationReport):
        try:
            numeric_time = time_s.astype(float)
        except (TypeError, ValueError):
            DataValidator._add_error(
                report,
                "TIME_NOT_NUMERIC",
                "The time channel contains non-numeric values.",
            )
            return

        try:
            finite_mask = np.isfinite(numeric_time)
        except TypeError:
            DataValidator._add_error(
                report,
                "TIME_NOT_NUMERIC",
                "The time channel contains non-numeric values.",
            )
            return

        missing_count = int(np.count_nonzero(np.isnan(numeric_time)))
        infinite_count = int(np.count_nonzero(np.isinf(numeric_time)))

        report.missing_time_values = missing_count
        report.infinite_time_values = infinite_count

        if missing_count:
            DataValidator._add_error(
                report,
                "TIME_MISSING_VALUES",
                f"The time channel contains {missing_count} missing value(s).",
            )

        if infinite_count:
            DataValidator._add_error(
                report,
                "TIME_INFINITE_VALUES",
                f"The time channel contains {infinite_count} infinite value(s).",
            )

        if not np.all(finite_mask):
            return

        differences = np.diff(numeric_time)

        report.time_monotonic = bool(np.all(differences > 0))

        duplicate_count = int(np.count_nonzero(differences == 0))
        report.duplicate_timestamps = duplicate_count

        if duplicate_count:
            DataValidator._add_error(
                report,
                "DUPLICATE_TIMESTAMPS",
                f"The time channel contains {duplicate_count} duplicate timestamp(s).",
            )

        if not report.time_monotonic:
            DataValidator._add_error(
                report,
                "TIME_NOT_MONOTONIC",
                "Time values must increase strictly from one sample to the next.",
            )

        report.time_valid = (
            report.missing_time_values == 0
            and report.infinite_time_values == 0
            and report.duplicate_timestamps == 0
            and report.time_monotonic
        )

    @staticmethod
    def _validate_thrust(thrust_N: np.ndarray, report: DataValidationReport):
        try:
            numeric_thrust = thrust_N.astype(float)
        except (TypeError, ValueError):
            DataValidator._add_error(
                report,
                "THRUST_NOT_NUMERIC",
                "The thrust channel contains non-numeric values.",
            )
            return

        missing_count = int(np.count_nonzero(np.isnan(numeric_thrust)))
        infinite_count = int(np.count_nonzero(np.isinf(numeric_thrust)))

        report.missing_thrust_values = missing_count
        report.infinite_thrust_values = infinite_count

        if missing_count:
            DataValidator._add_error(
                report,
                "THRUST_MISSING_VALUES",
                f"The thrust channel contains {missing_count} missing value(s).",
            )

        if infinite_count:
            DataValidator._add_error(
                report,
                "THRUST_INFINITE_VALUES",
                f"The thrust channel contains {infinite_count} infinite value(s).",
            )

        report.thrust_valid = (
            missing_count == 0
            and infinite_count == 0
        )

    @staticmethod
    def _validate_optional_channel(
        channel_name: str,
        channel,
        expected_length: int,
        report: DataValidationReport,
    ):
        if channel is None:
            return

        try:
            actual_length = len(channel)
        except TypeError:
            DataValidator._add_error(
                report,
                "OPTIONAL_CHANNEL_INVALID",
                (
                    f"The optional channel '{channel_name}' "
                    "is not a valid time-series array."
                ),
            )
            return

        if actual_length != expected_length:
            DataValidator._add_error(
                report,
                "OPTIONAL_CHANNEL_LENGTH_MISMATCH",
                (
                    f"The optional channel '{channel_name}' contains "
                    f"{actual_length} samples, but the test contains "
                    f"{expected_length}."
                ),
            )

    @classmethod
    def _analyze_sampling(
        cls,
        time_s: np.ndarray,
        report: DataValidationReport,
        gap_multiplier: float,
    ):
        differences = np.diff(time_s)

        if len(differences) == 0:
            return

        median_interval = float(np.median(differences))

        if median_interval <= 0:
            return

        report.sample_rate_hz = 1.0 / median_interval

        gap_threshold = max(
            median_interval * gap_multiplier,
            median_interval + cls.MIN_GAP_SECONDS,
        )

        gap_mask = differences > gap_threshold
        gap_indices = np.flatnonzero(gap_mask)

        report.sampling_gap_count = len(gap_indices)
        report.largest_sampling_gap_s = float(np.max(differences))

        if report.sampling_gap_count:
            cls._add_warning(
                report,
                "SAMPLING_GAPS",
                (
                    f"{report.sampling_gap_count} unusually large "
                    "sampling gap(s) were detected."
                ),
            )

    @staticmethod
    def _add_error(report: DataValidationReport, code: str, message: str):
        report.issues.append(
            ValidationIssue(
                severity="error",
                code=code,
                message=message,
            )
        )

    @staticmethod
    def _add_warning(report: DataValidationReport, code: str, message: str):
        report.issues.append(
            ValidationIssue(
                severity="warning",
                code=code,
                message=message,
            )
        )
