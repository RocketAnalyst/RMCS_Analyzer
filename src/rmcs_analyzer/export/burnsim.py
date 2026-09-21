"""BurnSim experimental test-data CSV export.

Exports the measured RMCS time/pressure/thrust trace in the simple
BurnSim test-data format established for RMCS: Time, Pressure, Thrust.

The export intentionally contains measured data only. It does not export
RMCS simulation channels or derived engineering metrics.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def _field(obj: Any, name: str, default=None):
    return getattr(obj, name, default) if obj is not None else default


def _trace_rows(test: Any) -> list[tuple[float, float | None, float]]:
    """Return the complete measured trace as (time_s, pressure_psi, thrust_N).

    RMCS stores the authoritative measured channels on ``test.data``.
    ``AnalysisResults`` contains calculated metrics and event information,
    but it is not the source of the raw time-series arrays.
    """
    data = _field(test, "data")
    if data is None:
        return []

    times = _field(data, "time_s", None)
    thrust_values = _field(data, "thrust_N", None)
    pressure_values = _field(data, "pressure_psi", None)

    def as_list(value):
        if value is None:
            return []
        try:
            return list(value)
        except TypeError:
            return []

    t = as_list(times)
    f = as_list(thrust_values)
    p = as_list(pressure_values)

    if not t or not f or len(t) != len(f):
        return []

    rows = []
    for i, (time_value, thrust_value) in enumerate(zip(t, f)):
        try:
            time_s = float(time_value)
            thrust_n = float(thrust_value)
        except (TypeError, ValueError):
            continue

        pressure_psi = None
        if i < len(p):
            try:
                value = float(p[i])
                if value == value:
                    pressure_psi = value
            except (TypeError, ValueError):
                pressure_psi = None

        rows.append((time_s, pressure_psi, thrust_n))

    return rows


def export_burnsim_csv(test: Any, output_path: str | Path) -> Path:
    """Export one analyzed RMCS test as BurnSim test-data CSV.

    Columns are:
      Time, Pressure, Thrust

    Time is seconds, pressure is psi, and thrust is newtons.
    The complete measured recording is retained, including pre-ignition
    and post-burnout samples.
    """
    rows = _trace_rows(test)
    if not rows:
        raise ValueError("The test does not contain a complete measured thrust trace.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Time", "Pressure", "Thrust"])
        for time_s, pressure_psi, thrust_n in rows:
            writer.writerow([
                f"{time_s:.6f}",
                "" if pressure_psi is None else f"{pressure_psi:.6f}",
                f"{thrust_n:.6f}",
            ])

    return output
