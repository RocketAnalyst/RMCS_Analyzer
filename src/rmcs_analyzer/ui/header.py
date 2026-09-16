from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class Header(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("header")
        self.setFixedHeight(70)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)

        title = QLabel("RMCS Analyzer")
        title.setObjectName("title")

        subtitle = QLabel("Rocket Motor Characterization System")
        subtitle.setObjectName("subtitle")

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        layout.addLayout(title_layout)
        layout.addStretch()

        self.open_button = QPushButton("Open Test")
        self.open_button.setObjectName("headerButton")

        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("headerButton")

        self.export_button = QPushButton("Export")
        self.export_button.setObjectName("headerButton")

        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName("settingsButton")
        self.settings_button.setFixedWidth(42)

        layout.addWidget(self.open_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.export_button)
        layout.addWidget(self.settings_button)