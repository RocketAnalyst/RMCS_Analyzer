# RMCS Analyzer --- Development & Analysis Specification

**Status:** Authoritative project direction\
**Project:** RMCS Analyzer\
**Purpose:** Desktop software for analyzing standardized rocket motor
static-test data

## 1. Purpose

RMCS Analyzer is a standalone Windows desktop application for analyzing
standardized rocket motor static-test data.

The primary engineering goal is:

> Given a properly measured and formatted rocket-motor thrust test, RMCS
> Analyzer shall process and reduce the data using documented
> industry-standard motor-performance methodology so that its results
> are directly comparable to published/certification motor-performance
> data.

The application must produce reproducible, documented, testable
calculations rather than merely plausible numbers.

A single firing is not expected to exactly equal a manufacturer's
published representative or certification result. The software's
responsibility is to apply the same definitions and data-reduction
methodology where applicable.

## 2. Development Phases

### Phase 1 --- Project Cleanup

Before changing the motor-performance methodology:

1.  Audit the current codebase.
2.  Identify what every source file does.
3.  Identify obsolete, duplicate, experimental, or superseded code.
4.  Classify files as KEEP, REWORK, MERGE, DELETE, TEST, or UI.
5.  Simplify the architecture.
6.  Remove dead code and obsolete approaches.
7.  Organize tests.
8.  Ensure imports and dependencies are clean.
9.  Confirm the application runs.
10. Run the existing tests.

**Phase 1 must not change the intended industry-standard
motor-performance calculations.**

### Phase 2 --- Industry-Standard Analysis

After Phase 1 is stable:

1.  Establish the authoritative calculation engine.
2.  Implement the documented motor-performance methodology.
3.  Build reference tests using known thrust curves.
4.  Compare RMCS calculations with published/certification reference
    results.
5.  Correct discrepancies.
6.  Only after validation, connect the authoritative results to the GUI
    and exports.

## 3. Core Architecture

``` text
Standardized CSV / RMCS Project
            |
            v
       CSV Reader
            |
            v
        TestData
            |
            v
    Data Validation
            |
            v
       Processing
            |
            v
    Prepared TestData
            |
            +----------------------+
            |                      |
            v                      v
     Physical Events       Standard Reduction
            |                      |
            |               +------+------+
            |               |             |
            |               v             v
            |          Motor Metrics  Classification
            |               |
            +-------+-------+
                    |
                    v
              Analysis Results
                    |
          +---------+---------+
          |         |         |
          v         v         v
         GUI      Graphs    Exports
```

The GUI is a consumer of analysis results.

**The GUI must not independently calculate or modify authoritative
motor-performance results.**

## 4. Data Principles

### 4.1 Authoritative thrust

The standardized CSV column `Thrust (N)` is the authoritative thrust
measurement for performance analysis.

The Analyzer shall not reconstruct authoritative thrust from
`Raw Thrust (N) + Prop Loss (kg)` even when those channels are present.

Raw thrust and propellant-loss data may be retained for diagnostics and
engineering analysis.

### 4.2 Time

The original acquisition time `Time(s)` must be preserved.

If a valid `Time Cal (s)` channel is present, it is used as the analysis
timeline.

If it is absent or invalid, `Time(s)` is used.

The original acquisition timeline must never be silently destroyed.

### 4.3 Actual timestamps

Numerical calculations must use actual timestamps in the data. The
Analyzer must not assume every sample is separated by exactly
`1 / SampleRate` when actual timestamps are available.

## 5. Processing Rules

``` text
Raw TestData
    |
    v
Raw validation
    |
    v
Select analysis timeline
    |
    v
Data cleaning / preparation
    |
    v
Baseline correction
    |
    v
Prepared validation
    |
    v
Performance analysis
```

Processing must be deterministic and reproducible.

The raw imported dataset must remain available. Processing must not
silently overwrite original measurement values.

## 6. Baseline Correction

Baseline correction is permitted when required by the test setup.

The baseline correction method must be explicit and configurable.

Negative values after baseline correction are allowed and can represent
load-cell behavior or measurement offset after motor burnout.

