from pathlib import Path
import csv

from rmcs_analyzer.analysis import AnalysisEngine
from rmcs_analyzer.data import RMCSCSVReader
from rmcs_analyzer.export.analysis_csv import COLUMNS, export_analysis_csv
from rmcs_analyzer.project.test_model import TestModel


def _load_test(path: Path):
    data = RMCSCSVReader().read(path)
    test = TestModel(data=data)
    test.analysis_results = AnalysisEngine().analyze(data)
    return test


def test_single_test_analysis_csv_uses_authoritative_results(tmp_path):
    root = Path(__file__).parent
    test = _load_test(root / "test_data" / "Synthetic-Test-01.csv")
    output = export_analysis_csv([test], tmp_path / "analysis.csv")

    with output.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    row = rows[0]
    assert len(row) == len(COLUMNS)
    assert row["Test Name"] == "Synthetic-Test-01.csv"
    assert float(row["Peak Thrust (N)"]) == test.analysis_results.thrust.peak_thrust_N
    assert float(row["Total Impulse (N·s)"]) == test.analysis_results.thrust.total_impulse_valid_curve_Ns
    assert row["Motor Class"] == test.analysis_results.classification.motor_class
    assert row["Calculated Designation"] == test.analysis_results.thrust.designation


def test_campaign_analysis_csv_exports_one_row_per_test(tmp_path):
    root = Path(__file__).parent
    tests = [
        _load_test(root / "test_data" / "Synthetic-Test-01.csv"),
        _load_test(root / "test_data" / "Synthetic-Test-03.csv"),
    ]
    output = export_analysis_csv(tests, tmp_path / "campaign.csv")

    with output.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    assert [row["Test Name"] for row in rows] == [
        "Synthetic-Test-01.csv",
        "Synthetic-Test-03.csv",
    ]
    assert all(row["Total Impulse (N·s)"] for row in rows)


def test_analysis_csv_rejects_unanalyzed_test(tmp_path):
    root = Path(__file__).parent
    data = RMCSCSVReader().read(root / "test_data" / "Synthetic-Test-01.csv")
    test = TestModel(data=data)

    try:
        export_analysis_csv([test], tmp_path / "analysis.csv")
    except ValueError as error:
        assert "have not been analyzed" in str(error)
    else:
        raise AssertionError("Expected unanalyzed test to be rejected")
