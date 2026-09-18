import numpy as np

from ..data.models import TestData
from .results import EventResults, ThrustResults


class ThrustAnalyzer:
    """
    Calculate thrust and impulse characteristics for a supplied
    analysis event window.

    This module intentionally preserves the current Phase 1
    calculation behavior.  The industry-standard performance
    reduction will replace this calculation in Phase 2.
    """

    def analyze(
        self,
        test_data: TestData,
        events: EventResults,
    ) -> ThrustResults:
        """Calculate current thrust metrics within the event window."""

        if (
            events.ignition_index is None
            or events.burnout_index is None
        ):
            return ThrustResults()

        start = events.ignition_index
        end = events.burnout_index

        if start < 0 or end >= test_data.sample_count:
            return ThrustResults()

        if end <= start:
            return ThrustResults()

        time = np.asarray(
            test_data.time_s[start:end + 1],
            dtype=float,
        )
        thrust = np.asarray(
            test_data.thrust_N[start:end + 1],
            dtype=float,
        )

        if len(time) < 2 or len(time) != len(thrust):
            return ThrustResults()

        finite = np.isfinite(time) & np.isfinite(thrust)

        if np.count_nonzero(finite) < 2:
            return ThrustResults()

        time = time[finite]
        thrust = thrust[finite]

        # Negative corrected load-cell readings are not motor thrust.
        motor_thrust = np.maximum(thrust, 0.0)

        peak_local_index = int(np.argmax(motor_thrust))
        peak_thrust = float(motor_thrust[peak_local_index])
        peak_time = float(time[peak_local_index])

        burn_time = float(time[-1] - time[0])

        total_impulse = float(
            np.trapezoid(motor_thrust, time)
        )

        average_thrust = (
            total_impulse / burn_time
            if burn_time > 0
            else 0.0
        )

        return ThrustResults(
            peak_thrust_N=peak_thrust,
            peak_thrust_time_s=peak_time,
            average_thrust_N=average_thrust,
            burn_time_s=burn_time,
            total_impulse_Ns=total_impulse,
            time_to_peak_s=peak_time - time[0],
        )