Baseline correction must not be confused with motor-event detection.

## 7. Thrust Sign Convention

Motor-performance calculations use positive thrust.

The Analyzer must **never use absolute thrust magnitude** for
motor-performance calculations.

For example:

``` text
+3000 N = positive motor thrust
-100 N  = negative load-cell measurement, not 100 N of motor thrust
```

Therefore negative values cannot create peak thrust, trigger ignition,
trigger burnout, or become positive thrust through `abs(thrust)`.

The original processed curve may retain negative values for diagnostics
and graphing.

## 8. Peak Thrust

Peak thrust is the maximum positive thrust value in the valid processed
thrust curve.

``` text
Peak Thrust = max(thrust)
```

The time corresponding to the maximum is retained as peak time.

## 9. Physical Events vs Standardized Performance Events

The Analyzer shall distinguish between:

### Physical events

-   Physical ignition
-   Physical peak
-   Physical/recorded burnout
-   Other diagnostic events

### Standardized performance boundaries

-   5% burn start
-   5% burn end
-   Standard burn time

Physical burnout must not automatically determine standardized burn
time.

## 10. Standardized 5% Burn-Time Method

For standardized motor-performance reporting, RMCS shall use the
5%-of-peak method documented by ThrustCurve as the NFPA 1125-based
convention.

``` text
Threshold = Peak Thrust × 0.05
```

### 10.1 5% start

Find the first rising crossing of the 5% threshold during startup.
Interpolate between surrounding samples when appropriate.

### 10.2 5% end

Find the falling crossing of the same threshold after the burn.
Interpolate between surrounding samples when appropriate.

### 10.3 Standard burn time

``` text
Standard Burn Time = 5% End Time - 5% Start Time
```

This is the standardized burn time reported as the motor's burn time.

## 11. Total Impulse

Total impulse is the numerical integral of the valid thrust curve
according to the established industry methodology.

The implementation must use actual timestamps and numerical integration.

The Analyzer must distinguish the total-impulse integration window from
the 5%-normalized burn-time window.

ThrustCurve documents the NFPA 1125-based convention that total impulse
is measured over the whole thrust curve rather than being limited to the
5%-defined burn interval.

The exact treatment of invalid samples and negative post-burn
measurements must be explicitly implemented and covered by reference
tests rather than inferred from a convenient rule.

## 12. Standardized Average Thrust

Standardized average thrust is calculated from the impulse contained
within the standardized 5%-to-5% burn interval divided by standardized
burn time.

``` text
Normalized Impulse
------------------
Standard Burn Time
```

It must not simply be `Total Impulse / physical burnout time` unless
those windows happen to be identical.

## 13. Initial Thrust

Initial thrust is a separate performance metric.

For ThrustCurve-style reporting, the reference definition is the average
thrust during the first 0.5 seconds. The implementation must clearly
define how the 0.5-second interval is handled when sample boundaries do
not land exactly on 0.5 seconds.

## 14. Motor Classification

Motor class is determined from total impulse.

The class calculation must use the applicable impulse-class boundaries
rather than being inferred from average thrust.

The class calculation must be isolated from the GUI and covered by
tests.

## 15. Motor Designation

The calculated motor designation is based on:

``` text
Impulse Class + Average Thrust
```

Example:

``` text
N + 1816 -> N1816
```

Exact rounding/formatting rules must be documented and tested. Delay
information is separate from the core static-performance designation.

## 16. Performance Extensions

RMCS includes derived performance quantities that require test metadata or
auxiliary sensor channels in addition to the thrust curve. These values
are calculated by a dedicated performance-extension layer and exposed to
the GUI through the authoritative results model.

### 16.1 Specific impulse (Isp)

When total impulse and valid propellant mass are available:

``` text
Isp = Total Impulse / (Propellant Mass × g0)
```

Propellant mass is converted from grams to kilograms before calculation,
and standard gravity is `9.80665 m/s²`.

If propellant mass is missing or invalid, Isp remains unavailable and the
result includes an explicit status rather than inventing a value.

### 16.2 Characteristic velocity (C*)

