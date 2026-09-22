import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMenu,
    QPushButton,
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
        self.setFlag(self.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.moved_callback is not None:
            self.moved_callback(self.event_name, self.pos())


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

        self.events_button = QPushButton("Events ▾")
        self.events_button.setObjectName("eventsButton")
        self.events_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.events_button.clicked.connect(self._show_events_menu)
        self.events_button.setStyleSheet(
            "QPushButton#eventsButton {"
            " background-color: #17232d; color: #d7e1e8;"
            " border: 1px solid #40515e; border-radius: 4px;"
            " padding: 4px 10px; font-weight: 600;"
            "} QPushButton#eventsButton:hover {"
            " background-color: #223442;"
            "}"
        )
        self.events_button.adjustSize()

        self.data_time = None
        self.data_pressure = None
        self.hover_marker = None
        self.hover_readout = None
        self.playback_cursor = None

        self.ignition_line = None
        self.peak_line = None
        self.burn_time_line = None
        self.burnout_line = None
        self.recording_end_line = None
        self.case_limit_line = None
        self.ignition_label = None
        self.peak_label = None
        self.burn_time_label = None
        self.burnout_label = None
        self.recording_end_label = None
        self.case_limit_label = None
        self._event_labels = []
        self._event_x = {}
        self._label_offsets = {}
        self._event_visibility = {
            "ignition": True,
            "peak": True,
            "burn_time": True,
            "burnout": True,
            "recording_end": True,
        }
        self._show_event_markers = True

        self.mouse_proxy = pg.SignalProxy(
            self.plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self._handle_mouse_move,
        )
        self.hover_readout = QLabel(self.plot)
        self.hover_readout.setObjectName("plotHoverReadout")
        self.hover_readout.setStyleSheet(
            "QLabel {"
            " background: rgba(8, 14, 19, 220);"
            " color: #d9e5ed; border: 1px solid #526674;"
            " border-radius: 4px; padding: 5px 8px; font-size: 11px;"
            "}"
        )
        self.hover_readout.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hover_readout.hide()

        self.plot.getPlotItem().vb.sigRangeChanged.connect(self._update_event_labels)

    def _create_placeholder(self):
        frame = QFrame()
        frame.setObjectName("graphPlaceholder")
        layout = QVBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("No Pressure Data Available")
        title.setObjectName("graphTitle")
        description = QLabel("This test does not contain a valid pressure channel.")
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

    def _create_event_label(self, name, text, color):
        label = DraggableEventLabel(name, self._event_label_moved)
        label.setDefaultTextColor(color)
        label.setFont(label.font())
        label.setPlainText(text)
        label.setZValue(30)
        self.plot.scene().addItem(label)
        self._event_labels.append(label)
        return label

    def _event_label_moved(self, name, pos):
        self._label_offsets[name] = (float(pos.x()), float(pos.y()))

    def _remove_event_labels(self):
        for label in self._event_labels:
            try:
                self.plot.scene().removeItem(label)
            except Exception:
                pass
        self._event_labels = []

    def _event_items(self, name):
        return {
            "ignition": (self.ignition_line, self.ignition_label),
            "peak": (self.peak_line, self.peak_label),
            "burn_time": (self.burn_time_line, self.burn_time_label),
            "burnout": (self.burnout_line, self.burnout_label),
            "recording_end": (self.recording_end_line, self.recording_end_label),
        }.get(name, (None, None))

    def _set_event_visibility(self, name, visible):
        self._event_visibility[name] = bool(visible)
        line, label = self._event_items(name)
        for item in (line, label):
            if item is not None:
                item.setVisible(bool(visible) and self._show_event_markers)
        self._update_event_labels()

    def _set_all_event_visibility(self, visible):
        for name in self._event_visibility:
            self._event_visibility[name] = bool(visible)
        for name in self._event_visibility:
            self._set_event_visibility(name, visible)

    def _show_events_menu(self):
        menu = QMenu(self.events_button)
        labels = [
            ("ignition", "Ignition"),
            ("peak", "Peak Pressure"),
            ("burn_time", "Burn Time"),
            ("burnout", "Burnout"),
            ("recording_end", "End of Data"),
        ]
        for name, label in labels:
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(self._event_visibility.get(name, True))
            line, marker_label = self._event_items(name)
            action.setEnabled(line is not None or marker_label is not None)
            action.toggled.connect(
                lambda checked, event_name=name: self._set_event_visibility(event_name, checked)
            )
        menu.addSeparator()
        show_all = menu.addAction("Show All")
        hide_all = menu.addAction("Hide All")
        menu.addSeparator()
        reset_action = menu.addAction("Reset Marker Positions")
        chosen = menu.exec(
            self.events_button.mapToGlobal(self.events_button.rect().bottomLeft())
        )
        if chosen is show_all:
            self._set_all_event_visibility(True)
        elif chosen is hide_all:
            self._set_all_event_visibility(False)
        elif chosen is reset_action:
            self._label_offsets = {}
            self._update_event_labels()

    def _add_vertical_event(self, name, value, label_text, color):
        if value is None or not np.isfinite(value):
            return None, None
        line = pg.InfiniteLine(
            pos=float(value),
            angle=90,
            pen=pg.mkPen(color, width=1, style=Qt.PenStyle.DashLine),
        )
        line.setZValue(10)
        self.plot.addItem(line)
        label = self._create_event_label(name, label_text, color)
        self._event_x[name] = float(value)
        return line, label

    def _add_peak_marker(self, name, time_value, pressure_value, label_text, color):
        if (
            time_value is None
            or pressure_value is None
            or not np.isfinite(time_value)
            or not np.isfinite(pressure_value)
        ):
            return None, None

        marker = pg.ScatterPlotItem(
            [float(time_value)],
            [float(pressure_value)],
            size=10,
            pen=pg.mkPen(color, width=2),
            brush=pg.mkBrush("#080e13"),
        )
        marker.setZValue(25)
        self.plot.addItem(marker)
        label = self._create_event_label(name, label_text, color)
        self._event_x[name] = float(time_value)
        return marker, label

    def set_data(
        self,
        time_s,
        pressure_psi,
        ignition_time_s=None,
        burn_time_s=None,
        burnout_time_s=None,
        recording_end_time_s=None,
        case_pressure_limit_psi=None,
    ):
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

        self._remove_event_labels()
        self._label_offsets = {}
        self._event_x = {}
        self.plot.clear()
        self.ignition_line = self.peak_line = self.burn_time_line = None
        self.burnout_line = self.recording_end_line = None
        self.case_limit_line = None
        self.ignition_label = self.peak_label = self.burn_time_label = None
        self.burnout_label = self.recording_end_label = None
        self.case_limit_label = None
        self.playback_cursor = None

        self.data_time = time
        self.data_pressure = pressure

        self.plot.plot(
            time,
            pressure,
            pen=pg.mkPen("#6fb7ff", width=2),
            name="Recorded Pressure",
        )

        if self._show_simulation and self.simulation_time is not None and self.simulation_pressure is not None:
            self._add_simulation_curve()

        self.plot.addLine(y=0, pen=pg.mkPen("#526674", width=1))

        peak_index = int(np.nanargmax(pressure))
        peak_time_s = float(time[peak_index])
        peak_pressure_psi = float(pressure[peak_index])

        self.ignition_line, self.ignition_label = self._add_vertical_event(
            "ignition", ignition_time_s,
            f"Ignition\n{float(ignition_time_s):.3f} s" if ignition_time_s is not None else "",
            "#65d18a",
        )
        self.peak_line, self.peak_label = self._add_peak_marker(
            "peak", peak_time_s, peak_pressure_psi,
            f"Peak Pressure\n{peak_pressure_psi:.2f} psi",
            "#3aa7ff",
        )
        self.burn_time_line, self.burn_time_label = self._add_vertical_event(
            "burn_time", burn_time_s,
            f"Burn Time\n{float(burn_time_s):.3f} s" if burn_time_s is not None else "",
            "#ff4d4d",
        )
        self.burnout_line, self.burnout_label = self._add_vertical_event(
            "burnout", burnout_time_s,
            f"Burnout\n{float(burnout_time_s):.3f} s" if burnout_time_s is not None else "",
            "#ff9f43",
        )
        self.recording_end_line, self.recording_end_label = self._add_vertical_event(
            "recording_end", recording_end_time_s,
            f"End of Data\n{float(recording_end_time_s):.3f} s" if recording_end_time_s is not None else "",
            "#c77dff",
        )

        if case_pressure_limit_psi is not None:
            try:
                limit = float(case_pressure_limit_psi)
            except (TypeError, ValueError):
                limit = None
            if limit is not None and np.isfinite(limit) and limit > 0:
                self.case_limit_line = pg.InfiniteLine(
                    pos=limit,
                    angle=0,
                    pen=pg.mkPen("#ffcc66", width=2, style=Qt.PenStyle.DashLine),
                )
                self.case_limit_line.setZValue(8)
                self.plot.addItem(self.case_limit_line)
                self.case_limit_label = self._create_event_label(
                    "case_limit",
                    f"Case Pressure Limit — {limit:.0f} psi",
                    "#ffcc66",
                )
                self.case_limit_label.setZValue(20)
                self._event_x["case_limit"] = float(time[-1])

        self.plot.enableAutoRange()
        if self.case_limit_line is not None:
            limit = float(self.case_limit_line.value())
            view_min, view_max = self.plot.getPlotItem().vb.viewRange()[1]
            if limit > view_max:
                self.plot.setYRange(view_min, limit * 1.08, padding=0)

        self._apply_event_visibility()
        self._update_event_labels()
        self.stack.setCurrentWidget(self.plot)

    def _apply_event_visibility(self):
        for name in self._event_visibility:
            line, label = self._event_items(name)
            visible = self._event_visibility[name] and self._show_event_markers
            for item in (line, label):
                if item is not None:
                    item.setVisible(visible)

    def _update_event_labels(self, *args):
        if not self._event_labels or not self._show_event_markers:
            return

        vb = self.plot.getPlotItem().vb
        rect = vb.sceneBoundingRect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        label_items = (
            ("ignition", self.ignition_label),
            ("peak", self.peak_label),
            ("burn_time", self.burn_time_label),
            ("burnout", self.burnout_label),
            ("recording_end", self.recording_end_label),
            ("case_limit", self.case_limit_label),
        )
        preferred_rows = {
            "ignition": 0,
            "peak": 1,
            "burn_time": 0,
            "burnout": 1,
            "recording_end": 2,
            "case_limit": 0,
        }
        specs = []

        for name, item in label_items:
            if item is None or not self._event_visibility.get(name, True):
                continue
            x_value = self._event_x.get(name)
            if x_value is None or not np.isfinite(x_value):
                continue
            scene_point = vb.mapViewToScene(QPointF(float(x_value), 0.0))
            width = item.boundingRect().width()
            height = item.boundingRect().height()
            offset = self._label_offsets.get(name, (0.0, 0.0))
            left = scene_point.x() - width / 2.0 + float(offset[0])
            left = max(rect.left() + 4.0, min(left, rect.right() - width - 4.0))
            specs.append({
                "name": name,
                "item": item,
                "center_x": scene_point.x(),
                "left": left,
                "width": width,
                "height": height,
                "preferred_row": preferred_rows.get(name, 0),
            })

        rows = []
        for spec in sorted(specs, key=lambda value: (value["preferred_row"], value["center_x"])):
            row_index = spec["preferred_row"]
            while len(rows) <= row_index:
                rows.append([])
            while any(
                spec["left"] < other["right"] + 8.0
                and spec["left"] + spec["width"] > other["left"] - 8.0
                for other in rows[row_index]
            ):
                row_index += 1
                while len(rows) <= row_index:
                    rows.append([])
            spec["row"] = row_index
            rows[row_index].append({"left": spec["left"], "right": spec["left"] + spec["width"]})

        top = rect.top() + 48.0
        row_gap = 5.0
        for spec in specs:
            offset_y = float(self._label_offsets.get(spec["name"], (0.0, 0.0))[1])
            y = top + spec["row"] * (spec["height"] + row_gap) + offset_y
            y = max(rect.top() + 4.0, min(y, rect.bottom() - spec["height"] - 4.0))
            spec["item"].setPos(spec["left"], y)

    def _add_simulation_curve(self):
        if self.simulation_time is None or self.simulation_pressure is None:
            return
        if len(self.simulation_time) != len(self.simulation_pressure):
            return
        mask = np.isfinite(self.simulation_time) & np.isfinite(self.simulation_pressure)
        if not np.any(mask):
            return
        self.simulation_curve = self.plot.plot(
            self.simulation_time[mask],
            self.simulation_pressure[mask],
            pen=pg.mkPen("#ffb84d", width=2, style=Qt.PenStyle.DashLine),
            name="Simulation Pressure",
        )
        self.simulation_curve.setZValue(5)

    def _update_simulation_curve(self):
        if self.simulation_curve is not None:
            try:
                self.plot.removeItem(self.simulation_curve)
            except Exception:
                pass
            self.simulation_curve = None
        if self._show_simulation and self.data_time is not None:
            self._add_simulation_curve()

    def set_simulation(self, time_s=None, pressure_psi=None, visible=False):
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
        self._show_simulation = bool(visible)
        self._update_simulation_curve()

    def set_playback_position(self, position_s):
        if self.data_time is None or self.data_pressure is None or len(self.data_time) == 0:
            return
        position = float(position_s)
        if position < float(self.data_time[0]) or position > float(self.data_time[-1]):
            if self.playback_cursor is not None:
                self.playback_cursor.hide()
            return
        index = int(np.searchsorted(self.data_time, position, side="left"))
        if index <= 0:
            index = 0
        elif index >= len(self.data_time):
            index = len(self.data_time) - 1
        if self.playback_cursor is None:
            self.playback_cursor = pg.ScatterPlotItem(size=9, pen=pg.mkPen("#ffffff", width=1.5), brush=pg.mkBrush("#ffffff"))
            self.playback_cursor.setZValue(50)
            self.plot.addItem(self.playback_cursor)
        self.playback_cursor.setData([float(self.data_time[index])], [float(self.data_pressure[index])])
        self.playback_cursor.show()

    def clear_playback_position(self):
        if self.playback_cursor is not None:
            self.playback_cursor.hide()

    def _position_hover_readout(self):
        if self.hover_readout is None or not self.hover_readout.isVisible():
            return
        self.hover_readout.adjustSize()
        x = max(8, self.plot.width() - self.hover_readout.width() - 10)
        self.hover_readout.move(x, 10)

    def _handle_mouse_move(self, event):
        if self.data_time is None or self.data_pressure is None or len(self.data_time) == 0:
            self.hover_readout.hide()
            return
        scene_pos = event[0]
        if not self.plot.sceneBoundingRect().contains(scene_pos):
            self.hover_readout.hide()
            return
        mouse_point = self.plot.getPlotItem().vb.mapSceneToView(scene_pos)
        x = float(mouse_point.x())
        if x < float(self.data_time[0]) or x > float(self.data_time[-1]):
            self.hover_readout.hide()
            return
        index = int(np.searchsorted(self.data_time, x, side="left"))
        if index <= 0:
            index = 0
        elif index >= len(self.data_time):
            index = len(self.data_time) - 1
        self.hover_readout.setText(
            f"Time: {float(self.data_time[index]):.3f} s   Pressure: {float(self.data_pressure[index]):.2f} psi"
        )
        self.hover_readout.adjustSize()
        self.hover_readout.show()
        self._position_hover_readout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "events_button"):
            self.events_button.adjustSize()
        if hasattr(self, "_event_labels"):
            self._update_event_labels()
        if hasattr(self, "hover_readout"):
            self._position_hover_readout()

    def clear(self):
        self._remove_event_labels()
        self._label_offsets = {}
        self.plot.clear()
        self.simulation_curve = None
        self.ignition_line = self.peak_line = self.burn_time_line = None
        self.burnout_line = self.recording_end_line = self.case_limit_line = None
        self.ignition_label = self.peak_label = self.burn_time_label = None
        self.burnout_label = self.recording_end_label = self.case_limit_label = None
        self.data_time = None
        self.data_pressure = None
        self.playback_cursor = None
        self.hover_readout.hide()
        self.stack.setCurrentWidget(self.placeholder)
