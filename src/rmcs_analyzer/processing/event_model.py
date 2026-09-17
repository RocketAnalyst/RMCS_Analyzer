from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EventType(str, Enum):
    """Types of events that can occur during a motor test."""

    IGNITION = "ignition"
    BURNOUT = "burnout"
    PEAK_THRUST = "peak_thrust"
    CUSTOM = "custom"


@dataclass
class DetectedEvent:
    """
    Represents a single event within a test.

    Event time is stored in seconds relative to the original
    test recording unless a later processing step explicitly
    changes the time reference.
    """

    event_type: EventType
    time_s: float

    sample_index: Optional[int] = None

    value: Optional[float] = None

    confidence: Optional[float] = None

    label: str = ""

    notes: str = ""

    automatically_detected: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert the event to a JSON-compatible dictionary."""

        return {
            "event_type": self.event_type.value,
            "time_s": self.time_s,
            "sample_index": self.sample_index,
            "value": self.value,
            "confidence": self.confidence,
            "label": self.label,
            "notes": self.notes,
            "automatically_detected": (
                self.automatically_detected
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "DetectedEvent":
        """Create a DetectedEvent from a dictionary."""

        return cls(
            event_type=EventType(
                data["event_type"]
            ),
            time_s=float(data["time_s"]),
            sample_index=data.get("sample_index"),
            value=data.get("value"),
            confidence=data.get("confidence"),
            label=data.get("label", ""),
            notes=data.get("notes", ""),
            automatically_detected=data.get(
                "automatically_detected",
                True,
            ),
        )


@dataclass
class EventSet:
    """
    Collection of events associated with one test.

    EventSet belongs to the prepared/analyzed representation
    of a test and does not modify the underlying raw data.
    """

    events: list[DetectedEvent] = field(
        default_factory=list
    )

    def add(self, event: DetectedEvent) -> None:
        """Add an event."""

        self.events.append(event)

    def clear(self) -> None:
        """Remove all events."""

        self.events.clear()

    def get(
        self,
        event_type: EventType,
    ) -> Optional[DetectedEvent]:
        """
        Return the first event of the requested type.

        Returns None when the event does not exist.
        """

        for event in self.events:
            if event.event_type == event_type:
                return event

        return None

    def get_all(
        self,
        event_type: EventType,
    ) -> list[DetectedEvent]:
        """Return all events of the requested type."""

        return [
            event
            for event in self.events
            if event.event_type == event_type
        ]

    @property
    def ignition(self) -> Optional[DetectedEvent]:
        """Return the ignition event, if present."""

        return self.get(EventType.IGNITION)

    @property
    def burnout(self) -> Optional[DetectedEvent]:
        """Return the burnout event, if present."""

        return self.get(EventType.BURNOUT)

    @property
    def peak_thrust(self) -> Optional[DetectedEvent]:
        """Return the peak-thrust event, if present."""

        return self.get(EventType.PEAK_THRUST)

    def to_dict(self) -> dict[str, Any]:
        """Convert the event set to a JSON-compatible dictionary."""

        return {
            "events": [
                event.to_dict()
                for event in self.events
            ]
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "EventSet":
        """Create an EventSet from a dictionary."""

        return cls(
            events=[
                DetectedEvent.from_dict(event_data)
                for event_data in data.get(
                    "events",
                    [],
                )
            ]
        )