When valid chamber-pressure data, propellant mass, nozzle throat diameter,
and a valid standardized 5% burn interval are available, RMCS currently
calculates an average C* using:

``` text
C* = Pc × At / mdot
```

where:

- `Pc` is the time-weighted average chamber pressure over the standardized
  5% burn interval.
- `At` is nozzle throat area calculated from the supplied throat diameter.
- `mdot` is average propellant mass flow calculated from propellant mass
  divided by standardized burn time.

Pressure is converted from psi to Pa and nozzle dimensions from inches to
meters before calculation. Exact standardized-burn boundary times are
handled by interpolation when calculating the pressure average.

C* is only reported when all required inputs are valid. Missing or invalid
pressure, propellant mass, throat diameter, or burn-interval data produces
an explicit unavailable status.

The current C* implementation is a calculated engineering extension. Its
input assumptions must remain visible to the user; in particular, user-
supplied or estimated nozzle geometry must not be presented as measured
hardware data. Future work may add time-resolved C* analysis and additional
validation against appropriate reference data.

## 17. Sampling and Numerical Integration

The Analyzer shall support irregular sample timing.

Numerical integration shall use actual time values associated with each
thrust sample.

The calculation must not blindly multiply nominal sample spacing by
sample count.

Interpolation may be used when determining threshold crossings and
interval boundaries.

The numerical integration method must be deterministic and documented.

## 18. Filtering

The primary performance calculation must not silently distort the
measured thrust curve.

Default behavior:

-   Do not apply an undisclosed smoothing filter.
-   Preserve measured samples.
-   Make optional filtering explicit.
-   Clearly distinguish raw, processed, and display-only curves if
    filtering is eventually added.

Display smoothing must never silently become the source of authoritative
motor-performance results.

## 19. Results Model

### Standard motor performance

-   Peak thrust
-   Peak time
-   Total impulse
-   Standard burn time
-   Standardized average thrust
-   Initial thrust
-   Motor class
-   Calculated designation
-   Specific impulse (Isp) when valid propellant mass is available
-   Characteristic velocity (C*) when required pressure, mass, burn-time,
    and throat inputs are available
-   Average chamber pressure used for C*
-   Average propellant mass flow used for C*
-   Availability/status diagnostics for performance extensions

### Physical/diagnostic events

-   Physical ignition
-   Physical peak
-   Physical/recorded burnout
-   5% start
-   5% end

### Data quality

-   Sample count
-   Actual calculated sample rate
-   Data duration
-   Baseline
-   Processing status
-   Validation issues

The result model must be independent of the GUI.


## 20. Video Analysis and Overlay System

RMCS Analyzer treats test video as an analysis presentation medium rather
than as a separate media player.

### 20.1 Per-test video state

Each `TestModel` owns a `VideoState`.

The current video state includes:

- Video source path
- Synchronization start/offset
- Playback position
- Thrust curve overlay visibility
- Pressure curve overlay visibility
- Simulation overlay visibility
- Results overlay visibility
- Event-marker visibility
- Thrust curve overlay position and size
- Pressure curve overlay position and size
- Results overlay position and size
- Events overlay position
- Individual event positions and visibility
- Curve title
- Results title
- Selected result fields
- Curve grid visibility
- Curve axes/scale visibility
- Curve background visibility

This state is test-specific and must not leak between loaded tests.

### 20.2 Video association

The `.rmcs` project stores the video association as a path.

The source video is not embedded in the project archive.

A future portable-project/package workflow may address external media
packaging, but that is not part of the current implementation.

### 20.3 Master timeline

When no video is loaded, RMCS playback uses the RMCS/CSV analysis timeline.

When video is loaded, the **video timeline is the master timeline**.

The full source-video duration is preserved.

The video is not clipped or shifted merely because RMCS test time begins
later in the video.

### 20.4 Sync Start semantics

`Sync Start` is defined as:

> The video timestamp at which RMCS test time `t = 0` begins.

For video time `Tv` and RMCS time `Tr`:

```text
Tr = Tv - Sync Start
```

RMCS analysis state is active only when the resulting RMCS time is within
the test timeline.

The intended behavior is:

