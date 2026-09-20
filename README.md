# RMCS Analyzer

**Rocket Motor Characterization System Data Analysis Software**

RMCS Analyzer is a standalone Windows desktop application for analyzing rocket motor static-test data. It is designed to turn standardized test-stand measurements into traceable motor-performance results through an engineering-focused interface.

The application is being developed with Python, PySide6, PyQtGraph, NumPy, and Pandas. The long-term goal is a packaged Windows application that can be used without requiring Python or a development environment.

---

## Current Development Status

## v0.3.0

RMCS Analyzer v0.3.0 establishes **Campaign Analysis v1** as the next functional
milestone after the v0.2.0 Compare and project-workflow release.

### Completed in v0.3.0

- Campaign Analysis workspace for selecting multiple recorded tests.
- Population statistics for Total Impulse, Peak Thrust, Burn Time, Average Thrust,
  Isp, and C* when the underlying test results are available.
- Mean, median, minimum, maximum, population standard deviation, and coefficient
  of variation for campaign metrics.
- Metric Distribution visualization for the selected campaign metric.
- Campaign Thrust Curve visualization with absolute-time and normalized-burn-time
  views.
- Campaign thrust-curve population statistics including mean, median, standard
  deviation, minimum, and maximum.
- Campaign selections remain independent of the active individual test.
- Campaign selections persist in `.rmcs` project files and are restored when a
  project is reopened.
- Tests without completed analysis results are excluded from campaign calculations
  rather than being treated as zero-valued measurements.
- Existing v0.2.0 Compare, metadata, import, pressure-curve, and project workflows
  remain part of the current application.

RMCS Analyzer remains in active development.

The project has completed the core analysis-engine foundation and the first
functional video-analysis workflow. The authoritative analysis layer is
separate from the GUI and is protected by standalone regression/reference
tests. The current application also supports persistent RMCS projects,
interactive thrust analysis, synchronized test video playback, and a
functional configurable video-overlay system.

The current development priority is **functionality before visual polish**.
The video overlay system is considered functional enough for the current
milestone; final styling, rendered video export, and transparent overlay
export are intentionally deferred.

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
- Interactive thrust-curve visualization
- Test metadata and test-file panels
- Motor classification display
- Analysis reference and edge-case validation

The graphical interface is functional in its current foundation, while several workspace areas remain under development.

---

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
│       │
│       ├── analysis/
│       │   ├── analyzer.py
│       │   ├── events.py
│       │   ├── impulse.py
│       │   ├── motor_class.py
│       │   ├── performance.py
│       │   └── results.py
│       │
│       ├── data/
│       │   ├── csv_reader.py
│       │   └── models.py
│       │
│       ├── processing/
│       │   ├── alignment.py
│       │   ├── baseline.py
│       │   ├── cleaning.py
│       │   ├── event_model.py
│       │   ├── pipeline.py
│       │   ├── settings.py
│       │   └── validation.py
│       │
│       ├── project/
│       │   ├── project_file.py
│       │   ├── session.py
│       │   ├── test_model.py
│       │   └── validation.py
│       │
│       └── ui/
│           ├── branding.py
│           ├── header.py
│           ├── playback_controls.py
│           ├── results_panel.py
│           ├── test_files_panel.py
│           ├── test_info_panel.py
│           └── thrust_plot.py
│
├── test_data/
│   └── Zerox.csv
│
├── docs/
│   └── RMCS_ANALYZER_SPEC.md
│
├── test_analysis_engine.py
├── test_performance.py
├── test_reference_validation.py
├── test_reference_analysis.py
├── test_thrustcurve_reference.py
├── test_performance_edge_cases.py
├── test_motor_classification.py
├── test_cstar_isp.py
├── test_thrust_rate_metrics.py
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
test_performance.py
test_reference_validation.py
test_reference_analysis.py
test_thrustcurve_reference.py
test_performance_edge_cases.py
test_motor_classification.py
test_cstar_isp.py
test_thrust_rate_metrics.py
test_processing_analysis_path.py
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
- Data Table

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
- Video association/path
- Video synchronization state
- Playback position
- Overlay visibility/configuration
- Overlay positions and sizes
- Overlay event positions/visibility
- Overlay titles and selected result fields

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
10. Final rendered-video export and transparent overlay-video export are not
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

- Complete the **Compare** workflow
- Compare measured tests without duplicating analysis logic
- Treat simulation/reference data as optional additional curves on the Thrust Curve workspace
- Preserve project/test state while switching between comparisons

### Analysis and data workflow

- Additional pressure-curve analysis
- Improved event/data-quality workflows
- Explicit handling of padded pre-ignition and post-burn recording data
- More detailed engineering statistics
- Additional reference-motor comparison
- Time-resolved C* analysis when the available data supports it

### Simulation

- Simulation-curve workflow
- Measured-vs-simulation comparison
- Simulation overlay integration when real simulation data is available

The simulation workflow should not be treated as complete until the project
has real simulation data and a defined import/data model.

### Export

Future export work may include:

- Broader engineering-data export
- RASP `.eng`
- RockSim `.rse`
- OpenRocket-compatible data
- BurnSim-compatible workflows
- OpenMotor-compatible workflows

### Video

After the underlying curve/analysis workflows are mature:

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
