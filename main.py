import sys

from PySide6.QtWidgets import QApplication

from src.rmcs_analyzer.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("RMCS Analyzer")
    app.setApplicationDisplayName("RMCS Analyzer")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()