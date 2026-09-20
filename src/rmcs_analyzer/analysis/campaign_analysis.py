"""Population-level analysis of measured motor test performance.

Campaign analysis intentionally operates on completed RMCS test results. It
summarizes what a set of fired motors actually did; it does not simulate
motor behavior or characterize propellant burn-rate parameters.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np


METRIC_DEFINITIONS = {
    "Total Impulse": ("total_impulse_valid_curve_Ns", "N·s"),
    "Peak Thrust": ("peak_thrust_N", "N"),
    "Burn Time": ("burn_time_5pct_s", "s"),
    "Average Thrust": ("average_thrust_5pct_N", "N"),
    "Isp": ("isp_s", "s"),
    "C*": ("cstar_m_per_s", "m/s"),
}


@dataclass(frozen=True)
class CampaignMetricStats:
    """Population statistics for one measured performance metric."""

    name: str
    unit: str
    count: int
    total_tests: int
    mean: Optional[float]
    median: Optional[float]
    minimum: Optional[float]
    maximum: Optional[float]
    std_dev: Optional[float]
    coefficient_variation_percent: Optional[float]


@dataclass(frozen=True)
class CampaignCurve:
    """Population thrust-curve statistics on a common time basis."""

    time: np.ndarray
    mean: np.ndarray
    median: np.ndarray
    std_dev: np.ndarray
    minimum: np.ndarray
    maximum: np.ndarray
    sample_count: np.ndarray
    basis: str
    test_count: int
    individual_curves: tuple[tuple[np.ndarray, np.ndarray], ...] = ()


@dataclass(frozen=True)
class CampaignAnalysisResult:
    """Complete result of a campaign calculation."""

    total_tests: int
    included_tests: int
    excluded_tests: tuple[str, ...]
    metrics: dict[str, CampaignMetricStats]
    curve: Optional[CampaignCurve]


class CampaignAnalyzer:
    """Analyze a collection of completed TestModel objects."""

    def __init__(self, curve_points: int = 500):
        self.curve_points = max(int(curve_points), 50)

    def analyze(self, tests, *, curve_basis: str = "absolute") -> CampaignAnalysisResult:
        tests = list(tests)
        excluded = tuple(
            test.display_name
            for test in tests
            if test.analysis_results is None
        )
        usable = [test for test in tests if test.analysis_results is not None]

        metrics = {}
        for name, (attribute, unit) in METRIC_DEFINITIONS.items():
            values = []
            for test in tests:
                results = test.analysis_results
                value = getattr(results.thrust, attribute, None) if results else None
                if value is not None and np.isfinite(value):
                    values.append(float(value))
            metrics[name] = self._statistics(name, unit, values, len(tests))

        curve = self._build_curve(usable, curve_basis=curve_basis)

        return CampaignAnalysisResult(
            total_tests=len(tests),
            included_tests=len(usable),
            excluded_tests=excluded,
            metrics=metrics,
            curve=curve,
        )

    @staticmethod
    def _statistics(name, unit, values, total_tests):
        if not values:
            return CampaignMetricStats(
                name=name,
                unit=unit,
                count=0,
                total_tests=total_tests,
                mean=None,
                median=None,
                minimum=None,
                maximum=None,
                std_dev=None,
                coefficient_variation_percent=None,
            )

        data = np.asarray(values, dtype=float)
        mean = float(np.mean(data))
        std_dev = float(np.std(data, ddof=0))
        cv = None
        if np.isfinite(mean) and mean != 0:
            cv = float(std_dev / abs(mean) * 100.0)

        return CampaignMetricStats(
            name=name,
            unit=unit,
            count=int(data.size),
            total_tests=total_tests,
            mean=mean,
            median=float(np.median(data)),
            minimum=float(np.min(data)),
            maximum=float(np.max(data)),
            std_dev=std_dev,
            coefficient_variation_percent=cv,
        )

    def _build_curve(self, tests, *, curve_basis):
        if curve_basis not in {"absolute", "normalized"}:
            raise ValueError("curve_basis must be 'absolute' or 'normalized'")

        curves = []
        max_x = 0.0

        for test in tests:
            data = test.data
            results = test.analysis_results
            if results is None:
                continue

            start = results.thrust.burn_start_5pct_time_s
            end = results.thrust.burn_end_5pct_time_s
            if start is None or end is None or end <= start:
                continue

            time = np.asarray(data.time_s, dtype=float)
            thrust = np.asarray(data.thrust_N, dtype=float)
            if time.size != thrust.size or time.size < 2:
                continue

            finite = np.isfinite(time) & np.isfinite(thrust)
            time = time[finite]
            thrust = thrust[finite]
            if time.size < 2:
                continue

            order = np.argsort(time, kind="stable")
            time = time[order]
            thrust = thrust[order]

            unique_time, unique_idx = np.unique(time, return_index=True)
            time = unique_time
            thrust = thrust[unique_idx]
            if time.size < 2:
                continue

            if start < time[0] or end > time[-1]:
                continue

            start_thrust = float(np.interp(start, time, thrust))
            end_thrust = float(np.interp(end, time, thrust))
            inside = (time > start) & (time < end)
            local_time = np.concatenate(([start], time[inside], [end]))
            local_thrust = np.concatenate(([start_thrust], thrust[inside], [end_thrust]))

            if curve_basis == "normalized":
                local_time = (local_time - start) / (end - start)
                max_x = 1.0
            else:
                local_time = local_time - start
                max_x = max(max_x, float(local_time[-1]))

            curves.append((local_time, local_thrust))

        if not curves or max_x <= 0:
            return None

        grid = np.linspace(0.0, max_x, self.curve_points)
        matrix = np.full((len(curves), grid.size), np.nan, dtype=float)

        for row, (x, y) in enumerate(curves):
            finite = np.isfinite(x) & np.isfinite(y)
            x = x[finite]
            y = y[finite]
            if x.size < 2:
                continue
            matrix[row, :] = np.interp(grid, x, y, left=np.nan, right=np.nan)
            matrix[row, grid > x[-1]] = np.nan

        valid_count = np.sum(np.isfinite(matrix), axis=0)
        valid = valid_count > 0
        if not np.any(valid):
            return None

        mean = np.full(grid.shape, np.nan)
        median = np.full(grid.shape, np.nan)
        std_dev = np.full(grid.shape, np.nan)
        minimum = np.full(grid.shape, np.nan)
        maximum = np.full(grid.shape, np.nan)

        for index in np.flatnonzero(valid):
            values = matrix[:, index]
            values = values[np.isfinite(values)]
            mean[index] = np.mean(values)
            median[index] = np.median(values)
            std_dev[index] = np.std(values, ddof=0)
            minimum[index] = np.min(values)
            maximum[index] = np.max(values)

        return CampaignCurve(
            time=grid,
            mean=mean,
            median=median,
            std_dev=std_dev,
            minimum=minimum,
            maximum=maximum,
            sample_count=valid_count,
            basis=curve_basis,
            test_count=len(curves),
            individual_curves=tuple(curves),
        )
