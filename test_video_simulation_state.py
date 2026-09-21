from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import numpy as np

from rmcs_analyzer.data.models import TestData
from rmcs_analyzer.project.project_file import ProjectFile
from rmcs_analyzer.project.session import TestSession
from rmcs_analyzer.project.test_model import TestModel


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def test_video_simulation_state_round_trip():
    data = TestData(
        time_s=np.array([0.0, 0.1, 0.2], dtype=float),
        thrust_N=np.array([0.0, 10.0, 0.0], dtype=float),
        pressure_psi=np.array([0.0, 20.0, 0.0], dtype=float),
    )
    test = TestModel(data=data, source_file="Synthetic-Test-01.csv")
    test.video.show_simulation_overlay = True
    test.video.curve_mode = "pressure"
    test.video.curve_title = "Measured Pressure"

    session = TestSession()
    check(session.add_test(test), "Test should be added to the session.")

    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "video_simulation_state.rmcs"
        ProjectFile.save(session, str(project_path))

        loaded = ProjectFile.load(str(project_path))
        restored = loaded.active_test

        check(restored is not None, "Active test was not restored.")
        check(restored.video.show_simulation_overlay is True, "Simulation visibility was not persisted.")
        check(restored.video.curve_mode == "pressure", "Video curve mode was not persisted.")
        check(restored.video.curve_title == "Measured Pressure", "Video curve title was not persisted.")


def test_legacy_video_defaults():
    data = TestData(
        time_s=np.array([0.0, 0.1], dtype=float),
        thrust_N=np.array([0.0, 1.0], dtype=float),
    )
    test = TestModel(data=data)
    check(test.video.show_simulation_overlay is False, "Simulation overlay should default to hidden.")
    check(test.video.curve_mode == "thrust", "Video curve mode should default to thrust.")


def test_pdf_frame_position_round_trip():
    data = TestData(
        time_s=np.array([0.0, 0.1, 0.2], dtype=float),
        thrust_N=np.array([0.0, 10.0, 0.0], dtype=float),
    )
    test = TestModel(data=data, source_file="Synthetic-Test-01.csv")
    test.video.source_path = "test-video.mp4"
    test.video.pdf_frame_position_s = 4.25

    session = TestSession()
    check(session.add_test(test), "Test should be added to the session.")

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


def test_pdf_frame_clear():
    data = TestData(
        time_s=np.array([0.0, 0.1], dtype=float),
        thrust_N=np.array([0.0, 1.0], dtype=float),
    )
    test = TestModel(data=data)
    test.video.pdf_frame_position_s = 2.5
    test.video.clear_video()
    check(test.video.pdf_frame_position_s is None, "Removing video should clear the selected PDF frame.")


def main():
    tests = [
        test_video_simulation_state_round_trip,
        test_legacy_video_defaults,
        test_pdf_frame_position_round_trip,
        test_pdf_frame_clear,
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
    print(f"Video simulation state tests passed: {passed}/{len(tests)}")


if __name__ == "__main__":
    main()
