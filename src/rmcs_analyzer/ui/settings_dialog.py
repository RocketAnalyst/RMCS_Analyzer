from PySide6.QtCore import Qt, Signal
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
    overlay_visibility_preview_changed = Signal(object)
    video_display_mode_preview_changed = Signal(str)
    """Application settings dialog, beginning with per-test video overlay settings."""

    def __init__(self, video_configuration=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RMCS Analyzer Settings")
        self.setMinimumSize(620, 560)
        self.resize(700, 620)

        configuration = video_configuration or {}
        self._video_tab_index = 1

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
        }


class QWidgetLikeLayout(QWidget):
    """
    Small internal helper used as a QWidget container for a prepared layout.
    """

    def __init__(self, layout):
        super().__init__()
        self.setLayout(layout)
