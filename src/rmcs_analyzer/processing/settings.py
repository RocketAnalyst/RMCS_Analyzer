from dataclasses import dataclass, field
from typing import Any

from .baseline import BaselineSettings
from .cleaning import CleaningSettings


@dataclass
class ProcessingSettings:
    """
    Complete set of settings used to prepare a test dataset.

    ProcessingSettings describes how raw data should be transformed
    into prepared data. It does not contain the data itself.

    The settings are intentionally kept separate from TestData so
    they can later be stored in an RMCS project file.
    """

    cleaning: CleaningSettings = field(
        default_factory=CleaningSettings
    )

    baseline: BaselineSettings = field(
        default_factory=BaselineSettings
    )

    def reset(self):
        """Reset all processing settings to their defaults."""
        self.cleaning.reset()
        self.baseline.reset()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert processing settings to a JSON-compatible dictionary.
        """

        return {
            "cleaning": {
                "start_time_s": self.cleaning.start_time_s,
                "end_time_s": self.cleaning.end_time_s,
            },
            "baseline": {
                "baseline_start_time_s": (
                    self.baseline.baseline_start_time_s
                ),
                "baseline_end_time_s": (
                    self.baseline.baseline_end_time_s
                ),
            },
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "ProcessingSettings":
        """
        Create ProcessingSettings from a dictionary.

        Missing sections or fields use their normal defaults.
        """

        cleaning_data = data.get("cleaning", {})
        baseline_data = data.get("baseline", {})

        cleaning = CleaningSettings(
            start_time_s=cleaning_data.get(
                "start_time_s"
            ),
            end_time_s=cleaning_data.get(
                "end_time_s"
            ),
        )

        baseline = BaselineSettings(
            baseline_start_time_s=baseline_data.get(
                "baseline_start_time_s"
            ),
            baseline_end_time_s=baseline_data.get(
                "baseline_end_time_s"
            ),
        )

        return cls(
            cleaning=cleaning,
            baseline=baseline,
        )