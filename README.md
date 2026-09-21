# RMCS Analyzer

**Rocket Motor Characterization System Data Analysis Software**

RMCS Analyzer is a standalone Windows desktop application for analyzing rocket motor static-test data. It is designed to turn standardized test-stand measurements into traceable motor-performance results through an engineering-focused interface.

The application is being developed with Python, PySide6, PyQtGraph, NumPy, and Pandas. The long-term goal is a packaged Windows application that can be used without requiring Python or a development environment.

---

## Current Development Status

## v0.4.0

RMCS Analyzer v0.4.0 establishes **Simulation Integration, Expanded Video
Analysis, PDF Reporting, and BurnSim Export** as the current functional
milestone after the v0.3.0 Campaign Analysis release.

### Completed in v0.4.0

- Project-level simulation import from BurnSim/OpenMotor-style CSV data.
- Simulator-independent simulation normalization for time, thrust, and pressure.
- Simulation comparison on the Thrust Curve workspace.
- Simulation comparison on the Pressure Curve workspace.
- Persistence of imported simulation data inside `.rmcs` projects.
- Independent video Thrust and Pressure graph overlays.
- Simultaneous Thrust and Pressure video overlays.
- Simulation curves on the corresponding video graph overlays.
- Persistent video overlay positions, sizes, visibility, and related presentation
  state.
- Improved saved-project video source restoration.
- Synthetic simulation fixtures for regression testing.
- Continued Campaign Analysis v1 functionality from v0.3.0.
- Campaign-level and single-test PDF reports.
- Conditional PDF sections based on available pressure, simulation, video, and notes data.
- User-selectable PDF report video frame stored with each test.
- Automatic PDF representative-frame fallback remains available when no frame is selected.
- Selected PDF frame timestamp persists in `.rmcs` projects without changing project format 3.
- PDF video evidence preserves the source video's native aspect ratio.
- PDF reports use the authoritative standardized analysis results rather than duplicating engineering calculations.
- BurnSim CSV export from the measured RMCS test trace, including the complete pre-ignition through post-burnout recording.

RMCS Analyzer remains in active development.

The project has completed the core analysis-engine foundation and now has
functional test, campaign, simulation-comparison, and synchronized video
analysis workflows. The authoritative analysis layer remains separate from the
GUI and is protected by standalone regression/reference tests.

The current development priority remains **functionality before final visual
polish**. PDF reporting and BurnSim export are complete. The remaining planned
interchange/data exports are OpenMotor and Analysis CSV, followed by the broader
GUI and production-readiness refinement. Final rendered-video export and
transparent overlay-video export remain separate future capabilities.

The current architecture is:

```text
Standardized CSV / RMCS Project
      │
      ▼
   CSV Reader
      │
      ▼
    TestData
      │
      ▼
ProcessingPipeline
      │
      ├── Validation / preparation
      ├── Timeline selection
      ├── Cleaning / trimming
      ├── Baseline correction
      ├── Physical event detection
      └── Time alignment
      │
      ▼
 Prepared TestData
      │
      ▼
 AnalysisEngine
      │
      ├── Performance reduction
      ├── Statistical analysis
      ├── Motor classification
      └── Performance extensions (Isp / C*)
      │
      ▼
 AnalysisResults
      │
      ├── GUI
      └── Future exports

TestModel / TestSession
      │
      ├── AnalysisResults
      ├── Test metadata
      └── VideoState
              │
              ├── Video association
              ├── Synchronization
              ├── Playback state
              └── Overlay configuration
```

A major design requirement is that the GUI does not independently calculate
authoritative engineering results. Analysis is performed by the analysis
layer and exposed through `AnalysisResults`.

---

## Current Features

The current codebase supports:

