from .events import EventDetector
from .impulse import ThrustAnalyzer
from .motor_class import MotorClassCalculator
from .results import AnalysisResults
from .statistics import StatisticsAnalyzer
from ..processing.event_model import EventSet


class AnalysisEngine:
    """
    Coordinates analysis calculations for prepared test data.

    Event detection normally occurs during the processing pipeline.
    When an EventSet is supplied, it is used as the authoritative
    event source.

    The existing thrust-analysis subsystem still expects the
    legacy EventResults interface, so the EventDetector's legacy
    detect() result is retained internally for compatibility.

    The engine does not modify the supplied TestData.
    """

    def __init__(
        self,
        event_detector=None,
        thrust_analyzer=None,
        statistics_analyzer=None,
        motor_class_calculator=None,
    ):
        self.event_detector = (
            event_detector
            or EventDetector()
        )

        self.thrust_analyzer = (
            thrust_analyzer
            or ThrustAnalyzer()
        )

        self.statistics_analyzer = (
            statistics_analyzer
            or StatisticsAnalyzer()
        )

        self.motor_class_calculator = (
            motor_class_calculator
            or MotorClassCalculator()
        )

    def analyze(
        self,
        test_data,
        events: EventSet | None = None,
    ):
        """
        Analyze prepared test data.

        Args:
            test_data:
                Prepared TestData to analyze.

            events:
                Optional EventSet produced by the processing
                pipeline.

        Returns:
            AnalysisResults containing events, thrust results,
            statistics, and motor classification.
        """

        # ---------------------------------------------------------
        # Event detection
        # ---------------------------------------------------------

        if events is None:
            # Generate both representations from the same detection
            # pass. The EventSet is exposed to the rest of the
            # application while EventResults remains available to
            # legacy analysis code.
            legacy_events = self.event_detector.detect(
                test_data
            )

            events = self.event_detector.detect_events(
                test_data
            )
        else:
            # The supplied EventSet is authoritative.
            #
            # The existing ThrustAnalyzer still requires the
            # legacy EventResults representation. Generate that
            # compatibility representation here.
            legacy_events = self.event_detector.detect(
                test_data
            )

        # ---------------------------------------------------------
        # Thrust analysis
        # ---------------------------------------------------------

        thrust_results = (
            self.thrust_analyzer.analyze(
                test_data,
                legacy_events,
            )
        )

        # ---------------------------------------------------------
        # General statistics
        # ---------------------------------------------------------

        statistics = (
            self.statistics_analyzer.analyze(
                test_data
            )
        )

        # ---------------------------------------------------------
        # Motor classification
        # ---------------------------------------------------------

        if (
            thrust_results.total_impulse_Ns
            is not None
        ):
            classification = (
                self.motor_class_calculator.classify(
                    thrust_results.total_impulse_Ns
                )
            )
        else:
            classification = (
                self.motor_class_calculator.classify(
                    -1
                )
            )

        # ---------------------------------------------------------
        # Combined analysis result
        # ---------------------------------------------------------

        return AnalysisResults(
            events=events,
            thrust=thrust_results,
            statistics=statistics,
            classification=classification,
        )