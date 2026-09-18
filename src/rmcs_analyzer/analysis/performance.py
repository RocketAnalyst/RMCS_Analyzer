"""Authoritative Phase 2 rocket-motor performance reduction.

The reduction in this module follows the project specification and the
NFPA-1125-based convention documented by ThrustCurve:

* Peak thrust is the maximum positive finite thrust.
* Burn start and burn end are the interpolated crossings of 5% of peak
  thrust.
* Standardized average thrust is the impulse within the 5%-defined burn
  interval divided by that burn time.
* Total impulse is measured over the complete valid recorded thrust curve,
  not merely the 5%-defined burn interval.
* Negative thrust readings are not motor thrust and therefore contribute
  zero area to total impulse.
* Non-finite samples are excluded from the valid curve.
* The calibrated Time Cal (s) channel is used when it is present and valid;
  otherwise Time(s) is used.
* Initial thrust is the average thrust over the first 0.5 s beginning at
  the standardized 5% burn start.
* Motor class is based on total impulse.
* Motor designation is the impulse class plus rounded standardized average
  thrust.

Physical burnout and standardized 5% burnout are intentionally separate
concepts. The physical EventSet is not used to truncate total impulse because
the standardized definition measures total impulse over the whole thrust
curve. A recorded test curve must therefore be prepared/trimmed by the
processing layer if samples outside the valid test curve are known to be
invalid.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..data.models import TestData
from .motor_class import MotorClassCalculator


@dataclass(frozen=True)
class PerformanceReduction:
    """Standardized motor-performance results."""

    peak_thrust_N: Optional[float] = None
    peak_thrust_time_s: Optional[float] = None

    threshold_percent: float = 5.0
    threshold_thrust_N: Optional[float] = None

    burn_start_5pct_time_s: Optional[float] = None
    burn_end_5pct_time_s: Optional[float] = None
    burn_time_5pct_s: Optional[float] = None

    total_impulse_Ns: Optional[float] = None
    normalized_impulse_Ns: Optional[float] = None
    average_thrust_N: Optional[float] = None

    initial_thrust_average_N: Optional[float] = None
    initial_thrust_window_s: Optional[float] = None

    curve_start_time_s: Optional[float] = None
    curve_end_time_s: Optional[float] = None

    impulse_class: Optional[str] = None
    designation: Optional[str] = None


class PerformanceReducer:
    """Reduce prepared TestData using the RMCS standardized methodology."""

    THRESHOLD_PERCENT = 5.0
    INITIAL_THRUST_WINDOW_S = 0.5

    def __init__(
        self,
        motor_class_calculator: Optional[MotorClassCalculator] = None,
    ):
        self.motor_class_calculator = (
            motor_class_calculator or MotorClassCalculator()
        )

    def reduce(self, test_data: TestData) -> PerformanceReduction:
        time_s, thrust_N = self._prepare_curve(test_data)

        if time_s.size == 0:
            return PerformanceReduction()

        peak_index = int(np.argmax(thrust_N))
        peak_thrust = float(thrust_N[peak_index])
        peak_time = float(time_s[peak_index])

        curve_start = float(time_s[0])
        curve_end = float(time_s[-1])

        total_impulse = self._integrate_positive_curve(
            time_s,
            thrust_N,
        )

        if peak_thrust <= 0.0:
            return PerformanceReduction(
                peak_thrust_N=peak_thrust,
                peak_thrust_time_s=peak_time,
                threshold_percent=self.THRESHOLD_PERCENT,
                threshold_thrust_N=0.0,
                total_impulse_Ns=total_impulse,
                curve_start_time_s=curve_start,
                curve_end_time_s=curve_end,
            )

        threshold = (
            peak_thrust
            * self.THRESHOLD_PERCENT
            / 100.0
        )

        start_time = self._find_rising_crossing(
            time_s,
            thrust_N,
            threshold,
            peak_index,
        )

        end_time = self._find_falling_crossing(
            time_s,
            thrust_N,
            threshold,
            peak_index,
        )

        if (
            start_time is None
            or end_time is None
            or end_time <= start_time
        ):
            classification = self.motor_class_calculator.classify(
                total_impulse
            )

            return PerformanceReduction(
                peak_thrust_N=peak_thrust,
                peak_thrust_time_s=peak_time,
                threshold_percent=self.THRESHOLD_PERCENT,
                threshold_thrust_N=threshold,
                total_impulse_Ns=total_impulse,
                curve_start_time_s=curve_start,
                curve_end_time_s=curve_end,
                impulse_class=classification.motor_class,
            )

        normalized_impulse = self._integrate_interval(
            time_s,
            thrust_N,
            start_time,
            end_time,
            threshold,
        )

        burn_time = end_time - start_time
        average_thrust = (
            normalized_impulse / burn_time
        )

        initial_average = self._initial_thrust_average(
            time_s,
            thrust_N,
            start_time,
        )

        classification = self.motor_class_calculator.classify(
            total_impulse
        )

        designation = None

        if classification.motor_class:
            designation = (
                f"{classification.motor_class}"
                f"{round(average_thrust):d}"
            )

        return PerformanceReduction(
            peak_thrust_N=peak_thrust,
            peak_thrust_time_s=peak_time,
            threshold_percent=self.THRESHOLD_PERCENT,
            threshold_thrust_N=threshold,
            burn_start_5pct_time_s=start_time,
            burn_end_5pct_time_s=end_time,
            burn_time_5pct_s=burn_time,
            total_impulse_Ns=total_impulse,
            normalized_impulse_Ns=normalized_impulse,
            average_thrust_N=average_thrust,
            initial_thrust_average_N=initial_average,
            initial_thrust_window_s=self.INITIAL_THRUST_WINDOW_S,
            curve_start_time_s=curve_start,
            curve_end_time_s=curve_end,
            impulse_class=classification.motor_class,
            designation=designation,
        )

    @staticmethod
    def _prepare_curve(
        test_data: TestData,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Prepare the complete finite recorded thrust curve.

        The source timeline is Time Cal(s) when available and valid.
        Original Time(s) remains preserved in TestData.

        Samples with non-finite time or thrust are excluded. The remaining
        samples are sorted by time and duplicate timestamps are reduced to
        their first occurrence. This method does not truncate the curve at
        physical burnout or at the 5% threshold.
        """

        original_time = np.asarray(
            test_data.time_s,
            dtype=float,
        )

        calibrated = test_data.calibrated_time_s

        if calibrated is not None:
            calibrated = np.asarray(
                calibrated,
                dtype=float,
            )

        if (
            calibrated is not None
            and calibrated.shape == original_time.shape
            and calibrated.size > 0
            and np.all(np.isfinite(calibrated))
        ):
            time_s = calibrated
        else:
            time_s = original_time

        thrust_N = np.asarray(
            test_data.thrust_N,
            dtype=float,
        )

        if (
            time_s.shape != thrust_N.shape
            or time_s.size == 0
        ):
            return (
                np.array([], dtype=float),
                np.array([], dtype=float),
            )

        valid = (
            np.isfinite(time_s)
            & np.isfinite(thrust_N)
        )

        time_s = time_s[valid]
        thrust_N = thrust_N[valid]

        if time_s.size == 0:
            return (
                np.array([], dtype=float),
                np.array([], dtype=float),
            )

        order = np.argsort(
            time_s,
            kind="stable",
        )

        time_s = time_s[order]
        thrust_N = thrust_N[order]

        unique_time, unique_index = np.unique(
            time_s,
            return_index=True,
        )

        return (
            unique_time,
            thrust_N[unique_index],
        )

    @staticmethod
    def _find_rising_crossing(
        time_s: np.ndarray,
        thrust_N: np.ndarray,
        threshold_N: float,
        peak_index: int,
    ) -> Optional[float]:
        """Find the first rising 5% threshold crossing before peak."""

        if peak_index == 0:
            if thrust_N[0] >= threshold_N:
                return float(time_s[0])
            return None

        for index in range(
            1,
            peak_index + 1,
        ):
            y0 = thrust_N[index - 1]
            y1 = thrust_N[index]

            if y0 < threshold_N <= y1:
                return PerformanceReducer._interpolate_crossing(
                    time_s[index - 1],
                    y0,
                    time_s[index],
                    y1,
                    threshold_N,
                )

            if y0 == threshold_N:
                return float(time_s[index - 1])

        return None

    @staticmethod
    def _find_falling_crossing(
        time_s: np.ndarray,
        thrust_N: np.ndarray,
        threshold_N: float,
        peak_index: int,
    ) -> Optional[float]:
        """Find the final falling 5% threshold crossing after peak."""

        last_crossing = None

        for index in range(
            peak_index + 1,
            len(time_s),
        ):
            y0 = thrust_N[index - 1]
            y1 = thrust_N[index]

            if y0 >= threshold_N > y1:
                last_crossing = (
                    PerformanceReducer._interpolate_crossing(
                        time_s[index - 1],
                        y0,
                        time_s[index],
                        y1,
                        threshold_N,
                    )
                )

            elif (
                y0 == threshold_N
                and y1 < threshold_N
            ):
                last_crossing = float(
                    time_s[index - 1]
                )

        return last_crossing

    @staticmethod
    def _interpolate_crossing(
        t0: float,
        y0: float,
        t1: float,
        y1: float,
        threshold: float,
    ) -> float:
        """Linearly interpolate a threshold crossing."""

        if y1 == y0:
            return float(t0)

        fraction = (
            (threshold - y0)
            / (y1 - y0)
        )

        return float(
            t0 + fraction * (t1 - t0)
        )

    @staticmethod
    def _integrate_positive_curve(
        time_s: np.ndarray,
        thrust_N: np.ndarray,
    ) -> float:
        """Integrate the complete finite curve with negative thrust clipped.

        Negative load-cell values cannot represent negative motor thrust.
        They therefore contribute zero area rather than negative impulse.
        """

        positive_thrust = np.maximum(
            thrust_N,
            0.0,
        )

        return float(
            np.trapezoid(
                positive_thrust,
                time_s,
            )
        )

    @staticmethod
    def _integrate_interval(
        time_s: np.ndarray,
        thrust_N: np.ndarray,
        start_time: float,
        end_time: float,
        threshold_N: float,
    ) -> float:
        """Integrate positive thrust over an exact 5% interval."""

        mask = (
            (time_s > start_time)
            & (time_s < end_time)
        )

        interval_time = np.concatenate(
            (
                np.array([start_time]),
                time_s[mask],
                np.array([end_time]),
            )
        )

        interval_thrust = np.concatenate(
            (
                np.array([threshold_N]),
                thrust_N[mask],
                np.array([threshold_N]),
            )
        )

        positive_thrust = np.maximum(
            interval_thrust,
            0.0,
        )

        return float(
            np.trapezoid(
                positive_thrust,
                interval_time,
            )
        )

    def _initial_thrust_average(
        self,
        time_s: np.ndarray,
        thrust_N: np.ndarray,
        start_time: float,
    ) -> float:
        """Average thrust during the first 0.5 s after 5% start."""

        end_time = (
            start_time
            + self.INITIAL_THRUST_WINDOW_S
        )

        if end_time > time_s[-1]:
            return float("nan")

        mask = (
            (time_s > start_time)
            & (time_s < end_time)
        )

        interior_time = time_s[mask]
        interior_thrust = thrust_N[mask]

        start_thrust = self._interpolate_value(
            time_s,
            thrust_N,
            start_time,
        )

        end_thrust = self._interpolate_value(
            time_s,
            thrust_N,
            end_time,
        )

        interval_time = np.concatenate(
            (
                np.array([start_time]),
                interior_time,
                np.array([end_time]),
            )
        )

        interval_thrust = np.concatenate(
            (
                np.array([start_thrust]),
                interior_thrust,
                np.array([end_thrust]),
            )
        )

        interval_thrust = np.maximum(
            interval_thrust,
            0.0,
        )

        impulse = np.trapezoid(
            interval_thrust,
            interval_time,
        )

        return float(
            impulse
            / self.INITIAL_THRUST_WINDOW_S
        )

    @staticmethod
    def _interpolate_value(
        time_s: np.ndarray,
        thrust_N: np.ndarray,
        target_time: float,
    ) -> float:
        """Linearly interpolate thrust at an exact timestamp."""

        if target_time <= time_s[0]:
            return float(thrust_N[0])

        if target_time >= time_s[-1]:
            return float(thrust_N[-1])

        index = int(
            np.searchsorted(
                time_s,
                target_time,
            )
        )

        if time_s[index] == target_time:
            return float(thrust_N[index])

        t0 = time_s[index - 1]
        t1 = time_s[index]
        y0 = thrust_N[index - 1]
        y1 = thrust_N[index]

        if t1 == t0:
            return float(y0)

        fraction = (
            (target_time - t0)
            / (t1 - t0)
        )

        return float(
            y0 + fraction * (y1 - y0)
        )
