import sys
from pathlib import Path

# The RMCS project uses a src/ layout. Add it to the import path so this
# test can be run directly with the project's Python interpreter.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import numpy as np
from types import SimpleNamespace

from rmcs_analyzer.analysis.campaign_analysis import CampaignAnalyzer
from rmcs_analyzer.analysis.results import (
    AnalysisResults,
    ThrustResults,
    StatisticalResults,
    MotorClassification,
)
from rmcs_analyzer.data.models import (
    TestData as RMCSData,
    TestMetadata as RMCSMetadata,
)


def make_test(name, peak, impulse, burn_time, isp=100.0, cstar=1200.0):
    time = np.linspace(0.0, burn_time + 1.0, 101)
    thrust = np.where(
        time <= burn_time,
        peak * np.sin(np.pi * time / burn_time),
        0.0,
    )

    data = RMCSData(
        time_s=time,
        thrust_N=thrust,
        metadata=RMCSMetadata(source_file=name),
    )

    thrust_results = ThrustResults(
        peak_thrust_N=peak,
        total_impulse_valid_curve_Ns=impulse,
        burn_time_5pct_s=burn_time,
        burn_start_5pct_time_s=0.0,
        burn_end_5pct_time_s=burn_time,
        average_thrust_5pct_N=impulse / burn_time,
        isp_s=isp,
        cstar_m_per_s=cstar,
    )

    results = AnalysisResults(
        events=None,
        thrust=thrust_results,
        statistics=StatisticalResults(),
        classification=MotorClassification(),
    )

    return SimpleNamespace(
        display_name=name,
        source_file=name,
        data=data,
        analysis_results=results,
    )


def test_campaign_metric_statistics_use_population_std_and_cv():
    tests = [
        make_test("A", 100.0, 1000.0, 2.0),
        make_test("B", 110.0, 1100.0, 2.2),
        make_test("C", 90.0, 900.0, 1.8),
    ]

    result = CampaignAnalyzer(curve_points=50).analyze(tests)
    stats = result.metrics["Peak Thrust"]

    assert stats.count == 3
    assert stats.total_tests == 3
    assert stats.mean == 100.0
    assert stats.median == 100.0
    assert stats.minimum == 90.0
    assert stats.maximum == 110.0
    assert np.isclose(stats.std_dev, np.sqrt(200 / 3))
    assert np.isclose(stats.coefficient_variation_percent, np.sqrt(200 / 3))


def test_campaign_ignores_missing_metric_without_treating_it_as_zero():
    first = make_test("A", 100.0, 1000.0, 2.0)
    second = make_test("B", 110.0, 1100.0, 2.2)
    second.analysis_results.thrust.cstar_m_per_s = None

    result = CampaignAnalyzer().analyze([first, second])
    cstar = result.metrics["C*"]

    assert cstar.count == 1
    assert cstar.total_tests == 2
    assert cstar.mean == 1200.0


def test_campaign_curve_is_aligned_to_ignition_and_can_be_normalized():
    tests = [
        make_test("A", 100.0, 1000.0, 2.0),
        make_test("B", 200.0, 2200.0, 4.0),
    ]

    result = CampaignAnalyzer(curve_points=100).analyze(
        tests,
        curve_basis="normalized",
    )

    curve = result.curve

    assert curve is not None
    assert curve.test_count == 2
    assert np.isclose(curve.time[0], 0.0)
    assert np.isclose(curve.time[-1], 1.0)
    assert np.all(curve.sample_count == 2)
    assert np.isfinite(curve.mean).all()


def main():
    tests = [
        test_campaign_metric_statistics_use_population_std_and_cv,
        test_campaign_ignores_missing_metric_without_treating_it_as_zero,
        test_campaign_curve_is_aligned_to_ignition_and_can_be_normalized,
    ]

    failed = 0

    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"FAIL: {test.__name__}: {exc}")

    passed = len(tests) - failed
    print(f"\n{passed} passed, {failed} failed")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
