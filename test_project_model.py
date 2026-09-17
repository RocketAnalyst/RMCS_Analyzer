from pathlib import Path

from src.rmcs_analyzer.data import (
    CSVReadError,
    RMCSCSVReader,
)

from src.rmcs_analyzer.project import TestModel


def main():
    csv_file = (
        Path(__file__).parent
        / "test_data"
        / "TEST_010_SAMPLE_MOTOR.csv"
    )

    print("=" * 60)
    print("RMCS ANALYZER - PROJECT MODEL TEST")
    print("=" * 60)

    reader = RMCSCSVReader()

    try:
        test_data = reader.read(
            str(csv_file)
        )
    except CSVReadError as error:
        print("\nCSV ERROR:")
        print(error)
        return

    test = TestModel(
        data=test_data
    )

    print("\n--- TEST MODEL ---")
    print(f"Display Name: {test.display_name}")
    print(f"Filename: {test.filename}")
    print(f"Test Number: {test.test_number}")
    print(f"Motor: {test.motor_designation}")
    print(f"Date: {test.test_date}")
    print(f"Source File: {test.source_file}")

    print("\n--- MODIFICATION STATE ---")
    print(f"Modified: {test.modified}")

    test.test_number = "010"
    test.mark_modified()

    print("\nAfter editing Test Number:")
    print(f"Test Number: {test.test_number}")
    print(f"Modified: {test.modified}")

    test.mark_saved()

    print("\nAfter saving:")
    print(f"Modified: {test.modified}")

    print("\n" + "=" * 60)
    print("PROJECT MODEL TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()