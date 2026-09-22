from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
)

from .branding import Branding


class Header(QFrame):
    """
    Application header containing RMCS Analyzer branding,
    application status, import controls, and primary actions.
    """

    import_rmcs_requested = Signal()
    import_project_requested = Signal()
    import_simulation_requested = Signal()

    def __init__(
        self,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName(
            "header"
        )

        self.setFixedHeight(
            70
        )

        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            18,
            0,
            18,
            0
        )

        layout.setSpacing(
            10
        )

        # =========================================================
        # RMCS ANALYZER BRANDING
        # =========================================================

        self.branding = Branding(
            mode="compact"
        )

        layout.addWidget(
            self.branding
        )

        # Keep the header focused on the RMCS Analyzer brand.
        # The application descriptor and ROCI tagline are intentionally
        # omitted to match the current dashboard direction.
        layout.addStretch(1)

        # =========================================================
        # APPLICATION STATUS
        # =========================================================

        self.status = QLabel(
            "READY — No test loaded"
        )

        self.status.setObjectName(
            "headerStatus"
        )

        self.status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status.setFixedWidth(
            266
        )

        self.status.setFixedHeight(
            34
        )

        layout.addWidget(
            self.status
        )

        # =========================================================
        # IMPORT MENU
        # =========================================================

        self.import_button = QPushButton(
            "Import"
        )

        self.import_button.setObjectName(
            "headerButton"
        )

        self.import_menu = QMenu(
            self.import_button
        )

        # Give the menu an explicit point-sized font.
        # This prevents Qt from inheriting a pixel-sized font
        # whose point size may be reported as -1.

        menu_font = QFont(
            "Segoe UI"
        )

        menu_font.setPointSize(
            10
        )

        self.import_menu.setFont(
            menu_font
        )

        self.rmcs_action = (
            self.import_menu.addAction(
                "RMCS Test Data (.csv)"
            )
        )

        self.project_action = (
            self.import_menu.addAction(
                "RMCS Analyzer Project (.rmcs)"
            )
        )

        self.simulation_action = (
            self.import_menu.addAction(
                "Simulation Data (.csv)"
            )
        )

        self.import_button.setMenu(
            self.import_menu
        )

        layout.addWidget(
            self.import_button
        )

        # =========================================================
        # SAVE
        # =========================================================

        self.save_button = QPushButton(
            "Save"
        )

        self.save_button.setObjectName(
            "headerButton"
        )

        layout.addWidget(
            self.save_button
        )

        # =========================================================
        # SETTINGS
        # =========================================================

        self.settings_button = QPushButton(
            "⚙"
        )

        self.settings_button.setObjectName(
            "settingsButton"
        )

        self.settings_button.setFixedWidth(
            42
        )

        layout.addWidget(
            self.settings_button
        )

        # =========================================================
        # MENU SIGNALS
        # =========================================================

        self.rmcs_action.triggered.connect(
            self.import_rmcs_requested.emit
        )

        self.project_action.triggered.connect(
            self.import_project_requested.emit
        )

        self.simulation_action.triggered.connect(
            self.import_simulation_requested.emit
        )

        # =========================================================
        # INITIAL STATUS
        # =========================================================

        self.set_status(
            "READY — No test loaded",
            modified=False
        )

    def set_status(
        self,
        text,
        modified=False,
    ):
        """
        Update the application status indicator.

        Green indicates the current project is saved and ready.
        Red indicates the project contains unsaved changes.
        """

        self.status.setText(
            text
        )

        self.status.setProperty(
            "modified",
            "true" if modified else "false"
        )

        self.status.style().unpolish(
            self.status
        )

        self.status.style().polish(
            self.status
        )

        self.status.update()