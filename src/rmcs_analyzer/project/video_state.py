from dataclasses import dataclass, field
from typing import Dict, List


DEFAULT_RESULT_FIELDS = [
    "designation",
    "peak_thrust",
    "average_thrust",
    "total_impulse",
    "burn_time",
]


DEFAULT_EVENT_POSITIONS = {
    "ignition": [0.05, 0.78],
    "peak_thrust": [0.18, 0.16],
    "burnout": [0.82, 0.78],
}


DEFAULT_EVENT_VISIBILITY = {
    "ignition": True,
    "peak_thrust": True,
    "burnout": True,
}


@dataclass
class VideoState:
    """Persistent video, synchronization, and overlay configuration for one test."""

    source_path: str = ""
    sync_offset_s: float = 0.0

    show_curve_overlay: bool = True
    show_pressure_overlay: bool = False
    show_simulation_overlay: bool = False
    show_results_overlay: bool = True
    show_event_markers: bool = True

    playback_position_s: float = 0.0

    # Normalized position and size for the editable overlay components.
    curve_overlay_x: float = 0.06
    curve_overlay_y: float = 0.58
    curve_overlay_w: float = 0.58
    curve_overlay_h: float = 0.34

    pressure_overlay_x: float = 0.06
    pressure_overlay_y: float = 0.10
    pressure_overlay_w: float = 0.58
    pressure_overlay_h: float = 0.34

    results_overlay_x: float = 0.70
    results_overlay_y: float = 0.06
    results_overlay_w: float = 0.25
    results_overlay_h: float = 0.24

    # Legacy event group position fields retained for backward compatibility.
    events_overlay_x: float = 0.06
    events_overlay_y: float = 0.05

    # Individual event label positions, normalized to the video image.
    event_overlay_positions: Dict[str, List[float]] = field(
        default_factory=lambda: {
            key: value.copy()
            for key, value in DEFAULT_EVENT_POSITIONS.items()
        }
    )

    # Individual event visibility.
    event_visibility: Dict[str, bool] = field(
        default_factory=lambda: DEFAULT_EVENT_VISIBILITY.copy()
    )

    # Overlay presentation/configuration.
    curve_title: str = "Measured Thrust"
    curve_mode: str = "thrust"
    results_title: str = "Test Results"
    result_fields: List[str] = field(
        default_factory=lambda: DEFAULT_RESULT_FIELDS.copy()
    )
    curve_show_grid: bool = True
    curve_show_axes: bool = True
    curve_show_background: bool = True

    def clear_video(self):
        """Remove the associated video while retaining overlay configuration."""
        self.source_path = ""
        self.sync_offset_s = 0.0
        self.playback_position_s = 0.0

    @property
    def has_video(self) -> bool:
        return bool(self.source_path)

    def normalized_event_positions(self) -> Dict[str, List[float]]:
        """Return a safe copy of event positions with all values normalized."""
        result = {}
        for key, default in DEFAULT_EVENT_POSITIONS.items():
            value = self.event_overlay_positions.get(key, default)
            if not isinstance(value, (list, tuple)) or len(value) < 2:
                value = default
            result[key] = [
                max(0.0, min(1.0, float(value[0]))),
                max(0.0, min(1.0, float(value[1]))),
            ]
        return result
