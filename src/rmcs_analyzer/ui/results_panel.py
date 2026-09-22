from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class ResultsPanel(QFrame):
    """
    Displays authoritative rocket motor analysis results,
    detected physical events, and application status.

    The panel performs display formatting only. Engineering
    calculations are performed by the analysis engine.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("keyResultsPanel")
        self.setMinimumWidth(285)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(7)

        title = QLabel("Key Results")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.current_thrust = self.add_metric(layout, "●", "Current Thrust", "—", "N")
        self.peak_thrust = self.add_metric(layout, "▲", "Peak Thrust", "—", "N")
        self.average_thrust = self.add_metric(layout, "▥", "Average Thrust", "—", "N")
        self.total_impulse = self.add_metric(layout, "Σ", "Total Impulse", "—", "N·s")
        self.burn_time = self.add_metric(layout, "◷", "Burn Time", "—", "s")
        self.time_to_peak = self.add_metric(layout, "△", "Time to Peak", "—", "s")
        self.specific_impulse = self.add_metric(layout, "◌", "Specific Impulse", "—", "s")
        self.peak_pressure = self.add_metric(layout, "◉", "Peak Pressure", "—", "psi")

        layout.addSpacing(5)

        events_title = QLabel("Detected Events")
        events_title.setObjectName("sectionTitle")
        layout.addWidget(events_title)

        self.ignition = self.add_event(layout, "eventDotIgnition", "Ignition", "—")
        self.peak_event = self.add_event(layout, "eventDotPeak", "Peak Thrust", "—")
        self.burnout = self.add_event(layout, "eventDotBurnout", "Burnout", "—")

        layout.addStretch(1)

        self.status = QLabel("READY — No test loaded")
        self.status.setObjectName("statusLabel")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)

    def add_metric(self, layout, icon, name, value, unit):
        card = QFrame()
        card.setObjectName("metricCard")
        card.setMinimumHeight(47)

        row = QHBoxLayout(card)
        row.setContentsMargins(9, 5, 9, 5)
        row.setSpacing(7)

        icon_label = QLabel(icon)
        icon_label.setObjectName("metricIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(icon_label)

        name_label = QLabel(name)
        name_label.setObjectName("metricName")
        row.addWidget(name_label)

        row.addStretch(1)

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(value_label)

        if unit:
            unit_label = QLabel(unit)
            unit_label.setObjectName("metricUnit")
            row.addWidget(unit_label)

        layout.addWidget(card)
        return value_label

    def add_event(self, layout, dot_object, name, value):
        row = QFrame()
        row.setObjectName("eventRow")
        row.setMinimumHeight(30)

        h = QHBoxLayout(row)
        h.setContentsMargins(8, 4, 8, 4)
        h.setSpacing(8)

        dot = QLabel()
        dot.setObjectName(dot_object)
        dot.setFixedSize(7, 7)
        h.addWidget(dot)

        name_label = QLabel(name)
        name_label.setObjectName("eventName")
        h.addWidget(name_label)
        h.addStretch(1)

        value_label = QLabel(value)
        value_label.setObjectName("eventValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        h.addWidget(value_label)

        layout.addWidget(row)
        return value_label

    def set_results(self, thrust_results, events, classification):
        self.current_thrust.setText("—")
        self.peak_thrust.setText(self._format_number(thrust_results.peak_thrust_N))
        self.average_thrust.setText(self._format_number(thrust_results.average_thrust_5pct_N))
        self.total_impulse.setText(self._format_number(thrust_results.total_impulse_valid_curve_Ns))
        self.burn_time.setText(self._format_number(thrust_results.burn_time_5pct_s))
        self.time_to_peak.setText(self._format_number(thrust_results.peak_thrust_time_s))

        self.specific_impulse.setText(
            self._format_number(thrust_results.isp_s)
        )
        self.peak_pressure.setText(
            self._format_number(thrust_results.peak_pressure_psi)
        )

        ignition_event = events.ignition
        self.ignition.setText(
            self._format_number(ignition_event.time_s) + " s"
            if ignition_event is not None else "—"
        )

        peak_event = events.peak_thrust
        self.peak_event.setText(
            self._format_number(peak_event.time_s) + " s"
            if peak_event is not None else "—"
        )

        burnout_event = events.burnout
        self.burnout.setText(
            self._format_number(burnout_event.time_s) + " s"
            if burnout_event is not None else "—"
        )

    def clear_results(self):
        for widget in (
            self.current_thrust, self.peak_thrust, self.average_thrust, self.total_impulse,
            self.burn_time, self.time_to_peak, self.specific_impulse,
            self.peak_pressure, self.ignition, self.peak_event,
            self.burnout
        ):
            widget.setText("—")

    def set_current_thrust(self, value):
        self.current_thrust.setText(self._format_number(value))

    @staticmethod
    def _format_number(value):
        return "—" if value is None else f"{value:.2f}"
