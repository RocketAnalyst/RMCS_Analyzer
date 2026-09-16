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
    It does not perform motor analysis or read files.
    """

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

        self.plot.enableAutoRange(
            axis="xy",
            enable=True,
        )

        self.stack.setCurrentWidget(
            self.plot
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