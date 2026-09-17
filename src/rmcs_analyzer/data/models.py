from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class TestMetadata:
    """Metadata associated with a motor test."""

    source_file: str = ""
    rmcs_version: Optional[str] = None
    test_number: Optional[int] = None
    calibration_counts_per_newton: Optional[float] = None
    tare_raw: Optional[int] = None

    motor_designation: str = ""
    motor_type: str = ""
    manufacturer: str = ""
    builder: str = ""
    case_material: str = ""
    test_date: str = ""
    test_stand: str = ""
    test_operator: str = ""
    location: str = ""

    motor_diameter: Optional[float] = None
    motor_length: Optional[float] = None
    initial_mass: Optional[float] = None
    propellant_mass: Optional[float] = None
    propellant_type: str = ""

    nozzle_throat: Optional[float] = None
    nozzle_exit: Optional[float] = None
    nozzle_material: str = ""

    load_cell: str = ""
    load_cell_calibration: str = ""
    pressure_sensor: str = ""
    pressure_sensor_calibration: str = ""
    sample_rate_hz: Optional[float] = None

    notes: str = ""


@dataclass
class TestData:
    """
    Standardized time-series test data.

    Time is stored internally in seconds.
    Thrust is stored internally in Newtons.
    Pressure is stored internally in PSI.

    The original acquisition time is preserved separately from an
    optional test-stand-calibrated time.
    """

    time_s: np.ndarray
    thrust_N: np.ndarray

    calibrated_time_s: Optional[np.ndarray] = None
    raw_thrust_N: Optional[np.ndarray] = None
    prop_loss_kg: Optional[np.ndarray] = None
    pressure_psi: Optional[np.ndarray] = None

    delta: Optional[np.ndarray] = None
    state: Optional[np.ndarray] = None

    metadata: TestMetadata = field(
        default_factory=TestMetadata
    )

    @property
    def sample_count(self) -> int:
        """Return the number of samples."""

        return len(self.time_s)

    @property
    def duration_s(self) -> float:
        """Return total recording duration."""

        if self.sample_count < 2:
            return 0.0

        return float(
            self.time_s[-1] - self.time_s[0]
        )

    @property
    def sample_rate_hz(self) -> float:
        """
        Estimate the sampling rate from the original time data.
        """

        if self.sample_count < 2:
            return 0.0

        duration = self.duration_s

        if duration <= 0:
            return 0.0

        return float(
            (self.sample_count - 1) / duration
        )

    @property
    def minimum_thrust_N(self) -> float:
        """Return minimum recorded thrust."""

        if self.sample_count == 0:
            return 0.0

        return float(np.min(self.thrust_N))

    @property
    def maximum_thrust_N(self) -> float:
        """Return maximum recorded thrust."""

        if self.sample_count == 0:
            return 0.0

        return float(np.max(self.thrust_N))