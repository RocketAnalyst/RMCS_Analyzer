# RMCS Analyzer Specification

## 1. Project Identity

```text
Project:              RMCS Analyzer
Current release:      v1.0.0
v1.0 status:           Feature-complete; final code review and QA complete
Project format:       .rmcs format 3
Reference CSV format: 1.0
Primary language:     Python
GUI framework:        PySide6
Plotting:             Matplotlib
Source control:       Git / GitHub
```

RMCS Analyzer is a desktop engineering application for analyzing rocket motor
static-test data, managing test sessions, comparing tests and campaigns,
visualizing pressure/thrust/simulation data, synchronizing test video, and
producing engineering-oriented reports and exports.

## 2. Architecture

The authoritative engineering calculations remain in the analysis layer.
The GUI displays those results and manages interaction; it does not duplicate
engineering calculations.

```text
CSV / Project
    |
    v
TestData / TestModel
    |
    v
ProcessingPipeline
    |
    v
AnalysisEngine
    |
    v
AnalysisResults
    |
    +--> GUI
    +--> PDF
    +--> BurnSim CSV
    +--> RASP / .ENG
    +--> Analysis CSV
```

Project/session state owns metadata overrides, campaign selections, video state,
simulation state, and other information that must persist across project saves.

The `.rmcs` project format remains version 3. The v0.4.0 simulation, video, and
PDF-frame state additions are additive and do not require a project-format bump.

## 3. v0.4.0 Completed Functionality

### 3.1 Simulation Integration

RMCS Analyzer supports project-level import of BurnSim/OpenMotor-style simulation
CSV data using a simulator-independent normalized representation.

Simulation data can be displayed on:

- Thrust Curve
- Pressure Curve
- Video Thrust overlay
- Video Pressure overlay

Simulation state and video overlay presentation state persist in `.rmcs`
projects.

### 3.2 Simulation CSV Import Format

RMCS Analyzer accepts simulator-independent CSV output from BurnSim/OpenMotor-style
sources.

Required structure:

- recognizable time column
- at least one recognizable thrust or pressure column
- numeric data rows
- monotonically non-decreasing time

Recognized time units:

```text
s, ms, us
```

Recognized thrust units:

```text
N, lbf, kgf
```

Recognized pressure units:

```text
psi, Pa, kPa, MPa, bar, atm
```

The importer normalizes all simulation data internally to:

```text
time    = seconds
thrust  = newtons
pressure = psi
```

Simulator identification is metadata only and does not change parsing behavior.
RMCS Analyzer provides blank BurnSim and OpenMotor simulation import templates
through Settings to document the expected CSV structure.

Measured test analysis remains authoritative when simulation and measured data
are displayed together.

### 3.3 Video Analysis

Video analysis supports:

- video association with tests
- synchronization using a Sync Start point
- independent Thrust and Pressure graph overlays
- measured Results and Events overlays
- simulation overlays
- persisted overlay presentation state
- selectable PDF report frame

The full video timeline remains distinct from the RMCS analysis timeline.

### 3.4 PDF Reporting

PDF reporting supports:

- compact single-test reports
- campaign reports
- conditional pressure/simulation/video sections
- authoritative analysis results
- selected or automatic representative video evidence
- native source-video aspect ratio preservation

Optional sections are omitted when the underlying data is unavailable.

### 3.5 BurnSim CSV Export

BurnSim export produces:

```text
Time,Pressure,Thrust
```

with:

- time in seconds
- pressure in psi
- thrust in newtons
- a header row
- the complete measured recording, including pre-ignition and post-burnout

This export is experimental-test-data interchange and is intentionally different
from the RASP export.

BurnSim export was validated against Synthetic-Test-01, Synthetic-Test-03,
and Zerox reference data and against the documented BurnSim CSV structure.
Direct import into BurnSim was not performed because BurnSim is not available
in the development environment.

### 3.6 RASP / `.ENG` Export

RASP export produces the standard `.eng` motor-data format used by flight
simulation software.

The exporter uses the authoritative standardized measured thrust curve rather
than the complete experimental recording used by BurnSim.

A single-test export contains one motor entry.

A multi-test Campaign export contains one motor entry for every selected
Campaign test. Curves are not averaged together. This preserves real
test-to-test variation in measured motor performance.

Each entry includes the required RASP motor header fields and a reduced
time/thrust curve with:

- increasing time
- positive thrust values through the measured curve
- retained peak-thrust behavior
- the standardized burn endpoint
- a final zero-thrust point

Static-test entries use `P` for the ejection/delay field.

The exporter remains limited to the RASP `.eng` interchange format; it does not
create proprietary OpenRocket or RockSim formats.

RASP export was validated using:

- Zerox single-test export
- five-test Synthetic campaign export

Validation confirmed valid entry structure and separate campaign motor entries.

### 3.7 Analysis CSV Export

