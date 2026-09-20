import numpy as np
import pyqtgraph as pg

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ComparePanel(QFrame):
    """Compare multiple loaded tests without changing individual-test state."""

    selection_changed = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("compareWorkspace")
        self.tests = []
        self.checkboxes = []
        self._selected_sources = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QLabel("Test Comparison")
        header.setObjectName("graphTitle")
        layout.addWidget(header)

        description = QLabel(
            "Select two or more loaded tests to compare their measured thrust curves "
            "and key performance results."
        )
        description.setObjectName("graphDescription")
        description.setWordWrap(True)
        layout.addWidget(description)

        self.test_selector = QScrollArea()
        self.test_selector.setWidgetResizable(True)
        self.test_selector.setMaximumHeight(110)
        selector_host = QWidget()
        self.selector_layout = QHBoxLayout(selector_host)
        self.selector_layout.setContentsMargins(4, 2, 4, 2)
        self.selector_layout.setSpacing(14)
        self.test_selector.setWidget(selector_host)
        layout.addWidget(self.test_selector)

        self.status = QLabel("Load multiple tests to begin comparison.")
        self.status.setObjectName("graphDescription")
        layout.addWidget(self.status)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#080e13")
        self.plot.setLabel("bottom", "Time", units="s", color="#9aabb8")
        self.plot.setLabel("left", "Thrust", units="N", color="#9aabb8")
        self.plot.showGrid(x=True, y=True, alpha=0.18)
        self.plot.setMouseEnabled(x=True, y=True)
        self.legend = self.plot.addLegend(offset=(10, 10))
        layout.addWidget(self.plot, 1)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "Test", "Total Impulse (N·s)", "Peak Thrust (N)",
            "Burn Time (s)", "Average Thrust (N)", "Isp (s)", "C* (m/s)"
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 0)

    def set_tests(self, tests, active_test=None):
        previous_sources = set(self._selected_sources)
        self.tests = list(tests)

        current_sources = {
            test.source_file
            for test in self.tests
            if test.source_file
        }
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
                checked = test is active_test or len(self.tests) == 1
            checkbox.setChecked(checked)
            checkbox.stateChanged.connect(self._refresh)
            checkbox.setProperty("test_index", index)
            self.selector_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        self.selector_layout.addStretch(1)
        self._refresh()

    def _selected_tests(self):
        selected = [
            self.tests[int(cb.property("test_index"))]
            for cb in self.checkboxes
            if cb.isChecked()
        ]
        self._selected_sources = {
            test.source_file
            for test in selected
            if test.source_file
        }
        return selected

    def _refresh(self, *args):
        selected = self._selected_tests()
        self.plot.clear()
        self.legend = self.plot.addLegend(offset=(10, 10))
        self.table.setRowCount(0)

        if not selected:
            self.status.setText("Select at least one test.")
            return

        if len(selected) == 1:
            self.status.setText("Select another test to compare multiple firings.")
        else:
            self.status.setText(f"Comparing {len(selected)} tests.")

        plotted = 0
        for test in selected:
            time = np.asarray(test.data.time_s, dtype=float)
            thrust = np.asarray(test.data.thrust_N, dtype=float)
            mask = np.isfinite(time) & np.isfinite(thrust)
            if not np.any(mask):
                continue

            # pyqtgraph's ``values`` argument is a count of brightness
            # values, not a brightness fraction.  A fractional value such
            # as 0.95 becomes zero internally and causes division by zero.
            color = pg.intColor(
                plotted,
                hues=max(len(selected), 1),
                values=1,
            )

            self.plot.plot(
                time[mask],
                thrust[mask],
                pen=pg.mkPen(color=color, width=2),
                name=test.display_name,
            )
            plotted += 1

            row = self.table.rowCount()
            self.table.insertRow(row)
            self._set(row, 0, test.display_name)

            results = test.analysis_results.thrust if test.analysis_results else None
            values = [
                results.total_impulse_valid_curve_Ns if results else None,
                results.peak_thrust_N if results else None,
                results.burn_time_5pct_s if results else None,
                results.average_thrust_5pct_N if results else None,
                results.isp_s if results else None,
                results.cstar_m_per_s if results else None,
            ]

            for column, value in enumerate(values, start=1):
                self._set(row, column, self._format(value))

        self.table.resizeColumnsToContents()

        # The normal Thrust Curve workspace explicitly establishes its
        # initial viewport. Compare needs to do the same after all selected
        # curves are added; otherwise pyqtgraph can retain a broad default
        # viewport that makes smaller curves appear tiny.
        if plotted:
            self.plot.getViewBox().autoRange(padding=0.08)

    def _set(self, row, column, value):
        self.table.setItem(row, column, QTableWidgetItem(str(value)))

    @staticmethod
    def _format(value):
        return "—" if value is None else f"{float(value):.2f}"
