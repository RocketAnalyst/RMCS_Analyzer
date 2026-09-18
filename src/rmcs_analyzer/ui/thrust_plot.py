import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import Qt
from PySide6.QtGui import QPen
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QStackedLayout,
    QVBoxLayout,
)


class ThrustPlot(QFrame):
    """
    Interactive thrust-curve visualization.

    This component displays the processed thrust data without
    modifying the underlying TestData.

    The plot can optionally receive a detected burnout time. When
    supplied, the motor-burn portion and post-burn recorded data are
    displayed separately:

        motor thrust     -> normal thrust curve
        post-burn data   -> retained, but visually distinguished

    This keeps post-burn load-cell behavior available without
    presenting it as motor thrust.
    """

    AUTO_VIEW_MARGIN_S = 0.5
    AUTO_VIEW_THRESHOLD = 0.02

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("graphPlaceholder")

        self.stack = QStackedLayout(self)
        self.stack.setContentsMargins(0, 0, 0, 0)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#080e13")

        self.placeholder = self.create_placeholder()

        self.stack.addWidget(self.placeholder)
        self.stack.addWidget(self.plot)

        self.configure_plot()

        self.curve = None
        self.post_burn_curve = None
        self.zero_line = None
        self.burnout_line = None
        self.burn_start_line = None
        self.burn_end_line = None
        self.peak_marker = None

    def create_placeholder(self):
        """Create the empty-state display."""

        frame = QFrame()
        frame.setObjectName("graphPlaceholder")

        layout = QStackedLayout(frame)

        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title = QLabel("No Test Data Loaded")
        title.setObjectName("graphTitle")

        description = QLabel(
            "Open an RMCS or compatible CSV file to display the "
            "thrust curve."
        )
        description.setObjectName("graphDescription")
        description.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        content_layout.addWidget(title)
        content_layout.addWidget(description)

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

        for axis_name in ("bottom", "left"):
            axis = self.plot.getAxis(axis_name)
            axis.setPen(axis_pen)
            axis.setTextPen("#8396a5")

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
        burnout_time_s=None,
        burn_start_5pct_time_s=None,
        burn_end_5pct_time_s=None,
        peak_time_s=None,
        peak_thrust_N=None,
    ):
        """
        Display a thrust curve.

        Parameters
        ----------
        time:
            Time values in seconds.

        thrust:
            Processed thrust values in Newtons.

        burnout_time_s:
            Optional detected burnout time in the same time coordinate
            system as ``time``.

            When supplied, data after burnout is retained on the plot
            as a separate post-burn recording rather than being
            presented as motor thrust.
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
                "Time and thrust arrays must have the same length."
            )

        self.plot.clear()

        # ---------------------------------------------------------
        # Determine whether a valid burnout boundary was supplied.
        # ---------------------------------------------------------

        valid_burnout = (
            burnout_time_s is not None
            and np.isfinite(burnout_time_s)
            and burnout_time_s >= time[0]
            and burnout_time_s <= time[-1]
        )

        valid_burn_start = (
            burn_start_5pct_time_s is not None
            and np.isfinite(burn_start_5pct_time_s)
            and burn_start_5pct_time_s >= time[0]
            and burn_start_5pct_time_s <= time[-1]
        )

        valid_burn_end = (
            burn_end_5pct_time_s is not None
            and np.isfinite(burn_end_5pct_time_s)
            and burn_end_5pct_time_s >= time[0]
            and burn_end_5pct_time_s <= time[-1]
        )

        # ---------------------------------------------------------
        # Motor-burn curve
        #
        # Include samples through the detected burnout boundary.
        # ---------------------------------------------------------

        if valid_burnout:
            motor_mask = (
                np.isfinite(time)
                & np.isfinite(thrust)
                & (time <= burnout_time_s)
            )

            post_burn_mask = (
                np.isfinite(time)
                & np.isfinite(thrust)
                & (time > burnout_time_s)
            )
        else:
            motor_mask = (
                np.isfinite(time)
                & np.isfinite(thrust)
            )

            post_burn_mask = np.zeros(
                len(time),
                dtype=bool,
            )

        if np.any(motor_mask):
            curve_pen = pg.mkPen(
                color="#38a8ff",
                width=2,
            )

            self.curve = self.plot.plot(
                time[motor_mask],
                thrust[motor_mask],
                pen=curve_pen,
                name="Motor Thrust",
            )

        # ---------------------------------------------------------
        # Post-burn recording
        #
        # Keep these samples visible, but do not visually imply that
        # they are motor thrust. A thinner/dashed curve makes the
        # distinction explicit.
        # ---------------------------------------------------------

        if np.any(post_burn_mask):
            post_burn_pen = pg.mkPen(
                color="#687b89",
                width=1,
                style=Qt.PenStyle.DashLine,
            )

            self.post_burn_curve = self.plot.plot(
                time[post_burn_mask],
                thrust[post_burn_mask],
                pen=post_burn_pen,
                name="Post-Burn Recording",
            )

        # ---------------------------------------------------------
        # Zero reference
        # ---------------------------------------------------------

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
        # Standardized 5% performance boundaries
        #
        # These are analysis boundaries, not data-trimming boundaries.
        # The complete recorded curve remains visible.
        # ---------------------------------------------------------

        analysis_pen = pg.mkPen(
            color="#8fa8b8",
            width=1,
            style=Qt.PenStyle.DashLine,
        )

        if valid_burn_start:
            self.burn_start_line = pg.InfiniteLine(
                pos=float(burn_start_5pct_time_s),
                angle=90,
                pen=analysis_pen,
            )
            self.plot.addItem(
                self.burn_start_line,
                ignoreBounds=True,
            )

        if valid_burn_end:
            self.burn_end_line = pg.InfiniteLine(
                pos=float(burn_end_5pct_time_s),
                angle=90,
                pen=analysis_pen,
            )
            self.plot.addItem(
                self.burn_end_line,
                ignoreBounds=True,
            )

        # ---------------------------------------------------------
        # Peak thrust marker
        # ---------------------------------------------------------

        valid_peak = (
            peak_time_s is not None
            and peak_thrust_N is not None
            and np.isfinite(peak_time_s)
            and np.isfinite(peak_thrust_N)
            and peak_time_s >= time[0]
            and peak_time_s <= time[-1]
        )

        if valid_peak:
            self.peak_marker = pg.ScatterPlotItem(
                [float(peak_time_s)],
                [float(peak_thrust_N)],
                size=9,
                pen=pg.mkPen("#38a8ff", width=2),
                brush=pg.mkBrush("#080e13"),
            )
            self.plot.addItem(
                self.peak_marker,
                ignoreBounds=True,
            )

        # ---------------------------------------------------------
        # Recorded test-end marker
        #
        # This is the end of the recorded data/event timeline. It is
        # deliberately distinct from the standardized 5% burn-end.
        # ---------------------------------------------------------

        if valid_burnout:
            test_end_pen = pg.mkPen(
                color="#687b89",
                width=1,
                style=Qt.PenStyle.DotLine,
            )
            self.burnout_line = pg.InfiniteLine(
                pos=float(burnout_time_s),
                angle=90,
                pen=test_end_pen,
            )
            self.plot.addItem(
                self.burnout_line,
                ignoreBounds=True,
            )

        # ---------------------------------------------------------
        # Y-axis
        # ---------------------------------------------------------

        self.plot.enableAutoRange(
            axis="y",
            enable=True,
        )

        # ---------------------------------------------------------
        # Initial X-axis view
        # ---------------------------------------------------------

        self.set_initial_view(
            time,
            thrust,
            burnout_time_s=(
                float(burnout_time_s)
                if valid_burnout
                else None
            ),
        )

        self.stack.setCurrentWidget(
            self.plot
        )

    def set_initial_view(
        self,
        time,
        thrust,
        burnout_time_s=None,
        burn_start_5pct_time_s=None,
        burn_end_5pct_time_s=None,
        peak_time_s=None,
        peak_thrust_N=None,
    ):
        """
        Focus the initial X-axis view around the motor firing region.

        If burnout is known, it is used as the right-hand boundary
        of the motor firing region. Otherwise the previous signal-
        based fallback is used.
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

        valid_time = time[finite_mask]
        valid_thrust = thrust[finite_mask]

        if len(valid_time) < 2:
            self.plot.enableAutoRange(
                axis="x",
                enable=True,
            )
            return

        # ---------------------------------------------------------
        # Preferred view: use detected burnout.
        # ---------------------------------------------------------

        if (
            burnout_time_s is not None
            and np.isfinite(burnout_time_s)
            and burnout_time_s >= valid_time[0]
            and burnout_time_s <= valid_time[-1]
        ):
            firing_start = float(valid_time[0])
            firing_end = float(burnout_time_s)

        else:
            # -----------------------------------------------------
            # Fallback: identify the apparent firing region from
            # positive thrust rather than absolute thrust.
            #
            # Negative post-burn values must not expand the initial
            # motor viewport.
            # -----------------------------------------------------

            peak_thrust = float(
                np.max(
                    np.maximum(
                        valid_thrust,
                        0.0,
                    )
                )
            )

            if (
                not np.isfinite(peak_thrust)
                or peak_thrust <= 0
            ):
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
                valid_thrust >= threshold
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

        view_start = max(
            float(valid_time[0]),
            firing_start - self.AUTO_VIEW_MARGIN_S,
        )

        view_end = min(
            float(valid_time[-1]),
            firing_end + self.AUTO_VIEW_MARGIN_S,
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
        self.post_burn_curve = None
        self.zero_line = None
        self.burnout_line = None
        self.burn_start_line = None
        self.burn_end_line = None
        self.peak_marker = None

        self.stack.setCurrentWidget(
            self.placeholder
        )

    def get_plot_widget(self):
        """Return the underlying PlotWidget."""

        return self.plot