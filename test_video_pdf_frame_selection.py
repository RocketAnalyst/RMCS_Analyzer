import os

# Keep Qt tests headless when the regression suite is run on a machine without
# a display server.  On normal Windows development machines this is harmless.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from PySide6.QtWidgets import QApplication

from rmcs_analyzer.project.project_file import ProjectFile
from rmcs_analyzer.project.session import TestSession
from rmcs_analyzer.project.model import TestModel
from rmcs_analyzer.data.models import TestData
from rmcs_analyzer.ui.video_panel import VideoPanel

import numpy as np


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def test_video_panel_frame_selection():
    app = QApplication.instance() or QApplication([])
    panel = VideoPanel()

    changes = []
    panel.pdf_frame_changed.connect(changes.append)

    panel._set_pdf_frame_position(2.345)
    check(panel.pdf_frame_position_s() == 2.345, "Selected PDF frame was not stored in the panel.")
    check(panel.pdf_frame_label.text() == "PDF Report Frame: 2.345 s", "Selected frame label is incorrect.")
    check(changes[-1] == 2.345, "Frame selection signal did not emit the selected position.")

    panel._set_pdf_frame_position(None)
    check(panel.pdf_frame_position_s() is None, "Clearing the PDF frame did not restore automatic selection.")
    check(panel.pdf_frame_label.text() == "PDF Report Frame: Automatic", "Automatic frame label is incorrect.")
    check(changes[-1] is None, "Clearing the PDF frame did not emit None.")

    panel.set_video_state("", pdf_frame_position_s=None)
    check(panel.pdf_frame_position_s() is None, "Automatic frame state did not survive video-state initialization.")

    panel.deleteLater()
    app.processEvents()


def test_project_round_trip_preserves_pdf_frame():
    data = TestData(
        time_s=np.array([0.0, 0.1, 0.2], dtype=float),
        thrust_N=np.array([0.0, 10.0, 0.0], dtype=float),
    )
    test = TestModel(data=data, source_file="Synthetic-Test-01.csv")
    test.video.source_path = "test-video.mp4"
    test.video.pdf_frame_position_s = 4.25

    session = TestSession()
    check(session.add_test(test), "Test should be added to the session.")

    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "pdf-frame.rmcs"
        ProjectFile.save(session, str(project_path))
        loaded = ProjectFile.load(str(project_path))

    restored = loaded.active_test
    check(restored is not None, "Active test was not restored.")
    check(
        restored.video.pdf_frame_position_s == 4.25,
        "Selected PDF frame was not persisted in the RMCS project.",
    )


def main():
    tests = [
        test_video_panel_frame_selection,
        test_project_round_trip_preserves_pdf_frame,
    ]
    passed = 0
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
            passed += 1
        except Exception as exc:
            print(f"FAIL: {test.__name__}")
            print(f"      {type(exc).__name__}: {exc}")
            raise
    print()
    print(f"Video PDF frame selection tests passed: {passed}/{len(tests)}")


if __name__ == "__main__":
    main()
