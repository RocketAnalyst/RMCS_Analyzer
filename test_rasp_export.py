from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from rmcs_analyzer.data import RMCSCSVReader
from rmcs_analyzer.analysis import AnalysisEngine
from rmcs_analyzer.project.test_model import TestModel
from rmcs_analyzer.export.rasp import export_rasp_eng


def _load_test(path: Path):
    reader = RMCSCSVReader()
    data = reader.read(path)
    test = TestModel(data=data)
    test.analysis_results = AnalysisEngine().analyze(data)
    return test


def _parse_entries(text: str):
    entries = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue
        fields = line.split()
        if len(fields) == 7 and fields[3] == "P":
            current = {"header": fields, "points": []}
            entries.append(current)
            continue
        assert len(fields) == 2
        current["points"].append(tuple(map(float, fields)))
    return entries


def test_single_test_rasp_export(tmp_path):
    root = Path(__file__).parent
    test = _load_test(root / "test_data" / "Synthetic-Test-01.csv")
    output = export_rasp_eng([test], tmp_path / "test.eng")
    entries = _parse_entries(output.read_text(encoding="utf-8"))

    assert len(entries) == 1
    header = entries[0]["header"]
    points = entries[0]["points"]

    assert len(header) == 7
    assert header[3] == "P"
    assert float(header[1]) == 98.0
    assert float(header[2]) == 1219.0
    assert abs(float(header[4]) - 5.92) < 1e-9
    assert abs(float(header[5]) - 6.17) < 1e-9
    assert points[-1][1] == 0.0
    assert all(points[i][0] < points[i + 1][0] for i in range(len(points) - 1))
    assert len(points) <= 31


def test_campaign_rasp_export(tmp_path):
    root = Path(__file__).parent
    tests = [
        _load_test(root / "test_data" / "Synthetic-Test-01.csv"),
        _load_test(root / "test_data" / "Synthetic-Test-03.csv"),
    ]
    output = export_rasp_eng(tests, tmp_path / "campaign.eng")
    entries = _parse_entries(output.read_text(encoding="utf-8"))

    assert len(entries) == 2
    assert entries[0]["header"][0] == "Synthetic-Test-01"
    assert entries[1]["header"][0] == "Synthetic-Test-03"
    for entry in entries:
        points = entry["points"]
        assert points[-1][1] == 0.0
        assert all(points[i][0] < points[i + 1][0] for i in range(len(points) - 1))
        assert len(points) <= 31
