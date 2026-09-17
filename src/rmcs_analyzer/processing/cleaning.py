from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..data.models import TestData


# =============================================================
# CLEANING SETTINGS
# =============================================================


@dataclass
class CleaningSettings:
    """
    Defines non-destructive preparation settings for a test.

    None means that no boundary has been specified.

    Times are always expressed in seconds using the normalized
    TestData time base.
    """

    start_time_s: Optional[float] = None
    end_time_s: Optional[float] = None

    def reset(self):
        """Reset all cleaning boundaries."""

        self.start_time_s = None
        self.end_time_s = None


# =============================================================
# CLEANING RESULT
# =============================================================


@dataclass
class CleaningResult:
    """
    Result of applying CleaningSettings to a TestData object.

    The original TestData is never modified.
    """

    data: TestData

    start_index: int
    end_index: int

    original_sample_count: int
    prepared_sample_count: int


# =============================================================
# DATA CLEANER
# =============================================================


class DataCleaner:
    """
    Applies non-destructive cleaning operations to TestData.

    The first supported operation is time-based trimming.

    Raw TestData is never modified. The cleaner produces a new
    TestData object containing the selected analysis region.
    """

    # =========================================================
    # PUBLIC API
    # =========================================================

    @classmethod
    def prepare(
        cls,
        test_data: TestData,
        settings: CleaningSettings,
    ) -> CleaningResult:
        """
        Apply cleaning settings to a TestData object.

        Parameters
        ----------
        test_data:
            Original normalized test data.

        settings:
            Cleaning settings describing the desired
            analysis region.

        Returns
        -------
        CleaningResult
            Prepared data and information about the selected
            sample range.

        Notes
        -----
        The original TestData object and all of its arrays
        remain unchanged.
        """

        if test_data is None:
            raise ValueError(
                "Test data cannot be None."
            )

        if settings is None:
            settings = CleaningSettings()

        time_s = np.asarray(
            test_data.time_s
        )

        if len(time_s) == 0:
            raise ValueError(
                "Cannot prepare an empty dataset."
            )

        start_index = cls._find_start_index(
            time_s,
            settings.start_time_s,
        )

        end_index = cls._find_end_index(
            time_s,
            settings.end_time_s,
        )

        if start_index > end_index:
            raise ValueError(
                "Cleaning start time must occur before "
                "the cleaning end time."
            )

        prepared_data = cls._slice_test_data(
            test_data,
            start_index,
            end_index,
        )

        return CleaningResult(
            data=prepared_data,
            start_index=start_index,
            end_index=end_index,
            original_sample_count=len(time_s),
            prepared_sample_count=(
                len(prepared_data.time_s)
            ),
        )

    # =========================================================
    # START BOUNDARY
    # =========================================================

    @staticmethod
    def _find_start_index(
        time_s: np.ndarray,
        start_time_s: Optional[float],
    ) -> int:
        """
        Find the first sample at or after the requested
        start time.

        If no start time is supplied, use the first sample.
        """

        if start_time_s is None:
            return 0

        start_time_s = float(
            start_time_s
        )

        if not np.isfinite(
            start_time_s
        ):
            raise ValueError(
                "Cleaning start time must be finite."
            )

        return int(
            np.searchsorted(
                time_s,
                start_time_s,
                side="left",
            )
        )

    # =========================================================
    # END BOUNDARY
    # =========================================================

    @staticmethod
    def _find_end_index(
        time_s: np.ndarray,
        end_time_s: Optional[float],
    ) -> int:
        """
        Find the last sample at or before the requested
        end time.

        If no end time is supplied, use the final sample.
        """

        if end_time_s is None:
            return len(time_s) - 1

        end_time_s = float(
            end_time_s
        )

        if not np.isfinite(
            end_time_s
        ):
            raise ValueError(
                "Cleaning end time must be finite."
            )

        return int(
            np.searchsorted(
                time_s,
                end_time_s,
                side="right",
            )
            - 1
        )

    # =========================================================
    # DATA SLICING
    # =========================================================

    @staticmethod
    def _slice_test_data(
        test_data: TestData,
        start_index: int,
        end_index: int,
    ) -> TestData:
        """
        Create a new TestData object containing the selected
        sample range.

        The slice is inclusive of both boundaries.
        """

        data_slice = slice(
            start_index,
            end_index + 1,
        )

        return TestData(
            time_s=np.array(
                test_data.time_s[
                    data_slice
                ],
                copy=True,
            ),

            thrust_N=np.array(
                test_data.thrust_N[
                    data_slice
                ],
                copy=True,
            ),

            raw_hx711=(
                None
                if test_data.raw_hx711 is None
                else np.array(
                    test_data.raw_hx711[
                        data_slice
                    ],
                    copy=True,
                )
            ),

            delta=(
                None
                if test_data.delta is None
                else np.array(
                    test_data.delta[
                        data_slice
                    ],
                    copy=True,
                )
            ),

            state=(
                None
                if test_data.state is None
                else np.array(
                    test_data.state[
                        data_slice
                    ],
                    copy=True,
                )
            ),

            pressure_kPa=(
                None
                if test_data.pressure_kPa is None
                else np.array(
                    test_data.pressure_kPa[
                        data_slice
                    ],
                    copy=True,
                )
            ),

            metadata=test_data.metadata,
        )