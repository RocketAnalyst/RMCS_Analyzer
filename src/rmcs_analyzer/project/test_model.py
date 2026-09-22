from dataclasses import dataclass, field, replace
from typing import Optional

from ..analysis.results import AnalysisResults
from ..data.models import TestData

from .video_state import VideoState


@dataclass
class TestModel:
    """
    Represents one complete test within an RMCS Analyzer project.

    A TestModel keeps the imported test data together with its
    analysis results and user-editable metadata.

    The filename is deliberately kept separate from the test number.
    """

    # =============================================================
    # CORE DATA
    # =============================================================

    data: TestData

    # =============================================================
    # USER-EDITABLE TEST INFORMATION
    # =============================================================

    test_number: str = ""

    motor_designation: str = ""
    motor_type: str = ""
    manufacturer: str = ""
    builder: str = ""
    case_material: str = ""
    test_date: str = ""
    test_stand: str = ""
    test_operator: str = ""
    location: str = ""

    motor_diameter_mm: Optional[float] = None
    motor_length_mm: Optional[float] = None

    initial_mass_g: Optional[float] = None
    propellant_mass_g: Optional[float] = None

    propellant_type: str = ""

    nozzle_throat_in: Optional[float] = None
    nozzle_exit_in: Optional[float] = None
    nozzle_material: str = ""

    load_cell: str = ""
    load_cell_calibration: str = ""
    pressure_sensor: str = ""
    pressure_sensor_calibration: str = ""
    sample_rate_hz: Optional[float] = None
    case_pressure_limit_psi: Optional[float] = None

    notes: str = ""

    # =============================================================
    # ANALYSIS
    # =============================================================

    analysis_results: Optional[AnalysisResults] = None

    # =============================================================
    # VIDEO / OVERLAY
    # =============================================================

    video: VideoState = field(default_factory=VideoState)

    # =============================================================
    # FILE INFORMATION
    # =============================================================

    source_file: str = ""

    # =============================================================
    # PROJECT STATE
    # =============================================================

    modified: bool = False

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __post_init__(self):
        """
        Initialize file information and import metadata when available.

        Imported metadata is used only as an initial value. The
        user-editable fields remain independent of the filename.
        """

        if not self.source_file:
            self.source_file = self.data.metadata.source_file

        self._load_metadata_defaults()

    # =============================================================
    # METADATA
    # =============================================================

    def _load_metadata_defaults(self):
        """
        Populate empty fields from imported RMCS metadata.

        Existing user values are never overwritten.
        """

        metadata = self.data.metadata

        if not self.test_number and metadata.test_number is not None:
            self.test_number = str(
                metadata.test_number
            )

        if not self.motor_designation:
            self.motor_designation = (
                metadata.motor_designation or ""
            )

        if not self.motor_type:
            self.motor_type = metadata.motor_type or ""

        if not self.manufacturer:
            self.manufacturer = metadata.manufacturer or ""

        if not self.builder:
            self.builder = metadata.builder or ""

        if not self.case_material:
            self.case_material = metadata.case_material or ""

        if not self.test_date:
            self.test_date = metadata.test_date or ""

        if not self.test_stand:
            self.test_stand = metadata.test_stand or ""

        if not self.test_operator:
            self.test_operator = metadata.test_operator or ""

        if not self.location:
            self.location = metadata.location or ""

        if self.motor_diameter_mm is None:
            self.motor_diameter_mm = (
                metadata.motor_diameter
            )

        if self.motor_length_mm is None:
            self.motor_length_mm = (
                metadata.motor_length
            )

        if self.initial_mass_g is None:
            self.initial_mass_g = (
                metadata.initial_mass
            )

        if self.propellant_mass_g is None:
            self.propellant_mass_g = (
                metadata.propellant_mass
            )

        if not self.propellant_type:
            self.propellant_type = metadata.propellant_type or ""

        if self.nozzle_throat_in is None:
            self.nozzle_throat_in = metadata.nozzle_throat

        if self.nozzle_exit_in is None:
            self.nozzle_exit_in = metadata.nozzle_exit

        if not self.nozzle_material:
            self.nozzle_material = metadata.nozzle_material or ""

        if not self.load_cell:
            self.load_cell = metadata.load_cell or ""

        if not self.load_cell_calibration:
            self.load_cell_calibration = metadata.load_cell_calibration or ""

        if not self.pressure_sensor:
            self.pressure_sensor = metadata.pressure_sensor or ""

        if not self.pressure_sensor_calibration:
            self.pressure_sensor_calibration = metadata.pressure_sensor_calibration or ""

        if self.sample_rate_hz is None:
            self.sample_rate_hz = metadata.sample_rate_hz

        if self.case_pressure_limit_psi is None:
            self.case_pressure_limit_psi = metadata.case_pressure_limit_psi



    def reset_metadata_to_source(self):
        """Restore all editable metadata fields from the imported CSV metadata."""
        metadata = self.data.metadata

        self.test_number = (
            str(metadata.test_number)
            if metadata.test_number is not None
            else ""
        )
        self.motor_designation = metadata.motor_designation or ""
        self.motor_type = metadata.motor_type or ""
        self.manufacturer = metadata.manufacturer or ""
        self.builder = metadata.builder or ""
        self.case_material = metadata.case_material or ""
        self.test_date = metadata.test_date or ""
        self.test_stand = metadata.test_stand or ""
        self.test_operator = metadata.test_operator or ""
        self.location = metadata.location or ""
        self.motor_diameter_mm = metadata.motor_diameter
        self.motor_length_mm = metadata.motor_length
        self.initial_mass_g = metadata.initial_mass
        self.propellant_mass_g = metadata.propellant_mass
        self.propellant_type = metadata.propellant_type or ""
        self.nozzle_throat_in = metadata.nozzle_throat
        self.nozzle_exit_in = metadata.nozzle_exit
        self.nozzle_material = metadata.nozzle_material or ""
        self.load_cell = metadata.load_cell or ""
        self.load_cell_calibration = metadata.load_cell_calibration or ""
        self.pressure_sensor = metadata.pressure_sensor or ""
        self.pressure_sensor_calibration = metadata.pressure_sensor_calibration or ""
        self.sample_rate_hz = metadata.sample_rate_hz
        self.case_pressure_limit_psi = metadata.case_pressure_limit_psi
        self.notes = metadata.notes or ""

    def analysis_data(self) -> TestData:
        """
        Return a prepared-data-compatible TestData view using the current
        project metadata overrides. Raw measurement arrays are untouched.
        """
        metadata = replace(
            self.data.metadata,
            test_number=self._parse_test_number(),
            motor_designation=self.motor_designation,
            motor_type=self.motor_type,
            manufacturer=self.manufacturer,
            builder=self.builder,
            case_material=self.case_material,
            test_date=self.test_date,
            test_stand=self.test_stand,
            test_operator=self.test_operator,
            location=self.location,
            motor_diameter=self.motor_diameter_mm,
            motor_length=self.motor_length_mm,
            initial_mass=self.initial_mass_g,
            propellant_mass=self.propellant_mass_g,
            propellant_type=self.propellant_type,
            nozzle_throat=self.nozzle_throat_in,
            nozzle_exit=self.nozzle_exit_in,
            nozzle_material=self.nozzle_material,
            load_cell=self.load_cell,
            load_cell_calibration=self.load_cell_calibration,
            pressure_sensor=self.pressure_sensor,
            pressure_sensor_calibration=self.pressure_sensor_calibration,
            sample_rate_hz=self.sample_rate_hz,
            case_pressure_limit_psi=self.case_pressure_limit_psi,
            notes=self.notes,
        )

        return replace(
            self.data,
            metadata=metadata,
        )

    def _parse_test_number(self):
        value = str(self.test_number).strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return self.data.metadata.test_number

    # =============================================================
    # DISPLAY HELPERS
    # =============================================================

    @property
    def filename(self) -> str:
        """
        Return only the filename portion of the source path.
        """

        if not self.source_file:
            return ""

        return self.source_file.replace(
            "\\",
            "/",
        ).split("/")[-1]

    @property
    def display_name(self) -> str:
        """
        Return the name displayed in the test list.
        """

        if self.filename:
            return self.filename

        if self.test_number:
            return f"Test {self.test_number}"

        return "Unnamed Test"

    # =============================================================
    # MODIFICATION TRACKING
    # =============================================================

    def mark_modified(self):
        """
        Mark the test as having unsaved changes.
        """

        self.modified = True

    def mark_saved(self):
        """
        Mark the test as synchronized with its saved state.
        """

        self.modified = False