- Standardized RMCS CSV import
- Test metadata parsing
- Original acquisition-time preservation
- Optional calibrated-time handling
- Data validation
- Data cleaning and trimming
- Baseline correction
- Physical event detection
- Time alignment
- Peak thrust analysis
- 5% standardized burn-time analysis
- Total impulse calculation
- Standardized average thrust
- Initial thrust averaging
- Motor impulse-class classification
- Calculated performance designation
- Basic statistical results
- Thrust rise and decay rates
- Specific impulse (Isp) when propellant mass is available
- Characteristic velocity (C*) when chamber pressure, propellant mass, and nozzle throat data are available
- Project/session persistence
- Campaign Analysis
- Campaign metric population statistics
- Campaign metric distribution visualization
- Campaign thrust-curve population comparison
- Persistent Campaign test selection
- Project-level simulation import and persistence
- BurnSim/OpenMotor-style simulation comparison
- BurnSim measured-data CSV export
- Thrust and pressure simulation overlays
- Independent synchronized video Thrust and Pressure graph overlays
- Persistent video overlay positions and configuration
- Selectable PDF report video frame
- Campaign and individual-test PDF report generation
- Interactive thrust-curve visualization
- Test metadata and test-file panels
- Motor classification display
- Analysis reference and edge-case validation

The graphical interface is functional in its current foundation, while several workspace areas remain under development.

---

## PDF Report Video Frame Selection

The Video Analysis workspace supports selecting the exact video moment that should appear in the PDF report.

### Workflow

1. Load a test with an associated video.
2. Play or scrub to the desired video moment.
3. Click **Use Current Frame** in the Video Analysis controls.
4. The selected video timestamp is displayed as the PDF report frame.
5. Save the `.rmcs` project if the selection should persist.
6. Generate the PDF report normally.

The selected timestamp is stored in **video time**, preserving RMCS Analyzer's existing video timeline and Sync Start model. Clicking **Clear Selection** returns the report to its automatic representative-frame behavior.

The `.rmcs` project format remains **3**; the PDF-frame timestamp is an additive video-state field.

PDF export decodes the selected frame forward from the beginning of the source video rather than relying on a non-zero MP4 seek. This avoids Windows Qt multimedia seek/backend issues while preserving the selected timestamp and the video's native aspect ratio.

## PDF Reporting

PDF reporting is the first completed export workflow.

The PDF exporter supports two report modes:

### Single-test report

A one-test campaign produces a compact motor test report containing only
sections supported by the available data:

- Measured thrust profile
- Pressure analysis when pressure data is available
- Simulation comparison when simulation data is available
- Engineering analysis and detected events
- Data-quality/acquisition information
- Video Evidence when a video is available

Campaign population analysis is omitted for a single-test report.

### Multi-test campaign report

A campaign containing multiple analyzed tests includes:

- Campaign overview
- Test summary
- Population-level Campaign Analysis
- Individual test reports
- Video Evidence for tests that have video

Optional sections are omitted rather than rendered as empty placeholders.

### Video evidence

If a PDF frame is selected for a test, the report uses that stored video
timestamp. Otherwise the exporter selects a representative frame automatically.
The source video's native aspect ratio is preserved.

The PDF exporter consumes authoritative `AnalysisResults` and project/test state.
It does not recalculate motor-performance metrics independently of the analysis
layer.

## Standardized CSV Format

RMCS Analyzer uses a defined CSV structure rather than treating arbitrary CSV files as interchangeable input.

The current reference format is **Format Version 1.0**.

The official development reference dataset is:

```text
test_data/Zerox.csv
```

### Metadata

The CSV contains metadata as `key,value` pairs followed by the measurement table.

The standardized metadata fields include:

```text
Format Version
Test Number
Test Date
Test Stand
Test Operator
Location
Notes
Motor Designation
Motor Type
Manufacturer
Builder
Case Material
Motor Diameter (in)
Motor Length (in)
Initial Mass (g)
Propellant Mass (g)
Propellant Type
Nozzle Throat Diameter (in)
Nozzle Exit Diameter (in)
Nozzle Material
Load Cell
Load Cell Calibration
Pressure Sensor
Pressure Sensor Calibration
Sample Rate (Hz)
```

### Measurement columns

The standardized measurement table uses:

```text
Sample
Time(s)
Time Cal (s)
Raw Thrust (N)
Prop Loss (kg)
Thrust (N)
Pressure (psi)
```

`Sample`, `Time(s)`, and `Thrust (N)` are required.

The other measurement columns are optional. When present, they are preserved by the data model.

### Authoritative thrust

