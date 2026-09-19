from pathlib import Path

import numpy as np

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoFrame, QVideoSink
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
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
            self._scaled = self._image.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._scaled_size = rect.size()
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
    event_positions_changed = Signal(object)

    CURVE = QColor(77, 220, 255)
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
        self._show_results = True
        self._show_events = True

        self._curve = [0.06, 0.58, 0.58, 0.34]
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

    def set_analysis(self, times, thrust, thrust_results=None, classification=None, events=None):
        self._times = np.asarray(times, dtype=float) if times is not None else None
        self._thrust = np.asarray(thrust, dtype=float) if thrust is not None else None

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

    def set_visibility(self, curve, results, events):
        self._show_curve = bool(curve)
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

    def _results_rect(self):
        return self._rect(self._results)

    def _data(self):
        if self._times is None or self._thrust is None:
            return np.array([]), np.array([])
        mask = np.isfinite(self._times) & np.isfinite(self._thrust)
        return self._times[mask], self._thrust[mask]

    def _current_thrust(self):
        times, thrust = self._data()
        if len(times) == 0 or self._time < times[0]:
            return None
        return float(np.interp(self._time, times, thrust))

    def _format_metric(self, key):
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
    # Painting
    # ---------------------------------------------------------

    def paintEvent(self, event):
        if self._times is None or self._thrust is None or len(self._times) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._show_curve:
            self._paint_curve(painter)
        if self._show_results:
            self._paint_results(painter)
        if self._show_events:
            self._paint_events(painter)
        self._paint_selection(painter)

        painter.end()

    def _draw_shadow_text(self, painter, x, y, text, font, color=WHITE):
        painter.setFont(font)
        painter.setPen(self.SHADOW)
        painter.drawText(x + 2, y + 2, text)
        painter.setPen(color)
        painter.drawText(x, y, text)

    def _paint_curve(self, painter):
        times, thrust = self._data()
        if len(times) < 2:
            return

        t0 = float(times[0])
        t1 = float(times[-1])
        if t1 <= t0:
            return

        max_thrust = max(1.0, float(np.nanmax(thrust)))
        r = self._curve_rect()

        # Optional subtle chart background. This can be disabled in Settings
        # when the video itself provides enough contrast.
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
            self._curve_title,
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

        path = QPainterPath()
        for i, (t, value) in enumerate(zip(times, thrust)):
            x = plot.left() + (float(t) - t0) / (t1 - t0) * plot.width()
            y = plot.bottom() - float(value) / max_thrust * plot.height()
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        painter.setPen(
            QPen(
                self.CURVE,
                max(2, int(min(r.width(), r.height()) / 105)),
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        painter.drawPath(path)

        # Y-axis labels are deliberately placed outside the plot area so
        # they never sit on top of the thrust curve.
        axis_font = QFont(
            "Segoe UI",
            max(7, int(r.height() / 23)),
            QFont.Weight.Normal,
        )
        painter.setFont(axis_font)
        for fraction in (0.0, 0.5, 1.0):
            value = max_thrust * fraction
            y = plot.bottom() - int(fraction * plot.height())
            label = f"{value:.0f} N"
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

        # X-axis labels
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

        # Current playback marker.
        if self._time >= t0:
            tm = min(self._time, t1)
            tv = float(np.interp(tm, times, thrust))
            x = plot.left() + (tm - t0) / (t1 - t0) * plot.width()
            y = plot.bottom() - tv / max_thrust * plot.height()
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
        times, thrust = self._data()
        if len(times) < 2:
            return None
        t0, t1 = float(times[0]), float(times[-1])
        max_thrust = max(1.0, float(np.nanmax(thrust)))
        tm = max(t0, min(float(event_time), t1))
        tv = float(np.interp(tm, times, thrust))
        x = chart_rect.left() + (tm - t0) / (t1 - t0) * chart_rect.width()
        y = chart_rect.bottom() - tv / max_thrust * chart_rect.height()
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

        chart = self._curve_rect()
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
        elif self._selected == "results":
            rect = self._results_rect()
        elif self._selected.startswith("event:"):
            rect = self._event_label_rect(self._selected.split(":", 1)[1])
        else:
            return

        painter.setPen(QPen(self.SELECTION, 1, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        if self._selected in ("curve", "results"):
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

        if self._show_curve and self._curve_rect().contains(point):
            return "curve"

        return None

    def _resize_hit(self, point, target):
        if target not in ("curve", "results"):
            return False
        rect = self._curve_rect() if target == "curve" else self._results_rect()
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

            if target in ("curve", "results"):
                rect = (
                    self._curve_rect()
                    if target == "curve"
                    else self._results_rect()
                )
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
            box = (
                self._curve
                if self._resize_target == "curve"
                else self._results
            )
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
            self._emit_positions()
            event.accept()
            return

        if (
            self._drag_target
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            target = self._drag_target

            if target in ("curve", "results"):
                box = self._curve if target == "curve" else self._results
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
            event.accept()
            return

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_target = None
            self._resize_target = None
            self.update()
            event.accept()

    def _emit_positions(self):
        self.overlay_positions_changed.emit(*self.overlay_positions())


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
    overlay_positions_changed = Signal(float, float, float, float, float, float, float, float)
    overlay_event_positions_changed = Signal(object)
    overlay_configuration_changed = Signal(object)
    duration_changed = Signal(float)

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
        self._video_container.setMinimumHeight(150)
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

        options = QHBoxLayout()
        options.setSpacing(8)
        self.curve_check = QCheckBox("Curve")
        self.results_check = QCheckBox("Results")
        self.events_check = QCheckBox("Events")
        for checkbox in (self.curve_check, self.results_check, self.events_check):
            checkbox.setObjectName("videoOption")
            options.addWidget(checkbox)
        options.addStretch(1)

        self.sync_spin = QDoubleSpinBox()
        self.sync_spin.setObjectName("videoSyncSpin")
        self.sync_spin.setRange(-3600.0, 3600.0)
        self.sync_spin.setDecimals(3)
        self.sync_spin.setSingleStep(0.010)
        self.sync_spin.setSuffix(" s")
        self.sync_spin.setPrefix("Sync Start ")
        self.sync_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.sync_spin.setToolTip("Video time at which RMCS analysis t = 0 begins.")

        self.sync_up_button = QPushButton("▲")
        self.sync_down_button = QPushButton("▼")
        for button in (self.sync_up_button, self.sync_down_button):
            button.setObjectName("videoSyncStepButton")
            button.setFixedWidth(26)

        sync = QHBoxLayout()
        sync.setContentsMargins(0, 0, 0, 0)
        sync.setSpacing(2)
        sync.addWidget(self.sync_spin)
        sync.addWidget(self.sync_up_button)
        sync.addWidget(self.sync_down_button)
        options.addLayout(sync)
        layout.addLayout(options)

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(1.0)
        self.player.setAudioOutput(self.audio)
        self.video_sink = QVideoSink(self)
        self.video_sink.videoFrameChanged.connect(self._on_video_frame)
        self.player.setVideoSink(self.video_sink)
        self.player.durationChanged.connect(self._duration_changed)
        self.player.errorOccurred.connect(self._error_occurred)

        self.load_button.clicked.connect(self._choose_video)
        self.remove_button.clicked.connect(self.video_removed.emit)
        self.popout_button.clicked.connect(self.toggle_popout)
        self.sync_spin.valueChanged.connect(self._sync_changed)
        self.sync_up_button.clicked.connect(self.sync_spin.stepUp)
        self.sync_down_button.clicked.connect(self.sync_spin.stepDown)

        for checkbox in (
            self.curve_check,
            self.results_check,
            self.events_check,
        ):
            checkbox.toggled.connect(self._overlay_toggled)

        self.overlay.overlay_positions_changed.connect(
            self._overlay_position_changed
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

        self.player.stop()
        self.player.setSource(QUrl())
        self.status_label.setText("No video loaded")
        self.status_label.setToolTip("")
        self.remove_button.setEnabled(False)
        self.popout_button.setEnabled(False)
        self._video_duration_s = 0.0
        self._video_name = ""
        self._playing = False
        self.video_surface.clear_frame()
        self._has_analysis = False
        self.overlay.set_analysis(None, None)
        self.overlay.hide()
        self.duration_changed.emit(0.0)

    def set_video_state(
        self,
        source_path,
        sync_offset_s=0.0,
        show_curve=True,
        show_results=True,
        show_events=True,
        curve_x=0.06,
        curve_y=0.58,
        results_x=0.70,
        results_y=0.06,
        curve_w=0.58,
        curve_h=0.34,
        results_w=0.25,
        results_h=0.24,
        event_positions=None,
        curve_title="Measured Thrust",
        results_title="Test Results",
        result_fields=None,
        event_visibility=None,
        curve_show_grid=True,
        curve_show_axes=True,
        curve_show_background=True,
    ):
        self._loading_state = True
        try:
            self._sync_offset_s = float(sync_offset_s or 0.0)
            self.sync_spin.setValue(self._sync_offset_s)
            self.curve_check.setChecked(bool(show_curve))
            self.results_check.setChecked(bool(show_results))
            self.events_check.setChecked(bool(show_events))

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
        thrust_results,
        classification,
        events,
    ):
        self._has_analysis = times is not None and thrust is not None
        self.overlay.set_analysis(
            times,
            thrust,
            thrust_results,
            classification,
            events,
        )
        self._update_overlay_time()
        self.overlay.set_visibility(
            self.curve_check.isChecked(),
            self.results_check.isChecked(),
            self.events_check.isChecked(),
        )
        if self.is_loaded():
            self.overlay.show()
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
        self.player.stop()
        self._video_duration_s = 0.0
        self.video_surface.clear_frame()
        self.overlay.hide()
        self.duration_changed.emit(0.0)

        self.player.setSource(QUrl.fromLocalFile(str(path.resolve())))
        self._video_name = path.name
        self.status_label.setText(path.name)
        self.status_label.setToolTip(str(path.resolve()))
        self.remove_button.setEnabled(True)
        self.popout_button.setEnabled(True)

        if emit_signal:
            self.video_changed.emit(str(path.resolve()))
        return True

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

    def _overlay_toggled(self):
        values = (
            self.curve_check.isChecked(),
            self.results_check.isChecked(),
            self.events_check.isChecked(),
        )
        self.overlay.set_visibility(*values)
        if self.is_loaded():
            self.overlay.show()
        else:
            self.overlay.hide()
        if not self._loading_state:
            self.overlay_changed.emit(*values)

    def _overlay_position_changed(self, *values):
        if not self._loading_state:
            self.overlay_positions_changed.emit(*values)

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
        if self._has_analysis and self.is_loaded():
            self.overlay.show()
            self._video_container.sync_overlay_geometry()

    def _choose_video(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Test Video",
            "",
            self.SUPPORTED_FILTER,
        )
        if filename:
            self.load_video(filename)

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
        self.overlay.apply_configuration(
            curve_title=configuration["curve_title"],
            results_title=configuration["results_title"],
            result_fields=configuration["result_fields"],
            event_visibility=configuration["event_visibility"],
            curve_show_grid=configuration["curve_show_grid"],
            curve_show_axes=configuration["curve_show_axes"],
            curve_show_background=configuration.get("curve_show_background", True),
        )
        if not self._loading_state:
            self.overlay_configuration_changed.emit(
                self.overlay.configuration()
            )

    def overlay_configuration(self):
        return self.overlay.configuration()

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
