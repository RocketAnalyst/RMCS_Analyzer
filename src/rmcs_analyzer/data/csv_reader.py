import csv
import os
from typing import List, Tuple

import numpy as np

from .models import TestData, TestMetadata


class CSVReadError(Exception):
    """Raised when a CSV test file cannot be read."""

    pass


class RMCSCSVReader:
    """
    Reader for RMCS CSV files.

    The reader understands the metadata/header structure used
    by RMCS firmware while keeping the resulting TestData object
    independent of the original file format.
    """

    REQUIRED_COLUMNS = {
        "sample",
        "time_ms",
        "thrust_N",
    }

    def read(self, filename: str) -> TestData:
        """
        Read an RMCS CSV file.

        Parameters
        ----------
        filename:
            Path to the CSV file.

        Returns
        -------
        TestData
            Standardized test data.
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

        header_index = self._find_data_header(
            rows
        )

        if header_index is None:
            raise CSVReadError(
                "Could not find the test-data header row."
            )

        headers = [
            column.strip()
            for column in rows[header_index]
        ]

        header_map = {
            name: index
            for index, name in enumerate(headers)
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

        if not parsed:
            raise CSVReadError(
                "No valid measurement data was found."
            )

        (
            time_s,
            thrust_N,
            raw_hx711,
            delta,
            state,
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
            raw_hx711=self._to_optional_array(
                raw_hx711,
                dtype=float,
            ),
            delta=self._to_optional_array(
                delta,
                dtype=float,
            ),
            state=self._to_optional_string_array(
                state
            ),
            metadata=metadata,
        )

    def _read_metadata(
        self,
        rows: List[List[str]],
        filename: str,
    ) -> TestMetadata:
        """Read known RMCS metadata fields."""

        metadata = TestMetadata(
            source_file=os.path.basename(filename)
        )

        for row in rows:
            if len(row) < 2:
                continue

            key = row[0].strip()
            value = row[1].strip()

            if key == "RMCS Version":
                metadata.rmcs_version = value

            elif key == "Test Number":
                metadata.test_number = (
                    self._parse_int(value)
                )

            elif key == "Calibration Counts Per Newton":
                metadata.calibration_counts_per_newton = (
                    self._parse_float(value)
                )

            elif key == "Tare Raw":
                metadata.tare_raw = (
                    self._parse_int(value)
                )

        return metadata

    def _find_data_header(
        self,
        rows: List[List[str]],
    ) -> int | None:
        """Find the measurement header row."""

        for index, row in enumerate(rows):
            normalized = {
                column.strip()
                for column in row
            }

            if self.REQUIRED_COLUMNS.issubset(
                normalized
            ):
                return index

        return None

    def _parse_data_rows(
        self,
        rows: List[List[str]],
        header_map: dict,
    ) -> Tuple[
        List[float],
        List[float],
        List[float],
        List[float],
        List[str],
    ]:
        """Parse measurement rows."""

        time_s = []
        thrust_N = []
        raw_hx711 = []
        delta = []
        state = []

        for row in rows:
            if not row:
                continue

            try:
                time_ms = self._get_value(
                    row,
                    header_map,
                    "time_ms",
                )

                thrust = self._get_value(
                    row,
                    header_map,
                    "thrust_N",
                )

                if time_ms == "":
                    continue

                if thrust == "":
                    continue

                time_s.append(
                    float(time_ms) / 1000.0
                )

                thrust_N.append(
                    float(thrust)
                )

                raw_hx711.append(
                    self._get_optional_float(
                        row,
                        header_map,
                        "raw_hx711",
                    )
                )

                delta.append(
                    self._get_optional_float(
                        row,
                        header_map,
                        "delta",
                    )
                )

                state.append(
                    self._get_optional_string(
                        row,
                        header_map,
                        "state",
                    )
                )

            except (ValueError, TypeError):
                # Ignore malformed data rows rather than
                # destroying an otherwise valid test file.
                continue

        return (
            time_s,
            thrust_N,
            raw_hx711,
            delta,
            state,
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
    ):
        """Get an optional numeric value."""

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
    def _get_optional_string(
        row: List[str],
        header_map: dict,
        column: str,
    ) -> str:
        """Get an optional string value."""

        if column not in header_map:
            return ""

        return RMCSCSVReader._get_value(
            row,
            header_map,
            column,
        )

    @staticmethod
    def _parse_float(
        value: str,
    ):
        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_int(
        value: str,
    ):
        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _to_optional_array(
        values,
        dtype=float,
    ):
        if not values:
            return None

        return np.asarray(
            values,
            dtype=dtype,
        )

    @staticmethod
    def _to_optional_string_array(
        values,
    ):
        if not values:
            return None

        return np.asarray(
            values,
            dtype=str,
        )