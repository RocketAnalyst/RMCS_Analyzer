import numpy as np

from .events import EventDetector
from .motor_class import MotorClassCalculator
from .performance import PerformanceReducer
from .performance_extensions import PerformanceExtensionCalculator
from .results import AnalysisResults, ThrustResults
from .statistics import StatisticsAnalyzer
from ..processing.event_model import EventSet


class AnalysisEngine:
    """
    Coordinate the complete analysis stack.

    The processing pipeline's EventSet is the authoritative event
    representation. PerformanceReducer is the authoritative source for
    standardized motor-performance metrics.

    The engine does not modify the supplied TestData.
    """

    def __init__(
        self,
        event_detector=None,
        statistics_analyzer=None,
        motor_class_calculator=None,
        performance_reducer=None,
        performance_extension_calculator=None,
    ):
        self.event_detector = event_detector or EventDetector()
        self.statistics_analyzer = (
            statistics_analyzer or StatisticsAnalyzer()
        )
        self.motor_class_calculator = (
            motor_class_calculator or MotorClassCalculator()
        )
        self.performance_reducer = (
            performance_reducer or PerformanceReducer()
        )
        self.performance_extension_calculator = (
            performance_extension_calculator
            or PerformanceExtensionCalculator()
        )

    def analyze(
        self,
        test_data,
        events: EventSet | None = None,
    ) -> AnalysisResults:
        """
        Analyze prepared test data.

        If an EventSet is supplied, it is authoritative and is used
        directly. Otherwise, events are detected once.

        PerformanceReducer supplies the authoritative standardized motor-
        performance values used by the application and exporters.
        """

        if events is None:
            events = self.event_detector.detect_events(test_data)

        standardized = self.performance_reducer.reduce(test_data)

        # The standardized reduction is authoritative for the core
        # performance fields. The explicit 5% fields remain available for
        # callers that need to distinguish standardized burn-window metrics
        # from the complete recorded curve.
        thrust_results = ThrustResults(
            peak_thrust_N=standardized.peak_thrust_N,
            peak_thrust_time_s=standardized.peak_thrust_time_s,
            average_thrust_N=standardized.average_thrust_N,
            burn_time_s=standardized.burn_time_5pct_s,
            total_impulse_Ns=standardized.total_impulse_Ns,
            time_to_peak_s=(
                standardized.peak_thrust_time_s - standardized.curve_start_time_s
                if standardized.peak_thrust_time_s is not None
                and standardized.curve_start_time_s is not None
                else None
            ),
        )

        thrust_results.threshold_percent = (
            standardized.threshold_percent
        )
        thrust_results.threshold_thrust_N = (
            standardized.threshold_thrust_N
        )
        thrust_results.burn_start_5pct_time_s = (
            standardized.burn_start_5pct_time_s
        )
        thrust_results.burn_end_5pct_time_s = (
            standardized.burn_end_5pct_time_s
        )
        thrust_results.burn_time_5pct_s = (
            standardized.burn_time_5pct_s
        )
        thrust_results.average_thrust_5pct_N = (
            standardized.average_thrust_N
        )
        thrust_results.initial_thrust_average_N = (
            standardized.initial_thrust_average_N
        )
        thrust_results.initial_thrust_window_s = (
            standardized.initial_thrust_window_s
        )
        thrust_results.thrust_rise_rate_N_per_s = (
            standardized.thrust_rise_rate_N_per_s
        )
        thrust_results.thrust_decay_rate_N_per_s = (
            standardized.thrust_decay_rate_N_per_s
        )

        extensions = self.performance_extension_calculator.calculate(
            test_data,
            total_impulse_Ns=standardized.total_impulse_Ns,
            burn_start_5pct_time_s=standardized.burn_start_5pct_time_s,
            burn_end_5pct_time_s=standardized.burn_end_5pct_time_s,
            burn_time_5pct_s=standardized.burn_time_5pct_s,
        )

        thrust_results.isp_s = extensions.isp_s
        thrust_results.isp_status = extensions.isp_status
        thrust_results.cstar_m_per_s = extensions.cstar_m_per_s
        thrust_results.cstar_status = extensions.cstar_status
        thrust_results.average_chamber_pressure_psi = (
            extensions.average_chamber_pressure_psi
        )
        thrust_results.average_mass_flow_kg_per_s = (
            extensions.average_mass_flow_kg_per_s
        )

        # Peak pressure is a primary measured result used by the dashboard.
        # Keep it in the authoritative analysis result model so display
        # panels do not perform their own engineering calculations.
        pressure = test_data.pressure_psi
        if pressure is not None:
            pressure_array = np.asarray(pressure, dtype=float)
            finite_pressure = pressure_array[np.isfinite(pressure_array)]
            thrust_results.peak_pressure_psi = (
                float(np.max(finite_pressure))
                if finite_pressure.size
                else None
            )
        else:
            thrust_results.peak_pressure_psi = None
        thrust_results.total_impulse_valid_curve_Ns = (
            standardized.total_impulse_Ns
        )
        thrust_results.normalized_impulse_Ns = (
            standardized.normalized_impulse_Ns
        )
        thrust_results.impulse_class = standardized.impulse_class
        thrust_results.designation = standardized.designation

        statistics = self.statistics_analyzer.analyze(test_data)

        classification = self.motor_class_calculator.classify(
            standardized.total_impulse_Ns
            if standardized.total_impulse_Ns is not None
            else -1
        )

        return AnalysisResults(
            events=events,
            thrust=thrust_results,
            statistics=statistics,
            classification=classification,
        )
