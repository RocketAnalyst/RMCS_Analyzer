import os
import tempfile

import numpy as np

from src.rmcs_analyzer.data.models import (
    TestData,
    TestMetadata,
)

from src.rmcs_analyzer.project.project_file import (
    ProjectFile,
)

from src.rmcs_analyzer.project.session import (
    TestSession,
)

from src.rmcs_analyzer.project.test_model import (
    TestModel,
)

from src.rmcs_analyzer.processing.event_model import (
    DetectedEvent,
    EventSet,
    EventType,
)

from src.rmcs_analyzer.analysis.results import (
    AnalysisResults,
    ThrustResults,
    StatisticalResults,
    MotorClassification,
)


def print_header(title):
    print()
    print("=" * 75)
    print(title)
    print("=" * 75)


def create_test():
    """Create a representative test model for project testing."""

    time = np.arange(
        0.0,
        1.0,
        0.1,
    )

    thrust = np.array(
        [
            0.0,
            0.0,
            10.0,
            50.0,
            100.0,
            80.0,
            40.0,
            10.0,
            0.0,
            0.0,
        ],
        dtype=float,
    )

    metadata = TestMetadata(
        source_file="test_data/test_motor.csv",
        rmcs_version="0.1.0",
        test_number=12,
        calibration_counts_per_newton=100.0,
        tare_raw=12345,
        motor_designation="TEST MOTOR",
        manufacturer="RMCS Analyzer",
        builder="Test Builder",
        test_date="9-17-2026",
        location="Muncie, IN",
        motor_diameter=2.6,
        motor_length=7.5,
        initial_mass=425.0,
        propellant_mass=250.0,
        propellant_type="Composite",
        nozzle_throat=0.25,
        nozzle_exit=0.50,
        notes="Project file round-trip test.",
    )

    data = TestData(
        time_s=time,
        thrust_N=thrust,
        raw_hx711=np.arange(
            1000,
            1010,
            dtype=float,
        ),
        delta=np.arange(
            10,
            20,
            dtype=float,
        ),
        state=np.zeros(
            10,
            dtype=int,
        ),
        pressure_kPa=np.linspace(
            0.0,
            100.0,
            10,
        ),
        metadata=metadata,
    )

    events = EventSet(
        events=[
            DetectedEvent(
                event_type=EventType.IGNITION,
                time_s=0.2,
                sample_index=2,
                value=10.0,
                confidence=0.95,
                label="Ignition",
                automatically_detected=True,
            ),
            DetectedEvent(
                event_type=EventType.PEAK_THRUST,
                time_s=0.4,
                sample_index=4,
                value=100.0,
                confidence=1.0,
                label="Peak Thrust",
                automatically_detected=True,
            ),
            DetectedEvent(
                event_type=EventType.BURNOUT,
                time_s=0.8,
                sample_index=8,
                value=0.0,
                confidence=0.90,
                label="Burnout",
                automatically_detected=True,
            ),
        ]
    )

    thrust_results = ThrustResults(
        peak_thrust_N=100.0,
        peak_thrust_time_s=0.4,
        average_thrust_N=36.25,
        burn_time_s=0.6,
        total_impulse_Ns=21.75,
        time_to_peak_s=0.2,
    )

    statistics = StatisticalResults(
        sample_count=10,
        sample_rate_hz=10.0,
        minimum_thrust_N=0.0,
        maximum_thrust_N=100.0,
        baseline_mean_N=0.0,
        baseline_std_N=0.0,
    )

    classification = MotorClassification(
        motor_class="H",
        lower_limit_Ns=160.0,
        upper_limit_Ns=320.0,
        description="Test classification",
    )

    analysis = AnalysisResults(
        events=events,
        thrust=thrust_results,
        statistics=statistics,
        classification=classification,
    )

    test = TestModel(
        data=data,
        test_number="012",
        motor_designation="TEST MOTOR",
        manufacturer="RMCS Analyzer",
        test_date="9-17-2026",
        location="Muncie, IN",
        motor_diameter_in=2.6,
        motor_length_in=7.5,
        initial_mass_g=425.0,
        propellant_mass_g=250.0,
        propellant_type="Composite",
        nozzle_throat_in=0.25,
        nozzle_exit_in=0.50,
        notes="Project file round-trip test.",
        source_file="test_data/test_motor.csv",
    )

    test.analysis_results = analysis

    return test


def assert_arrays_equal(original, loaded):
    """Verify two NumPy arrays contain identical data."""

    assert np.array_equal(
        original,
        loaded,
    )


