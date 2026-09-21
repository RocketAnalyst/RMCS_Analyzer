# Changelog

All notable changes to RMCS Analyzer are documented here.

## [0.4.0] - 2026-09-20

### Added

- Project-level simulation data import from BurnSim/OpenMotor-style CSV output.
- Simulator-independent normalized simulation data model using seconds, Newtons,
  and psi internally.
- Simulation comparison controls on the Thrust Curve and Pressure Curve
  workspaces.
- Project-level simulation persistence inside `.rmcs` project files.
- Simulation project round-trip regression coverage.
- Independent video Thrust and Pressure graph overlays that can be displayed
  simultaneously.
- Simulation curves on the corresponding video Thrust and Pressure overlays.
- Persistent video overlay positions and sizes for the independent curve
  overlays.
- Video simulation overlay state persistence.
- Synthetic BurnSim-style and OpenMotor-style simulation fixtures based on the
  existing synthetic RMCS test population.

### Changed

- Expanded the functional video overlay system to support both measured thrust
  and pressure curves.
- Improved saved-project video source restoration when projects are moved and
  the original absolute video path is no longer available.
- Preserved the RMCS project format at version 3 because the simulation state
  is an additive extension within the existing project format.
- Kept the standardized RMCS CSV format at version 1.0.
- Corrected video overlay rendering so pressure curves are rendered as line
  overlays without unintended area fill.
- Corrected saved `.rmcs` project loading so a successfully opened project
  returns to a clean `READY` state rather than being incorrectly marked
  `MODIFIED`.

### Validation

- Simulation CSV import regression tests cover normalized BurnSim-style and
  OpenMotor-style fixtures.
- Simulation project persistence tests cover save/load round trips and legacy
  projects without simulation data.
- Video simulation-state persistence tests cover simulation visibility and
  existing video overlay state.
- Existing analysis, processing, classification, performance, reference, and
  Campaign Analysis regression tests remain part of the project test suite.

## [0.3.0] - 2026-09-20

### Added

- Campaign Analysis v1 workspace for population-level analysis of completed
  recorded motor tests.
- Campaign metric statistics for Total Impulse, Peak Thrust, Burn Time,
  Average Thrust, Isp, and C*.
- Mean, median, minimum, maximum, population standard deviation, and coefficient
  of variation reporting for campaign metrics.
- Metric Distribution visualization.
- Campaign Thrust Curve visualization.
- Absolute burn-time and normalized burn-time campaign curve views.
- Population thrust-curve statistics including mean, median, standard deviation,
  minimum, and maximum.
- Persistent project-level Campaign test selection.

### Changed

- Added Campaign selection state to the RMCS project manifest.
- Restored Campaign selection when an `.rmcs` project is reopened.
- Kept Campaign selection independent from the active individual test.
- Added duplicate-selection prevention through source-based test selection.
- Preserved compatibility with older projects that do not contain Campaign
  selection state.

### Validation

- Campaign analysis regression tests cover population metric statistics,
  missing-metric handling, and campaign curve alignment/normalization.
- Existing analysis-engine, performance, classification, processing, and
  reference-validation tests remain part of the regression suite.

## [0.2.0] - 2026-09-19

### Added

- Multi-test Compare workspace with thrust-curve overlays and key metrics.
- Dedicated Pressure Curve workspace.
- Editable project-level test metadata overrides.
- Metadata reset to source-CSV values.
- Persistent metadata overrides in `.rmcs` projects.
- Multi-file RMCS CSV import.
- Removal of tests from the current project without deleting source CSV files.

### Changed

- Compare selection state remains independent of the active individual test.
- Original imported CSV/source data remains separate from project-level metadata
  overrides.
