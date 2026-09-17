from .alignment import (
    AlignmentResult,
    AlignmentSettings,
    TimeAligner,
)

from .baseline import (
    BaselineCorrector,
    BaselineResult,
    BaselineSettings,
)

from .cleaning import (
    CleaningResult,
    CleaningSettings,
    DataCleaner,
)

from .event_model import (
    DetectedEvent,
    EventSet,
    EventType,
)

from .settings import (
    ProcessingSettings,
)

from .validation import (
    DataValidationReport,
    DataValidator,
    ValidationIssue,
)


def __getattr__(name):
    """
    Lazily expose pipeline classes.

    ProcessingPipeline imports EventDetector, while EventDetector
    imports processing.event_model. Loading the pipeline eagerly
    from this package initializer would therefore create a circular
    import.
    """

    if name in (
        "ProcessingPipeline",
        "ProcessingResult",
    ):
        from .pipeline import (
            ProcessingPipeline,
            ProcessingResult,
        )

        if name == "ProcessingPipeline":
            return ProcessingPipeline

        return ProcessingResult

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )


__all__ = [
    "AlignmentResult",
    "AlignmentSettings",
    "TimeAligner",
    "BaselineCorrector",
    "BaselineResult",
    "BaselineSettings",
    "CleaningResult",
    "CleaningSettings",
    "DataCleaner",
    "DetectedEvent",
    "EventSet",
    "EventType",
    "ProcessingPipeline",
    "ProcessingResult",
    "ProcessingSettings",
    "DataValidationReport",
    "DataValidator",
    "ValidationIssue",
]