from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QMessageBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
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
    overlay_visibility_preview_changed = Signal(object)
    video_display_mode_preview_changed = Signal(str)
    theme_preview_changed = Signal(str)
    """Application settings dialog, beginning with per-test video overlay settings."""

    def __init__(self, video_configuration=None, current_theme="dark", parent=None):
        super().__init__(parent)
        self.setWindowTitle("RMCS Analyzer Settings")
        self.setMinimumSize(620, 560)
        self.resize(700, 620)

        configuration = video_configuration or {}
        self._video_tab_index = 1
        self._initial_theme = str(current_theme or "dark").lower()
        self._theme_changed = False

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

        intro = QLabel("Application-wide preferences")
        intro.setWordWrap(True)
        intro.setObjectName("settingsIntro")
        general.addWidget(intro)

        theme_group = QGroupBox("Appearance")
        theme_layout = QFormLayout(theme_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")
        theme_index = self.theme_combo.findData(self._initial_theme)
        self.theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
        self.theme_combo.currentIndexChanged.connect(self._emit_theme_preview)

        theme_layout.addRow("Theme:", self.theme_combo)
        general.addWidget(theme_group)

        # ---------------------------------------------------------
        # Data Templates
        # ---------------------------------------------------------
        template_group = QGroupBox("Data Templates")
        template_layout = QVBoxLayout(template_group)

        template_note = QLabel(
            "Download blank CSV templates showing the formats RMCS Analyzer "
            "expects for test data and simulation imports. Simulation templates "
            "are RMCS import-format examples; BurnSim and OpenMotor normally "
            "produce these files directly."
        )
        template_note.setWordWrap(True)
        template_note.setObjectName("settingsIntro")
        template_layout.addWidget(template_note)

        test_template_row = QHBoxLayout()
        test_template_button = QPushButton("Download Test Data Template")
        test_template_button.setToolTip(
            "Save a blank RMCS test-data CSV template."
        )
        test_template_button.clicked.connect(
            lambda: self._save_template("test")
        )
        test_template_row.addWidget(test_template_button)
        test_template_row.addStretch(1)
        template_layout.addLayout(test_template_row)

        burnsim_template_row = QHBoxLayout()
        burnsim_template_button = QPushButton("Download BurnSim Simulation Template")
        burnsim_template_button.setToolTip(
            "Save a blank CSV showing the BurnSim simulation import columns."
        )
        burnsim_template_button.clicked.connect(
            lambda: self._save_template("burnsim")
        )
        burnsim_template_row.addWidget(burnsim_template_button)
        burnsim_template_row.addStretch(1)
        template_layout.addLayout(burnsim_template_row)

        openmotor_template_row = QHBoxLayout()
        openmotor_template_button = QPushButton("Download OpenMotor Simulation Template")
        openmotor_template_button.setToolTip(
            "Save a blank CSV showing the OpenMotor simulation import columns."
        )
        openmotor_template_button.clicked.connect(
            lambda: self._save_template("openmotor")
        )
        openmotor_template_row.addWidget(openmotor_template_button)
        openmotor_template_row.addStretch(1)
        template_layout.addLayout(openmotor_template_row)

        general.addWidget(template_group)

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

        overlay_defaults = QGroupBox("Overlay Visibility")
        overlay_defaults_layout = QVBoxLayout(overlay_defaults)

        overlay_defaults_note = QLabel(
            "Choose which overlay layers are enabled for the active test. "
            "Changes preview immediately; click OK to keep them or Cancel to restore the previous settings."
        )
        overlay_defaults_note.setWordWrap(True)
        overlay_defaults_note.setObjectName("settingsIntro")
        overlay_defaults_layout.addWidget(overlay_defaults_note)

        visibility = configuration.get("overlay_visibility", {})

        self.show_thrust_check = QCheckBox("Thrust")
        self.show_pressure_check = QCheckBox("Pressure")
        self.show_simulation_check = QCheckBox("Simulation")
        self.show_results_check = QCheckBox("Results")
        self.show_events_check = QCheckBox("Events")

        self.show_thrust_check.setChecked(
            bool(visibility.get("thrust", configuration.get("show_curve", True)))
        )
        self.show_pressure_check.setChecked(
            bool(visibility.get("pressure", configuration.get("show_pressure", False)))
        )
        self.show_simulation_check.setChecked(
            bool(visibility.get("simulation", configuration.get("show_simulation", False)))
        )
        self.show_results_check.setChecked(
            bool(visibility.get("results", configuration.get("show_results", True)))
        )
        self.show_events_check.setChecked(
            bool(visibility.get("events", configuration.get("show_events", True)))
        )

        for checkbox in (
            self.show_thrust_check,
            self.show_pressure_check,
            self.show_simulation_check,
            self.show_results_check,
            self.show_events_check,
        ):
            overlay_defaults_layout.addWidget(checkbox)

        video_page.addWidget(overlay_defaults)

        display = QGroupBox("Video Display")
        display_layout = QFormLayout(display)
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItem("Fit — show the entire video", "fit")
        self.display_mode_combo.addItem("Fill — use the full preview area", "fill")
        current_display_mode = str(configuration.get("display_mode", "fit")).lower()
        index = self.display_mode_combo.findData(current_display_mode)
        self.display_mode_combo.setCurrentIndex(index if index >= 0 else 0)
        self.display_mode_combo.setToolTip(
            "Fit preserves the full frame without cropping. Fill enlarges the video "
            "to use the entire preview area and may crop the edges."
        )
        display_layout.addRow("Display mode:", self.display_mode_combo)
        video_page.addWidget(display)

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

        # The result list should display all available fields without its own
        # nested scrollbar. The surrounding Video Overlay tab may scroll instead.
        self.result_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.result_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.result_list.setMinimumHeight(300)
        self.result_list.setSizeAdjustPolicy(QListWidget.SizeAdjustPolicy.AdjustToContents)
        results_layout.addWidget(self.result_list)
        video_page.addWidget(results)

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

        self.display_mode_combo.currentIndexChanged.connect(
            self._emit_display_mode_preview
        )

        for checkbox in (
            self.show_thrust_check,
            self.show_pressure_check,
            self.show_simulation_check,
            self.show_results_check,
            self.show_events_check,
        ):
            checkbox.toggled.connect(self._emit_visibility_preview)

        video_page.addStretch(1)

        video_page_widget = QWidgetLikeLayout(video_page)
        video_scroll = QScrollArea()
        video_scroll.setWidgetResizable(True)
        video_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        video_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        video_scroll.setWidget(video_page_widget)
        tabs.addTab(video_scroll, "Video Overlay")

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

    @staticmethod
    def _template_contents(template_type):
        if template_type == "test":
            return """Format Version,1.0,,,,,
Test Number,,,,,,
Test Date,,,,,,
Test Stand,,,,,,
Test Operator,,,,,,
Location,,,,,,
Notes,,,,,,
Motor Designation,,,,,,
Motor Type,,,,,,
Manufacturer,,,,,,
Builder,,,,,,
Case Material,,,,,,
Motor Diameter (mm),,,,,,
Motor Length (mm),,,,,,
Initial Mass (g),,,,,,
Propellant Mass (g),,,,,,
Propellant Type,,,,,,
Nozzle Throat Diameter (in),,,,,,
Nozzle Exit Diameter (in),,,,,,
Nozzle Material,,,,,,
Load Cell,,,,,,
Load Cell Calibration,,,,,,
Pressure Sensor,,,,,,
Pressure Sensor Calibration,,,,,,
Sample Rate (Hz),,,,,,
case pressure limit (psi),,,,,,
,,,,,,
,,,,,,
,,,,,,
Sample,Time(s),Time Cal (s),Raw Thrust (N),Prop Loss (kg),Thrust (N),Pressure (psi)
"""
        if template_type == "burnsim":
            return """Time (s),Pressure (psi),Thrust (N)\n"""
        if template_type == "openmotor":
            return """Time (s),Chamber Pressure (psi),Thrust (N),Kn (-),Mass Flow (kg/s),Mass Flux (kg/m^2/s),Regression (m),Web (m)\n"""
        raise ValueError(f"Unknown template type: {template_type}")

    def _save_template(self, template_type):
        names = {
            "test": ("RMCS Test Data Template.csv", "RMCS test-data CSV"),
            "burnsim": ("RMCS BurnSim Simulation Template.csv", "BurnSim simulation CSV"),
            "openmotor": ("RMCS OpenMotor Simulation Template.csv", "OpenMotor simulation CSV"),
        }
        default_name, description = names[template_type]
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {description} Template",
            default_name,
            "CSV Files (*.csv);;All Files (*)",
        )
        if not path:
            return
        try:
            Path(path).write_text(
                self._template_contents(template_type),
                encoding="utf-8",
                newline="",
            )
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Template Download Failed",
                f"Could not save the template file.\\n\\n{exc}",
            )

    def _emit_theme_preview(self, _index=0):
        theme = str(self.theme_combo.currentData() or "dark")
        self._theme_changed = theme != self._initial_theme
        self.theme_preview_changed.emit(theme)

    def _visibility_configuration(self):
        return {
            "thrust": self.show_thrust_check.isChecked(),
            "pressure": self.show_pressure_check.isChecked(),
            "simulation": self.show_simulation_check.isChecked(),
            "results": self.show_results_check.isChecked(),
            "events": self.show_events_check.isChecked(),
        }

    def _emit_visibility_preview(self, _checked=False):
        self.overlay_visibility_preview_changed.emit(
            self._visibility_configuration()
        )

    def _emit_display_mode_preview(self, _index=0):
        self.video_display_mode_preview_changed.emit(
            str(self.display_mode_combo.currentData() or "fit")
        )

    def select_video_overlay_tab(self):
        # The Video Overlay page is intentionally the second settings tab.
        self.findChild(QTabWidget).setCurrentIndex(self._video_tab_index)

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
            "overlay_visibility": {
                "thrust": self.show_thrust_check.isChecked(),
                "pressure": self.show_pressure_check.isChecked(),
                "simulation": self.show_simulation_check.isChecked(),
                "results": self.show_results_check.isChecked(),
                "events": self.show_events_check.isChecked(),
            },
            # Compatibility keys for the existing video-state model.
            "show_curve": self.show_thrust_check.isChecked(),
            "show_pressure": self.show_pressure_check.isChecked(),
            "show_simulation": self.show_simulation_check.isChecked(),
            "show_results": self.show_results_check.isChecked(),
            "show_events": self.show_events_check.isChecked(),
            "display_mode": str(self.display_mode_combo.currentData() or "fit"),
            "theme": str(self.theme_combo.currentData() or "dark"),
        }


class QWidgetLikeLayout(QWidget):
    """
    Small internal helper used as a QWidget container for a prepared layout.
    """

    def __init__(self, layout):
        super().__init__()
        self.setLayout(layout)