```text
Video time < Sync Start
    → video plays normally
    → RMCS marker/results are inactive

Video time = Sync Start
    → RMCS time = 0

Sync Start < Video time < Sync Start + RMCS duration
    → RMCS marker/results follow the synchronized analysis timeline

Video time >= Sync Start + RMCS duration
    → RMCS marker remains at final curve point
    → video continues to the end of the source video
```

Changing Sync Start must change synchronization, not clip or truncate the
video.

### 20.5 Playback

The video and RMCS timeline must remain responsive during normal playback.

The implementation should allow the media player to play continuously and
should avoid repeatedly seeking the video on every playback tick.

Timeline scrubbing may seek the video when the user changes position.

Playback controls remain part of the core analyzer workflow.

### 20.6 No-video behavior

A video is optional.

The analyzer must remain fully usable without a video. RMCS playback,
curve-marker movement, and synchronized metrics may operate on the RMCS
timeline alone.

No video overlay should be presented when no video is associated with the
active test.

### 20.7 Overlay objects

The current functional overlay system contains:

- Measured-thrust curve overlay
- Results overlay
- Individual event markers/objects
- Ignition event
- Peak-thrust event
- Burnout event

Overlay objects are draggable and resizable.

Positions are stored per test using normalized coordinates so that overlay
placement remains associated with the video presentation rather than with a
single fixed pixel size.

### 20.8 Overlay configuration

The application Settings dialog currently provides configuration for:

- Curve title
- Results title
- Results fields
- Ignition visibility
- Peak-thrust visibility
- Burnout visibility
- Curve grid
- Curve axes/scale
- Curve background

Overlay visibility and configuration are persisted with the test's
`VideoState`.

### 20.9 Overlay presentation status

The current overlay implementation is a functional v1 system.

The following are intentionally deferred:

- Final chart styling
- Final typography
- Final spacing/layout polish
- Advanced event presentation
- Final colors/visual language
- Transparent overlay-video export
- Final rendered-video export

These are presentation/export milestones and must not be allowed to
destabilize the underlying synchronization or analysis behavior.

### 20.10 Synchronized curve overlays

The current functional overlay system supports two independent engineering
curve overlays:

- Measured Thrust
- Measured Pressure

The Thrust and Pressure graph overlays may be displayed simultaneously.

When a project-level simulation is loaded, the corresponding simulation
channel may be displayed on each graph:

- Simulation thrust on the Thrust overlay
- Simulation pressure on the Pressure overlay

Simulation curves are a comparison/reference layer. They do not replace the
authoritative measured RMCS test data or the authoritative `AnalysisResults`.

### 20.11 Simulation Data Integration

RMCS Analyzer supports one optional project-level simulation dataset.

Simulation data is imported from CSV and normalized into a simulator-independent
runtime model. The current normalized channels are:

- Time in seconds
- Thrust in Newtons
- Pressure in psi

The importer recognizes common BurnSim/OpenMotor-style column names and units.
Simulator identification is metadata only and does not determine the parsing
rules.

The normalized simulation model contains:

- Time samples
- Optional thrust samples
- Optional pressure samples
- Source metadata
- Simulator metadata when it can be identified

The imported simulation is stored inside the `.rmcs` project as project-level
data. The original simulation CSV remains an external source file and is not
required for the saved project's simulation curves after import.

Simulation data is intentionally separate from individual test data because
one imported simulation represents the project-level reference/comparison
case rather than a measurement belonging to one particular firing.

Simulation data may have a different sample rate or time grid from measured
RMCS data. Plotting and video synchronization therefore use each source's
own
time axis rather than assuming sample-for-sample correspondence.

### 20.12 Project persistence

The following video/overlay state must survive test switching and
`.rmcs` save/load:

- Project-level simulation data, when imported
- Video association
- Sync Start
- Playback position
- Thrust and Pressure overlay visibility
- Simulation overlay visibility
- Overlay positions/sizes
- Event visibility/positions
- Overlay titles
- Selected result fields
- Curve display settings

The project-file format is currently versioned and serializes the video
state as part of each test.

### 20.13 PDF report frame selection

