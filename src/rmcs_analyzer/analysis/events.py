import numpy as np

from ..data.models import TestData
from .results import EventResults


class EventDetector:
    """
    Detect important events in a thrust curve.

    RMCS state information is preferred when available.
    A threshold-based fallback is provided for generic data.
    """

    def __init__(
        self,
        threshold_N: float = 5.0,
    ):
        self.threshold_N = threshold_N

    def detect(
        self,
        test_data: TestData,
    ) -> EventResults:
        """
        Detect ignition, burnout, and peak events.
        """

        if test_data.sample_count == 0:
            return EventResults()

        if self._has_rmcs_states(
            test_data
        ):
            return self._detect_from_states(
                test_data
            )

        return self._detect_from_threshold(
            test_data
        )

    def _has_rmcs_states(
        self,
        test_data: TestData,
    ) -> bool:
        """Determine whether useful RMCS state data exists."""

        if test_data.state is None:
            return False

        states = {
            str(value).strip()
            for value in test_data.state
            if str(value).strip()
        }

        return (
            "BURNING" in states
            and (
                "WAITING_FOR_IGNITION"
                in states
                or "POST_BURN"
                in states
            )
        )

    def _detect_from_states(
        self,
        test_data: TestData,
    ) -> EventResults:
        """Detect events from RMCS state transitions."""

        states = np.asarray(
            test_data.state,
            dtype=str,
        )

        burning_indices = np.where(
            states == "BURNING"
        )[0]

        if len(burning_indices) == 0:
            return EventResults()

        ignition_index = int(
            burning_indices[0]
        )

        # Prefer the first POST_BURN sample as
        # the burnout boundary.
        post_burn_indices = np.where(
            states == "POST_BURN"
        )[0]

        valid_post_burn = (
            post_burn_indices[
                post_burn_indices > ignition_index
            ]
        )

        if len(valid_post_burn) > 0:
            burnout_index = int(
                valid_post_burn[0]
            )
        else:
            burnout_index = int(
                burning_indices[-1]
            )

        burn_slice = slice(
            ignition_index,
            burnout_index + 1,
        )

        burn_thrust = test_data.thrust_N[
            burn_slice
        ]

        if len(burn_thrust) == 0:
            return EventResults()

        local_peak_index = int(
            np.argmax(
                np.abs(burn_thrust)
            )
        )

        peak_index = (
            ignition_index
            + local_peak_index
        )

        return EventResults(
            ignition_time_s=float(
                test_data.time_s[
                    ignition_index
                ]
            ),
            burnout_time_s=float(
                test_data.time_s[
                    burnout_index
                ]
            ),
            peak_time_s=float(
                test_data.time_s[
                    peak_index
                ]
            ),
            ignition_index=ignition_index,
            burnout_index=burnout_index,
            peak_index=peak_index,
            detection_method="RMCS state data",
        )

    def _detect_from_threshold(
        self,
        test_data: TestData,
    ) -> EventResults:
        """
        Detect events using a configurable thrust threshold.

        This is the fallback for non-RMCS CSV data.
        """

        thrust = np.asarray(
            test_data.thrust_N,
            dtype=float,
        )

        above_threshold = (
            np.abs(thrust)
            >= self.threshold_N
        )

        indices = np.where(
            above_threshold
        )[0]

        if len(indices) == 0:
            return EventResults(
                detection_method=(
                    "Threshold — no event detected"
                )
            )

        ignition_index = int(
            indices[0]
        )

        # Find the final threshold crossing.
        burnout_index = int(
            indices[-1]
        )

        burn_slice = slice(
            ignition_index,
            burnout_index + 1,
        )

        burn_thrust = thrust[
            burn_slice
        ]

        local_peak_index = int(
            np.argmax(
                np.abs(burn_thrust)
            )
        )

        peak_index = (
            ignition_index
            + local_peak_index
        )

        return EventResults(
            ignition_time_s=float(
                test_data.time_s[
                    ignition_index
                ]
            ),
            burnout_time_s=float(
                test_data.time_s[
                    burnout_index
                ]
            ),
            peak_time_s=float(
                test_data.time_s[
                    peak_index
                ]
            ),
            ignition_index=ignition_index,
            burnout_index=burnout_index,
            peak_index=peak_index,
            detection_method=(
                "Threshold detection"
            ),
        )