from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


RESULT_OPTIONS = [
    ("current_thrust", "Current Thrust"),
    ("designation", "Calculated Designation"),
    ("motor_class", "Motor Class"),
    ("peak_thrust", "Peak Thrust"),
    ("average_thrust", "Average Thrust"),
    ("total_impulse", "Total Impulse"),
    ("burn_time", "Burn Time"),
    ("time_to_peak", "Time to Peak"),
    ("isp", "Isp"),
    ("cstar", "C*"),
    ("avg_pressure", "Average Chamber Pressure"),
    ("avg_mass_flow", "Average Mass Flow"),
]


class SettingsDialog(QDialog):
    """Application settings dialog, beginning with per-test video overlay settings."""

    def __init__(self, video_configuration=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RMCS Analyzer Settings")
        self.setMinimumSize(620, 560)
        self.resize(700, 620)

        configuration = video_configuration or {}

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        tabs = QTabWidget()
        tabs.setObjectName("settingsTabs")
        root.addWidget(tabs, 1)

        # ---------------------------------------------------------
        # General
        # ---------------------------------------------------------
        general = QVBoxLayout()
        general.setContentsMargins(16, 16, 16, 16)

        intro = QLabel(
            "Application-wide preferences will live here as RMCS Analyzer grows."
        )
        intro.setWordWrap(True)
        intro.setObjectName("settingsIntro")
        general.addWidget(intro)

        units_group = QGroupBox("Units")
        units_layout = QFormLayout(units_group)

        thrust_units = QComboBox()
        thrust_units.addItems(["Newtons (N)"])
        thrust_units.setEnabled(False)

        pressure_units = QComboBox()
        pressure_units.addItems(["psi"])
        pressure_units.setEnabled(False)

        mass_units = QComboBox()
        mass_units.addItems(["grams / kilograms"])
        mass_units.setEnabled(False)

        units_layout.addRow("Thrust:", thrust_units)
        units_layout.addRow("Pressure:", pressure_units)
        units_layout.addRow("Mass:", mass_units)

        general.addWidget(units_group)

        theme_group = QGroupBox("Appearance")
        theme_layout = QFormLayout(theme_group)

        theme_combo = QComboBox()
        theme_combo.addItems(["Dark"])
        theme_combo.setEnabled(False)
        theme_combo.setToolTip("Light mode will be added in a future settings pass.")

        theme_layout.addRow("Theme:", theme_combo)
        general.addWidget(theme_group)

        general.addStretch(1)

        general_page = QWidgetLikeLayout(general)
        tabs.addTab(general_page, "General")

        # ---------------------------------------------------------
        # Video Overlay
        # ---------------------------------------------------------
        video_page = QVBoxLayout()
        video_page.setContentsMargins(16, 16, 16, 16)
        video_page.setSpacing(12)

        note = QLabel(
            "These settings apply to the active test's video overlay and are "
            "saved with the .rmcs project. They do not change the underlying analysis."
        )
        note.setWordWrap(True)
        note.setObjectName("settingsIntro")
        video_page.addWidget(note)

        titles = QGroupBox("Overlay Titles")
        titles_layout = QFormLayout(titles)

        self.curve_title = QLineEdit(
            configuration.get("curve_title", "Measured Thrust")
        )
        self.results_title = QLineEdit(
            configuration.get("results_title", "Test Results")
        )

        titles_layout.addRow("Curve title:", self.curve_title)
        titles_layout.addRow("Results title:", self.results_title)
        video_page.addWidget(titles)

        chart = QGroupBox("Thrust Curve")
        chart_layout = QVBoxLayout(chart)

        self.grid_check = QCheckBox("Show chart grid")
        self.grid_check.setChecked(
            bool(configuration.get("curve_show_grid", True))
        )

        self.axes_check = QCheckBox("Show axes and scale")
        self.axes_check.setChecked(
            bool(configuration.get("curve_show_axes", True))
        )

        self.background_check = QCheckBox("Show chart background")
        self.background_check.setChecked(
            bool(configuration.get("curve_show_background", True))
        )
        self.background_check.setToolTip(
            "Show or hide the subtle translucent background behind the thrust chart."
        )

        chart_layout.addWidget(self.grid_check)
        chart_layout.addWidget(self.axes_check)
        chart_layout.addWidget(self.background_check)
        video_page.addWidget(chart)

        results = QGroupBox("Results Overlay — Select Fields")
        results_layout = QVBoxLayout(results)

        self.result_list = QListWidget()
        self.result_list.setSelectionMode(
            QListWidget.SelectionMode.NoSelection
        )

        selected_fields = set(
            configuration.get(
                "result_fields",
                [
                    "designation",
                    "peak_thrust",
                    "average_thrust",
                    "total_impulse",
                    "burn_time",
                ],
            )
        )

        for key, label in RESULT_OPTIONS:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            item.setCheckState(
                Qt.CheckState.Checked
                if key in selected_fields
                else Qt.CheckState.Unchecked
            )
            self.result_list.addItem(item)

        results_layout.addWidget(self.result_list)
        video_page.addWidget(results, 1)

        events = QGroupBox("Events — Visibility")
        events_layout = QHBoxLayout(events)

        event_visibility = configuration.get(
            "event_visibility",
            {
                "ignition": True,
                "peak_thrust": True,
                "burnout": True,
            },
        )

        self.ignition_check = QCheckBox("Ignition")
        self.peak_check = QCheckBox("Peak Thrust")
        self.burnout_check = QCheckBox("Burnout")

        self.ignition_check.setChecked(
            bool(event_visibility.get("ignition", True))
        )
        self.peak_check.setChecked(
            bool(event_visibility.get("peak_thrust", True))
        )
        self.burnout_check.setChecked(
            bool(event_visibility.get("burnout", True))
        )

        events_layout.addWidget(self.ignition_check)
        events_layout.addWidget(self.peak_check)
        events_layout.addWidget(self.burnout_check)
        events_layout.addStretch(1)

        video_page.addWidget(events)

        video_page.addStretch(1)

        video_page_widget = QWidgetLikeLayout(video_page)
        tabs.addTab(video_page_widget, "Video Overlay")

        # ---------------------------------------------------------
        # Buttons
        # ---------------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Ok
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def configuration(self):
        fields = []
        for index in range(self.result_list.count()):
            item = self.result_list.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                fields.append(
                    item.data(Qt.ItemDataRole.UserRole)
                )

        return {
            "curve_title": self.curve_title.text().strip() or "Measured Thrust",
            "results_title": self.results_title.text().strip() or "Test Results",
            "result_fields": fields,
            "event_visibility": {
                "ignition": self.ignition_check.isChecked(),
                "peak_thrust": self.peak_check.isChecked(),
                "burnout": self.burnout_check.isChecked(),
            },
            "curve_show_grid": self.grid_check.isChecked(),
            "curve_show_axes": self.axes_check.isChecked(),
            "curve_show_background": self.background_check.isChecked(),
        }


class QWidgetLikeLayout(QWidget):
    """
    Small internal helper used as a QWidget container for a prepared layout.
    """

    def __init__(self, layout):
        super().__init__()
        self.setLayout(layout)
