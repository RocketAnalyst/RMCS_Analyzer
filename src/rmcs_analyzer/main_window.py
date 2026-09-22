from pathlib import Path
import sys

import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QDialog,
    QFrame,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
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

from .simulation import SimulationImportError, import_simulation_csv

from .project.project_file import (
    ProjectFile,
    ProjectFileError,
)

from .ui.branding import Branding
from .ui.header import Header
from .ui.test_info_panel import TestInfoPanel
from .ui.test_files_panel import TestFilesPanel
from .ui.thrust_plot import ThrustPlot
from .ui.pressure_plot import PressurePlot
from .ui.compare_panel import ComparePanel
from .ui.campaign_panel import CampaignPanel
from .ui.playback_controls import PlaybackControls
from .ui.results_panel import ResultsPanel
from .ui.data_table import DataTable
from .ui.analysis_panel import AnalysisPanel
from .ui.motor_classification_panel import MotorClassificationPanel
from .ui.playback_timeline import PlaybackTimeline
from .ui.video_panel import VideoPanel
from .ui.settings_dialog import SettingsDialog
from .ui.metadata_dialog import MetadataDialog


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
        - Pressure Curve
        - Analysis
        - Compare
        - Campaign
        - Data Table
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "RMCS Analyzer"
        )

        self.resize(
            1536,
            1024,
        )

        self.setMinimumSize(
            1280,
            800,
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
        self.playback_timeline = PlaybackTimeline(self)

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
            "sidebarContainer"
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
        self.test_info.setObjectName("sideCard")

        self.test_files = TestFilesPanel()
        self.test_files.setObjectName("sideCard")

        self.branding = Branding(
            mode="full"
        )
        self.branding.setObjectName("brandingCard")

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
            "workspaceContainer"
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

        thrust_options = QHBoxLayout()
        thrust_options.setContentsMargins(4, 0, 4, 0)
        thrust_options.setSpacing(8)
        thrust_options.addWidget(QLabel("Comparison:"))
        self.thrust_simulation_check = QCheckBox("Show Simulation")
        self.thrust_simulation_check.setEnabled(False)
        self.thrust_simulation_check.setToolTip(
            "Overlay the imported project-level simulation on the measured thrust curve."
        )
        thrust_options.addWidget(self.thrust_simulation_check)
        thrust_options.addWidget(self.thrust_plot.events_button)
        thrust_options.addStretch(1)
        thrust_layout.addLayout(thrust_options)

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
        # PRESSURE CURVE TAB
        # =========================================================

        pressure_workspace = QWidget()
        pressure_layout = QVBoxLayout(pressure_workspace)
        pressure_layout.setContentsMargins(4, 4, 4, 4)
        pressure_layout.setSpacing(8)

        pressure_options = QHBoxLayout()
        pressure_options.setContentsMargins(4, 0, 4, 0)
        pressure_options.setSpacing(8)
        pressure_options.addWidget(QLabel("Comparison:"))
        self.pressure_simulation_check = QCheckBox("Show Simulation")
        self.pressure_simulation_check.setEnabled(False)
        self.pressure_simulation_check.setToolTip(
            "Overlay the imported project-level simulation on the measured pressure curve."
        )
        pressure_options.addWidget(self.pressure_simulation_check)
        pressure_options.addStretch(1)
        pressure_layout.addLayout(pressure_options)

        self.pressure_plot = PressurePlot()
        pressure_layout.addWidget(self.pressure_plot, 1)

        self.workspace_tabs.addTab(
            pressure_workspace,
            "Pressure Curve",
        )

        # =========================================================
        # ANALYSIS TAB
        # =========================================================

        self.analysis_panel = AnalysisPanel()

        self.workspace_tabs.addTab(
            self.analysis_panel,
            "Analysis",
        )

        # =========================================================
        # COMPARE TAB
        # =========================================================

        self.compare_panel = ComparePanel()

        self.workspace_tabs.addTab(
            self.compare_panel,
            "Compare",
        )

        # =========================================================
        # CAMPAIGN TAB
        # =========================================================

        self.campaign_panel = CampaignPanel()

        self.workspace_tabs.addTab(
            self.campaign_panel,
            "Campaign",
        )

        # =========================================================
        # DATA TABLE TAB
        # =========================================================

        self.data_table = DataTable()

        self.workspace_tabs.addTab(
            self.data_table,
            "Data Table",
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

        self.video_panel = VideoPanel()

        self.video_panel.setMinimumHeight(205)
        lower_panels.addWidget(
            self.video_panel,
            4,
        )

        # ---------------------------------------------------------
        # EXPORT
        # ---------------------------------------------------------

        self.export_panel = self.create_export_placeholder()

        self.export_panel.setMinimumHeight(205)
        lower_panels.addWidget(
            self.export_panel,
            2,
        )

        # ---------------------------------------------------------
        # MOTOR CLASSIFICATION
        # ---------------------------------------------------------

        self.classification_panel = MotorClassificationPanel()

        self.classification_panel.setMinimumHeight(205)
        lower_panels.addWidget(
            self.classification_panel,
            2,
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
            "sidebarContainer"
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
            "v0.4.0"
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
            "lowerPanelHeader"
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

    def create_export_placeholder(self):
        """Create the compact export pane."""

        panel = QFrame()
        panel.setObjectName("subPanel")
        panel.setMinimumWidth(205)
        panel.setMaximumWidth(220)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)
        layout.addWidget(self.create_panel_header("Export"))
        # Add a little breathing room below the section title so the export
        # buttons sit visually centered in the available pane height rather
        # than appearing pressed against the header.
        layout.addSpacing(7)

        self.burnsim_export_button = QPushButton("BurnSim")
        self.burnsim_export_button.setObjectName("exportButton")
        self.burnsim_export_button.setToolTip(
            "Export the active measured test as a BurnSim test-data CSV."
        )
        self.burnsim_export_button.clicked.connect(self.export_burnsim_csv)

        self.rasp_export_button = QPushButton("RASP / .ENG Motor Curve")
        self.rasp_export_button.setObjectName("exportButton")
        self.rasp_export_button.setToolTip(
            "Export the current single test or multi-test campaign as RASP / .ENG motor data."
        )
        self.rasp_export_button.clicked.connect(self.export_rasp_eng)

        self.analysis_csv_export_button = QPushButton("Analysis CSV")
        self.analysis_csv_export_button.setObjectName("exportButton")
        self.analysis_csv_export_button.setEnabled(True)
        self.analysis_csv_export_button.setToolTip(
            "Export analyzed test results as an Analysis CSV."
        )
        self.analysis_csv_export_button.clicked.connect(self.export_analysis_csv)

        self.pdf_report_export_button = QPushButton("PDF Report")
        self.pdf_report_export_button.setObjectName("exportButton")
        self.pdf_report_export_button.setToolTip(
            "Generate a presentation-ready campaign report."
        )
        self.pdf_report_export_button.clicked.connect(self.export_pdf_report)

        self.video_export_button = QPushButton("Video")
        self.video_export_button.setObjectName("exportButton")
        self.video_export_button.setToolTip(
            "Future Feature — video export is not yet available."
        )
        self.video_export_button.clicked.connect(self.export_video_placeholder)

        self.overlay_export_button = QPushButton("Overlay")
        self.overlay_export_button.setObjectName("exportButton")
        self.overlay_export_button.setToolTip(
            "Future Feature — overlay export is not yet available."
        )
        self.overlay_export_button.clicked.connect(self.export_overlay_placeholder)

        # Keep every export action in one vertical column.  The export pane
        # is deliberately width-constrained so the RASP label cannot force
        # the adjacent Motor Classification pane to collapse.
        for button in (
            self.burnsim_export_button,
            self.rasp_export_button,
            self.analysis_csv_export_button,
            self.pdf_report_export_button,
            self.video_export_button,
            self.overlay_export_button,
        ):
            button.setFixedHeight(25)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            layout.addWidget(button)

        layout.addStretch(1)
        return panel

    def export_burnsim_csv(self):
        """Export the active measured test as a BurnSim test-data CSV."""

        test = self.session.active_test

        if test is None:
            QMessageBox.information(
                self,
                "No Test Loaded",
                "Load a motor test before exporting BurnSim test data.",
            )
            return

        stem = Path(test.filename).stem if test.filename else "RMCS_Test"
        default_name = f"{stem}_BurnSim.csv"

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export BurnSim Test Data",
            default_name,
            "CSV Files (*.csv);;All Files (*.*)",
        )

        if not filename:
            return

        try:
            from .export import export_burnsim_csv

            output_path = export_burnsim_csv(
                test,
                filename,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                "BurnSim Export Unavailable",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "BurnSim Export Failed",
                f"An unexpected error occurred while creating the BurnSim CSV:\n\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "BurnSim CSV Created",
            f"The BurnSim test-data CSV was created successfully.\n\n{output_path}",
            QMessageBox.StandardButton.Ok,
        )


    def _analysis_csv_export_tests(self):
        """Return the test population used for the Analysis CSV export."""
        if self.session.test_count == 0:
            return []

        if self.session.test_count == 1:
            return list(self.session.tests)

        selected_sources = self.campaign_panel.selected_sources()
        return [
            test
            for test in self.session.tests
            if test.source_file and test.source_file in selected_sources
        ]

    def export_analysis_csv(self):
        """Export one analysis-summary row for each selected test."""
        selected_tests = self._analysis_csv_export_tests()
        if not selected_tests:
            QMessageBox.information(
                self,
                "No Campaign Tests Selected",
                (
                    "Select at least one test in the Campaign tab before "
                    "exporting the Analysis CSV."
                ),
            )
            return

        if len(selected_tests) == 1:
            test = selected_tests[0]
            stem = Path(test.filename).stem if test.filename else "RMCS_Test"
            default_name = f"{stem}_Analysis.csv"
            source_label = "test"
        else:
            default_name = "RMCS_Campaign_Analysis.csv"
            source_label = f"{len(selected_tests)}-test campaign"

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analysis CSV",
            default_name,
            "CSV Files (*.csv);;All Files (*.*)",
        )
        if not filename:
            return

        try:
            from .export import export_analysis_csv

            output_path = export_analysis_csv(
                selected_tests,
                filename,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Analysis CSV Export Unavailable",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Analysis CSV Export Failed",
                (
                    "An unexpected error occurred while creating the "
                    f"Analysis CSV:\n\n{error}"
                ),
            )
            return

        QMessageBox.information(
            self,
            "Analysis CSV Created",
            (
                f"The Analysis CSV for the selected {source_label} "
                "was created successfully.\n\n"
                f"{output_path}"
            ),
            QMessageBox.StandardButton.Ok,
        )


    def _rasp_export_tests(self):
        """Return the test population used for the RASP export.

        RMCS treats a multi-test session as a campaign export.  When only one
        test is loaded, that single test is exported.  When multiple tests are
        loaded, the Campaign selection defines which tests are included.
        """
        if self.session.test_count == 0:
            return []

        if self.session.test_count == 1:
            return list(self.session.tests)

        selected_sources = self.campaign_panel.selected_sources()
        selected_tests = [
            test
            for test in self.session.tests
            if test.source_file and test.source_file in selected_sources
        ]
        return selected_tests

    def export_rasp_eng(self):
        """Export a single measured motor or the current Campaign as RASP .ENG."""

        selected_tests = self._rasp_export_tests()
        if not selected_tests:
            QMessageBox.information(
                self,
                "No Campaign Tests Selected",
                (
                    "Select at least one test in the Campaign tab before "
                    "exporting a RASP / .ENG motor curve."
                ),
            )
            return

        if len(selected_tests) == 1:
            test = selected_tests[0]
            stem = Path(test.filename).stem if test.filename else "RMCS_Test"
            default_name = f"{stem}.eng"
            source_label = "test"
        else:
            default_name = "RMCS_Campaign.eng"
            source_label = f"{len(selected_tests)}-test campaign"

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export RASP / .ENG Motor Data",
            default_name,
            "RASP Motor Files (*.eng);;All Files (*.*)",
        )
        if not filename:
            return

        try:
            from .export import export_rasp_eng

            output_path = export_rasp_eng(
                selected_tests,
                filename,
            )
        except ValueError as error:
            QMessageBox.warning(
                self,
                "RASP Export Unavailable",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "RASP Export Failed",
                (
                    "An unexpected error occurred while creating the "
                    f"RASP / .ENG file:\n\n{error}"
                ),
            )
            return

        QMessageBox.information(
            self,
            "RASP / .ENG File Created",
            (
                f"The RASP / .ENG motor data for the selected {source_label} "
                "was created successfully.\n\n"
                f"{output_path}"
            ),
            QMessageBox.StandardButton.Ok,
        )

    def export_video_placeholder(self):
        """Placeholder for the v2 video export feature."""
        QMessageBox.information(
            self,
            "Future Feature",
            "Video export is not yet available.\n\nThis feature is planned for RMCS Analyzer v2.",
        )

    def export_overlay_placeholder(self):
        """Placeholder for the v2 overlay export feature."""
        QMessageBox.information(
            self,
            "Future Feature",
            "Overlay export is not yet available.\n\nThis feature is planned for RMCS Analyzer v2.",
        )


    def export_pdf_report(self):
        """Generate the complete PDF report for the current campaign."""

        if self.session.test_count == 0:
            QMessageBox.information(
                self,
                "No Tests Loaded",
                "Load at least one motor test before generating a PDF report.",
            )
            return

        default_name = "RMCS_Campaign_Report.pdf"

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Campaign PDF Report",
            default_name,
            "PDF Reports (*.pdf);;All Files (*.*)",
        )

        if not filename:
            return

        try:
            # Keep PDF-specific dependencies out of normal application startup.
            from .export import PDFReportError, generate_campaign_pdf_report

            output_path = generate_campaign_pdf_report(
                self.session,
                output_path=filename,
                app_version="0.4.0",
            )
        except ModuleNotFoundError as error:
            package = getattr(error, "name", "") or "required package"
            QMessageBox.critical(
                self,
                "PDF Export Dependency Missing",
                (
                    f"The PDF report requires the {package} package.\n\n"
                    "Install the project dependencies in the RMCS Analyzer virtual environment with:\n\n"
                    "pip install -r requirements.txt"
                ),
            )
            return
        except PDFReportError as error:
            QMessageBox.critical(
                self,
                "PDF Export Failed",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "PDF Export Failed",
                f"An unexpected error occurred while generating the campaign report:\n\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Campaign PDF Report Created",
            f"The campaign PDF report was created successfully.\n\n{output_path}",
            QMessageBox.StandardButton.Ok,
        )


    def create_additional_metrics_panel(self):
        """Create the additional metrics pane."""

        panel = QFrame()

        panel.setObjectName(
            "additionalMetricsPanel"
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
            "cstarPanel"
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

        self.isp_status = QLabel(
            "Isp unavailable"
        )

        self.isp_status.setObjectName(
            "metricValueSmall"
        )

        self.isp_status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.cstar_pressure = QLabel(
            "Average chamber pressure: —"
        )
        self.cstar_pressure.setObjectName(
            "graphDescription"
        )
        self.cstar_pressure.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.cstar_mass_flow = QLabel(
            "Average mass flow: —"
        )
        self.cstar_mass_flow.setObjectName(
            "graphDescription"
        )
        self.cstar_mass_flow.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        cstar_description = QLabel(
            "C* requires valid chamber pressure data, "
            "propellant mass, and nozzle throat diameter."
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
            self.isp_status
        )

        layout.addWidget(
            self.cstar_pressure
        )

        layout.addWidget(
            self.cstar_mass_flow
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

        self.header.import_simulation_requested.connect(
            self.import_simulation
        )

        self.thrust_simulation_check.toggled.connect(
            self.on_thrust_simulation_toggled
        )
        self.pressure_simulation_check.toggled.connect(
            self.on_pressure_simulation_toggled
        )

        self.header.save_button.clicked.connect(
            self.save_project
        )

        self.header.settings_button.clicked.connect(
            self.open_settings
        )

        self.test_files.test_selected.connect(
            self.select_test
        )
        self.test_files.remove_requested.connect(
            self.remove_test
        )

        self.test_info.edit_metadata_requested.connect(
            self.edit_active_test_metadata
        )

        self.video_panel.video_changed.connect(
            self.on_video_changed
        )
        self.video_panel.video_removed.connect(
            self.on_video_removed
        )
        self.video_panel.sync_offset_changed.connect(
            self.on_video_sync_changed
        )
        self.video_panel.overlay_changed.connect(
            self.on_video_overlay_changed
        )
        self.video_panel.simulation_overlay_changed.connect(
            self.on_video_simulation_overlay_changed
        )
        self.video_panel.pressure_overlay_changed.connect(
            self.on_video_pressure_overlay_changed
        )
        self.video_panel.curve_mode_changed.connect(
            self.on_video_curve_mode_changed
        )
        self.video_panel.overlay_positions_changed.connect(
            self.on_video_overlay_positions_changed
        )
        self.video_panel.pressure_overlay_positions_changed.connect(
            self.on_video_pressure_overlay_positions_changed
        )
        self.video_panel.overlay_event_positions_changed.connect(
            self.on_video_overlay_event_positions_changed
        )
        self.video_panel.overlay_configuration_changed.connect(
            self.on_video_overlay_configuration_changed
        )
        self.video_panel.duration_changed.connect(
            self.on_video_duration_changed
        )
        self.video_panel.pdf_frame_changed.connect(
            self.on_video_pdf_frame_changed
        )

        self.playback.play_requested.connect(
            self.playback_timeline.toggle
        )
        self.playback.reset_requested.connect(
            self.playback_timeline.stop
        )
        self.playback.seek_requested.connect(
            self.playback_timeline.set_position
        )
        self.playback.scrub_started.connect(
            self.on_scrub_started
        )
        self.playback.scrub_finished.connect(
            self.on_scrub_finished
        )
        self.playback_timeline.position_changed.connect(
            self.on_playback_position_changed
        )
        self.playback_timeline.playing_changed.connect(
            self.on_playback_state_changed
        )
        self.playback_timeline.finished.connect(
            self.on_playback_finished
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
        Import one or more RMCS-compatible CSV test files.
        """

        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Import RMCS Test Data",
            "",
            (
                "RMCS CSV Test Files (*.csv *.CSV);;"
                "All Files (*.*)"
            ),
        )

        if not filenames:
            return

        # Preserve the existing single-file behavior while allowing a
        # multi-selection to be imported as one operation.  Tests are
        # added to the session first and the individual-test view is
        # updated only once at the end.
        imported_indices = []
        duplicate_indices = []
        failures = []

        for filename in filenames:
            result = self.open_test(
                filename,
                select_test_after=False,
                show_errors=False,
            )

            if result["status"] == "imported":
                imported_indices.append(
                    result["test_index"]
                )
            elif result["status"] == "duplicate":
                duplicate_indices.append(
                    result["test_index"]
                )
            else:
                failures.append(
                    (
                        Path(filename).name,
                        result["error"],
                    )
                )

        # Select the last newly imported test, matching the existing
        # behavior of ending an import operation on the imported test.
        if imported_indices:
            self.test_files.set_current_test(
                imported_indices[-1]
            )
            self.select_test(
                imported_indices[-1]
            )
        elif duplicate_indices:
            self.test_files.set_current_test(
                duplicate_indices[-1]
            )
            self.select_test(
                duplicate_indices[-1]
            )

        if failures:
            message = (
                f"Imported {len(imported_indices)} "
                f"of {len(filenames)} selected file(s)."
            )

            if duplicate_indices:
                message += (
                    f"\n\n{len(duplicate_indices)} "
                    "file(s) were already loaded."
                )

            message += "\n\nFiles that could not be imported:\n"

            message += "\n".join(
                f"• {filename}: {error}"
                for filename, error in failures
            )

            QMessageBox.warning(
                self,
                "Import Completed with Errors",
                message,
            )

    # =============================================================
    # IMPORT SIMULATION DATA
    # =============================================================

    def import_simulation(self):
        """Import and store one project-level simulation dataset."""
        if self.session.simulation is not None:
            response = QMessageBox.question(
                self,
                "Replace Simulation",
                "A simulation dataset is already loaded. Replace it with the selected simulation?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if response != QMessageBox.StandardButton.Yes:
                return

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import Simulation Data",
            "",
            "Simulation CSV Files (*.csv *.CSV);;All Files (*.*)",
        )
        if not filename:
            return

        try:
            simulation = import_simulation_csv(filename)
        except SimulationImportError as error:
            QMessageBox.critical(
                self,
                "Unable to Import Simulation",
                str(error),
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "Unexpected Simulation Import Error",
                f"An unexpected error occurred while importing the simulation:\n\n{error}",
            )
            return

        self.session.simulation = simulation
        self.project_modified = True
        self._update_simulation_controls()

        # Refresh the active test views immediately if one is loaded.
        if self.session.active_test is not None:
            self.display_active_test()

        # Importing simulation data changes the project, so keep the normal
        # project-dirty status rather than presenting the load operation as a
        # separate transient state.
        if self.session.active_test is not None:
            self.update_status(self.session.active_test)
        else:
            self.header.set_status(
                "MODIFIED — Unsaved project changes",
                modified=True,
            )

    def _update_simulation_controls(self):
        """Refresh simulation visibility controls and plot data."""
        simulation = self.session.simulation
        has_thrust = simulation is not None and simulation.has_thrust
        has_pressure = simulation is not None and simulation.has_pressure

        for checkbox, available in (
            (self.thrust_simulation_check, has_thrust),
            (self.pressure_simulation_check, has_pressure),
        ):
            checkbox.blockSignals(True)
            checkbox.setEnabled(available)
            if not available:
                checkbox.setChecked(False)
            checkbox.blockSignals(False)

        self.thrust_plot.set_simulation(
            simulation.time_s if has_thrust else None,
            simulation.thrust_N if has_thrust else None,
            visible=self.thrust_simulation_check.isChecked(),
        )
        self.pressure_plot.set_simulation(
            simulation.time_s if has_pressure else None,
            simulation.pressure_psi if has_pressure else None,
            visible=self.pressure_simulation_check.isChecked(),
        )

    def on_thrust_simulation_toggled(self, checked):
        self.thrust_plot.set_simulation_visible(bool(checked))

    def on_pressure_simulation_toggled(self, checked):
        self.pressure_plot.set_simulation_visible(bool(checked))

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
        Process and analyze a TestData object using the default
        non-destructive processing settings.

        Imported measurement values are not baseline-corrected or
        time-aligned unless those processing options are explicitly
        enabled. A valid source-provided Time Cal (s) timeline is
        selected by the processing pipeline as the analysis timeline.

        Raw imported data remains untouched.
        """

        processing_settings = ProcessingSettings()

        processing_result = (
            self.processing_pipeline.process(
                test_data,
                processing_settings,
            )
        )

        # The processing pipeline's EventSet is authoritative. Because
        # default alignment is disabled, these event times remain on the
        # source-provided analysis timeline.
        events = processing_result.event_set

        analysis_result = (
            self.analysis_engine.analyze(
                processing_result.prepared_data,
                events=events,
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
        select_test_after=True,
        show_errors=True,
    ):
        """
        Load, process, analyze, and add an RMCS CSV test to the session.

        ``select_test_after`` is disabled by batch import so the active
        individual-test view is updated only once after all selected files
        have been processed.

        Returns a small status dictionary for callers that need to report
        batch-import results.
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

            if index is not None and select_test_after:

                self.test_files.set_current_test(
                    index
                )

                self.select_test(
                    index
                )

            return {
                "status": "duplicate",
                "test_index": index,
                "error": None,
            }

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
                return {
                    "status": "duplicate",
                    "test_index": self.get_test_index(test),
                    "error": None,
                }

            if self.project_filename is not None:

                self.project_modified = True

            test_index = self.get_test_index(
                test
            )

            if test_index is None:
                return {
                    "status": "failed",
                    "test_index": None,
                    "error": "The imported test could not be located in the session.",
                }

            self.test_files.add_file(
                test.display_name,
                test_index,
            )

            if select_test_after:

                self.select_test(
                    test_index
                )

            return {
                "status": "imported",
                "test_index": test_index,
                "error": None,
            }

        except CSVReadError as error:

            if show_errors:
                QMessageBox.critical(
                    self,
                    "Unable to Import Test",
                    str(error),
                )

            return {
                "status": "failed",
                "test_index": None,
                "error": str(error),
            }

        except ValueError as error:

            if show_errors:
                QMessageBox.critical(
                    self,
                    "Unable to Process Test",
                    str(error),
                )

            return {
                "status": "failed",
                "test_index": None,
                "error": str(error),
            }

        except Exception as error:

            message = (
                "An unexpected error occurred "
                "while importing, processing, "
                "or analyzing the test:\n\n"
                f"{error}"
            )

            if show_errors:
                QMessageBox.critical(
                    self,
                    "Unexpected Error",
                    message,
                )

            return {
                "status": "failed",
                "test_index": None,
                "error": str(error),
            }

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

        self._update_simulation_controls()

        self.project_filename = filename

        self.project_modified = False

        self.current_test = None

        self.current_analysis = None
        self.playback_timeline.stop()

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

                # Restore the Campaign Analysis selection after the active
                # test view has populated the panel.
                self.campaign_panel.restore_selection(
                    self.session.campaign_selected_sources
                )

        else:

            self.test_info.clear()

            self.thrust_plot.clear()
            self.pressure_plot.clear()
            self.compare_panel.set_tests([])

            self.data_table.clear()

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

        # Opening an RMCS project always establishes a clean saved
        # snapshot.  Rendering/restoring the active test can trigger
        # UI callbacks, so explicitly re-synchronize the runtime
        # modification flags immediately before the final status update.
        for test in self.session.tests:
            test.mark_saved()
        self.project_modified = False

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

            # Campaign selection is project-level UI state, so persist it
            # alongside the loaded tests when the project is saved.
            self.session.campaign_selected_sources = (
                self.campaign_panel.selected_sources()
            )

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
    # REMOVE TEST
    # =============================================================

    def remove_test(
        self,
        test_index,
    ):
        """Remove a loaded test from the current session without deleting its source file."""

        tests = self.session.tests

        if test_index < 0 or test_index >= len(tests):
            return

        test = tests[test_index]
        filename = test.display_name

        response = QMessageBox.question(
            self,
            "Remove Test",
            (
                f"Remove '{filename}' from the current session?\n\n"
                "The original CSV file will not be deleted."
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if response != QMessageBox.StandardButton.Yes:
            return

        was_active = self.session.active_test is test

        if not self.session.remove_test(test):
            return

        self.test_files.remove_file(test_index)
        self.mark_project_modified()

        if self.session.test_count == 0:
            self.current_test = None
            self.current_analysis = None
            self.test_info.clear()
            self.thrust_plot.clear()
            self.pressure_plot.clear()
            self.compare_panel.set_tests([])
            self.campaign_panel.set_tests([])
            self.data_table.clear()
            return

        # Keep the active individual-test view valid after the session
        # collection changes. If the removed test was not active, keep
        # the current test selected. Otherwise select the session's new
        # active test.
        target = (
            self.session.active_test
            if was_active
            else self.current_test
        )

        target_index = self.get_test_index(target)
        if target_index is None:
            target = self.session.active_test
            target_index = self.get_test_index(target)

        if target_index is not None:
            self.test_files.set_current_test(target_index)
            self.select_test(target_index)

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

        self.data_table.set_data(
            test.data
        )

        ignition_time_s = None
        burn_time_s = None
        burnout_time_s = None
        recording_end_time_s = None
        peak_time_s = None
        peak_thrust_N = None

        if test.analysis_results is not None:

            analysis = test.analysis_results

            ignition_event = analysis.events.ignition

            if ignition_event is not None:
                ignition_time_s = ignition_event.time_s

            # Burn Time is the standardized 5% threshold-derived
            # performance metric. Burnout remains the separate
            # detected physical event.
            burn_time_s = analysis.thrust.burn_time_5pct_s

            burnout_event = analysis.events.burnout
            if burnout_event is not None:
                burnout_time_s = burnout_event.time_s

            peak_time_s = (
                analysis.thrust.peak_thrust_time_s
            )

            peak_thrust_N = (
                analysis.thrust.peak_thrust_N
            )

        # The end-of-recording marker represents the final recorded
        # sample, not the standardized 5% burn-end calculation.
        if test.data.sample_count > 0:
            recording_end_time_s = float(
                test.data.time_s[-1]
            )

        simulation = self.session.simulation
        self.thrust_plot.set_simulation(
            simulation.time_s if simulation is not None and simulation.has_thrust else None,
            simulation.thrust_N if simulation is not None and simulation.has_thrust else None,
            visible=self.thrust_simulation_check.isChecked(),
        )

        self.pressure_plot.set_simulation(
            simulation.time_s if simulation is not None and simulation.has_pressure else None,
            simulation.pressure_psi if simulation is not None and simulation.has_pressure else None,
            visible=self.pressure_simulation_check.isChecked(),
        )

        self.thrust_plot.set_data(
            test.data.time_s,
            test.data.thrust_N,
            ignition_time_s=ignition_time_s,
            burn_time_s=burn_time_s,
            burnout_time_s=burnout_time_s,
            recording_end_time_s=recording_end_time_s,
            peak_time_s=peak_time_s,
            peak_thrust_N=peak_thrust_N,
        )

        if test.data.pressure_psi is not None:
            self.pressure_plot.set_data(
                test.data.time_s,
                test.data.pressure_psi,
                ignition_time_s=ignition_time_s,
                burnout_time_s=burnout_time_s,
                recording_end_time_s=recording_end_time_s,
            )
        else:
            self.pressure_plot.clear()

        self.compare_panel.set_tests(
            self.session.tests,
            active_test=test,
        )

        self.campaign_panel.set_tests(
            self.session.tests,
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

            self.analysis_panel.set_results(
                analysis.thrust,
                analysis.statistics,
                analysis.classification,
                recorded_duration_s=test.data.duration_s,
            )

        duration_s = float(test.data.duration_s) if test.data.sample_count else 0.0
        self.playback_timeline.pause()
        self.playback_timeline.set_duration(duration_s)
        self.playback_timeline.set_position(
            min(test.video.playback_position_s, duration_s)
        )
        self.playback.set_duration(duration_s)
        self.playback.set_position(self.playback_timeline.position_s)

        self.video_panel.set_video_state(
            test.video.source_path,
            sync_offset_s=test.video.sync_offset_s,
            show_curve=test.video.show_curve_overlay,
            show_pressure=test.video.show_pressure_overlay,
            show_simulation=test.video.show_simulation_overlay,
            show_results=test.video.show_results_overlay,
            show_events=test.video.show_event_markers,
            curve_x=test.video.curve_overlay_x,
            curve_y=test.video.curve_overlay_y,
            results_x=test.video.results_overlay_x,
            results_y=test.video.results_overlay_y,
            curve_w=test.video.curve_overlay_w,
            curve_h=test.video.curve_overlay_h,
            pressure_x=test.video.pressure_overlay_x,
            pressure_y=test.video.pressure_overlay_y,
            pressure_w=test.video.pressure_overlay_w,
            pressure_h=test.video.pressure_overlay_h,
            results_w=test.video.results_overlay_w,
            results_h=test.video.results_overlay_h,
            event_positions=test.video.normalized_event_positions(),
            curve_title=test.video.curve_title,
            curve_mode=test.video.curve_mode,
            results_title=test.video.results_title,
            result_fields=test.video.result_fields,
            event_visibility=test.video.event_visibility,
            curve_show_grid=test.video.curve_show_grid,
            curve_show_axes=test.video.curve_show_axes,
            curve_show_background=test.video.curve_show_background,
            pdf_frame_position_s=test.video.pdf_frame_position_s,
        )
        self.video_panel.set_timeline_position(
            self.playback_timeline.position_s
        )
        analysis = test.analysis_results
        simulation = self.session.simulation
        self.video_panel.set_analysis(
            test.data.time_s,
            test.data.thrust_N,
            test.data.pressure_psi,
            analysis.thrust if analysis is not None else None,
            analysis.classification if analysis is not None else None,
            analysis.events if analysis is not None else None,
            simulation.time_s if simulation is not None else None,
            simulation.thrust_N if simulation is not None and simulation.has_thrust else None,
            simulation.pressure_psi if simulation is not None and simulation.has_pressure else None,
        )
        self.on_playback_position_changed(
            self.playback_timeline.position_s
        )

        self.update_status(
            test
        )

    # =============================================================
    # PLAYBACK / VIDEO
    # =============================================================

    def on_scrub_started(self, was_playing):
        """Pause the master timeline while the user drags the slider."""
        if was_playing:
            self.playback_timeline.pause()

    def on_scrub_finished(self, was_playing):
        """Resume playback after a seek when playback was active before scrubbing."""
        if was_playing:
            self.playback_timeline.play()


    def on_playback_position_changed(self, position_s):
        """Drive the graph, dynamic metrics, and video from one timeline."""
        test = self.session.active_test
        if test is None:
            return

        test.video.playback_position_s = float(position_s)
        self.playback.set_position(position_s)
        self.video_panel.set_timeline_position(position_s)

        # The playback timeline is video time when a video is loaded.
        # Sync Start is the video timestamp at which RMCS analysis t=0
        # begins. Without a video, playback time is already analysis time.
        analysis_position_s = float(position_s)
        if test.video.has_video:
            analysis_position_s -= float(test.video.sync_offset_s)

        self.thrust_plot.set_playback_position(
            analysis_position_s
        )

        data = test.data
        value = None
        if data.sample_count and data.time_s is not None:
            times = data.time_s
            thrust = data.thrust_N
            if len(times) and analysis_position_s >= float(times[0]):
                index = int(
                    np.searchsorted(
                        times,
                        analysis_position_s,
                        side="left",
                    )
                )
                if index <= 0:
                    value = float(thrust[0])
                elif index >= len(times):
                    value = float(thrust[-1])
                else:
                    t0 = float(times[index - 1])
                    t1 = float(times[index])
                    y0 = float(thrust[index - 1])
                    y1 = float(thrust[index])
                    if t1 == t0:
                        value = y1
                    else:
                        fraction = (analysis_position_s - t0) / (t1 - t0)
                        value = y0 + fraction * (y1 - y0)

        self.results.set_current_thrust(value)

    def on_playback_state_changed(self, playing):
        self.playback.set_playing(playing)
        self.video_panel.set_playing(playing)

    def on_playback_finished(self):
        test = self.session.active_test
        if test is not None:
            test.video.playback_position_s = self.playback_timeline.position_s

    def on_video_changed(self, filename):
        test = self.session.active_test
        if test is None:
            return

        test.video.source_path = filename
        test.video.playback_position_s = self.playback_timeline.position_s
        test.video.pdf_frame_position_s = None
        test.mark_modified()
        self.project_modified = True
        self.update_status(test)

    def on_video_removed(self):
        test = self.session.active_test
        if test is None:
            return

        test.video.clear_video()
        self.video_panel.show_empty_state()
        duration_s = (
            float(test.data.duration_s)
            if test.data.sample_count
            else 0.0
        )
        self.playback_timeline.set_duration(duration_s)
        self.playback.set_duration(duration_s)
        test.mark_modified()
        self.project_modified = True
        self.update_status(test)

    def on_video_pdf_frame_changed(self, position_s):
        test = self.session.active_test
        if test is None:
            return
        if position_s is None:
            test.video.pdf_frame_position_s = None
        else:
            try:
                test.video.pdf_frame_position_s = max(0.0, float(position_s))
            except (TypeError, ValueError):
                test.video.pdf_frame_position_s = None
        test.mark_modified()
        self.project_modified = True
        self.update_status(test)

    def on_video_sync_changed(self, offset_s):
        test = self.session.active_test
        if test is None:
            return
        test.video.sync_offset_s = float(offset_s)
        test.mark_modified()
        self.project_modified = True
        self.on_playback_position_changed(
            self.playback_timeline.position_s
        )
        self.update_status(test)

    def on_video_duration_changed(self, duration_s):
        """Use the full video duration as the playback timeline when video is loaded."""
        test = self.session.active_test
        if test is None:
            return

        duration = float(duration_s or 0.0)

        if duration > 0.0 and test.video.has_video:
            self.playback_timeline.set_duration(duration)
            position = min(
                test.video.playback_position_s,
                duration,
            )
            self.playback_timeline.set_position(position)
            self.playback.set_duration(duration)
            self.playback.set_position(position)
        elif not test.video.has_video:
            duration = (
                float(test.data.duration_s)
                if test.data.sample_count
                else 0.0
            )
            self.playback_timeline.set_duration(duration)
            position = min(
                self.playback_timeline.position_s,
                duration,
            )
            self.playback.set_duration(duration)
            self.playback.set_position(position)

    def on_video_overlay_changed(self, show_curve, show_results, show_events):
        test = self.session.active_test
        if test is None:
            return
        test.video.show_curve_overlay = bool(show_curve)
        test.video.show_results_overlay = bool(show_results)
        test.video.show_event_markers = bool(show_events)
        test.mark_modified()
        self.project_modified = True
        self.update_status(test)

    def on_video_simulation_overlay_changed(self, visible):
        test = self.session.active_test
        if test is None:
            return
        test.video.show_simulation_overlay = bool(visible)
        test.mark_modified()
        self.project_modified = True
        self.update_status(test)

    def on_video_pressure_overlay_changed(self, visible):
        test = self.session.active_test
        if test is None:
            return
        test.video.show_pressure_overlay = bool(visible)
        test.mark_modified()
        self.project_modified = True
        self.update_status(test)

    def on_video_curve_mode_changed(self, mode):
        test = self.session.active_test
        if test is None:
            return
        mode = str(mode or "thrust").strip().lower()
        if mode not in {"thrust", "pressure"}:
            mode = "thrust"
        test.video.curve_mode = mode

        default_titles = {
            "thrust": "Measured Thrust",
            "pressure": "Measured Pressure",
        }
        current_title = str(test.video.curve_title or "").strip()
        if current_title in {
            "Measured Thrust",
            "Measured Pressure",
        }:
            test.video.curve_title = default_titles[mode]

        test.mark_modified()
        self.project_modified = True
        self.update_status(test)

    def on_video_overlay_positions_changed(
        self,
        curve_x, curve_y, results_x, results_y,
        curve_w, curve_h, results_w, results_h,
    ):
        test = self.session.active_test
        if test is None:
            return
        test.video.curve_overlay_x = float(curve_x)
        test.video.curve_overlay_y = float(curve_y)
        test.video.results_overlay_x = float(results_x)
        test.video.results_overlay_y = float(results_y)
        test.video.curve_overlay_w = float(curve_w)
        test.video.curve_overlay_h = float(curve_h)
        test.video.results_overlay_w = float(results_w)
        test.video.results_overlay_h = float(results_h)
        test.mark_modified()
        self.project_modified = True
        self.update_status(test)

    def on_video_pressure_overlay_positions_changed(
        self,
        pressure_x,
        pressure_y,
        pressure_w,
        pressure_h,
    ):
        test = self.session.active_test
        if test is None:
            return
        test.video.pressure_overlay_x = float(pressure_x)
        test.video.pressure_overlay_y = float(pressure_y)
        test.video.pressure_overlay_w = float(pressure_w)
        test.video.pressure_overlay_h = float(pressure_h)
        test.mark_modified()
        self.project_modified = True
        self.update_status(test)

    def on_video_overlay_event_positions_changed(self, positions):
        test = self.session.active_test
        if test is None:
            return
        safe = {}
        for key, value in (positions or {}).items():
            if isinstance(value, (list, tuple)) and len(value) >= 2:
                safe[key] = [
                    max(0.0, min(1.0, float(value[0]))),
                    max(0.0, min(1.0, float(value[1]))),
                ]
        test.video.event_overlay_positions = safe
        test.mark_modified()
        self.project_modified = True
        self.update_status(test)

    def on_video_overlay_configuration_changed(self, configuration):
        test = self.session.active_test
        if test is None:
            return
        test.video.curve_title = configuration.get(
            "curve_title", "Measured Thrust"
        )
        test.video.results_title = configuration.get(
            "results_title", "Test Results"
        )
        test.video.result_fields = list(
            configuration.get("result_fields", [])
        )
        test.video.event_visibility = dict(
            configuration.get(
                "event_visibility",
                {"ignition": True, "peak_thrust": True, "burnout": True},
            )
        )
        test.video.curve_show_grid = bool(
            configuration.get("curve_show_grid", True)
        )
        test.video.curve_show_axes = bool(
            configuration.get("curve_show_axes", True)
        )
        test.video.curve_show_background = bool(
            configuration.get("curve_show_background", True)
        )
        test.mark_modified()
        self.project_modified = True
        self.update_status(test)

    def open_settings(self):
        """Open application settings, beginning with active-test video overlay options."""
        test = self.session.active_test
        configuration = (
            self.video_panel.overlay_configuration()
            if test is not None
            else None
        )
        dialog = SettingsDialog(
            video_configuration=configuration,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if test is None:
            return
        configuration = dialog.configuration()
        self.video_panel.apply_overlay_configuration(configuration)

    # =============================================================
    # UPDATE ACTIVE TEST METADATA
    # =============================================================

    def update_active_test_metadata(self):
        """Store edited basic metadata and refresh dependent analysis."""

        test = self.session.active_test
        if test is None:
            return

        test.test_number = self.test_info.test_number.text().strip()
        test.motor_designation = self.test_info.motor.text().strip()
        test.test_date = self.test_info.date.text().strip()
        test.motor_diameter_mm = self.parse_optional_float(
            self.test_info.diameter.text()
        )
        test.motor_length_mm = self.parse_optional_float(
            self.test_info.length.text()
        )
        test.initial_mass_g = self.parse_optional_float(
            self.test_info.initial_mass.text()
        )
        test.propellant_mass_g = self.parse_optional_float(
            self.test_info.propellant_mass.text()
        )

        self._reanalyze_test(test)

    def edit_active_test_metadata(self):
        """Open the full metadata editor for the active test."""
        test = self.session.active_test
        if test is None:
            return

        dialog = MetadataDialog(test, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.test_info.set_test_model(test)
        self._reanalyze_test(test)

    def _reanalyze_test(self, test):
        """Recalculate one test using its current project metadata overrides."""
        try:
            _, analysis_result = self.process_and_analyze(
                test.analysis_data()
            )
            test.analysis_results = analysis_result
            test.mark_modified()
            self.project_modified = True

            if test is self.session.active_test:
                self.display_active_test()
            else:
                # Compare reads the TestModel directly; refresh it without
                # changing the active-test selection or comparison selection.
                self.compare_panel.set_tests(
                    self.session.tests,
                    active_test=self.session.active_test,
                )
                self.campaign_panel.set_tests(
                    self.session.tests,
                )
                self.update_status(test)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Unable to Recalculate Test",
                (
                    "The metadata was updated, but the test could not be "
                    "recalculated:\n\n"
                    f"{error}"
                ),
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
        """Update the visible analysis results from authoritative results."""

        # ResultsPanel is display-only. Authoritative standardized
        # performance values come directly from AnalysisResults.
        self.results.set_results(
            thrust_results,
            events,
            classification,
        )

        # ---------------------------------------------------------
        # Additional Metrics
        # ---------------------------------------------------------

        initial_thrust = thrust_results.initial_thrust_average_N
        initial_window = thrust_results.initial_thrust_window_s

        if initial_thrust is not None:
            if initial_window is not None:
                initial_text = (
                    f"{initial_thrust:.1f} N"
                )
            else:
                initial_text = f"{initial_thrust:.1f} N"
        else:
            initial_text = "—"

        self.metric_initial_thrust.findChildren(
            QLabel
        )[-1].setText(
            initial_text
        )

        # The minimum thrust is not the final sample and should not be
        # presented as a final thrust measurement. Display the actual
        # final prepared sample only as a diagnostic value.
        data = self.session.active_test.data

        if data.sample_count > 0:
            final_sample_thrust = float(
                data.thrust_N[-1]
            )

            self.metric_final_thrust.findChildren(
                QLabel
            )[-1].setText(
                f"{final_sample_thrust:.1f} N"
            )
        else:
            self.metric_final_thrust.findChildren(
                QLabel
            )[-1].setText(
                "—"
            )

        rise_rate = thrust_results.thrust_rise_rate_N_per_s
        decay_rate = thrust_results.thrust_decay_rate_N_per_s

        self.metric_rise_rate.findChildren(
            QLabel
        )[-1].setText(
            f"{rise_rate:.1f} N/s"
            if rise_rate is not None
            else "—"
        )

        self.metric_decay_rate.findChildren(
            QLabel
        )[-1].setText(
            f"{decay_rate:.1f} N/s"
            if decay_rate is not None
            else "—"
        )

        self.metric_samples.findChildren(
            QLabel
        )[-1].setText(
            f"{statistics.sample_count:,}"
        )

        self.metric_sample_rate.findChildren(
            QLabel
        )[-1].setText(
            f"{statistics.sample_rate_hz:.2f} SPS"
        )

        # ---------------------------------------------------------
        # Motor Classification Pane
        # ---------------------------------------------------------

        self.classification_panel.set_result(
            classification,
            thrust_results.total_impulse_valid_curve_Ns,
        )

        # ---------------------------------------------------------
        # Performance Extensions / C* Pane
        # ---------------------------------------------------------

        isp = thrust_results.isp_s
        isp_status = thrust_results.isp_status

        if isp is not None:
            self.isp_status.setText(
                f"Isp: {isp:.2f} s"
            )
        else:
            self.isp_status.setText(
                f"Isp unavailable: {isp_status}"
            )

        cstar = thrust_results.cstar_m_per_s
        cstar_status = thrust_results.cstar_status

        if cstar is not None:
            self.cstar_status.setText(
                f"C*: {cstar:.2f} m/s"
            )
        else:
            self.cstar_status.setText(
                f"C* unavailable: {cstar_status}"
            )

        avg_pressure = (
            thrust_results.average_chamber_pressure_psi
        )

        if avg_pressure is not None:
            self.cstar_pressure.setText(
                f"Average chamber pressure: "
                f"{avg_pressure:.2f} psi"
            )
        else:
            self.cstar_pressure.setText(
                "Average chamber pressure: —"
            )

        avg_mass_flow = (
            thrust_results.average_mass_flow_kg_per_s
        )

        if avg_mass_flow is not None:
            self.cstar_mass_flow.setText(
                f"Average mass flow: "
                f"{avg_mass_flow:.4f} kg/s"
            )
        else:
            self.cstar_mass_flow.setText(
                "Average mass flow: —"
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

            # Distinguish project-level changes (such as imported
            # simulation data) from edits to an individual test.
            # A project-level change does not modify the source CSV.
            if self.session.has_modified_tests:
                status_text = f"MODIFIED — {test.filename}"
            else:
                status_text = "MODIFIED — Unsaved project changes"

            self.header.set_status(
                status_text,
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