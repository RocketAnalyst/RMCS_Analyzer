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

## 16. Sampling and Numerical Integration

The Analyzer shall support irregular sample timing.

Numerical integration shall use actual time values associated with each
thrust sample.

The calculation must not blindly multiply nominal sample spacing by
sample count.

Interpolation may be used when determining threshold crossings and
interval boundaries.

The numerical integration method must be deterministic and documented.

## 17. Filtering

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

## 18. Results Model

### Standard motor performance

-   Peak thrust
-   Peak time
-   Total impulse
-   Standard burn time
-   Standardized average thrust
-   Initial thrust
-   Motor class
-   Calculated designation

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

## 19. GUI Rules

The GUI displays authoritative results produced by the analysis engine.

The GUI must not independently recalculate impulse, burn time, motor
class, baseline, thresholds, or event times.

If a displayed result is wrong, the authoritative analysis result should
be corrected rather than patched in the GUI.

The thrust plot may visually distinguish motor-performance and
diagnostic regions and standardized boundaries without modifying
underlying data.

## 20. Reference Validation

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

## 21. Commercial Motor Validation Goal

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

## 22. Current Zerox Reference

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

## 23. Architecture Cleanup Principles

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

## 24. Development Rules

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

## 25. Definition of Done for the Analysis Engine

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

## 26. Sources and Methodology References

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

## 27. Current Project Direction

The project has completed the core analysis-engine validation milestone.

``` text
1. Audit current project
        ↓
2. Clean and simplify codebase
        ↓
3. Verify application/tests
        ↓
4. Lock specification and analysis baseline into Git
        ↓
5. Connect validated results to GUI
        ↓
6. Build additional GUI analysis views
        ↓
7. Add reference/comparison workflows
        ↓
8. Expand exports and engineering features
        ↓
9. Continue reference and commercial-motor validation
```

The current authoritative analysis implementation is protected by the
canonical standalone regression suite.

Before the next major analytical methodology change, new reference data
or documented methodology should be added to the validation suite.

The GUI may now consume the validated `AnalysisResults` model. It must not
reimplement authoritative calculations.

This document is the project's source of truth for the intended analysis
direction.
