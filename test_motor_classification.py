import numpy as np

from src.rmcs_analyzer.analysis.analyzer import AnalysisEngine
from src.rmcs_analyzer.analysis.motor_class import MotorClassCalculator
from src.rmcs_analyzer.data.csv_reader import RMCSCSVReader


# ============================================================================
# Motor Classification / Designation Validation
#
# Purpose:
#   Validate motor impulse classification and verify that the complete
#   AnalysisEngine produces the designation from the authoritative
#   performance-reduction result.
#
# Responsibility split:
#   MotorClassCalculator -> impulse class
#   PerformanceReducer   -> standardized average thrust / impulse
#   AnalysisEngine       -> combines those results into AnalysisResults and
#                           exposes the final designation
#
# This test does NOT add a designation API to MotorClassCalculator.
# ============================================================================


BOUNDARY_CASES = [
    ("A", 1.26, 2.50),
    ("B", 2.51, 5.00),
    ("C", 5.01, 10.00),
    ("D", 10.01, 20.00),
    ("E", 20.01, 40.00),
    ("F", 40.01, 80.00),
    ("G", 80.01, 160.00),
    ("H", 160.01, 320.00),
    ("I", 320.01, 640.00),
    ("J", 640.01, 1280.00),
    ("K", 1280.01, 2560.00),
    ("L", 2560.01, 5120.00),
    ("M", 5120.01, 10240.00),
    ("N", 10240.01, 20480.00),
    ("O", 20480.01, 40960.00),
]


def get_class(calculator, impulse):
    """Return the class letter from the existing calculator API."""
    if hasattr(calculator, "calculate_class"):
        result = calculator.calculate_class(impulse)
    elif hasattr(calculator, "classify"):
        result = calculator.classify(impulse)
    else:
        raise AttributeError(
            "MotorClassCalculator does not expose calculate_class() or classify()."
        )

    if hasattr(result, "motor_class"):
        return result.motor_class

    return result


def extract_designation(results):
    """Find the designation in the actual AnalysisResults structure."""
    if hasattr(results, "designation"):
        return results.designation

    if hasattr(results, "thrust") and hasattr(results.thrust, "designation"):
        return results.thrust.designation

    if hasattr(results, "classification") and hasattr(
        results.classification, "designation"
    ):
        return results.classification.designation

    raise AttributeError(
        "AnalysisResults does not expose a designation in the expected "
        "results structure."
    )


def run_analysis(engine, data):
    """Support the existing AnalysisEngine entry point."""
    if hasattr(engine, "analyze"):
        return engine.analyze(data)

    if hasattr(engine, "run"):
        return engine.run(data)

    raise AttributeError(
        "AnalysisEngine does not expose analyze() or run()."
    )


def _script_regression():
    calculator = MotorClassCalculator()

    print("RMCS Analyzer Motor Classification Validation")
    print("=" * 78)

    # ------------------------------------------------------------------
    # Basic classification at representative points.
    # ------------------------------------------------------------------

    print()
    print("REPRESENTATIVE CLASS TESTS")
    print("-" * 78)

    for expected_class, lower, upper in BOUNDARY_CASES:
        midpoint = (lower + upper) / 2.0
        actual = get_class(calculator, midpoint)

        assert actual == expected_class, (
            f"{expected_class}: midpoint {midpoint} classified as {actual}"
        )

        print(
            f"{expected_class}: {lower:.2f} - {upper:.2f} Ns "
            f"midpoint {midpoint:.3f} -> PASSED"
        )

    # ------------------------------------------------------------------
    # Boundary transitions.
    # ------------------------------------------------------------------

    print()
    print("CLASS TRANSITION TESTS")
    print("-" * 78)

    for index in range(len(BOUNDARY_CASES) - 1):
        current_class, _, current_upper = BOUNDARY_CASES[index]
        next_class, next_lower, _ = BOUNDARY_CASES[index + 1]

        actual_below = get_class(calculator, current_upper)
        actual_above = get_class(calculator, next_lower)

        assert actual_below == current_class, (
            f"{current_upper} Ns should be {current_class}, got {actual_below}"
        )

        assert actual_above == next_class, (
            f"{next_lower} Ns should be {next_class}, got {actual_above}"
        )

        print(
            f"{current_class} -> {next_class}: "
            f"{current_upper:.2f}/{next_lower:.2f} Ns -> PASSED"
        )

    # ------------------------------------------------------------------
    # Zerox classification.
    # ------------------------------------------------------------------

    print()
    print("ZEROX CLASSIFICATION")
    print("-" * 78)

    reader = RMCSCSVReader()
    zerox = reader.read("test_data/Zerox.csv")

    zerox_impulse = 14471.744320
    zerox_average = 2031.225247

    zerox_class = get_class(calculator, zerox_impulse)

    assert zerox_class == "N", (
        f"Zerox impulse should be N class, got {zerox_class}"
    )

    print(f"Zerox total impulse:     {zerox_impulse:.6f} Ns")
    print(f"Zerox class:             {zerox_class} -> PASSED")

    # ------------------------------------------------------------------
    # Designation through the real analysis path.
    # ------------------------------------------------------------------

    print()
    print("DESIGNATION VIA ANALYSIS ENGINE")
    print("-" * 78)

    engine = AnalysisEngine()
    results = run_analysis(engine, zerox)
    designation = extract_designation(results)

    assert designation == "N2031", (
        f"Expected current Zerox designation N2031, got {designation}"
    )

    print(f"Zerox standardized average: {zerox_average:.6f} N")
    print(f"Zerox designation:          {designation} -> PASSED")

    # ------------------------------------------------------------------
    # Values outside the A-O range.
    #
    # The calculator intentionally supports fractional low-power motor
    # designations below class A (for example 1/8A). Therefore 0.0 and 1.0
    # are NOT treated as invalid by this test.
    #
    # This test only verifies that values above the supported A-O range do
    # not get silently assigned an A-O class. Non-finite inputs are also
    # checked separately.
    # ------------------------------------------------------------------

    print()
    print("OUT-OF-RANGE / INVALID INPUT TESTS")
    print("-" * 78)

    above_range = 40960.01

    try:
        result = get_class(calculator, above_range)
    except (ValueError, TypeError):
        result = None

    assert result is None or result == "", (
        f"Impulse {above_range!r} unexpectedly classified as {result!r}"
    )

    for impulse in [np.nan, np.inf, -np.inf]:
        try:
            result = get_class(calculator, impulse)
        except (ValueError, TypeError, OverflowError):
            result = None

        assert result is None or result == "", (
            f"Non-finite impulse {impulse!r} unexpectedly classified as {result!r}"
        )

    print("Above O range: PASSED")
    print("Non-finite inputs: PASSED")

    print()
    print("=" * 78)
    print("ALL MOTOR CLASSIFICATION TESTS PASSED")
    print("=" * 78)



def test_script_regression():
    _script_regression()


if __name__ == "__main__":
    _script_regression()
