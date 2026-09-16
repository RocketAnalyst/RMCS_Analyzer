from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)


class ResultsPanel(QFrame):
    """
    Displays calculated rocket motor analysis results,
    detected events, and application status.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("panel")
        self.setFixedWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # =========================================================
        # KEY RESULTS
        # =========================================================

        title = QLabel("KEY RESULTS")
        title.setObjectName("sectionTitle")

        layout.addWidget(title)

        self.peak_thrust = self.add_metric(
            layout,
            "Peak Thrust",
            "—",
            "N",
        )

        self.average_thrust = self.add_metric(
            layout,
            "Average Thrust",
            "—",
            "N",
        )

        self.total_impulse = self.add_metric(
            layout,
            "Total Impulse",
            "—",
            "N·s",
        )

        self.burn_time = self.add_metric(
            layout,
            "Burn Time",
            "—",
            "s",
        )

        self.time_to_peak = self.add_metric(
            layout,
            "Time to Peak",
            "—",
            "s",
        )

        self.motor_class = self.add_metric(
            layout,
            "Motor Class",
            "—",
            "",
        )

        self.calculated_designation = self.add_metric(
            layout,
            "Calculated Designation",
            "—",
            "",
        )

        # =========================================================
        # DETECTED EVENTS
        # =========================================================

        layout.addSpacing(8)

        events_title = QLabel("DETECTED EVENTS")
        events_title.setObjectName("sectionTitle")

        layout.addWidget(events_title)

        self.ignition = self.add_event(
            layout,
            "Ignition",
            "—",
        )

        self.peak_event = self.add_event(
            layout,
            "Peak Thrust",
            "—",
        )

        self.burnout = self.add_event(
            layout,
            "Burnout",
            "—",
        )

        layout.addStretch()

        # =========================================================
        # STATUS
        # =========================================================

        self.status = QLabel(
            "READY — No test loaded"
        )

        self.status.setObjectName(
            "statusLabel"
        )

        self.status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            self.status
        )

    def add_metric(
        self,
        layout,
        name,
        value,
        unit,
    ):
        """Create and add a metric card."""

        card = QFrame()
        card.setObjectName(
            "metricCard"
        )

        card_layout = QHBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        name_label = QLabel(
            name
        )

        name_label.setObjectName(
            "metricName"
        )

        value_label = QLabel(
            value
        )

        value_label.setObjectName(
            "metricValue"
        )

        value_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        card_layout.addWidget(
            name_label
        )

        card_layout.addStretch()

        card_layout.addWidget(
            value_label
        )

        if unit:
            unit_label = QLabel(
                unit
            )

            unit_label.setObjectName(
                "metricUnit"
            )

            card_layout.addWidget(
                unit_label
            )

        layout.addWidget(
            card
        )

        return value_label

    def add_event(
        self,
        layout,
        name,
        value,
    ):
        """Create and add an event row."""

        row = QFrame()

        row.setObjectName(
            "eventRow"
        )

        row_layout = QHBoxLayout(
            row
        )

        row_layout.setContentsMargins(
            8,
            6,
            8,
            6,
        )

        name_label = QLabel(
            name
        )

        name_label.setObjectName(
            "eventName"
        )

        value_label = QLabel(
            value
        )

        value_label.setObjectName(
            "eventValue"
        )

        row_layout.addWidget(
            name_label
        )

        row_layout.addStretch()

        row_layout.addWidget(
            value_label
        )

        layout.addWidget(
            row
        )

        return value_label

    def set_results(
        self,
        thrust_results,
        events,
        classification,
    ):
        """
        Display calculated analysis results.
        """

        # =========================================================
        # KEY RESULTS
        # =========================================================

        self.peak_thrust.setText(
            self._format_value(
                thrust_results.peak_thrust_N,
                "N",
            )
        )

        self.average_thrust.setText(
            self._format_value(
                thrust_results.average_thrust_N,
                "N",
            )
        )

        self.total_impulse.setText(
            self._format_value(
                thrust_results.total_impulse_Ns,
                "N·s",
            )
        )

        self.burn_time.setText(
            self._format_value(
                thrust_results.burn_time_s,
                "s",
            )
        )

        self.time_to_peak.setText(
            self._format_value(
                thrust_results.time_to_peak_s,
                "s",
            )
        )

        # Motor impulse classification
        if classification.motor_class:
            self.motor_class.setText(
                classification.motor_class
            )
        else:
            self.motor_class.setText(
                "—"
            )

        # Calculated designation:
        # impulse class + rounded measured average thrust.
        if (
            classification.motor_class
            and thrust_results.average_thrust_N
            is not None
        ):
            average_thrust = round(
                thrust_results.average_thrust_N
            )

            designation = (
                f"{classification.motor_class}"
                f"{average_thrust}"
            )

            self.calculated_designation.setText(
                designation
            )

        else:
            self.calculated_designation.setText(
                "—"
            )

        # =========================================================
        # DETECTED EVENTS
        # =========================================================

        self.ignition.setText(
            self._format_value(
                events.ignition_time_s,
                "s",
            )
        )

        self.peak_event.setText(
            self._format_value(
                events.peak_time_s,
                "s",
            )
        )

        self.burnout.setText(
            self._format_value(
                events.burnout_time_s,
                "s",
            )
        )

    def clear_results(self):
        """Reset displayed analysis results."""

        self.peak_thrust.setText("—")
        self.average_thrust.setText("—")
        self.total_impulse.setText("—")
        self.burn_time.setText("—")
        self.time_to_peak.setText("—")
        self.motor_class.setText("—")
        self.calculated_designation.setText("—")

        self.ignition.setText("—")
        self.peak_event.setText("—")
        self.burnout.setText("—")

    @staticmethod
    def _format_value(
        value,
        unit,
    ):
        """Format an analysis value for display."""

        if value is None:
            return "—"

        return f"{value:.2f} {unit}"