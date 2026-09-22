"""Professional campaign and test PDF reports for RMCS Analyzer.

The report is built from the authoritative TestSession/TestModel and
AnalysisResults objects.  Engineering calculations are not duplicated here.
Optional sections are omitted when their source data does not exist.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterable, Optional

from PIL import Image as PILImage
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


APP_VERSION = "0.4.0"
PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.55 * inch

NAVY = colors.HexColor("#08131D")
PANEL = colors.HexColor("#0D1B26")
PANEL_2 = colors.HexColor("#122532")
BLUE = colors.HexColor("#1598FF")
CYAN = colors.HexColor("#4DDCFF")
YELLOW = colors.HexColor("#FFD45A")
MUTED = colors.HexColor("#7FA4C8")
WHITE = colors.HexColor("#F2F6FA")
TEXT = colors.HexColor("#DCE8F2")
GRID = colors.HexColor("#29404F")
GREEN = colors.HexColor("#39D98A")
RED = colors.HexColor("#FF5A64")


class PDFReportError(RuntimeError):
    """Raised when an RMCS Analyzer PDF report cannot be generated."""


def _fmt(value, unit="", decimals=2, unavailable="—") -> str:
    if value is None:
        return unavailable
    try:
        text = f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        text = str(value)
    return f"{text} {unit}".strip()


def _total_impulse_value(test):
    """Return the current authoritative RMCS total impulse value.

    The performance analysis introduced ``total_impulse_valid_curve_Ns`` as
    the standardized total-impulse result used by campaign analysis and
    classification.  Keep a fallback for older project data.
    """
    analysis = getattr(test, "analysis_results", None)
    thrust = getattr(analysis, "thrust", None) if analysis is not None else None
    if thrust is None:
        return None
    value = getattr(thrust, "total_impulse_valid_curve_Ns", None)
    if value is None:
        value = getattr(thrust, "total_impulse_Ns", None)
    return value


def _clean(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _escape(value) -> str:
    return (
        _clean(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _metadata_rows(test) -> list[tuple[str, str]]:
    rows = []
    analysis = test.analysis_results
    pairs = [
        ("Test Number", test.test_number),
        ("Motor Designation", test.motor_designation),
        ("Calculated Designation", getattr(analysis.thrust, "designation", None) if analysis else None),
        ("Motor Type", test.motor_type),
        ("Manufacturer", test.manufacturer),
        ("Builder", test.builder),
        ("Case Material", test.case_material),
        ("Test Date", test.test_date),
        ("Test Stand", test.test_stand),
        ("Test Operator", test.test_operator),
        ("Location", test.location),
        ("Motor Diameter", _fmt(test.motor_diameter_mm, "mm")),
        ("Motor Length", _fmt(test.motor_length_mm, "mm")),
        ("Initial Mass", _fmt(test.initial_mass_g, "g")),
        ("Propellant Mass", _fmt(test.propellant_mass_g, "g")),
        ("Propellant Type", test.propellant_type),
        ("Nozzle Throat", _fmt(test.nozzle_throat_in, "in", 4)),
        ("Nozzle Exit", _fmt(test.nozzle_exit_in, "in", 4)),
        ("Nozzle Material", test.nozzle_material),
        ("Load Cell", test.load_cell),
        ("Load Cell Calibration", test.load_cell_calibration),
        ("Pressure Sensor", test.pressure_sensor),
        ("Pressure Calibration", test.pressure_sensor_calibration),
        ("Case Pressure Limit", _fmt(test.case_pressure_limit_psi, "psi")),
        ("Sample Rate", _fmt(test.sample_rate_hz, "SPS", 2)),
    ]
    for label, value in pairs:
        text = _clean(value)
        if text and text != "—":
            rows.append((label, text))
    return rows


def _metric_rows(test) -> list[tuple[str, str]]:
    analysis = test.analysis_results
    if analysis is None:
        return []
    thrust = analysis.thrust
    classification = analysis.classification
    rows = [
        ("Motor Class", classification.motor_class),
        ("Total Impulse", _fmt(_total_impulse_value(test), "N·s")),
        ("Normalized Impulse", _fmt(thrust.normalized_impulse_Ns, "N·s")),
        ("Peak Thrust", _fmt(thrust.peak_thrust_N, "N")),
        ("Average Thrust", _fmt(
            thrust.average_thrust_5pct_N
            if thrust.average_thrust_5pct_N is not None
            else thrust.average_thrust_N,
            "N",
        )),
        ("Burn Time", _fmt(thrust.burn_time_5pct_s or thrust.burn_time_s, "s")),
        ("Time to Peak", _fmt(thrust.time_to_peak_s, "s")),
        ("Isp", _fmt(thrust.isp_s, "s")),
        ("C*", _fmt(thrust.cstar_m_per_s, "m/s")),
        ("Initial Thrust", _fmt(thrust.initial_thrust_average_N, "N")),
        ("Thrust Rise Rate", _fmt(thrust.thrust_rise_rate_N_per_s, "N/s")),
        ("Thrust Decay Rate", _fmt(thrust.thrust_decay_rate_N_per_s, "N/s")),
        ("Avg. Chamber Pressure", _fmt(thrust.average_chamber_pressure_psi, "psi")),
        ("Avg. Mass Flow", _fmt(thrust.average_mass_flow_kg_per_s, "kg/s", 4)),
    ]
    return [(label, value) for label, value in rows if _clean(value) and value != "—"]


def _event_rows(test) -> list[tuple[str, str]]:
    analysis = test.analysis_results
    if analysis is None or analysis.events is None:
        return []
    rows = []
    for label, event in (
        ("Ignition", analysis.events.ignition),
        ("Peak Thrust", analysis.events.peak_thrust),
        ("Burnout", analysis.events.burnout),
    ):
        if event is not None:
            rows.append((label, _fmt(event.time_s, "s", 3)))
    return rows


def _table(data: list[tuple[str, str]], widths=None) -> Table:
    if not data:
        return Table([[]])
    table = Table([[label, value] for label, value in data], colWidths=widths, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [PANEL, PANEL_2]),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, GRID),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), WHITE),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.4),
        ("LEADING", (0, 0), (-1, -1), 8.8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    return table


def _four_column_table(data, widths, font_size=7.0) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PANEL_2),
        ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
        ("BACKGROUND", (0, 1), (-1, -1), PANEL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PANEL, PANEL_2]),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, GRID),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 2),
        ("TEXTCOLOR", (0, 1), (-1, -1), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def _two_column_table(rows: list[tuple[str, str]], available_width: float) -> Table:
    midpoint = (len(rows) + 1) // 2
    left = rows[:midpoint]
    right = rows[midpoint:]
    count = max(len(left), len(right))
    data = []
    label_style = ParagraphStyle("TwoColLabel", fontName="Helvetica-Bold", fontSize=6.8, leading=8, textColor=MUTED)
    value_style = ParagraphStyle("TwoColValue", fontName="Helvetica", fontSize=6.8, leading=8, textColor=WHITE)
    for index in range(count):
        l = left[index] if index < len(left) else ("", "")
        r = right[index] if index < len(right) else ("", "")
        data.append([
            Paragraph(_escape(l[0]), label_style),
            Paragraph(_escape(l[1]), value_style),
            Paragraph(_escape(r[0]), label_style),
            Paragraph(_escape(r[1]), value_style),
        ])
    table = Table(data, colWidths=[1.32 * inch, 1.65 * inch, 1.32 * inch, 1.65 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [PANEL, PANEL_2]),
        ("BOX", (0, 0), (-1, -1), 0.5, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, GRID),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (2, 0), (2, -1), MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), WHITE),
        ("TEXTCOLOR", (3, 0), (3, -1), WHITE),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6.7),
        ("LEADING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
    ]))
    return table


def _fig_to_reportlab_image(fig, *, max_width=7.25 * inch, max_height=None) -> Image:
    """Convert a Matplotlib figure to a ReportLab image without distortion."""
    buffer = BytesIO()
    fig.savefig(
        buffer,
        format="png",
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
        pad_inches=0.06,
    )
    plt.close(fig)
    buffer.seek(0)

    # Read the rendered PNG dimensions and preserve its native aspect ratio.
    with PILImage.open(buffer) as rendered:
        pixel_width, pixel_height = rendered.size
    if pixel_width <= 0 or pixel_height <= 0:
        raise PDFReportError("Generated chart image has invalid dimensions.")

    aspect = pixel_width / pixel_height
    draw_width = float(max_width)
    draw_height = draw_width / aspect
    if max_height is not None and draw_height > max_height:
        draw_height = float(max_height)
        draw_width = draw_height * aspect

    buffer.seek(0)
    image = Image(buffer)
    image.drawWidth = draw_width
    image.drawHeight = draw_height
    return image


def _chart_image(
    time_s: np.ndarray,
    measured: np.ndarray,
    *,
    ylabel: str,
    title: str,
    simulation_time: Optional[np.ndarray] = None,
    simulation: Optional[np.ndarray] = None,
    events: Optional[Iterable[tuple[str, float, object]]] = None,
    max_height=2.45 * inch,
) -> Image:
    # Deliberately use a near-3:1 figure ratio. The rendered image is then
    # placed using its actual PNG dimensions, so ReportLab cannot stretch it.
    fig, ax = plt.subplots(figsize=(8.8, 2.95), dpi=160)
    fig.patch.set_facecolor("#08131D")
    ax.set_facecolor("#08131D")
    ax.plot(time_s, measured, color="#4DDCFF", linewidth=2.0, label="Measured", zorder=3)
    if simulation_time is not None and simulation is not None and len(simulation_time):
        ax.plot(simulation_time, simulation, color="#FFD45A", linewidth=1.6, linestyle="--", label="Simulation", zorder=2)
    if events:
        for label, event_time, color in events:
            if event_time is None:
                continue
            ax.axvline(float(event_time), color=color, linewidth=0.9, linestyle="--", alpha=0.85)
            ax.text(float(event_time), 0.96, label, transform=ax.get_xaxis_transform(), color=color, fontsize=7.2, ha="left", va="top", clip_on=True)
    ax.set_title(title, color="#F2F6FA", fontsize=11.5, fontweight="bold", loc="left", pad=8)
    ax.set_xlabel("Time (s)", color="#B8CCDB", fontsize=8.2)
    ax.set_ylabel(ylabel, color="#B8CCDB", fontsize=8.2)
    ax.tick_params(colors="#9FB5C5", labelsize=7.2)
    for spine in ax.spines.values():
        spine.set_color("#29404F")
    ax.grid(True, color="#29404F", alpha=0.42, linewidth=0.55)
    ax.margins(x=0.01)
    if simulation_time is not None and simulation is not None and len(simulation_time):
        legend = ax.legend(loc="upper right", frameon=False, fontsize=7.2)
        for text in legend.get_texts():
            text.set_color("#DCE8F2")
    fig.tight_layout(pad=0.8)
    return _fig_to_reportlab_image(fig, max_height=max_height)

def _campaign_curve_image(curve, title="Campaign Thrust Comparison") -> Image:
    fig, ax = plt.subplots(figsize=(8.8, 3.65), dpi=160)
    fig.patch.set_facecolor("#08131D")
    ax.set_facecolor("#08131D")
    overlap_mask = curve.sample_count >= max(2, int(np.ceil(curve.test_count * 0.5)))
    overlap_indices = np.flatnonzero(overlap_mask)
    common_end_time = float(curve.time[overlap_indices[-1]]) if overlap_indices.size else None
    for x, y in curve.individual_curves:
        valid = np.isfinite(x) & np.isfinite(y)
        if common_end_time is not None:
            valid &= x <= common_end_time
        if np.any(valid):
            ax.plot(x[valid], y[valid], color="#4DDCFF", alpha=0.14, linewidth=0.8)
    mean = np.asarray(curve.mean, dtype=float).copy()
    minimum = np.asarray(curve.minimum, dtype=float).copy()
    maximum = np.asarray(curve.maximum, dtype=float).copy()
    mean[~overlap_mask] = np.nan
    minimum[~overlap_mask] = np.nan
    maximum[~overlap_mask] = np.nan
    ax.plot(curve.time, mean, color="#FFD45A", linewidth=2.2, label="Campaign Mean", zorder=4)
    if np.any(np.isfinite(minimum)) and np.any(np.isfinite(maximum)):
        ax.fill_between(curve.time, minimum, maximum, color="#1598FF", alpha=0.10, label="Min / Max")
    ax.set_title(title, color="#F2F6FA", fontsize=12, fontweight="bold", loc="left", pad=10)
    ax.set_xlabel("Burn Time (s)" if curve.basis == "absolute" else "Normalized Burn Time", color="#B8CCDB", fontsize=8.5)
    ax.set_ylabel("Thrust (N)", color="#B8CCDB", fontsize=8.5)
    ax.tick_params(colors="#9FB5C5", labelsize=7.5)
    for spine in ax.spines.values():
        spine.set_color("#29404F")
    ax.grid(True, color="#29404F", alpha=0.42, linewidth=0.55)
    legend = ax.legend(loc="upper right", frameon=False, fontsize=7.5)
    for text in legend.get_texts():
        text.set_color("#DCE8F2")
    fig.tight_layout(pad=1.0)
    return _fig_to_reportlab_image(fig, max_height=3.55 * inch)

def _campaign_metric_image(tests, attribute, unit, title) -> Optional[Image]:
    usable = []
    for test in tests:
        if test.analysis_results is None:
            continue
        value = getattr(test.analysis_results.thrust, attribute, None)
        if value is None:
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if np.isfinite(value):
            usable.append((test.display_name, value))
    if not usable:
        return None
    labels = [x[0] for x in usable]
    values = [x[1] for x in usable]
    fig, ax = plt.subplots(figsize=(8.8, 3.15), dpi=160)
    fig.patch.set_facecolor("#08131D")
    ax.set_facecolor("#08131D")
    x = np.arange(len(values))
    ax.bar(x, values, color="#1598FF", alpha=0.82, width=0.62)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=22, ha="right", color="#B8CCDB", fontsize=7.3)
    ax.set_ylabel(unit, color="#B8CCDB", fontsize=8.5)
    ax.set_title(title, color="#F2F6FA", fontsize=12, fontweight="bold", loc="left", pad=10)
    ax.tick_params(axis="y", colors="#9FB5C5", labelsize=7.5)
    for spine in ax.spines.values():
        spine.set_color("#29404F")
    ax.grid(axis="y", color="#29404F", alpha=0.42, linewidth=0.55)
    fig.tight_layout(pad=1.0)
    return _fig_to_reportlab_image(fig, max_height=3.55 * inch)

def _campaign_pressure_image(tests) -> Optional[Image]:
    usable = []
    for test in tests:
        data = test.data
        if data.pressure_psi is None or len(data.pressure_psi) != len(data.time_s):
            continue
        usable.append(test)
    if not usable:
        return None
    fig, ax = plt.subplots(figsize=(8.8, 3.45), dpi=160)
    fig.patch.set_facecolor("#08131D")
    ax.set_facecolor("#08131D")
    for test in usable:
        label = test.display_name
        ax.plot(test.data.time_s, test.data.pressure_psi, linewidth=1.25, alpha=0.72, label=label)
    ax.set_title("Campaign Pressure Comparison", color="#F2F6FA", fontsize=12, fontweight="bold", loc="left", pad=10)
    ax.set_xlabel("Time (s)", color="#B8CCDB", fontsize=8.5)
    ax.set_ylabel("Pressure (psi)", color="#B8CCDB", fontsize=8.5)
    ax.tick_params(colors="#9FB5C5", labelsize=7.5)
    for spine in ax.spines.values():
        spine.set_color("#29404F")
    ax.grid(True, color="#29404F", alpha=0.42, linewidth=0.55)
    legend = ax.legend(loc="upper right", frameon=False, fontsize=6.5)
    for text in legend.get_texts():
        text.set_color("#DCE8F2")
    fig.tight_layout(pad=1.0)
    return _fig_to_reportlab_image(fig, max_height=3.55 * inch)

def _event_tuples(test):
    analysis = test.analysis_results
    if analysis is None:
        return []
    result = []
    if analysis.events.ignition is not None:
        result.append(("Ignition", analysis.events.ignition.time_s, "#39D98A"))
    if analysis.events.peak_thrust is not None:
        result.append(("Peak", analysis.events.peak_thrust.time_s, "#1598FF"))
    burnout = analysis.thrust.burn_end_5pct_time_s
    if burnout is not None:
        result.append(("Burn End", burnout, "#FF5A64"))
    return result


def _build_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("ReportTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=27, leading=30, textColor=WHITE, alignment=TA_LEFT, spaceAfter=8),
        "subtitle": ParagraphStyle("ReportSubtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=11, leading=14, textColor=MUTED, spaceAfter=5),
        "section": ParagraphStyle("Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=WHITE, spaceBefore=3, spaceAfter=8),
        "subsection": ParagraphStyle("Subsection", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=TEXT, spaceBefore=4, spaceAfter=6),
        "body": ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.8, leading=12, textColor=TEXT, spaceAfter=6),
        "small": ParagraphStyle("Small", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.5, leading=10, textColor=MUTED, spaceAfter=4),
        "note": ParagraphStyle("Note", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=8.2, leading=11, textColor=MUTED, spaceAfter=5),
        "kpi": ParagraphStyle("KPI", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=13, leading=15, textColor=WHITE, alignment=TA_CENTER),
        "kpilabel": ParagraphStyle("KPILabel", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.2, leading=9, textColor=MUTED, alignment=TA_CENTER),
    }


def _kpi_table(test, styles):
    analysis = test.analysis_results
    if analysis is None:
        return None
    thrust = analysis.thrust
    values = [
        ("TOTAL IMPULSE", _fmt(_total_impulse_value(test), "N·s")),
        ("PEAK THRUST", _fmt(thrust.peak_thrust_N, "N")),
        ("BURN TIME", _fmt(thrust.burn_time_5pct_s or thrust.burn_time_s, "s")),
        ("MOTOR CLASS", analysis.classification.motor_class or "—"),
    ]
    data = [[Paragraph(label, styles["kpilabel"]), Paragraph(value, styles["kpi"])] for label, value in values]
    table = Table([data], colWidths=[1.75 * inch] * 4)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), 0.7, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return table


def _campaign_kpi_table(tests, styles):
    analyzed = [t for t in tests if t.analysis_results is not None]
    if not analyzed:
        return None
    total_impulse = [_total_impulse_value(t) for t in analyzed if _total_impulse_value(t) is not None]
    peak = [t.analysis_results.thrust.peak_thrust_N for t in analyzed if t.analysis_results.thrust.peak_thrust_N is not None]
    burn = [t.analysis_results.thrust.burn_time_5pct_s or t.analysis_results.thrust.burn_time_s for t in analyzed]
    burn = [x for x in burn if x is not None]
    values = [
        ("TESTS", str(len(tests))),
        ("ANALYZED", str(len(analyzed))),
        ("MEAN IMPULSE", _fmt(np.mean(total_impulse), "N·s") if total_impulse else "—"),
        ("MEAN PEAK THRUST", _fmt(np.mean(peak), "N") if peak else "—"),
    ]
    data = [[Paragraph(label, styles["kpilabel"]), Paragraph(value, styles["kpi"])] for label, value in values]
    table = Table([data], colWidths=[1.75 * inch] * 4)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), 0.7, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return table


def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 0.42 * inch, PAGE_WIDTH - MARGIN, 0.42 * inch)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, 0.25 * inch, f"RMCS Analyzer v{APP_VERSION} • Rocket Motor Characterization System")
    canvas.drawRightString(PAGE_WIDTH - MARGIN, 0.25 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _video_frame_image(test) -> Optional[tuple[Image, str]]:
    """Extract the selected or representative video frame using Qt Multimedia.

    The decoder intentionally runs forward from the beginning of the video
    instead of seeking directly to the requested timestamp. Direct seeks are
    backend-dependent for some MP4/H.264 files and can fail to deliver a
    decoded frame on some Windows Qt multimedia backends. Forward decoding
    uses the same QMediaPlayer/QVideoSink stack as the Video Analysis panel
    and is reliable for the short test videos used by RMCS.
    """
    source = _clean(getattr(getattr(test, "video", None), "source_path", ""))
    if not source:
        return None

    path = Path(source)
    if not path.exists() or not path.is_file():
        return None

    try:
        from PySide6.QtCore import (
            QByteArray,
            QBuffer,
            QEventLoop,
            QIODevice,
            QTimer,
            QUrl,
        )
        from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink
        from PySide6.QtWidgets import QApplication
    except Exception:
        return None

    if QApplication.instance() is None:
        return None

    selected_video_s = getattr(test.video, "pdf_frame_position_s", None)
    selected = selected_video_s is not None

    if selected:
        target_video_s = max(0.0, float(selected_video_s))
    else:
        target_analysis_s = 0.0
        analysis = test.analysis_results
        if analysis is not None:
            if analysis.events.ignition is not None:
                target_analysis_s = float(analysis.events.ignition.time_s)
            elif analysis.events.peak_thrust is not None:
                target_analysis_s = float(analysis.events.peak_thrust.time_s)
            elif analysis.thrust.burn_start_5pct_time_s is not None:
                target_analysis_s = float(analysis.thrust.burn_start_5pct_time_s)

        sync_offset = float(getattr(test.video, "sync_offset_s", 0.0) or 0.0)
        target_video_s = max(0.0, target_analysis_s + sync_offset)

    player = QMediaPlayer()
    audio = QAudioOutput()
    audio.setVolume(0.0)
    sink = QVideoSink()
    player.setAudioOutput(audio)
    player.setVideoSink(sink)

    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)

    captured = {
        "image": None,
        "position": 0.0,
        "distance": float("inf"),
    }
    finished = {"value": False}
    started = {"value": False}

    def finish():
        if finished["value"]:
            return
        finished["value"] = True
        if loop.isRunning():
            loop.quit()

    def on_status(status):
        try:
            if status in (
                QMediaPlayer.MediaStatus.LoadedMedia,
                QMediaPlayer.MediaStatus.BufferedMedia,
            ):
                if not started["value"]:
                    started["value"] = True
                    # Decode forward from the beginning. Avoid a non-zero seek
                    # because some Windows MP4/H.264 backends do not reliably
                    # emit video frames after seeking.
                    player.setPosition(0)
                    player.play()
            elif status == QMediaPlayer.MediaStatus.EndOfMedia:
                finish()
            elif status == QMediaPlayer.MediaStatus.InvalidMedia:
                finish()
        except Exception:
            finish()

    def on_frame(frame):
        if not frame.isValid():
            return

        try:
            image = frame.toImage()
        except Exception:
            return
        if image.isNull():
            return

        frame_time_s = player.position() / 1000.0
        try:
            start_time = frame.startTime()
            if start_time is not None and start_time >= 0:
                frame_time_s = max(
                    frame_time_s,
                    float(start_time) / 1_000_000.0,
                )
        except Exception:
            pass

        distance = abs(frame_time_s - target_video_s)
        if distance < captured["distance"]:
            captured["image"] = image
            captured["position"] = frame_time_s
            captured["distance"] = distance

        # Once a frame at or beyond the requested point has been decoded,
        # the closest frame observed so far is the best available match.
        if frame_time_s >= target_video_s:
            finish()

    player.mediaStatusChanged.connect(on_status)
    sink.videoFrameChanged.connect(on_frame)
    timer.timeout.connect(finish)

    # Prevent a broken media backend from hanging the export indefinitely.
    timer.start(15000)
    player.setSource(QUrl.fromLocalFile(str(path.resolve())))
    loop.exec()

    try:
        player.stop()
        player.deleteLater()
        audio.deleteLater()
        sink.deleteLater()
        timer.deleteLater()
    except Exception:
        pass

    image = captured["image"]
    if image is None:
        return None

    image_bytes = QByteArray()
    qt_buffer = QBuffer(image_bytes)
    if not qt_buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        return None
    try:
        saved = image.save(qt_buffer, "PNG")
    finally:
        qt_buffer.close()
    if not saved:
        return None

    report_buffer = BytesIO(bytes(image_bytes))
    report_image = Image(report_buffer)

    aspect = image.width() / image.height() if image.height() else 16 / 9
    max_w = 7.25 * inch
    max_h = 6.15 * inch
    if aspect >= (max_w / max_h):
        draw_w = max_w
        draw_h = max_w / aspect
    else:
        draw_h = max_h
        draw_w = max_h * aspect

    report_image.drawWidth = draw_w
    report_image.drawHeight = draw_h

    target_analysis_s = target_video_s - float(
        getattr(test.video, "sync_offset_s", 0.0) or 0.0
    )
    label = "Selected PDF frame" if selected else "Representative video frame"
    caption = (
        f"{label} • analysis t = {target_analysis_s:.3f} s • "
        f"video t = {captured['position']:.3f} s"
    )
    return report_image, caption


def _add_test_report(story, test, simulation, styles, *, include_heading=True, include_page_break=False, compact_single=False):
    """Append a complete individual-test report.

    Multi-test campaigns use a predictable two-page test layout:
      page 1: measured thrust, metadata, pressure
      page 2: simulation comparison and engineering results

    A one-test campaign uses the same information but allows pressure to flow
    onto the analysis page instead of creating a mostly empty standalone page.
    Video evidence remains a dedicated page so the selected/representative
    frame always has enough room and its aspect ratio is preserved.
    """
    if include_page_break:
        story.append(PageBreak())

    analysis = test.analysis_results
    data = test.data
    if include_heading:
        designation = (analysis.thrust.designation if analysis else None) or test.motor_designation or test.display_name
        if compact_single:
            story.append(Paragraph("Measured Test", styles["section"]))
        else:
            story.append(Paragraph("Individual Test Report", styles["section"]))
            story.append(Paragraph(_escape(f"{test.display_name} • {designation}"), styles["subtitle"]))
            story.append(HRFlowable(width="100%", thickness=1.0, color=BLUE, spaceBefore=3, spaceAfter=10))

    if analysis is None:
        story.append(Paragraph("Analysis Results", styles["subsection"]))
        story.append(Paragraph("This test is loaded in the campaign but does not have completed analysis results. Available imported test metadata is included below.", styles["body"]))
        summary_rows = _metadata_rows(test)
        if summary_rows:
            story.append(_two_column_table(summary_rows, 7.25 * inch))
        return

    thrust = analysis.thrust
    kpis = _kpi_table(test, styles)
    if kpis:
        story.append(kpis)
        story.append(Spacer(1, 0.08 * inch))

    # Measured thrust profile.
    if len(data.time_s) and len(data.thrust_N):
        story.append(_chart_image(
            np.asarray(data.time_s), np.asarray(data.thrust_N),
            ylabel="Thrust (N)", title="Measured Thrust Profile",
            simulation_time=None, simulation=None,
            events=_event_tuples(test), max_height=2.18 * inch,
        ))
        story.append(Spacer(1, 0.05 * inch))

    summary_rows = _metadata_rows(test)
    if summary_rows:
        story.append(Paragraph("Test Summary", styles["subsection"]))
        story.append(_two_column_table(summary_rows, 7.25 * inch))

    pressure_available = data.pressure_psi is not None and len(data.pressure_psi)
    if pressure_available:
        # For a single-test report the pressure section starts the analysis
        # page. This prevents an orphan heading while using the page for the
        # simulation/engineering content that follows it.
        if compact_single:
            story.append(PageBreak())
        else:
            story.append(Spacer(1, 0.08 * inch))

        finite = np.asarray(data.pressure_psi, dtype=float)
        finite = finite[np.isfinite(finite)]
        story.append(Paragraph("Pressure Analysis", styles["subsection"]))
        story.append(_chart_image(
            np.asarray(data.time_s), np.asarray(data.pressure_psi),
            ylabel="Pressure (psi)", title="Measured Chamber Pressure vs. Time",
            simulation_time=None, simulation=None,
            events=_event_tuples(test), max_height=1.50 * inch if compact_single else 2.02 * inch,
        ))
        pressure_rows = []
        if finite.size:
            pressure_rows.append(("Peak Recorded Pressure", _fmt(float(np.max(finite)), "psi")))
        if thrust.average_chamber_pressure_psi is not None:
            pressure_rows.append(("Avg. Chamber Pressure", _fmt(thrust.average_chamber_pressure_psi, "psi")))
        if pressure_rows:
            story.append(_table(pressure_rows, widths=[2.15 * inch, 5.10 * inch]))

    # In multi-test reports this begins the intentionally separate analysis
    # page. In a one-test report it follows pressure directly on the same page.
    if not compact_single:
        story.append(PageBreak())

    if simulation is not None and (simulation.has_thrust or simulation.has_pressure):
        story.append(Paragraph("Simulation Comparison", styles["section"]))
        sim_name = _escape(simulation.metadata.simulator or "Imported simulation")
        story.append(Paragraph(
            f"Reference simulation: <b>{sim_name}</b>. Simulation data is shown as a comparison layer and does not replace measured RMCS test data.",
            styles["body"],
        ))
        if simulation.has_thrust and len(data.thrust_N):
            story.append(_chart_image(
                np.asarray(data.time_s), np.asarray(data.thrust_N),
                ylabel="Thrust (N)", title="Measured vs. Simulated Thrust",
                simulation_time=np.asarray(simulation.time_s), simulation=np.asarray(simulation.thrust_N),
                events=_event_tuples(test), max_height=1.65 * inch if compact_single else 2.48 * inch,
            ))
            story.append(Spacer(1, 0.04 * inch))
        if simulation.has_pressure and data.pressure_psi is not None:
            story.append(_chart_image(
                np.asarray(data.time_s), np.asarray(data.pressure_psi),
                ylabel="Pressure (psi)", title="Measured vs. Simulated Pressure",
                simulation_time=np.asarray(simulation.time_s), simulation=np.asarray(simulation.pressure_psi),
                events=_event_tuples(test), max_height=1.65 * inch if compact_single else 2.48 * inch,
            ))
        story.append(Spacer(1, 0.05 * inch))

    story.append(Paragraph("Engineering Analysis", styles["section"]))
    metric_rows = _metric_rows(test)
    if metric_rows:
        story.append(_two_column_table(metric_rows, 7.25 * inch))

    event_rows = _event_rows(test)
    if event_rows:
        story.append(Spacer(1, 0.07 * inch))
        story.append(Paragraph("Detected Events", styles["subsection"]))
        story.append(_table(event_rows, widths=[2.65 * inch, 4.60 * inch]))

    story.append(Spacer(1, 0.05 * inch))
    story.append(Paragraph("Data Quality and Acquisition", styles["subsection"]))
    acquisition_rows = [
        ("Samples", str(data.sample_count)),
        ("Estimated Sample Rate", _fmt(data.sample_rate_hz, "SPS", 2)),
        ("Recording Duration", _fmt(data.duration_s, "s", 3)),
    ]
    if data.pressure_psi is not None:
        acquisition_rows.append(("Pressure Channel", "Available"))
    if simulation is not None:
        acquisition_rows.append(("Simulation", "Available"))
    if test.source_file and not compact_single:
        acquisition_rows.append(("Source File", Path(test.source_file).name))

    if compact_single:
        # A one-test report should keep acquisition details on the analysis
        # page instead of allowing a small table to spill onto a mostly empty
        # third page before the optional video evidence page.
        quality_parts = []
        for label, value in acquisition_rows:
            quality_parts.append(f"<b>{_escape(label)}:</b> {_escape(value)}")
        story.append(Paragraph(" • ".join(quality_parts), styles["small"]))
    else:
        story.append(_two_column_table(acquisition_rows, 7.25 * inch))

    # Video is a distinct evidence section. Keep its heading with the image.
    if getattr(test.video, "source_path", "") and Path(test.video.source_path).exists():
        frame = _video_frame_image(test)
        if frame is not None:
            image, caption = frame
            story.append(PageBreak())
            story.append(Paragraph("Video Evidence", styles["section"]))
            story.append(Paragraph(_escape(caption), styles["small"]))
            story.append(image)
            story.append(Spacer(1, 0.08 * inch))
            frame_row_value = (
                f"{getattr(test.video, 'pdf_frame_position_s', None):.3f} s (selected)"
                if getattr(test.video, 'pdf_frame_position_s', None) is not None
                else "Automatic representative frame"
            )
            story.append(_table([
                ("Video File", Path(test.video.source_path).name),
                ("Sync Start", _fmt(test.video.sync_offset_s, "s", 3)),
                ("PDF Frame", frame_row_value),
            ], widths=[2.65 * inch, 4.60 * inch]))

    notes = _clean(test.notes)
    if notes:
        story.append(Spacer(1, 0.10 * inch))
        story.append(Paragraph("Test Notes", styles["subsection"]))
        story.append(Paragraph(_escape(notes).replace("\n", "<br/>"), styles["body"]))


def _campaign_summary_table(tests, styles):
    rows = [[
        "Test", "Designation", "Class", "Impulse", "Peak", "Burn", "Pressure", "Video"
    ]]
    for test in tests:
        analysis = test.analysis_results
        if analysis is None:
            rows.append([_escape(test.display_name), _escape(test.motor_designation), "—", "—", "—", "—", "—", "Yes" if getattr(test.video, "source_path", "") else "—"])
            continue
        thrust = analysis.thrust
        rows.append([
            _escape(test.display_name),
            _escape(thrust.designation or test.motor_designation),
            _escape(analysis.classification.motor_class),
            _fmt(_total_impulse_value(test), "N·s"),
            _fmt(thrust.peak_thrust_N, "N"),
            _fmt(thrust.burn_time_5pct_s or thrust.burn_time_s, "s"),
            "Yes" if test.data.pressure_psi is not None else "—",
            "Yes" if getattr(test.video, "source_path", "") and Path(test.video.source_path).exists() else "—",
        ])
    # Convert text to Paragraphs so long filenames/designations wrap cleanly.
    wrapped = []
    for row_index, row in enumerate(rows):
        if row_index == 0:
            wrapped.append([Paragraph(_escape(v), ParagraphStyle("cth", fontName="Helvetica-Bold", fontSize=6.4, textColor=MUTED)) for v in row])
        else:
            wrapped.append([Paragraph(str(v), ParagraphStyle("ctd", fontName="Helvetica", fontSize=6.3, leading=7.5, textColor=WHITE)) for v in row])
    return _four_column_table([], [1, 1, 1, 1]) if False else Table(wrapped, colWidths=[0.88*inch, 1.28*inch, 0.48*inch, 0.90*inch, 0.82*inch, 0.62*inch, 0.68*inch, 0.62*inch], repeatRows=1, hAlign="LEFT", style=TableStyle([
        ("BACKGROUND", (0,0), (-1,0), PANEL_2),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [PANEL, PANEL_2]),
        ("BOX", (0,0), (-1,-1), 0.5, GRID),
        ("INNERGRID", (0,0), (-1,-1), 0.35, GRID),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))


def _campaign_metric_stats_table(result) -> Optional[Table]:
    rows = [["Metric", "Tests", "Mean", "Median", "Min", "Max", "Std Dev", "CV"]]
    for name, stats in result.metrics.items():
        if stats.count == 0:
            continue
        rows.append([
            name,
            str(stats.count),
            _fmt(stats.mean, stats.unit),
            _fmt(stats.median, stats.unit),
            _fmt(stats.minimum, stats.unit),
            _fmt(stats.maximum, stats.unit),
            _fmt(stats.std_dev, stats.unit),
            _fmt(stats.coefficient_variation_percent, "%", 1),
        ])
    if len(rows) == 1:
        return None
    wrapped = []
    for ri, row in enumerate(rows):
        style = ParagraphStyle(f"mst{ri}", fontName="Helvetica-Bold" if ri == 0 else "Helvetica", fontSize=6.3, leading=7.5, textColor=MUTED if ri == 0 else WHITE)
        wrapped.append([Paragraph(_escape(v), style) for v in row])
    return Table(wrapped, colWidths=[1.0*inch,0.48*inch,0.9*inch,0.9*inch,0.9*inch,0.9*inch,0.9*inch,0.72*inch], repeatRows=1, hAlign="LEFT", style=TableStyle([
        ("BACKGROUND", (0,0), (-1,0), PANEL_2),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [PANEL, PANEL_2]),
        ("BOX", (0,0), (-1,-1), 0.5, GRID),
        ("INNERGRID", (0,0), (-1,-1), 0.35, GRID),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))


def generate_pdf_report(test, simulation=None, output_path=None, app_version=APP_VERSION) -> str:
    """Generate a single-test PDF report.

    Kept for compatibility with the existing export test and as a useful
    lower-level export service. The main application uses the campaign export.
    """
    if test is None:
        raise PDFReportError("No test is selected.")
    path = Path(output_path) if output_path else Path.cwd() / f"{test.filename}_RMCS_Report.pdf"
    if path.suffix.lower() != ".pdf":
        path = path.with_suffix(".pdf")
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = _build_styles()
    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=MARGIN, leftMargin=MARGIN, topMargin=0.52*inch, bottomMargin=0.58*inch, title="RMCS Analyzer Motor Test Report", author="RMCS Analyzer")
    story = [Spacer(1, 0.18*inch), Paragraph("RMCS ANALYZER", styles["subtitle"]), Paragraph("Motor Test Report", styles["title"]), Paragraph(_escape((test.analysis_results.thrust.designation if test.analysis_results else None) or test.motor_designation or test.display_name), styles["subtitle"]), HRFlowable(width="100%", thickness=1.1, color=BLUE, spaceBefore=5, spaceAfter=15)]
    kpi = _kpi_table(test, styles)
    if kpi:
        story += [kpi, Spacer(1, 0.16*inch)]
    _add_test_report(story, test, simulation, styles, include_heading=False, include_page_break=False)
    story.append(Spacer(1, 0.15*inch))
    story.append(HRFlowable(width="100%", thickness=0.7, color=GRID, spaceBefore=5, spaceAfter=7))
    story.append(Paragraph(f"Generated by RMCS Analyzer v{app_version}. Engineering calculations in this report are sourced from the application's authoritative analysis results.", styles["small"]))
    try:
        doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    except Exception as error:
        raise PDFReportError(f"Unable to generate PDF report:\n{error}") from error
    return str(path.resolve())


def generate_campaign_pdf_report(session, output_path=None, app_version=APP_VERSION) -> str:
    """Generate the complete campaign report for all tests in a session."""
    if session is None or not session.tests:
        raise PDFReportError("No motor tests are loaded in the current campaign.")

    tests = list(session.tests)
    path = Path(output_path) if output_path else Path.cwd() / "RMCS_Campaign_Report.pdf"
    if path.suffix.lower() != ".pdf":
        path = path.with_suffix(".pdf")
    path.parent.mkdir(parents=True, exist_ok=True)

    styles = _build_styles()
    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=MARGIN, leftMargin=MARGIN, topMargin=0.52*inch, bottomMargin=0.58*inch, title="RMCS Analyzer Campaign Report", author="RMCS Analyzer")
    if len(tests) == 1:
        single = tests[0]
        single_designation = (
            single.analysis_results.thrust.designation
            if single.analysis_results is not None
            else None
        ) or single.motor_designation or single.display_name
        story = [
            Spacer(1, 0.25*inch),
            Paragraph("RMCS ANALYZER", styles["subtitle"]),
            Paragraph("Motor Test Report", styles["title"]),
            Paragraph(_escape(f"{single.display_name} • {single_designation}"), styles["subtitle"]),
            HRFlowable(width="100%", thickness=1.1, color=BLUE, spaceBefore=5, spaceAfter=15),
        ]
    else:
        story = [Spacer(1, 0.25*inch), Paragraph("RMCS ANALYZER", styles["subtitle"]), Paragraph("Motor Characterization Campaign Report", styles["title"]), Paragraph(f"{len(tests)} loaded tests", styles["subtitle"]), HRFlowable(width="100%", thickness=1.1, color=BLUE, spaceBefore=5, spaceAfter=15)]

    kpi = _campaign_kpi_table(tests, styles)
    if kpi:
        story += [kpi, Spacer(1, 0.18*inch)]

    analyzed = [t for t in tests if t.analysis_results is not None]

    # Campaign-level overview and comparison material only add value when
    # there is a population to compare. A one-test campaign is presented as
    # a focused individual report instead of a population-of-one report.
    if len(tests) > 1:
        story.append(Paragraph("Campaign Overview", styles["section"]))
        videos = [t for t in tests if getattr(t.video, "source_path", "") and Path(t.video.source_path).exists()]
        pressure_tests = [t for t in tests if t.data.pressure_psi is not None]
        overview_rows = [
            ("Loaded Tests", str(len(tests))),
            ("Analyzed Tests", str(len(analyzed))),
            ("Tests with Pressure", str(len(pressure_tests))),
            ("Tests with Video", str(len(videos))),
        ]
        if session.simulation is not None:
            overview_rows.append(("Simulation", session.simulation.metadata.simulator or "Imported"))
        story.append(_table(overview_rows, widths=[2.65*inch, 4.60*inch]))
        story.append(Spacer(1, 0.18*inch))

        story.append(Paragraph("Test Summary", styles["section"]))
        story.append(_campaign_summary_table(tests, styles))

    try:
        from ..analysis.campaign_analysis import CampaignAnalyzer
        campaign_result = CampaignAnalyzer().analyze(analyzed, curve_basis="absolute") if analyzed else None
    except Exception as error:
        raise PDFReportError(f"Unable to calculate campaign report statistics:\n{error}") from error

    if len(tests) > 1 and campaign_result is not None and campaign_result.included_tests:
        story.append(PageBreak())
        story.append(Paragraph("Campaign Analysis", styles["section"]))
        story.append(Paragraph("Population-level statistics summarize the measured tests included in this campaign. They do not replace the individual test results.", styles["body"]))
        stats_table = _campaign_metric_stats_table(campaign_result)
        if stats_table:
            story.append(stats_table)
            story.append(Spacer(1, 0.18*inch))
        curve = campaign_result.curve
        if curve is not None:
            story.append(_campaign_curve_image(curve))
            story.append(Spacer(1, 0.12*inch))
        impulse_chart = _campaign_metric_image(analyzed, "total_impulse_valid_curve_Ns", "N·s", "Total Impulse by Test")
        if impulse_chart:
            story.append(impulse_chart)

        story.append(PageBreak())
        peak_chart = _campaign_metric_image(analyzed, "peak_thrust_N", "N", "Peak Thrust by Test")
        if peak_chart:
            story.append(peak_chart)
        pressure_chart = _campaign_pressure_image(analyzed)
        if pressure_chart:
            story.append(Spacer(1, 0.18*inch))
            story.append(pressure_chart)

    # Individual reports are deliberately complete and self-contained.
    for index, test in enumerate(tests):
        if len(tests) > 1:
            story.append(PageBreak())
            story.append(Paragraph(f"Test {index + 1} of {len(tests)}", styles["subtitle"]))
        _add_test_report(
            story,
            test,
            session.simulation,
            styles,
            include_heading=True,
            include_page_break=False,
            compact_single=(len(tests) == 1),
        )

    try:
        doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    except Exception as error:
        raise PDFReportError(f"Unable to generate campaign PDF report:\n{error}") from error
    return str(path.resolve())
