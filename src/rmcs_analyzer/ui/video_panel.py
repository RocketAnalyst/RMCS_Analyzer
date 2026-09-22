from pathlib import Path

import numpy as np

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QUrl, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoFrame, QVideoSink
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class VideoFrameWidget(QWidget):
    """Paint decoded QVideoFrames into a normal QWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QImage()
        self._scaled = QImage()
        self._scaled_size = QSize()
        self._content_rect = QRect()
        self._display_mode = "fit"
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_frame(self, frame: QVideoFrame):
        if not frame.isValid():
            return
        try:
            image = frame.toImage()
        except Exception:
            return
        if image.isNull():
            return
        self._image = image
        self._scaled = QImage()
        self._scaled_size = QSize()
        self._recalculate_content_rect()
        self.update()

    def set_display_mode(self, mode):
        mode = str(mode or "fit").lower()
        if mode not in ("fit", "fill"):
            mode = "fit"
        self._display_mode = mode
        self._scaled = QImage()
        self._scaled_size = QSize()
        self._recalculate_content_rect()
        self.update()

    def display_mode(self):
        return self._display_mode

    def clear_frame(self):
        self._image = QImage()
        self._scaled = QImage()
        self._scaled_size = QSize()
        self._content_rect = QRect()
        self.update()

    def content_rect(self):
        return QRect(self._content_rect)

    def _recalculate_content_rect(self):
        if self._image.isNull() or self._image.height() <= 0:
            self._content_rect = self.rect()
            return
        source_ratio = self._image.width() / self._image.height()
        if self._display_mode == "fill":
            self._content_rect = self.rect()
            return

        # Fit: maximize the decoded frame inside the available area while
        # preserving its aspect ratio. This supports both portrait and
        # landscape video without distortion or cropping.
        target_w = float(self.width())
        target_h = target_w / source_ratio
        if target_h > self.height():
            target_h = float(self.height())
            target_w = target_h * source_ratio
        x = (self.width() - target_w) / 2.0
        y = (self.height() - target_h) / 2.0
        self._content_rect = QRect(
            round(x),
            round(y),
            max(1, round(target_w)),
            max(1, round(target_h)),
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scaled = QImage()
        self._scaled_size = QSize()
        self._recalculate_content_rect()
        parent = self.parentWidget()
        if parent is not None and hasattr(parent, "sync_overlay_geometry"):
            parent.sync_overlay_geometry()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        if self._image.isNull():
            painter.end()
            return
        rect = self._content_rect
        if self._scaled.isNull() or self._scaled_size != rect.size():
            aspect_mode = (
                Qt.AspectRatioMode.KeepAspectRatioByExpanding
                if self._display_mode == "fill"
                else Qt.AspectRatioMode.KeepAspectRatio
            )
            self._scaled = self._image.scaled(
                rect.size(),
                aspect_mode,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._scaled_size = rect.size()

        if self._display_mode == "fill":
            # Keep the image centered after expanding; this crops only the
            # excess area needed to fill the preview.
            x = max(0, (self._scaled.width() - rect.width()) // 2)
            y = max(0, (self._scaled.height() - rect.height()) // 2)
            source = QRect(x, y, rect.width(), rect.height())
            painter.drawImage(rect.topLeft(), self._scaled, source)
        else:
            painter.drawImage(rect.topLeft(), self._scaled)
        painter.end()


class VideoCanvas(QFrame):
    """Normal QWidget container for video and transparent analysis graphics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("videoCanvas")
        self.setStyleSheet("QFrame#videoCanvas { background: #000000; }")
        self.video_surface = None
        self.overlay = None

    def sync_overlay_geometry(self):
        if self.video_surface is None or self.overlay is None:
            return
        self.overlay.setGeometry(self.video_surface.content_rect())
        self.overlay.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.video_surface is not None:
            self.video_surface.setGeometry(self.rect())
            self.video_surface._recalculate_content_rect()
        self.sync_overlay_geometry()


