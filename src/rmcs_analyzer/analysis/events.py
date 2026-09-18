import numpy as np

from ..data.models import TestData
from ..processing.event_model import (
    DetectedEvent,
    EventSet,
    EventType,
)
from .results import EventResults


class EventDetector:
    """
    Detect important events in a thrust curve.

    RMCS state information is preferred when available.
    A threshold-based fallback is provided for generic data.

    The original EventResults API is preserved.
    A standardized EventSet representation is also available through
    detect_events().

    For threshold-based detection, rocket motor thrust is treated as
    positive thrust. Negative post-burn load-cell values are therefore
    not interpreted as continued motor thrust.

    Burnout is the first sustained transition below the thrust
    threshold after ignition/peak, rather than simply the last sample
    that happens to exceed the threshold.
    """

    def __init__(
        self,
        threshold_N: float = 5.0,
        burnout_hold_time_s: float = 0.10,
    ):
        self.threshold_N = float(threshold_N)
        self.burnout_hold_time_s = float(
            burnout_hold_time_s
        )

    def detect(
        self,
        test_data: TestData,
    ) -> EventResults:
        """
        Detect ignition, burnout, and peak events.

        This preserves the existing EventResults API.
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

    def detect_events(
        self,
        test_data: TestData,
    ) -> EventSet:
        """
        Detect events and return them as standardized EventSet objects.

        This uses the existing detection algorithm and converts its
        EventResults into the new event model.
        """

        results = self.detect(test_data)

        event_set = EventSet()

        if results.ignition_time_s is not None:
            event_set.add(
                DetectedEvent(
                    event_type=EventType.IGNITION,
                    time_s=results.ignition_time_s,
                    sample_index=results.ignition_index,
                    value=self._value_at_index(
                        test_data,
                        results.ignition_index,
                    ),
                    label="Ignition",
                    notes=(
                        f"Detection method: "
                        f"{results.detection_method}"
                    ),
                    automatically_detected=True,
                )
            )

        if results.burnout_time_s is not None:
            event_set.add(
                DetectedEvent(
                    event_type=EventType.BURNOUT,
                    time_s=results.burnout_time_s,
                    sample_index=results.burnout_index,
                    value=self._value_at_index(
                        test_data,
                        results.burnout_index,
                    ),
                    label="Burnout",
                    notes=(
                        f"Detection method: "
                        f"{results.detection_method}"
                    ),
                    automatically_detected=True,
                )
            )

        if results.peak_time_s is not None:
            event_set.add(
                DetectedEvent(
                    event_type=EventType.PEAK_THRUST,
                    time_s=results.peak_time_s,
                    sample_index=results.peak_index,
                    value=self._value_at_index(
                        test_data,
                        results.peak_index,
                    ),
                    label="Peak Thrust",
                    notes=(
                        f"Detection method: "
                        f"{results.detection_method}"
                    ),
                    automatically_detected=True,
                )
            )

        return event_set

    @staticmethod
    def _value_at_index(
        test_data: TestData,
        index: int | None,
    ) -> float | None:
        """Return thrust at an event index when available."""

        if index is None:
            return None

        if index < 0:
            return None

        if index >= test_data.sample_count:
            return None

        return float(
            test_data.thrust_N[index]
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

        # Motor thrust is treated as positive. Do not let a negative
        # load-cell value become the reported peak.
        local_peak_index = int(
            np.argmax(
                burn_thrust
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
        Detect events using a configurable positive-thrust threshold.

        Ignition:
            First sample at or above threshold.

        Peak:
            Maximum positive thrust between ignition and burnout.

        Burnout:
            First sample after the peak for which thrust remains below
            threshold for burnout_hold_time_s.

        If the signal never provides a sustained below-threshold
        region, the final valid sample is used as the burnout boundary.
        """

        thrust = np.asarray(
            test_data.thrust_N,
            dtype=float,
        )

        time = np.asarray(
            test_data.time_s,
            dtype=float,
        )

        if len(thrust) == 0:
            return EventResults()

        finite = np.isfinite(thrust)

        if not np.any(finite):
            return EventResults(
                detection_method=(
                    "Threshold — no event detected"
                )
            )

        # Positive thrust is the expected motor-load direction.
        above_threshold = (
            finite
            & (thrust >= self.threshold_N)
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

        # Peak is found from the positive thrust signal after ignition.
        peak_search = np.where(
            finite
            & (
                np.arange(len(thrust))
                >= ignition_index
            )
        )[0]

        if len(peak_search) == 0:
            return EventResults()

        peak_index = int(
            peak_search[
                np.argmax(
                    thrust[peak_search]
                )
            ]
        )

        # ---------------------------------------------------------
        # Find sustained post-peak burnout.
        #
        # We look for the first below-threshold sample after the
        # peak whose following samples remain below threshold for
        # the configured hold time.
        # ---------------------------------------------------------

        burnout_index = self._find_sustained_burnout(
            thrust,
            time,
            peak_index,
        )

        if burnout_index is None:
            # No sustained below-threshold region was observed.
            # Preserve the old API's useful fallback behavior.
            burnout_index = int(
                indices[-1]
            )

        # The burnout boundary should not precede the peak.
        burnout_index = max(
            burnout_index,
            peak_index,
        )

        burn_slice = slice(
            ignition_index,
            burnout_index + 1,
        )

        burn_thrust = thrust[
            burn_slice
        ]

        if len(burn_thrust) == 0:
            return EventResults()

        return EventResults(
            ignition_time_s=float(
                time[ignition_index]
            ),
            burnout_time_s=float(
                time[burnout_index]
            ),
            peak_time_s=float(
                time[peak_index]
            ),
            ignition_index=ignition_index,
            burnout_index=burnout_index,
            peak_index=peak_index,
            detection_method=(
                "Threshold detection"
            ),
        )

    def _find_sustained_burnout(
        self,
        thrust: np.ndarray,
        time: np.ndarray,
        peak_index: int,
    ) -> int | None:
        """
        Find the first sustained below-threshold region after peak.

        The returned index is the first sample below threshold in the
        sustained region, so the reported burnout time corresponds to
        the beginning of the post-burn transition rather than the end
        of the recording.
        """

        if peak_index >= len(thrust) - 1:
            return None

        if (
            not np.isfinite(self.burnout_hold_time_s)
            or self.burnout_hold_time_s <= 0
        ):
            hold_time_s = 0.0
        else:
            hold_time_s = self.burnout_hold_time_s

        for index in range(
            peak_index + 1,
            len(thrust),
        ):

            if not np.isfinite(thrust[index]):
                continue

            if thrust[index] >= self.threshold_N:
                continue

            target_time = (
                time[index]
                + hold_time_s
            )

            end_index = int(
                np.searchsorted(
                    time,
                    target_time,
                    side="left",
                )
            )

            if end_index >= len(thrust):
                # The recording ends before we can confirm the
                # requested hold period.
                continue

            region = thrust[
                index : end_index + 1
            ]

            if len(region) == 0:
                continue

            if np.all(
                np.isfinite(region)
                & (region < self.threshold_N)
            ):
                return index

        return None