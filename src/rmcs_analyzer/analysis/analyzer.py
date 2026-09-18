from .events import EventDetector
from .impulse import ThrustAnalyzer
from .motor_class import MotorClassCalculator
from .performance import PerformanceReducer
from .results import AnalysisResults, EventResults
from .statistics import StatisticsAnalyzer
from ..processing.event_model import EventSet, EventType


class AnalysisEngine:
    """
    Coordinate the complete analysis stack.

    The processing pipeline's EventSet is the authoritative event
    representation. The Phase 2 PerformanceReducer is the authoritative
    source for standardized motor-performance metrics.

    The legacy ThrustAnalyzer remains available during the transition so
    existing GUI/persistence consumers continue to receive the original
    Phase 1 metrics. Standardized values are copied into ThrustResults
    from PerformanceReducer.

    The engine does not modify the supplied TestData.
    """

    def __init__(
        self,
        event_detector=None,
        thrust_analyzer=None,
        statistics_analyzer=None,
        motor_class_calculator=None,
        performance_reducer=None,
    ):
        self.event_detector = event_detector or EventDetector()
        self.thrust_analyzer = thrust_analyzer or ThrustAnalyzer()
        self.statistics_analyzer = (
            statistics_analyzer or StatisticsAnalyzer()
        )
        self.motor_class_calculator = (
            motor_class_calculator or MotorClassCalculator()
        )
        self.performance_reducer = (
            performance_reducer or PerformanceReducer()
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

        Legacy Phase 1 thrust results are still generated for compatibility.
        Standardized Phase 2 performance results are then generated from the
        same prepared TestData and copied into the result model.
        """

        if events is None:
            events = self.event_detector.detect_events(test_data)

        legacy_events = self._event_set_to_legacy(events)

        thrust_results = self.thrust_analyzer.analyze(
            test_data,
            legacy_events,
        )

        standardized = self.performance_reducer.reduce(test_data)

        # Keep the existing Phase 1 fields intact while making the
        # standardized Phase 2 fields authoritative for those metrics.
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
        thrust_results.total_impulse_valid_curve_Ns = (
            standardized.total_impulse_Ns
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

    @staticmethod
    def _event_set_to_legacy(events: EventSet) -> EventResults:
        """Convert the authoritative EventSet to the legacy result model."""

        ignition = events.get(EventType.IGNITION)
        burnout = events.get(EventType.BURNOUT)
        peak = events.get(EventType.PEAK_THRUST)

        detection_methods = [
            event.notes.replace("Detection method: ", "", 1)
            for event in (ignition, burnout, peak)
            if event is not None and event.notes
        ]

        detection_method = (
            detection_methods[0]
            if detection_methods
            else ""
        )

        return EventResults(
            ignition_time_s=(
                ignition.time_s if ignition is not None else None
            ),
            burnout_time_s=(
                burnout.time_s if burnout is not None else None
            ),
            peak_time_s=(
                peak.time_s if peak is not None else None
            ),
            ignition_index=(
                ignition.sample_index if ignition is not None else None
            ),
            burnout_index=(
                burnout.sample_index if burnout is not None else None
            ),
            peak_index=(
                peak.sample_index if peak is not None else None
            ),
            detection_method=detection_method,
        )