`Thrust (N)` is the authoritative thrust measurement used by RMCS Analyzer.

The analyzer does **not** reconstruct authoritative thrust from `Raw Thrust (N)` and `Prop Loss (kg)`. Those channels are retained as supporting data when supplied by the test stand.

### Time handling

Original `Time(s)` data is preserved.

When a valid `Time Cal (s)` channel is supplied, it can be used as the analysis timeline while the original acquisition time remains available. When calibrated time is unavailable, the original time is used and the processing pipeline can perform its configured alignment.

---

## Analysis Methodology

The analysis engine separates physical event detection from standardized motor-performance reduction.

This distinction is important because a physical event such as detected burnout is not automatically the same thing as the standardized burn-time definition used for motor statistics.

### Peak thrust

Peak thrust is the maximum finite positive thrust value in the valid analysis curve.

Negative thrust values are not treated as positive thrust by taking their absolute value.

### Standardized burn time

The current standardized performance reduction uses a **5% of peak-thrust threshold**.

The burn interval is determined by:

1. Finding peak positive thrust.
2. Calculating 5% of peak thrust.
3. Finding the threshold crossing before peak thrust.
4. Finding the threshold crossing after peak thrust.
5. Linearly interpolating crossing times when the threshold falls between samples.

The resulting interval defines the standardized burn time:

```text
Burn time = 5% end time - 5% start time
```

This approach follows the methodology documented by ThrustCurve Motor Statistics and the project's current reference-validation work.

### Average thrust

Standardized average thrust is calculated from the impulse within the standardized 5% burn interval divided by the standardized burn time.

The total impulse used for motor classification is treated separately.

### Total impulse

Total impulse is obtained by integrating the valid thrust curve over the full valid test curve rather than truncating the integration to the standardized 5% burn interval.

Negative thrust values are excluded from the positive-thrust impulse calculation.

The exact handling of invalid/non-finite samples and duplicate timestamps is implemented by the performance-reduction layer and covered by regression tests.

### Initial thrust

The current performance reduction also calculates an initial-thrust average over the first **0.5 seconds** beginning at the standardized burn start.

### Motor classification

Motor class is determined from measured total impulse.

The current classification system covers the standard A through O ranges used by the analyzer and also supports fractional low-power designations implemented by the motor-class calculator.

### Performance designation

The calculated designation combines:

```text
Impulse class + rounded standardized average thrust
```

For example:

```text
N2031
```

The calculated designation describes the measured test performance. It is not intended to replace or infer a manufacturer's certified commercial-motor designation.

---

## Reference Validation

The analysis foundation is validated against both the project's Zerox reference data and an external published thrust-curve reference.

### Zerox reference

The current Zerox dataset contains:

```text
661 samples
Original acquisition duration: 8.538 s
Calculated acquisition sample rate: 77.301 Hz
Maximum thrust: 3230.339730 N
```

The current standardized reduction produces:

```text
5% start:             0.044210 s
5% end:               7.117326 s
5% burn time:         7.073116 s
Total impulse:    14471.744320 N·s
Normalized impulse: 14367.091390 N·s
Average thrust:      2031.225247 N
Initial average:     2635.834021 N
Impulse class:       N
Designation:         N2031
```

These values are regression references for the current implementation.

The Zerox test video displays the label **N2300**. The label is retained
only as source-video context and is **not** used as an independent
validation target or as the measured designation produced by the Analyzer.

The current validation work confirms that the CSV and video agree on the
recorded test duration and peak thrust. The current analyzer reduction of
the supplied CSV produces N2031 using the documented standardized
methodology.

### ThrustCurve G73C reference

The project also validates the standardized reduction against a published G73C thrust curve.

The published reference reports approximately:

```text
Total impulse:       128.64 N·s
Peak thrust:          96 N
5% threshold:          4.8 N
5% burn time:           1.814 s
Average thrust:        70.90 N
```

The analyzer's reduction is within the current validation tolerances for those published values.

This reference validation is important because it tests the methodology against an established motor-performance dataset rather than only checking internal consistency.

---

## Project Architecture

The source tree is organized by responsibility.

