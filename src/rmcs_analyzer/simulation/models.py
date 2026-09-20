"""Normalized simulation data models.

Simulation data is deliberately independent of any simulator-specific CSV
format.  Importers normalize source data into these models so the rest of the
application can work with a stable RMCS representation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class SimulationMetadata:
    """Metadata describing the imported simulation source."""

    source_path: str
    source_format: str = "CSV"
    simulator: str | None = None
    title: str | None = None
    extra: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SimulationData:
    """Normalized simulation channels used by RMCS Analyzer.

    Internal units are fixed regardless of source-file units:
      * time: seconds
      * thrust: Newtons
      * pressure: psi

    Thrust and pressure are optional because a valid simulation source may
    provide only one of the channels.
    """

    time_s: np.ndarray
    thrust_N: np.ndarray | None
    pressure_psi: np.ndarray | None
    metadata: SimulationMetadata

    def __post_init__(self) -> None:
        time = np.asarray(self.time_s, dtype=float)
        object.__setattr__(self, "time_s", time)

        if time.ndim != 1 or time.size == 0:
            raise ValueError("Simulation time must be a non-empty 1-D array.")
        if not np.all(np.isfinite(time)):
            raise ValueError("Simulation time contains non-finite values.")
        if np.any(np.diff(time) < 0):
            raise ValueError("Simulation time must be monotonically non-decreasing.")

        for name in ("thrust_N", "pressure_psi"):
            values = getattr(self, name)
            if values is None:
                continue
            values = np.asarray(values, dtype=float)
            if values.ndim != 1 or values.size != time.size:
                raise ValueError(f"{name} must be a 1-D array matching time length.")
            if not np.all(np.isfinite(values)):
                raise ValueError(f"{name} contains non-finite values.")
            object.__setattr__(self, name, values)

        if self.thrust_N is None and self.pressure_psi is None:
            raise ValueError("Simulation data must contain thrust and/or pressure.")

    @property
    def duration_s(self) -> float:
        """Return the simulation duration in seconds."""
        return float(self.time_s[-1] - self.time_s[0])

    @property
    def has_thrust(self) -> bool:
        return self.thrust_N is not None

    @property
    def has_pressure(self) -> bool:
        return self.pressure_psi is not None

    @property
    def source_name(self) -> str:
        return Path(self.metadata.source_path).name
