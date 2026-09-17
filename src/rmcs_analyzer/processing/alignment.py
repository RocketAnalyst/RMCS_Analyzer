from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from ..data.models import TestData
from .event_model import DetectedEvent, EventSet, EventType


@dataclass
class AlignmentSettings:
    """
    Settings used for time-axis alignment.

    When enabled, the selected reference event is shifted to
    t = 0.000 seconds.

    By default, ignition is used as the reference event.
    """

    enabled: bool = False

    reference_event: EventType = EventType.IGNITION

    manual_reference_time_s: Optional[float] = None

    def reset(self):
        """Reset alignment settings to their defaults."""

        self.enabled = False
        self.reference_event = EventType.IGNITION
        self.manual_reference_time_s = None

    def to_dict(self) -> dict[str, Any]:
        """Convert alignment settings to a JSON-compatible dictionary."""

        return {
            "enabled": self.enabled,
            "reference_event": self.reference_event.value,
            "manual_reference_time_s": (
                self.manual_reference_time_s
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "AlignmentSettings":
        """Create alignment settings from a dictionary."""

        reference_value = data.get(
            "reference_event",
            EventType.IGNITION.value,
        )

        try:
            reference_event = EventType(
                reference_value
            )
        except ValueError:
            reference_event = EventType.IGNITION

        return cls(
            enabled=data.get(
                "enabled",
                False,
            ),
            reference_event=reference_event,
            manual_reference_time_s=data.get(
                "manual_reference_time_s"
            ),
        )


@dataclass
class AlignmentResult:
    """Result of applying time-axis alignment."""

    data: TestData

    offset_s: float

    reference_time_s: float

    reference_event: Optional[DetectedEvent]

    sample_count: int


class TimeAligner:
    """
    Performs non-destructive time-axis alignment.

    The original TestData is never modified.

    Alignment subtracts the selected reference time from the
    working time axis:

        aligned_time = original_time - reference_time

    The source-provided calibrated_time_s channel is preserved
    unchanged. Only the working time_s channel is shifted.
    """

    @classmethod
    def align(
        cls,
        test_data: TestData,
        settings: AlignmentSettings | None = None,
        events: EventSet | None = None,
    ) -> AlignmentResult:
        """
        Apply time-axis alignment.
        """

        if test_data.sample_count == 0:
            raise ValueError(
                "Cannot align empty data."
            )

        if settings is None:
            settings = AlignmentSettings()

        # ---------------------------------------------------------
        # Alignment disabled
        # ---------------------------------------------------------

        if not settings.enabled:
            return cls._copy_without_alignment(
                test_data
            )

        reference_event = None

        # ---------------------------------------------------------
        # Determine reference time
        # ---------------------------------------------------------

        if settings.manual_reference_time_s is not None:

            if not np.isfinite(
                settings.manual_reference_time_s
            ):
                raise ValueError(
                    "Manual reference time must be finite."
                )

            reference_time_s = float(
                settings.manual_reference_time_s
            )

        else:

            if events is None:
                raise ValueError(
                    "Alignment requires detected events "
                    "when no manual reference time is supplied."
                )

            reference_event = events.get(
                settings.reference_event
            )

            if reference_event is None:
                raise ValueError(
                    "The selected alignment reference event "
                    "was not detected."
                )

            reference_time_s = float(
                reference_event.time_s
            )

        # ---------------------------------------------------------
        # Align working time axis
        # ---------------------------------------------------------

        aligned_time = (
            test_data.time_s.copy()
            - reference_time_s
        )

        # ---------------------------------------------------------
        # Create aligned data
        # ---------------------------------------------------------

        aligned_data = TestData(
            # -----------------------------------------------------
            # Primary channels
            # -----------------------------------------------------

            time_s=aligned_time,

            thrust_N=test_data.thrust_N.copy(),

            # -----------------------------------------------------
            # Standardized optional channels
            #
            # calibrated_time_s intentionally remains unchanged.
            # It represents the source-provided calibrated timeline,
            # while time_s represents the current working timeline.
            # -----------------------------------------------------

            calibrated_time_s=(
                test_data.calibrated_time_s.copy()
                if test_data.calibrated_time_s is not None
                else None
            ),

            raw_thrust_N=(
                test_data.raw_thrust_N.copy()
                if test_data.raw_thrust_N is not None
                else None
            ),

            prop_loss_kg=(
                test_data.prop_loss_kg.copy()
                if test_data.prop_loss_kg is not None
                else None
            ),

            pressure_psi=(
                test_data.pressure_psi.copy()
                if test_data.pressure_psi is not None
                else None
            ),

            # -----------------------------------------------------
            # Existing processing channels
            # -----------------------------------------------------

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

            # -----------------------------------------------------
            # Metadata
            # -----------------------------------------------------

            metadata=test_data.metadata,
        )

        return AlignmentResult(
            data=aligned_data,
            offset_s=-reference_time_s,
            reference_time_s=reference_time_s,
            reference_event=reference_event,
            sample_count=aligned_data.sample_count,
        )

    @staticmethod
    def _copy_without_alignment(
        test_data: TestData,
    ) -> AlignmentResult:
        """
        Return an independent copy without changing time.

        All time-series channels are copied. The original
        TestData object is never modified.
        """

        copied_data = TestData(
            # -----------------------------------------------------
            # Primary channels
            # -----------------------------------------------------

            time_s=test_data.time_s.copy(),

            thrust_N=test_data.thrust_N.copy(),

            # -----------------------------------------------------
            # Standardized optional channels
            # -----------------------------------------------------

            calibrated_time_s=(
                test_data.calibrated_time_s.copy()
                if test_data.calibrated_time_s is not None
                else None
            ),

            raw_thrust_N=(
                test_data.raw_thrust_N.copy()
                if test_data.raw_thrust_N is not None
                else None
            ),

            prop_loss_kg=(
                test_data.prop_loss_kg.copy()
                if test_data.prop_loss_kg is not None
                else None
            ),

            pressure_psi=(
                test_data.pressure_psi.copy()
                if test_data.pressure_psi is not None
                else None
            ),

            # -----------------------------------------------------
            # Existing processing channels
            # -----------------------------------------------------

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

            # -----------------------------------------------------
            # Metadata
            # -----------------------------------------------------

            metadata=test_data.metadata,
        )

        return AlignmentResult(
            data=copied_data,
            offset_s=0.0,
            reference_time_s=0.0,
            reference_event=None,
            sample_count=copied_data.sample_count,
        )