```text
RMCS_Analyzer/
│
├── main.py
│
├── src/
│   └── rmcs_analyzer/
│       ├── analysis/
│       ├── data/
│       ├── processing/
│       ├── project/
│       ├── simulation/
│       ├── export/
│       └── ui/
│
├── test_data/
│   └── Zerox.csv
│
├── sim_data/
│   ├── Synthetic-Simulation-BurnSim.csv
│   └── Synthetic-Simulation-OpenMotor.csv
│
├── docs/
│   └── RMCS_ANALYZER_SPEC.md
│
├── test_analysis_engine.py
├── test_campaign_analysis.py
├── test_cstar_isp.py
├── test_motor_classification.py
├── test_pdf_report.py
├── test_performance.py
├── test_performance_edge_cases.py
├── test_processing_analysis_path.py
├── test_reference_analysis.py
├── test_reference_validation.py
├── test_simulation_import.py
├── test_simulation_project.py
├── test_thrust_rate_metrics.py
├── test_thrustcurve_reference.py
├── test_video_pdf_frame_selection.py
├── test_video_simulation_state.py
├── test_burnsim_export.py
│
├── .gitignore
└── README.md
```

The exact source tree may expand as additional subsystems are implemented.

---

## Test Suite

The project uses standalone Python validation scripts rather than a pytest-based test suite.

The current canonical tests are:

```text
test_analysis_engine.py
test_campaign_analysis.py
test_cstar_isp.py
test_motor_classification.py
test_pdf_report.py
test_performance.py
test_performance_edge_cases.py
test_processing_analysis_path.py
test_reference_analysis.py
test_reference_validation.py
test_simulation_import.py
test_simulation_project.py
test_thrust_rate_metrics.py
test_thrustcurve_reference.py
test_video_pdf_frame_selection.py
test_video_simulation_state.py
```

These tests cover:

- Analysis-engine integration
- Standardized performance reduction
- Zerox regression values
- Zerox/video investigation calculations
- Published G73C reference validation
- Linear threshold interpolation
- Irregular timestamps
- Negative thrust handling
- Non-finite samples
- Duplicate timestamps
- Full-curve versus normalized-interval impulse
- Motor impulse-class boundaries
- Motor-class transitions
- Isp calculation and missing-input handling
- C* calculation and missing-input handling
- Thrust rise/decay-rate calculation
- Performance designation
- Raw-data protection
- Processing-pipeline integration
- Campaign population statistics and curve alignment
- Simulation CSV normalization and project persistence
- PDF report generation for single tests and multi-test campaigns
- PDF video-frame selection and persistence
- Video simulation-state persistence

The test suite is intended to protect the authoritative analysis layer as the GUI and future features are developed.

---

## Current GUI

The desktop interface currently includes:

### Application shell

- RMCS Analyzer branding and application status
- Import/open controls
- Save project controls
- Application Settings
- Persistent test/project state

### Workspaces

The application provides the current workspace structure for:

- Thrust Curve
- Data Table
- Analysis
- Pressure Curve
- Compare
- Campaign

Campaign Analysis is functional for comparing completed recorded test results
at the population level. Additional campaign workflows and broader export and
simulation capabilities remain future development areas.

### Campaign Analysis

The Campaign workspace operates on selected completed tests in the current
project. It provides:

- Population statistics for Total Impulse, Peak Thrust, Burn Time, Average Thrust,
  Isp, and C*.
- Mean, median, minimum, maximum, population standard deviation, and coefficient
  of variation.
- A metric distribution view for the selected campaign metric.
- A campaign thrust-curve view using either absolute burn time or normalized
  burn time.
- Population curve statistics including mean, median, standard deviation,
  minimum, and maximum.
- Automatic exclusion of tests that do not contain completed analysis results.
- Project-level persistence of the Campaign test selection.

Campaign selection is independent of the active individual test. Changing which
test is displayed must not silently change which tests are included in Campaign
Analysis.

### Side panels

The current dashboard includes areas for:

- Test Information
- Test Files
- Key Results
- Additional Metrics
- C* Analysis
- Motor Classification

### Thrust analysis

The current thrust-curve view provides:

