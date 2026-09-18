from typing import Optional

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..data.models import TestData


class DataTable(QFrame):
    """
    Read-only display of the standardized sample-level TestData.

    The table displays the same TestData used by the default analysis
    path. It performs no calculations and does not modify the data.
    """

    COLUMNS = (
        ("Sample", "sample"),
        ("Time (s)", "time"),
        ("Time Cal (s)", "calibrated_time"),
        ("Raw Thrust (N)", "raw_thrust"),
        ("Prop Loss (kg)", "prop_loss"),
        ("Thrust (N)", "thrust"),
        ("Pressure (psi)", "pressure"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("subPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 0)

        title = QLabel("SAMPLE DATA")
        title.setObjectName("sectionTitle")

        self.summary = QLabel("No test loaded")
        self.summary.setObjectName("graphDescription")
        self.summary.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.summary)

        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setObjectName("dataTable")
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(
            [label for label, _ in self.COLUMNS]
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setWordWrap(False)
        self.table.setShowGrid(True)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)

        layout.addWidget(self.table, 1)

        self.clear()

    def set_data(self, data: Optional[TestData]):
        """Display the supplied TestData without modifying it."""

        self.table.setSortingEnabled(False)
        self.table.clearContents()

        if data is None or data.sample_count == 0:
            self.table.setRowCount(0)
            self.summary.setText("No test loaded")
            return

        row_count = data.sample_count
        self.table.setRowCount(row_count)

        time_s = np.asarray(data.time_s, dtype=float)
        thrust_N = np.asarray(data.thrust_N, dtype=float)

        calibrated = self._optional_channel(
            data.calibrated_time_s,
            row_count,
        )
        raw_thrust = self._optional_channel(
            data.raw_thrust_N,
            row_count,
        )
        prop_loss = self._optional_channel(
            data.prop_loss_kg,
            row_count,
        )
        pressure = self._optional_channel(
            data.pressure_psi,
            row_count,
        )

        channels = (
            time_s,
            calibrated,
            raw_thrust,
            prop_loss,
            thrust_N,
            pressure,
        )

        for row in range(row_count):
            # The current TestData model does not retain the source
            # Sample column separately. Until that model is expanded,
            # the table displays the sample's position in the loaded
            # standardized measurement sequence.
            self._set_item(
                row,
                0,
                str(row + 1),
                align_right=True,
            )

            for column_offset, values in enumerate(channels, start=1):
                value = values[row]

                if value is None or not np.isfinite(value):
                    text = ""
                else:
                    text = self._format_channel(
                        value,
                        column_offset,
                    )

                self._set_item(
                    row,
                    column_offset,
                    text,
                    align_right=True,
                )

        self.table.resizeColumnsToContents()

        # Keep the table usable at the normal application width.
        minimum_widths = (
            70,
            105,
            125,
            125,
            115,
            105,
            115,
        )

        for index, width in enumerate(minimum_widths):
            if self.table.columnWidth(index) < width:
                self.table.setColumnWidth(index, width)

        self.summary.setText(
            f"{row_count:,} samples"
        )

    def clear(self):
        """Clear all displayed sample data."""

        self.table.clearContents()
        self.table.setRowCount(0)
        self.summary.setText("No test loaded")

    def _set_item(
        self,
        row: int,
        column: int,
        text: str,
        align_right: bool = False,
    ):
        item = QTableWidgetItem(text)

        if align_right:
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

        self.table.setItem(row, column, item)

    @staticmethod
    def _optional_channel(
        values,
        expected_length: int,
    ):
        if values is None:
            return None

        array = np.asarray(values, dtype=float)

        if array.shape != (expected_length,):
            return None

        return array

    @staticmethod
    def _format_channel(value, column):
        """Format displayed numeric precision by measurement column."""

        if column in (1, 2):
            return f"{value:.6f}"

        if column == 3:
            return f"{value:.3f}"

        if column == 4:
            return f"{value:.6f}"

        if column == 5:
            return f"{value:.6f}"

        if column == 6:
            return f"{value:.3f}"

        return f"{value:.6f}"
