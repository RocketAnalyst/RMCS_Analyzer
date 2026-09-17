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
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .theme import APPLICATION_STYLE

from .data import (
    CSVReadError,
    RMCSCSVReader,
)

from .analysis import (
    AnalysisEngine,
)

from .processing import (
    ProcessingPipeline,
    ProcessingSettings,
)

from .processing.event_model import (
    DetectedEvent,
    EventSet,
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
    Main RMCS Analyzer application window.

    The main window coordinates:
        - application UI
        - test sessions
        - CSV importing
        - project loading/saving
        - processing
        - analysis
        - result display

    The UI is organized around the primary analysis workspaces:
        - Thrust Curve
        - Data Table
        - Analysis
        - Compare
        - Simulation Overlay
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

        self.processing_pipeline = ProcessingPipeline()

        self.analysis_engine = AnalysisEngine()

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
        # MAIN APPLICATION AREA
        # =========================================================

        content = QFrame()

        content.setObjectName(
            "content"
        )

        content_layout = QHBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        content_layout.setSpacing(
            10
        )

        # =========================================================
        # LEFT SIDEBAR
        # =========================================================

        left_container = QFrame()

        left_container.setObjectName(
            "panel"
        )

        left_container.setMinimumWidth(
            280
        )

        left_container.setMaximumWidth(
            320
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
            8
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
        )

        content_layout.addWidget(
            left_container
        )

        # =========================================================
        # CENTER WORKSPACE
        # =========================================================

        center_container = QFrame()

        center_container.setObjectName(
            "panel"
        )

        center_layout = QVBoxLayout(
            center_container
        )

        center_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        center_layout.setSpacing(
            8
        )

        # ---------------------------------------------------------
        # WORKSPACE TABS
        # ---------------------------------------------------------

        self.workspace_tabs = QTabWidget()

        self.workspace_tabs.setObjectName(
            "workspaceTabs"
        )

        self.workspace_tabs.setDocumentMode(
            True
        )

        # =========================================================
        # THRUST CURVE TAB
        # =========================================================

        thrust_workspace = QWidget()

        thrust_layout = QVBoxLayout(
            thrust_workspace
        )

        thrust_layout.setContentsMargins(
            4,
            4,
            4,
            4,
        )

        thrust_layout.setSpacing(
            8
        )

        self.thrust_plot = ThrustPlot()

        self.playback = PlaybackControls()

        thrust_layout.addWidget(
            self.thrust_plot,
            1,
        )

        thrust_layout.addWidget(
            self.playback,
            0,
        )

        self.workspace_tabs.addTab(
            thrust_workspace,
            "Thrust Curve",
        )

        # =========================================================
        # DATA TABLE TAB
        # =========================================================

        data_table_page = self.create_placeholder_page(
            "Data Table",
            (
                "Sample-level test data will be displayed here."
                "\n\n"
                "Planned capabilities:\n"
                "• Browse recorded samples\n"
                "• Inspect time and thrust values\n"
                "• View optional sensor channels\n"
                "• Review processed data"
            ),
        )

        self.workspace_tabs.addTab(
            data_table_page,
            "Data Table",
        )

        # =========================================================
        # ANALYSIS TAB
        # =========================================================

        analysis_page = self.create_placeholder_page(
            "Analysis",
            (
                "Detailed engineering analysis will be displayed here."
                "\n\n"
                "Planned capabilities:\n"
                "• Thrust statistics\n"
                "• Impulse analysis\n"
                "• Performance metrics\n"
                "• Motor classification\n"
                "• C* and Isp analysis"
            ),
        )

        self.workspace_tabs.addTab(
            analysis_page,
            "Analysis",
        )

        # =========================================================
        # COMPARE TAB
        # =========================================================

        compare_page = self.create_placeholder_page(
            "Compare",
            (
                "Test comparison workspace."
                "\n\n"
                "Planned capabilities:\n"
                "• Select multiple tests\n"
                "• Overlay thrust curves\n"
                "• Compare calculated results\n"
                "• Compare motor performance"
            ),
        )

        self.workspace_tabs.addTab(
            compare_page,
            "Compare",
        )

        # =========================================================
        # SIMULATION OVERLAY TAB
        # =========================================================

        simulation_page = self.create_placeholder_page(
            "Simulation Overlay",
            (
                "Simulation comparison workspace."
                "\n\n"
                "Planned capabilities:\n"
                "• Load simulation data\n"
                "• Overlay measured thrust\n"
                "• Compare OpenMotor/BurnSim results\n"
                "• Review measured vs. predicted performance"
            ),
        )

        self.workspace_tabs.addTab(
            simulation_page,
            "Simulation Overlay",
        )

        center_layout.addWidget(
            self.workspace_tabs,
            1,
        )

        # =========================================================
        # LOWER SUPPORTING PANES
        # =========================================================

        lower_panels = QHBoxLayout()

        lower_panels.setSpacing(
            8
        )

        # ---------------------------------------------------------
        # VIDEO OVERLAY
        # ---------------------------------------------------------

        self.video_panel = self.create_video_placeholder()

        lower_panels.addWidget(
            self.video_panel,
            1,
        )

        # ---------------------------------------------------------
        # EXPORT
        # ---------------------------------------------------------

        self.export_panel = self.create_export_placeholder()

        lower_panels.addWidget(
            self.export_panel,
            1,
        )

        # ---------------------------------------------------------
        # MOTOR CLASSIFICATION
        # ---------------------------------------------------------

        self.classification_panel = (
            self.create_classification_panel()
        )

        lower_panels.addWidget(
            self.classification_panel,
            1,
        )

        center_layout.addLayout(
            lower_panels
        )

        content_layout.addWidget(
            center_container,
            1,
        )

        # =========================================================
        # RIGHT SIDEBAR
        # =========================================================

        right_container = QFrame()

        right_container.setObjectName(
            "panel"
        )

        right_container.setMinimumWidth(
            285
        )

        right_container.setMaximumWidth(
            330
        )

        right_layout = QVBoxLayout(
            right_container
        )

        right_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        right_layout.setSpacing(
            8
        )

        # ---------------------------------------------------------
        # KEY RESULTS
        # ---------------------------------------------------------

        self.results = ResultsPanel()

        self.results.status.hide()

        right_layout.addWidget(
            self.results,
            0,
        )

        # ---------------------------------------------------------
        # ADDITIONAL METRICS
        # ---------------------------------------------------------

        self.additional_metrics_panel = (
            self.create_additional_metrics_panel()
        )

        right_layout.addWidget(
            self.additional_metrics_panel,
            1,
        )

        # ---------------------------------------------------------
        # C* ANALYSIS
        # ---------------------------------------------------------

        self.cstar_panel = (
            self.create_cstar_panel()
        )

        right_layout.addWidget(
            self.cstar_panel,
            0,
        )

        content_layout.addWidget(
            right_container
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
    # PLACEHOLDER / SUPPORTING UI
    # =============================================================

    def create_panel_header(
        self,
        title,
    ):
        """Create a standard section heading."""

        label = QLabel(
            title
        )

        label.setObjectName(
            "sectionTitle"
        )

        return label

    def create_placeholder_page(
        self,
        title,
        description,
    ):
        """
        Create a placeholder workspace.

        These pages establish the final application architecture
        before their underlying functionality is implemented.
        """

        page = QFrame()

        page.setObjectName(
            "workspacePlaceholder"
        )

        layout = QVBoxLayout(
            page
        )

        layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "graphTitle"
        )

        title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        description_label = QLabel(
            description
        )

        description_label.setObjectName(
            "graphDescription"
        )

        description_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        description_label.setWordWrap(
            True
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            description_label
        )

        return page

    def create_video_placeholder(self):
        """Create the future video overlay pane."""

        panel = QFrame()

        panel.setObjectName(
            "subPanel"
        )

        layout = QVBoxLayout(
            panel
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            6
        )

        header = self.create_panel_header(
            "Video Overlay"
        )

        layout.addWidget(
            header
        )

        body = QFrame()

        body_layout = QVBoxLayout(
            body
        )

        body_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        status = QLabel(
            "No video loaded"
        )

        status.setObjectName(
            "graphDescription"
        )

        status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        button = QPushButton(
            "Load Video..."
        )

        button.setEnabled(
            False
        )

        body_layout.addWidget(
            status
        )

        body_layout.addWidget(
            button,
            0,
            Qt.AlignmentFlag.AlignCenter,
        )

        layout.addWidget(
            body,
            1,
        )

        return panel

    def create_export_placeholder(self):
        """Create the future export pane."""

        panel = QFrame()

        panel.setObjectName(
            "subPanel"
        )

        layout = QVBoxLayout(
            panel
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            5
        )

        layout.addWidget(
            self.create_panel_header(
                "Export"
            )
        )

        export_items = (
            "OpenRocket",
            "RockSim",
            "BurnSim",
            "Analysis CSV",
            "PDF Report",
        )

        for item in export_items:

            button = QPushButton(
                item
            )

            button.setEnabled(
                False
            )

            layout.addWidget(
                button
            )

        return panel

    def create_classification_panel(self):
        """
        Create the motor classification pane.

        The actual classification result is populated when a test
        is loaded.
        """

        panel = QFrame()

        panel.setObjectName(
            "subPanel"
        )

        layout = QVBoxLayout(
            panel
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            5
        )

        layout.addWidget(
            self.create_panel_header(
                "Motor Classification"
            )
        )

        self.classification_class = QLabel(
            "—"
        )

        self.classification_class.setObjectName(
            "metricValue"
        )

        self.classification_class.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.classification_impulse = QLabel(
            "Measured Impulse: —"
        )

        self.classification_impulse.setObjectName(
            "graphDescription"
        )

        self.classification_impulse.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.classification_range = QLabel(
            "Classification range: —"
        )

        self.classification_range.setObjectName(
            "graphDescription"
        )

        self.classification_range.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            self.classification_class
        )

        layout.addWidget(
            self.classification_impulse
        )

        layout.addWidget(
            self.classification_range
        )

        return panel

    def create_additional_metrics_panel(self):
        """Create the additional metrics pane."""

        panel = QFrame()

        panel.setObjectName(
            "subPanel"
        )

        layout = QVBoxLayout(
            panel
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            5
        )

        layout.addWidget(
            self.create_panel_header(
                "Additional Metrics"
            )
        )

        self.metric_initial_thrust = self.create_metric_row(
            "Initial Thrust",
            "— N",
        )

        self.metric_final_thrust = self.create_metric_row(
            "Final Thrust",
            "— N",
        )

        self.metric_rise_rate = self.create_metric_row(
            "Thrust Rise Rate",
            "— N/s",
        )

        self.metric_decay_rate = self.create_metric_row(
            "Thrust Decay Rate",
            "— N/s",
        )

        self.metric_samples = self.create_metric_row(
            "Samples",
            "—",
        )

        self.metric_sample_rate = self.create_metric_row(
            "Sample Rate",
            "— SPS",
        )

        layout.addWidget(
            self.metric_initial_thrust
        )

        layout.addWidget(
            self.metric_final_thrust
        )

        layout.addWidget(
            self.metric_rise_rate
        )

        layout.addWidget(
            self.metric_decay_rate
        )

        layout.addWidget(
            self.metric_samples
        )

        layout.addWidget(
            self.metric_sample_rate
        )

        layout.addStretch()

        return panel

    def create_metric_row(
        self,
        name,
        value,
    ):
        """Create a simple metric display row."""

        row = QFrame()

        row.setObjectName(
            "metricRow"
        )

        row_layout = QHBoxLayout(
            row
        )

        row_layout.setContentsMargins(
            4,
            2,
            4,
            2,
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
            "metricValueSmall"
        )

        value_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        row_layout.addWidget(
            name_label
        )

        row_layout.addStretch()

        row_layout.addWidget(
            value_label
        )

        return row

    def create_cstar_panel(self):
        """Create the future C* analysis pane."""

        panel = QFrame()

        panel.setObjectName(
            "subPanel"
        )

        layout = QVBoxLayout(
            panel
        )

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            5
        )

        layout.addWidget(
            self.create_panel_header(
                "C* Analysis"
            )
        )

        self.cstar_status = QLabel(
            "C* unavailable"
        )

        self.cstar_status.setObjectName(
            "metricValueSmall"
        )

        self.cstar_status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        cstar_description = QLabel(
            "Chamber pressure data and "
            "nozzle throat area are required "
            "to calculate characteristic "
            "velocity (C*)."
        )

        cstar_description.setObjectName(
            "graphDescription"
        )

        cstar_description.setWordWrap(
            True
        )

        cstar_description.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            self.cstar_status
        )

        layout.addWidget(
            cstar_description
        )

        return panel

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
    # ALIGN EVENT SET
    # =============================================================

    def align_event_set(
        self,
        event_set,
        offset_s,
    ):
        """
        Create an aligned copy of an EventSet.

        Event detection occurs before time alignment in the
        processing pipeline. The prepared data, however, uses the
        aligned time axis.

        This method keeps the event information synchronized with
        that prepared time axis without modifying the original
        EventSet.
        """

        if event_set is None:
            return None

        aligned_events = []

        for event in event_set.events:

            aligned_events.append(
                DetectedEvent(
                    event_type=event.event_type,
                    time_s=float(
                        event.time_s + offset_s
                    ),
                    sample_index=event.sample_index,
                    value=event.value,
                    confidence=event.confidence,
                    label=event.label,
                    notes=event.notes,
                    automatically_detected=(
                        event.automatically_detected
                    ),
                )
            )

        return EventSet(
            events=aligned_events
        )

    # =============================================================
    # PROCESS AND ANALYZE TEST
    # =============================================================

    def process_and_analyze(
        self,
        test_data,
    ):
        """
        Process and analyze a TestData object.

        The GUI establishes an automatic pre-ignition baseline
        and automatically aligns the prepared time axis to ignition.

        Raw data remains untouched.
        """

        processing_settings = (
            ProcessingSettings()
        )

        # ---------------------------------------------------------
        # Determine automatic pre-ignition baseline.
        # ---------------------------------------------------------

        preliminary_events = (
            self.analysis_engine.event_detector.detect_events(
                test_data
            )
        )

        ignition_event = (
            preliminary_events.ignition
        )

        if ignition_event is not None:

            if (
                ignition_event.sample_index is not None
                and ignition_event.sample_index > 0
            ):

                baseline_index = (
                    ignition_event.sample_index - 1
                )

                processing_settings.baseline.baseline_end_time_s = (
                    float(
                        test_data.time_s[
                            baseline_index
                        ]
                    )
                )

            else:

                processing_settings.baseline.baseline_end_time_s = (
                    float(
                        ignition_event.time_s
                    )
                )

        # ---------------------------------------------------------
        # Automatically align motor tests to ignition.
        # ---------------------------------------------------------

        processing_settings.alignment.enabled = True

        processing_settings.alignment.reference_event = (
            preliminary_events.ignition.event_type
            if preliminary_events.ignition is not None
            else processing_settings.alignment.reference_event
        )

        # ---------------------------------------------------------
        # Run the unified processing pipeline.
        # ---------------------------------------------------------

        processing_result = (
            self.processing_pipeline.process(
                test_data,
                processing_settings,
            )
        )

        # ---------------------------------------------------------
        # Shift detected events into aligned time.
        # ---------------------------------------------------------

        aligned_events = self.align_event_set(
            processing_result.event_set,
            processing_result.alignment_result.offset_s,
        )

        # ---------------------------------------------------------
        # Analyze the prepared data.
        # ---------------------------------------------------------

        analysis_result = (
            self.analysis_engine.analyze(
                processing_result.prepared_data,
                events=aligned_events,
            )
        )

        return (
            processing_result,
            analysis_result,
        )

    # =============================================================
    # OPEN CSV TEST
    # =============================================================

    def open_test(
        self,
        filename,
    ):
        """
        Load, process, analyze, and add an RMCS CSV test
        to the session.
        """

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

            test_data = self.reader.read(
                filename
            )

            (
                processing_result,
                analysis_result,
            ) = self.process_and_analyze(
                test_data
            )

            from .project.test_model import TestModel

            test = TestModel(
                data=processing_result.prepared_data
            )

            test.analysis_results = (
                analysis_result
            )

            added = self.session.add_test(
                test
            )

            if not added:
                return

            if self.project_filename is not None:

                self.project_modified = True

            test_index = self.get_test_index(
                test
            )

            if test_index is None:
                return

            self.test_files.add_file(
                test.display_name,
                test_index,
            )

            self.select_test(
                test_index
            )

        except CSVReadError as error:

            QMessageBox.critical(
                self,
                "Unable to Import Test",
                str(error),
            )

        except ValueError as error:

            QMessageBox.critical(
                self,
                "Unable to Process Test",
                str(error),
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Unexpected Error",
                (
                    "An unexpected error occurred "
                    "while importing, processing, "
                    "or analyzing the test:\n\n"
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

        self.session = loaded_session

        self.project_filename = filename

        self.project_modified = False

        self.current_test = None

        self.current_analysis = None

        self.test_files.clear()

        for index, test in enumerate(
            self.session.tests
        ):

            self.test_files.add_file(
                test.display_name,
                index,
            )

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

        project_name = Path(
            filename
        ).name

        self.setWindowTitle(
            f"{project_name} — RMCS Analyzer"
        )

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

        self.project_filename = filename

        self.project_modified = False

        for test in self.session.tests:
            test.mark_saved()

        project_name = Path(
            filename
        ).name

        self.setWindowTitle(
            f"{project_name} — RMCS Analyzer"
        )

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

        self.test_info.set_test_model(
            test
        )

        self.thrust_plot.set_data(
            test.data.time_s,
            test.data.thrust_N,
        )

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
        """Update the visible analysis results."""

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

        # ---------------------------------------------------------
        # Events
        # ---------------------------------------------------------

        ignition_event = (
            events.ignition
        )

        if ignition_event is not None:

            self.results.ignition.setText(
                f"{ignition_event.time_s:.2f} s"
            )

        else:

            self.results.ignition.setText(
                "—"
            )

        peak_event = (
            events.peak_thrust
        )

        if peak_event is not None:

            self.results.peak_event.setText(
                f"{peak_event.time_s:.2f} s"
            )

        else:

            self.results.peak_event.setText(
                "—"
            )

        burnout_event = (
            events.burnout
        )

        if burnout_event is not None:

            self.results.burnout.setText(
                f"{burnout_event.time_s:.2f} s"
            )

        else:

            self.results.burnout.setText(
                "—"
            )

        # ---------------------------------------------------------
        # Additional Metrics
        # ---------------------------------------------------------

        data = self.session.active_test.data

        if data.sample_count > 0:

            initial_thrust = float(
                data.thrust_N[0]
            )

            final_thrust = float(
                data.thrust_N[-1]
            )

            self.metric_initial_thrust.findChildren(
                QLabel
            )[-1].setText(
                f"{initial_thrust:.1f} N"
            )

            self.metric_final_thrust.findChildren(
                QLabel
            )[-1].setText(
                f"{final_thrust:.1f} N"
            )

            self.metric_samples.findChildren(
                QLabel
            )[-1].setText(
                f"{data.sample_count:,}"
            )

            self.metric_sample_rate.findChildren(
                QLabel
            )[-1].setText(
                f"{data.sample_rate_hz:.2f} SPS"
            )

        # ---------------------------------------------------------
        # Motor Classification Pane
        # ---------------------------------------------------------

        if classification.motor_class is not None:

            self.classification_class.setText(
                f"Class {classification.motor_class}"
            )

        else:

            self.classification_class.setText(
                "Class —"
            )

        if thrust_results.total_impulse_Ns is not None:

            self.classification_impulse.setText(
                (
                    "Measured Impulse: "
                    f"{thrust_results.total_impulse_Ns:.2f} N·s"
                )
            )

        else:

            self.classification_impulse.setText(
                "Measured Impulse: —"
            )

        # ---------------------------------------------------------
        # C* Pane
        # ---------------------------------------------------------

        self.cstar_status.setText(
            "C* unavailable"
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