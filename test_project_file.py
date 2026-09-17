from pathlib import Path
import tempfile

import numpy as np

from src.rmcs_analyzer.analysis.results import (
    AnalysisResults,
    EventResults,
    MotorClassification,
    StatisticalResults,
    ThrustResults,
)

from src.rmcs_analyzer.data.models import (
    TestData,
    TestMetadata,
)

from src.rmcs_analyzer.project import (
    TestModel,
    TestSession,
)

from src.rmcs_analyzer.project.project_file import (
    ProjectFile,
)


print()
print("RMCS Analyzer Project File Test")
print("=" * 75)


# =============================================================
# CREATE TEST DATA
# =============================================================

time = np.array(
    [
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
    ]
)

thrust = np.array(
    [
        0.0,
        100.0,
        250.0,
        200.0,
        0.0,
    ]
)

raw_hx711 = np.array(
    [
        21915,
        21892,
        21970,
        21940,
        21915,
    ]
)

delta = np.array(
    [
        0,
        -23,
        55,
        25,
        0,
    ]
)

state = np.array(
    [
        "WAITING_FOR_IGNITION",
        "BURNING",
        "BURNING",
        "BURNING",
        "POST_BURN",
    ]
)

metadata = TestMetadata(
    source_file="TEST_SAMPLE.CSV",
    rmcs_version="0.01",
    test_number=12,
    calibration_counts_per_newton=226.0,
    tare_raw=21915,
)

test_data = TestData(
    time_s=time,
    thrust_N=thrust,
    raw_hx711=raw_hx711,
    delta=delta,
    state=state,
    metadata=metadata,
)


# =============================================================
# CREATE TEST MODEL
# =============================================================

test = TestModel(
    data=test_data,
)

test.test_number = "012"
test.motor_designation = "TEST MOTOR"
test.manufacturer = "Test Manufacturer"
test.test_date = "9-17-2026"
test.location = "Test Location"
test.motor_diameter_in = 2.6
test.motor_length_in = 12.0
test.initial_mass_g = 500.0
test.propellant_mass_g = 200.0
test.propellant_type = "Test Propellant"
test.nozzle_throat_in = 0.25
test.nozzle_exit_in = 0.5
test.notes = "Project round-trip test"


# =============================================================
# CREATE ANALYSIS RESULTS
# =============================================================

test.analysis_results = AnalysisResults(
    events=EventResults(
        ignition_time_s=0.1,
        burnout_time_s=0.4,
        peak_time_s=0.2,
        ignition_index=1,
        burnout_index=4,
        peak_index=2,
        detection_method="TEST",
    ),
    thrust=ThrustResults(
        peak_thrust_N=250.0,
        peak_thrust_time_s=0.2,
        average_thrust_N=166.666666,
        burn_time_s=0.3,
        total_impulse_Ns=50.0,
        time_to_peak_s=0.1,
    ),
    statistics=StatisticalResults(
        sample_count=5,
        sample_rate_hz=10.0,
        minimum_thrust_N=0.0,
        maximum_thrust_N=250.0,
        baseline_mean_N=0.0,
        baseline_std_N=0.0,
    ),
    classification=MotorClassification(
        motor_class="B",
        lower_limit_Ns=2.5,
        upper_limit_Ns=5.0,
        description="Test classification",
    ),
)

# Simulate user modification.
test.mark_modified()


# =============================================================
# CREATE SESSION
# =============================================================

session = TestSession()

assert session.add_test(test)

assert session.active_test is test

print("Original session:")
print(f"  Tests: {session.test_count}")
print(f"  Active test: {session.active_test.test_number}")
print(f"  Modified: {session.active_test.modified}")


# =============================================================
# SAVE / LOAD
# =============================================================

with tempfile.TemporaryDirectory() as temp_dir:

    project_path = (
        Path(temp_dir)
        / "round_trip_test.rmcs"
    )

    ProjectFile.save(
        session,
        str(project_path),
    )

    print()
    print(
        f"Project saved: {project_path.name}"
    )

    loaded_session = ProjectFile.load(
        str(project_path)
    )


# =============================================================
# VERIFY
# =============================================================

loaded_test = (
    loaded_session.active_test
)

assert loaded_session.test_count == 1

assert loaded_test is not None

assert loaded_test.test_number == "012"

assert (
    loaded_test.motor_designation
    == "TEST MOTOR"
)

assert (
    loaded_test.manufacturer
    == "Test Manufacturer"
)

assert (
    loaded_test.test_date
    == "9-17-2026"
)

assert (
    loaded_test.motor_diameter_in
    == 2.6
)

assert (
    loaded_test.initial_mass_g
    == 500.0
)

assert (
    loaded_test.propellant_mass_g
    == 200.0
)

assert (
    loaded_test.modified
    is True
)

assert np.array_equal(
    loaded_test.data.time_s,
    time,
)

assert np.array_equal(
    loaded_test.data.thrust_N,
    thrust,
)

assert np.array_equal(
    loaded_test.data.raw_hx711,
    raw_hx711,
)

assert np.array_equal(
    loaded_test.data.delta,
    delta,
)

assert np.array_equal(
    loaded_test.data.state,
    state,
)

assert (
    loaded_test.data.metadata.test_number
    == 12
)

assert (
    loaded_test.data.metadata.tare_raw
    == 21915
)

assert (
    loaded_test.analysis_results
    is not None
)

assert (
    loaded_test.analysis_results.thrust.peak_thrust_N
    == 250.0
)

assert (
    loaded_test.analysis_results.classification.motor_class
    == "B"
)


# =============================================================
# SUCCESS
# =============================================================

print()
print("Loaded session:")
print(
    f"  Tests: {loaded_session.test_count}"
)
print(
    f"  Active test: "
    f"{loaded_test.test_number}"
)
print(
    f"  Motor: "
    f"{loaded_test.motor_designation}"
)
print(
    f"  Peak thrust: "
    f"{loaded_test.analysis_results.thrust.peak_thrust_N} N"
)
print(
    f"  Modified: "
    f"{loaded_test.modified}"
)

print()
print("ALL PROJECT FILE TESTS PASSED")