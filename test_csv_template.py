import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from src.rmcs_analyzer.data.csv_reader import CSVReadError, RMCSCSVReader


def main():
    path = Path(__file__).parent / "test_data" / "Zerox.csv"
    data = RMCSCSVReader().read(path)

    m = data.metadata
    assert m.motor_diameter == 98.0
    assert m.motor_length == 1018.79
    assert m.initial_mass == 7711.0
    assert m.propellant_mass == 7484.274
    assert m.nozzle_throat == 1.0
    assert m.nozzle_exit == 2.737
    assert m.sample_rate_hz == 80.0
    assert m.case_pressure_limit_psi is None or m.case_pressure_limit_psi == 0.0

    assert data.time_s.size > 0
    assert data.thrust_N.size == data.time_s.size
    assert data.pressure_psi is not None

    # The current template intentionally leaves Case pressure limit blank.
    # Blank numeric metadata is represented as None.
    assert m.case_pressure_limit_psi is None

    # The old inch-based motor-dimension template must no longer be accepted.
    rows = list(csv.reader(path.open(encoding="utf-8-sig")))
    for row in rows:
        if row and row[0] == "Motor Diameter (mm)":
            row[0] = "Motor Diameter (in)"
            break

    with TemporaryDirectory() as temp_dir:
        bad_path = Path(temp_dir) / "old_format.csv"
        with bad_path.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerows(rows)

        try:
            RMCSCSVReader().read(bad_path)
        except CSVReadError:
            pass
        else:
            raise AssertionError("Old inch-based motor diameter metadata was accepted.")

    print("CSV TEMPLATE REGRESSION PASSED")


if __name__ == "__main__":
    main()
