# Changelog

All notable changes to RMCS Analyzer are documented here.

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
