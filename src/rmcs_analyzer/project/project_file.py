import json
import zipfile

from pathlib import Path
from typing import Any

import numpy as np

from ..analysis.results import (
    AnalysisResults,
    EventResults,
    MotorClassification,
    StatisticalResults,
    ThrustResults,
)

from ..data.models import (
    TestData,
    TestMetadata,
)

from .test_model import TestModel
from .session import TestSession


class ProjectFileError(Exception):
    """Raised when an RMCS Analyzer project cannot be saved or loaded."""


class ProjectFile:
    """
    Save and load RMCS Analyzer project files.

    RMCS project files are ZIP containers containing JSON metadata
    and compressed NumPy test-data arrays.

    The project's saved state is always considered clean when it
    is successfully written. Runtime 'modified' flags are therefore
    not persisted as project data.
    """

    FORMAT_NAME = "RMCS Analyzer Project"
    FORMAT_VERSION = 1
    FILE_EXTENSION = ".rmcs"

    # =============================================================
    # SAVE
    # =============================================================

    @classmethod
    def save(
        cls,
        session: TestSession,
        filename: str,
    ):
        """
        Save a TestSession to an RMCS project file.

        A successfully saved project represents a clean snapshot.
        Individual TestModel.modified flags are therefore not stored.
        """

        path = Path(filename)

        if path.suffix.lower() != cls.FILE_EXTENSION:
            path = path.with_suffix(
                cls.FILE_EXTENSION
            )

        try:

            with zipfile.ZipFile(
                path,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:

                # -------------------------------------------------
                # Project manifest
                # -------------------------------------------------

                manifest = {
                    "format": cls.FORMAT_NAME,
                    "format_version": cls.FORMAT_VERSION,
                    "active_test_index": cls._get_active_index(
                        session
                    ),
                    "test_count": session.test_count,
                }

                cls._write_json(
                    archive,
                    "project.json",
                    manifest,
                )

                # -------------------------------------------------
                # Individual tests
                # -------------------------------------------------

                for index, test in enumerate(
                    session.tests
                ):

                    cls._write_test(
                        archive,
                        test,
                        index,
                    )

        except Exception as error:

            if isinstance(
                error,
                ProjectFileError,
            ):
                raise

            raise ProjectFileError(
                f"Unable to save project:\n{error}"
            ) from error

    # =============================================================
    # LOAD
    # =============================================================

    @classmethod
    def load(
        cls,
        filename: str,
    ) -> TestSession:
        """
        Load an RMCS Analyzer project file into a new TestSession.

        A successfully loaded project represents the last saved state,
        so all loaded tests begin with modified=False.
        """

        path = Path(filename)

        if not path.exists():

            raise ProjectFileError(
                f"Project file does not exist:\n{path}"
            )

        try:

            with zipfile.ZipFile(
                path,
                mode="r",
            ) as archive:

                # -------------------------------------------------
                # Read and validate manifest
                # -------------------------------------------------

                manifest = cls._read_json(
                    archive,
                    "project.json",
                )

                cls._validate_manifest(
                    manifest
                )

                # -------------------------------------------------
                # Reconstruct session
                # -------------------------------------------------

                session = TestSession()

                test_count = manifest.get(
                    "test_count",
                    0,
                )

                for index in range(
                    test_count
                ):

                    test = cls._read_test(
                        archive,
                        index,
                    )

                    if not session.add_test(
                        test
                    ):

                        raise ProjectFileError(
                            "Duplicate test encountered "
                            "while loading project."
                        )

                # -------------------------------------------------
                # Restore active test
                # -------------------------------------------------

                active_index = manifest.get(
                    "active_test_index"
                )

                if active_index is not None:

                    tests = session.tests

                    if (
                        0 <= active_index < len(tests)
                    ):

                        session.select_test(
                            tests[active_index]
                        )

                return session

        except ProjectFileError:
            raise

        except (
            zipfile.BadZipFile,
            KeyError,
            json.JSONDecodeError,
            OSError,
            ValueError,
        ) as error:

            raise ProjectFileError(
                f"Unable to load project:\n{error}"
            ) from error

        except Exception as error:

            raise ProjectFileError(
                f"Unable to load project:\n{error}"
            ) from error

    # =============================================================
    # TEST SERIALIZATION
    # =============================================================

    @classmethod
    def _write_test(
        cls,
        archive,
        test: TestModel,
        index: int,
    ):
        """Write one TestModel to the project archive."""

        test_folder = (
            f"tests/test_{index:04d}"
        )

        # ---------------------------------------------------------
        # Test metadata
        # ---------------------------------------------------------

        metadata = {
            "test_number": test.test_number,
            "motor_designation": test.motor_designation,
            "manufacturer": test.manufacturer,
            "test_date": test.test_date,
            "location": test.location,
            "motor_diameter_in": test.motor_diameter_in,
            "motor_length_in": test.motor_length_in,
            "initial_mass_g": test.initial_mass_g,
            "propellant_mass_g": test.propellant_mass_g,
            "propellant_type": test.propellant_type,
            "nozzle_throat_in": test.nozzle_throat_in,
            "nozzle_exit_in": test.nozzle_exit_in,
            "notes": test.notes,
            "source_file": test.source_file,
        }

        # IMPORTANT:
        # 'modified' is intentionally not stored.
        #
        # A project file is a saved snapshot. When it is loaded,
        # its tests are considered clean until the user changes them.

        cls._write_json(
            archive,
            f"{test_folder}/metadata.json",
            metadata,
        )

        # ---------------------------------------------------------
        # Test data
        # ---------------------------------------------------------

        data = test.data

        arrays = {
            "time_s": data.time_s,
            "thrust_N": data.thrust_N,
        }

        optional_arrays = {
            "raw_hx711": data.raw_hx711,
            "delta": data.delta,
            "state": data.state,
            "pressure_kPa": data.pressure_kPa,
        }

        for name, array in optional_arrays.items():

            if array is not None:
                arrays[name] = array

        data_path = (
            f"{test_folder}/data.npz"
        )

        with archive.open(
            data_path,
            mode="w",
        ) as file:

            np.savez_compressed(
                file,
                **arrays,
            )

        # ---------------------------------------------------------
        # Imported source metadata
        # ---------------------------------------------------------

        source_metadata = cls._serialize_metadata(
            data.metadata
        )

        cls._write_json(
            archive,
            f"{test_folder}/source_metadata.json",
            source_metadata,
        )

        # ---------------------------------------------------------
        # Analysis results
        # ---------------------------------------------------------

        if test.analysis_results is not None:

            analysis = cls._serialize_analysis(
                test.analysis_results
            )

            cls._write_json(
                archive,
                f"{test_folder}/analysis.json",
                analysis,
            )

    @classmethod
    def _read_test(
        cls,
        archive,
        index: int,
    ) -> TestModel:
        """Read one TestModel from the project archive."""

        test_folder = (
            f"tests/test_{index:04d}"
        )

        # ---------------------------------------------------------
        # Metadata
        # ---------------------------------------------------------

        metadata = cls._read_json(
            archive,
            f"{test_folder}/metadata.json",
        )

        # ---------------------------------------------------------
        # Source metadata
        # ---------------------------------------------------------

        source_metadata = cls._read_json(
            archive,
            f"{test_folder}/source_metadata.json",
        )

        test_metadata = (
            cls._deserialize_metadata(
                source_metadata
            )
        )

        # ---------------------------------------------------------
        # Data arrays
        # ---------------------------------------------------------

        data_path = (
            f"{test_folder}/data.npz"
        )

        try:

            with archive.open(
                data_path,
                mode="r",
            ) as file:

                loaded = np.load(
                    file,
                    allow_pickle=False,
                )

                arrays = {
                    name: loaded[name]
                    for name in loaded.files
                }

        except KeyError as error:

            raise ProjectFileError(
                f"Missing test data: {data_path}"
            ) from error

        test_data = TestData(
            time_s=arrays["time_s"],
            thrust_N=arrays["thrust_N"],
            raw_hx711=arrays.get(
                "raw_hx711"
            ),
            delta=arrays.get(
                "delta"
            ),
            state=arrays.get(
                "state"
            ),
            pressure_kPa=arrays.get(
                "pressure_kPa"
            ),
            metadata=test_metadata,
        )

        # ---------------------------------------------------------
        # Test model
        # ---------------------------------------------------------

        test = TestModel(
            data=test_data,
            test_number=metadata.get(
                "test_number",
                "",
            ),
            motor_designation=metadata.get(
                "motor_designation",
                "",
            ),
            manufacturer=metadata.get(
                "manufacturer",
                "",
            ),
            test_date=metadata.get(
                "test_date",
                "",
            ),
            location=metadata.get(
                "location",
                "",
            ),
            motor_diameter_in=metadata.get(
                "motor_diameter_in"
            ),
            motor_length_in=metadata.get(
                "motor_length_in"
            ),
            initial_mass_g=metadata.get(
                "initial_mass_g"
            ),
            propellant_mass_g=metadata.get(
                "propellant_mass_g"
            ),
            propellant_type=metadata.get(
                "propellant_type",
                "",
            ),
            nozzle_throat_in=metadata.get(
                "nozzle_throat_in"
            ),
            nozzle_exit_in=metadata.get(
                "nozzle_exit_in"
            ),
            notes=metadata.get(
                "notes",
                "",
            ),
            source_file=metadata.get(
                "source_file",
                "",
            ),

            # A loaded project is a clean saved snapshot.
            modified=False,
        )

        # ---------------------------------------------------------
        # Analysis
        # ---------------------------------------------------------

        analysis_path = (
            f"{test_folder}/analysis.json"
        )

        if analysis_path in archive.namelist():

            analysis_data = cls._read_json(
                archive,
                analysis_path,
            )

            test.analysis_results = (
                cls._deserialize_analysis(
                    analysis_data
                )
            )

        return test

    # =============================================================
    # METADATA SERIALIZATION
    # =============================================================

    @staticmethod
    def _serialize_metadata(
        metadata: TestMetadata,
    ) -> dict[str, Any]:
        """Convert TestMetadata into JSON-compatible data."""

        return {
            "source_file": metadata.source_file,
            "rmcs_version": metadata.rmcs_version,
            "test_number": metadata.test_number,
            "calibration_counts_per_newton": (
                metadata.calibration_counts_per_newton
            ),
            "tare_raw": metadata.tare_raw,
            "motor_designation": metadata.motor_designation,
            "manufacturer": metadata.manufacturer,
            "builder": metadata.builder,
            "test_date": metadata.test_date,
            "location": metadata.location,
            "motor_diameter": metadata.motor_diameter,
            "motor_length": metadata.motor_length,
            "initial_mass": metadata.initial_mass,
            "propellant_mass": metadata.propellant_mass,
            "propellant_type": metadata.propellant_type,
            "nozzle_throat": metadata.nozzle_throat,
            "nozzle_exit": metadata.nozzle_exit,
            "notes": metadata.notes,
        }

    @staticmethod
    def _deserialize_metadata(
        data: dict[str, Any],
    ) -> TestMetadata:
        """Convert JSON data back into TestMetadata."""

        return TestMetadata(
            source_file=data.get(
                "source_file",
                "",
            ),
            rmcs_version=data.get(
                "rmcs_version"
            ),
            test_number=data.get(
                "test_number"
            ),
            calibration_counts_per_newton=data.get(
                "calibration_counts_per_newton"
            ),
            tare_raw=data.get(
                "tare_raw"
            ),
            motor_designation=data.get(
                "motor_designation",
                "",
            ),
            manufacturer=data.get(
                "manufacturer",
                "",
            ),
            builder=data.get(
                "builder",
                "",
            ),
            test_date=data.get(
                "test_date",
                "",
            ),
            location=data.get(
                "location",
                "",
            ),
            motor_diameter=data.get(
                "motor_diameter"
            ),
            motor_length=data.get(
                "motor_length"
            ),
            initial_mass=data.get(
                "initial_mass"
            ),
            propellant_mass=data.get(
                "propellant_mass"
            ),
            propellant_type=data.get(
                "propellant_type",
                "",
            ),
            nozzle_throat=data.get(
                "nozzle_throat"
            ),
            nozzle_exit=data.get(
                "nozzle_exit"
            ),
            notes=data.get(
                "notes",
                "",
            ),
        )

    # =============================================================
    # ANALYSIS SERIALIZATION
    # =============================================================

    @staticmethod
    def _serialize_analysis(
        analysis: AnalysisResults,
    ) -> dict[str, Any]:
        """Convert AnalysisResults into JSON-compatible data."""

        return {
            "events": {
                "ignition_time_s": (
                    analysis.events.ignition_time_s
                ),
                "burnout_time_s": (
                    analysis.events.burnout_time_s
                ),
                "peak_time_s": (
                    analysis.events.peak_time_s
                ),
                "ignition_index": (
                    analysis.events.ignition_index
                ),
                "burnout_index": (
                    analysis.events.burnout_index
                ),
                "peak_index": (
                    analysis.events.peak_index
                ),
                "detection_method": (
                    analysis.events.detection_method
                ),
            },
            "thrust": {
                "peak_thrust_N": (
                    analysis.thrust.peak_thrust_N
                ),
                "peak_thrust_time_s": (
                    analysis.thrust.peak_thrust_time_s
                ),
                "average_thrust_N": (
                    analysis.thrust.average_thrust_N
                ),
                "burn_time_s": (
                    analysis.thrust.burn_time_s
                ),
                "total_impulse_Ns": (
                    analysis.thrust.total_impulse_Ns
                ),
                "time_to_peak_s": (
                    analysis.thrust.time_to_peak_s
                ),
            },
            "statistics": {
                "sample_count": (
                    analysis.statistics.sample_count
                ),
                "sample_rate_hz": (
                    analysis.statistics.sample_rate_hz
                ),
                "minimum_thrust_N": (
                    analysis.statistics.minimum_thrust_N
                ),
                "maximum_thrust_N": (
                    analysis.statistics.maximum_thrust_N
                ),
                "baseline_mean_N": (
                    analysis.statistics.baseline_mean_N
                ),
                "baseline_std_N": (
                    analysis.statistics.baseline_std_N
                ),
            },
            "classification": {
                "motor_class": (
                    analysis.classification.motor_class
                ),
                "lower_limit_Ns": (
                    analysis.classification.lower_limit_Ns
                ),
                "upper_limit_Ns": (
                    analysis.classification.upper_limit_Ns
                ),
                "description": (
                    analysis.classification.description
                ),
            },
        }

    @staticmethod
    def _deserialize_analysis(
        data: dict[str, Any],
    ) -> AnalysisResults:
        """Convert JSON data back into AnalysisResults."""

        events_data = data["events"]
        thrust_data = data["thrust"]
        statistics_data = data["statistics"]
        classification_data = data["classification"]

        events = EventResults(
            ignition_time_s=events_data.get(
                "ignition_time_s"
            ),
            burnout_time_s=events_data.get(
                "burnout_time_s"
            ),
            peak_time_s=events_data.get(
                "peak_time_s"
            ),
            ignition_index=events_data.get(
                "ignition_index"
            ),
            burnout_index=events_data.get(
                "burnout_index"
            ),
            peak_index=events_data.get(
                "peak_index"
            ),
            detection_method=events_data.get(
                "detection_method",
                "",
            ),
        )

        thrust = ThrustResults(
            peak_thrust_N=thrust_data.get(
                "peak_thrust_N"
            ),
            peak_thrust_time_s=thrust_data.get(
                "peak_thrust_time_s"
            ),
            average_thrust_N=thrust_data.get(
                "average_thrust_N"
            ),
            burn_time_s=thrust_data.get(
                "burn_time_s"
            ),
            total_impulse_Ns=thrust_data.get(
                "total_impulse_Ns"
            ),
            time_to_peak_s=thrust_data.get(
                "time_to_peak_s"
            ),
        )

        statistics = StatisticalResults(
            sample_count=statistics_data.get(
                "sample_count",
                0,
            ),
            sample_rate_hz=statistics_data.get(
                "sample_rate_hz",
                0.0,
            ),
            minimum_thrust_N=statistics_data.get(
                "minimum_thrust_N",
                0.0,
            ),
            maximum_thrust_N=statistics_data.get(
                "maximum_thrust_N",
                0.0,
            ),
            baseline_mean_N=statistics_data.get(
                "baseline_mean_N"
            ),
            baseline_std_N=statistics_data.get(
                "baseline_std_N"
            ),
        )

        classification = MotorClassification(
            motor_class=classification_data.get(
                "motor_class"
            ),
            lower_limit_Ns=classification_data.get(
                "lower_limit_Ns"
            ),
            upper_limit_Ns=classification_data.get(
                "upper_limit_Ns"
            ),
            description=classification_data.get(
                "description",
                "",
            ),
        )

        return AnalysisResults(
            events=events,
            thrust=thrust,
            statistics=statistics,
            classification=classification,
        )

    # =============================================================
    # JSON HELPERS
    # =============================================================

    @staticmethod
    def _write_json(
        archive,
        filename: str,
        data: dict[str, Any],
    ):
        """Write JSON data into a ZIP archive."""

        content = json.dumps(
            data,
            indent=2,
        )

        archive.writestr(
            filename,
            content,
        )

    @staticmethod
    def _read_json(
        archive,
        filename: str,
    ) -> dict[str, Any]:
        """Read JSON data from a ZIP archive."""

        try:

            content = archive.read(
                filename
            )

        except KeyError as error:

            raise ProjectFileError(
                f"Missing project file: {filename}"
            ) from error

        return json.loads(
            content.decode("utf-8")
        )

    # =============================================================
    # VALIDATION
    # =============================================================

    @classmethod
    def _validate_manifest(
        cls,
        manifest: dict[str, Any],
    ):
        """Validate the project manifest."""

        if manifest.get("format") != cls.FORMAT_NAME:

            raise ProjectFileError(
                "This file is not a valid RMCS Analyzer project."
            )

        version = manifest.get(
            "format_version"
        )

        if version != cls.FORMAT_VERSION:

            raise ProjectFileError(
                (
                    "Unsupported RMCS Analyzer project "
                    f"format version: {version}"
                )
            )

        test_count = manifest.get(
            "test_count"
        )

        if not isinstance(
            test_count,
            int,
        ) or test_count < 0:

            raise ProjectFileError(
                "Invalid test count in project."
            )

    # =============================================================
    # SESSION HELPERS
    # =============================================================

    @staticmethod
    def _get_active_index(
        session: TestSession,
    ):
        """Return the active test index without dataclass equality."""

        active_test = session.active_test

        if active_test is None:
            return None

        for index, test in enumerate(
            session.tests
        ):

            if test is active_test:
                return index

        return None