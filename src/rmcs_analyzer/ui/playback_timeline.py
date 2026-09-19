import time

from PySide6.QtCore import QObject, QTimer, Signal


class PlaybackTimeline(QObject):
    """Master RMCS playback timeline independent of video."""

    position_changed = Signal(float)
    playing_changed = Signal(bool)
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._duration_s = 0.0
        self._position_s = 0.0
        self._rate = 1.0
        self._playing = False
        self._last_tick = None

        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    @property
    def duration_s(self):
        return self._duration_s

    @property
    def position_s(self):
        return self._position_s

    @property
    def playing(self):
        return self._playing

    @property
    def rate(self):
        return self._rate

    def set_duration(self, duration_s):
        self._duration_s = max(0.0, float(duration_s or 0.0))
        self.set_position(self._position_s)

    def set_rate(self, rate):
        self._rate = max(0.05, float(rate))

    def set_position(self, position_s, emit=True):
        position = max(0.0, float(position_s or 0.0))
        if self._duration_s > 0.0:
            position = min(position, self._duration_s)

        changed = abs(position - self._position_s) > 1e-9
        self._position_s = position

        if emit and (changed or not self._playing):
            self.position_changed.emit(self._position_s)

    def play(self):
        if self._duration_s <= 0.0:
            return

        if self._position_s >= self._duration_s:
            self._position_s = 0.0
            self.position_changed.emit(0.0)

        if self._playing:
            return

        self._playing = True
        self._last_tick = time.monotonic()
        self._timer.start()
        self.playing_changed.emit(True)

    def pause(self):
        if not self._playing:
            return

        self._tick()
        self._playing = False
        self._timer.stop()
        self._last_tick = None
        self.playing_changed.emit(False)

    def stop(self):
        was_playing = self._playing
        self._playing = False
        self._timer.stop()
        self._last_tick = None
        self.set_position(0.0)
        if was_playing:
            self.playing_changed.emit(False)

    def toggle(self):
        self.pause() if self._playing else self.play()

    def _tick(self):
        if not self._playing:
            return

        now = time.monotonic()
        if self._last_tick is None:
            self._last_tick = now
            return

        elapsed = max(0.0, now - self._last_tick)
        self._last_tick = now

        new_position = self._position_s + elapsed * self._rate

        if new_position >= self._duration_s:
            self._position_s = self._duration_s
            self.position_changed.emit(self._position_s)
            self._playing = False
            self._timer.stop()
            self._last_tick = None
            self.playing_changed.emit(False)
            self.finished.emit()
            return

        self._position_s = new_position
        self.position_changed.emit(self._position_s)
