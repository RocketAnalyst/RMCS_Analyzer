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

from ..processing.event_model import (
    DetectedEvent,
    EventSet,
    EventType,
)

from .test_model import TestModel
from .session import TestSession
from .video_state import VideoState
from ..simulation.models import SimulationData, SimulationMetadata


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

    Project files use the current format version while retaining
    read compatibility with legacy version-1 projects.

    Legacy projects containing obsolete data-channel names,
    EventResults, and unaligned time data are migrated when loaded.
    """

    FORMAT_NAME = "RMCS Analyzer Project"
    FORMAT_VERSION = 3
    LEGACY_FORMAT_VERSION = 1
    PRE_VIDEO_FORMAT_VERSION = 2
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
                    "simulation_present": session.simulation is not None,
                    "campaign_selected_sources": (
                        sorted(session.campaign_selected_sources)
                        if session.campaign_selected_sources is not None
                        else None
                    ),
                }

                cls._write_json(
                    archive,
                    "project.json",
                    manifest,
                )

                # -------------------------------------------------
                # Project-level simulation
                # -------------------------------------------------

                if session.simulation is not None:
                    cls._write_simulation(
                        archive,
                        session.simulation,
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

        Legacy project files are migrated into the current runtime
        representation when necessary.
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

                    # Video files remain external to the .rmcs archive.
                    # Resolve saved paths robustly when a project is moved:
                    # 1) use the original path if it still exists;
                    # 2) resolve relative paths beside the .rmcs file;
                    # 3) if an old absolute path no longer exists, look for
                    #    a video with the same filename beside the project.
                    test.video.source_path = cls._resolve_video_source_path(
                        test.video.source_path,
                        path.parent,
                    )

                    if not session.add_test(
                        test
                    ):

                        raise ProjectFileError(
                            "Duplicate test encountered "
                            "while loading project."
                        )

                # -------------------------------------------------
                # Restore project-level simulation
                # -------------------------------------------------

                if manifest.get("simulation_present", False):
                    session.simulation = cls._read_simulation(archive)
                else:
                    session.simulation = None

                # -------------------------------------------------
                # Restore Campaign Analysis selection state
                # -------------------------------------------------

                campaign_sources = manifest.get(
                    "campaign_selected_sources"
                )
                if campaign_sources is None:
                    # Older projects did not persist Campaign selection.
                    # Leave this as None so the Campaign panel defaults
                    # to all loaded tests.
                    session.campaign_selected_sources = None
                elif isinstance(campaign_sources, list):
                    session.campaign_selected_sources = {
                        str(source)
                        for source in campaign_sources
                        if source
                    }
                else:
                    raise ProjectFileError(
                        "Invalid Campaign selection data in project."
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
    # SIMULATION SERIALIZATION
    # =============================================================

    @classmethod
    def _write_simulation(cls, archive, simulation: SimulationData):
        """Store the optional project-level simulation dataset."""
        metadata = {
            "source_path": simulation.metadata.source_path,
            "source_format": simulation.metadata.source_format,
            "simulator": simulation.metadata.simulator,
            "title": simulation.metadata.title,
            "extra": dict(simulation.metadata.extra),
            "has_thrust": simulation.thrust_N is not None,
            "has_pressure": simulation.pressure_psi is not None,
        }
        cls._write_json(archive, "simulation/metadata.json", metadata)
        arrays = {"time_s": simulation.time_s}
        if simulation.thrust_N is not None:
            arrays["thrust_N"] = simulation.thrust_N
        if simulation.pressure_psi is not None:
            arrays["pressure_psi"] = simulation.pressure_psi
        with archive.open("simulation/data.npz", mode="w") as file:
            np.savez_compressed(file, **arrays)

    @classmethod
    def _read_simulation(cls, archive) -> SimulationData:
        metadata = cls._read_json(archive, "simulation/metadata.json")
        try:
            with archive.open("simulation/data.npz", mode="r") as file:
                loaded = np.load(file, allow_pickle=False)
                arrays = {name: loaded[name] for name in loaded.files}
        except KeyError as error:
            raise ProjectFileError("Missing simulation data in project.") from error

        if "time_s" not in arrays:
            raise ProjectFileError("Simulation data is missing time_s.")
        thrust = arrays.get("thrust_N")
        pressure = arrays.get("pressure_psi")
        if thrust is None and pressure is None:
            raise ProjectFileError("Simulation data contains neither thrust nor pressure.")

        sim_metadata = SimulationMetadata(
            source_path=str(metadata.get("source_path", "")),
            source_format=str(metadata.get("source_format", "CSV")),
            simulator=metadata.get("simulator"),
            title=metadata.get("title"),
            extra=metadata.get("extra", {}) or {},
        )
        return SimulationData(
            time_s=arrays["time_s"],
            thrust_N=thrust,
            pressure_psi=pressure,
            metadata=sim_metadata,
        )

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
            "motor_type": test.motor_type,
            "manufacturer": test.manufacturer,
            "builder": test.builder,
            "case_material": test.case_material,
            "test_date": test.test_date,
            "test_stand": test.test_stand,
            "test_operator": test.test_operator,
            "location": test.location,
            "motor_diameter_in": test.motor_diameter_in,
            "motor_length_in": test.motor_length_in,
            "initial_mass_g": test.initial_mass_g,
            "propellant_mass_g": test.propellant_mass_g,
            "propellant_type": test.propellant_type,
            "nozzle_throat_in": test.nozzle_throat_in,
            "nozzle_exit_in": test.nozzle_exit_in,
            "nozzle_material": test.nozzle_material,
            "load_cell": test.load_cell,
            "load_cell_calibration": test.load_cell_calibration,
            "pressure_sensor": test.pressure_sensor,
            "pressure_sensor_calibration": test.pressure_sensor_calibration,
            "sample_rate_hz": test.sample_rate_hz,
            "notes": test.notes,
            "source_file": test.source_file,
            "video": {
                "source_path": test.video.source_path,
                "sync_offset_s": test.video.sync_offset_s,
                "show_curve_overlay": test.video.show_curve_overlay,
                "show_pressure_overlay": test.video.show_pressure_overlay,
                "show_simulation_overlay": test.video.show_simulation_overlay,
                "show_results_overlay": test.video.show_results_overlay,
                "show_event_markers": test.video.show_event_markers,
                "playback_position_s": test.video.playback_position_s,
                "curve_overlay_x": test.video.curve_overlay_x,
                "curve_overlay_y": test.video.curve_overlay_y,
                "curve_overlay_w": test.video.curve_overlay_w,
                "curve_overlay_h": test.video.curve_overlay_h,
                "pressure_overlay_x": test.video.pressure_overlay_x,
                "pressure_overlay_y": test.video.pressure_overlay_y,
                "pressure_overlay_w": test.video.pressure_overlay_w,
                "pressure_overlay_h": test.video.pressure_overlay_h,
                "results_overlay_x": test.video.results_overlay_x,
                "results_overlay_y": test.video.results_overlay_y,
                "results_overlay_w": test.video.results_overlay_w,
                "results_overlay_h": test.video.results_overlay_h,
                "events_overlay_x": test.video.events_overlay_x,
                "events_overlay_y": test.video.events_overlay_y,
                "event_overlay_positions": test.video.normalized_event_positions(),
                "event_visibility": dict(test.video.event_visibility),
                "curve_title": test.video.curve_title,
                "curve_mode": test.video.curve_mode,
                "results_title": test.video.results_title,
                "result_fields": list(test.video.result_fields),
                "curve_show_grid": test.video.curve_show_grid,
                "curve_show_axes": test.video.curve_show_axes,
                "curve_show_background": test.video.curve_show_background,
            },
        }

        # 'modified' is intentionally not stored.
        # A project file represents a saved snapshot.

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
            "calibrated_time_s": data.calibrated_time_s,
            "raw_thrust_N": data.raw_thrust_N,
            "prop_loss_kg": data.prop_loss_kg,
            "pressure_psi": data.pressure_psi,
            "delta": data.delta,
            "state": data.state,
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

        # Current projects use standardized channel names.
        # Version-1 projects may contain the obsolete raw_hx711 and
        # pressure_kPa arrays. Legacy raw_hx711 cannot safely be
        # relabeled as raw_thrust_N, so it is intentionally not
        # migrated into a different physical quantity. Legacy
        # pressure is converted from kPa to the current PSI unit.
        if "pressure_psi" in arrays:
            pressure_psi = arrays["pressure_psi"]
        elif "pressure_kPa" in arrays:
            pressure_psi = arrays["pressure_kPa"] * 0.14503773773020923
        else:
            pressure_psi = None

        test_data = TestData(
            time_s=arrays["time_s"],
            thrust_N=arrays["thrust_N"],
            calibrated_time_s=arrays.get(
                "calibrated_time_s"
            ),
            raw_thrust_N=arrays.get(
                "raw_thrust_N"
            ),
            prop_loss_kg=arrays.get(
                "prop_loss_kg"
            ),
            pressure_psi=pressure_psi,
            delta=arrays.get(
                "delta"
            ),
            state=arrays.get(
                "state"
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
            motor_type=metadata.get(
                "motor_type",
                "",
            ),
            manufacturer=metadata.get(
                "manufacturer",
                "",
            ),
            builder=metadata.get(
                "builder",
                "",
            ),
            case_material=metadata.get(
                "case_material",
                "",
            ),
            test_date=metadata.get(
                "test_date",
                "",
            ),
            test_stand=metadata.get(
                "test_stand",
                "",
            ),
            test_operator=metadata.get(
                "test_operator",
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
            nozzle_material=metadata.get(
                "nozzle_material",
                "",
            ),
            load_cell=metadata.get(
                "load_cell",
                "",
            ),
            load_cell_calibration=metadata.get(
                "load_cell_calibration",
                "",
            ),
            pressure_sensor=metadata.get(
                "pressure_sensor",
                "",
            ),
            pressure_sensor_calibration=metadata.get(
                "pressure_sensor_calibration",
                "",
            ),
            sample_rate_hz=metadata.get(
                "sample_rate_hz"
            ),
            notes=metadata.get(
                "notes",
                "",
            ),
            source_file=metadata.get(
                "source_file",
                "",
            ),
            video=VideoState(
                source_path=metadata.get("video", {}).get("source_path", ""),
                sync_offset_s=metadata.get("video", {}).get("sync_offset_s", 0.0),
                show_curve_overlay=metadata.get("video", {}).get(
                    "show_curve_overlay",
                    metadata.get("video", {}).get("curve_mode", "thrust") != "pressure",
                ),
                show_pressure_overlay=metadata.get("video", {}).get(
                    "show_pressure_overlay",
                    metadata.get("video", {}).get("curve_mode", "thrust") == "pressure",
                ),
                show_simulation_overlay=metadata.get("video", {}).get("show_simulation_overlay", False),
                show_results_overlay=metadata.get("video", {}).get("show_results_overlay", True),
                show_event_markers=metadata.get("video", {}).get("show_event_markers", True),
                playback_position_s=metadata.get("video", {}).get("playback_position_s", 0.0),
                curve_overlay_x=metadata.get("video", {}).get("curve_overlay_x", 0.06),
                curve_overlay_y=metadata.get("video", {}).get("curve_overlay_y", 0.62),
                curve_overlay_w=metadata.get("video", {}).get("curve_overlay_w", 0.56),
                curve_overlay_h=metadata.get("video", {}).get("curve_overlay_h", 0.30),
                pressure_overlay_x=metadata.get("video", {}).get("pressure_overlay_x", 0.06),
                pressure_overlay_y=metadata.get("video", {}).get("pressure_overlay_y", 0.10),
                pressure_overlay_w=metadata.get("video", {}).get("pressure_overlay_w", 0.58),
                pressure_overlay_h=metadata.get("video", {}).get("pressure_overlay_h", 0.34),
                results_overlay_x=metadata.get("video", {}).get("results_overlay_x", 0.70),
                results_overlay_y=metadata.get("video", {}).get("results_overlay_y", 0.06),
                results_overlay_w=metadata.get("video", {}).get("results_overlay_w", 0.25),
                results_overlay_h=metadata.get("video", {}).get("results_overlay_h", 0.22),
                events_overlay_x=metadata.get("video", {}).get("events_overlay_x", 0.06),
                events_overlay_y=metadata.get("video", {}).get("events_overlay_y", 0.05),
                event_overlay_positions=metadata.get("video", {}).get(
                    "event_overlay_positions",
                    {
                        "ignition": [0.05, 0.78],
                        "peak_thrust": [0.18, 0.16],
                        "burnout": [0.82, 0.78],
                    },
                ),
                event_visibility=metadata.get("video", {}).get(
                    "event_visibility",
                    {
                        "ignition": True,
                        "peak_thrust": True,
                        "burnout": True,
                    },
                ),
                curve_title=metadata.get("video", {}).get(
                    "curve_title",
                    "Measured Thrust",
                ),
                curve_mode=(
                    metadata.get("video", {}).get("curve_mode", "thrust")
                    if metadata.get("video", {}).get("curve_mode", "thrust") in {"thrust", "pressure"}
                    else "thrust"
                ),
                results_title=metadata.get("video", {}).get(
                    "results_title",
                    "Test Results",
                ),
                result_fields=metadata.get("video", {}).get(
                    "result_fields",
                    [
                        "designation",
                        "peak_thrust",
                        "average_thrust",
                        "total_impulse",
                        "burn_time",
                    ],
                ),
                curve_show_grid=metadata.get("video", {}).get(
                    "curve_show_grid",
                    True,
                ),
                curve_show_axes=metadata.get("video", {}).get(
                    "curve_show_axes",
                    True,
                ),
                curve_show_background=metadata.get("video", {}).get(
                    "curve_show_background",
                    True,
                ),
            ),

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

            (
                analysis,
                legacy_project,
            ) = cls._deserialize_analysis(
                analysis_data
            )

            test.analysis_results = analysis

            # -----------------------------------------------------
            # Migrate legacy projects.
            #
            # Older projects stored:
            #   EventResults
            #   absolute event times
            #   unaligned test time
            #
            # Current projects use:
            #   EventSet
            #   ignition-aligned prepared time
            #
            # If this is a legacy project and ignition occurred
            # after t=0, shift the saved prepared data and event
            # times so the project opens using the same coordinate
            # system as current CSV imports.
            # -----------------------------------------------------

            if legacy_project:

                cls._migrate_legacy_alignment(
                    test
                )

        return test

    @staticmethod
    def _resolve_video_source_path(source_path: str, project_dir: Path) -> str:
        """Resolve an external video path saved with an RMCS project."""
        if not source_path:
            return ""

        raw = Path(str(source_path)).expanduser()

        # Preserve an existing absolute/working-directory path.
        if raw.exists() and raw.is_file():
            return str(raw.resolve())

        # Relative paths are interpreted relative to the project file.
        if not raw.is_absolute():
            candidate = project_dir / raw
            if candidate.exists() and candidate.is_file():
                return str(candidate.resolve())

        # If the project was moved, the original absolute path may no longer
        # exist. A same-named video beside the project is a safe recovery.
        candidate = project_dir / raw.name
        if candidate.exists() and candidate.is_file():
            return str(candidate.resolve())

        return str(raw)

    # =============================================================
    # LEGACY PROJECT MIGRATION
    # =============================================================

    @staticmethod
    def _migrate_legacy_alignment(
        test: TestModel,
    ):
        """
        Migrate a legacy project from absolute time to
        ignition-relative time.

        This is intentionally limited to legacy EventResults
        projects. Current EventSet projects are assumed to already
        contain the prepared/aligned data saved by the current
        processing pipeline.
        """

        analysis = test.analysis_results

        if analysis is None:
            return

        events = analysis.events

        if not isinstance(
            events,
            EventSet,
        ):
            return

        ignition = events.ignition

        if ignition is None:
            return

        ignition_time = float(
            ignition.time_s
        )

        if not np.isfinite(
            ignition_time
        ):
            return

        if abs(ignition_time) < 1e-12:
            return

        data = test.data

        # ---------------------------------------------------------
        # Shift prepared time axis.
        # ---------------------------------------------------------

        aligned_time = (
            data.time_s.copy()
            - ignition_time
        )

        test.data = TestData(
            time_s=aligned_time,
            thrust_N=data.thrust_N.copy(),
            calibrated_time_s=(
                data.calibrated_time_s.copy()
                if data.calibrated_time_s is not None
                else None
            ),
            raw_thrust_N=(
                data.raw_thrust_N.copy()
                if data.raw_thrust_N is not None
                else None
            ),
            prop_loss_kg=(
                data.prop_loss_kg.copy()
                if data.prop_loss_kg is not None
                else None
            ),
            pressure_psi=(
                data.pressure_psi.copy()
                if data.pressure_psi is not None
                else None
            ),
            delta=(
                data.delta.copy()
                if data.delta is not None
                else None
            ),
            state=(
                data.state.copy()
                if data.state is not None
                else None
            ),
            metadata=data.metadata,
        )

        # ---------------------------------------------------------
        # Shift event times.
        # ---------------------------------------------------------

        shifted_events = []

        for event in events.events:

            shifted_events.append(
                DetectedEvent(
                    event_type=event.event_type,
                    time_s=float(
                        event.time_s
                        - ignition_time
                    ),
                    sample_index=event.sample_index,
                    value=event.value,
                    confidence=event.confidence,
                    label=event.label,
                    notes=event.notes,
                    automatically_detected=(
                        event.automatically_detected
                    ),
                )
            )

        analysis.events = EventSet(
            events=shifted_events
        )

        # ---------------------------------------------------------
        # Shift absolute peak-event time.
        #
        # time_to_peak is already relative to ignition and therefore
        # must not be changed.
        # ---------------------------------------------------------

        if (
            analysis.thrust.peak_thrust_time_s
            is not None
        ):

            analysis.thrust.peak_thrust_time_s = (
                float(
                    analysis.thrust.peak_thrust_time_s
                )
                - ignition_time
            )

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
            "motor_type": metadata.motor_type,
            "manufacturer": metadata.manufacturer,
            "builder": metadata.builder,
            "case_material": metadata.case_material,
            "test_date": metadata.test_date,
            "test_stand": metadata.test_stand,
            "test_operator": metadata.test_operator,
            "location": metadata.location,
            "motor_diameter": metadata.motor_diameter,
            "motor_length": metadata.motor_length,
            "initial_mass": metadata.initial_mass,
            "propellant_mass": metadata.propellant_mass,
            "propellant_type": metadata.propellant_type,
            "nozzle_throat": metadata.nozzle_throat,
            "nozzle_exit": metadata.nozzle_exit,
            "nozzle_material": metadata.nozzle_material,
            "load_cell": metadata.load_cell,
            "load_cell_calibration": metadata.load_cell_calibration,
            "pressure_sensor": metadata.pressure_sensor,
            "pressure_sensor_calibration": metadata.pressure_sensor_calibration,
            "sample_rate_hz": metadata.sample_rate_hz,
            "notes": metadata.notes,
        }


    @staticmethod
    def _deserialize_metadata(
        data: dict[str, Any],
    ) -> TestMetadata:
        """Convert JSON data back into TestMetadata."""

        return TestMetadata(
            source_file=data.get("source_file", ""),
            rmcs_version=data.get("rmcs_version"),
            test_number=data.get("test_number"),
            calibration_counts_per_newton=data.get(
                "calibration_counts_per_newton"
            ),
            tare_raw=data.get("tare_raw"),
            motor_designation=data.get("motor_designation", ""),
            motor_type=data.get("motor_type", ""),
            manufacturer=data.get("manufacturer", ""),
            builder=data.get("builder", ""),
            case_material=data.get("case_material", ""),
            test_date=data.get("test_date", ""),
            test_stand=data.get("test_stand", ""),
            test_operator=data.get("test_operator", ""),
            location=data.get("location", ""),
            motor_diameter=data.get("motor_diameter"),
            motor_length=data.get("motor_length"),
            initial_mass=data.get("initial_mass"),
            propellant_mass=data.get("propellant_mass"),
            propellant_type=data.get("propellant_type", ""),
            nozzle_throat=data.get("nozzle_throat"),
            nozzle_exit=data.get("nozzle_exit"),
            nozzle_material=data.get("nozzle_material", ""),
            load_cell=data.get("load_cell", ""),
            load_cell_calibration=data.get(
                "load_cell_calibration", ""
            ),
            pressure_sensor=data.get("pressure_sensor", ""),
            pressure_sensor_calibration=data.get(
                "pressure_sensor_calibration", ""
            ),
            sample_rate_hz=data.get("sample_rate_hz"),
            notes=data.get("notes", ""),
        )

    # =============================================================
    # ANALYSIS SERIALIZATION
    # =============================================================

    @staticmethod
    def _serialize_analysis(
        analysis: AnalysisResults,
    ) -> dict[str, Any]:
        """
        Convert AnalysisResults into JSON-compatible data.

        Current projects store EventSet.
        A compatibility path is retained for legacy EventResults.
        """

        events = analysis.events

        # ---------------------------------------------------------
        # Current EventSet representation
        # ---------------------------------------------------------

        if isinstance(
            events,
            EventSet,
        ):

            events_data = {
                "format": "event_set",
                "events": events.to_dict()["events"],
            }

        # ---------------------------------------------------------
        # Legacy EventResults representation
        # ---------------------------------------------------------

        elif isinstance(
            events,
            EventResults,
        ):

            events_data = {
                "format": "legacy_event_results",
                "ignition_time_s": (
                    events.ignition_time_s
                ),
                "burnout_time_s": (
                    events.burnout_time_s
                ),
                "peak_time_s": (
                    events.peak_time_s
                ),
                "ignition_index": (
                    events.ignition_index
                ),
                "burnout_index": (
                    events.burnout_index
                ),
                "peak_index": (
                    events.peak_index
                ),
                "detection_method": (
                    events.detection_method
                ),
            }

        else:

            raise ProjectFileError(
                "Unsupported event result type while saving project."
            )

        return {
            "events": events_data,

            "thrust": {
                "peak_thrust_N": analysis.thrust.peak_thrust_N,
                "peak_thrust_time_s": analysis.thrust.peak_thrust_time_s,
                "average_thrust_N": analysis.thrust.average_thrust_N,
                "burn_time_s": analysis.thrust.burn_time_s,
                "total_impulse_Ns": analysis.thrust.total_impulse_Ns,
                "time_to_peak_s": analysis.thrust.time_to_peak_s,
                "threshold_percent": analysis.thrust.threshold_percent,
                "threshold_thrust_N": analysis.thrust.threshold_thrust_N,
                "burn_start_5pct_time_s": analysis.thrust.burn_start_5pct_time_s,
                "burn_end_5pct_time_s": analysis.thrust.burn_end_5pct_time_s,
                "burn_time_5pct_s": analysis.thrust.burn_time_5pct_s,
                "average_thrust_5pct_N": analysis.thrust.average_thrust_5pct_N,
                "initial_thrust_average_N": analysis.thrust.initial_thrust_average_N,
                "initial_thrust_window_s": analysis.thrust.initial_thrust_window_s,
                "thrust_rise_rate_N_per_s": analysis.thrust.thrust_rise_rate_N_per_s,
                "thrust_decay_rate_N_per_s": analysis.thrust.thrust_decay_rate_N_per_s,
                "isp_s": analysis.thrust.isp_s,
                "isp_status": analysis.thrust.isp_status,
                "cstar_m_per_s": analysis.thrust.cstar_m_per_s,
                "cstar_status": analysis.thrust.cstar_status,
                "average_chamber_pressure_psi": analysis.thrust.average_chamber_pressure_psi,
                "average_mass_flow_kg_per_s": analysis.thrust.average_mass_flow_kg_per_s,
                "total_impulse_valid_curve_Ns": analysis.thrust.total_impulse_valid_curve_Ns,
                "normalized_impulse_Ns": analysis.thrust.normalized_impulse_Ns,
                "impulse_class": analysis.thrust.impulse_class,
                "designation": analysis.thrust.designation,
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
    ):
        """
        Convert JSON data back into AnalysisResults.

        Returns:
            tuple[AnalysisResults, bool]

        The boolean indicates whether the project used the legacy
        EventResults representation and therefore requires migration.
        """

        events_data = data["events"]
        thrust_data = data["thrust"]
        statistics_data = data["statistics"]
        classification_data = data["classification"]

        # ---------------------------------------------------------
        # Events
        # ---------------------------------------------------------

        event_format = events_data.get(
            "format"
        )

        legacy_project = False

        if (
            event_format == "event_set"
            or "events" in events_data
        ):

            events = EventSet.from_dict(
                events_data
            )

        else:

            # -----------------------------------------------------
            # Legacy EventResults
            # -----------------------------------------------------

            legacy_project = True

            legacy_events = EventResults(
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

            events = (
                ProjectFile._legacy_events_to_event_set(
                    legacy_events
                )
            )

        # ---------------------------------------------------------
        # Thrust
        # ---------------------------------------------------------

        thrust = ThrustResults(
            peak_thrust_N=thrust_data.get("peak_thrust_N"),
            peak_thrust_time_s=thrust_data.get("peak_thrust_time_s"),
            average_thrust_N=thrust_data.get("average_thrust_N"),
            burn_time_s=thrust_data.get("burn_time_s"),
            total_impulse_Ns=thrust_data.get("total_impulse_Ns"),
            time_to_peak_s=thrust_data.get("time_to_peak_s"),
            threshold_percent=thrust_data.get("threshold_percent", 5.0),
            threshold_thrust_N=thrust_data.get("threshold_thrust_N"),
            burn_start_5pct_time_s=thrust_data.get("burn_start_5pct_time_s"),
            burn_end_5pct_time_s=thrust_data.get("burn_end_5pct_time_s"),
            burn_time_5pct_s=thrust_data.get("burn_time_5pct_s"),
            average_thrust_5pct_N=thrust_data.get("average_thrust_5pct_N"),
            initial_thrust_average_N=thrust_data.get("initial_thrust_average_N"),
            initial_thrust_window_s=thrust_data.get("initial_thrust_window_s"),
            thrust_rise_rate_N_per_s=thrust_data.get("thrust_rise_rate_N_per_s"),
            thrust_decay_rate_N_per_s=thrust_data.get("thrust_decay_rate_N_per_s"),
            isp_s=thrust_data.get("isp_s"),
            isp_status=thrust_data.get("isp_status", "unavailable"),
            cstar_m_per_s=thrust_data.get("cstar_m_per_s"),
            cstar_status=thrust_data.get("cstar_status", "unavailable"),
            average_chamber_pressure_psi=thrust_data.get("average_chamber_pressure_psi"),
            average_mass_flow_kg_per_s=thrust_data.get("average_mass_flow_kg_per_s"),
            total_impulse_valid_curve_Ns=thrust_data.get("total_impulse_valid_curve_Ns"),
            normalized_impulse_Ns=thrust_data.get("normalized_impulse_Ns"),
            impulse_class=thrust_data.get("impulse_class"),
            designation=thrust_data.get("designation"),
        )

        # ---------------------------------------------------------
        # Statistics
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # Classification
        # ---------------------------------------------------------

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

        analysis = AnalysisResults(
            events=events,
            thrust=thrust,
            statistics=statistics,
            classification=classification,
        )

        return (
            analysis,
            legacy_project,
        )

    @staticmethod
    def _legacy_events_to_event_set(
        events: EventResults,
    ) -> EventSet:
        """Convert legacy EventResults into the current EventSet."""

        event_set = EventSet()

        if events.ignition_time_s is not None:

            event_set.add(
                DetectedEvent(
                    event_type=EventType.IGNITION,
                    time_s=float(
                        events.ignition_time_s
                    ),
                    sample_index=events.ignition_index,
                    label="Ignition",
                    notes=(
                        "Migrated from legacy "
                        "EventResults."
                    ),
                    automatically_detected=True,
                )
            )

        if events.peak_time_s is not None:

            event_set.add(
                DetectedEvent(
                    event_type=EventType.PEAK_THRUST,
                    time_s=float(
                        events.peak_time_s
                    ),
                    sample_index=events.peak_index,
                    label="Peak Thrust",
                    notes=(
                        "Migrated from legacy "
                        "EventResults."
                    ),
                    automatically_detected=True,
                )
            )

        if events.burnout_time_s is not None:

            event_set.add(
                DetectedEvent(
                    event_type=EventType.BURNOUT,
                    time_s=float(
                        events.burnout_time_s
                    ),
                    sample_index=events.burnout_index,
                    label="Burnout",
                    notes=(
                        "Migrated from legacy "
                        "EventResults."
                    ),
                    automatically_detected=True,
                )
            )

        return event_set

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

        if version not in (
            cls.FORMAT_VERSION,
            cls.PRE_VIDEO_FORMAT_VERSION,
            cls.LEGACY_FORMAT_VERSION,
        ):

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