Each test's `VideoState` may contain an optional PDF report frame timestamp.

The value:

- Is stored in video time.
- Is independent of the current playback position.
- Persists with the `.rmcs` project.
- Is cleared when the associated video is removed.
- May be cleared by the user to restore automatic representative-frame
  selection.

PDF frame extraction must preserve the source video's native aspect ratio.

The current PDF exporter avoids relying on a direct non-zero seek when the
underlying Qt multimedia backend cannot reliably deliver a decoded frame after
seeking. It decodes forward from the beginning of the source video and retains
the closest decoded frame to the requested timestamp.

### 20.14 PDF reporting

PDF reporting is a completed v0.4.0 export workflow.

A single-test report shall:

- Omit population-level Campaign Analysis.
- Include measured thrust analysis.
- Include pressure analysis only when pressure data is available.
- Include simulation comparison only when simulation data is available.
- Include engineering metrics, detected events, and data-quality information
  when available.
- Include Video Evidence only when a usable video frame can be extracted.

A multi-test campaign report shall:

- Include Campaign Overview.
- Include Test Summary.
- Include population-level Campaign Analysis.
- Include each analyzed test's individual report.
- Include Video Evidence only for tests with usable video.

Optional sections must be omitted rather than rendered as empty placeholders.

PDF engineering values must come from the authoritative `AnalysisResults`
and associated project/test state. The PDF exporter must not create a second
independent implementation of motor-performance calculations.

Video evidence must preserve the source video's native aspect ratio.

## 21. Export Workflows

Export services consume the authoritative analysis/results layer and project
state. Export implementations must not duplicate the motor-performance
calculation methodology.

### 21.1 PDF Report

The PDF report is the first completed export workflow in v0.4.0.

It supports:

- Single-test reports.
- Multi-test campaign reports.
- Conditional pressure, simulation, and video sections.
- Campaign population statistics for multi-test reports.
- User-selected PDF video frames.
- Automatic representative video-frame selection.
- Native video aspect-ratio preservation.

The PDF report is intended to document and communicate RMCS results. It does
not replace the authoritative analysis engine.

### 21.2 BurnSim CSV export

BurnSim CSV export is implemented and is available from the Export panel.

The export is intentionally a **measured test-data export**, not a re-export of
RMCS simulation data or derived engineering results. It writes the complete
measured trace using the following columns:

```text
Time,Pressure,Thrust
```

Units are:

- Time: seconds
- Pressure: psi
- Thrust: newtons

The complete recorded trace is retained, including pre-ignition and
post-burnout samples. Pressure is interpolated onto the measured thrust time
base when the two measured channels use different time bases.

The exporter includes the CSV header and does not add an RMCS-specific metadata
or units row. This matches the documented BurnSim 4 CSV import structure.

The export has been independently checked against Synthetic-Test-01,
Synthetic-Test-03, and Zerox reference data for sample count, time range, peak
values, and integrated impulse. Direct runtime import into BurnSim has not been
performed because BurnSim is not available in the current development
environment.

### 21.3 Remaining export roadmap

The remaining planned export workflows are:

- OpenMotor
- Analysis CSV

RockSim and OpenRocket exports are not part of the current RMCS Analyzer
export roadmap.

The remaining exports should be implemented independently and should consume the
existing `AnalysisResults`, prepared test data, simulation data, and metadata as
appropriate.

## 22. Campaign Analysis

Campaign Analysis is a population-level analysis workflow for comparing
completed recorded motor tests within an RMCS project.

Campaign Analysis operates on the authoritative `AnalysisResults` already
associated with each selected test. The Campaign layer must not independently
recalculate thrust, impulse, burn time, Isp, C*, motor classification, or other
authoritative engineering results.

### 22.1 Test Selection

The Campaign workspace maintains its own selection of project tests.

Campaign selection:

- Is independent of the active individual test.
- May include multiple tests from the current project.
- Must not change merely because the user changes the active test.
- Must not introduce duplicate tests.
- Must support restoring a previously saved selection.

A project that predates Campaign-selection persistence may have no stored
selection state. In that case, the Campaign workspace may use its normal
default selection behavior.

