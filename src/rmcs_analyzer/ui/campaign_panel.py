import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..analysis.campaign_analysis import CampaignAnalyzer, METRIC_DEFINITIONS


class CampaignPanel(QFrame):
    """Population-level analysis of measured motor-test performance."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("campaignWorkspace")
        self.tests = []
        self.checkboxes = []
        self._selected_sources = set()
        self._selection_initialized = False
        self.analyzer = CampaignAnalyzer()
        self._result = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Campaign Analysis")
        title.setObjectName("graphTitle")
        layout.addWidget(title)

        description = QLabel(
            "Analyze measured motor performance across multiple firings. "
            "Campaign analysis summarizes recorded results; it does not simulate motor behavior."
        )
        description.setObjectName("graphDescription")
        description.setWordWrap(True)
        layout.addWidget(description)

        # ---------------------------------------------------------
        # TEST SELECTION
        # ---------------------------------------------------------
        selector_host = QWidget()
        selector_layout = QHBoxLayout(selector_host)
        selector_layout.setContentsMargins(4, 2, 4, 2)
        selector_layout.setSpacing(8)

        self.select_all_button = QPushButton("Select All")
        self.clear_button = QPushButton("Clear All")
        self.select_all_button.clicked.connect(self._select_all)
        self.clear_button.clicked.connect(self._clear_all)
        selector_layout.addWidget(self.select_all_button)
        selector_layout.addWidget(self.clear_button)

        self.test_selector = QScrollArea()
        self.test_selector.setWidgetResizable(True)
        self.test_selector.setMaximumHeight(72)
        self.test_selector.setWidget(selector_host)
        self.selector_layout = selector_layout
        layout.addWidget(self.test_selector)

        self.status = QLabel("Load multiple tests to begin campaign analysis.")
        self.status.setObjectName("graphDescription")
        layout.addWidget(self.status)

        # ---------------------------------------------------------
        # CAMPAIGN KPI STRIP
        # ---------------------------------------------------------
        kpi_layout = QGridLayout()
        kpi_layout.setHorizontalSpacing(6)
        kpi_layout.setVerticalSpacing(6)
        self.kpis = {}
        for index, name in enumerate(
            ("Tests", "Total Impulse", "Peak Thrust", "Burn Time", "Average Thrust", "C*")
        ):
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            box = QVBoxLayout(frame)
            box.setContentsMargins(8, 5, 8, 5)
            box.setSpacing(2)
            label = QLabel(name)
            value = QLabel("—")
            value.setObjectName("sectionTitle")
            box.addWidget(label)
            box.addWidget(value)
            self.kpis[name] = value
            kpi_layout.addWidget(frame, 0, index)
        layout.addLayout(kpi_layout)

        # ---------------------------------------------------------
        # STATISTICS TABLE
        # ---------------------------------------------------------
        self.stats_table = QTableWidget(0, 8)
        self.stats_table.setHorizontalHeaderLabels([
            "Metric", "Tests", "Mean", "Median", "Min", "Max", "Std Dev", "CV (%)",
        ])
        self.stats_table.horizontalHeaderItem(7).setToolTip(
            "Coefficient of Variation: standard deviation / mean × 100%"
        )
        self.stats_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.stats_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.stats_table.setMaximumHeight(180)
        self.stats_table.verticalHeader().setVisible(False)
        header = self.stats_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.stats_table)

        # ---------------------------------------------------------
        # ANALYSIS VIEWS
        # ---------------------------------------------------------
        self.view_tabs = QTabWidget()
        self.view_tabs.setDocumentMode(True)
        self.view_tabs.setObjectName("campaignViewTabs")
        layout.addWidget(self.view_tabs, 1)

        # Metric distribution view.
        metric_view = QWidget()
        metric_layout = QVBoxLayout(metric_view)
        metric_layout.setContentsMargins(2, 4, 2, 2)
        metric_layout.setSpacing(4)

        metric_controls = QHBoxLayout()
        metric_controls.addWidget(QLabel("Metric:"))
        self.metric_combo = QComboBox()
        self.metric_combo.addItems(METRIC_DEFINITIONS.keys())
        self.metric_combo.currentTextChanged.connect(self._refresh_metric_plot)
        metric_controls.addWidget(self.metric_combo)
        metric_controls.addStretch(1)
        metric_layout.addLayout(metric_controls)

        self.metric_plot = pg.PlotWidget()
        self.metric_plot.setBackground("#080e13")
        self.metric_plot.showGrid(x=False, y=True, alpha=0.18)
        metric_layout.addWidget(self.metric_plot, 1)
        self.view_tabs.addTab(metric_view, "Metric Distribution")

        # Campaign thrust curve view.
        curve_view = QWidget()
        curve_layout = QVBoxLayout(curve_view)
        curve_layout.setContentsMargins(2, 4, 2, 2)
        curve_layout.setSpacing(4)

        curve_controls = QHBoxLayout()
        curve_controls.addWidget(QLabel("Curve basis:"))
        self.curve_basis = QComboBox()
        self.curve_basis.addItem("Absolute Burn Time", "absolute")
        self.curve_basis.addItem("Normalized Burn Time", "normalized")
        self.curve_basis.currentIndexChanged.connect(self._refresh)
        curve_controls.addWidget(self.curve_basis)
        self.show_individual = QCheckBox("Individual Tests")
        self.show_individual.setChecked(False)
        self.show_individual.stateChanged.connect(self._refresh_curve_plot)
        curve_controls.addWidget(self.show_individual)
        self.show_minmax = QCheckBox("Min/Max Envelope")
        self.show_minmax.setChecked(False)
        self.show_minmax.stateChanged.connect(self._refresh_curve_plot)
        curve_controls.addWidget(self.show_minmax)
        curve_controls.addStretch(1)
        curve_layout.addLayout(curve_controls)

        self.curve_plot = pg.PlotWidget()
        self.curve_plot.setBackground("#080e13")
        self.curve_plot.setLabel("bottom", "Burn Time", units="s")
        self.curve_plot.setLabel("left", "Thrust", units="N")
        self.curve_plot.showGrid(x=True, y=True, alpha=0.18)
        self.curve_legend = self.curve_plot.addLegend(offset=(10, 10))
        curve_layout.addWidget(self.curve_plot, 1)
        self.view_tabs.addTab(curve_view, "Campaign Thrust Curve")

    def _select_all(self):
        for checkbox in self.checkboxes:
            checkbox.blockSignals(True)
            checkbox.setChecked(True)
            checkbox.blockSignals(False)
        self._refresh()

    def _clear_all(self):
        for checkbox in self.checkboxes:
            checkbox.blockSignals(True)
            checkbox.setChecked(False)
            checkbox.blockSignals(False)
        self._refresh()

    def selected_sources(self):
        """Return the source files currently selected for Campaign Analysis."""
        return set(self._selected_sources)

    def restore_selection(self, selected_sources):
        """Restore a previously saved Campaign Analysis selection.

        ``None`` means no selection state was persisted (legacy project), so
        the panel keeps its normal default of selecting all tests.
        """
        if selected_sources is None:
            return

        selected_sources = set(selected_sources)

        for checkbox in self.checkboxes:
            index = checkbox.property("test_index")
            try:
                index = int(index)
            except (TypeError, ValueError):
                continue

            if index < 0 or index >= len(self.tests):
                continue

            test = self.tests[index]
            checked = bool(
                test.source_file
                and test.source_file in selected_sources
            )

            checkbox.blockSignals(True)
            checkbox.setChecked(checked)
            checkbox.blockSignals(False)

        self._selected_tests()
        self._refresh()

    def _selected_tests(self):
        """Return the currently checked TestModel objects.

        The Campaign panel owns only the selection state. The TestModel
        objects remain the authoritative source for test data and analysis
        results.
        """

        selected = []
        selected_sources = set()

        for checkbox in self.checkboxes:
            if not checkbox.isChecked():
                continue

            index = checkbox.property("test_index")
            if index is None:
                continue

            try:
                index = int(index)
            except (TypeError, ValueError):
                continue

            if index < 0 or index >= len(self.tests):
                continue

            test = self.tests[index]
            selected.append(test)

            if test.source_file:
                selected_sources.add(test.source_file)

        self._selected_sources = selected_sources
        return selected

    def set_tests(self, tests):
        previous = set(self._selected_sources)
        self.tests = list(tests)

        sources = {
            test.source_file
            for test in self.tests
            if test.source_file
        }
        preserved = previous & sources

        # Keep the two fixed controls (Select All / Clear All) and remove
        # every previously created test checkbox. Test checkboxes start at
        # layout index 2 because the selector contains only those two fixed
        # buttons; leaving index 2 behind would create a stale duplicate
        # checkbox every time set_tests() is called.
        while self.selector_layout.count() > 2:
            item = self.selector_layout.takeAt(2)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Disambiguate duplicate filenames in a loaded project.
        name_counts = {}
        for test in self.tests:
            name = test.display_name or "Unnamed Test"
            name_counts[name] = name_counts.get(name, 0) + 1

        name_seen = {}
        self.checkboxes = []
        for index, test in enumerate(self.tests):
            name = test.display_name or f"Test {index + 1}"
            name_seen[name] = name_seen.get(name, 0) + 1
            label = name
            if name_counts[name] > 1:
                label = f"{name} ({name_seen[name]})"

            checkbox = QCheckBox(label)
            checkbox.setProperty("test_index", index)
            checkbox.setChecked(
                test.source_file in preserved
                if self._selection_initialized
                else True
            )
            checkbox.stateChanged.connect(self._refresh)
            self.selector_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        self._selection_initialized = True
        self._refresh()

    def _refresh(self, *args):
        selected = self._selected_tests()
        basis = self.curve_basis.currentData() or "absolute"
        self._result = self.analyzer.analyze(selected, curve_basis=basis)

        if not selected:
            self.status.setText("Select at least one test.")
        else:
            self.status.setText(
                f"{len(selected)} tests selected; {self._result.included_tests} included in analysis."
            )

        self._refresh_kpis()
        self._refresh_table()
        self._refresh_metric_plot()
        self._refresh_curve_plot()

    def _refresh_kpis(self):
        if self._result is None:
            return
        self.kpis["Tests"].setText(str(self._result.included_tests))
        for label, metric in (
            ("Total Impulse", "Total Impulse"),
            ("Peak Thrust", "Peak Thrust"),
            ("Burn Time", "Burn Time"),
            ("Average Thrust", "Average Thrust"),
            ("C*", "C*"),
        ):
            stats = self._result.metrics[metric]
            self.kpis[label].setText(self._format(stats.mean, stats.unit))

    def _refresh_table(self):
        self.stats_table.setRowCount(0)
        if self._result is None:
            return
        for name, stats in self._result.metrics.items():
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)
            values = [
                name,
                f"{stats.count}/{stats.total_tests}",
                self._format(stats.mean, stats.unit),
                self._format(stats.median, stats.unit),
                self._format(stats.minimum, stats.unit),
                self._format(stats.maximum, stats.unit),
                self._format(stats.std_dev, stats.unit),
                "—" if stats.coefficient_variation_percent is None else f"{stats.coefficient_variation_percent:.2f}%",
            ]
            for column, value in enumerate(values):
                self.stats_table.setItem(row, column, QTableWidgetItem(value))
        self.stats_table.resizeColumnsToContents()

    def _refresh_metric_plot(self, *args):
        self.metric_plot.clear()
        if self._result is None:
            return

        metric = self.metric_combo.currentText()
        attribute, unit = METRIC_DEFINITIONS[metric]
        selected = self._selected_tests()
        values = []
        labels = []
        for index, test in enumerate(selected):
            results = test.analysis_results
            value = getattr(results.thrust, attribute, None) if results else None
            if value is not None and np.isfinite(value):
                values.append(float(value))
                labels.append(test.display_name or f"Test {index + 1}")
        if not values:
            self.metric_plot.setLabel("left", metric, units=unit)
            return

        x = np.arange(len(values), dtype=float)
        bars = pg.BarGraphItem(
            x=x,
            height=np.asarray(values),
            width=0.55,
            brush=pg.mkBrush("#2aa9ff"),
            pen=pg.mkPen("#5bc0ff", width=1),
        )
        self.metric_plot.addItem(bars)

        stats = self._result.metrics[metric]
        if stats.mean is not None:
            self.metric_plot.addItem(
                pg.InfiniteLine(
                    pos=stats.mean,
                    angle=0,
                    pen=pg.mkPen("#39d98a", width=2, style=Qt.PenStyle.DashLine),
                    label=f"Mean {stats.mean:,.2f} {unit}",
                    labelOpts={"position": 0.92, "color": "#39d98a"},
                )
            )

        axis = self.metric_plot.getAxis("bottom")
        axis.setTicks([[(i, label) for i, label in enumerate(labels)]])
        self.metric_plot.setLabel("left", metric, units=unit)
        self.metric_plot.setLabel("bottom", "Test")

        # Keep campaign bars visually proportional and leave useful breathing
        # room around a single test. PyQtGraph's default auto-range can make a
        # single bar expand to nearly the entire plot width.
        count = len(values)
        self.metric_plot.setXRange(-0.75, max(0.75, count - 0.25), padding=0.0)
        finite_values = np.asarray(values, dtype=float)
        finite_values = finite_values[np.isfinite(finite_values)]
        if finite_values.size:
            low = float(np.min(finite_values))
            high = float(np.max(finite_values))
            if low == high:
                magnitude = max(abs(high), 1.0)
                if low >= 0:
                    low = 0.0
                    high = magnitude * 1.12
                else:
                    span = magnitude * 0.12
                    low -= span
                    high += span
            else:
                span = high - low
                low -= span * 0.08
                high += span * 0.08
            self.metric_plot.setYRange(low, high, padding=0.0)

    def _refresh_curve_plot(self):
        self.curve_plot.clear()
        self.curve_legend = self.curve_plot.addLegend(offset=(10, 10))
        if self._result is None or self._result.curve is None:
            return

        curve = self._result.curve
        x = curve.time

        # Individual tests use a small, deterministic palette so separate
        # firings are easy to distinguish without overpowering the summary.
        individual_colors = [
            "#2aa9ff", "#ffb84d", "#39d98a", "#b388ff", "#ff6b6b",
            "#5ee7df", "#f78fb3", "#82b1ff",
        ]
        if self.show_individual.isChecked():
            for index, (individual_x, individual_y) in enumerate(curve.individual_curves):
                color = individual_colors[index % len(individual_colors)]
                self.curve_plot.plot(
                    individual_x,
                    individual_y,
                    pen=pg.mkPen(color, width=1.25),
                    name=f"Test {index + 1}",
                )

        # Mean is the primary campaign result; median is a secondary robust
        # statistic. The variability band is visually distinct from both.
        mean_curve = self.curve_plot.plot(
            x,
            curve.mean,
            pen=pg.mkPen("#2aa9ff", width=3),
            name="Mean",
        )
        median_curve = self.curve_plot.plot(
            x,
            curve.median,
            pen=pg.mkPen("#ffb84d", style=Qt.PenStyle.DashLine, width=2),
            name="Median",
        )

        upper = curve.mean + curve.std_dev
        lower = curve.mean - curve.std_dev
        finite = np.isfinite(x) & np.isfinite(upper) & np.isfinite(lower)
        if np.any(finite):
            upper_curve = self.curve_plot.plot(
                x[finite],
                upper[finite],
                pen=pg.mkPen("#39d98a", style=Qt.PenStyle.DotLine, width=1.5),
                name="Mean ±1σ",
            )
            lower_curve = self.curve_plot.plot(
                x[finite],
                lower[finite],
                pen=pg.mkPen("#39d98a", style=Qt.PenStyle.DotLine, width=1.5),
            )
            band = pg.FillBetweenItem(
                upper_curve,
                lower_curve,
                brush=pg.mkBrush(57, 217, 138, 35),
            )
            self.curve_plot.addItem(band)

        if self.show_minmax.isChecked():
            envelope = np.isfinite(x) & np.isfinite(curve.minimum) & np.isfinite(curve.maximum)
            if np.any(envelope):
                self.curve_plot.plot(
                    x[envelope],
                    curve.minimum[envelope],
                    pen=pg.mkPen("#aab4bf", style=Qt.PenStyle.DashDotLine, width=1),
                    name="Min/Max",
                )
                self.curve_plot.plot(
                    x[envelope],
                    curve.maximum[envelope],
                    pen=pg.mkPen("#aab4bf", style=Qt.PenStyle.DashDotLine, width=1),
                )

        self.curve_plot.setLabel(
            "bottom",
            "Normalized Burn Time" if curve.basis == "normalized" else "Burn Time",
            units="%" if curve.basis == "normalized" else "s",
        )
        if curve.basis == "normalized":
            self.curve_plot.setXRange(0, 1, padding=0.03)

    @staticmethod
    def _format(value, unit):
        if value is None:
            return "—"
        if unit == "s" or unit == "m/s":
            return f"{float(value):.2f} {unit}"
        return f"{float(value):,.2f} {unit}"
