from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from ..data.models import TestData


# =============================================================
# VALIDATION ISSUE
# =============================================================


@dataclass
class ValidationIssue:
    """
    Describes a single data-quality issue.

    severity:
        "error" prevents the dataset from being considered valid.

        "warning" allows the dataset to proceed, but alerts
        the user to a potential data-quality concern.
    """

    severity: str
    code: str
    message: str


# =============================================================
# VALIDATION REPORT
# =============================================================


@dataclass
class DataValidationReport:
    """
    Complete validation report for a TestData object.

    This class contains no UI logic and does not modify the
    underlying test data.
    """

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

    issues: List[ValidationIssue] = field(
        default_factory=list
    )

    @property
    def errors(self) -> List[ValidationIssue]:
        """Return all validation errors."""

        return [
            issue
            for issue in self.issues
            if issue.severity == "error"
        ]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Return all validation warnings."""

        return [
            issue
            for issue in self.issues
            if issue.severity == "warning"
        ]

    @property
    def has_errors(self) -> bool:
        """Return True when at least one error exists."""

        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Return True when at least one warning exists."""

        return len(self.warnings) > 0

    @property
    def status(self) -> str:
        """
        Return a human-readable overall validation status.

        Possible values:

            VALID
            VALID WITH WARNINGS
            INVALID
        """

        if self.has_errors:
            return "INVALID"

        if self.has_warnings:
            return "VALID WITH WARNINGS"

        return "VALID"


# =============================================================
# DATA VALIDATOR
# =============================================================


