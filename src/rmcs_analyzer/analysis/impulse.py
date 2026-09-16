import numpy as np

from ..data.models import TestData
from .results import EventResults, ThrustResults


class ThrustAnalyzer:
    """Calculate thrust and impulse characteristics."""

    def analyze(
        self,
        test_data: TestData,
        events: EventResults,
    ) -> ThrustResults:
        """Calculate thrust metrics for the detected burn."""

        if (
            events.ignition_index is None
            or events.burnout_index is None
        ):
            return ThrustResults()

        start = events.ignition_index
        end = events.burnout_index

        if end <= start:
            return ThrustResults()

        time = test_data.time_s[
            start : end + 1
        ]

        thrust = test_data.thrust_N[
            start : end + 1
        ]

        if len(time) < 2:
            return ThrustResults()

        # Preserve the recorded thrust sign for the curve,
        # but use magnitude for motor-performance metrics.
        thrust_magnitude = np.abs(
            thrust
        )

        peak_local_index = int(
            np.argmax(thrust_magnitude)
        )

        peak_thrust = float(
            thrust_magnitude[
                peak_local_index
            ]
        )

        peak_time = float(
            time[
                peak_local_index
            ]
        )

        burn_time = float(
            time[-1] - time[0]
        )

        total_impulse = float(
            np.trapezoid(
                thrust_magnitude,
                time,
            )
        )

        if burn_time > 0:
            average_thrust = (
                total_impulse
                / burn_time
            )
        else:
            average_thrust = 0.0

        time_to_peak = (
            peak_time - time[0]
        )

        return ThrustResults(
            peak_thrust_N=peak_thrust,
            peak_thrust_time_s=peak_time,
            average_thrust_N=average_thrust,
            burn_time_s=burn_time,
            total_impulse_Ns=total_impulse,
            time_to_peak_s=time_to_peak,
        )