def main():

    print("RMCS Analyzer Project File Test")

    test = create_test()

    session = TestSession()

    added = session.add_test(
        test
    )

    assert added is True

    session.select_test(
        test
    )

    # -------------------------------------------------------------
    # Modify the test before saving.
    #
    # This confirms that the project writer creates a clean
    # saved snapshot rather than persisting the runtime modified
    # flag.
    # -------------------------------------------------------------

    test.modified = True

    print_header(
        "Original session"
    )

    print(
        f"  Tests: {session.test_count}"
    )

    print(
        f"  Active test: {session.active_test.test_number}"
    )

    print(
        f"  Modified: {test.modified}"
    )

    assert session.test_count == 1
    assert session.active_test is test
    assert test.modified is True

    # -------------------------------------------------------------
    # Save project
    # -------------------------------------------------------------

    with tempfile.TemporaryDirectory() as temp_dir:

        project_path = os.path.join(
            temp_dir,
            "round_trip_test.rmcs",
        )

        ProjectFile.save(
            session,
            project_path,
        )

        print()
        print(
            f"Project saved: {project_path}"
        )

        assert os.path.exists(
            project_path
        )

        print(
            "Save: PASSED"
        )

        # ---------------------------------------------------------
        # Load project
        # ---------------------------------------------------------

        loaded_session = ProjectFile.load(
            project_path
        )

        print_header(
            "Loaded session"
        )

        print(
            f"  Tests: {loaded_session.test_count}"
        )

        print(
            f"  Active test: "
            f"{loaded_session.active_test.test_number}"
        )

        loaded_test = (
            loaded_session.active_test
        )

        assert loaded_test is not None

        print(
            f"  Modified: {loaded_test.modified}"
        )

        # A freshly loaded project represents the saved state.
        assert loaded_test.modified is False

        print(
            "Loaded project state: PASSED"
        )

        # ---------------------------------------------------------
        # Test metadata
        # ---------------------------------------------------------

        print_header(
            "Test metadata"
        )

        assert loaded_test.test_number == "012"
        assert loaded_test.motor_designation == "TEST MOTOR"
        assert loaded_test.manufacturer == "RMCS Analyzer"
        assert loaded_test.test_date == "9-17-2026"
        assert loaded_test.location == "Muncie, IN"
        assert loaded_test.motor_diameter_in == 2.6
        assert loaded_test.motor_length_in == 7.5
        assert loaded_test.initial_mass_g == 425.0
        assert loaded_test.propellant_mass_g == 250.0
        assert loaded_test.propellant_type == "Composite"
        assert loaded_test.nozzle_throat_in == 0.25
        assert loaded_test.nozzle_exit_in == 0.50
        assert loaded_test.notes == (
            "Project file round-trip test."
        )

        print(
            "Metadata preserved: YES"
        )

        print(
            "Metadata: PASSED"
        )

        # ---------------------------------------------------------
        # Test data
        # ---------------------------------------------------------

        print_header(
            "Test data"
        )

        loaded_data = loaded_test.data

        assert_arrays_equal(
            test.data.time_s,
            loaded_data.time_s,
        )

        assert_arrays_equal(
            test.data.thrust_N,
            loaded_data.thrust_N,
        )

        assert_arrays_equal(
            test.data.raw_hx711,
            loaded_data.raw_hx711,
        )

        assert_arrays_equal(
            test.data.delta,
            loaded_data.delta,
        )

        assert_arrays_equal(
            test.data.state,
            loaded_data.state,
        )

        assert_arrays_equal(
            test.data.pressure_kPa,
            loaded_data.pressure_kPa,
        )

        print(
            "Time array preserved: YES"
        )

        print(
            "Thrust array preserved: YES"
        )

        print(
            "Optional channels preserved: YES"
        )

        print(
            "Test data: PASSED"
        )

        # ---------------------------------------------------------
        # Source metadata
        # ---------------------------------------------------------

        print_header(
            "Source metadata"
        )

        loaded_metadata = (
            loaded_data.metadata
        )

        assert loaded_metadata.source_file == (
            "test_data/test_motor.csv"
        )

        assert loaded_metadata.rmcs_version == (
            "0.1.0"
        )

        assert loaded_metadata.test_number == 12

        assert (
            loaded_metadata
            .calibration_counts_per_newton
            == 100.0
        )

        assert loaded_metadata.tare_raw == 12345

        assert loaded_metadata.motor_designation == (
            "TEST MOTOR"
        )

        assert loaded_metadata.manufacturer == (
            "RMCS Analyzer"
        )

        assert loaded_metadata.builder == (
            "Test Builder"
        )

        assert loaded_metadata.motor_diameter == 2.6
        assert loaded_metadata.motor_length == 7.5
        assert loaded_metadata.initial_mass == 425.0
        assert loaded_metadata.propellant_mass == 250.0
        assert loaded_metadata.propellant_type == "Composite"
        assert loaded_metadata.nozzle_throat == 0.25
        assert loaded_metadata.nozzle_exit == 0.50

        print(
            "Source metadata preserved: YES"
        )

        print(
            "Source metadata: PASSED"
        )

        # ---------------------------------------------------------
        # Analysis
        # ---------------------------------------------------------

        print_header(
            "Analysis results"
        )

        loaded_analysis = (
            loaded_test.analysis_results
        )

        assert loaded_analysis is not None

        assert isinstance(
            loaded_analysis,
            AnalysisResults,
        )

        assert isinstance(
            loaded_analysis.events,
            EventSet,
        )

        assert loaded_analysis.events.ignition is not None
        assert loaded_analysis.events.peak_thrust is not None
        assert loaded_analysis.events.burnout is not None

        assert np.isclose(
            loaded_analysis.events.ignition.time_s,
            0.2,
        )

        assert np.isclose(
            loaded_analysis.events.peak_thrust.time_s,
            0.4,
        )

        assert np.isclose(
            loaded_analysis.events.burnout.time_s,
            0.8,
        )

        assert np.isclose(
            loaded_analysis.thrust.peak_thrust_N,
            100.0,
        )

        assert np.isclose(
            loaded_analysis.thrust.total_impulse_Ns,
            21.75,
        )

        assert loaded_analysis.classification.motor_class == (
            "H"
        )

        print(
            "EventSet preserved: YES"
        )

        print(
            "Thrust results preserved: YES"
        )

        print(
            "Statistics preserved: YES"
        )

        print(
            "Classification preserved: YES"
        )

        print(
            "Analysis: PASSED"
        )

        # ---------------------------------------------------------
        # Active test
        # ---------------------------------------------------------

        print_header(
            "Active test"
        )

        assert loaded_session.active_test is loaded_test

        print(
            "Active test restored: YES"
        )

        print(
            "Active test: PASSED"
        )

    # -------------------------------------------------------------
    # Final result
    # -------------------------------------------------------------

    print()
    print("=" * 75)
    print(
        "ALL PROJECT FILE TESTS PASSED"
    )
    print("=" * 75)


if __name__ == "__main__":
    main()