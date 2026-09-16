import os
import sys

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

from .ui.header import Header
from .ui.test_info_panel import TestInfoPanel
from .ui.test_files_panel import TestFilesPanel
from .ui.thrust_plot import ThrustPlot
from .ui.playback_controls import PlaybackControls
from .ui.results_panel import ResultsPanel


class MainWindow(QMainWindow):
    """
    Main application window.

    The main window coordinates the UI components and connects
    imported test data to the analysis engine.
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
        # DATA / ANALYSIS
        # =========================================================

        self.reader = RMCSCSVReader()

        self.event_detector = EventDetector()
        self.thrust_analyzer = ThrustAnalyzer()
        self.statistics_analyzer = StatisticsAnalyzer()
        self.class_calculator = MotorClassCalculator()

        self.current_test = None
        self.current_analysis = None

        self.build_ui()

        self.setStyleSheet(
            APPLICATION_STYLE
        )

        self.connect_signals()

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

        main_layout.setSpacing(0)

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

        left_layout.setSpacing(0)

        self.test_info = TestInfoPanel()
        self.test_files = TestFilesPanel()

        left_layout.addWidget(
            self.test_info
        )

        left_layout.addWidget(
            self.test_files,
            1,
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

    def connect_signals(self):
        """Connect GUI signals to application actions."""

        self.header.open_button.clicked.connect(
            self.open_test
        )

    def open_test(self):
        """Open, load, and analyze a CSV test file."""

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Test Data",
            "",
            (
                "CSV Files (*.csv *.CSV);;"
                "All Files (*.*)"
            ),
        )

        if not filename:
            return

        try:
            # -----------------------------------------------------
            # LOAD DATA
            # -----------------------------------------------------

            test_data = self.reader.read(
                filename
            )

            # -----------------------------------------------------
            # ANALYZE DATA
            # -----------------------------------------------------

            events = self.event_detector.detect(
                test_data
            )

            thrust_results = self.thrust_analyzer.analyze(
                test_data,
                events,
            )

            statistics = self.statistics_analyzer.analyze(
                test_data
            )

            if thrust_results.total_impulse_Ns is not None:
                classification = self.class_calculator.classify(
                    thrust_results.total_impulse_Ns
                )
            else:
                classification = self.class_calculator.classify(
                    -1
                )

            # -----------------------------------------------------
            # STORE CURRENT DATA
            # -----------------------------------------------------

            self.current_test = test_data

            self.current_analysis = {
                "events": events,
                "thrust": thrust_results,
                "statistics": statistics,
                "classification": classification,
            }

        except CSVReadError as error:
            QMessageBox.critical(
                self,
                "Unable to Load Test",
                str(error),
            )

            return

        except Exception as error:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                (
                    "An unexpected error occurred "
                    "while loading or analyzing the test:\n\n"
                    f"{error}"
                ),
            )

            return

        # =========================================================
        # UPDATE GUI
        # =========================================================

        self.test_info.set_test_data(
            test_data
        )

        self.test_files.add_file(
            os.path.basename(filename)
        )

        self.thrust_plot.set_data(
            test_data.time_s,
            test_data.thrust_N,
        )

        self.results.set_results(
            thrust_results,
            events,
            classification,
        )

        self.update_status(
            test_data
        )

    def update_status(
        self,
        test_data,
    ):
        """Update the application status display."""

        filename = (
            test_data.metadata.source_file
        )

        self.results.status.setText(
            f"READY — {filename}"
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