### 22.2 Campaign Metrics

The current Campaign Analysis implementation reports population statistics for:

- Total Impulse
- Peak Thrust
- Burn Time
- Average Thrust
- Isp
- C*

For each metric, the population result may include:

- Count of valid values
- Mean
- Median
- Minimum
- Maximum
- Population standard deviation
- Coefficient of variation

Tests that do not contain completed analysis results are excluded from
campaign calculations rather than being represented as zero-valued measurements.

### 22.3 Campaign Thrust Curves

Campaign thrust-curve analysis places usable individual thrust curves on a
common time basis and calculates population statistics.

Supported curve bases are:

- Absolute burn time
- Normalized burn time

The population curve provides:

- Mean
- Median
- Standard deviation
- Minimum
- Maximum
- Number of contributing tests at each point

Individual campaign curves may also be displayed for comparison.

### 22.4 Campaign Visualization

The Campaign workspace currently provides:

- A campaign test-selection area.
- A campaign metric statistics table.
- A Metric Distribution view.
- A Campaign Thrust Curve view.
- Absolute and normalized burn-time curve selection.

Campaign visualization is presentation of authoritative analysis results and
must not alter the underlying recorded test data.

### 22.5 Campaign Project Persistence

Campaign test selection is project-level state and must survive `.rmcs`
save/load operations.

The project file may persist the source identifiers of the selected tests.
When a project is reopened, the saved selection must be restored after the
project tests are loaded.

The Campaign selection state must remain distinct from:

- The active test.
- Compare selection state.
- Individual test metadata.
- Individual test video state.

Adding the Campaign selection field to the project manifest is an additive
change and must remain compatible with older projects that do not contain the
field.

## 23. GUI Rules

The GUI displays authoritative results produced by the analysis engine.

The GUI must not independently recalculate impulse, burn time, motor
class, baseline, thresholds, or event times.

If a displayed result is wrong, the authoritative analysis result should
be corrected rather than patched in the GUI.

The thrust plot may visually distinguish motor-performance and
diagnostic regions and standardized boundaries without modifying
underlying data.

## 24. Reference Validation

Reference data is a first-class part of the project.

The Analyzer must eventually be tested against known thrust curves with
known published/certification statistics.

Reference tests should include:

-   Short-burning motors
-   Long-burning motors
-   High-thrust motors
-   Low-thrust motors
-   Startup spikes
-   Shutdown tails
-   Irregular sampling

Where a published reference provides the underlying thrust curve and
calculated statistics, RMCS should reproduce the documented results
within a defined numerical tolerance.

At minimum, reference tests should verify:

-   Peak thrust
-   Peak time
-   5% start
-   5% end
-   Standard burn time
-   Total impulse
-   Standardized average thrust
-   Motor class

## 25. Commercial Motor Validation Goal

A commercial motor test is an important real-world validation case.

The objective is not to force RMCS to reproduce a manufacturer's
published number.

Instead:

1.  The test stand must be properly calibrated.
2.  The thrust curve must be accurately measured.
3.  RMCS must apply the documented calculation methodology.
4.  RMCS results must be directly comparable with
    published/certification results.
5.  Differences should then be investigated as potential measurement,
    motor-variation, test-condition, or reference-data differences.

## 26. Current Zerox Reference

The current Zerox CSV is the project's primary development and regression
dataset.

The current authoritative analysis engine produces the following
standardized Phase 2 results:

``` text
Samples:                 661
Curve duration:          8.538000 s
Peak thrust:             3230.339730 N
Peak time:                  0.349000 s

5% threshold:             161.516987 N
5% start:                    0.044210 s
5% end:                      7.117326 s
Standard burn time:          7.073116 s

Total impulse:          14471.744320 N-s
Normalized impulse:     14367.091390 N-s
Average thrust:           2031.225247 N
Initial thrust average:   2635.834021 N

Impulse class:                    N
Calculated designation:       N2031

Performance extensions (using supplied auxiliary inputs):
Specific impulse:            197.17 s
Average chamber pressure:    348.10 psi
Average mass flow:             1.0581 kg/s
Characteristic velocity (C*): 1149.34 m/s
```

