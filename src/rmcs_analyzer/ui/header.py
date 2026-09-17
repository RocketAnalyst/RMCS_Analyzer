from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
)

from .branding import Branding


class Header(QFrame):
    """
    Application header containing RMCS Analyzer branding
    and primary application controls.
    """

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
            0,
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

        layout.addStretch()

        # =========================================================
        # APPLICATION CONTROLS
        # =========================================================

        self.open_button = QPushButton(
            "Open Test"
        )

        self.open_button.setObjectName(
            "headerButton"
        )

        self.save_button = QPushButton(
            "Save"
        )

        self.save_button.setObjectName(
            "headerButton"
        )

        self.export_button = QPushButton(
            "Export"
        )

        self.export_button.setObjectName(
            "headerButton"
        )

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
            self.open_button
        )

        layout.addWidget(
            self.save_button
        )

        layout.addWidget(
            self.export_button
        )

        layout.addWidget(
            self.settings_button
        )