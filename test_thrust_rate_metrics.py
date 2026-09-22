from pathlib import Path
import math

from src.rmcs_analyzer.data.csv_reader import RMCSCSVReader
from src.rmcs_analyzer.processing import ProcessingPipeline, ProcessingSettings
from src.rmcs_analyzer.analysis import AnalysisEngine


PROJECT_ROOT = Path(__file__).resolve().parent
REFERENCE_FILE = PROJECT_ROOT / "test_data" / "Zerox.csv"


def _script_regression():
    data = RMCSCSVReader().read(REFERENCE_FILE)

    processing = ProcessingPipeline().process(
        data,
        ProcessingSettings(),
    )

    analysis = AnalysisEngine().analyze(
        processing.prepared_data,
        events=processing.event_set,
    )

    rise = analysis.thrust.thrust_rise_rate_N_per_s
    decay = analysis.thrust.thrust_decay_rate_N_per_s

    assert rise is not None
    assert decay is not None
    assert math.isfinite(rise)
    assert math.isfinite(decay)
    assert rise > 0.0
    assert decay < 0.0

    # Regression values for the current Zerox reference data and the
    # defined 0.10 s smoothing / derivative methodology.
    assert math.isclose(
        rise,
        24505.882071237444,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )
    assert math.isclose(
        decay,
        -4172.026215151534,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )

    print(f"Thrust rise rate:  {rise:.6f} N/s")
    print(f"Thrust decay rate: {decay:.6f} N/s")
    print("THRUST RATE METRICS REGRESSION PASSED")



def test_script_regression():
    _script_regression()


if __name__ == "__main__":
    _script_regression()
