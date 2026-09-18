from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)


class ResultsPanel(QFrame):
    """
    Displays authoritative rocket motor analysis results,
    detected physical events, and application status.

    The panel performs display formatting only. Engineering
    calculations are performed by the analysis engine.
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

        self.status.setObjectName("statusLabel")

        self.status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(self.status)

    def add_metric(
        self,
        layout,
        name,
        value,
        unit,
    ):
        """Create and add a metric card."""

        card = QFrame()
        card.setObjectName("metricCard")

        # Prevent the card from being vertically compressed enough
        # to clip the metric text.
        card.setMinimumHeight(52)

        card_layout = QHBoxLayout(card)

        card_layout.setContentsMargins(
            12,
            8,
            12,
            8,
        )

        card_layout.setSpacing(6)

        name_label = QLabel(name)
        name_label.setObjectName("metricName")
        name_label.setMinimumHeight(20)

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        value_label.setMinimumHeight(20)

        value_label.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )

        card_layout.addWidget(name_label)
        card_layout.addStretch()
        card_layout.addWidget(value_label)

        if unit:
            unit_label = QLabel(unit)
            unit_label.setObjectName("metricUnit")
            unit_label.setMinimumHeight(20)
            unit_label.setAlignment(
                Qt.AlignmentFlag.AlignVCenter
            )
            card_layout.addWidget(unit_label)

        layout.addWidget(card)

        return value_label

    def add_event(
        self,
        layout,
        name,
        value,
    ):
        """Create and add an event row."""

        row = QFrame()
        row.setObjectName("eventRow")
        row.setMinimumHeight(30)

        row_layout = QHBoxLayout(row)

        row_layout.setContentsMargins(
            8,
            4,
            8,
            4,
        )

        name_label = QLabel(name)
        name_label.setObjectName("eventName")
        name_label.setMinimumHeight(18)

        value_label = QLabel(value)
        value_label.setObjectName("eventValue")
        value_label.setMinimumHeight(18)
        value_label.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )

        row_layout.addWidget(name_label)
        row_layout.addStretch()
        row_layout.addWidget(value_label)

        layout.addWidget(row)

        return value_label

    def set_results(
        self,
        thrust_results,
        events,
        classification,
    ):
        """
        Display authoritative analysis results.

        Key Results come directly from standardized Phase 2
        ThrustResults fields.

        Detected Events come from the authoritative EventSet.

        No engineering calculations are performed here.
        """

        # =========================================================
        # AUTHORITATIVE KEY RESULTS
        # =========================================================

        self.peak_thrust.setText(
            self._format_number(
                thrust_results.peak_thrust_N
            )
        )

        self.average_thrust.setText(
            self._format_number(
                thrust_results.average_thrust_5pct_N
            )
        )

        self.total_impulse.setText(
            self._format_number(
                thrust_results.total_impulse_valid_curve_Ns
            )
        )

        self.burn_time.setText(
            self._format_number(
                thrust_results.burn_time_5pct_s
            )
        )

        self.time_to_peak.setText(
            self._format_number(
                thrust_results.peak_thrust_time_s
            )
        )

        # =========================================================
        # MOTOR CLASS
        # =========================================================

        motor_class = (
            thrust_results.impulse_class
            or classification.motor_class
        )

        self.motor_class.setText(
            motor_class if motor_class else "—"
        )

        # =========================================================
        # AUTHORITATIVE DESIGNATION
        # =========================================================

        self.calculated_designation.setText(
            thrust_results.designation
            if thrust_results.designation
            else "—"
        )

        # =========================================================
        # DETECTED PHYSICAL EVENTS
        # =========================================================

        ignition_event = events.ignition

        if ignition_event is not None:
            self.ignition.setText(
                self._format_number(
                    ignition_event.time_s
                ) + " s"
            )
        else:
            self.ignition.setText("—")

        peak_event = events.peak_thrust

        if peak_event is not None:
            self.peak_event.setText(
                self._format_number(
                    peak_event.time_s
                ) + " s"
            )
        else:
            self.peak_event.setText("—")

        burnout_event = events.burnout

        if burnout_event is not None:
            self.burnout.setText(
                self._format_number(
                    burnout_event.time_s
                ) + " s"
            )
        else:
            self.burnout.setText("—")

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
    def _format_number(value):
        """Format a numeric value for display."""

        if value is None:
            return "—"

        return f"{value:.2f}"