- Interactive PyQtGraph visualization
- Standardized 5% burn-start and burn-end annotations
- Peak-thrust annotation
- Physical/diagnostic event information
- Time/thrust cursor readout
- Post-burnout visualization
- Zero reference line
- Authoritative analysis results from the analysis layer

### Video analysis

A functional video-analysis workflow is now implemented.

When a test has an associated video, RMCS Analyzer supports:

- Per-test video file association
- Video playback with normal audio/video playback
- RMCS timeline synchronization
- Manual Sync Start adjustment
- Play / pause / reset controls
- Timeline scrubbing
- Video pop-out / enlarged viewing
- Synchronized thrust-curve marker
- Current-thrust display during playback
- Results and event synchronization
- Configurable video overlays

The video timeline is the master timeline when video is loaded. The full
video duration is preserved.

`Sync Start` means:

> the video timestamp at which RMCS test time `t = 0` begins.

Therefore:

```text
Before Sync Start
    → video plays normally
    → RMCS marker/results are inactive

At Sync Start
    → RMCS t = 0 begins

During RMCS test
    → curve marker and synchronized results follow RMCS time

After the RMCS curve ends
    → marker remains at the final curve point
    → video continues through its remaining duration
```

Without a loaded video, the RMCS timeline remains usable on its own.

### Video Overlay System

The current overlay system provides a functional foundation for analysis
video presentation.

It currently supports:

- Measured-thrust curve overlay
- Results overlay
- Individual event overlays/markers
- Ignition, peak-thrust, and burnout event visibility
- Draggable/resizable overlay objects
- Persistent per-test overlay positions
- Configurable overlay titles
- Selectable result fields
- Curve grid visibility
- Curve axes/scale visibility
- Curve background visibility
- Overlay settings through the application Settings dialog

Overlay state is stored with the individual test and persists when switching
tests and when saving/loading an `.rmcs` project.

The current overlay presentation is intentionally considered a functional
v1 system rather than final visual polish. Chart styling, typography,
spacing, event presentation, and other presentation refinements remain
future work.

### RMCS Project persistence

`.rmcs` is the native project format.

A project stores the working state needed to reopen a test, including:

- Test metadata
- Imported test data
- Analysis results
- Project-level simulation data, when imported
- Video association/path
- Video synchronization state
- Playback position
- Overlay visibility/configuration
- Independent Thrust and Pressure overlay positions and sizes
- Overlay event positions/visibility
- Overlay titles and selected result fields
- Selected PDF report frame timestamp

The video file itself is referenced by path rather than embedded in the
`.rmcs` project.

---

## Current Video / Overlay Design Rules

These rules describe the current implementation and should be preserved as
the system develops:

1. The RMCS analysis timeline and video timeline are synchronized, but the
   video itself is not clipped to the RMCS curve.
2. `Sync Start` identifies the video timestamp corresponding to RMCS `t=0`.
3. The complete source-video duration remains available.
4. Before synchronization begins, video playback continues without an RMCS
   marker or active test metrics.
5. After the measured curve ends, the video continues while the RMCS marker
   remains at the final curve point.
6. Video state belongs to the individual test, not to the global application.
7. Overlay settings that describe the presentation of a test video are
   persisted with that test.
8. Global application settings remain appropriate for global/default
   configuration; test-specific video state belongs in the `.rmcs` project.
9. No-video operation remains a supported analyzer workflow.
10. The current video overlay system supports independent measured
    Thrust and Pressure graph overlays.
11. Thrust and Pressure overlays may be displayed simultaneously.
12. When simulation data is loaded, the corresponding simulation curve may be
    shown on the Thrust and Pressure overlays.
13. Final rendered-video export and transparent overlay-video export are not
    yet implemented.

---

## Dashboard Visual Direction

The GUI is being developed against a project visual reference established during the design process. The reference defines the intended overall composition rather than the exact values shown in the mockup.

The target dashboard uses:

- A dark engineering-focused visual theme
- A three-column application layout
- Test information and file navigation on the left
- The primary analysis workspace in the center
- Key results and engineering metrics on the right
- Tabbed analysis workspaces
- Dedicated lower panels for video, exports, and motor classification
- Clear visual distinction between measured data, calculated results, and unavailable/estimated inputs
- Consistent status/event colors without allowing annotations to obscure the thrust curve

