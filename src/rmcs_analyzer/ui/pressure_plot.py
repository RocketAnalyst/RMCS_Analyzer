import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QStackedLayout, QVBoxLayout


class PressurePlot(QFrame):
    """Interactive pressure-vs-time visualization for a single test."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("graphPlaceholder")

        self.stack = QStackedLayout(self)
        self.stack.setContentsMargins(0, 0, 0, 0)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#080e13")

        self.placeholder = self._create_placeholder()
        self.stack.addWidget(self.placeholder)
        self.stack.addWidget(self.plot)

        self._configure_plot()
        self.simulation_curve = None
        self.simulation_time = None
        self.simulation_pressure = None
        self._show_simulation = False

    def _create_placeholder(self):
        frame = QFrame()
        frame.setObjectName("graphPlaceholder")
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("No Pressure Data Available")
        title.setObjectName("graphTitle")
        description = QLabel(
            "This test does not contain a valid pressure channel."
        )
        description.setObjectName("graphDescription")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(description)
        return frame

    def _configure_plot(self):
        self.plot.setLabel("bottom", "Time", units="s", color="#9aabb8")
        self.plot.setLabel("left", "Pressure", units="psi", color="#9aabb8")
        self.plot.showGrid(x=True, y=True, alpha=0.18)
        self.plot.setMouseEnabled(x=True, y=True)
        self.plot.setMenuEnabled(True)

    def set_data(self, time_s, pressure_psi, ignition_time_s=None,
                 burnout_time_s=None, recording_end_time_s=None):
        time = np.asarray(time_s, dtype=float)
        pressure = np.asarray(pressure_psi, dtype=float)

        if len(time) == 0 or len(pressure) == 0 or len(time) != len(pressure):
            self.clear()
            return

        mask = np.isfinite(time) & np.isfinite(pressure)
        time = time[mask]
        pressure = pressure[mask]

        if len(time) == 0:
            self.clear()
            return

        self.plot.clear()
        self.plot.plot(
            time,
            pressure,
            pen=pg.mkPen("#6fb7ff", width=2),
            name="Recorded Pressure",
        )

        if (
            self._show_simulation
            and self.simulation_time is not None
            and self.simulation_pressure is not None
            and len(self.simulation_time) == len(self.simulation_pressure)
        ):
            sim_mask = (
                np.isfinite(self.simulation_time)
                & np.isfinite(self.simulation_pressure)
            )
            if np.any(sim_mask):
                self.plot.plot(
                    self.simulation_time[sim_mask],
                    self.simulation_pressure[sim_mask],
                    pen=pg.mkPen("#ffb84d", width=2, style=Qt.PenStyle.DashLine),
                    name="Simulation Pressure",
                )

        if np.all(np.isfinite(pressure)):
            self.plot.addLine(y=0, pen=pg.mkPen("#526674", width=1))

        for value, label, pen in (
            (ignition_time_s, "Ignition", "#65d18a"),
            (burnout_time_s, "Burnout", "#ff6b6b"),
            (recording_end_time_s, "Recording End", "#d0d7de"),
        ):
            if value is not None and np.isfinite(value):
                line = pg.InfiniteLine(
                    pos=float(value),
                    angle=90,
                    pen=pg.mkPen(pen, width=1, style=Qt.PenStyle.DashLine),
                )
                line.setZValue(10)
                self.plot.addItem(line)

        self.plot.enableAutoRange()
        self.stack.setCurrentWidget(self.plot)

    def _update_simulation_curve(self):
        """Add, remove, or refresh the simulation curve without rebuilding measured data or event markers."""
        if self.simulation_curve is not None:
            try:
                self.plot.removeItem(self.simulation_curve)
            except Exception:
                pass
            self.simulation_curve = None

        if (
            not self._show_simulation
            or self.simulation_time is None
            or self.simulation_pressure is None
            or len(self.simulation_time) != len(self.simulation_pressure)
        ):
            return

        sim_mask = (
            np.isfinite(self.simulation_time)
            & np.isfinite(self.simulation_pressure)
        )

        if not np.any(sim_mask):
            return

        self.simulation_curve = self.plot.plot(
            self.simulation_time[sim_mask],
            self.simulation_pressure[sim_mask],
            pen=pg.mkPen(
                "#ffb84d",
                width=2,
                style=Qt.PenStyle.DashLine,
            ),
            name="Simulation Pressure",
        )
        self.simulation_curve.setZValue(5)

    def set_simulation(self, time_s=None, pressure_psi=None, visible=False):
        """Set the optional project-level simulation pressure curve."""
        if time_s is None or pressure_psi is None:
            self.simulation_time = None
            self.simulation_pressure = None
        else:
            time = np.asarray(time_s, dtype=float)
            pressure = np.asarray(pressure_psi, dtype=float)
            if len(time) != len(pressure):
                raise ValueError("Simulation time and pressure arrays must have the same length.")
            self.simulation_time = time
            self.simulation_pressure = pressure

        self._show_simulation = bool(visible)
        self._update_simulation_curve()

    def set_simulation_visible(self, visible):
        """Toggle simulation visibility without rebuilding measured data or event markers."""
        self._show_simulation = bool(visible)
        self._update_simulation_curve()

    def clear(self):
        self.plot.clear()
        self.stack.setCurrentWidget(self.placeholder)
