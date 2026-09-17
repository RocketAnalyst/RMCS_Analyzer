from src.rmcs_analyzer.project.validation import MetadataValidator


def show_result(label, result):
    print(
        f"{label:<30} "
        f"valid={result.valid:<5} "
        f"value={result.value!r:<12} "
        f"message={result.message!r}"
    )


print()
print("RMCS Analyzer Metadata Validation")
print("=" * 75)

show_result(
    "Test Number 010",
    MetadataValidator.test_number("010"),
)

show_result(
    "Diameter 2.6",
    MetadataValidator.motor_diameter("2.6"),
)

show_result(
    "Diameter blank",
    MetadataValidator.motor_diameter(""),
)

show_result(
    "Diameter text",
    MetadataValidator.motor_diameter("asdf"),
)

show_result(
    "Diameter negative",
    MetadataValidator.motor_diameter("-2.6"),
)

show_result(
    "Initial Mass 450",
    MetadataValidator.initial_mass("450"),
)

show_result(
    "Initial Mass zero",
    MetadataValidator.initial_mass("0"),
)

show_result(
    "Propellant Mass 125.5",
    MetadataValidator.propellant_mass("125.5"),
)

show_result(
    "Date 2026-09-17",
    MetadataValidator.test_date("2026-09-17"),
)

show_result(
    "Date blank",
    MetadataValidator.test_date(""),
)

show_result(
    "Date text",
    MetadataValidator.test_date("asdf"),
)

show_result(
    "Date bad date",
    MetadataValidator.test_date("2026-99-99"),
)

show_result(
    "Date wrong format",
    MetadataValidator.test_date("09/17/2026"),
)

print()