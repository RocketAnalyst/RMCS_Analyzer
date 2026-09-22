from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class AnalysisPanel(QFrame):
    """
    Detailed engineering summary of the authoritative RMCS results.

    This widget performs no engineering calculations. Values are supplied
    by the analysis layer and metadata model and are formatted for display
    only.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("analysisPanel")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(8, 8, 8, 8)
        outer_layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(10)

        title = QLabel("ENGINEERING ANALYSIS")
        title.setObjectName("sectionTitle")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "Standardized motor-performance results, test characteristics, "
            "and available engineering calculations."
        )
        subtitle.setObjectName("graphDescription")
        content_layout.addWidget(subtitle)

        # =========================================================
        # TEST / MOTOR
        # =========================================================

        motor_group, motor_grid = self._create_group("TEST & MOTOR")
        content_layout.addWidget(motor_group)

        self.motor_designation = self._add_metric(
            motor_grid, 0, 0, "Motor Designation", "—", ""
        )
        self.motor_type = self._add_metric(
            motor_grid, 0, 1, "Motor Type", "—", ""
        )
        self.manufacturer = self._add_metric(
            motor_grid, 1, 0, "Manufacturer", "—", ""
        )
        self.builder = self._add_metric(
            motor_grid, 1, 1, "Builder", "—", ""
        )
        self.propellant_type = self._add_metric(
            motor_grid, 2, 0, "Propellant", "—", ""
        )
        self.case_material = self._add_metric(
            motor_grid, 2, 1, "Case Material", "—", ""
        )

        # =========================================================
        # THRUST PERFORMANCE
        # =========================================================

        thrust_group, thrust_grid = self._create_group(
            "THRUST PERFORMANCE"
        )
        content_layout.addWidget(thrust_group)

        self.peak_thrust = self._add_metric(
            thrust_grid, 0, 0, "Peak Thrust", "—", "N"
        )
        self.peak_time = self._add_metric(
            thrust_grid, 0, 1, "Peak Thrust Time", "—", "s"
        )
        self.average_thrust = self._add_metric(
            thrust_grid, 1, 0, "Average Thrust (5%)", "—", "N"
        )
        self.initial_average = self._add_metric(
            thrust_grid, 1, 1, "Initial Thrust Average", "—", "N"
        )
        self.rise_rate = self._add_metric(
            thrust_grid, 2, 0, "Thrust Rise Rate", "—", "N/s"
        )
        self.decay_rate = self._add_metric(
            thrust_grid, 2, 1, "Thrust Decay Rate", "—", "N/s"
        )

        # =========================================================
        # BURN CHARACTERISTICS
        # =========================================================

        burn_group, burn_grid = self._create_group(
            "BURN CHARACTERISTICS"
        )
        content_layout.addWidget(burn_group)

        self.threshold = self._add_metric(
            burn_grid, 0, 0, "5% Threshold", "—", "N"
        )
        self.burn_start = self._add_metric(
            burn_grid, 0, 1, "5% Burn Start", "—", "s"
        )
        self.burn_end = self._add_metric(
            burn_grid, 1, 0, "5% Burn End", "—", "s"
        )
        self.burn_time = self._add_metric(
            burn_grid, 1, 1, "Standardized Burn Time", "—", "s"
        )
        self.ignition_time = self._add_metric(
            burn_grid, 2, 0, "Ignition", "—", "s"
        )
        self.burnout_time = self._add_metric(
            burn_grid, 2, 1, "Burnout", "—", "s"
        )

        burn_note = QLabel(
            "Burn time uses the standardized 5% of peak-thrust threshold. "
            "Burnout is the detected end-of-motor-action event and may "
            "differ from the standardized burn-time endpoint."
        )
        burn_note.setObjectName("graphDescription")
        burn_note.setWordWrap(True)
        burn_grid.addWidget(burn_note, 3, 0, 1, 2)

        # =========================================================
        # IMPULSE / EFFICIENCY
        # =========================================================

        impulse_group, impulse_grid = self._create_group(
            "IMPULSE & EFFICIENCY"
        )
        content_layout.addWidget(impulse_group)

        self.total_impulse = self._add_metric(
            impulse_grid, 0, 0, "Total Impulse", "—", "N·s"
        )
        self.normalized_impulse = self._add_metric(
            impulse_grid, 0, 1, "5% Normalized Impulse", "—", "N·s"
        )
        self.impulse_class = self._add_metric(
            impulse_grid, 1, 0, "Impulse Class", "—", ""
        )
        self.designation = self._add_metric(
            impulse_grid, 1, 1, "Calculated Designation", "—", ""
        )
        self.isp = self._add_metric(
            impulse_grid, 2, 0, "Specific Impulse", "—", "s"
        )
        self.cstar = self._add_metric(
            impulse_grid, 2, 1, "Characteristic Velocity", "—", "m/s"
        )

        # =========================================================
        # PRESSURE / NOZZLE
        # =========================================================

        pressure_group, pressure_grid = self._create_group(
            "PRESSURE & NOZZLE"
        )
        content_layout.addWidget(pressure_group)

        self.average_pressure = self._add_metric(
            pressure_grid, 0, 0, "Average Chamber Pressure", "—", "psi"
        )
        self.pressure_limit = self._add_metric(
            pressure_grid, 0, 1, "Case Pressure Limit", "—", "psi"
        )
        self.average_mass_flow = self._add_metric(
            pressure_grid, 1, 0, "Average Mass Flow", "—", "kg/s"
        )
        self.throat_diameter = self._add_metric(
            pressure_grid, 1, 1, "Nozzle Throat Diameter", "—", "in"
        )
        self.exit_diameter = self._add_metric(
            pressure_grid, 2, 0, "Nozzle Exit Diameter", "—", "in"
        )
        self.nozzle_material = self._add_metric(
            pressure_grid, 2, 1, "Nozzle Material", "—", ""
        )
        self.load_cell = self._add_metric(
            pressure_grid, 3, 0, "Load Cell", "—", ""
        )
        self.pressure_sensor = self._add_metric(
            pressure_grid, 3, 1, "Pressure Sensor", "—", ""
        )

        # =========================================================
        # TEST DATA
        # =========================================================

        data_group, data_grid = self._create_group(
            "TEST DATA & RECORDING"
        )
        content_layout.addWidget(data_group)

        self.sample_count = self._add_metric(
            data_grid, 0, 0, "Samples", "—", ""
        )
        self.sample_rate = self._add_metric(
            data_grid, 0, 1, "Sample Rate", "—", "Hz"
        )
        self.recorded_duration = self._add_metric(
            data_grid, 1, 0, "Recorded Duration", "—", "s"
        )
        self.minimum_thrust = self._add_metric(
            data_grid, 1, 1, "Minimum Recorded Thrust", "—", "N"
        )
        self.maximum_thrust = self._add_metric(
            data_grid, 2, 0, "Maximum Recorded Thrust", "—", "N"
        )
        self.initial_mass = self._add_metric(
            data_grid, 2, 1, "Initial Mass", "—", "g"
        )
        self.propellant_mass = self._add_metric(
            data_grid, 3, 0, "Propellant Mass", "—", "g"
        )
        self.motor_diameter = self._add_metric(
            data_grid, 3, 1, "Motor Diameter", "—", "mm"
        )
        self.motor_length = self._add_metric(
            data_grid, 4, 0, "Motor Length", "—", "mm"
        )
        self.baseline_mean = self._add_metric(
            data_grid, 4, 1, "Baseline Mean", "—", "N"
        )
        self.baseline_std = self._add_metric(
            data_grid, 5, 0, "Baseline Std. Dev.", "—", "N"
        )

        self.data_note = QLabel()
        self.data_note.setObjectName("graphDescription")
        self.data_note.setWordWrap(True)
        data_grid.addWidget(
            self.data_note, 5, 1, 1, 1
        )

        # =========================================================
        # STATUS / LIMITATIONS
        # =========================================================

        status_group, status_layout = self._create_vertical_group(
            "CALCULATION STATUS"
        )
        content_layout.addWidget(status_group)

        self.cstar_status = QLabel("C* unavailable")
        self.cstar_status.setObjectName("metricValueSmall")
        status_layout.addWidget(self.cstar_status)

        self.status_description = QLabel()
        self.status_description.setObjectName("graphDescription")
        self.status_description.setWordWrap(True)
        status_layout.addWidget(self.status_description)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        self.clear_results()

    def _create_group(self, title):
        group = QFrame()
        group.setObjectName("analysisGroup")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(7)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(32)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        layout.addLayout(grid)

        return group, grid

    def _create_vertical_group(self, title):
        group = QFrame()
        group.setObjectName("analysisGroup")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(7)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)

        return group, layout

    def _add_metric(self, grid, row, column, name, value, unit):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        name_label = QLabel(name)
        name_label.setObjectName("metricName")

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        value_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )
        value_label.setMinimumWidth(85)

        unit_label = QLabel(unit)
        unit_label.setObjectName("metricUnit")
        unit_label.setMinimumWidth(38)

        layout.addWidget(name_label, 1)
        layout.addWidget(value_label, 0)
        layout.addWidget(unit_label, 0)

        grid.addWidget(container, row, column)
        return value_label

    def set_results(
        self,
        thrust_results,
        statistics,
        classification,
        recorded_duration_s=None,
        metadata=None,
        events=None,
    ):
        """Display authoritative analysis results and test metadata."""

        self._set_value(self.peak_thrust, thrust_results.peak_thrust_N)
        self._set_value(self.peak_time, thrust_results.peak_thrust_time_s)
        self._set_value(
            self.average_thrust,
            thrust_results.average_thrust_5pct_N,
        )
        self._set_value(
            self.initial_average,
            thrust_results.initial_thrust_average_N,
        )
        self._set_value(
            self.rise_rate,
            thrust_results.thrust_rise_rate_N_per_s,
        )
        self._set_value(
            self.decay_rate,
            thrust_results.thrust_decay_rate_N_per_s,
        )

        self._set_value(
            self.threshold,
            thrust_results.threshold_thrust_N,
        )
        self._set_value(
            self.burn_start,
            thrust_results.burn_start_5pct_time_s,
        )
        self._set_value(
            self.burn_end,
            thrust_results.burn_end_5pct_time_s,
        )
        self._set_value(
            self.burn_time,
            thrust_results.burn_time_5pct_s,
        )

        ignition = events.ignition if events is not None else None
        burnout = events.burnout if events is not None else None
        self._set_value(
            self.ignition_time,
            ignition.time_s if ignition is not None else None,
        )
        self._set_value(
            self.burnout_time,
            burnout.time_s if burnout is not None else None,
        )

        self._set_value(
            self.total_impulse,
            thrust_results.total_impulse_valid_curve_Ns,
        )
        self._set_value(
            self.normalized_impulse,
            thrust_results.normalized_impulse_Ns,
        )

        self.impulse_class.setText(
            classification.motor_class
            if classification.motor_class
            else "—"
        )
        self.designation.setText(
            thrust_results.designation
            if thrust_results.designation
            else "—"
        )

        self._set_value(
            self.isp,
            thrust_results.isp_s,
        )
        self._set_value(
            self.cstar,
            thrust_results.cstar_m_per_s,
        )
        self._set_value(
            self.average_pressure,
            thrust_results.average_chamber_pressure_psi,
        )
        self._set_value(
            self.average_mass_flow,
            thrust_results.average_mass_flow_kg_per_s,
        )

        self._set_count(
            self.sample_count,
            statistics.sample_count,
        )
        self._set_value(
            self.sample_rate,
            statistics.sample_rate_hz,
        )
        self._set_value(
            self.recorded_duration,
            recorded_duration_s,
        )
        self._set_value(
            self.minimum_thrust,
            statistics.minimum_thrust_N,
        )
        self._set_value(
            self.maximum_thrust,
            statistics.maximum_thrust_N,
        )
        self._set_value(
            self.baseline_mean,
            statistics.baseline_mean_N,
        )
        self._set_value(
            self.baseline_std,
            statistics.baseline_std_N,
        )

        if metadata is not None:
            self._set_text(self.motor_designation, metadata.motor_designation)
            self._set_text(self.motor_type, metadata.motor_type)
            self._set_text(self.manufacturer, metadata.manufacturer)
            self._set_text(self.builder, metadata.builder)
            self._set_text(self.propellant_type, metadata.propellant_type)
            self._set_text(self.case_material, metadata.case_material)
            self._set_value(self.initial_mass, metadata.initial_mass)
            self._set_value(self.propellant_mass, metadata.propellant_mass)
            self._set_value(self.motor_diameter, metadata.motor_diameter)
            self._set_value(self.motor_length, metadata.motor_length)
            self._set_value(self.throat_diameter, metadata.nozzle_throat)
            self._set_value(self.exit_diameter, metadata.nozzle_exit)
            self._set_text(self.nozzle_material, metadata.nozzle_material)
            self._set_text(self.load_cell, metadata.load_cell)
            self._set_text(self.pressure_sensor, metadata.pressure_sensor)
            self._set_value(
                self.pressure_limit,
                metadata.case_pressure_limit_psi,
            )

            self.data_note.setText(
                f"Test stand: {metadata.test_stand or '—'}  •  "
                f"Operator: {metadata.test_operator or '—'}  •  "
                f"Location: {metadata.location or '—'}"
            )
        else:
            self.data_note.setText("Test metadata unavailable.")

        if thrust_results.isp_s is not None:
            isp_status = (
                f"Isp calculated from total impulse and propellant mass. "
                f"Status: {thrust_results.isp_status}."
            )
        else:
            isp_status = (
                f"Isp unavailable: {thrust_results.isp_status}"
            )

        if thrust_results.cstar_m_per_s is not None:
            cstar_status = (
                f"C* calculated as {thrust_results.cstar_m_per_s:.2f} m/s. "
                f"Status: {thrust_results.cstar_status}."
            )
        else:
            cstar_status = (
                f"C* unavailable: {thrust_results.cstar_status}"
            )

        self.cstar_status.setText(cstar_status)
        self.status_description.setText(
            f"{isp_status} {cstar_status}"
        )

    def clear_results(self):
        """Clear all displayed analysis values."""

        fields = (
            self.motor_designation,
            self.motor_type,
            self.manufacturer,
            self.builder,
            self.propellant_type,
            self.case_material,
            self.peak_thrust,
            self.peak_time,
            self.average_thrust,
            self.initial_average,
            self.rise_rate,
            self.decay_rate,
            self.threshold,
            self.burn_start,
            self.burn_end,
            self.burn_time,
            self.ignition_time,
            self.burnout_time,
            self.total_impulse,
            self.normalized_impulse,
            self.impulse_class,
            self.designation,
            self.isp,
            self.cstar,
            self.average_pressure,
            self.average_mass_flow,
            self.pressure_limit,
            self.throat_diameter,
            self.exit_diameter,
            self.nozzle_material,
            self.load_cell,
            self.pressure_sensor,
            self.sample_count,
            self.sample_rate,
            self.recorded_duration,
            self.minimum_thrust,
            self.maximum_thrust,
            self.initial_mass,
            self.propellant_mass,
            self.motor_diameter,
            self.motor_length,
            self.baseline_mean,
            self.baseline_std,
        )

        for field in fields:
            field.setText("—")

        self.data_note.setText("")
        self.cstar_status.setText("C* unavailable")
        self.status_description.setText(
            "Load a test to display engineering analysis results."
        )

    @staticmethod
    def _set_text(label, value):
        text = str(value).strip() if value is not None else ""
        label.setText(text if text else "—")

    @staticmethod
    def _set_count(label, value):
        if value is None:
            label.setText("—")
            return

        try:
            label.setText(f"{int(value):,}")
        except (TypeError, ValueError):
            label.setText("—")

    @staticmethod
    def _set_value(label, value):
        label.setText(AnalysisPanel._format_number(value))

    @staticmethod
    def _format_number(value):
        if value is None:
            return "—"

        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return "—"
