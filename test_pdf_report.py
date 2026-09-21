from pathlib import Path

from pypdf import PdfReader

from src.rmcs_analyzer.analysis import AnalysisEngine
from src.rmcs_analyzer.data import RMCSCSVReader
from src.rmcs_analyzer.export.pdf_report import (
    generate_campaign_pdf_report,
    generate_pdf_report,
)
from src.rmcs_analyzer.processing import ProcessingPipeline
from src.rmcs_analyzer.project.session import TestSession as RMCS_TestSession
from src.rmcs_analyzer.project.test_model import TestModel as RMCS_TestModel
from src.rmcs_analyzer.simulation import import_simulation_csv


ROOT = Path(__file__).parent


def build_test(filename="Synthetic-Test-01.csv"):
    source = ROOT / "test_data" / filename
    data = RMCSCSVReader().read(source)
    processed = ProcessingPipeline().process(data)
    analysis = AnalysisEngine().analyze(
        processed.prepared_data,
        events=processed.event_set,
    )
    test = RMCS_TestModel(data=processed.prepared_data)
    test.analysis_results = analysis
    return test


def build_campaign():
    session = RMCS_TestSession()
    for index in range(1, 6):
        test = build_test(f"Synthetic-Test-{index:02d}.csv")
        session.add_test(test)
    return session


def test_pdf_report_generation(tmp_path):
    test = build_test()
    output = tmp_path / "report.pdf"
    result = generate_pdf_report(test, output_path=output)

    assert Path(result).exists()
    assert Path(result).stat().st_size > 10_000


def test_pdf_report_with_simulation(tmp_path):
    test = build_test()
    simulation = import_simulation_csv(
        ROOT / "sim_data" / "Synthetic-Simulation-BurnSim.csv"
    )
    output = tmp_path / "report-with-sim.pdf"
    result = generate_pdf_report(
        test,
        simulation=simulation,
        output_path=output,
    )

    assert Path(result).exists()
    assert Path(result).stat().st_size > 10_000


def test_campaign_pdf_report(tmp_path):
    session = build_campaign()
    session.simulation = import_simulation_csv(
        ROOT / "sim_data" / "Synthetic-Simulation-OpenMotor.csv"
    )
    output = tmp_path / "campaign-report.pdf"
    result = generate_campaign_pdf_report(
        session,
        output_path=output,
    )

    report = Path(result)
    assert report.exists()
    assert report.stat().st_size > 50_000


def test_campaign_pdf_uses_authoritative_total_impulse(tmp_path):
    session = build_campaign()
    output = tmp_path / "campaign-authoritative-impulse.pdf"
    result = generate_campaign_pdf_report(session, output_path=output)

    text = "\n".join(page.extract_text() or "" for page in PdfReader(result).pages)
    assert "99.62 N·s" in text
    assert "99.23 N·s" not in text
    assert "96.61 N·s" in text
    assert "102.06 N·s" in text


def test_campaign_pdf_layout_has_no_blank_pages(tmp_path):
    session = build_campaign()
    session.simulation = import_simulation_csv(
        ROOT / "sim_data" / "Synthetic-Simulation-OpenMotor.csv"
    )
    output = tmp_path / "campaign-layout.pdf"
    result = generate_campaign_pdf_report(session, output_path=output)

    pages = PdfReader(result).pages
    assert len(pages) == 13
    assert all((page.extract_text() or "").strip() for page in pages)


def test_video_frame_state_and_pdf_selection_support():
    from src.rmcs_analyzer.project.video_state import VideoState
    state = VideoState()
    assert state.pdf_frame_position_s is None
    state.pdf_frame_position_s = 1.234
    assert state.pdf_frame_position_s == 1.234


def test_single_test_campaign_uses_compact_report_layout(tmp_path):
    session = RMCS_TestSession()
    session.add_test(build_test("Synthetic-Test-01.csv"))
    session.simulation = import_simulation_csv(
        ROOT / "sim_data" / "Synthetic-Simulation-OpenMotor.csv"
    )
    output = tmp_path / "single-test-campaign.pdf"
    result = generate_campaign_pdf_report(session, output_path=output)

    pages = PdfReader(result).pages
    text = "\n".join(page.extract_text() or "" for page in pages)

    # A one-test campaign is intentionally presented as a focused motor test
    # report rather than a population-level campaign report.
    assert len(pages) == 2
    assert "Motor Test Report" in (pages[0].extract_text() or "")
    assert "Campaign Analysis" not in text
    assert "Campaign Overview" not in text
    assert "Population-level statistics" not in text