The mockup is the visual reference for layout and presentation. The authoritative analysis engine remains the source of all engineering values.

## Planned Development

Development is intentionally proceeding in functional milestones.

### Immediate / next major milestone

- Implement the remaining planned engineering/data interchange exports.
- Keep export calculations driven by the authoritative `AnalysisResults` and
  project/test data rather than duplicating analysis logic.
- Validate exported data against the existing RMCS analysis results.

The PDF report export is complete and should be treated as a stable export
workflow rather than part of the remaining export work.

### Analysis and data workflow

- Additional pressure-curve analysis
- Improved event/data-quality workflows
- Explicit handling of padded pre-ignition and post-burn recording data
- More detailed engineering statistics
- Additional reference-motor comparison
- Time-resolved C* analysis when the available data supports it

### Simulation

The core simulation-import and comparison workflow is now functional.

Current simulation behavior:

- Import one project-level simulation dataset from CSV.
- Normalize imported time to seconds, thrust to Newtons, and pressure to psi.
- Support BurnSim/OpenMotor-style column naming without making simulator identity
  a requirement for parsing.
- Preserve the imported simulation inside the `.rmcs` project.
- Allow independent simulation visibility on the Thrust Curve and Pressure Curve
  workspaces.
- Allow simulation visibility on the corresponding video graph overlays.

### Export

The export panel exposes the completed PDF Report and BurnSim CSV workflows,
with placeholders for the remaining exports.

Completed:

- PDF report
- BurnSim CSV export

BurnSim export details:

- Uses the complete measured RMCS trace rather than simulation or derived engineering data.
- Exports `Time,Pressure,Thrust` in seconds, psi, and newtons.
- Retains pre-ignition and post-burnout samples.
- Includes the CSV header required by the documented BurnSim 4 import workflow.
- Does not add an RMCS-specific metadata or units row.
- The exported data has been independently checked against Synthetic-Test-01, Synthetic-Test-03, and Zerox reference data.

Remaining planned exports:

- OpenMotor
- Analysis CSV

RockSim and OpenRocket exports are intentionally not part of the current
export roadmap.

Each export must use the authoritative analysis/result model and clearly
distinguish measured data, calculated results, and exported metadata.

### Video

The current synchronized video-analysis workflow is functional, including
independent Thrust and Pressure graph overlays and optional simulation curves.

Future video work includes:

- Final rendered-video export at source resolution
- Transparent overlay-video export for external video software such as OBS
  or DaVinci Resolve
- Additional synchronized analysis presentation features

### Final polish

After core functionality is established:

- Final overlay visual styling
- Typography and spacing refinement
- Chart styling
- Results presentation refinement
- Event presentation refinement
- Broader GUI polish
- Production-readiness review and cleanup

### Packaging

The final application is expected to be distributed as a Windows desktop
application using a packaging workflow such as PyInstaller.

---

## Development Environment

Current development uses:

- Python 3.14
- PySide6
- PyQtGraph
- NumPy
- Pandas
- VS Code
- Python virtual environment
- Git
- GitHub Desktop

The project is currently developed and executed from the local Python environment.

The virtual environment is intentionally excluded from source control.

---

## Design Goals

### Standalone

The finished application should operate as a normal desktop application rather than requiring users to work from a Python terminal. The current development environment remains Python-based.

### Modular

Data import, processing, analysis, visualization, persistence, and export should remain separated into independent components.

### Traceable

Calculated values should be traceable to the underlying measurement data and documented analysis methodology.

### Engineering-Focused

The application should provide useful engineering information without hiding how the reported values were produced.

### Extensible

The architecture should support future RMCS firmware output as well as additional standardized-compatible test data.

### Protected Analysis Core

The GUI should consume authoritative analysis results rather than implementing separate calculations that could diverge from the analysis engine.

---

## Safety and Engineering Disclaimer

RMCS Analyzer is software for analyzing and visualizing rocket motor test data.

The software does not replace applicable safety procedures, testing standards, certification requirements, engineering review, or professional judgment.

Users are responsible for validating measurements, calculations, assumptions, and conclusions produced by the software.

---

## License

License information will be added as the project develops.
