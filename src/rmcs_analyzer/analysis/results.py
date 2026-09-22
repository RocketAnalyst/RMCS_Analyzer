from dataclasses import dataclass
from typing import Optional

from ..processing.event_model import EventSet


@dataclass
class EventResults:
    """
    Legacy event result container retained only for project-file migration.

    Current runtime event data uses processing.event_model.EventSet.
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
    Authoritative calculated thrust and motor-performance results.

    Core fields contain the standardized performance reduction. Explicit
    5% fields are retained to make the standardized burn-window definition
    unambiguous in the UI, exports, and project persistence.
    """

    # ---------------------------------------------------------
    # Core standardized metrics
    # ---------------------------------------------------------

    peak_thrust_N: Optional[float] = None
    peak_thrust_time_s: Optional[float] = None

    average_thrust_N: Optional[float] = None

    burn_time_s: Optional[float] = None
    total_impulse_Ns: Optional[float] = None

    time_to_peak_s: Optional[float] = None

    # ---------------------------------------------------------
    # Standardized burn-window and extension metrics
    # ---------------------------------------------------------

    threshold_percent: float = 5.0
    threshold_thrust_N: Optional[float] = None

    burn_start_5pct_time_s: Optional[float] = None
    burn_end_5pct_time_s: Optional[float] = None

    burn_time_5pct_s: Optional[float] = None

    average_thrust_5pct_N: Optional[float] = None

    initial_thrust_average_N: Optional[float] = None
    initial_thrust_window_s: Optional[float] = None

    thrust_rise_rate_N_per_s: Optional[float] = None
    thrust_decay_rate_N_per_s: Optional[float] = None

    # Performance extensions requiring metadata / auxiliary channels
    isp_s: Optional[float] = None
    isp_status: str = "unavailable"

    cstar_m_per_s: Optional[float] = None
    cstar_status: str = "unavailable"

    average_chamber_pressure_psi: Optional[float] = None
    peak_pressure_psi: Optional[float] = None
    average_mass_flow_kg_per_s: Optional[float] = None

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

    Event detection is represented by the processing layer's EventSet.
    EventResults is retained separately only so older project files can be
    migrated into the current EventSet representation.
    """

    events: EventSet
    thrust: ThrustResults
    statistics: StatisticalResults
    classification: MotorClassification
