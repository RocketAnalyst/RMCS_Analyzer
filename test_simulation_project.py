from pathlib import Path
import sys
import tempfile

# The RMCS project uses a src/ layout. Add it to the import path so this
# regression test can be run directly with the project's Python interpreter.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import numpy as np

from rmcs_analyzer.project.project_file import ProjectFile
from rmcs_analyzer.project.session import TestSession
from rmcs_analyzer.simulation import import_simulation_csv


SIM_DIR = Path(__file__).parent / "sim_data"


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def test_project_simulation_round_trip():
    simulation = import_simulation_csv(
        SIM_DIR / "Synthetic-Simulation-BurnSim.csv"
    )

    session = TestSession()
    session.simulation = simulation

    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "simulation_test.rmcs"
        ProjectFile.save(session, str(project_path))

        loaded = ProjectFile.load(str(project_path))
        restored = loaded.simulation

        check(restored is not None, "Simulation was not restored from project.")
        check(np.allclose(restored.time_s, simulation.time_s), "Simulation time changed during project round-trip.")
        check(np.allclose(restored.thrust_N, simulation.thrust_N), "Simulation thrust changed during project round-trip.")
        check(np.allclose(restored.pressure_psi, simulation.pressure_psi), "Simulation pressure changed during project round-trip.")
        check(restored.metadata.source_path == simulation.metadata.source_path, "Simulation source metadata changed.")


def test_legacy_project_without_simulation():
    session = TestSession()
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "legacy_compatible.rmcs"
        ProjectFile.save(session, str(project_path))
        loaded = ProjectFile.load(str(project_path))
        check(loaded.simulation is None, "Projects without simulation should load with no simulation.")


def main():
    tests = [
        test_project_simulation_round_trip,
        test_legacy_project_without_simulation,
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
    print(f"Simulation project tests passed: {passed}/{len(tests)}")


if __name__ == "__main__":
    main()
