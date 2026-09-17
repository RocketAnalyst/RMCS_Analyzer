import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import Qt
from PySide6.QtGui import QPen
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QStackedLayout,
)


class ThrustPlot(QFrame):
    """
    Interactive thrust-curve visualization.

    This component is responsible only for displaying data.
    It does not modify the underlying test data or perform
    motor analysis.

    When data is loaded, the initial X-axis view is automatically
    focused around the apparent motor firing region. The full
    dataset remains available through normal plot interaction.
    """

    # Amount of surrounding dead time shown around the apparent
    # motor firing region.
    AUTO_VIEW_MARGIN_S = 0.5

    # Fraction of peak thrust used to identify the active firing
    # region for the initial viewport.
    AUTO_VIEW_THRESHOLD = 0.02

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("graphPlaceholder")

        self.stack = QStackedLayout(self)
        self.stack.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#080e13")

        self.placeholder = self.create_placeholder()

        self.stack.addWidget(
            self.placeholder
        )

        self.stack.addWidget(
            self.plot
        )

        self.configure_plot()

        self.curve = None
        self.zero_line = None

    def create_placeholder(self):
        """Create the empty-state display."""

        frame = QFrame()
        frame.setObjectName(
            "graphPlaceholder"
        )

        layout = QStackedLayout(frame)

        content = QFrame()

        from PySide6.QtWidgets import (
            QVBoxLayout,
        )

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title = QLabel(
            "No Test Data Loaded"
        )
        title.setObjectName(
            "graphTitle"
        )

        description = QLabel(
            "Open an RMCS or compatible "
            "CSV file to display the "
            "thrust curve."
        )

        description.setObjectName(
            "graphDescription"
        )

        description.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        content_layout.addWidget(title)
        content_layout.addWidget(
            description
        )

        layout.addWidget(content)

        return frame

    def configure_plot(self):
        """Configure the appearance and behavior."""

        self.plot.setLabel(
            "bottom",
            "Time",
            units="s",
            color="#9aabb8",
        )

        self.plot.setLabel(
            "left",
            "Thrust",
            units="N",
            color="#9aabb8",
        )

        self.plot.showGrid(
            x=True,
            y=True,
            alpha=0.18,
        )

        self.plot.setMouseEnabled(
            x=True,
            y=True,
        )

        self.plot.setMenuEnabled(True)

        axis_pen = QPen("#526674")
        axis_pen.setWidth(1)

        for axis_name in (
            "bottom",
            "left",
        ):
            axis = self.plot.getAxis(
                axis_name
            )

            axis.setPen(axis_pen)
            axis.setTextPen(
                "#8396a5"
            )

        self.plot.setContentsMargins(
            10,
            10,
            10,
            10,
        )

    def set_data(
        self,
        time,
        thrust,
    ):
        """
        Display a thrust curve.

        The full dataset is plotted. The initial X-axis view is
        automatically focused around the apparent firing region,
        while preserving all data for later navigation.

        Parameters
        ----------
        time:
            Time values in seconds.

        thrust:
            Thrust values in Newtons.
        """

        time = np.asarray(
            time,
            dtype=float,
        )

        thrust = np.asarray(
            thrust,
            dtype=float,
        )

        if len(time) == 0 or len(thrust) == 0:
            self.clear()
            return

        if len(time) != len(thrust):
            raise ValueError(
                "Time and thrust arrays "
                "must have the same length."
            )

        self.plot.clear()

        curve_pen = pg.mkPen(
            color="#38a8ff",
            width=2,
        )

        self.curve = self.plot.plot(
            time,
            thrust,
            pen=curve_pen,
            name="Thrust",
        )

        zero_pen = pg.mkPen(
            color="#40515e",
            width=1,
            style=Qt.PenStyle.DashLine,
        )

        self.zero_line = pg.InfiniteLine(
            pos=0,
            angle=0,
            pen=zero_pen,
        )

        self.plot.addItem(
            self.zero_line,
            ignoreBounds=True,
        )

        # ---------------------------------------------------------
        # Set the Y-axis automatically.
        # ---------------------------------------------------------

        self.plot.enableAutoRange(
            axis="y",
            enable=True,
        )

        # ---------------------------------------------------------
        # Determine the apparent motor firing region.
        #
        # This affects only the initial viewport. It does not
        # modify, trim, or delete any samples.
        # ---------------------------------------------------------

        self.set_initial_view(
            time,
            thrust,
        )

        self.stack.setCurrentWidget(
            self.plot
        )

    def set_initial_view(
        self,
        time,
        thrust,
    ):
        """
        Focus the initial X-axis view around the apparent firing
        region.

        The firing region is identified using a small percentage
        of the maximum absolute thrust. If a useful firing region
        cannot be identified, the full dataset is displayed.
        """

        finite_mask = (
            np.isfinite(time)
            & np.isfinite(thrust)
        )

        if not np.any(finite_mask):
            self.plot.enableAutoRange(
                axis="x",
                enable=True,
            )
            return

        valid_time = time[
            finite_mask
        ]

        valid_thrust = thrust[
            finite_mask
        ]

        if len(valid_time) < 2:
            self.plot.enableAutoRange(
                axis="x",
                enable=True,
            )
            return

        peak_thrust = float(
            np.max(
                np.abs(valid_thrust)
            )
        )

        if not np.isfinite(peak_thrust) or peak_thrust <= 0:
            self.plot.enableAutoRange(
                axis="x",
                enable=True,
            )
            return

        threshold = (
            peak_thrust
            * self.AUTO_VIEW_THRESHOLD
        )

        active_mask = (
            np.abs(valid_thrust)
            >= threshold
        )

        active_indices = np.flatnonzero(
            active_mask
        )

        if len(active_indices) == 0:
            self.plot.enableAutoRange(
                axis="x",
                enable=True,
            )
            return

        firing_start = float(
            valid_time[
                active_indices[0]
            ]
        )

        firing_end = float(
            valid_time[
                active_indices[-1]
            ]
        )

        # Add visual margin without allowing the viewport to extend
        # beyond the actual recorded time range.

        view_start = max(
            float(valid_time[0]),
            firing_start
            - self.AUTO_VIEW_MARGIN_S,
        )

        view_end = min(
            float(valid_time[-1]),
            firing_end
            + self.AUTO_VIEW_MARGIN_S,
        )

        if view_end <= view_start:
            self.plot.enableAutoRange(
                axis="x",
                enable=True,
            )
            return

        self.plot.enableAutoRange(
            axis="x",
            enable=False,
        )

        self.plot.setXRange(
            view_start,
            view_end,
            padding=0,
        )

    def clear(self):
        """Return the plot to the empty state."""

        self.plot.clear()

        self.curve = None
        self.zero_line = None

        self.stack.setCurrentWidget(
            self.placeholder
        )

    def get_plot_widget(self):
        """Return the underlying PlotWidget."""

        return self.plot