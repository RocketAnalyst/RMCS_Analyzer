import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.rmcs_analyzer.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    app.setApplicationName(
        "RMCS Analyzer"
    )

    app.setApplicationDisplayName(
        "RMCS Analyzer"
    )

    # Establish an explicit application font with a valid
    # point size before any widgets are created.
    app_font = QFont(
        "Segoe UI"
    )

    app_font.setPointSize(
        10
    )

    app.setFont(
        app_font
    )

    window = MainWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()