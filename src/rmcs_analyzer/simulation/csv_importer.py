"""CSV importer for BurnSim/OpenMotor-style simulation output."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np

from .models import SimulationData, SimulationMetadata


class SimulationImportError(ValueError):
    """Raised when a simulation CSV cannot be interpreted by RMCS."""


def _normalize_header(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _unit(header: str) -> str | None:
    match = re.search(r"\(([^()]*)\)", header)
    return match.group(1).strip().lower() if match else None


def _find_column(headers: list[str], candidates: tuple[str, ...]) -> int | None:
    normalized = [_normalize_header(h) for h in headers]
    for candidate in candidates:
        candidate_norm = _normalize_header(candidate)
        for index, header in enumerate(normalized):
            if header == candidate_norm:
                return index
    return None


def _find_time_column(headers: list[str]) -> int | None:
    exact = _find_column(headers, ("time", "time (s)"))
    if exact is not None:
        return exact
    for i, header in enumerate(headers):
        n = _normalize_header(header)
        if n.startswith("time ") or n == "time":
            return i
    return None


def _find_thrust_column(headers: list[str]) -> int | None:
    exact = _find_column(headers, ("thrust", "thrust (n)", "thrust (lbf)"))
    if exact is not None:
        return exact
    for i, header in enumerate(headers):
        n = _normalize_header(header)
        if n.startswith("thrust") or n == "force":
            return i
    return None


def _find_pressure_column(headers: list[str]) -> int | None:
    exact = _find_column(
        headers,
        (
            "pressure",
            "pressure (psi)",
            "pressure (pa)",
            "chamber pressure",
            "chamber pressure (psi)",
            "chamber pressure (pa)",
        ),
    )
    if exact is not None:
        return exact
    for i, header in enumerate(headers):
        n = _normalize_header(header)
        if "chamber pressure" in n or n.startswith("pressure"):
            return i
    return None


def _convert_time(values: np.ndarray, unit: str | None) -> np.ndarray:
    unit = (unit or "s").lower()
    if unit in {"s", "sec", "second", "seconds"}:
        return values
    if unit in {"ms", "millisecond", "milliseconds"}:
        return values / 1000.0
    if unit in {"us", "microsecond", "microseconds"}:
        return values / 1_000_000.0
    raise SimulationImportError(f"Unsupported time unit: {unit}")


def _convert_thrust(values: np.ndarray, unit: str | None) -> np.ndarray:
    unit = (unit or "n").lower()
    if unit in {"n", "newton", "newtons"}:
        return values
    if unit in {"lbf", "lb f", "pound force", "pounds force"}:
        return values * 4.4482216152605
    if unit in {"kgf", "kilogram force", "kilogram-force"}:
        return values * 9.80665
    raise SimulationImportError(f"Unsupported thrust unit: {unit}")


def _convert_pressure(values: np.ndarray, unit: str | None) -> np.ndarray:
    unit = (unit or "psi").lower()
    if unit in {"psi", "psia", "psi a"}:
        return values
    if unit in {"pa", "pascal", "pascals"}:
        return values / 6894.757293168
    if unit in {"kpa"}:
        return values * 1000.0 / 6894.757293168
    if unit in {"mpa"}:
        return values * 1_000_000.0 / 6894.757293168
    if unit in {"bar", "bars"}:
        return values * 14.503773773
    if unit in {"atm", "atmosphere", "atmospheres"}:
        return values * 14.6959487755
    raise SimulationImportError(f"Unsupported pressure unit: {unit}")


def _read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    # Simulator exports and our fixtures may contain comment lines before the
    # actual header. Skip blank/comment-only lines before handing the content
    # to csv.DictReader-like parsing.
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        lines = [line for line in handle if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        raise SimulationImportError("Simulation CSV is empty.")

    reader = csv.reader(lines)
    rows = list(reader)
    headers = [cell.strip() for cell in rows[0]]
    data = [row for row in rows[1:] if len(row) == len(headers)]
    return headers, data


def import_simulation_csv(path: str | Path) -> SimulationData:
    """Import a BurnSim/OpenMotor-style CSV into normalized RMCS units."""
    source = Path(path)
    if not source.is_file():
        raise SimulationImportError(f"Simulation file not found: {source}")

    headers, rows = _read_csv(source)
    time_index = _find_time_column(headers)
    thrust_index = _find_thrust_column(headers)
    pressure_index = _find_pressure_column(headers)

    if time_index is None:
        raise SimulationImportError("No recognizable time column was found.")
    if thrust_index is None and pressure_index is None:
        raise SimulationImportError("No recognizable thrust or pressure column was found.")

    def column(index: int) -> np.ndarray:
        try:
            return np.asarray([float(row[index]) for row in rows], dtype=float)
        except (ValueError, IndexError) as exc:
            raise SimulationImportError("Simulation CSV contains a non-numeric data value.") from exc

    time = _convert_time(column(time_index), _unit(headers[time_index]))
    thrust = None if thrust_index is None else _convert_thrust(column(thrust_index), _unit(headers[thrust_index]))
    pressure = None if pressure_index is None else _convert_pressure(column(pressure_index), _unit(headers[pressure_index]))

    if np.any(np.diff(time) < 0):
        raise SimulationImportError("Simulation time must be monotonically non-decreasing.")

    # Heuristic source identification is metadata only; it never changes
    # parsing behavior.
    header_text = " ".join(_normalize_header(h) for h in headers)
    if "openmotor" in header_text or "chamber pressure" in header_text:
        simulator = "OpenMotor"
    elif "burnsim" in header_text:
        simulator = "BurnSim"
    else:
        simulator = None

    metadata = SimulationMetadata(
        source_path=str(source),
        source_format="CSV",
        simulator=simulator,
        title=source.stem,
    )
    return SimulationData(
        time_s=time,
        thrust_N=thrust,
        pressure_psi=pressure,
        metadata=metadata,
    )