These values are regression references for the current implementation.

The Zerox source video displays the label **N2300**. The label is retained
only as source-video context and is not used as an independent validation
target or as the measured designation produced by the Analyzer.

The current validation work confirms that the CSV and video agree on the
recorded test duration and peak thrust. The current analyzer reduction of
the supplied CSV produces N2031 using the documented standardized
methodology.

The current Zerox reduction is therefore treated as a documented
regression result rather than as a manufacturer's certified performance
designation.

The current Isp and C* values are derived performance extensions and are
not independent validation targets. The Zerox C* result depends on the
supplied propellant mass, chamber-pressure channel, and nozzle throat
diameter; those auxiliary inputs may be estimated or user-supplied. The
software must preserve that distinction rather than presenting assumed
geometry as measured hardware data.

## 27. Architecture Cleanup Principles

The codebase must favor clear responsibilities over historical
compatibility.

Each module should have one primary responsibility.

We will remove or merge code when it duplicates another module's
responsibility.

The following concepts must remain clearly separated:

``` text
Data loading
Processing
Physical event detection
Standard performance reduction
Motor classification
Results model
GUI presentation
Export
```

## 28. Development Rules

1.  Work on one subsystem at a time.
2.  Do not make unrelated changes in the same step.
3.  Prefer complete replacement files when a source file needs
    substantial modification.
4.  Test every meaningful change before moving on.
5.  Do not use the GUI as the source of truth for calculations.
6.  Do not declare a calculation correct merely because it looks
    plausible.
7.  Use documented methodology and reference data to validate
    calculations.
8.  Preserve raw test data.
9.  Document significant engineering decisions.
10. Commit stable milestones to Git.

## 29. Definition of Done for the Analysis Engine

The current analysis-engine milestone is complete when:

-   Calculation rules are documented.
-   Code implements those rules independently of the GUI.
-   Reference thrust curves are available.
-   Standalone reference tests pass.
-   Published metrics can be reproduced within defined tolerances.
-   Irregular timestamps are handled correctly.
-   Negative post-burn load-cell readings cannot create false thrust.
-   Standardized burn time is independent of diagnostic physical-burnout
    detection.
-   Total impulse and standardized average thrust use their correct
    respective windows.
-   Motor classification is based on total impulse.
-   GUI values come directly from the authoritative result model.

The current implementation satisfies this milestone for the validated
reference cases presently in the project.

The analysis engine remains open to additional validation as more
published thrust curves and properly characterized commercial tests become
available.

## 30. Sources and Methodology References

**ThrustCurve.org --- Motor Statistics**\
https://www.thrustcurve.org/info/motorstats.html

**National Association of Rocketry --- Static Motor Testing Manual**\
https://www.nar.org/wp-content/uploads/2014/08/ST-MotorTestingManual.pdf

**AeroTech Rocketry**\
https://aerotech-rocketry.com/

Manufacturer-published motor specifications may be used as external
validation/reference data, with the distinction that a published or
certification result may represent representative or averaged
performance rather than a single firing.

## 31. GUI Visual Direction

The GUI is being developed against a project visual reference established
during the design process. The reference is authoritative for presentation
and layout, while the analysis engine remains authoritative for engineering
values.

The intended dashboard composition is:

- dark engineering-focused styling
- left column for test information and test files
- center column for the primary thrust-analysis workspace
- right column for key results, detected events, additional metrics, and C*
- tabbed center workspaces for Thrust Curve, Pressure Curve, Data Table, Analysis,
  and Compare
- lower supporting panels for video overlay, exports, and motor
  classification

New GUI work should extend this visual system rather than replacing it with
a different layout or styling direction. Annotations and controls should
remain readable at the default window size and should not obscure the
engineering curve or each other.

## 32. Current Project Direction

The core analysis-engine validation milestone is complete, and the project
has moved into functional GUI and workflow development.

The current development sequence is:

