# RMCS Analyzer

**Rocket Motor Characterization System Data Analysis Software**

RMCS Analyzer is a desktop application for analyzing rocket motor test-stand data. It is designed to turn raw thrust measurements into useful motor performance information through an interactive, engineering-focused interface.

The application is being developed as a standalone Windows desktop application using Python, PySide6, PyQtGraph, NumPy, and Pandas.

---

## Current Features

- Import RMCS-compatible CSV test data
- Display interactive thrust curves
- Automatic ignition detection
- Automatic burnout detection
- Peak thrust detection
- Peak thrust calculation
- Average thrust calculation
- Burn time calculation
- Total impulse calculation
- Motor impulse-class classification
- Calculated motor performance designation
- Basic test-data quality statistics
- RMCS test metadata display
- Test file tracking within the application

---

## Motor Classification and Designation

RMCS Analyzer determines the motor impulse class from measured total impulse.

The application also calculates a performance designation using:

- **Measured total impulse** → impulse class
- **Measured average thrust** → numerical designation

For example:

```text
Total Impulse:            4906.49 N·s
Average Thrust:             265.07 N
Motor Class:                    L
Calculated Designation:       L265
```

The calculated designation represents the measured performance of the imported test data. It should not be interpreted as a manufacturer's certified commercial motor designation.

For example, an analyzed test may produce a designation such as `L265`, while the actual motor being tested may have a different manufacturer designation.

---

## Analysis Results

The current analysis engine calculates:

### Thrust Performance

- Peak thrust
- Average thrust
- Burn time
- Time to peak thrust
- Total impulse

### Event Detection

- Ignition time
- Peak thrust time
- Burnout time
- Detection method

### Data Quality

- Sample count
- Sample rate
- Minimum measured thrust
- Maximum measured thrust
- Baseline mean
- Baseline standard deviation

---

## Project Architecture

The application is intentionally divided into separate layers so that data import, analysis, visualization, and future export functionality remain independent.

```text
CSV File
   │
   ▼
CSV Reader
   │
   ▼
TestData Model
   │
   ├──────────────────────┐
   ▼                      ▼
Analysis                  GUI
   │                      │
   ├── Event Detection    ├── Test Information
   ├── Thrust Analysis    ├── Test Files
   ├── Statistics         ├── Thrust Plot
   └── Classification     └── Results
   │
   ▼
Analysis Results
   │
   ▼
GUI Results / Visualization
```

This architecture is intended to allow RMCS Analyzer to eventually support data from RMCS as well as compatible data from other test stands.

---

## Project Structure

```text
RMCS_Analyzer/
│
├── main.py
│
├── src/
│   └── rmcs_analyzer/
│       │
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── events.py
│       │   ├── impulse.py
│       │   ├── motor_class.py
│       │   ├── results.py
│       │   └── statistics.py
│       │
│       ├── data/
│       │   ├── __init__.py
│       │   ├── csv_reader.py
│       │   └── models.py
│       │
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── header.py
│       │   ├── playback_controls.py
│       │   ├── results_panel.py
│       │   ├── test_files_panel.py
│       │   ├── test_info_panel.py
│       │   └── thrust_plot.py
│       │
│       ├── __init__.py
│       ├── main_window.py
│       └── theme.py
│
├── test_data/
│   └── TEST_008.CSV
│
├── .gitignore
└── README.md
```

---

## Data Import

The current version supports RMCS-compatible CSV files.

The application separates the imported data from the user interface so that additional CSV formats can be supported in the future.

The intended architecture is:

```text
RMCS CSV
Generic CSV
Other Test Stand
Future Telemetry
       │
       ▼
 Import / Mapping
       │
       ▼
    TestData
       │
   ┌───┼────┐
   ▼   ▼    ▼
  GUI Analysis Export
```

Future versions are expected to provide configurable CSV column mapping so users can import data from other test stands without modifying the application source code.

---

## Sample Data

The repository includes:

```text
test_data/TEST_008.CSV
```

as a sample dataset.

This dataset is a controlled bench-load acceptance test used to validate the RMCS data-processing and analysis pipeline.

It is included as software test data and **does not represent an actual rocket motor firing**.

The sample currently contains:

- 2,764 samples
- Approximately 85.27 Hz sample rate
- Approximately 32.4 seconds of recorded data
- Measured peak load of approximately 280.40 N
- Calculated total impulse of approximately 4,906.49 N·s

The sample is intended to provide a known dataset for development, demonstration, and future regression testing.

---

## Current Development Environment

RMCS Analyzer is currently developed using:

- Python 3
- PySide6
- PyQtGraph
- NumPy
- Pandas
- VS Code
- Python virtual environment
- Git
- GitHub Desktop

The application is currently run from the development environment.

A packaged Windows executable is planned for a later stage so that end users will not need Python installed.

---

## Development Status

RMCS Analyzer is currently in early development.

The current milestone establishes the core data pipeline:

```text
Import CSV
     ↓
Parse Test Data
     ↓
Detect Events
     ↓
Calculate Thrust
     ↓
Calculate Total Impulse
     ↓
Determine Motor Class
     ↓
Calculate Performance Designation
     ↓
Display Results
```

The core pipeline has been validated using `TEST_008.CSV`.

---

## Planned Features

The project is expected to grow to include features such as:

### Analysis

- Interactive thrust-curve analysis
- Event markers
- Adjustable ignition and burnout points
- Manual event adjustment
- More robust event-detection algorithms
- Additional data-quality diagnostics
- Baseline correction
- Signal filtering options
- Configurable thrust polarity
- More detailed motor performance statistics

### Motor Information

- User-entered motor designation
- Manufacturer information
- Motor type
- Motor diameter
- Motor length
- Initial mass
- Propellant mass
- Motor metadata management
- Comparison of measured performance against entered motor specifications

### Data Import

- Generic CSV import
- User-defined column mapping
- Time-column selection
- Thrust-column selection
- Unit selection
- Support for additional test-stand data formats

### Pressure and Performance Analysis

- Chamber-pressure analysis
- Pressure/thrust correlation
- C* calculation when sufficient pressure, mass-flow, and nozzle data are available
- Additional internal-ballistics analysis where appropriate data is available

### Export and Interoperability

- RASP `.eng` export
- RockSim `.rse` export
- OpenRocket compatibility
- BurnSim compatibility
- OpenMotor interoperability
- Additional engineering data formats

### Visualization

- Advanced interactive thrust curves
- Zooming and panning
- Event markers
- Cursor measurements
- Multiple curve overlays
- Comparison of multiple tests
- Optional panels
- Expandable plot area
- Light and dark themes

### Video Analysis

- Test video import
- Video synchronization with test data
- Thrust-curve/video overlays
- Animated test playback
- Time synchronization tools

### Application

- Configurable application panels
- Persistent user settings
- Test project files
- Improved test management
- Packaged Windows installer
- User documentation

Features listed above are planned and may change as development progresses.

---

## Design Goals

RMCS Analyzer is being developed with several core goals:

### Standalone

The finished application should operate as a normal desktop application rather than requiring users to work from a Python terminal.

### Modular

Data import, analysis, visualization, and export functionality should remain separated into independent components.

### Extensible

The application should be able to accept data from RMCS as well as other compatible test stands.

### Engineering-Focused

Results should be presented in a way that is useful for analyzing real test data rather than simply displaying raw measurements.

### Transparent

Calculated values should be traceable back to the underlying test data and analysis methods.

---

## Safety and Engineering Disclaimer

RMCS Analyzer is software for analyzing and visualizing rocket motor test data.

The software does not replace applicable safety procedures, testing standards, certification requirements, engineering review, or professional judgment.

Users are responsible for validating measurements, calculations, assumptions, and conclusions produced by the software.

---

## License

License information will be added as the project develops.


