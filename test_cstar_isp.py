import numpy as np

from src.rmcs_analyzer.analysis.performance_extensions import (
    PerformanceExtensionCalculator,
)
from src.rmcs_analyzer.data.models import TestData, TestMetadata


def main():
    time_s = np.linspace(0.0, 2.0, 201)
    thrust_N = np.full_like(time_s, 100.0)
    pressure_psi = np.full_like(time_s, 500.0)

    metadata = TestMetadata(
        propellant_mass=1000.0,
        nozzle_throat=0.25,
    )

    data = TestData(
        time_s=time_s,
        calibrated_time_s=time_s.copy(),
        thrust_N=thrust_N,
        pressure_psi=pressure_psi,
        metadata=metadata,
    )

    calculator = PerformanceExtensionCalculator()

    result = calculator.calculate(
        data,
        total_impulse_Ns=200.0,
        burn_start_5pct_time_s=0.1,
        burn_end_5pct_time_s=1.9,
        burn_time_5pct_s=1.8,
    )

    expected_isp = 200.0 / (1.0 * 9.80665)

    throat_m = 0.25 * 0.0254
    throat_area = np.pi * throat_m**2 / 4.0
    expected_mdot = 1.0 / 1.8
    expected_cstar = (
        500.0 * 6894.757293168
        * throat_area
        / expected_mdot
    )

    assert result.isp_s is not None
    assert np.isclose(result.isp_s, expected_isp, rtol=1e-12)

    assert result.cstar_m_per_s is not None
    assert np.isclose(
        result.cstar_m_per_s,
        expected_cstar,
        rtol=1e-12,
    )

    missing_propellant = TestData(
        time_s=time_s,
        calibrated_time_s=time_s.copy(),
        thrust_N=thrust_N,
        pressure_psi=pressure_psi,
        metadata=TestMetadata(
            nozzle_throat=0.25,
        ),
    )

    missing = calculator.calculate(
        missing_propellant,
        total_impulse_Ns=200.0,
        burn_start_5pct_time_s=0.1,
        burn_end_5pct_time_s=1.9,
        burn_time_5pct_s=1.8,
    )

    assert missing.isp_s is None
    assert missing.isp_status == "Propellant mass required."
    assert missing.cstar_m_per_s is None
    assert missing.cstar_status == "Propellant mass required."

    missing_throat = TestData(
        time_s=time_s,
        calibrated_time_s=time_s.copy(),
        thrust_N=thrust_N,
        pressure_psi=pressure_psi,
        metadata=TestMetadata(
            propellant_mass=1000.0,
        ),
    )

    missing_throat_result = calculator.calculate(
        missing_throat,
        total_impulse_Ns=200.0,
        burn_start_5pct_time_s=0.1,
        burn_end_5pct_time_s=1.9,
        burn_time_5pct_s=1.8,
    )

    assert missing_throat_result.isp_s is not None
    assert missing_throat_result.cstar_m_per_s is None
    assert (
        missing_throat_result.cstar_status
        == "Nozzle throat diameter required."
    )

    print(f"Isp: {result.isp_s:.6f} s")
    print(f"C*: {result.cstar_m_per_s:.6f} m/s")
    print(f"Isp status (missing mass): {missing.isp_status}")
    print(f"C* status (missing throat): {missing_throat_result.cstar_status}")
    print("C* / ISP REGRESSION PASSED")


if __name__ == "__main__":
    main()