class VideoOverlayWidget(QWidget):
    """
    Resolution-independent analysis graphics rendered directly over the
    decoded video frame.

    Curve, results, and each event label are independent editable objects.
    """

    overlay_positions_changed = Signal(
        float, float, float, float, float, float, float, float
    )
    pressure_overlay_positions_changed = Signal(float, float, float, float)
    event_positions_changed = Signal(object)

    CURVE = QColor(77, 220, 255)
    SIMULATION = QColor(255, 184, 77)
    WHITE = QColor(248, 252, 255)
    AXIS = QColor(226, 236, 242, 220)
    GRID = QColor(235, 245, 250, 58)
    IGNITION = QColor(49, 232, 111)
    PEAK = QColor(80, 165, 255)
    BURNOUT = QColor(255, 83, 92)
    SHADOW = QColor(0, 0, 0, 215)
    SELECTION = QColor(90, 220, 255, 220)

    EVENT_COLORS = {
        "ignition": IGNITION,
        "peak_thrust": PEAK,
        "burnout": BURNOUT,
    }

    EVENT_LABELS = {
        "ignition": "Ignition",
        "peak_thrust": "Peak Thrust",
        "burnout": "Burnout",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        self._times = None
        self._thrust = None
        self._pressure = None
        self._simulation_times = None
        self._simulation_thrust = None
        self._simulation_pressure = None
        self._curve_mode = "thrust"
        self._show_pressure_curve = False
        self._time = 0.0
        self._peak = None
        self._average = None
        self._impulse = None
        self._burn_time = None
        self._time_to_peak = None
        self._isp = None
        self._cstar = None
        self._avg_pressure = None
        self._avg_mass_flow = None
        self._designation = None
        self._motor_class = None
        self._event_data = {}

        self._show_curve = True
        self._show_pressure_curve = False
        self._show_simulation = False
        self._show_results = True
        self._show_events = True

        self._curve = [0.06, 0.58, 0.58, 0.34]
        self._pressure_curve = [0.06, 0.10, 0.58, 0.34]
        self._results = [0.70, 0.06, 0.25, 0.24]
        self._event_positions = {
            "ignition": [0.05, 0.78],
            "peak_thrust": [0.18, 0.16],
            "burnout": [0.82, 0.78],
        }
        self._event_visibility = {
            "ignition": True,
            "peak_thrust": True,
            "burnout": True,
        }

        self._curve_title = "Measured Thrust"
        self._results_title = "Test Results"
        self._result_fields = [
            "designation",
            "peak_thrust",
            "average_thrust",
            "total_impulse",
            "burn_time",
        ]
        self._curve_show_grid = True
        self._curve_show_axes = True
        self._curve_show_background = True

        self._selected = None
        self._drag_target = None
        self._resize_target = None
        self._drag_offset = QPoint()

    # ---------------------------------------------------------
    # Analysis/configuration
    # ---------------------------------------------------------

    def set_analysis(
        self,
        times,
        thrust,
        pressure=None,
        thrust_results=None,
        classification=None,
        events=None,
        simulation_times=None,
        simulation_thrust=None,
        simulation_pressure=None,
    ):
        self._times = np.asarray(times, dtype=float) if times is not None else None
        self._thrust = np.asarray(thrust, dtype=float) if thrust is not None else None
        self._pressure = (
            np.asarray(pressure, dtype=float) if pressure is not None else None
        )
        self._simulation_times = (
            np.asarray(simulation_times, dtype=float)
            if simulation_times is not None
            else None
        )
        self._simulation_thrust = (
            np.asarray(simulation_thrust, dtype=float)
            if simulation_thrust is not None
            else None
        )
        self._simulation_pressure = (
            np.asarray(simulation_pressure, dtype=float)
            if simulation_pressure is not None
            else None
        )

        if thrust_results is not None:
            self._peak = thrust_results.peak_thrust_N
            self._average = thrust_results.average_thrust_5pct_N
            self._impulse = thrust_results.total_impulse_valid_curve_Ns
            self._burn_time = thrust_results.burn_time_5pct_s
            self._time_to_peak = thrust_results.peak_thrust_time_s
            self._isp = thrust_results.isp_s
            self._cstar = thrust_results.cstar_m_per_s
            self._avg_pressure = thrust_results.average_chamber_pressure_psi
            self._avg_mass_flow = thrust_results.average_mass_flow_kg_per_s
            self._designation = thrust_results.designation
        else:
            self._peak = self._average = self._impulse = self._burn_time = None
            self._time_to_peak = None
            self._isp = self._cstar = self._avg_pressure = self._avg_mass_flow = None
            self._designation = None

        self._motor_class = (
            getattr(classification, "motor_class", None)
            if classification is not None
            else None
        )

        self._event_data = {}
        if events is not None:
            for key, event in (
                ("ignition", getattr(events, "ignition", None)),
                ("peak_thrust", getattr(events, "peak_thrust", None)),
                ("burnout", getattr(events, "burnout", None)),
            ):
                if event is not None:
                    self._event_data[key] = float(event.time_s)

        self.update()

    def set_curve_mode(self, mode):
        mode = str(mode or "thrust").strip().lower()
        self._curve_mode = mode if mode in {"thrust", "pressure"} else "thrust"
        self.update()

    def curve_mode(self):
        return self._curve_mode

    def set_simulation_visible(self, visible):
        self._show_simulation = bool(visible)
        self.update()

    def simulation_visible(self):
        return self._show_simulation

    def set_pressure_visible(self, visible):
        self._show_pressure_curve = bool(visible)
        self.update()

    def pressure_visible(self):
        return self._show_pressure_curve

    def set_pressure_overlay_position(self, x, y, w=0.58, h=0.34):
        self._pressure_curve = [
            self._clamp01(x),
            self._clamp01(y),
            self._clamp_size(w),
            self._clamp_size(h),
        ]
        self.update()

    def pressure_overlay_position(self):
        return tuple(self._pressure_curve)

    def has_simulation_for_mode(self, mode=None):
        mode = mode or self._curve_mode
        return (
            self._simulation_pressure is not None
            if mode == "pressure"
            else self._simulation_thrust is not None
        )

    def apply_configuration(

        self,
        *,
        curve_title,
        results_title,
        result_fields,
        event_visibility,
        curve_show_grid,
        curve_show_axes,
        curve_show_background=True,
    ):
        self._curve_title = str(curve_title).strip() or "Measured Thrust"
        self._results_title = str(results_title).strip() or "Test Results"
        self._result_fields = list(result_fields)
        for key in self.EVENT_LABELS:
            self._event_visibility[key] = bool(
                event_visibility.get(key, True)
            )
        self._curve_show_grid = bool(curve_show_grid)
        self._curve_show_axes = bool(curve_show_axes)
        self._curve_show_background = bool(curve_show_background)
        self.update()

    def configuration(self):
        return {
            "curve_title": self._curve_title,
            "results_title": self._results_title,
            "result_fields": list(self._result_fields),
            "event_visibility": dict(self._event_visibility),
            "curve_show_grid": self._curve_show_grid,
            "curve_show_axes": self._curve_show_axes,
            "curve_show_background": self._curve_show_background,
        }

    def set_position(self, position_s):
        self._time = float(position_s or 0.0)
        self.update()

    def set_visibility(self, curve, results, events, pressure=False):
        self._show_curve = bool(curve)
        self._show_pressure_curve = bool(pressure)
        self._show_results = bool(results)
        self._show_events = bool(events)
        self.update()

    def set_overlay_positions(
        self,
        curve_x,
        curve_y,
        results_x,
        results_y,
        curve_w=0.58,
        curve_h=0.34,
        results_w=0.25,
        results_h=0.24,
        event_positions=None,
    ):
        self._curve = [
            self._clamp01(curve_x),
            self._clamp01(curve_y),
            self._clamp_size(curve_w),
            self._clamp_size(curve_h),
        ]
        self._results = [
            self._clamp01(results_x),
            self._clamp01(results_y),
            self._clamp_size(results_w),
            self._clamp_size(results_h),
        ]

        if event_positions is not None:
            for key in self.EVENT_LABELS:
                value = event_positions.get(key)
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    self._event_positions[key] = [
                        self._clamp01(value[0]),
                        self._clamp01(value[1]),
                    ]

        self.update()

    def overlay_positions(self):
        return (
            self._curve[0],
            self._curve[1],
            self._results[0],
            self._results[1],
            self._curve[2],
            self._curve[3],
            self._results[2],
            self._results[3],
        )

    def event_positions(self):
        return {
            key: value.copy()
            for key, value in self._event_positions.items()
        }

    @staticmethod
    def _clamp01(value):
        return max(0.0, min(1.0, float(value)))

    @staticmethod
    def _clamp_size(value):
        return max(0.12, min(0.90, float(value)))

    def _rect(self, box):
        return QRect(
            int(box[0] * self.width()),
            int(box[1] * self.height()),
            max(70, int(box[2] * self.width())),
            max(50, int(box[3] * self.height())),
        )

    def _curve_rect(self):
        return self._rect(self._curve)

    def _pressure_curve_rect(self):
        return self._rect(self._pressure_curve)

    def _results_rect(self):
        return self._rect(self._results)

    def _selected_measured_data(self):
        values = self._pressure if self._curve_mode == "pressure" else self._thrust
        if self._times is None or values is None:
            return np.array([]), np.array([])
        mask = np.isfinite(self._times) & np.isfinite(values)
        return self._times[mask], values[mask]

    def _selected_simulation_data(self):
        values = (
            self._simulation_pressure
            if self._curve_mode == "pressure"
            else self._simulation_thrust
        )
        if self._simulation_times is None or values is None:
            return np.array([]), np.array([])
        mask = np.isfinite(self._simulation_times) & np.isfinite(values)
        return self._simulation_times[mask], values[mask]

    def _data(self):
        return self._selected_measured_data()

    def _thrust_data(self):
        if self._times is None or self._thrust is None:
            return np.array([]), np.array([])
        mask = np.isfinite(self._times) & np.isfinite(self._thrust)
        return self._times[mask], self._thrust[mask]

    def _current_thrust(self):
        times, thrust = self._thrust_data()
        if len(times) == 0 or self._time < times[0]:
            return None
        return float(np.interp(self._time, times, thrust))

    def _format_metric(
self, key):
        value = {
            "current_thrust": self._current_thrust(),
            "designation": self._designation,
            "motor_class": self._motor_class,
            "peak_thrust": self._peak,
            "average_thrust": self._average,
            "total_impulse": self._impulse,
            "burn_time": self._burn_time,
            "time_to_peak": self._time_to_peak,
            "isp": self._isp,
            "cstar": self._cstar,
            "avg_pressure": self._avg_pressure,
            "avg_mass_flow": self._avg_mass_flow,
        }.get(key)

        labels = {
            "current_thrust": ("Current Thrust", lambda v: f"{v:.0f} N"),
            "designation": ("Designation", lambda v: str(v)),
            "motor_class": ("Motor Class", lambda v: str(v)),
            "peak_thrust": ("Peak Thrust", lambda v: f"{v:.0f} N"),
            "average_thrust": ("Average Thrust", lambda v: f"{v:.0f} N"),
            "total_impulse": ("Total Impulse", lambda v: f"{v:.0f} N·s"),
            "burn_time": ("Burn Time", lambda v: f"{v:.2f} s"),
            "time_to_peak": ("Time to Peak", lambda v: f"{v:.2f} s"),
            "isp": ("Isp", lambda v: f"{v:.2f} s"),
            "cstar": ("C*", lambda v: f"{v:.0f} m/s"),
            "avg_pressure": ("Avg Chamber Pressure", lambda v: f"{v:.1f} psi"),
            "avg_mass_flow": ("Avg Mass Flow", lambda v: f"{v:.4f} kg/s"),
        }
        label, formatter = labels.get(key, (key, str))
        if value is None or value == "":
            return f"{label}  —"
        return f"{label}  {formatter(value)}"

    # ---------------------------------------------------------
    def _graph_data(self, mode, simulation=False):
        if simulation:
            times = self._simulation_times
            values = self._simulation_pressure if mode == "pressure" else self._simulation_thrust
        else:
            times = self._times
            values = self._pressure if mode == "pressure" else self._thrust
        if times is None or values is None:
            return np.array([]), np.array([])
        times = np.asarray(times, dtype=float)
        values = np.asarray(values, dtype=float)
        mask = np.isfinite(times) & np.isfinite(values)
        return times[mask], values[mask]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._show_curve:
            self._paint_graph(
                painter,
                mode="thrust",
                box=self._curve,
                title=self._curve_title,
            )

        if self._show_pressure_curve:
            self._paint_graph(
                painter,
                mode="pressure",
                box=self._pressure_curve,
                title="Measured Pressure",
            )

        if self._show_results:
            self._paint_results(painter)
        if self._show_events:
            self._paint_events(painter)
        self._paint_selection(painter)

        painter.end()

    def _draw_shadow_text(self, painter, x, y, text, font, color=None):
        if color is None:
            color = self.WHITE
        painter.setFont(font)
        painter.setPen(self.SHADOW)
        painter.drawText(x + 2, y + 2, text)
        painter.setPen(color)
        painter.drawText(x, y, text)

    def _paint_graph(self, painter, *, mode, box, title):
        measured_times, measured_values = self._graph_data(mode, simulation=False)
        simulation_times, simulation_values = self._graph_data(mode, simulation=True)

        measured_ok = len(measured_times) >= 2
        simulation_ok = self._show_simulation and len(simulation_times) >= 2

        if not measured_ok and not simulation_ok:
            return

        all_times = []
        all_values = []
        if measured_ok:
            all_times.append(measured_times)
            all_values.append(measured_values)
        if simulation_ok:
            all_times.append(simulation_times)
            all_values.append(simulation_values)

        t0 = min(float(values[0]) for values in all_times)
        t1 = max(float(values[-1]) for values in all_times)
        if t1 <= t0:
            return

        max_value = max(
            1.0,
            max(float(np.nanmax(values)) for values in all_values),
        )
        r = self._rect(box)

        if self._curve_show_background:
            painter.fillRect(r, QColor(0, 0, 0, 52))

        title_font = QFont(
            "Segoe UI",
            max(8, int(r.height() / 14)),
            QFont.Weight.DemiBold,
        )
        self._draw_shadow_text(
            painter,
            r.left() + int(r.width() * 0.035),
            r.top() + int(r.height() * 0.075),
            title,
            title_font,
        )

        left = r.left() + int(r.width() * 0.12)
        top = r.top() + int(r.height() * 0.19)
        right = r.right() - int(r.width() * 0.035)
        bottom = r.bottom() - int(r.height() * 0.15)
        plot = QRect(
            left,
            top,
            max(20, right - left),
            max(20, bottom - top),
        )

        if self._curve_show_grid:
            painter.setPen(QPen(self.GRID, 1))
            for i in range(1, 5):
                y = plot.top() + int(i * plot.height() / 5)
                painter.drawLine(plot.left(), y, plot.right(), y)
            for i in range(1, 5):
                x = plot.left() + int(i * plot.width() / 5)
                painter.drawLine(x, plot.top(), x, plot.bottom())

        if self._curve_show_axes:
            painter.setPen(QPen(self.AXIS, 1))
            painter.drawLine(plot.left(), plot.top(), plot.left(), plot.bottom())
            painter.drawLine(plot.left(), plot.bottom(), plot.right(), plot.bottom())

        def draw_series(times, values, pen):
            path = QPainterPath()
            for i, (t, value) in enumerate(zip(times, values)):
                x = plot.left() + (float(t) - t0) / (t1 - t0) * plot.width()
                y = plot.bottom() - float(value) / max_value * plot.height()
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            # drawPath() uses the painter's current brush as its fill.
            # The playback marker later uses a white brush, so explicitly
            # disable the brush here; the graph must remain a line-only
            # overlay for both thrust and pressure.
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(pen)
            painter.drawPath(path)

        width = max(2, int(min(r.width(), r.height()) / 105))
        if measured_ok:
            draw_series(
                measured_times,
                measured_values,
                QPen(
                    self.CURVE,
                    width,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                ),
            )

        if simulation_ok:
            draw_series(
                simulation_times,
                simulation_values,
                QPen(
                    self.SIMULATION,
                    width,
                    Qt.PenStyle.DashLine,
                    Qt.PenCapStyle.RoundCap,
                    Qt.PenJoinStyle.RoundJoin,
                ),
            )

        unit = "psi" if mode == "pressure" else "N"
        axis_font = QFont(
            "Segoe UI",
            max(7, int(r.height() / 23)),
            QFont.Weight.Normal,
        )
        painter.setFont(axis_font)

        for fraction in (0.0, 0.5, 1.0):
            value = max_value * fraction
            y = plot.bottom() - int(fraction * plot.height())
            label = f"{value:.0f} {unit}"
            bounds = painter.fontMetrics().boundingRect(label)
            label_x = plot.left() - bounds.width() - 7
            label_y = y + int(bounds.height() * 0.35)
            self._draw_shadow_text(
                painter,
                label_x,
                label_y,
                label,
                axis_font,
                self.WHITE,
            )

        for fraction in (0.0, 0.5, 1.0):
            value = t0 + (t1 - t0) * fraction
            x = plot.left() + int(fraction * plot.width())
            self._draw_shadow_text(
                painter,
                x - 12,
                r.bottom() - 4,
                f"{value:.1f}",
                axis_font,
                self.WHITE,
            )

        self._draw_shadow_text(
            painter,
            plot.right() - 28,
            r.bottom() - 4,
            "s",
            axis_font,
            self.WHITE,
        )

        if self._time >= t0 and measured_ok:
            tm = min(self._time, float(measured_times[-1]))
            tv = float(np.interp(tm, measured_times, measured_values))
            x = plot.left() + (tm - t0) / (t1 - t0) * plot.width()
            y = plot.bottom() - tv / max_value * plot.height()
            radius = max(4, int(min(r.width(), r.height()) / 45))
            painter.setPen(QPen(self.WHITE, 2))
            painter.setBrush(self.WHITE)
            painter.drawEllipse(
                int(x - radius),
                int(y - radius),
                radius * 2,
                radius * 2,
            )

    def _paint_results(self, painter):
        r = self._results_rect()

        title_font = QFont(
            "Segoe UI",
            max(9, int(r.height() / 11)),
            QFont.Weight.DemiBold,
        )
        value_font = QFont(
            "Segoe UI",
            max(8, int(r.height() / max(13, len(self._result_fields) * 3))),
            QFont.Weight.Normal,
        )

        self._draw_shadow_text(
            painter,
            r.left(),
            r.top() + title_font.pointSize() + 2,
            self._results_title,
            title_font,
        )

        y = r.top() + title_font.pointSize() + value_font.pointSize() + 10
        for key in self._result_fields:
            self._draw_shadow_text(
                painter,
                r.left(),
                y,
                self._format_metric(key),
                value_font,
                self.WHITE,
            )
            y += value_font.pointSize() + 5

    def _event_anchor(self, event_key, event_time, chart_rect):
        times, values = self._graph_data("thrust", simulation=False)
        if len(times) < 2:
            times, values = self._graph_data("thrust", simulation=True)
        if len(times) < 2:
            return None
        t0, t1 = float(times[0]), float(times[-1])
        max_value = max(1.0, float(np.nanmax(values)))
        tm = max(t0, min(float(event_time), t1))
        tv = float(np.interp(tm, times, values))
        x = chart_rect.left() + (tm - t0) / (t1 - t0) * chart_rect.width()
        y = chart_rect.bottom() - tv / max_value * chart_rect.height()
        return QPoint(int(x), int(y))

    def _event_label_rect(self, event_key):
        pos = self._event_positions.get(event_key, [0.1, 0.1])
        font_size = max(8, int(min(self.width(), self.height()) / 75))
        width = max(95, int(font_size * 8.2))
        height = max(24, int(font_size * 2.2))
        x = int(pos[0] * self.width())
        y = int(pos[1] * self.height())
        return QRect(x, y, width, height)

    def _paint_events(self, painter):
        if not self._event_data:
            return

        chart = (
            self._curve_rect()
            if self._show_curve
            else self._pressure_curve_rect()
        )
        plot_left = chart.left() + int(chart.width() * 0.12)
        plot_top = chart.top() + int(chart.height() * 0.19)
        plot_right = chart.right() - int(chart.width() * 0.035)
        plot_bottom = chart.bottom() - int(chart.height() * 0.15)
        plot = QRect(
            plot_left,
            plot_top,
            max(20, plot_right - plot_left),
            max(20, plot_bottom - plot_top),
        )

        font = QFont(
            "Segoe UI",
            max(8, int(min(self.width(), self.height()) / 75)),
            QFont.Weight.DemiBold,
        )

        for key, event_time in self._event_data.items():
            if not self._event_visibility.get(key, True):
                continue
            anchor = self._event_anchor(key, event_time, plot)
            if anchor is None:
                continue

            rect = self._event_label_rect(key)
            color = self.EVENT_COLORS.get(key, self.WHITE)
            painter.setPen(QPen(color, 1))
            painter.drawLine(anchor, rect.center())

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(anchor.x() - 4, anchor.y() - 4, 8, 8)

            self._draw_shadow_text(
                painter,
                rect.left(),
                rect.top() + font.pointSize() + 4,
                f"{self.EVENT_LABELS.get(key, key)}  {event_time:.2f} s",
                font,
                color,
            )

    # ---------------------------------------------------------
    # Editing
    # ---------------------------------------------------------

    def _paint_selection(self, painter):
        if self._selected is None:
            return

        if self._selected == "curve":
            rect = self._curve_rect()
        elif self._selected == "pressure":
            rect = self._pressure_curve_rect()
        elif self._selected == "results":
            rect = self._results_rect()
        elif self._selected.startswith("event:"):
            rect = self._event_label_rect(self._selected.split(":", 1)[1])
        else:
            return

        painter.setPen(QPen(self.SELECTION, 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        if self._selected in ("curve", "pressure", "results"):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.SELECTION)
            painter.drawRect(rect.right() - 7, rect.bottom() - 7, 7, 7)

    def _hit(self, point):
        if self._show_results and self._results_rect().contains(point):
            return "results"

        if self._show_events:
            for key in self._event_data:
                if self._event_visibility.get(key, True):
                    if self._event_label_rect(key).contains(point):
                        return f"event:{key}"

        if self._show_pressure_curve and self._pressure_curve_rect().contains(point):
            return "pressure"

        if self._show_curve and self._curve_rect().contains(point):
            return "curve"

        return None

    def _resize_hit(self, point, target):
        if target not in ("curve", "pressure", "results"):
            return False
        if target == "curve":
            rect = self._curve_rect()
        elif target == "pressure":
            rect = self._pressure_curve_rect()
        else:
            rect = self._results_rect()
        return (
            abs(point.x() - rect.right()) <= 12
            and abs(point.y() - rect.bottom()) <= 12
        )

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        point = event.position().toPoint()
        target = self._hit(point)

        if target is None:
            self._selected = None
            self._drag_target = None
            self._resize_target = None
            self.update()
            return

        self._selected = target

        if self._resize_hit(point, target):
            self._resize_target = target
            self._drag_target = None
        else:
            self._drag_target = target
            self._resize_target = None

            if target in ("curve", "pressure", "results"):
                if target == "curve":
                    rect = self._curve_rect()
                elif target == "pressure":
                    rect = self._pressure_curve_rect()
                else:
                    rect = self._results_rect()
            else:
                rect = self._event_label_rect(
                    target.split(":", 1)[1]
                )

            self._drag_offset = QPoint(
                point.x() - rect.left(),
                point.y() - rect.top(),
            )

        self.update()
        event.accept()

    def mouseMoveEvent(self, event):
        point = event.position().toPoint()

        if (
            self._resize_target
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            if self._resize_target == "curve":
                box = self._curve
            elif self._resize_target == "pressure":
                box = self._pressure_curve
            else:
                box = self._results
            left = box[0] * self.width()
            top = box[1] * self.height()
            box[2] = max(
                0.12,
                min(
                    0.90 - box[0],
                    (point.x() - left) / max(1, self.width()),
                ),
            )
            box[3] = max(
                0.12,
                min(
                    0.90 - box[1],
                    (point.y() - top) / max(1, self.height()),
                ),
            )
            self.update()
            self._emit_positions(self._resize_target)
            event.accept()
            return

        if (
            self._drag_target
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            target = self._drag_target

            if target in ("curve", "pressure", "results"):
                if target == "curve":
                    box = self._curve
                elif target == "pressure":
                    box = self._pressure_curve
                else:
                    box = self._results
                x = (
                    point.x() - self._drag_offset.x()
                ) / max(1, self.width())
                y = (
                    point.y() - self._drag_offset.y()
                ) / max(1, self.height())
                box[0] = max(0.0, min(1.0 - box[2], x))
                box[1] = max(0.0, min(1.0 - box[3], y))
                self._emit_positions()
            elif target.startswith("event:"):
                key = target.split(":", 1)[1]
                x = (
                    point.x() - self._drag_offset.x()
                ) / max(1, self.width())
                y = (
                    point.y() - self._drag_offset.y()
                ) / max(1, self.height())
                width = self._event_label_rect(key).width() / max(1, self.width())
                height = self._event_label_rect(key).height() / max(1, self.height())
                self._event_positions[key][0] = max(
                    0.0, min(1.0 - width, x)
                )
                self._event_positions[key][1] = max(
                    0.0, min(1.0 - height, y)
                )
                self.event_positions_changed.emit(self.event_positions())

            self.update()
            if target in ("curve", "pressure", "results"):
                self._emit_positions(target)
            event.accept()
            return

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_target = None
            self._resize_target = None
            self.update()
            event.accept()

    def _emit_positions(self, target=None):
        if target in (None, "curve", "results"):
            self.overlay_positions_changed.emit(*self.overlay_positions())
        if target in ("pressure", None):
            self.pressure_overlay_positions_changed.emit(
                *self.pressure_overlay_position()
            )


class VideoPopoutWindow(QDialog):
    closed = Signal()

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RMCS Video")
        self.resize(1100, 800)
        self.setMinimumSize(650, 500)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        self.canvas = canvas
        self.canvas.setParent(self)
        layout.addWidget(self.canvas, 1)

    def closeEvent(self, event):
        self.closed.emit()
        event.accept()


class VideoPanel(QFrame):
    video_changed = Signal(str)
    video_removed = Signal()
    sync_offset_changed = Signal(float)
    overlay_changed = Signal(bool, bool, bool)
    pressure_overlay_changed = Signal(bool)
    simulation_overlay_changed = Signal(bool)
    curve_mode_changed = Signal(str)
    overlay_positions_changed = Signal(float, float, float, float, float, float, float, float)
    pressure_overlay_positions_changed = Signal(float, float, float, float)
    overlay_event_positions_changed = Signal(object)
    overlay_configuration_changed = Signal(object)
    duration_changed = Signal(float)
    pdf_frame_changed = Signal(object)
    overlay_options_requested = Signal()

    SUPPORTED_FILTER = (
        "Video Files (*.mp4 *.mov *.m4v *.avi *.mkv *.wmv *.webm);;"
        "All Files (*.*)"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("subPanel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._sync_offset_s = 0.0
        self._timeline_position_s = 0.0
        self._video_duration_s = 0.0
        self._loading_state = False
        self._playing = False
        self._video_name = ""
        self._popout = None
        self._has_analysis = False
        self._priming_frame = False
        self._priming_audio_volume = None
        self._pdf_frame_position_s = None
        self._display_mode = "fit"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)
        self._video_layout = layout

        header = QHBoxLayout()
        header.addWidget(self._header("Video Overlay"))
        header.addStretch(1)
        self.status_label = QLabel("No video loaded")
        self.status_label.setObjectName("videoStatus")
        self.status_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        self.status_label.setMaximumWidth(210)
        self.status_label.setToolTip("")
        header.addWidget(self.status_label)
        self.overlay_options_button = QPushButton("Overlay Options…")
        self.overlay_options_button.setObjectName("videoOverlayOptionsButton")
        self.overlay_options_button.setToolTip(
            "Open Video Overlay settings for the active test."
        )
        header.addWidget(self.overlay_options_button)

        self.load_button = QPushButton("Load Video…")
        self.load_button.setObjectName("loadVideoButton")
        header.addWidget(self.load_button)
        self.popout_button = QPushButton("Pop Out")
        self.popout_button.setObjectName("videoPopoutButton")
        self.popout_button.setEnabled(False)
        header.addWidget(self.popout_button)
        self.remove_button = QPushButton("×")
        self.remove_button.setObjectName("videoRemoveButton")
        self.remove_button.setEnabled(False)
        header.addWidget(self.remove_button)
        layout.addLayout(header)

        self._video_container = VideoCanvas()
        self._video_container.setObjectName("videoPreview")
        self._video_container.setMinimumHeight(82)
        self._video_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        layout.addWidget(self._video_container, 1)

        self.video_surface = VideoFrameWidget(self._video_container)
        self._video_container.video_surface = self.video_surface
        self.overlay = VideoOverlayWidget(self._video_container)
        self._video_container.overlay = self.overlay
        self._video_container.sync_overlay_geometry()

        sync_row = QHBoxLayout()
        sync_row.setSpacing(4)

        self.sync_spin = QDoubleSpinBox()
        self.sync_spin.setObjectName("videoSyncSpin")
        self.sync_spin.setRange(-3600.0, 3600.0)
        self.sync_spin.setDecimals(3)
        self.sync_spin.setSingleStep(0.010)
        self.sync_spin.setSuffix(" s")
        self.sync_spin.setPrefix("Sync Start ")
        self.sync_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.sync_spin.setFixedWidth(104)
        self.sync_spin.setToolTip("Video time at which RMCS analysis t = 0 begins.")

        self.sync_up_button = QPushButton("▲")
        self.sync_down_button = QPushButton("▼")
        for button in (self.sync_up_button, self.sync_down_button):
            button.setObjectName("videoSyncStepButton")
            button.setFixedWidth(22)

        sync = QHBoxLayout()
        sync.setContentsMargins(0, 0, 0, 0)
        sync.setSpacing(2)
        sync.addWidget(self.sync_spin)
        sync.addWidget(self.sync_up_button)
        sync.addWidget(self.sync_down_button)
        sync_row.addLayout(sync)
        layout.addLayout(sync_row)

        pdf_frame_row = QHBoxLayout()
        pdf_frame_row.setSpacing(5)
        self.pdf_frame_label = QLabel("PDF Report Frame: Automatic")
        self.pdf_frame_label.setObjectName("videoPdfFrameLabel")
        self.pdf_frame_label.setToolTip(
            "Position the video at the desired moment, then choose Use Current Frame. Automatic uses RMCS's representative frame."
        )
        pdf_frame_row.addWidget(self.pdf_frame_label)
        pdf_frame_row.addStretch(1)
        self.use_pdf_frame_button = QPushButton("Use Current Frame")
        self.use_pdf_frame_button.setObjectName("videoPdfFrameButton")
        self.use_pdf_frame_button.setEnabled(False)
        self.use_pdf_frame_button.setToolTip("Use the current video position as the PDF report frame for this test.")
        self.clear_pdf_frame_button = QPushButton("Clear Selection")
        self.clear_pdf_frame_button.setObjectName("videoPdfFrameButton")
        self.clear_pdf_frame_button.setEnabled(False)
        self.clear_pdf_frame_button.setToolTip("Return PDF frame selection to automatic representative-frame selection.")
        pdf_frame_row.addWidget(self.use_pdf_frame_button)
        pdf_frame_row.addWidget(self.clear_pdf_frame_button)
        layout.addLayout(pdf_frame_row)

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(1.0)
        self.player.setAudioOutput(self.audio)
        self.video_sink = QVideoSink(self)
        self.video_sink.videoFrameChanged.connect(self._on_video_frame)
        self.player.setVideoSink(self.video_sink)
        self.player.durationChanged.connect(self._duration_changed)
        self.player.mediaStatusChanged.connect(self._media_status_changed)
        self.player.errorOccurred.connect(self._error_occurred)

        self.overlay_options_button.clicked.connect(
            self.overlay_options_requested.emit
        )
        self.load_button.clicked.connect(self._choose_video)
        self.remove_button.clicked.connect(self.video_removed.emit)
        self.popout_button.clicked.connect(self.toggle_popout)
        self.sync_spin.valueChanged.connect(self._sync_changed)
        self.sync_up_button.clicked.connect(self.sync_spin.stepUp)
        self.sync_down_button.clicked.connect(self.sync_spin.stepDown)
        self.use_pdf_frame_button.clicked.connect(self.use_current_frame_for_pdf)
        self.clear_pdf_frame_button.clicked.connect(self.clear_pdf_frame)

        self.overlay.overlay_positions_changed.connect(
            self._overlay_position_changed
        )
        self.overlay.pressure_overlay_positions_changed.connect(
            self._pressure_overlay_position_changed
        )
        self.overlay.event_positions_changed.connect(
            self._overlay_event_position_changed
        )

        self.show_empty_state()

    def _header(self, text):
        label = QLabel(text)
        label.setObjectName("lowerPanelHeader")
        return label

    def show_empty_state(self):
        if self._popout is not None:
            self.close_popout()

        self._priming_frame = False
        if self._priming_audio_volume is not None:
            self.audio.setVolume(self._priming_audio_volume)
            self._priming_audio_volume = None
        self.player.stop()
        self.player.setSource(QUrl())
        self.status_label.setText("No video loaded")
        self.status_label.setToolTip("")
        self.remove_button.setEnabled(False)
        self.popout_button.setEnabled(False)
        self._video_duration_s = 0.0
        self._video_name = ""
        self._playing = False
        self._pdf_frame_position_s = None
        self.pdf_frame_label.setText("PDF Report Frame: Automatic")
        self.use_pdf_frame_button.setEnabled(False)
        self.clear_pdf_frame_button.setEnabled(False)
        self.video_surface.clear_frame()
        self._has_analysis = False
        self.overlay.set_analysis(None, None, pressure=None)
        self.overlay.set_visibility(False, False, False, pressure=False)
        self.overlay.hide()
        self.duration_changed.emit(0.0)

    def set_video_state(
        self,
        source_path,
        sync_offset_s=0.0,
        show_curve=True,
        show_pressure=False,
        show_simulation=False,
        show_results=True,
        show_events=True,
        curve_x=0.06,
        curve_y=0.58,
        pressure_x=0.06,
        pressure_y=0.10,
        results_x=0.70,
        results_y=0.06,
        curve_w=0.58,
        curve_h=0.34,
        pressure_w=0.58,
        pressure_h=0.34,
        results_w=0.25,
        results_h=0.24,
        event_positions=None,
        curve_title="Measured Thrust",
        curve_mode="thrust",
        results_title="Test Results",
        result_fields=None,
        event_visibility=None,
        curve_show_grid=True,
        curve_show_axes=True,
        curve_show_background=True,
        pdf_frame_position_s=None,
        display_mode="fit",
    ):
        self._loading_state = True
        try:
            self._set_pdf_frame_position(pdf_frame_position_s, emit=False)
            self.set_display_mode(display_mode)
            self._sync_offset_s = float(sync_offset_s or 0.0)
            self.sync_spin.setValue(self._sync_offset_s)
            self._show_curve = bool(show_curve)
            self._show_pressure_curve = bool(show_pressure)
            self._show_simulation = bool(show_simulation)
            self._show_results = bool(show_results)
            self._show_events = bool(show_events)
            # Older projects may still contain curve_mode; the new UI shows
            # independent thrust and pressure overlays instead.

            self.overlay.set_overlay_positions(
                curve_x,
                curve_y,
                results_x,
                results_y,
                curve_w,
                curve_h,
                results_w,
                results_h,
                event_positions,
            )
            self.overlay.set_pressure_overlay_position(
                pressure_x,
                pressure_y,
                pressure_w,
                pressure_h,
            )
            self.overlay.apply_configuration(
                curve_title=curve_title,
                results_title=results_title,
                result_fields=result_fields or [
                    "designation",
                    "peak_thrust",
                    "average_thrust",
                    "total_impulse",
                    "burn_time",
                ],
                event_visibility=event_visibility or {
                    "ignition": True,
                    "peak_thrust": True,
                    "burnout": True,
                },
                curve_show_grid=curve_show_grid,
                curve_show_axes=curve_show_axes,
                curve_show_background=curve_show_background,
            )
            self.overlay.set_visibility(
                show_curve,
                show_results,
                show_events,
                pressure=show_pressure,
            )

            if source_path:
                self.load_video(source_path, emit_signal=False)
            else:
                self.show_empty_state()
        finally:
            self._loading_state = False

    def set_analysis(
        self,
        times,
        thrust,
        pressure,
        thrust_results,
        classification,
        events,
        simulation_times=None,
        simulation_thrust=None,
        simulation_pressure=None,
    ):
        self._has_analysis = times is not None and thrust is not None
        self.overlay.set_analysis(
            times,
            thrust,
            pressure=pressure,
            thrust_results=thrust_results,
            classification=classification,
            events=events,
            simulation_times=simulation_times,
            simulation_thrust=simulation_thrust,
            simulation_pressure=simulation_pressure,
        )

        measured_pressure_available = (
            pressure is not None
            and np.asarray(pressure, dtype=float).size >= 2
        )
        simulation_pressure_available = self.overlay.has_simulation_for_mode("pressure")
        if not (measured_pressure_available or simulation_pressure_available):
            self._show_pressure_curve = False

        sim_available = (
            self.overlay.has_simulation_for_mode("thrust")
            or simulation_pressure_available
        )
        if not sim_available:
            self._show_simulation = False
        self.overlay.set_simulation_visible(self._show_simulation)

        self._update_overlay_time()
        self.overlay.set_visibility(
            self._show_curve,
            self._show_results,
            self._show_events,
            pressure=self._show_pressure_curve,
        )
        if self.is_loaded():
            self._video_container.sync_overlay_geometry()
            self.overlay.show()
            self.overlay.raise_()
        else:
            self.overlay.hide()

    def load_video(self, filename, emit_signal=True):
        path = Path(filename)
        if not path.exists():
            self.status_label.setText("Video file not found")
            self.remove_button.setEnabled(False)
            self.popout_button.setEnabled(False)
            return False

        self._playing = False
        self._priming_frame = False
        if self._priming_audio_volume is not None:
            self.audio.setVolume(self._priming_audio_volume)
            self._priming_audio_volume = None
        self.player.stop()
        self._video_duration_s = 0.0
        self.video_surface.clear_frame()
        self.overlay.hide()
        self.duration_changed.emit(0.0)

        self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self._video_name = path.name
        self.status_label.setText(path.name)
        self.status_label.setToolTip(str(path.resolve()))
        self.use_pdf_frame_button.setEnabled(True)
        self.clear_pdf_frame_button.setEnabled(self._pdf_frame_position_s is not None)
        self.remove_button.setEnabled(True)
        self.popout_button.setEnabled(True)

        if emit_signal:
            self.video_changed.emit(str(path.resolve()))
        return True

    def set_display_mode(self, mode):
        mode = str(mode or "fit").lower()
        if mode not in ("fit", "fill"):
            mode = "fit"
        self._display_mode = mode
        self.video_surface.set_display_mode(mode)
        self._video_container.sync_overlay_geometry()
        self.overlay.update()

    @property
    def display_mode(self):
        return self._display_mode

    def set_sync_offset(self, offset_s):
        self._loading_state = True
        try:
            self._sync_offset_s = float(offset_s or 0.0)
            self.sync_spin.setValue(self._sync_offset_s)
        finally:
            self._loading_state = False
        self._update_overlay_time()

    def _sync_changed(self, value):
        self._sync_offset_s = float(value)
        self._update_overlay_time()
        if not self._loading_state:
            self.sync_offset_changed.emit(self._sync_offset_s)

    def set_overlay_visibility(
        self,
        *,
        thrust=None,
        pressure=None,
        simulation=None,
        results=None,
        events=None,
        emit=True,
    ):
        """Set overlay layer visibility without exposing controls in the video pane."""
        if thrust is not None:
            self._show_curve = bool(thrust)
        if pressure is not None:
            self._show_pressure_curve = bool(pressure)
        if simulation is not None:
            self._show_simulation = bool(simulation)
        if results is not None:
            self._show_results = bool(results)
        if events is not None:
            self._show_events = bool(events)

        self.overlay.set_simulation_visible(self._show_simulation)
        self.overlay.set_visibility(
            self._show_curve,
            self._show_results,
            self._show_events,
            pressure=self._show_pressure_curve,
        )
        if self.is_loaded():
            self.overlay.show()
        else:
            self.overlay.hide()

        if emit and not self._loading_state:
            if thrust is not None or results is not None or events is not None:
                self.overlay_changed.emit(
                    self._show_curve,
                    self._show_results,
                    self._show_events,
                )
            if pressure is not None:
                self.pressure_overlay_changed.emit(self._show_pressure_curve)
            if simulation is not None:
                self.simulation_overlay_changed.emit(self._show_simulation)

    def _curve_mode_changed(self, index):
        # Retained for backward compatibility with older callers/projects.
        mode = "pressure" if str(index).lower() == "pressure" else "thrust"
        if not self._loading_state:
            self.curve_mode_changed.emit(mode)

    def _overlay_position_changed(self, *values):
        if not self._loading_state:
            self.overlay_positions_changed.emit(*values)

    def _pressure_overlay_position_changed(self, x, y, w, h):
        if not self._loading_state:
            self.pressure_overlay_positions_changed.emit(
                float(x), float(y), float(w), float(h)
            )

    def _overlay_event_position_changed(self, positions):
        if not self._loading_state:
            self.overlay_event_positions_changed.emit(positions)

    def _update_overlay_time(self):
        analysis_position_s = (
            self._timeline_position_s - self._sync_offset_s
            if self.is_loaded()
            else self._timeline_position_s
        )
        self.overlay.set_position(analysis_position_s)

    def set_timeline_position(self, position_s, force_video_seek=False):
        self._timeline_position_s = max(0.0, float(position_s or 0.0))
        self._update_overlay_time()

        if not self.is_loaded() or self._video_duration_s <= 0:
            return

        if self._playing and not force_video_seek:
            return

        self._seek_video_to_timeline()

    def _seek_video_to_timeline(self):
        if not self.is_loaded() or self._video_duration_s <= 0:
            return
        target_ms = int(
            round(
                max(
                    0.0,
                    min(
                        self._timeline_position_s,
                        self._video_duration_s,
                    ),
                )
                * 1000.0
            )
        )
        if abs(self.player.position() - target_ms) <= 45:
            return
        self.player.setPosition(target_ms)

    def set_playing(self, playing):
        self._playing = bool(playing)
        if not self.is_loaded():
            return
        if self._playing:
            self._seek_video_to_timeline()
            self.player.play()
        else:
            self.player.pause()

    def _on_video_frame(self, frame):
        self.video_surface.set_frame(frame)
        self._video_container.sync_overlay_geometry()

        if self._priming_frame:
            self._finish_priming_frame()

        if self._has_analysis and self.is_loaded():
            self.overlay.show()
            self.overlay.raise_()

    def _choose_video(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Test Video",
            "",
            self.SUPPORTED_FILTER,
        )
        if filename:
            self.load_video(filename)

    def _set_pdf_frame_position(self, position_s, emit=True):
        if position_s is None:
            self._pdf_frame_position_s = None
            self.pdf_frame_label.setText("PDF Report Frame: Automatic")
            self.clear_pdf_frame_button.setEnabled(self.is_loaded())
        else:
            try:
                value = max(0.0, float(position_s))
            except (TypeError, ValueError):
                value = None
            self._pdf_frame_position_s = value
            if value is None:
                self.pdf_frame_label.setText("PDF Report Frame: Automatic")
            else:
                self.pdf_frame_label.setText(f"PDF Report Frame: {value:.3f} s")
            self.clear_pdf_frame_button.setEnabled(self.is_loaded() and value is not None)
        if emit and not self._loading_state:
            self.pdf_frame_changed.emit(self._pdf_frame_position_s)

    def pdf_frame_position_s(self):
        return self._pdf_frame_position_s

    def use_current_frame_for_pdf(self):
        if not self.is_loaded():
            return
        position_s = self._timeline_position_s
        if self.is_loaded():
            media_position_s = self.player.position() / 1000.0
            if media_position_s > 0.0 or self._timeline_position_s <= 0.0:
                position_s = media_position_s
        self._set_pdf_frame_position(position_s, emit=True)

    def clear_pdf_frame(self):
        self._set_pdf_frame_position(None, emit=True)

    def _duration_changed(self, duration_ms):
        self._video_duration_s = max(0.0, duration_ms / 1000.0)
        self.duration_changed.emit(self._video_duration_s)
        if self._video_name and self._video_duration_s > 0.0:
            self.status_label.setText(
                f"{self._video_name}  •  {self._video_duration_s:.2f} s"
            )
        self.set_timeline_position(
            self._timeline_position_s,
            force_video_seek=True,
        )

    def _media_status_changed(self, status):
        """Refresh the overlay geometry once Qt has loaded the video source."""
        if status not in (
            QMediaPlayer.MediaStatus.LoadedMedia,
            QMediaPlayer.MediaStatus.BufferedMedia,
        ):
            return

        self._video_container.sync_overlay_geometry()
        if self._has_analysis and self.is_loaded():
            self.overlay.show()
            self.overlay.raise_()

        # QMediaPlayer may not deliver a decoded frame while paused. The
        # overlay needs the real video aspect ratio before its normalized
        # objects can be positioned correctly, so briefly prime one frame.
        if not self.video_surface._image.isNull():
            self._refresh_loaded_video_geometry()
        else:
            self._prime_video_frame()

    def _refresh_loaded_video_geometry(self):
        if not self.is_loaded():
            return
        self._video_container.sync_overlay_geometry()
        self.overlay.update()

    def _prime_video_frame(self):
        """Decode one frame so overlay geometry knows the video aspect ratio."""
        if not self.is_loaded() or self._priming_frame:
            return

        self._priming_frame = True
        self._priming_audio_volume = self.audio.volume()
        self.audio.setVolume(0.0)
        self.player.play()
        QTimer.singleShot(750, self._finish_priming_frame)

    def _finish_priming_frame(self):
        if not self._priming_frame:
            return
        self._priming_frame = False
        self.player.pause()
        if self._priming_audio_volume is not None:
            self.audio.setVolume(self._priming_audio_volume)
            self._priming_audio_volume = None
        self._video_container.sync_overlay_geometry()
        self.overlay.update()

    def _error_occurred(self, error, error_string):
        if error_string:
            self.status_label.setText(
                f"Video error: {error_string}"
            )

    def toggle_popout(self):
        if self._popout is not None:
            self.close_popout()
            return
        if not self.is_loaded():
            return

        self._video_layout.removeWidget(self._video_container)
        self._popout = VideoPopoutWindow(
            self._video_container,
            self,
        )
        self._popout.closed.connect(self._restore_docked)
        self.popout_button.setText("Dock")
        self._popout.show()
        self._popout.raise_()
        self._popout.activateWindow()

    def close_popout(self):
        if self._popout is not None:
            self._popout.close()

    def _restore_docked(self):
        dialog = self._popout
        if dialog is None:
            return
        self._popout = None
        self._video_container.setParent(self)
        self._video_layout.insertWidget(
            1,
            self._video_container,
            1,
        )
        self._video_container.show()
        self._video_container.sync_overlay_geometry()
        self.popout_button.setText("Pop Out")
        dialog.deleteLater()

    def apply_overlay_configuration(self, configuration):
        """Apply settings-dialog configuration to the current overlay."""
        self.set_display_mode(configuration.get("display_mode", self._display_mode))
        self.overlay.apply_configuration(
            curve_title=configuration["curve_title"],
            results_title=configuration["results_title"],
            result_fields=configuration["result_fields"],
            event_visibility=configuration["event_visibility"],
            curve_show_grid=configuration["curve_show_grid"],
            curve_show_axes=configuration["curve_show_axes"],
            curve_show_background=configuration.get("curve_show_background", True),
        )
        visibility = configuration.get("overlay_visibility", {})
        self.set_overlay_visibility(
            thrust=visibility.get("thrust", configuration.get("show_curve", self._show_curve)),
            pressure=visibility.get("pressure", configuration.get("show_pressure", self._show_pressure_curve)),
            simulation=visibility.get("simulation", configuration.get("show_simulation", self._show_simulation)),
            results=visibility.get("results", configuration.get("show_results", self._show_results)),
            events=visibility.get("events", configuration.get("show_events", self._show_events)),
            emit=True,
        )
        if not self._loading_state:
            self.overlay_configuration_changed.emit(
                self.overlay.configuration()
            )

    def overlay_configuration(self):
        configuration = self.overlay.configuration()
        configuration["overlay_visibility"] = {
            "thrust": self._show_curve,
            "pressure": self._show_pressure_curve,
            "simulation": self._show_simulation,
            "results": self._show_results,
            "events": self._show_events,
        }
        configuration["show_curve"] = self._show_curve
        configuration["show_pressure"] = self._show_pressure_curve
        configuration["show_simulation"] = self._show_simulation
        configuration["show_results"] = self._show_results
        configuration["show_events"] = self._show_events
        configuration["display_mode"] = self._display_mode
        return configuration

    def apply_event_positions(self, positions):
        self.overlay.set_overlay_positions(
            *self.overlay.overlay_positions()[:4],
            *self.overlay.overlay_positions()[4:],
            event_positions=positions,
        )

    @property
    def video_duration_s(self):
        return self._video_duration_s

    @property
    def sync_offset_s(self):
        return self._sync_offset_s

    def is_loaded(self):
        return self.player.source().isValid()
