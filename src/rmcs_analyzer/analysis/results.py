from dataclasses import dataclass
from typing import Optional


@dataclass
class EventResults:
    """
    Legacy-compatible event result container.

    This class remains available for compatibility with the existing
    analysis subsystems. The processing layer's EventSet is the
    authoritative event model for the application.
    """

    ignition_time_s: Optional[float] = None
    burnout_time_s: Optional[float] = None
    peak_time_s: Optional[float] = None

    ignition_index: Optional[int] = None
    burnout_index: Optional[int] = None
    peak_index: Optional[int] = None

    detection_method: str = ""


@dataclass
class ThrustResults:
    """
    Calculated thrust and impulse results.

    The current fields preserve the existing Phase 1 analysis API.
    Additional standardized-performance fields are reserved here so
    the authoritative Phase 2 reduction engine can expose its results
    without requiring another result-model redesign.

    These additional fields are intentionally not calculated yet.
    """

    # ---------------------------------------------------------
    # Existing Phase 1 metrics
    # ---------------------------------------------------------

    peak_thrust_N: Optional[float] = None
    peak_thrust_time_s: Optional[float] = None

    average_thrust_N: Optional[float] = None

    burn_time_s: Optional[float] = None
    total_impulse_Ns: Optional[float] = None

    time_to_peak_s: Optional[float] = None

    # ---------------------------------------------------------
    # Phase 2 standardized performance metrics
    # ---------------------------------------------------------
    #
    # These remain None until the industry-standard reduction
    # engine is implemented. Keeping them in the result model now
    # prevents the GUI, persistence, and comparison layers from
    # needing another structural change later.
    #

    threshold_percent: float = 5.0
    threshold_thrust_N: Optional[float] = None

    burn_start_5pct_time_s: Optional[float] = None
    burn_end_5pct_time_s: Optional[float] = None

    burn_time_5pct_s: Optional[float] = None

    average_thrust_5pct_N: Optional[float] = None

    initial_thrust_average_N: Optional[float] = None
    initial_thrust_window_s: Optional[float] = None

    total_impulse_valid_curve_Ns: Optional[float] = None
    normalized_impulse_Ns: Optional[float] = None

    impulse_class: Optional[str] = None

    designation: Optional[str] = None


@dataclass
class StatisticalResults:
    """Statistics describing the imported test data."""

    sample_count: int = 0
    sample_rate_hz: float = 0.0

    minimum_thrust_N: float = 0.0
    maximum_thrust_N: float = 0.0

    baseline_mean_N: Optional[float] = None
    baseline_std_N: Optional[float] = None


@dataclass
class MotorClassification:
    """Motor impulse classification results."""

    motor_class: Optional[str] = None

    lower_limit_Ns: Optional[float] = None
    upper_limit_Ns: Optional[float] = None

    description: str = ""


@dataclass
class AnalysisResults:
    """
    Complete set of analysis results for a test.

    Event detection is represented by the processing layer's
    EventSet in the current application. EventResults remains part
    of the model for compatibility with legacy analysis components
    while those components are transitioned to the authoritative
    processing/event architecture.
    """

    events: object
    thrust: ThrustResults
    statistics: StatisticalResults
    classification: MotorClassification
