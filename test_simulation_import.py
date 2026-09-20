from pathlib import Path

import numpy as np

from src.rmcs_analyzer.simulation import SimulationImportError, import_simulation_csv


SIM_DIR = Path(__file__).parent / "sim_data"


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def test_burnsim_style_import():
    path = SIM_DIR / "Synthetic-Simulation-BurnSim.csv"
    data = import_simulation_csv(path)

    check(data.time_s.ndim == 1, "BurnSim time data should be 1D.")
    check(len(data.time_s) == 73, f"Expected 73 BurnSim samples, got {len(data.time_s)}.")
    check(data.thrust_N is not None, "BurnSim fixture should contain thrust.")
    check(data.pressure_psi is not None, "BurnSim fixture should contain pressure.")
    check(np.isclose(data.time_s[0], 0.0), "BurnSim time should start at 0 seconds.")
    check(np.isclose(data.time_s[-1], 0.9), "BurnSim time should end at 0.9 seconds.")
    check(np.all(np.isfinite(data.time_s)), "BurnSim time contains non-finite values.")
    check(np.all(np.isfinite(data.thrust_N)), "BurnSim thrust contains non-finite values.")
    check(np.all(np.isfinite(data.pressure_psi)), "BurnSim pressure contains non-finite values.")
    check(np.all(np.diff(data.time_s) >= 0), "BurnSim time must be monotonic.")
    check(np.max(data.thrust_N) > 0, "BurnSim thrust should contain positive values.")
    check(np.max(data.pressure_psi) > 0, "BurnSim pressure should contain positive values.")


def test_openmotor_style_import():
    path = SIM_DIR / "Synthetic-Simulation-OpenMotor.csv"
    data = import_simulation_csv(path)

    check(data.time_s.ndim == 1, "OpenMotor time data should be 1D.")
    check(len(data.time_s) == 73, f"Expected 73 OpenMotor samples, got {len(data.time_s)}.")
    check(data.thrust_N is not None, "OpenMotor fixture should contain thrust.")
    check(data.pressure_psi is not None, "OpenMotor fixture should contain pressure.")
    check(np.all(np.isfinite(data.time_s)), "OpenMotor time contains non-finite values.")
    check(np.all(np.isfinite(data.thrust_N)), "OpenMotor thrust contains non-finite values.")
    check(np.all(np.isfinite(data.pressure_psi)), "OpenMotor pressure contains non-finite values.")
    check(np.all(np.diff(data.time_s) >= 0), "OpenMotor time must be monotonic.")


def test_normalized_results_match():
    burnsim = import_simulation_csv(
        SIM_DIR / "Synthetic-Simulation-BurnSim.csv"
    )
    openmotor = import_simulation_csv(
        SIM_DIR / "Synthetic-Simulation-OpenMotor.csv"
    )

    check(
        np.allclose(burnsim.time_s, openmotor.time_s),
        "Normalized simulation time arrays do not match.",
    )
    check(
        np.allclose(burnsim.thrust_N, openmotor.thrust_N),
        "Normalized simulation thrust arrays do not match.",
    )
    check(
        np.allclose(burnsim.pressure_psi, openmotor.pressure_psi),
        "Normalized simulation pressure arrays do not match.",
    )


def test_missing_file():
    missing = SIM_DIR / "this_file_does_not_exist.csv"

    try:
        import_simulation_csv(missing)
    except SimulationImportError:
        return

    raise AssertionError("Missing simulation file should raise SimulationImportError.")


def main():
    tests = [
        test_burnsim_style_import,
        test_openmotor_style_import,
        test_normalized_results_match,
        test_missing_file,
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
    print(f"Simulation import tests passed: {passed}/{len(tests)}")


if __name__ == "__main__":
    main()
