from pathlib import Path
import csv

import numpy as np

from rmcs_analyzer.data.models import TestData as RMCSData
from rmcs_analyzer.export.burnsim import export_burnsim_csv
from rmcs_analyzer.project.model import TestModel as RMCSTest


def make_test():
    data = RMCSData(
        time_s=np.array([0.0, 0.1, 0.2]),
        thrust_N=np.array([0.0, 100.0, 0.0]),
        pressure_psi=np.array([10.0, 20.0, 10.0]),
    )
    return RMCSTest(data=data)


def test_burnsim_export(tmp_path: Path):
    output = tmp_path / "burnsim.csv"
    export_burnsim_csv(make_test(), output)

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["Time", "Pressure", "Thrust"]
    assert rows[1] == ["0.000000", "10.000000", "0.000000"]
    assert rows[2] == ["0.100000", "20.000000", "100.000000"]
    assert rows[3] == ["0.200000", "10.000000", "0.000000"]


def test_burnsim_export_uses_measured_test_data(tmp_path: Path):
    """Regression test for the actual RMCS TestModel data structure."""
    source = Path(__file__).parent / "test_data" / "Synthetic-Test-01.csv"

    from rmcs_analyzer.data.csv_reader import RMCSCSVReader

    test = RMCSTest(data=RMCSCSVReader().read(source))
    output = tmp_path / "synthetic_burnsim.csv"
    export_burnsim_csv(test, output)

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == test.data.sample_count
    assert float(rows[0]["Time"]) == test.data.time_s[0]
    assert float(rows[-1]["Time"]) == test.data.time_s[-1]
    assert float(rows[-1]["Thrust"]) == test.data.thrust_N[-1]
    assert float(rows[-1]["Pressure"]) == test.data.pressure_psi[-1]
