import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QGraphicsTextItem,
    QPushButton,
    QScrollArea,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class DraggableCompareLabel(QGraphicsTextItem):
    """Screen-space comparison annotation that can be dragged by the user."""

    def __init__(self, key, moved_callback=None):
        super().__init__()
        self.key = key
        self.moved_callback = moved_callback
        self.setFlag(self.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable, True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.moved_callback is not None:
            self.moved_callback(self.key, self.pos())


class ComparePanel(QFrame):
    """Two-test comparison workspace with synchronized thrust/pressure plots."""

    selection_changed = None

    _TEST_COLORS = [
        "#38bdf8",
        "#f59e0b",
    ]
    # Match the event colors used by the individual Thrust/Pressure plots.
    _EVENT_COLORS = {
        "Ignition": "#35d26f",
        "Peak": "#3aa7ff",
        "Burn Time": "#ff4b4b",
        "Burnout": "#ff9f43",
        "End of Data": "#b06cff",
        "Case Limit": "#ffcc66",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("compareWorkspace")
        self.tests = []
        self.checkboxes = []
        self._selected_sources = set()
        self._selected_test_cache = []
        self._event_visibility = {
            "Ignition": True,
            "Peak": True,
            "Burn Time": True,
            "Burnout": True,
            "End of Data": True,
            "Case Pressure Limit": True,
        }
        self._event_labels = []
        self._event_label_specs = {}
        self._label_offsets = {}
        self._playback_lines = []
        self._duration_s = 0.0
        self._playing = False

        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self._advance_playback)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QLabel("Test Comparison")
        header.setObjectName("graphTitle")
        layout.addWidget(header)

        description = QLabel(
            "Select two loaded tests to compare thrust and pressure behavior on synchronized plots."
        )
        description.setObjectName("graphDescription")
        description.setWordWrap(True)
        layout.addWidget(description)

        self.test_selector = QScrollArea()
        self.test_selector.setWidgetResizable(True)
        self.test_selector.setMaximumHeight(72)
        selector_host = QWidget()
        self.selector_layout = QHBoxLayout(selector_host)
        self.selector_layout.setContentsMargins(4, 2, 4, 2)
        self.selector_layout.setSpacing(14)
        self.test_selector.setWidget(selector_host)
        layout.addWidget(self.test_selector)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(8)
        self.status = QLabel("Load at least two tests to begin comparison.")
        self.status.setObjectName("graphDescription")
        controls.addWidget(self.status, 1)

        self.events_button = QToolButton()
        self.events_button.setText("Events ▾")
        self.events_button.setToolTip("Choose which comparison event markers are visible.")
        self.events_menu = QMenu(self.events_button)
        self._event_actions = {}
        for name in self._event_visibility:
            action = self.events_menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(True)
            action.triggered.connect(
                lambda checked, event_name=name: self._set_event_visibility(event_name, checked)
            )
            self._event_actions[name] = action
        self.events_menu.addSeparator()
        show_all = self.events_menu.addAction("Show All")
        show_all.triggered.connect(lambda: self._set_all_events(True))
        hide_all = self.events_menu.addAction("Hide All")
        hide_all.triggered.connect(lambda: self._set_all_events(False))
        self.events_button.setMenu(self.events_menu)
        self.events_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        controls.addWidget(self.events_button)
        layout.addLayout(controls)

        self.thrust_plot, self.thrust_legend = self._make_plot("Thrust", "N")
        layout.addWidget(self._wrap_plot(self.thrust_plot, self.thrust_legend), 3)

        self.pressure_plot, self.pressure_legend = self._make_plot("Pressure", "psi")
        layout.addWidget(self._wrap_plot(self.pressure_plot, self.pressure_legend), 3)

        playback = QHBoxLayout()
        playback.setContentsMargins(0, 0, 0, 0)
        playback.setSpacing(6)
        self.reset_button = QPushButton("⏮")
        self.reset_button.setToolTip("Reset comparison playback")
        self.reset_button.clicked.connect(self._reset_playback)
        playback.addWidget(self.reset_button)

        self.play_button = QPushButton("▶")
        self.play_button.setToolTip("Play / pause comparison playback")
        self.play_button.clicked.connect(self._toggle_playback)
        playback.addWidget(self.play_button)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 10000)
        self.slider.setSingleStep(10)
        self.slider.valueChanged.connect(self._slider_changed)
        playback.addWidget(self.slider, 1)

        self.time_label = QLabel("0.000 / 0.000 s")
        self.time_label.setMinimumWidth(115)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        playback.addWidget(self.time_label)
        layout.addLayout(playback)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Test",
            "Total Impulse (N·s)",
            "Peak Thrust (N)",
            "Peak Pressure (psi)",
            "Burn Time (s)",
            "Average Thrust (N)",
            "Isp (s)",
            "C* (m/s)",
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 0)

    def _wrap_plot(self, plot, legend_layout):
        host = QWidget()
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setSpacing(2)
        host_layout.addLayout(legend_layout)
        host_layout.addWidget(plot, 1)
        return host

    def _make_plot(self, ylabel, units):
        plot = pg.PlotWidget()
        plot.setBackground("#080e13")
        plot.setLabel("bottom", "Time", units="s", color="#9aabb8")
        plot.setLabel("left", ylabel, units=units, color="#9aabb8")
        plot.showGrid(x=True, y=True, alpha=0.18)
        plot.setMouseEnabled(x=True, y=True)
        plot.setMinimumHeight(150)
        # Keep the plotting rectangles vertically aligned despite different
        # Y-axis label widths (Thrust vs Pressure).
        plot.getPlotItem().getAxis("left").setWidth(78)
        plot.getPlotItem().vb.sigRangeChanged.connect(self._update_event_labels)

        legend_layout = QHBoxLayout()
        legend_layout.setContentsMargins(4, 0, 4, 0)
        legend_layout.setSpacing(12)
        return plot, legend_layout

    def set_tests(self, tests, active_test=None):
        previous_sources = set(self._selected_sources)
        self.tests = list(tests)
        current_sources = {test.source_file for test in self.tests if test.source_file}
        preserved_sources = previous_sources & current_sources

        while self.selector_layout.count():
            item = self.selector_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.checkboxes = []
        for index, test in enumerate(self.tests):
            checkbox = QCheckBox(test.display_name or f"Test {index + 1}")
            if preserved_sources:
                checked = test.source_file in preserved_sources
            else:
                checked = test is active_test and len(self.tests) > 1
            checkbox.setChecked(checked)
            checkbox.stateChanged.connect(self._refresh)
            checkbox.setProperty("test_index", index)
            self.selector_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)
        self.selector_layout.addStretch(1)
        self._refresh()

    def _selected_tests_from_boxes(self):
        selected = [
            self.tests[int(cb.property("test_index"))]
            for cb in self.checkboxes
            if cb.isChecked()
        ]
        return selected

    def _selected_tests(self):
        selected = self._selected_tests_from_boxes()
        if len(selected) > 2:
            # Keep the two most recently checked boxes. This prevents a third
            # curve from silently changing the two-test comparison design.
            checked_boxes = [cb for cb in self.checkboxes if cb.isChecked()]
            for cb in checked_boxes[:-2]:
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.blockSignals(False)
            selected = self._selected_tests_from_boxes()

        self._selected_sources = {
            test.source_file for test in selected if test.source_file
        }
        self._selected_test_cache = selected
        return selected

    def _refresh(self, *args):
        selected = self._selected_tests()
        self._stop_playback()
        self._clear_plots()
        self.table.setRowCount(0)

        if not selected:
            self.status.setText("Load a test to begin comparison.")
            self._set_duration(0.0)
            return

        if len(selected) == 1:
            self.status.setText("1 test loaded — select another test to compare.")
        else:
            self.status.setText("Comparing 2 tests — shared time axis and playback.")

        self._duration_s = max(self._test_duration(test) for test in selected)
        self._set_duration(self._duration_s)

        for index, test in enumerate(selected):
            color = self._TEST_COLORS[index]
            self._plot_test(test, color, index)
            self._add_table_row(test)

        self.thrust_plot.setXLink(self.pressure_plot)
        self.thrust_plot.getViewBox().autoRange(padding=0.08)
        self.pressure_plot.getViewBox().autoRange(padding=0.08)
        self._add_playback_lines()
        self._update_playback_position(0.0)

    def _clear_plots(self):
        self.thrust_plot.clear()
        self.pressure_plot.clear()
        self._event_labels = []
        self._event_label_specs = {}
        self._label_offsets = {}
        self._playback_lines = []
        self._rebuild_legends([])

    def _plot_test(self, test, color, test_index):
        time = np.asarray(test.data.time_s, dtype=float)
        thrust = np.asarray(test.data.thrust_N, dtype=float)
        pressure = np.asarray(getattr(test.data, "pressure_psi", []), dtype=float)

        thrust_mask = np.isfinite(time) & np.isfinite(thrust)
        if np.any(thrust_mask):
            self.thrust_plot.plot(
                time[thrust_mask],
                thrust[thrust_mask],
                pen=pg.mkPen(color=color, width=2),
            )

        if pressure.size == time.size:
            pressure_mask = np.isfinite(time) & np.isfinite(pressure)
            if np.any(pressure_mask):
                self.pressure_plot.plot(
                    time[pressure_mask],
                    pressure[pressure_mask],
                    pen=pg.mkPen(color=color, width=2),
                )

        self._add_legend_entry(self.thrust_legend, test.display_name, color)
        self._add_legend_entry(self.pressure_legend, test.display_name, color)
        self._add_event_markers(test, color, test_index)

    def _add_legend_entry(self, layout, name, color):
        swatch = QLabel("●")
        swatch.setStyleSheet(f"color: {color}; font-size: 12px;")
        label = QLabel(name)
        label.setStyleSheet("color: #cbd5df;")
        layout.addWidget(swatch)
        layout.addWidget(label)

    def _rebuild_legends(self, entries):
        for layout in (self.thrust_legend, self.pressure_legend):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            for name, color in entries:
                self._add_legend_entry(layout, name, color)
            layout.addStretch(1)

    def _add_event_markers(self, test, color, test_index):
        results = test.analysis_results
        if results is None:
            return

        thrust_results = results.thrust
        events = results.events

        event_points = []
        ignition = getattr(events, "ignition", None)
        burnout = getattr(events, "burnout", None)
        if ignition is not None:
            event_points.append(("Ignition", float(ignition.time_s)))
        if thrust_results.peak_thrust_time_s is not None:
            event_points.append(("Peak", float(thrust_results.peak_thrust_time_s)))
        if thrust_results.burn_end_5pct_time_s is not None:
            event_points.append(("Burn Time", float(thrust_results.burn_end_5pct_time_s)))
        if burnout is not None:
            event_points.append(("Burnout", float(burnout.time_s)))
        if np.size(getattr(test.data, "time_s", [])):
            event_points.append(("End of Data", float(np.asarray(test.data.time_s)[-1])))

        time = np.asarray(test.data.time_s, dtype=float)
        thrust = np.asarray(test.data.thrust_N, dtype=float)
        pressure = np.asarray(getattr(test.data, "pressure_psi", []), dtype=float)

        # When multiple selected tests have the same event time, draw the
        # marker for each curve but keep a single label. This prevents
        # identical tests from producing stacked duplicate annotations.
        existing_events = {
            key.split(":", 2)[1:] for key in self._event_label_specs
            if key.count(":") >= 2 and key.split(":", 2)[2] == "event"
        }

        for event_name, event_time in event_points:
            if not self._event_visibility.get(event_name, True):
                continue
            thrust_value = self._interp_value(time, thrust, event_time)
            pressure_value = self._interp_value(time, pressure, event_time)
            marker_color = self._EVENT_COLORS[event_name]
            if thrust_value is not None:
                label_name = "Peak Thrust" if event_name == "Peak" else event_name
                self._add_event_point(
                    self.thrust_plot, label_name, event_name, event_time, thrust_value,
                    marker_color, test_index, "thrust", add_label=self._should_add_shared_label("thrust", event_name, event_time)
                )
            if pressure_value is not None:
                label_name = "Peak Pressure" if event_name == "Peak" else event_name
                self._add_event_point(
                    self.pressure_plot, label_name, event_name, event_time, pressure_value,
                    marker_color, test_index, "pressure", add_label=self._should_add_shared_label("pressure", event_name, event_time)
                )

        # Case pressure limit is an engineering reference, not a motor event.
        # Draw one line/label for each distinct limit among selected tests and
        # expose it through the same Events menu for visibility control.
        limit = self._pressure_limit(test)
        if limit is not None and self._event_visibility.get("Case Pressure Limit", True):
            duplicate_limit = any(
                spec.get("kind") == "case_limit" and abs(float(spec.get("limit", 0.0)) - limit) < 1e-9
                for spec in self._event_label_specs.values()
            )
            if not duplicate_limit:
                line = pg.InfiniteLine(
                    pos=limit,
                    angle=0,
                    pen=pg.mkPen(
                        color=self._EVENT_COLORS["Case Limit"],
                        width=1.5,
                        style=Qt.PenStyle.DashLine,
                    ),
                )
                line.setZValue(8)
                self.pressure_plot.addItem(line)

                key = f"case_limit:{limit:.9f}"
                label = self._create_label(
                    key,
                    f"Case Pressure Limit — {limit:.0f} psi",
                    self._EVENT_COLORS["Case Limit"],
                )
                self.pressure_plot.scene().addItem(label)
                self._event_labels.append(label)
                self._event_label_specs[key] = {
                    "item": label,
                    "plot": self.pressure_plot,
                    "x": float(time[-1]) if time.size else 0.0,
                    "preferred_row": 0,
                    "kind": "case_limit",
                    "limit": limit,
                }

    def _should_add_shared_label(self, plot_name, event_name, event_time):
        for spec in self._event_label_specs.values():
            if spec.get("kind") != "event" or spec.get("plot_name") != plot_name:
                continue
            if spec.get("event_name") == event_name and abs(float(spec.get("event_time", -9999.0)) - event_time) < 1e-6:
                return False
        return True

    def _create_label(self, key, text, color):
        label = DraggableCompareLabel(key, self._label_moved)
        label.setPlainText(text)
        label.setDefaultTextColor(QColor(color))
        font = QFont()
        font.setPointSize(9)
        label.setFont(font)
        label.setZValue(1000)
        label.setToolTip("Drag to reposition this label")
        return label

    def _add_event_point(self, plot, label_name, event_name, event_time, value, color, test_index, plot_name, add_label=True):
        scatter = pg.ScatterPlotItem(
            [event_time],
            [value],
            symbol="o",
            size=9,
            pen=pg.mkPen(color=color, width=1.5),
            brush=pg.mkBrush("#080e13"),
        )
        scatter.setZValue(25)
        plot.addItem(scatter)

        if not add_label:
            return

        key = f"event:{plot_name}:{event_name}:{event_time:.6f}"
        label = self._create_label(key, f"{label_name} — {event_time:.3f} s", color)
        plot.scene().addItem(label)
        self._event_labels.append(label)
        preferred = {
            "Ignition": 0,
            "Peak": 1,
            "Burn Time": 0,
            "Burnout": 1,
            "End of Data": 2,
        }.get(event_name, 0)
        self._event_label_specs[key] = {
            "item": label,
            "plot": plot,
            "plot_name": plot_name,
            "event_name": event_name,
            "event_time": float(event_time),
            "x": float(event_time),
            "preferred_row": preferred,
            "kind": "event",
        }

    def _label_moved(self, key, position):
        spec = self._event_label_specs.get(key)
        if spec is None:
            return
        plot = spec["plot"]
        item = spec["item"]
        vb = plot.getPlotItem().vb
        rect = vb.sceneBoundingRect()
        scene_point = vb.mapViewToScene(QPointF(float(spec["x"]), 0.0))
        default_left = scene_point.x() - item.boundingRect().width() / 2.0
        row = int(spec.get("preferred_row", 0))
        default_y = rect.top() + 34.0 + row * (item.boundingRect().height() + 4.0)
        self._label_offsets[key] = (
            float(position.x() - default_left),
            float(position.y() - default_y),
        )

    def _update_event_labels(self, *args):
        if not self._event_label_specs:
            return

        for plot in (self.thrust_plot, self.pressure_plot):
            specs = []
            vb = plot.getPlotItem().vb
            rect = vb.sceneBoundingRect()
            if rect.width() <= 0 or rect.height() <= 0:
                continue

            for key, spec in self._event_label_specs.items():
                if spec["plot"] is not plot:
                    continue
                item = spec["item"]
                x_value = spec["x"]
                scene_point = vb.mapViewToScene(QPointF(float(x_value), 0.0))
                width = item.boundingRect().width()
                height = item.boundingRect().height()
                offset = self._label_offsets.get(key, (0.0, 0.0))
                left = scene_point.x() - width / 2.0 + offset[0]
                left = max(rect.left() + 4.0, min(left, rect.right() - width - 4.0))
                specs.append({
                    "key": key, "item": item, "center_x": scene_point.x(),
                    "left": left, "width": width, "height": height,
                    "preferred_row": spec.get("preferred_row", 0),
                    "offset_y": offset[1],
                })

            rows = []
            for spec in sorted(specs, key=lambda v: (v["preferred_row"], v["center_x"])):
                row = spec["preferred_row"]
                while len(rows) <= row:
                    rows.append([])
                while any(spec["left"] < other["right"] + 8 and spec["left"] + spec["width"] > other["left"] - 8 for other in rows[row]):
                    row += 1
                    while len(rows) <= row:
                        rows.append([])
                spec["row"] = row
                rows[row].append({"left": spec["left"], "right": spec["left"] + spec["width"]})

            top = rect.top() + 34.0
            row_gap = 4.0
            for spec in specs:
                y = top + spec["row"] * (spec["height"] + row_gap) + spec["offset_y"]
                y = max(rect.top() + 4.0, min(y, rect.bottom() - spec["height"] - 4.0))
                spec["item"].setPos(spec["left"], y)
                spec["item"].show()

    @staticmethod
    def _interp_value(time, values, event_time):
        if values.size != time.size or values.size == 0:
            return None
        mask = np.isfinite(time) & np.isfinite(values)
        if not np.any(mask):
            return None
        x = time[mask]
        y = values[mask]
        if event_time < x[0] or event_time > x[-1]:
            return None
        return float(np.interp(event_time, x, y))

    @staticmethod
    def _pressure_limit(test):
        value = getattr(test, "case_pressure_limit_psi", None)
        try:
            parsed = float(value)
            return parsed if parsed > 0 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _test_duration(test):
        values = np.asarray(getattr(test.data, "time_s", []), dtype=float)
        finite = values[np.isfinite(values)] if values.size else values
        return float(finite[-1]) if finite.size else 0.0

    def _add_playback_lines(self):
        for plot in (self.thrust_plot, self.pressure_plot):
            line = pg.InfiniteLine(
                pos=0.0,
                angle=90,
                movable=False,
                pen=pg.mkPen("#e5e7eb", width=1, style=Qt.PenStyle.DashLine),
            )
            plot.addItem(line)
            self._playback_lines.append(line)

    def _set_duration(self, duration_s):
        self._duration_s = max(float(duration_s), 0.0)
        self.slider.blockSignals(True)
        self.slider.setValue(0)
        self.slider.blockSignals(False)
        self.time_label.setText(f"0.000 / {self._duration_s:.3f} s")

    def _slider_changed(self, value):
        if self._duration_s <= 0:
            position = 0.0
        else:
            position = self._duration_s * value / 10000.0
        self._update_playback_position(position)

    def _update_playback_position(self, position_s):
        position_s = max(0.0, min(float(position_s), self._duration_s))
        for line in self._playback_lines:
            line.setValue(position_s)
        self.slider.blockSignals(True)
        value = int(round((position_s / self._duration_s) * 10000)) if self._duration_s else 0
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.time_label.setText(f"{position_s:.3f} / {self._duration_s:.3f} s")

    def set_playback_position(self, position_s):
        """Update the shared comparison playback marker from MainWindow."""
        self._update_playback_position(position_s)

    def _toggle_playback(self):
        if self._duration_s <= 0:
            return
        if self._playing:
            self._stop_playback()
        else:
            self._playing = True
            self.play_button.setText("⏸")
            self._timer.start()

    def _stop_playback(self):
        self._playing = False
        self._timer.stop()
        self.play_button.setText("▶")

    def _reset_playback(self):
        self._stop_playback()
        self._update_playback_position(0.0)

    def _advance_playback(self):
        if self._duration_s <= 0:
            self._stop_playback()
            return
        current = self.slider.value() / 10000.0 * self._duration_s
        next_position = current + 0.03
        if next_position >= self._duration_s:
            self._update_playback_position(self._duration_s)
            self._stop_playback()
        else:
            self._update_playback_position(next_position)

    def _set_event_visibility(self, event_name, visible):
        self._event_visibility[event_name] = bool(visible)
        self._refresh()

    def _set_all_events(self, visible):
        for name, action in self._event_actions.items():
            self._event_visibility[name] = bool(visible)
            action.blockSignals(True)
            action.setChecked(bool(visible))
            action.blockSignals(False)
        self._refresh()

    def _add_table_row(self, test):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._set(row, 0, test.display_name)
        results = test.analysis_results.thrust if test.analysis_results else None
        pressure = np.asarray(getattr(test.data, "pressure_psi", []), dtype=float)
        peak_pressure = None
        if pressure.size == np.asarray(test.data.time_s).size:
            start_time = 0.0
            events = test.analysis_results.events if test.analysis_results else None
            ignition = getattr(events, "ignition", None) if events is not None else None
            if ignition is not None:
                start_time = float(ignition.time_s)
            time = np.asarray(test.data.time_s, dtype=float)
            mask = np.isfinite(time) & np.isfinite(pressure) & (time >= start_time)
            if np.any(mask):
                peak_pressure = float(np.max(pressure[mask]))
        values = [
            results.total_impulse_valid_curve_Ns if results else None,
            results.peak_thrust_N if results else None,
            peak_pressure,
            results.burn_time_5pct_s if results else None,
            results.average_thrust_5pct_N if results else None,
            results.isp_s if results else None,
            results.cstar_m_per_s if results else None,
        ]
        for column, value in enumerate(values, start=1):
            self._set(row, column, self._format(value))
        self.table.resizeColumnsToContents()

    def _set(self, row, column, value):
        self.table.setItem(row, column, QTableWidgetItem(str(value)))

    @staticmethod
    def _format(value):
        return "—" if value is None else f"{float(value):.2f}"
