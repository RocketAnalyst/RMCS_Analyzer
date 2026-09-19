from dataclasses import dataclass, field
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
    manufacturer: str = ""
    test_date: str = ""
    location: str = ""

    motor_diameter_in: Optional[float] = None
    motor_length_in: Optional[float] = None

    initial_mass_g: Optional[float] = None
    propellant_mass_g: Optional[float] = None

    propellant_type: str = ""

    nozzle_throat_in: Optional[float] = None
    nozzle_exit_in: Optional[float] = None

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

        if not self.test_date:
            self.test_date = (
                metadata.test_date or ""
            )

        if self.motor_diameter_in is None:
            self.motor_diameter_in = (
                metadata.motor_diameter
            )

        if self.motor_length_in is None:
            self.motor_length_in = (
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