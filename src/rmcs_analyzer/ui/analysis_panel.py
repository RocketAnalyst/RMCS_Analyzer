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
    Detailed display of authoritative RMCS Analyzer results.

    This widget performs no engineering calculations. Values are supplied
    by the analysis layer and are formatted for display only.
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
        content_layout.setSpacing(16)

        # =========================================================
        # HEADER
        # =========================================================

        title = QLabel("DETAILED ANALYSIS")
        title.setObjectName("sectionTitle")
        content_layout.addWidget(title)

        subtitle = QLabel(
            "Authoritative results from the RMCS analysis engine."
        )
        subtitle.setObjectName("graphDescription")
        content_layout.addWidget(subtitle)

        # =========================================================
        # PERFORMANCE
        # =========================================================

        performance_group, performance_grid = self._create_group(
            "PERFORMANCE"
        )
        content_layout.addWidget(performance_group)

        self.peak_thrust = self._add_metric(
            performance_grid,
            0,
            "Peak Thrust",
            "—",
            "N",
        )

        self.peak_time = self._add_metric(
            performance_grid,
            1,
            "Peak Time",
            "—",
            "s",
        )

        self.threshold = self._add_metric(
            performance_grid,
            2,
            "5% Threshold",
            "—",
            "N",
        )

        self.burn_start = self._add_metric(
            performance_grid,
            3,
            "5% Burn Start",
            "—",
            "s",
        )

        self.burn_end = self._add_metric(
            performance_grid,
            4,
            "5% Burn End",
            "—",
            "s",
        )

        self.burn_time = self._add_metric(
            performance_grid,
            5,
            "Standardized Burn Time",
            "—",
            "s",
        )

        self.average_thrust = self._add_metric(
            performance_grid,
            6,
            "Average Thrust",
            "—",
            "N",
        )

        self.initial_average = self._add_metric(
            performance_grid,
            7,
            "Initial Thrust Average",
            "—",
            "N",
        )

        self.total_impulse = self._add_metric(
            performance_grid,
            8,
            "Total Impulse",
            "—",
            "N·s",
        )

        self.normalized_impulse = self._add_metric(
            performance_grid,
            9,
            "Normalized Impulse",
            "—",
            "N·s",
        )

        # =========================================================
        # CLASSIFICATION
        # =========================================================

        classification_group, classification_grid = self._create_group(
            "MOTOR CLASSIFICATION"
        )
        content_layout.addWidget(classification_group)

        self.impulse_class = self._add_metric(
            classification_grid,
            0,
            "Impulse Class",
            "—",
            "",
        )

        self.designation = self._add_metric(
            classification_grid,
            1,
            "Calculated Designation",
            "—",
            "",
        )

        self.class_range = self._add_metric(
            classification_grid,
            2,
            "Classification Range",
            "—",
            "N·s",
        )

        # =========================================================
        # DATA QUALITY / TEST DATA
        # =========================================================

        data_group, data_grid = self._create_group(
            "DATA & TEST CHARACTERISTICS"
        )
        content_layout.addWidget(data_group)

        self.sample_count = self._add_metric(
            data_grid,
            0,
            "Samples",
            "—",
            "",
        )

        self.sample_rate = self._add_metric(
            data_grid,
            1,
            "Sample Rate",
            "—",
            "SPS",
        )

        self.recorded_duration = self._add_metric(
            data_grid,
            2,
            "Recorded Duration",
            "—",
            "s",
        )

        self.minimum_thrust = self._add_metric(
            data_grid,
            3,
            "Minimum Thrust",
            "—",
            "N",
        )

        self.maximum_thrust = self._add_metric(
            data_grid,
            4,
            "Maximum Thrust",
            "—",
            "N",
        )

        self.baseline_mean = self._add_metric(
            data_grid,
            5,
            "Baseline Mean",
            "—",
            "N",
        )

        self.baseline_std = self._add_metric(
            data_grid,
            6,
            "Baseline Std. Dev.",
            "—",
            "N",
        )

        # =========================================================
        # EXTENSIONS
        # =========================================================

        extensions_group, extensions_layout = self._create_vertical_group(
            "PERFORMANCE EXTENSIONS"
        )
        content_layout.addWidget(extensions_group)

        self.cstar_status = QLabel(
            "C* unavailable"
        )
        self.cstar_status.setObjectName("metricValueSmall")
        self.cstar_status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        extensions_layout.addWidget(
            self.cstar_status
        )

        self.cstar_description = QLabel(
            "Chamber pressure data and nozzle throat area are "
            "required to calculate characteristic velocity (C*)."
        )
        self.cstar_description.setObjectName("graphDescription")
        self.cstar_description.setWordWrap(True)
        self.cstar_description.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        extensions_layout.addWidget(
            self.cstar_description
        )

        content_layout.addStretch()

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        self.clear_results()

    def _create_group(self, title):
        group = QFrame()
        group.setObjectName("analysisGroup")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)

        layout.addLayout(grid)

        return group, grid

    def _create_vertical_group(self, title):
        group = QFrame()
        group.setObjectName("analysisGroup")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        layout.addWidget(title_label)

        return group, layout

    def _add_metric(
        self,
        grid,
        row,
        name,
        value,
        unit,
    ):
        name_label = QLabel(name)
        name_label.setObjectName("metricName")

        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        value_label.setAlignment(
            Qt.AlignmentFlag.AlignRight |
            Qt.AlignmentFlag.AlignVCenter
        )
        value_label.setMinimumWidth(120)

        unit_label = QLabel(unit)
        unit_label.setObjectName("metricUnit")
        unit_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft |
            Qt.AlignmentFlag.AlignVCenter
        )
        unit_label.setMinimumWidth(45)

        grid.addWidget(name_label, row, 0)
        grid.addWidget(value_label, row, 1)
        grid.addWidget(unit_label, row, 2)

        return value_label

    def set_results(
        self,
        thrust_results,
        statistics,
        classification,
        recorded_duration_s=None,
    ):
        """
        Display authoritative AnalysisResults fields.

        No calculations are performed here.
        """

        self._set_value(
            self.peak_thrust,
            thrust_results.peak_thrust_N,
        )

        self._set_value(
            self.peak_time,
            thrust_results.peak_thrust_time_s,
        )

        self._set_value(
            self.threshold,
            getattr(
                thrust_results,
                "threshold_N",
                None,
            ),
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

        self._set_value(
            self.average_thrust,
            thrust_results.average_thrust_5pct_N,
        )

        self._set_value(
            self.initial_average,
            thrust_results.initial_thrust_average_N,
        )

        self._set_value(
            self.total_impulse,
            thrust_results.total_impulse_valid_curve_Ns,
        )

        self._set_value(
            self.normalized_impulse,
            thrust_results.normalized_impulse_Ns,
        )

        # ---------------------------------------------------------
        # Classification
        # ---------------------------------------------------------

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

        if (
            classification.lower_limit_Ns is not None
            and classification.upper_limit_Ns is not None
        ):
            self.class_range.setText(
                f"{classification.lower_limit_Ns:.2f}"
                f" – "
                f"{classification.upper_limit_Ns:.2f}"
            )
        else:
            self.class_range.setText("—")

        # ---------------------------------------------------------
        # Statistics
        # ---------------------------------------------------------

        self.sample_count.setText(
            f"{statistics.sample_count:,}"
            if statistics.sample_count is not None
            else "—"
        )

        self.sample_rate.setText(
            self._format_number(statistics.sample_rate_hz)
        )

        self.recorded_duration.setText(
            self._format_number(recorded_duration_s)
        )

        self.minimum_thrust.setText(
            self._format_number(statistics.minimum_thrust_N)
        )

        self.maximum_thrust.setText(
            self._format_number(statistics.maximum_thrust_N)
        )

        self.baseline_mean.setText(
            self._format_number(statistics.baseline_mean_N)
        )

        self.baseline_std.setText(
            self._format_number(statistics.baseline_std_N)
        )

    def clear_results(self):
        """Clear all displayed analysis values."""

        fields = (
            self.peak_thrust,
            self.peak_time,
            self.threshold,
            self.burn_start,
            self.burn_end,
            self.burn_time,
            self.average_thrust,
            self.initial_average,
            self.total_impulse,
            self.normalized_impulse,
            self.impulse_class,
            self.designation,
            self.class_range,
            self.sample_count,
            self.sample_rate,
            self.recorded_duration,
            self.minimum_thrust,
            self.maximum_thrust,
            self.baseline_mean,
            self.baseline_std,
        )

        for field in fields:
            field.setText("—")

        self.cstar_status.setText(
            "C* unavailable"
        )

    @staticmethod
    def _set_value(label, value):
        label.setText(
            AnalysisPanel._format_number(value)
        )

    @staticmethod
    def _format_number(value):
        if value is None:
            return "—"

        try:
            return f"{float(value):.2f}"
        except (TypeError, ValueError):
            return "—"
