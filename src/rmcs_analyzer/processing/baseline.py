from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..data.models import TestData


@dataclass
class BaselineSettings:
    """
    Settings used for thrust baseline correction.

    baseline_start_time_s and baseline_end_time_s define the
    time window used to calculate the baseline.

    If neither value is supplied, the entire dataset is used.
    """

    baseline_start_time_s: Optional[float] = None
    baseline_end_time_s: Optional[float] = None

    def reset(self):
        """Reset baseline settings."""
        self.baseline_start_time_s = None
        self.baseline_end_time_s = None


@dataclass
class BaselineResult:
    """Result of applying baseline correction."""

    data: TestData

    baseline_N: float

    baseline_start_index: int
    baseline_end_index: int

    sample_count: int


class BaselineCorrector:
    """
    Performs non-destructive thrust baseline correction.

    The original TestData is never modified.

    Baseline correction subtracts a calculated resting thrust
    value from the thrust channel:

        corrected_thrust = original_thrust - baseline
    """

    @classmethod
    def correct(
        cls,
        test_data: TestData,
        settings: BaselineSettings | None = None,
    ) -> BaselineResult:
        """
        Apply baseline correction to TestData.

        Raises:
            ValueError: If the dataset is empty or the baseline
                        time range is invalid.
        """

        if test_data.sample_count == 0:
            raise ValueError(
                "Cannot perform baseline correction on empty data."
            )

        if settings is None:
            settings = BaselineSettings()

        time = test_data.time_s
        thrust = test_data.thrust_N

        # ---------------------------------------------------------
        # Determine baseline window
        # ---------------------------------------------------------
        start_index = 0
        end_index = test_data.sample_count - 1

        if settings.baseline_start_time_s is not None:
            if not np.isfinite(settings.baseline_start_time_s):
                raise ValueError(
                    "Baseline start time must be finite."
                )

            start_index = int(
                np.searchsorted(
                    time,
                    settings.baseline_start_time_s,
                    side="left",
                )
            )

        if settings.baseline_end_time_s is not None:
            if not np.isfinite(settings.baseline_end_time_s):
                raise ValueError(
                    "Baseline end time must be finite."
                )

            end_index = int(
                np.searchsorted(
                    time,
                    settings.baseline_end_time_s,
                    side="right",
                )
            ) - 1

        if start_index > end_index:
            raise ValueError(
                "Baseline start time must be before or equal to "
                "baseline end time."
            )

        if start_index >= test_data.sample_count:
            raise ValueError(
                "Baseline start time is outside the dataset."
            )

        if end_index < 0:
            raise ValueError(
                "Baseline end time is outside the dataset."
            )

        # ---------------------------------------------------------
        # Calculate baseline
        # ---------------------------------------------------------
        baseline = float(
            np.mean(
                thrust[start_index:end_index + 1]
            )
        )

        # ---------------------------------------------------------
        # Create corrected data without modifying raw data
        # ---------------------------------------------------------
        corrected_thrust = thrust.copy() - baseline

        corrected_data = TestData(
            time_s=test_data.time_s.copy(),
            thrust_N=corrected_thrust,
            raw_hx711=(
                test_data.raw_hx711.copy()
                if test_data.raw_hx711 is not None
                else None
            ),
            delta=(
                test_data.delta.copy()
                if test_data.delta is not None
                else None
            ),
            state=(
                test_data.state.copy()
                if test_data.state is not None
                else None
            ),
            pressure_kPa=(
                test_data.pressure_kPa.copy()
                if test_data.pressure_kPa is not None
                else None
            ),
            metadata=test_data.metadata,
        )

        return BaselineResult(
            data=corrected_data,
            baseline_N=baseline,
            baseline_start_index=start_index,
            baseline_end_index=end_index,
            sample_count=corrected_data.sample_count,
        )