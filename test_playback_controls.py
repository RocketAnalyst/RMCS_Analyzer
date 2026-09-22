import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from PySide6.QtWidgets import QApplication

from rmcs_analyzer.ui.playback_controls import PlaybackControls


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def test_playback_controls_seek_while_scrubbing():
    app = QApplication.instance() or QApplication([])
    controls = PlaybackControls()
    controls.set_duration(10.0)

    seeks = []
    scrub_started = []
    scrub_finished = []
    controls.seek_requested.connect(seeks.append)
    controls.scrub_started.connect(scrub_started.append)
    controls.scrub_finished.connect(scrub_finished.append)

    controls.set_playing(True)
    controls._slider_pressed()
    check(scrub_started == [True], "Scrub start did not report the previous playing state.")

    controls._slider_moved(500)
    check(seeks and abs(seeks[-1] - 5.0) < 1e-9, "Slider movement did not request a live seek.")

    controls._slider_released()
    check(scrub_finished == [True], "Scrub finish did not preserve the previous playing state.")

    controls.deleteLater()
    app.processEvents()


def main():
    test_playback_controls_seek_while_scrubbing()
    print("PASS: test_playback_controls_seek_while_scrubbing")
    print("Playback control tests passed: 1/1")


if __name__ == "__main__":
    main()