class DataValidator:
    """
    Validates time-series test data.

    This validator operates on normalized TestData objects.

    It does not:
        - modify data
        - trim data
        - filter data
        - correct data
        - change units
        - alter metadata
        - perform analysis

    Its sole responsibility is to determine whether the
    time-series data is structurally and numerically suitable
    for further processing.
    """

    # ---------------------------------------------------------
    # Sampling configuration
    # ---------------------------------------------------------

    # A gap is considered unusual when it is at least this many
    # times larger than the normal sample interval.
    DEFAULT_GAP_MULTIPLIER = 3.0

    # Never report extremely small floating-point differences
    # as sampling gaps.
    MIN_GAP_SECONDS = 0.001

    # ---------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------

    @classmethod
    def validate(
        cls,
        test_data: TestData,
        gap_multiplier: float = DEFAULT_GAP_MULTIPLIER,
    ) -> DataValidationReport:
        """
        Validate a TestData object.

        Parameters
        ----------
        test_data:
            Normalized RMCS Analyzer test data.

        gap_multiplier:
            A sampling interval larger than the median interval
            multiplied by this value is reported as a warning.

        Returns
        -------
        DataValidationReport
            Structured validation results.

        Notes
        -----
        This method never modifies test_data.

        The primary Time(s) and Thrust (N) channels are required.

        Optional channels are validated when present:
            - Time Cal (s)
            - Raw Thrust (N)
            - Prop Loss (kg)
            - Pressure (psi)
            - Delta
            - State
        """

        report = DataValidationReport()

        if test_data is None:

            cls._add_error(
                report,
                "NO_DATA",
                "No test data was provided.",
            )

            report.valid = False

            return report

        time_s = np.asarray(
            test_data.time_s
        )

        thrust_N = np.asarray(
            test_data.thrust_N
        )

        report.sample_count = len(
            time_s
        )

        # -----------------------------------------------------
        # Basic dataset checks
        # -----------------------------------------------------

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
                (
                    "Time and thrust channels contain "
                    "different numbers of samples."
                ),
            )

            report.valid = False

            # We cannot safely perform sample-by-sample
            # validation when the arrays do not match.
            return report

        if report.sample_count < 2:

            cls._add_error(
                report,
                "INSUFFICIENT_SAMPLES",
                (
                    "At least two samples are required "
                    "for time-series analysis."
                ),
            )

            report.valid = False

            return report

        # -----------------------------------------------------
        # Validate primary time channel
        # -----------------------------------------------------

        cls._validate_time(
            time_s,
            report,
        )

        # -----------------------------------------------------
        # Validate primary thrust channel
        # -----------------------------------------------------

        cls._validate_thrust(
            thrust_N,
            report,
        )

        # -----------------------------------------------------
        # Validate optional channels
        # -----------------------------------------------------

        cls._validate_optional_channel(
            "calibrated_time_s",
            test_data.calibrated_time_s,
            report.sample_count,
            report,
        )

        cls._validate_optional_channel(
            "raw_thrust_N",
            test_data.raw_thrust_N,
            report.sample_count,
            report,
        )

        cls._validate_optional_channel(
            "prop_loss_kg",
            test_data.prop_loss_kg,
            report.sample_count,
            report,
        )

        cls._validate_optional_channel(
            "pressure_psi",
            test_data.pressure_psi,
            report.sample_count,
            report,
        )

        cls._validate_optional_channel(
            "delta",
            test_data.delta,
            report.sample_count,
            report,
        )

        cls._validate_optional_channel(
            "state",
            test_data.state,
            report.sample_count,
            report,
        )

        # -----------------------------------------------------
        # Sampling analysis
        # -----------------------------------------------------

        if report.time_valid:

            cls._analyze_sampling(
                time_s,
                report,
                gap_multiplier,
            )

        report.valid = not report.has_errors

        return report

    # =========================================================
    # TIME VALIDATION
    # =========================================================

    @staticmethod
    def _validate_time(
        time_s: np.ndarray,
        report: DataValidationReport,
    ):
        """Validate the primary Time(s) channel."""

        # -----------------------------------------------------
        # Numeric conversion
        # -----------------------------------------------------

        if not np.issubdtype(
            time_s.dtype,
            np.number,
        ):

            try:

                time_s = time_s.astype(
                    float
                )

            except (
                TypeError,
                ValueError,
            ):

                DataValidator._add_error(
                    report,
                    "TIME_NOT_NUMERIC",
                    "The time channel contains non-numeric values.",
                )

                return

        # -----------------------------------------------------
        # Missing values
        # -----------------------------------------------------

        try:

            finite_mask = np.isfinite(
                time_s
            )

        except TypeError:

            DataValidator._add_error(
                report,
                "TIME_NOT_NUMERIC",
                "The time channel contains non-numeric values.",
            )

            return

        missing_count = int(
            np.count_nonzero(
                np.isnan(time_s)
            )
        )

        infinite_count = int(
            np.count_nonzero(
                np.isinf(time_s)
            )
        )

        report.missing_time_values = (
            missing_count
        )

        report.infinite_time_values = (
            infinite_count
        )

        if missing_count > 0:

            DataValidator._add_error(
                report,
                "TIME_MISSING_VALUES",
                (
                    f"The time channel contains "
                    f"{missing_count} missing value(s)."
                ),
            )

        if infinite_count > 0:

            DataValidator._add_error(
                report,
                "TIME_INFINITE_VALUES",
                (
                    f"The time channel contains "
                    f"{infinite_count} infinite value(s)."
                ),
            )

        if not np.all(
            finite_mask
        ):

            return

        # -----------------------------------------------------
        # Monotonicity
        # -----------------------------------------------------

        differences = np.diff(
            time_s
        )

        report.time_monotonic = bool(
            np.all(
                differences > 0
            )
        )

        duplicate_count = int(
            np.count_nonzero(
                differences == 0
            )
        )

        report.duplicate_timestamps = (
            duplicate_count
        )

        if duplicate_count > 0:

            DataValidator._add_error(
                report,
                "DUPLICATE_TIMESTAMPS",
                (
                    f"The time channel contains "
                    f"{duplicate_count} duplicate timestamp(s)."
                ),
            )

        if not report.time_monotonic:

            DataValidator._add_error(
                report,
                "TIME_NOT_MONOTONIC",
                (
                    "Time values must increase "
                    "strictly from one sample to the next."
                ),
            )

        report.time_valid = (
            report.missing_time_values == 0
            and report.infinite_time_values == 0
            and report.duplicate_timestamps == 0
            and report.time_monotonic
        )

    # =========================================================
    # THRUST VALIDATION
    # =========================================================

    @staticmethod
    def _validate_thrust(
        thrust_N: np.ndarray,
        report: DataValidationReport,
    ):
        """Validate the authoritative Thrust (N) channel."""

        try:

            numeric_thrust = thrust_N.astype(
                float
            )

        except (
            TypeError,
            ValueError,
        ):

            DataValidator._add_error(
                report,
                "THRUST_NOT_NUMERIC",
                (
                    "The thrust channel contains "
                    "non-numeric values."
                ),
            )

            return

        missing_count = int(
            np.count_nonzero(
                np.isnan(
                    numeric_thrust
                )
            )
        )

        infinite_count = int(
            np.count_nonzero(
                np.isinf(
                    numeric_thrust
                )
            )
        )

        report.missing_thrust_values = (
            missing_count
        )

        report.infinite_thrust_values = (
            infinite_count
        )

        if missing_count > 0:

            DataValidator._add_error(
                report,
                "THRUST_MISSING_VALUES",
                (
                    f"The thrust channel contains "
                    f"{missing_count} missing value(s)."
                ),
            )

        if infinite_count > 0:

            DataValidator._add_error(
                report,
                "THRUST_INFINITE_VALUES",
                (
                    f"The thrust channel contains "
                    f"{infinite_count} infinite value(s)."
                ),
            )

        report.thrust_valid = (
            missing_count == 0
            and infinite_count == 0
        )

    # =========================================================
    # OPTIONAL CHANNEL VALIDATION
    # =========================================================

    @staticmethod
    def _validate_optional_channel(
        channel_name: str,
        channel,
        expected_length: int,
        report: DataValidationReport,
    ):
        """
        Validate an optional channel.

        Missing optional channels are valid.

        If a channel exists, however, it must contain the same
        number of samples as the primary time-series channels.
        """

        if channel is None:
            return

        try:

            actual_length = len(
                channel
            )

        except TypeError:

            DataValidator._add_error(
                report,
                "OPTIONAL_CHANNEL_INVALID",
                (
                    f"The optional channel "
                    f"'{channel_name}' is not a valid "
                    f"time-series array."
                ),
            )

            return

        if actual_length != expected_length:

            DataValidator._add_error(
                report,
                "OPTIONAL_CHANNEL_LENGTH_MISMATCH",
                (
                    f"The optional channel "
                    f"'{channel_name}' contains "
                    f"{actual_length} samples, but the "
                    f"test contains {expected_length}."
                ),
            )

    # =========================================================
    # SAMPLING ANALYSIS
    # =========================================================

    @classmethod
    def _analyze_sampling(
        cls,
        time_s: np.ndarray,
        report: DataValidationReport,
        gap_multiplier: float,
    ):
        """Analyze sample rate and identify unusually large gaps."""

        differences = np.diff(
            time_s
        )

        if len(differences) == 0:
            return

        median_interval = float(
            np.median(
                differences
            )
        )

        if median_interval <= 0:
            return

        report.sample_rate_hz = (
            1.0 / median_interval
        )

        gap_threshold = max(
            median_interval * gap_multiplier,
            median_interval + cls.MIN_GAP_SECONDS,
        )

        gap_mask = (
            differences > gap_threshold
        )

        gap_indices = np.flatnonzero(
            gap_mask
        )

        report.sampling_gap_count = (
            len(gap_indices)
        )

        if len(differences) > 0:

            report.largest_sampling_gap_s = (
                float(
                    np.max(
                        differences
                    )
                )
            )

        if report.sampling_gap_count > 0:

            DataValidator._add_warning(
                report,
                "SAMPLING_GAPS",
                (
                    f"{report.sampling_gap_count} "
                    f"unusually large sampling gap(s) "
                    f"were detected."
                ),
            )

    # =========================================================
    # ISSUE HELPERS
    # =========================================================

    @staticmethod
    def _add_error(
        report: DataValidationReport,
        code: str,
        message: str,
    ):
        """Add an error to a validation report."""

        report.issues.append(
            ValidationIssue(
                severity="error",
                code=code,
                message=message,
            )
        )

    @staticmethod
    def _add_warning(
        report: DataValidationReport,
        code: str,
        message: str,
    ):
        """Add a warning to a validation report."""

        report.issues.append(
            ValidationIssue(
                severity="warning",
                code=code,
                message=message,
            )
        )