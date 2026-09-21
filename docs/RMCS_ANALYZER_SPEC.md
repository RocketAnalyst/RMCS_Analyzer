# RMCS Analyzer Specification

## 1. Project Identity

```text
Project:              RMCS Analyzer
Current release:      v0.4.0
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
    +--> Analysis CSV (planned)
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

### 3.2 Video Analysis

Video analysis supports:

- video association with tests
- synchronization using a Sync Start point
- independent Thrust and Pressure graph overlays
- measured Results and Events overlays
- simulation overlays
- persisted overlay presentation state
- selectable PDF report frame

The full video timeline remains distinct from the RMCS analysis timeline.

### 3.3 PDF Reporting

PDF reporting supports:

- compact single-test reports
- campaign reports
- conditional pressure/simulation/video sections
- authoritative analysis results
- selected or automatic representative video evidence
- native source-video aspect ratio preservation

Optional sections are omitted when the underlying data is unavailable.

### 3.4 BurnSim CSV Export

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

### 3.5 RASP / `.ENG` Export

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

### 3.6 Export Roadmap

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
- Analysis CSV — next functional export
- PDF Report — complete
- Video — v2 future feature placeholder
- Overlay — v2 future feature placeholder

OpenMotor export was removed from the roadmap because openMotor does not
provide a meaningful direct experimental-test-data import workflow for RMCS
test traces.

## 4. Campaign Behavior

Campaign selection is independent of the active individual test.

For RASP export:

- one selected test -> one-entry `.eng`
- multiple selected tests -> one multi-entry `.eng`
- campaign curves are preserved individually rather than averaged

The campaign export therefore represents the actual tested population and does
not hide firing-to-firing performance differences.

## 5. Engineering Authority

The application must continue to use `AnalysisResults` as the engineering
source of truth.

Exports must consume authoritative analysis results or measured source data
according to the purpose of the format. They must not duplicate engineering
calculations in the GUI.

## 6. Versioning

Current versions:

```text
Application:     v0.4.0
Project format:  3
CSV format:      1.0
```

An export feature addition does not automatically require a project-format
change.

## 7. Remaining v0.4.0 Work

The next functional export is Analysis CSV.

After the remaining export functionality is complete, the project moves into
the final overall refinement / production-readiness pass, including UI/layout
polish, chart presentation, consistency, and final regression validation.

Video and Overlay file export are intentionally deferred to v2.
