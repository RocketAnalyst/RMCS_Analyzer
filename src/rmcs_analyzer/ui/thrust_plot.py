import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPen
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMenu,
    QStackedLayout,
    QVBoxLayout,
    QGraphicsTextItem,
)



class DraggableEventLabel(QGraphicsTextItem):
    """Screen-space event label that can be repositioned by the user."""

    def __init__(self, event_name, moved_callback=None):
        super().__init__()
        self.event_name = event_name
        self.moved_callback = moved_callback

        self.setFlag(
            self.GraphicsItemFlag.ItemIgnoresTransformations,
            True,
        )
        self.setFlag(
            self.GraphicsItemFlag.ItemIsMovable,
            True,
        )
        self.setAcceptedMouseButtons(
            Qt.MouseButton.LeftButton
        )

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

        if self.moved_callback is not None:
            self.moved_callback(
                self.event_name,
                self.pos(),
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

        self.plot.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.plot.customContextMenuRequested.connect(
            self._show_plot_context_menu
        )

        self.curve = None
        self.post_burn_curve = None
        self.zero_line = None
        self.ignition_line = None
        self.burnout_line = None
        self.recording_end_line = None
        self.peak_marker = None
        self.ignition_label = None
        self.burnout_label = None
        self.recording_end_label = None
        self.peak_label = None
        self._event_labels = []

        # Event-label presentation state. Offsets are stored in scene
        # pixels so manual positioning survives zooming and panning.
        self._label_offsets = {}
        self._show_event_markers = True

        # Keep event annotations synchronized with zooming, panning,
        # and resizing. Labels are screen-positioned so they cannot
        # drift into the thrust curve or into one another.
        self.plot.getPlotItem().vb.sigRangeChanged.connect(
            self._update_event_labels
        )

        # Interactive inspection state.
        self.data_time = None
        self.data_thrust = None
        self.hover_cursor = None
        self.hover_marker = None
        self.hover_readout = None
        self.playback_cursor = None

        self.configure_hover_inspection()

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

    def _remove_event_labels(self):
        """Remove all screen-positioned event annotation labels."""

        scene = self.plot.scene()

        for item in self._event_labels:
            try:
                scene.removeItem(item)
            except Exception:
                pass

        self._event_labels = []

        self.ignition_label = None
        self.burnout_label = None
        self.recording_end_label = None
        self.peak_label = None

    def _create_event_label(self, text, color, event_name):
        """Create a draggable, screen-positioned event annotation label."""

        item = DraggableEventLabel(
            event_name,
            moved_callback=self._store_label_position,
        )
        item.setPlainText(text)
        item.setDefaultTextColor(QColor(color))

        font = QFont()
        font.setPointSize(10)
        item.setFont(font)

        item.setZValue(1000)
        item.setToolTip(
            "Drag to reposition this marker label"
        )

        self.plot.scene().addItem(item)
        self._event_labels.append(item)

        return item

    def _update_event_labels(self, *args):
        """
        Position event labels in a stable screen-space annotation band.

        Labels follow their event's X position but use fixed screen-space
        rows and user-adjustable pixel offsets. This keeps them readable
        during zooming and panning.
        """

        if not self._event_labels or not self._show_event_markers:
            return

        vb = self.plot.getPlotItem().vb
        rect = vb.sceneBoundingRect()

        if rect.width() <= 0 or rect.height() <= 0:
            return

        label_items = (
            ("ignition", self.ignition_label),
            ("peak", self.peak_label),
            ("burnout", self.burnout_label),
            ("recording_end", self.recording_end_label),
        )

        specs = []

        # Separate ignition/peak and burnout/end-of-recording by default.
        preferred_rows = {
            "ignition": 0,
            "peak": 1,
            "burnout": 0,
            "recording_end": 1,
        }

        for name, item in label_items:
            if item is None:
                continue

            x_value = self._event_x.get(name)
            if x_value is None or not np.isfinite(x_value):
                continue

            scene_point = vb.mapViewToScene(
                QPointF(float(x_value), 0.0)
            )

            width = item.boundingRect().width()
            height = item.boundingRect().height()

            default_left = (
                scene_point.x() - width / 2.0
            )

            offset = self._label_offsets.get(
                name,
                (0.0, 0.0),
            )

            left = (
                default_left
                + float(offset[0])
            )

            left = max(
                rect.left() + 4.0,
                min(
                    left,
                    rect.right() - width - 4.0,
                ),
            )

            specs.append(
                {
                    "name": name,
                    "item": item,
                    "center_x": scene_point.x(),
                    "left": left,
                    "width": width,
                    "height": height,
                    "preferred_row": preferred_rows.get(
                        name,
                        0,
                    ),
                }
            )

        # Use preferred rows first. If labels in the same row overlap,
        # push the later one down to the next available row.
        rows = []

        for spec in sorted(
            specs,
            key=lambda value: (
                value["preferred_row"],
                value["center_x"],
            ),
        ):
            row_index = spec["preferred_row"]

            while len(rows) <= row_index:
                rows.append([])

            while any(
                spec["left"] < other["right"] + 8.0
                and spec["left"] + spec["width"]
                > other["left"] - 8.0
                for other in rows[row_index]
            ):
                row_index += 1
                while len(rows) <= row_index:
                    rows.append([])

            spec["row"] = row_index
            rows[row_index].append(
                {
                    "left": spec["left"],
                    "right": (
                        spec["left"]
                        + spec["width"]
                    ),
                }
            )

        # Keep the labels below the hover readout.
        top = rect.top() + 48.0
        row_gap = 5.0

        for spec in specs:
            y = (
                top
                + spec["row"]
                * (spec["height"] + row_gap)
                + float(
                    self._label_offsets.get(
                        spec["name"],
                        (0.0, 0.0),
                    )[1]
                )
            )

            y = max(
                rect.top() + 4.0,
                min(
                    y,
                    rect.bottom()
                    - spec["height"]
                    - 4.0,
                ),
            )

            spec["item"].setPos(
                spec["left"],
                y,
            )
            spec["item"].show()

    def _store_label_position(self, name, position):
        """Store a user's screen-space label offset from its default position."""

        if not hasattr(self, "_event_x"):
            return

        item = getattr(
            self,
            f"{name}_label",
            None,
        )

        if item is None:
            return

        vb = self.plot.getPlotItem().vb
        x_value = self._event_x.get(name)

        if x_value is None:
            return

        rect = vb.sceneBoundingRect()
        scene_point = vb.mapViewToScene(
            QPointF(float(x_value), 0.0)
        )

        width = item.boundingRect().width()

        default_left = (
            scene_point.x() - width / 2.0
        )

        preferred_rows = {
            "ignition": 0,
            "peak": 1,
            "burnout": 0,
            "recording_end": 1,
        }

        row = preferred_rows.get(name, 0)
        top = rect.top() + 48.0

        default_y = (
            top
            + row
            * (item.boundingRect().height() + 5.0)
        )

        self._label_offsets[name] = (
            float(position.x() - default_left),
            float(position.y() - default_y),
        )

    def _show_plot_context_menu(self, position):
        """Show marker visibility and label-position controls."""

        menu = QMenu(self.plot)

        toggle_action = menu.addAction(
            "Show Event Markers"
        )
        toggle_action.setCheckable(True)
        toggle_action.setChecked(
            self._show_event_markers
        )

        menu.addSeparator()

        reset_action = menu.addAction(
            "Reset Marker Positions"
        )

        chosen = menu.exec(
            self.plot.mapToGlobal(position)
        )

        if chosen is toggle_action:
            self._show_event_markers = (
                toggle_action.isChecked()
            )

            for item in (
                self.ignition_line,
                self.burnout_line,
                self.recording_end_line,
                self.peak_marker,
            ):
                if item is not None:
                    item.setVisible(
                        self._show_event_markers
                    )

            for item in self._event_labels:
                item.setVisible(
                    self._show_event_markers
                )

            if self._show_event_markers:
                self._update_event_labels()

        elif chosen is reset_action:
            self._label_offsets = {}
            self._update_event_labels()

    def resizeEvent(self, event):
        """Refresh screen-positioned annotations after a resize."""

        super().resizeEvent(event)

        if hasattr(self, "_event_labels"):
            self._update_event_labels()

    def configure_hover_inspection(self):
        """Configure interactive point inspection for the thrust curve."""

        # A lightweight mouse-move proxy prevents the GUI from doing
        # unnecessary work for every raw mouse event while still giving
        # a responsive engineering readout.
        self.mouse_proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self.handle_mouse_move,
        )

        self.hover_readout = QLabel(
            self.plot
        )

        self.hover_readout.setObjectName(
            "plotHoverReadout"
        )

        self.hover_readout.setStyleSheet(
            "QLabel {"
            " background: rgba(8, 14, 19, 220);"
            " color: #d9e5ed;"
            " border: 1px solid #526674;"
            " border-radius: 4px;"
            " padding: 5px 8px;"
            " font-size: 11px;"
            "}"
        )

        self.hover_readout.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        self.hover_readout.hide()

    def handle_mouse_move(self, event):
        """Display the nearest recorded sample under the mouse cursor."""

        if (
            self.data_time is None
            or self.data_thrust is None
            or len(self.data_time) == 0
        ):
            self.hide_hover_inspection()
            return

        scene_pos = event[0]

        view_box = self.plot.getPlotItem().vb

        if not self.plot.sceneBoundingRect().contains(scene_pos):
            self.hide_hover_inspection()
            return

        mouse_point = view_box.mapSceneToView(
            scene_pos
        )

        mouse_time = float(mouse_point.x())

        if (
            mouse_time < float(self.data_time[0])
            or mouse_time > float(self.data_time[-1])
        ):
            self.hide_hover_inspection()
            return

        insertion_index = int(
            np.searchsorted(
                self.data_time,
                mouse_time,
                side="left",
            )
        )

        if insertion_index <= 0:
            index = 0
        elif insertion_index >= len(self.data_time):
            index = len(self.data_time) - 1
        else:
            previous_index = insertion_index - 1
            next_index = insertion_index

            if (
                abs(
                    self.data_time[next_index]
                    - mouse_time
                )
                < abs(
                    self.data_time[previous_index]
                    - mouse_time
                )
            ):
                index = next_index
            else:
                index = previous_index

        sample_time = float(
            self.data_time[index]
        )
        sample_thrust = float(
            self.data_thrust[index]
        )

        if not (
            np.isfinite(sample_time)
            and np.isfinite(sample_thrust)
        ):
            self.hide_hover_inspection()
            return

        if self.hover_cursor is None:
            self.hover_cursor = pg.InfiniteLine(
                angle=90,
                movable=False,
                pen=pg.mkPen(
                    color="#8fa8b8",
                    width=1,
                    style=Qt.PenStyle.DotLine,
                ),
            )
            self.plot.addItem(
                self.hover_cursor,
                ignoreBounds=True,
            )

        if self.hover_marker is None:
            self.hover_marker = pg.ScatterPlotItem(
                size=8,
                pen=pg.mkPen(
                    "#d9e5ed",
                    width=1,
                ),
                brush=pg.mkBrush(
                    "#080e13"
                ),
            )
            self.plot.addItem(
                self.hover_marker,
                ignoreBounds=True,
            )

        self.hover_cursor.setPos(
            sample_time
        )

        self.hover_marker.setData(
            [sample_time],
            [sample_thrust],
        )

        self.show_hover_inspection()

        self.hover_readout.setText(
            f"Time: {sample_time:.3f} s"
            f"    Thrust: {sample_thrust:.2f} N"
        )
        self.hover_readout.adjustSize()

        # Keep the inspection readout in the upper-right corner so it
        # does not cover the early portion of the thrust curve.
        right_margin = 12
        top_margin = 12

        readout_x = max(
            12,
            self.plot.width()
            - self.hover_readout.width()
            - right_margin,
        )

        self.hover_readout.move(
            readout_x,
            top_margin,
        )

        self.hover_readout.show()
        self.hover_readout.raise_()

    def hide_hover_inspection(self):
        """Hide the interactive inspection overlay."""

        if self.hover_cursor is not None:
            self.hover_cursor.hide()

        if self.hover_marker is not None:
            self.hover_marker.hide()

        if self.hover_readout is not None:
            self.hover_readout.hide()

    def show_hover_inspection(self):
        """Show the interactive inspection overlay when available."""

        if self.hover_cursor is not None:
            self.hover_cursor.show()

        if self.hover_marker is not None:
            self.hover_marker.show()

    def set_data(
        self,
        time,
        thrust,
        ignition_time_s=None,
        burnout_time_s=None,
        recording_end_time_s=None,
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

        ignition_time_s:
            Optional detected ignition time in the same time coordinate
            system as ``time``.

        burnout_time_s:
            Optional standardized burn-end time in the same time
            coordinate system as ``time``. The current application
            supplies the authoritative 5% burn-end time here.

            When supplied, data after this boundary is retained on
            the plot as a separate post-burn recording rather than
            being presented as motor thrust.

        recording_end_time_s:
            Optional end-of-recording time. When omitted, the final
            finite sample time is used.
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

        # Preserve a finite, time-ordered copy for interactive inspection.
        finite_mask = (
            np.isfinite(time)
            & np.isfinite(thrust)
        )

        self.data_time = time[finite_mask]
        self.data_thrust = thrust[finite_mask]

        self._remove_event_labels()
        self._label_offsets = {}
        self.plot.clear()
        self.hover_cursor = None
        self.hover_marker = None
        self.playback_cursor = None
        self.hide_hover_inspection()

        # ---------------------------------------------------------
        # Determine whether valid event boundaries were supplied.
        # ---------------------------------------------------------

        valid_ignition = (
            ignition_time_s is not None
            and np.isfinite(ignition_time_s)
            and ignition_time_s >= time[0]
            and ignition_time_s <= time[-1]
        )

        valid_burnout = (
            burnout_time_s is not None
            and np.isfinite(burnout_time_s)
            and burnout_time_s >= time[0]
            and burnout_time_s <= time[-1]
        )

        if recording_end_time_s is None:
            recording_end_time_s = float(
                self.data_time[-1]
            )

        valid_recording_end = (
            recording_end_time_s is not None
            and np.isfinite(recording_end_time_s)
            and recording_end_time_s >= time[0]
            and recording_end_time_s <= time[-1]
        )

        # ---------------------------------------------------------
        # Complete recorded thrust curve
        #
        # The event markers are annotations only. They must never
        # change the appearance of, or split, the measured curve.
        # The entire recorded dataset remains a single continuous
        # thrust curve through the end of recording.
        # ---------------------------------------------------------

        curve_mask = (
            np.isfinite(time)
            & np.isfinite(thrust)
        )

        if np.any(curve_mask):
            curve_pen = pg.mkPen(
                color="#38a8ff",
                width=2,
            )

            self.curve = self.plot.plot(
                time[curve_mask],
                thrust[curve_mask],
                pen=curve_pen,
                name="Recorded Thrust",
            )

        # Kept for compatibility with existing UI state. The curve is
        # intentionally not split or visually dimmed after burnout.
        self.post_burn_curve = None

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
        # Event markers
        #
        # These are annotations only. They do not alter the measured
        # thrust curve.
        #
        # 5% Burn End is the authoritative standardized burn-end
        # result supplied by the analysis engine.
        # End of Recording is the final recorded sample.
        #
        # The vertical lines remain in data coordinates. The text
        # labels are screen-positioned so zooming/panning cannot make
        # them overlap the curve or one another.
        # ---------------------------------------------------------

        ignition_pen = pg.mkPen(
            color="#35d26f",
            width=1,
            style=Qt.PenStyle.DashLine,
        )

        burnout_pen = pg.mkPen(
            color="#ff4b4b",
            width=1,
            style=Qt.PenStyle.DashLine,
        )

        recording_pen = pg.mkPen(
            color="#b06cff",
            width=1,
            style=Qt.PenStyle.DashLine,
        )

        self._event_x = {}

        if valid_ignition:
            self.ignition_line = pg.InfiniteLine(
                pos=float(ignition_time_s),
                angle=90,
                pen=ignition_pen,
            )
            self.plot.addItem(
                self.ignition_line,
                ignoreBounds=True,
            )

            self._event_x["ignition"] = float(
                ignition_time_s
            )

            self.ignition_label = self._create_event_label(
                (
                    "Ignition\n"
                    f"{float(ignition_time_s):.3f} s"
                ),
                "#35d26f",
                "ignition",
            )

        if valid_burnout:
            self.burnout_line = pg.InfiniteLine(
                pos=float(burnout_time_s),
                angle=90,
                pen=burnout_pen,
            )
            self.plot.addItem(
                self.burnout_line,
                ignoreBounds=True,
            )

            self._event_x["burnout"] = float(
                burnout_time_s
            )

            self.burnout_label = self._create_event_label(
                (
                    "5% Burn End\n"
                    f"{float(burnout_time_s):.3f} s"
                ),
                "#ff4b4b",
                "burnout",
            )

        if valid_recording_end:
            same_as_burnout = (
                valid_burnout
                and abs(
                    float(recording_end_time_s)
                    - float(burnout_time_s)
                ) < 1e-6
            )

            if not same_as_burnout:
                self.recording_end_line = pg.InfiniteLine(
                    pos=float(recording_end_time_s),
                    angle=90,
                    pen=recording_pen,
                )
                self.plot.addItem(
                    self.recording_end_line,
                    ignoreBounds=True,
                )

                self._event_x["recording_end"] = float(
                    recording_end_time_s
                )

                self.recording_end_label = (
                    self._create_event_label(
                        (
                            "End of Recording\n"
                            f"{float(recording_end_time_s):.3f} s"
                        ),
                        "#b06cff",
                        "recording_end",
                    )
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
            self._event_x["peak"] = float(
                peak_time_s
            )

            self.peak_label = self._create_event_label(
                f"Peak: {float(peak_thrust_N):.2f} N",
                "#38a8ff",
                "peak",
            )

        # The recording-end marker above represents the final recorded
        # sample. It is intentionally separate from the standardized
        # 5% burn-end marker supplied as burnout_time_s.

        # ---------------------------------------------------------
        # Y-axis
        # ---------------------------------------------------------

        # Keep a deliberate headroom band for the event labels instead
        # of allowing the labels to sit on top of the thrust curve.
        finite_thrust = thrust[np.isfinite(thrust)]

        if len(finite_thrust) > 0:
            y_min = float(np.min(finite_thrust))
            y_max = float(np.max(finite_thrust))

            if np.isfinite(y_min) and np.isfinite(y_max):
                if y_min > 0:
                    y_min = 0.0

                y_span = max(
                    y_max - y_min,
                    1.0,
                )

                self.plot.setYRange(
                    y_min - y_span * 0.02,
                    y_max + y_span * 0.20,
                    padding=0,
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

        # The initial view is now established, so position the
        # screen-space event labels against the final plot geometry.
        self._update_event_labels()

        # Respect the user's marker visibility preference when a new
        # test is loaded.
        marker_items = (
            self.ignition_line,
            self.burnout_line,
            self.recording_end_line,
            self.peak_marker,
        )

        for item in marker_items:
            if item is not None:
                item.setVisible(
                    self._show_event_markers
                )

        for item in self._event_labels:
            item.setVisible(
                self._show_event_markers
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

        self._remove_event_labels()
        self._label_offsets = {}

        self.plot.clear()

        self.curve = None
        self.post_burn_curve = None
        self.zero_line = None
        self.ignition_line = None
        self.burnout_line = None
        self.recording_end_line = None
        self.peak_marker = None
        self.ignition_label = None
        self.burnout_label = None
        self.recording_end_label = None
        self.peak_label = None
        self.data_time = None
        self.data_thrust = None
        self.hover_cursor = None
        self.hover_marker = None
        self.playback_cursor = None
        self.hide_hover_inspection()

        self.stack.setCurrentWidget(
            self.placeholder
        )

    def set_playback_position(self, position_s):
        """Show the shared playback position as a circular marker on the curve."""
        if self.data_time is None or len(self.data_time) == 0:
            return

        times = np.asarray(self.data_time, dtype=float)
        thrust = np.asarray(self.data_thrust, dtype=float)
        mask = np.isfinite(times) & np.isfinite(thrust)
        times = times[mask]
        thrust = thrust[mask]

        if len(times) == 0:
            return

        if self.playback_cursor is None:
            self.playback_cursor = pg.ScatterPlotItem(
                size=12,
                pen=pg.mkPen("#ffffff", width=2),
                brush=pg.mkBrush("#39d98a"),
                symbol="o",
                pxMode=True,
            )
            self.playback_cursor.setZValue(50)
            self.plot.addItem(self.playback_cursor)

        position = float(position_s)

        # When a video is loaded, its timeline begins before RMCS t=0.
        # Keep the analyzer marker hidden until the synchronization point.
        if position < float(times[0]):
            self.playback_cursor.hide()
            return

        # Once analysis has ended, hold the marker at the last measured
        # point while the video continues through its remaining frames.
        marker_position = min(
            position,
            float(times[-1]),
        )

        if len(times) == 1:
            thrust_value = float(thrust[0])
        else:
            thrust_value = float(
                np.interp(
                    marker_position,
                    times,
                    thrust,
                )
            )

        self.playback_cursor.setData(
            [marker_position],
            [thrust_value],
        )
        self.playback_cursor.show()

    def hide_playback_position(self):
        if self.playback_cursor is not None:
            self.playback_cursor.hide()

    def get_plot_widget(self):
        """Return the underlying PlotWidget."""

        return self.plot