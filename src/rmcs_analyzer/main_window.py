from pathlib import Path
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from .theme import APPLICATION_STYLE

from .data import (
    CSVReadError,
    RMCSCSVReader,
)

from .analysis import (
    EventDetector,
    MotorClassCalculator,
    StatisticsAnalyzer,
    ThrustAnalyzer,
)

from .project import (
    TestSession,
)

from .project.project_file import (
    ProjectFile,
    ProjectFileError,
)

from .ui.branding import Branding
from .ui.header import Header
from .ui.test_info_panel import TestInfoPanel
from .ui.test_files_panel import TestFilesPanel
from .ui.thrust_plot import ThrustPlot
from .ui.playback_controls import PlaybackControls
from .ui.results_panel import ResultsPanel


class MainWindow(QMainWindow):
    """
    Main application window.

    Coordinates the UI, test session, CSV importing,
    project loading/saving, analysis, and display.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "RMCS Analyzer"
        )

        self.resize(
            1500,
            950,
        )

        self.setMinimumSize(
            1200,
            750,
        )

        # =========================================================
        # DATA AND SESSION SERVICES
        # =========================================================

        self.reader = RMCSCSVReader()

        self.event_detector = EventDetector()
        self.thrust_analyzer = ThrustAnalyzer()
        self.statistics_analyzer = StatisticsAnalyzer()
        self.motor_class_calculator = MotorClassCalculator()

        self.session = TestSession()

        self.current_test = None
        self.current_analysis = None

        # =========================================================
        # PROJECT STATE
        # =========================================================

        self.project_filename = None
        self.project_modified = False

        self.build_ui()

        self.setStyleSheet(
            APPLICATION_STYLE
        )

        self.connect_signals()

        # Initial status
        self.header.set_status(
            "READY — No test loaded",
            modified=False,
        )

    # =============================================================
    # UI CONSTRUCTION
    # =============================================================

    def build_ui(self):
        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QVBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(
            0
        )

        # =========================================================
        # HEADER
        # =========================================================

        self.header = Header()

        main_layout.addWidget(
            self.header
        )

        # =========================================================
        # MAIN CONTENT
        # =========================================================

        content = QFrame()

        content.setObjectName(
            "content"
        )

        content_layout = QHBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        content_layout.setSpacing(
            14
        )

        # =========================================================
        # LEFT SIDEBAR
        # =========================================================

        left_container = QFrame()

        left_container.setObjectName(
            "panel"
        )

        left_layout = QVBoxLayout(
            left_container
        )

        left_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        left_layout.setSpacing(
            0
        )

        self.test_info = TestInfoPanel()

        self.test_files = TestFilesPanel()

        self.branding = Branding(
            mode="full"
        )

        left_layout.addWidget(
            self.test_info
        )

        left_layout.addWidget(
            self.test_files,
            1,
        )

        left_layout.addWidget(
            self.branding,
            0,
            Qt.AlignmentFlag.AlignBottom,
        )

        content_layout.addWidget(
            left_container
        )

        # =========================================================
        # CENTER PANEL
        # =========================================================

        center_panel = QFrame()

        center_panel.setObjectName(
            "panel"
        )

        center_layout = QVBoxLayout(
            center_panel
        )

        center_layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )

        center_layout.setSpacing(
            12
        )

        self.thrust_plot = ThrustPlot()

        self.playback = PlaybackControls()

        center_layout.addWidget(
            self.thrust_plot,
            1,
        )

        center_layout.addWidget(
            self.playback
        )

        content_layout.addWidget(
            center_panel,
            1,
        )

        # =========================================================
        # RIGHT SIDEBAR
        # =========================================================

        self.results = ResultsPanel()

        self.results.status.hide()

        content_layout.addWidget(
            self.results
        )

        main_layout.addWidget(
            content,
            1,
        )

        # =========================================================
        # FOOTER
        # =========================================================

        footer = QFrame()

        footer.setObjectName(
            "footer"
        )

        footer.setFixedHeight(
            30
        )

        footer_layout = QHBoxLayout(
            footer
        )

        footer_layout.setContentsMargins(
            18,
            0,
            18,
            0,
        )

        footer_text = QLabel(
            "RMCS Analyzer  •  "
            "Rocket Motor Characterization System"
        )

        footer_text.setObjectName(
            "footerLabel"
        )

        version = QLabel(
            "v0.1.0"
        )

        version.setObjectName(
            "footerLabel"
        )

        footer_layout.addWidget(
            footer_text
        )

        footer_layout.addStretch()

        footer_layout.addWidget(
            version
        )

        main_layout.addWidget(
            footer
        )

    # =============================================================
    # SIGNALS
    # =============================================================

    def connect_signals(self):
        """Connect GUI signals to application actions."""

        self.header.import_rmcs_requested.connect(
            self.import_rmcs_test
        )

        self.header.import_project_requested.connect(
            self.open_project_dialog
        )

        self.header.import_other_csv_requested.connect(
            self.import_other_csv
        )

        self.header.save_button.clicked.connect(
            self.save_project
        )

        self.test_files.test_selected.connect(
            self.select_test
        )

        self.test_info.metadata_changed.connect(
            self.update_active_test_metadata
        )

    # =============================================================
    # SESSION INDEX
    # =============================================================

    def get_test_index(
        self,
        target_test,
    ):
        """
        Return the session index of a TestModel using object identity.

        TestModel contains NumPy arrays, so normal equality comparison
        must not be used to locate tests in the session.
        """

        for index, test in enumerate(
            self.session.tests
        ):

            if test is target_test:
                return index

        return None

    # =============================================================
    # PROJECT STATE
    # =============================================================

    def has_unsaved_changes(self):
        """Return True when the current project has unsaved changes."""

        return (
            self.project_modified
            or self.session.has_modified_tests
        )

    def mark_project_modified(self):
        """Mark the current project as modified."""

        self.project_modified = True

        if self.session.active_test is not None:

            self.update_status(
                self.session.active_test
            )

    # =============================================================
    # IMPORT RMCS TEST DATA
    # =============================================================

    def import_rmcs_test(self):
        """
        Import one RMCS-compatible CSV test file.
        """

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import RMCS Test Data",
            "",
            (
                "RMCS CSV Test Files (*.csv *.CSV);;"
                "All Files (*.*)"
            ),
        )

        if not filename:
            return

        self.open_test(
            filename
        )

    # =============================================================
    # IMPORT OTHER CSV
    # =============================================================

    def import_other_csv(self):
        """
        Placeholder for future non-RMCS CSV import support.
        """

        QMessageBox.information(
            self,
            "Non-RMCS CSV Import",
            (
                "Support for importing and mapping "
                "non-RMCS test data is planned for "
                "a future version."
            ),
        )

    # =============================================================
    # OPEN PROJECT DIALOG
    # =============================================================

    def open_project_dialog(self):
        """
        Open the file dialog for RMCS Analyzer projects.
        """

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open RMCS Analyzer Project",
            "",
            (
                "RMCS Analyzer Projects (*.rmcs);;"
                "All Files (*.*)"
            ),
        )

        if not filename:
            return

        self.open_project(
            filename
        )

    # =============================================================
    # OPEN CSV TEST
    # =============================================================

    def open_test(
        self,
        filename,
    ):
        """
        Load, analyze, and add an RMCS CSV test to the session.
        """

        # ---------------------------------------------------------
        # Check whether this test is already loaded
        # ---------------------------------------------------------

        existing_test = (
            self.session.get_test_by_source(
                filename
            )
        )

        if existing_test is not None:

            index = self.get_test_index(
                existing_test
            )

            if index is not None:

                self.test_files.set_current_test(
                    index
                )

                self.select_test(
                    index
                )

            return

        try:

            # -----------------------------------------------------
            # Read CSV
            # -----------------------------------------------------

            test_data = self.reader.read(
                filename
            )

            # -----------------------------------------------------
            # Create TestModel
            # -----------------------------------------------------

            from .project.test_model import TestModel

            test = TestModel(
                data=test_data
            )

            # -----------------------------------------------------
            # Analyze test
            # -----------------------------------------------------

            events = self.event_detector.detect(
                test_data
            )

            thrust_results = (
                self.thrust_analyzer.analyze(
                    test_data,
                    events,
                )
            )

            statistics = (
                self.statistics_analyzer.analyze(
                    test_data
                )
            )

            if (
                thrust_results.total_impulse_Ns
                is not None
            ):

                classification = (
                    self.motor_class_calculator.classify(
                        thrust_results.total_impulse_Ns
                    )
                )

            else:

                classification = (
                    self.motor_class_calculator.classify(
                        -1
                    )
                )

            # -----------------------------------------------------
            # Store analysis
            # -----------------------------------------------------

            from .analysis.results import AnalysisResults

            test.analysis_results = (
                AnalysisResults(
                    events=events,
                    thrust=thrust_results,
                    statistics=statistics,
                    classification=classification,
                )
            )

            # -----------------------------------------------------
            # Add to session
            # -----------------------------------------------------

            added = self.session.add_test(
                test
            )

            if not added:
                return

            # -----------------------------------------------------
            # Adding a test to an existing project modifies it
            # -----------------------------------------------------

            if self.project_filename is not None:

                self.project_modified = True

            # -----------------------------------------------------
            # Add to test list
            # -----------------------------------------------------

            test_index = self.get_test_index(
                test
            )

            if test_index is None:
                return

            self.test_files.add_file(
                test.display_name,
                test_index,
            )

            # -----------------------------------------------------
            # Display test
            # -----------------------------------------------------

            self.select_test(
                test_index
            )

        except CSVReadError as error:

            QMessageBox.critical(
                self,
                "Unable to Import Test",
                str(error),
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Unexpected Error",
                (
                    "An unexpected error occurred "
                    "while importing or analyzing "
                    "the test:\n\n"
                    f"{error}"
                ),
            )

    # =============================================================
    # OPEN PROJECT
    # =============================================================

    def open_project(
        self,
        filename,
    ):
        """
        Load an RMCS Analyzer project from disk.
        """

        # ---------------------------------------------------------
        # Protect unsaved changes
        # ---------------------------------------------------------

        if self.has_unsaved_changes():

            project_name = Path(
                filename
            ).name

            response = QMessageBox.question(
                self,
                "Unsaved Changes",
                (
                    "The current project contains "
                    "unsaved changes.\n\n"
                    f"Open '{project_name}' anyway?"
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                ),
                QMessageBox.StandardButton.No,
            )

            if response != (
                QMessageBox.StandardButton.Yes
            ):

                return

        # ---------------------------------------------------------
        # Load project
        # ---------------------------------------------------------

        try:

            loaded_session = (
                ProjectFile.load(
                    filename
                )
            )

        except ProjectFileError as error:

            QMessageBox.critical(
                self,
                "Unable to Open Project",
                str(error),
            )

            return

        except Exception as error:

            QMessageBox.critical(
                self,
                "Unexpected Error",
                (
                    "An unexpected error occurred "
                    "while opening the project:\n\n"
                    f"{error}"
                ),
            )

            return

        # ---------------------------------------------------------
        # Replace session
        # ---------------------------------------------------------

        self.session = loaded_session

        self.project_filename = filename

        self.project_modified = False

        self.current_test = None

        self.current_analysis = None

        # ---------------------------------------------------------
        # Rebuild test list
        # ---------------------------------------------------------

        self.test_files.clear()

        for index, test in enumerate(
            self.session.tests
        ):

            self.test_files.add_file(
                test.display_name,
                index,
            )

        # ---------------------------------------------------------
        # Restore active test
        # ---------------------------------------------------------

        active_test = (
            self.session.active_test
        )

        if active_test is not None:

            active_index = (
                self.get_test_index(
                    active_test
                )
            )

            if active_index is not None:

                self.test_files.set_current_test(
                    active_index
                )

                self.select_test(
                    active_index
                )

        else:

            self.test_info.clear()

            self.thrust_plot.clear()

        # ---------------------------------------------------------
        # Window title
        # ---------------------------------------------------------

        project_name = Path(
            filename
        ).name

        self.setWindowTitle(
            f"{project_name} — RMCS Analyzer"
        )

        # ---------------------------------------------------------
        # Status
        # ---------------------------------------------------------

        if active_test is not None:

            self.update_status(
                active_test
            )

        else:

            self.header.set_status(
                f"READY — {project_name}",
                modified=False,
            )

    # =============================================================
    # SAVE PROJECT
    # =============================================================

    def save_project(self):
        """
        Save the current TestSession to an RMCS project file.
        """

        if self.session.test_count == 0:

            QMessageBox.information(
                self,
                "Nothing to Save",
                "There are no test files loaded.",
            )

            return

        # ---------------------------------------------------------
        # First save
        # ---------------------------------------------------------

        if self.project_filename is None:

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save RMCS Analyzer Project",
                "",
                (
                    "RMCS Analyzer Project (*.rmcs);;"
                    "All Files (*.*)"
                ),
            )

            if not filename:
                return

            path = Path(
                filename
            )

            if path.suffix.lower() != ".rmcs":

                path = path.with_suffix(
                    ".rmcs"
                )

            filename = str(
                path
            )

        else:

            filename = self.project_filename

        # ---------------------------------------------------------
        # Save
        # ---------------------------------------------------------

        try:

            ProjectFile.save(
                self.session,
                filename,
            )

        except ProjectFileError as error:

            QMessageBox.critical(
                self,
                "Unable to Save Project",
                str(error),
            )

            return

        except Exception as error:

            QMessageBox.critical(
                self,
                "Unexpected Error",
                (
                    "An unexpected error occurred "
                    "while saving the project:\n\n"
                    f"{error}"
                ),
            )

            return

        # ---------------------------------------------------------
        # Save successful
        # ---------------------------------------------------------

        self.project_filename = filename

        self.project_modified = False

        for test in self.session.tests:
            test.mark_saved()

        # ---------------------------------------------------------
        # Window title
        # ---------------------------------------------------------

        project_name = Path(
            filename
        ).name

        self.setWindowTitle(
            f"{project_name} — RMCS Analyzer"
        )

        # ---------------------------------------------------------
        # Status
        # ---------------------------------------------------------

        if self.session.active_test is not None:

            self.update_status(
                self.session.active_test

            )

        else:

            self.header.set_status(
                f"READY — {project_name}",
                modified=False,
            )

    # =============================================================
    # SELECT TEST
    # =============================================================

    def select_test(
        self,
        test_index,
    ):
        """
        Select a test and display it.
        """

        tests = self.session.tests

        if (
            test_index < 0
            or test_index >= len(tests)
        ):
            return

        test = tests[
            test_index
        ]

        if not self.session.select_test(
            test
        ):
            return

        self.current_test = test

        self.current_analysis = (
            test.analysis_results
        )

        self.display_active_test()

    # =============================================================
    # DISPLAY ACTIVE TEST
    # =============================================================

    def display_active_test(self):
        """Update all UI components for the active test."""

        test = self.session.active_test

        if test is None:
            return

        # ---------------------------------------------------------
        # Test information
        # ---------------------------------------------------------

        self.test_info.set_test_model(
            test
        )

        # ---------------------------------------------------------
        # Plot
        # ---------------------------------------------------------

        self.thrust_plot.set_data(
            test.data.time_s,
            test.data.thrust_N,
        )

        # ---------------------------------------------------------
        # Results
        # ---------------------------------------------------------

        if test.analysis_results is not None:

            analysis = (
                test.analysis_results
            )

            self.update_results(
                analysis.events,
                analysis.thrust,
                analysis.statistics,
                analysis.classification,
            )

        # ---------------------------------------------------------
        # Status
        # ---------------------------------------------------------

        self.update_status(
            test
        )

    # =============================================================
    # UPDATE ACTIVE TEST METADATA
    # =============================================================

    def update_active_test_metadata(self):
        """
        Store edited metadata in the active TestModel.
        """

        test = self.session.active_test

        if test is None:
            return

        test.test_number = (
            self.test_info.test_number.text().strip()
        )

        test.motor_designation = (
            self.test_info.motor.text().strip()
        )

        test.test_date = (
            self.test_info.date.text().strip()
        )

        test.motor_diameter_in = (
            self.parse_optional_float(
                self.test_info.diameter.text()
            )
        )

        test.motor_length_in = (
            self.parse_optional_float(
                self.test_info.length.text()
            )
        )

        test.initial_mass_g = (
            self.parse_optional_float(
                self.test_info.initial_mass.text()
            )
        )

        test.propellant_mass_g = (
            self.parse_optional_float(
                self.test_info.propellant_mass.text()
            )
        )

        test.mark_modified()

        self.project_modified = True

        self.update_status(
            test
        )

    # =============================================================
    # PARSE OPTIONAL FLOAT
    # =============================================================

    def parse_optional_float(
        self,
        value,
    ):
        """Convert an optional numeric field to float."""

        value = value.strip()

        if not value:
            return None

        try:

            return float(
                value
            )

        except ValueError:

            return None

    # =============================================================
    # UPDATE RESULTS
    # =============================================================

    def update_results(
        self,
        events,
        thrust_results,
        statistics,
        classification,
    ):
        """Update the results panel."""

        if thrust_results.peak_thrust_N is not None:

            self.results.peak_thrust.setText(
                f"{thrust_results.peak_thrust_N:.2f}"
            )

        else:

            self.results.peak_thrust.setText(
                "—"
            )

        if thrust_results.average_thrust_N is not None:

            self.results.average_thrust.setText(
                f"{thrust_results.average_thrust_N:.2f}"
            )

        else:

            self.results.average_thrust.setText(
                "—"
            )

        if thrust_results.total_impulse_Ns is not None:

            self.results.total_impulse.setText(
                f"{thrust_results.total_impulse_Ns:.2f}"
            )

        else:

            self.results.total_impulse.setText(
                "—"
            )

        if thrust_results.burn_time_s is not None:

            self.results.burn_time.setText(
                f"{thrust_results.burn_time_s:.2f}"
            )

        else:

            self.results.burn_time.setText(
                "—"
            )

        if thrust_results.time_to_peak_s is not None:

            self.results.time_to_peak.setText(
                f"{thrust_results.time_to_peak_s:.2f}"
            )

        else:

            self.results.time_to_peak.setText(
                "—"
            )

        if classification.motor_class is not None:

            self.results.motor_class.setText(
                classification.motor_class
            )

        else:

            self.results.motor_class.setText(
                "—"
            )

        if (
            classification.motor_class is not None
            and thrust_results.average_thrust_N
            is not None
        ):

            calculated_designation = (
                f"{classification.motor_class}"
                f"{round(thrust_results.average_thrust_N)}"
            )

            self.results.calculated_designation.setText(
                calculated_designation
            )

        else:

            self.results.calculated_designation.setText(
                "—"
            )

        if events.ignition_time_s is not None:

            self.results.ignition.setText(
                f"{events.ignition_time_s:.2f} s"
            )

        else:

            self.results.ignition.setText(
                "—"
            )

        if events.peak_time_s is not None:

            self.results.peak_event.setText(
                f"{events.peak_time_s:.2f} s"
            )

        else:

            self.results.peak_event.setText(
                "—"
            )

        if events.burnout_time_s is not None:

            self.results.burnout.setText(
                f"{events.burnout_time_s:.2f} s"
            )

        else:

            self.results.burnout.setText(
                "—"
            )

    # =============================================================
    # UPDATE STATUS
    # =============================================================

    def update_status(
        self,
        test,
    ):
        """
        Update the header status indicator.

        The project is considered modified when either the active
        test or another loaded test contains unsaved changes.
        """

        if self.has_unsaved_changes():

            self.header.set_status(
                f"MODIFIED — {test.filename}",
                modified=True,
            )

        else:

            self.header.set_status(
                f"READY — {test.filename}",
                modified=False,
            )


def main():
    """Application entry point."""

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "RMCS Analyzer"
    )

    app.setApplicationDisplayName(
        "RMCS Analyzer"
    )

    window = MainWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()