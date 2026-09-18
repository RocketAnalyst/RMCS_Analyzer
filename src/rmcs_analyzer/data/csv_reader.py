import csv
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from .models import TestData, TestMetadata


class CSVReadError(Exception):
    """Raised when an RMCS Analyzer CSV cannot be read safely."""


class RMCSCSVReader:
    """
    Read standardized RMCS Analyzer CSV files.

    Format 1.0 supports a required minimum of:

        Sample
        Time(s)

    plus at least one thrust channel:

        Thrust (N)       preferred/calibrated thrust
        Raw Thrust (N)   fallback thrust

    Analysis-channel selection is deliberately handled here at the
    source-normalization boundary:

        Time:
            Time Cal (s) -> Time(s)

        Thrust:
            Thrust (N) -> Raw Thrust (N)

    The original source channels are still preserved separately on
    TestData whenever they are present.

    Optional channels are never required for analysis.
    """

    FORMAT_VERSION = "1.0"

    REQUIRED_COLUMNS = (
        "Sample",
        "Time(s)",
    )

    OPTIONAL_COLUMNS = (
        "Time Cal (s)",
        "Raw Thrust (N)",
        "Prop Loss (kg)",
        "Pressure (psi)",
    )

    # Metadata keys used by Format 1.0.
    METADATA_FIELDS = {
        "Format Version": ("format_version", str),
        "Test Number": ("test_number", int),
        "Test Date": ("test_date", str),
        "Test Stand": ("test_stand", str),
        "Test Operator": ("test_operator", str),
        "Location": ("location", str),
        "Notes": ("notes", str),
        "Motor Designation": ("motor_designation", str),
        "Motor Type": ("motor_type", str),
        "Manufacturer": ("manufacturer", str),
        "Builder": ("builder", str),
        "Case Material": ("case_material", str),
        "Motor Diameter (in)": ("motor_diameter", float),
        "Motor Length (in)": ("motor_length", float),
        "Initial Mass (g)": ("initial_mass", float),
        "Propellant Mass (g)": ("propellant_mass", float),
        "Propellant Type": ("propellant_type", str),
        "Nozzle Throat Diameter (in)": ("nozzle_throat", float),
        "Nozzle Exit Diameter (in)": ("nozzle_exit", float),
        "Nozzle Material": ("nozzle_material", str),
        "Load Cell": ("load_cell", str),
        "Load Cell Calibration": ("load_cell_calibration", str),
        "Pressure Sensor": ("pressure_sensor", str),
        "Pressure Sensor Calibration": (
            "pressure_sensor_calibration",
            str,
        ),
        "Sample Rate (Hz)": ("sample_rate_hz", float),
    }

    # Legacy metadata names retained for compatibility with older
    # standardized drafts.
    LEGACY_METADATA_FIELDS = {
        "RMCS Version": ("rmcs_version", str),
        "Calibration Counts Per Newton": (
            "calibration_counts_per_newton",
            float,
        ),
        "Tare Raw": ("tare_raw", int),
    }

    def read(self, filename) -> TestData:
        """Read and normalize one RMCS Analyzer CSV file."""

        path = Path(filename)

        if not path.exists():
            raise CSVReadError(
                f"CSV file does not exist:\n{path}"
            )

        if not path.is_file():
            raise CSVReadError(
                f"CSV path is not a file:\n{path}"
            )

        try:
            with path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as handle:
                rows = list(
                    csv.reader(handle)
                )
        except OSError as error:
            raise CSVReadError(
                f"Unable to read CSV file:\n{error}"
            ) from error
        except csv.Error as error:
            raise CSVReadError(
                f"Unable to parse CSV file:\n{error}"
            ) from error

        if not rows:
            raise CSVReadError(
                "The CSV file is empty."
            )

        metadata = self._read_metadata(rows)
        metadata.source_file = str(path)

        data_header_index = self._find_data_header(rows)

        if data_header_index is None:
            raise CSVReadError(
                "No measurement header was found."
            )

        header = self._normalize_header(
            rows[data_header_index]
        )

        missing_required = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in header
        ]

        if missing_required:
            raise CSVReadError(
                "The CSV file is missing required "
                f"measurement column(s): "
                f"{', '.join(missing_required)}"
            )

        column_indices = {
            name: index
            for index, name in enumerate(header)
            if name
        }

        # A test must have either calibrated/authoritative thrust or
        # raw thrust available.  Thrust(N) remains preferred.
        has_thrust_column = (
            "Thrust (N)" in column_indices
        )

        has_raw_thrust_column = (
            "Raw Thrust (N)" in column_indices
        )

        if not has_thrust_column and not has_raw_thrust_column:
            raise CSVReadError(
                "No thrust measurement was found. "
                "The file must contain either "
                "'Thrust (N)' or 'Raw Thrust (N)'."
            )

        (
            sample_numbers,
            time_s,
            calibrated_time_s,
            raw_thrust_N,
            prop_loss_kg,
            thrust_N,
            pressure_psi,
        ) = self._parse_data_rows(
            rows[
                data_header_index + 1 :
            ],
            column_indices,
        )

        if len(sample_numbers) == 0:
            raise CSVReadError(
                "No valid measurement data was found."
            )

        if len(time_s) != len(thrust_N):
            raise CSVReadError(
                "Time and thrust channels contain "
                "different numbers of valid samples."
            )

        return TestData(
            time_s=time_s,
            thrust_N=thrust_N,
            calibrated_time_s=calibrated_time_s,
            raw_thrust_N=raw_thrust_N,
            prop_loss_kg=prop_loss_kg,
            pressure_psi=pressure_psi,
            metadata=metadata,
        )

    # =========================================================
    # METADATA
    # =========================================================

    def _read_metadata(
        self,
        rows: List[List[str]],
    ) -> TestMetadata:
        """Read Format 1.0 metadata rows before the data header."""

        values: Dict[str, str] = {}

        for row in rows:
            if not row:
                continue

            key = self._normalize_metadata_key(
                row[0]
            )

            if not key:
                continue

            # Stop once the measurement table begins.
            if self._normalize_column_name(key) == "Sample":
                break

            if len(row) < 2:
                value = ""
            else:
                value = row[1].strip()

            if key in self.METADATA_FIELDS:
                if key == "Format Version" and value == "1":
                    value = "1.0"
                values[key] = value

            elif key in self.LEGACY_METADATA_FIELDS:
                values[key] = value

        metadata = TestMetadata()

        # The source filename is filled by the caller-independent
        # reader once the object exists.
        self._assign_metadata_values(
            metadata,
            values,
        )

        return metadata

    def _assign_metadata_values(
        self,
        metadata: TestMetadata,
        values: Dict[str, str],
    ):
        """Convert metadata strings into TestMetadata fields."""

        for key, value in values.items():

            field_info = (
                self.METADATA_FIELDS.get(key)
                or self.LEGACY_METADATA_FIELDS.get(key)
            )

            if field_info is None:
                continue

            attribute_name, value_type = field_info

            if value == "":
                converted = None if value_type is not str else ""
            else:
                try:
                    converted = self._convert_metadata_value(
                        value,
                        value_type,
                    )
                except ValueError:
                    # Metadata that cannot be converted should not
                    # prevent otherwise valid test data from loading.
                    converted = None if value_type is not str else value

            if hasattr(metadata, attribute_name):
                setattr(
                    metadata,
                    attribute_name,
                    converted,
                )

    @staticmethod
    def _convert_metadata_value(
        value: str,
        value_type,
    ):
        if value_type is str:
            return value.strip()

        if value_type is int:
            return int(float(value))

        if value_type is float:
            return float(value)

        return value

    # =========================================================
    # DATA HEADER
    # =========================================================

    def _find_data_header(
        self,
        rows: List[List[str]],
    ) -> Optional[int]:
        """
        Locate the standardized measurement header.

        The reader intentionally recognizes a header by its required
        columns rather than relying on a fixed metadata row count.
        """

        for index, row in enumerate(rows):

            normalized = self._normalize_header(
                row
            )

            if (
                "Sample" in normalized
                and "Time(s)" in normalized
            ):
                return index

        return None

    # =========================================================
    # DATA ROWS
    # =========================================================

    def _parse_data_rows(
        self,
        rows: List[List[str]],
        column_indices: Dict[str, int],
    ):
        """Parse measurement rows and select the analysis thrust."""

        sample_values = []
        time_values = []
        calibrated_time_values = []
        raw_thrust_values = []
        prop_loss_values = []
        thrust_values = []
        pressure_values = []

        has_calibrated_time = (
            "Time Cal (s)" in column_indices
        )

        has_raw_thrust = (
            "Raw Thrust (N)" in column_indices
        )

        has_prop_loss = (
            "Prop Loss (kg)" in column_indices
        )

        has_pressure = (
            "Pressure (psi)" in column_indices
        )

        has_calibrated_thrust = (
            "Thrust (N)" in column_indices
        )

        for row in rows:

            if not row:
                continue

            # Ignore completely blank rows.
            if not any(
                cell.strip()
                for cell in row
            ):
                continue

            sample_text = self._cell(
                row,
                column_indices.get("Sample"),
            )

            time_text = self._cell(
                row,
                column_indices.get("Time(s)"),
            )

            # A row without sample/time is not a measurement row.
            if sample_text == "" or time_text == "":
                continue

            try:
                sample = int(
                    float(sample_text)
                )
                time_value = float(
                    time_text
                )
            except ValueError:
                # Ignore non-data rows following the measurement
                # header rather than turning them into samples.
                continue

            calibrated_time = (
                self._optional_float(
                    self._cell(
                        row,
                        column_indices.get(
                            "Time Cal (s)"
                        ),
                    )
                )
                if has_calibrated_time
                else None
            )

            raw_thrust = (
                self._optional_float(
                    self._cell(
                        row,
                        column_indices.get(
                            "Raw Thrust (N)"
                        ),
                    )
                )
                if has_raw_thrust
                else None
            )

            prop_loss = (
                self._optional_float(
                    self._cell(
                        row,
                        column_indices.get(
                            "Prop Loss (kg)"
                        ),
                    )
                )
                if has_prop_loss
                else None
            )

            pressure = (
                self._optional_float(
                    self._cell(
                        row,
                        column_indices.get(
                            "Pressure (psi)"
                        ),
                    )
                )
                if has_pressure
                else None
            )

            calibrated_thrust = (
                self._optional_float(
                    self._cell(
                        row,
                        column_indices.get(
                            "Thrust (N)"
                        ),
                    )
                )
                if has_calibrated_thrust
                else None
            )

            # -----------------------------------------------------
            # Thrust selection hierarchy
            #
            # 1. Thrust (N), when present and numeric.
            # 2. Raw Thrust (N), when calibrated thrust is absent
            #    or blank for this sample.
            #
            # This does NOT calculate thrust from propellant loss.
            # -----------------------------------------------------

            if calibrated_thrust is not None:
                analysis_thrust = calibrated_thrust
            elif raw_thrust is not None:
                analysis_thrust = raw_thrust
            else:
                # This sample has no usable thrust measurement.
                continue

            sample_values.append(sample)
            time_values.append(time_value)
            thrust_values.append(analysis_thrust)

            calibrated_time_values.append(
                calibrated_time
            )
            raw_thrust_values.append(
                raw_thrust
            )
            prop_loss_values.append(
                prop_loss
            )
            pressure_values.append(
                pressure
            )

        if not time_values:
            return (
                np.array([], dtype=int),
                np.array([], dtype=float),
                None,
                None,
                None,
                np.array([], dtype=float),
                None,
            )

        calibrated_time_array = (
            self._to_optional_array(
                calibrated_time_values
            )
        )

        raw_thrust_array = (
            self._to_optional_array(
                raw_thrust_values
            )
        )

        prop_loss_array = (
            self._to_optional_array(
                prop_loss_values
            )
        )

        pressure_array = (
            self._to_optional_array(
                pressure_values
            )
        )

        return (
            np.asarray(
                sample_values,
                dtype=int,
            ),
            np.asarray(
                time_values,
                dtype=float,
            ),
            calibrated_time_array,
            raw_thrust_array,
            prop_loss_array,
            np.asarray(
                thrust_values,
                dtype=float,
            ),
            pressure_array,
        )

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _cell(
        row: List[str],
        index: Optional[int],
    ) -> str:
        if index is None:
            return ""

        if index < 0 or index >= len(row):
            return ""

        return row[index].strip()

    @staticmethod
    def _optional_float(
        value: str,
    ) -> Optional[float]:
        if value == "":
            return None

        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def _to_optional_array(
        values: List[Optional[float]],
    ) -> Optional[np.ndarray]:
        """
        Convert an optional channel to an array.

        A channel is considered absent when every sample is blank or
        otherwise unusable. If the channel exists but has missing
        values, NaN is retained so validation can report the issue.
        """

        if not values:
            return None

        if not any(
            value is not None
            for value in values
        ):
            return None

        return np.asarray(
            [
                np.nan
                if value is None
                else float(value)
                for value in values
            ],
            dtype=float,
        )

    @staticmethod
    def _normalize_column_name(
        value: str,
    ) -> str:
        """
        Normalize harmless formatting differences in column names.

        For example:
            'Thrust  (N)' -> 'Thrust (N)'
            ' Time(s) '   -> 'Time(s)'
        """

        return " ".join(
            value.strip().split()
        )

    @classmethod
    def _normalize_header(
        cls,
        row: List[str],
    ) -> List[str]:
        return [
            cls._normalize_column_name(
                cell
            )
            for cell in row
        ]

    @staticmethod
    def _normalize_metadata_key(
        value: str,
    ) -> str:
        key = value.strip()

        # Accept older drafts that placed a colon after the key.
        if key.endswith(":"):
            key = key[:-1].rstrip()

        return key