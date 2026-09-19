from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSlider


class PlaybackControls(QFrame):
    """Controls for the shared RMCS playback timeline."""

    play_requested = Signal()
    pause_requested = Signal()
    reset_requested = Signal()
    seek_requested = Signal(float)
    scrub_started = Signal(bool)
    scrub_finished = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("playback")
        self._duration_s = 0.0
        self._updating = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        self.reset_button = QPushButton("⏮")
        self.reset_button.setObjectName("playbackButton")
        self.reset_button.setToolTip("Reset playback")

        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("playButton")
        self.play_button.setToolTip("Play")

        self.stop_button = QPushButton("⏹")
        self.stop_button.setObjectName("playbackButton")
        self.stop_button.setToolTip("Stop and reset")

        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setObjectName("playbackSlider")
        self.time_slider.setRange(0, 1000)
        self.time_slider.setSingleStep(1)
        self.time_slider.setPageStep(50)

        self.time_label = QLabel("0.000 / 0.000 s")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setMinimumWidth(125)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.reset_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)
        layout.addSpacing(8)
        layout.addWidget(self.time_slider, 1)
        layout.addWidget(self.time_label)

        self.play_button.clicked.connect(self.play_requested.emit)
        self.reset_button.clicked.connect(self.reset_requested.emit)
        self.stop_button.clicked.connect(self.reset_requested.emit)
        self.time_slider.sliderMoved.connect(self._slider_moved)
        self.time_slider.sliderPressed.connect(self._slider_pressed)
        self.time_slider.sliderReleased.connect(self._slider_released)

        self._slider_was_moving = False
        self._was_playing_before_scrub = False

    def set_duration(self, duration_s):
        self._duration_s = max(0.0, float(duration_s or 0.0))
        self.set_position(0.0)

    def set_position(self, position_s):
        position = max(0.0, float(position_s or 0.0))
        if self._duration_s > 0:
            position = min(position, self._duration_s)

        self._updating = True
        try:
            value = int(round((position / self._duration_s) * 1000)) if self._duration_s else 0
            self.time_slider.setValue(value)
            self.time_label.setText(f"{position:.3f} / {self._duration_s:.3f} s")
        finally:
            self._updating = False

    def set_playing(self, playing):
        self.play_button.setText("⏸" if playing else "▶")
        self.play_button.setToolTip("Pause" if playing else "Play")

    def _slider_pressed(self):
        self._slider_was_moving = True
        self._was_playing_before_scrub = self.play_button.text() == "⏸"
        self.scrub_started.emit(self._was_playing_before_scrub)

    def _slider_moved(self, value):
        if self._updating or self._duration_s <= 0:
            return
        position = (value / 1000.0) * self._duration_s
        self.time_label.setText(f"{position:.3f} / {self._duration_s:.3f} s")

    def _slider_released(self):
        was_playing = self._was_playing_before_scrub
        if self._duration_s <= 0:
            self._slider_was_moving = False
            self._was_playing_before_scrub = False
            self.scrub_finished.emit(was_playing)
            return

        value = self.time_slider.value()
        position = (value / 1000.0) * self._duration_s
        self.seek_requested.emit(position)
        self._slider_was_moving = False
        self._was_playing_before_scrub = False
        self.scrub_finished.emit(was_playing)
