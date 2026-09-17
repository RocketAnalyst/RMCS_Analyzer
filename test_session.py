from pathlib import Path

from src.rmcs_analyzer.data import (
    CSVReadError,
    RMCSCSVReader,
)

from src.rmcs_analyzer.project import (
    TestModel,
    TestSession,
)


def load_test(
    reader,
    filename,
):
    try:
        data = reader.read(
            str(filename)
        )
    except CSVReadError as error:
        print(
            f"CSV ERROR: {error}"
        )
        return None

    return TestModel(
        data=data
    )


def main():
    print("=" * 60)
    print("RMCS ANALYZER - TEST SESSION TEST")
    print("=" * 60)

    project_root = Path(
        __file__
    ).parent

    test_data_folder = (
        project_root
        / "test_data"
    )

    reader = RMCSCSVReader()

    test_008 = load_test(
        reader,
        test_data_folder
        / "TEST_008.CSV",
    )

    test_010 = load_test(
        reader,
        test_data_folder
        / "TEST_010_SAMPLE_MOTOR.csv",
    )

    if test_008 is None or test_010 is None:
        return

    session = TestSession()

    # =========================================================
    # ADD TESTS
    # =========================================================

    print("\n--- ADD TESTS ---")

    print(
        "Add TEST_008:",
        session.add_test(test_008)
    )

    print(
        "Add TEST_010:",
        session.add_test(test_010)
    )

    print(
        f"Test count: {session.test_count}"
    )

    print(
        f"Active test: "
        f"{session.active_test.display_name}"
    )

    # =========================================================
    # DUPLICATE TEST
    # =========================================================

    print("\n--- DUPLICATE TEST ---")

    duplicate = load_test(
        reader,
        test_data_folder
        / "TEST_010_SAMPLE_MOTOR.csv",
    )

    print(
        "Add duplicate TEST_010:",
        session.add_test(duplicate)
    )

    print(
        f"Test count after duplicate: "
        f"{session.test_count}"
    )

    # =========================================================
    # SELECT TEST
    # =========================================================

    print("\n--- SELECT TEST ---")

    print(
        "Select TEST_008:",
        session.select_test(test_008)
    )

    print(
        f"Active test: "
        f"{session.active_test.display_name}"
    )

    print(
        "Select TEST_010:",
        session.select_test(test_010)
    )

    print(
        f"Active test: "
        f"{session.active_test.display_name}"
    )

    # =========================================================
    # MODIFY TEST
    # =========================================================

    print("\n--- MODIFICATION STATE ---")

    test_010.test_number = "010"
    test_010.mark_modified()

    print(
        f"TEST_010 modified: "
        f"{test_010.modified}"
    )

    print(
        f"Session has modified tests: "
        f"{session.has_modified_tests}"
    )

    # =========================================================
    # REMOVE TEST
    # =========================================================

    print("\n--- REMOVE TEST ---")

    print(
        "Remove TEST_010:",
        session.remove_test(test_010)
    )

    print(
        f"Test count: "
        f"{session.test_count}"
    )

    print(
        f"Active test: "
        f"{session.active_test.display_name}"
        if session.active_test
        else "None"
    )

    # =========================================================
    # FINAL TEST LIST
    # =========================================================

    print("\n--- LOADED TESTS ---")

    for test in session.tests:
        print(
            f"- {test.display_name}"
        )

    print("\n" + "=" * 60)
    print("TEST SESSION TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()