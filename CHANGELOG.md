# Changelog

All notable changes to RMCS Analyzer are documented here.

## [0.4.0] - 2026-09-20

### RASP / `.ENG` Export

- Added functional RASP / `.ENG` motor-curve export.
- Single-test export produces one measured motor entry.
- Multi-test Campaign export produces one RASP motor entry per selected test
  rather than averaging campaign performance into one synthetic curve.
- RASP export uses the authoritative standardized measured thrust curve.
- Curve reduction preserves key thrust-curve features while remaining within
  the legacy-compatible RASP point-count limit.
- Static-test exports use `P` for the no-ejection-charge field.
- Added regression coverage for RASP header fields, curve validity, final
  zero-thrust points, and multi-entry campaign exports.
- Validated single-test Zerox and five-test synthetic campaign `.eng` outputs.
- Removed the planned OpenMotor export because openMotor does not provide a
  meaningful direct experimental-test-data import workflow.
- Added active Video and Overlay export buttons as explicit v2 future-feature
  placeholders rather than leaving dead controls in the GUI.


### Added

- Functional BurnSim CSV export from the measured RMCS test trace.
- BurnSim export uses the documented `Time,Pressure,Thrust` column order with a header and
  seconds / psi / newtons units.
- BurnSim export retains the complete recorded trace, including pre-ignition and post-burnout
  samples, rather than exporting only the standardized engineering analysis window.
- Campaign-level PDF reporting for multi-test projects.
- Compact single-test PDF reporting without population-level campaign analysis.
- Conditional PDF sections for pressure, simulation, notes, and video evidence.
- User-selectable PDF video frame support with `.rmcs` persistence.
- Automatic representative video-frame fallback when no PDF frame is selected.
- Native video aspect-ratio preservation in PDF video evidence.
- PDF regression coverage for report generation and selected-frame persistence.

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

- Completed the PDF reporting workflow using the authoritative standardized
  analysis results.
- PDF reports use separate single-test and multi-test campaign layouts.
- PDF video-frame extraction decodes forward from the source video to avoid
  unreliable non-zero MP4 seek behavior on the Windows Qt multimedia backend.
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

- BurnSim export was independently checked against Synthetic-Test-01, Synthetic-Test-03, and
  Zerox reference data for sample count, time range, peak values, and integrated impulse.
- BurnSim CSV structure was checked against the documented BurnSim 4 CSV import requirements.
- Direct runtime import into BurnSim has not been performed because BurnSim is not available
  in the current development environment.
- Simulation CSV import regression tests cover normalized BurnSim-style and
  OpenMotor-style fixtures.
- Simulation project persistence tests cover save/load round trips and legacy
  projects without simulation data.
- Video simulation-state persistence tests cover simulation visibility and
  existing video overlay state.
- PDF report tests cover single-test and campaign report generation,
  conditional sections, chart generation, and video-frame behavior.
- Existing analysis, processing, classification, performance, reference,
  simulation, video-state, Campaign Analysis, and BurnSim export regression tests
  remain part of the project test suite.

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