```text
1. Core analysis-engine validation
        ↓
2. Connect authoritative results to the GUI
        ↓
3. Build functional dashboard workspaces
        ↓
4. Functional video playback / synchronization / overlay
        ↓
5. Compare workflow
        ↓
6. Pressure-curve and broader analysis workflows
        ↓
7. Simulation import and comparison workflow
        ↓
8. PDF reporting
        ↓
9. BurnSim / OpenMotor / Analysis CSV exports
        ↓
10. Final GUI / overlay / production-readiness refinement
        ↓
11. Rendered-video and transparent-overlay export
        ↓
12. Continued reference and commercial-motor validation
```

The current project is intentionally prioritizing usable functionality over
final visual polish.

The functional video/overlay milestone is established, and the Compare,
Pressure Curve, Campaign Analysis, Simulation, and PDF reporting workflows are
now functional.

The current major functional milestone is **Simulation Integration, Expanded
Video Analysis, PDF Reporting, and BurnSim Export (v0.4.0)**. The remaining
export work is OpenMotor and Analysis CSV, followed by final GUI/overlay and
production-readiness refinement. Rendered-video and transparent-overlay export
remain separate future capabilities.

The analysis engine remains authoritative. New GUI workflows must consume the
existing result model rather than duplicating engineering calculations.

Before any major analytical methodology change, new reference data or
documented methodology should be added to the validation suite.

This document remains the project's source of truth for analysis
methodology, architecture, current functional behavior, and development
direction.

## v0.4.0 Milestone

Completed:

- Project-level simulation import from BurnSim/OpenMotor-style CSV data.
- Simulator-independent normalized simulation model.
- Simulation comparison on the Thrust Curve workspace.
- Simulation comparison on the Pressure Curve workspace.
- Simulation persistence inside `.rmcs` project files.
- Independent synchronized video Thrust and Pressure graph overlays.
- Simultaneous Thrust and Pressure video overlays.
- Simulation curves on the corresponding video overlays.
- Persistent independent overlay positions and sizes.
- Improved saved-project video source restoration.
- Pressure overlay rendering corrected to remain line-based without unintended
  area fill.
- Saved `.rmcs` projects reopen as clean projects rather than falsely showing
  `MODIFIED`.
- Campaign-level and compact single-test PDF reports.
- Conditional PDF report sections based on available data.
- User-selectable PDF report frame with `.rmcs` persistence.
- Automatic representative-frame fallback.
- Native video aspect-ratio preservation in PDF Video Evidence.
- Functional BurnSim CSV export from the complete measured RMCS test trace.
- BurnSim export validation against Synthetic-Test-01, Synthetic-Test-03, and Zerox reference data.

Project compatibility:

- RMCS project format remains version **3**.
- RMCS CSV format remains version **1.0**.

Next:

- OpenMotor export.
- Analysis CSV export.
- Final GUI/overlay and production-readiness refinement.
- Rendered-video and transparent-overlay export.
- Continued reference and commercial-motor validation.

## v0.3.0 Milestone

Completed:
- Campaign Analysis workspace for multi-test population analysis.
- Population statistics for Total Impulse, Peak Thrust, Burn Time, Average Thrust,
  Isp, and C*.
- Mean, median, minimum, maximum, population standard deviation, and coefficient
  of variation for campaign metrics.
- Metric Distribution visualization.
- Campaign Thrust Curve visualization with absolute and normalized burn-time views.
- Population thrust-curve statistics.
- Independent Campaign selection state.
- Persistent Campaign selection in `.rmcs` projects.
- Duplicate-selection prevention.
- Backward-compatible handling of projects without persisted Campaign selection.

The v0.2.0 Compare, Pressure Curve, metadata, import, and project-state work
remains part of the current application.

Next:
- Broader simulation/data workflows.
- Export workflows.
- Rendered-video and transparent-overlay export.
- Final GUI and overlay visual polish.
- Continued reference and commercial-motor validation.

## v0.2.0 Milestone

Completed:
- Compare workspace with multi-test thrust overlays and key metrics.
- Dedicated Pressure Curve workspace.
- Project-level editable metadata overrides with CSV-metadata reset.
- Persistent metadata overrides in `.rmcs`.
- Independent Compare selection state.
- Test removal from the current project.
- Multi-file CSV import.