Analysis CSV export produces one engineering-summary row per selected analyzed
test. The schema combines test metadata with authoritative `AnalysisResults`
values, including thrust, impulse, burn-time, Isp, C*, pressure, mass-flow,
classification, and event information.

A multi-test export contains one row per selected test. It does not create an
averaged campaign row.

### 3.8 Export Pane and Status

Current Export pane:

```text
BurnSim
RASP / .ENG Motor Curve
Analysis CSV
PDF Report
Video
Overlay
```

Status:

- BurnSim — complete
- RASP / `.ENG` — complete
- Analysis CSV — complete
- PDF Report — complete
- Video — v2 future feature placeholder
- Overlay — v2 future feature placeholder

OpenMotor export was removed from the roadmap because openMotor does not
provide a meaningful direct experimental-test-data import workflow for RMCS
test traces.

## 4. Application Settings, Themes, and Templates

The Settings dialog currently provides:

- Dark/Light application theme selection
- Video Overlay preferences
- Video display mode
- Overlay visibility
- Overlay titles
- Thrust chart grid/axis/background options
- Downloadable blank input templates

The Data Templates section is located under General → Appearance.

Available templates:

```text
RMCS Test Data Template
RMCS BurnSim Simulation Template
RMCS OpenMotor Simulation Template
```

The simulation templates describe the CSV import format RMCS Analyzer expects;
they are not native BurnSim/OpenMotor project files.

The Light theme is a functional application-wide presentation theme. Theme
selection persists across application launches. The engineering analysis layer
is unaffected by theme selection.

## 5. Compare Workspace Lifecycle

The Compare workspace supports synchronized multi-test thrust and pressure
visualization, event presentation, and comparison metrics.

Event annotations are scene-owned graphical items and must be explicitly removed
before comparison plots are refreshed. This prevents stale annotations from
accumulating and appearing as duplicate or ghost labels after selection,
visibility, or workspace refresh operations.

Compare selection remains independent of the active individual test.

## 6. Campaign Behavior

Campaign selection is independent of the active individual test.

For RASP export:

- one selected test -> one-entry `.eng`
- multiple selected tests -> one multi-entry `.eng`
- campaign curves are preserved individually rather than averaged

The campaign export therefore represents the actual tested population and does
not hide firing-to-firing performance differences.

## 7. Engineering Authority

The application must continue to use `AnalysisResults` as the engineering
source of truth.

Exports must consume authoritative analysis results or measured source data
according to the purpose of the format. They must not duplicate engineering
calculations in the GUI.

## 8. Versioning

Current versions:

```text
Application:     v1.0.0
Project format:  3
CSV format:      1.0
```

An export feature addition does not automatically require a project-format
change.

## 9. v1.0 Feature-Complete Status

The planned v1.0 engineering and data-analysis feature set is complete.

Completed v1.0 functionality includes:

- standardized RMCS CSV import and engineering analysis
- project/session persistence
- Compare workspace
- Pressure Curve workspace
- Campaign Analysis v1
- simulation CSV import and comparison
- synchronized video analysis
- measured and simulation Thrust/Pressure video overlays
- single-test and campaign PDF reporting
- BurnSim CSV export
- RASP / `.ENG` export
- Analysis CSV export

Analysis CSV provides one engineering-summary row per test. Campaign exports
contain one row per selected test and do not create an averaged campaign row.

The authoritative engineering results remain in `AnalysisResults`. Exporters
use authoritative analysis results or measured source data according to the
purpose of the format.

## 10. Final Review and QA

The v1.0 feature set is complete and the feature set is now frozen. Final code
review, cleanup, regression/QA, and representative manual QA are complete for
the v1.0.0 release baseline. Remaining work is release administration and final
documentation maintenance.

The code review will audit:

- obsolete/unused code and imports
- legacy state-machine remnants
- duplicated calculations or state
- plot and scene-item lifecycle
- signal/slot connections
- persistence and migration behavior
- theme/style consistency
- exporter boundaries
- repository hygiene

QA will cover:

- Zerox reference analysis
- single-test and multi-test workflows
- Compare and Campaign
- Thrust and Pressure workspaces
- Analysis and Data Table
- simulation import and comparison
- synchronized video and overlays
- PDF, BurnSim, RASP, and Analysis CSV exports
- Settings and downloadable templates
- Dark and Light themes
- `.rmcs` save/load and legacy compatibility

User-selectable display units are not part of the current v1.0 feature set.
The analysis engine continues to use its established engineering units.

## 11. Deferred v2 Functionality

Rendered video export and transparent overlay-video export remain deferred to
v2. The existing Video and Overlay export controls are intentionally presented
as future-feature placeholders.

## 12. Versioning

Current versions:

```text
Application:     v1.0.0
v1.0 status:     Feature-complete; final code review and QA complete
Project format:  3
CSV format:      1.0
```

The application and project format versions remain separate. Completing the
v1.0 feature set does not require a `.rmcs` format bump.

