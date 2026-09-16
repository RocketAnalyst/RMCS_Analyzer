import numpy as np

from ..data.models import TestData
from .results import StatisticalResults


class StatisticsAnalyzer:
    """Calculate basic measurement statistics."""

    def analyze(
        self,
        test_data: TestData,
    ) -> StatisticalResults:
        """Calculate statistics for the test data."""

        if test_data.sample_count == 0:
            return StatisticalResults()

        baseline_mean = None
        baseline_std = None

        if test_data.state is not None:
            states = np.asarray(
                test_data.state,
                dtype=str,
            )

            waiting_mask = (
                states
                == "WAITING_FOR_IGNITION"
            )

            if np.any(waiting_mask):
                baseline = (
                    test_data.thrust_N[
                        waiting_mask
                    ]
                )

                baseline_mean = float(
                    np.mean(baseline)
                )

                baseline_std = float(
                    np.std(baseline)
                )

        return StatisticalResults(
            sample_count=(
                test_data.sample_count
            ),
            sample_rate_hz=(
                test_data.sample_rate_hz
            ),
            minimum_thrust_N=(
                test_data.minimum_thrust_N
            ),
            maximum_thrust_N=(
                test_data.maximum_thrust_N
            ),
            baseline_mean_N=baseline_mean,
            baseline_std_N=baseline_std,
        )