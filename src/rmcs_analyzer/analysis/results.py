from dataclasses import dataclass
from typing import Optional


@dataclass
class EventResults:
    """Results from ignition, burnout, and peak event detection."""

    ignition_time_s: Optional[float] = None
    burnout_time_s: Optional[float] = None
    peak_time_s: Optional[float] = None

    ignition_index: Optional[int] = None
    burnout_index: Optional[int] = None
    peak_index: Optional[int] = None

    detection_method: str = ""


@dataclass
class ThrustResults:
    """Calculated thrust and impulse results."""

    peak_thrust_N: Optional[float] = None
    peak_thrust_time_s: Optional[float] = None

    average_thrust_N: Optional[float] = None

    burn_time_s: Optional[float] = None
    total_impulse_Ns: Optional[float] = None

    time_to_peak_s: Optional[float] = None


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
    """Complete set of analysis results for a test."""

    events: EventResults
    thrust: ThrustResults
    statistics: StatisticalResults
    classification: MotorClassification