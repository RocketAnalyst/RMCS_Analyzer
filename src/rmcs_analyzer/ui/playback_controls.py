from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
)


class PlaybackControls(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("playback")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        self.reset_button = QPushButton("⏮")
        self.reset_button.setObjectName("playbackButton")

        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("playButton")

        self.stop_button = QPushButton("⏹")
        self.stop_button.setObjectName("playbackButton")

        self.time_label = QLabel("0.000 s")
        self.time_label.setObjectName("timeLabel")

        layout.addWidget(self.reset_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)
        layout.addSpacing(16)
        layout.addWidget(self.time_label)
        layout.addStretch()