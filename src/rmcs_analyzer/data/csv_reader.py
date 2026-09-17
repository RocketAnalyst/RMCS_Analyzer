import csv
import os
from typing import List, Optional, Tuple

import numpy as np

from .models import TestData, TestMetadata


class CSVReadError(Exception):
    """Raised when a CSV test file cannot be read."""

    pass


class RMCSCSVReader:
    """
    Reader for RMCS Analyzer CSV Format 1.0.

    The file contains:
        1. A two-column metadata section.
        2. A measurement-data header.
        3. Time-series measurement data.

    Required measurement columns:
        Sample
        Time(s)
        Thrust (N)

    Optional measurement columns:
        Time Cal (s)
        Raw Thrust (N)
        Prop Loss (kg)
        Pressure (psi)

    The reader does not perform processing, baseline correction,
    event detection, or time alignment. It only converts the CSV
    into the application's TestData/TestMetadata models.
    """

    FORMAT_VERSION = "1.0"

    REQUIRED_COLUMNS = {
        "Sample",
        "Time(s)",
        "Thrust (N)",
    }

    OPTIONAL_COLUMNS = {
        "Time Cal (s)",
        "Raw Thrust (N)",
        "Prop Loss (kg)",
        "Pressure (psi)",
    }

    def read(self, filename: str) -> TestData:
        """
        Read an RMCS Analyzer CSV Format 1.0 file.

        Parameters
        ----------
        filename:
            Path to the CSV file.

        Returns
        -------
        TestData
            Parsed test data and metadata.

        Raises
        ------
        CSVReadError
            If the file cannot be read or required data is missing.
        """

        if not os.path.isfile(filename):
            raise CSVReadError(
                f"File does not exist:\n{filename}"
            )

        try:
            with open(
                filename,
                "r",
                newline="",
                encoding="utf-8-sig",
            ) as file:
                rows = list(csv.reader(file))
        except OSError as exc:
            raise CSVReadError(
                f"Unable to open file:\n{exc}"
            ) from exc

        if not rows:
            raise CSVReadError(
                "The CSV file is empty."
            )

        metadata = self._read_metadata(
            rows,
            filename,
        )

        header_index = self._find_data_header(rows)

        if header_index is None:
            raise CSVReadError(
                "Could not find the RMCS Analyzer measurement "
                "header row."
            )

        headers = [
            column.strip()
            for column in rows[header_index]
        ]

        header_map = {
            name: index
            for index, name in enumerate(headers)
            if name
        }

        missing = (
            self.REQUIRED_COLUMNS
            - set(header_map.keys())
        )

        if missing:
            missing_text = ", ".join(
                sorted(missing)
            )

            raise CSVReadError(
                "Required columns are missing:\n"
                f"{missing_text}"
            )

        data_rows = rows[
            header_index + 1 :
        ]

        parsed = self._parse_data_rows(
            data_rows,
            header_map,
        )

        if parsed is None:
            raise CSVReadError(
                "No valid measurement data was found."
            )

        (
            time_s,
            calibrated_time_s,
            thrust_N,
            raw_thrust_N,
            prop_loss_kg,
            pressure_psi,
        ) = parsed

        return TestData(
            time_s=np.asarray(
                time_s,
                dtype=float,
            ),
            thrust_N=np.asarray(
                thrust_N,
                dtype=float,
            ),
            calibrated_time_s=self._to_optional_array(
                calibrated_time_s
            ),
            raw_thrust_N=self._to_optional_array(
                raw_thrust_N
            ),
            prop_loss_kg=self._to_optional_array(
                prop_loss_kg
            ),
            pressure_psi=self._to_optional_array(
                pressure_psi
            ),
            metadata=metadata,
        )

    def _read_metadata(
        self,
        rows: List[List[str]],
        filename: str,
    ) -> TestMetadata:
        """
        Read the standardized metadata section.

        Unknown metadata fields are ignored so that the format
        can be extended in the future without breaking the reader.
        """

        metadata = TestMetadata(
            source_file=os.path.basename(filename)
        )

        for row in rows:
            if len(row) < 2:
                continue

            key = row[0].strip()
            value = row[1].strip()

            if not key:
                continue

            if key == "Format Version":
                metadata.rmcs_version = value

            elif key == "Test Number":
                metadata.test_number = self._parse_int(value)

            elif key == "Test Date":
                metadata.test_date = value

            elif key == "Test Stand":
                metadata.test_stand = value

            elif key == "Test Operator":
                metadata.test_operator = value

            elif key == "Location":
                metadata.location = value

            elif key == "Notes":
                metadata.notes = value

            elif key == "Motor Designation":
                metadata.motor_designation = value

            elif key == "Motor Type":
                metadata.motor_type = value

            elif key == "Manufacturer":
                metadata.manufacturer = value

            elif key == "Builder":
                metadata.builder = value

            elif key == "Case Material":
                metadata.case_material = value

            elif key == "Motor Diameter (in)":
                metadata.motor_diameter = self._parse_float(value)

            elif key == "Motor Length (in)":
                metadata.motor_length = self._parse_float(value)

            elif key == "Initial Mass (g)":
                metadata.initial_mass = self._parse_float(value)

            elif key == "Propellant Mass (g)":
                metadata.propellant_mass = self._parse_float(value)

            elif key == "Propellant Type":
                metadata.propellant_type = value

            elif key == "Nozzle Throat Diameter (in)":
                metadata.nozzle_throat = self._parse_float(value)

            elif key == "Nozzle Exit Diameter (in)":
                metadata.nozzle_exit = self._parse_float(value)

            elif key == "Nozzle Material":
                metadata.nozzle_material = value

            elif key == "Load Cell":
                metadata.load_cell = value

            elif key == "Load Cell Calibration":
                metadata.load_cell_calibration = value

            elif key == "Pressure Sensor":
                metadata.pressure_sensor = value

            elif key == "Pressure Sensor Calibration":
                metadata.pressure_sensor_calibration = value

            elif key == "Sample Rate (Hz)":
                metadata.sample_rate_hz = self._parse_float(value)

            # Legacy RMCS metadata is still recognized.
            elif key == "RMCS Version":
                metadata.rmcs_version = value

            elif key == "Calibration Counts Per Newton":
                metadata.calibration_counts_per_newton = (
                    self._parse_float(value)
                )

            elif key == "Tare Raw":
                metadata.tare_raw = self._parse_int(value)

        return metadata

    def _find_data_header(
        self,
        rows: List[List[str]],
    ) -> Optional[int]:
        """
        Find the standardized measurement header row.

        Blank rows and metadata rows are ignored.
        """

        for index, row in enumerate(rows):
            normalized = {
                column.strip()
                for column in row
                if column.strip()
            }

            if self.REQUIRED_COLUMNS.issubset(normalized):
                return index

        return None

    def _parse_data_rows(
        self,
        rows: List[List[str]],
        header_map: dict,
    ) -> Optional[
        Tuple[
            List[float],
            List[float],
            List[float],
            List[float],
            List[float],
            List[float],
        ]
    ]:
        """
        Parse measurement rows.

        Optional numeric columns are represented internally by
        NaN values when the column exists but a particular row
        contains no value.

        If an optional column is completely absent, the returned
        list remains empty and is converted to None.
        """

        time_s = []
        calibrated_time_s = []
        thrust_N = []
        raw_thrust_N = []
        prop_loss_kg = []
        pressure_psi = []

        for row in rows:
            if not row:
                continue

            try:
                sample = self._get_value(
                    row,
                    header_map,
                    "Sample",
                )

                time_value = self._get_value(
                    row,
                    header_map,
                    "Time(s)",
                )

                thrust_value = self._get_value(
                    row,
                    header_map,
                    "Thrust (N)",
                )

                # Ignore completely blank rows.
                if (
                    sample == ""
                    and time_value == ""
                    and thrust_value == ""
                ):
                    continue

                # Required values must be present.
                if time_value == "":
                    continue

                if thrust_value == "":
                    continue

                # Validate sample number if present.
                if sample != "":
                    float(sample)

                time_s.append(
                    float(time_value)
                )

                thrust_N.append(
                    float(thrust_value)
                )

                calibrated_time_s.append(
                    self._get_optional_float(
                        row,
                        header_map,
                        "Time Cal (s)",
                    )
                )

                raw_thrust_N.append(
                    self._get_optional_float(
                        row,
                        header_map,
                        "Raw Thrust (N)",
                    )
                )

                prop_loss_kg.append(
                    self._get_optional_float(
                        row,
                        header_map,
                        "Prop Loss (kg)",
                    )
                )

                pressure_psi.append(
                    self._get_optional_float(
                        row,
                        header_map,
                        "Pressure (psi)",
                    )
                )

            except (ValueError, TypeError):
                # Ignore malformed measurement rows rather than
                # destroying an otherwise usable test file.
                continue

        if not time_s:
            return None

        return (
            time_s,
            calibrated_time_s,
            thrust_N,
            raw_thrust_N,
            prop_loss_kg,
            pressure_psi,
        )

    @staticmethod
    def _get_value(
        row: List[str],
        header_map: dict,
        column: str,
    ) -> str:
        """Get a required column value."""

        index = header_map[column]

        if index >= len(row):
            return ""

        return row[index].strip()

    @staticmethod
    def _get_optional_float(
        row: List[str],
        header_map: dict,
        column: str,
    ) -> float:
        """
        Get an optional numeric value.

        Returns NaN when the column is missing or the cell is blank.
        """

        if column not in header_map:
            return np.nan

        value = RMCSCSVReader._get_value(
            row,
            header_map,
            column,
        )

        if value == "":
            return np.nan

        return float(value)

    @staticmethod
    def _parse_float(
        value: str,
    ) -> Optional[float]:
        """Parse an optional floating-point metadata value."""

        if value == "":
            return None

        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_int(
        value: str,
    ) -> Optional[int]:
        """Parse an optional integer metadata value."""

        if value == "":
            return None

        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _to_optional_array(
        values: List[float],
    ) -> Optional[np.ndarray]:
        """
        Convert an optional data column to a NumPy array.

        A completely absent column is represented by None.
        A present column containing blank cells remains an array
        containing NaN values.
        """

        if not values:
            return None

        # If every value is NaN, the column technically exists but
        # contains no usable data. Treat it as absent for analysis.
        array = np.asarray(
            values,
            dtype=float,
        )

        if np.all(np.isnan(array)):
            return None

        return array