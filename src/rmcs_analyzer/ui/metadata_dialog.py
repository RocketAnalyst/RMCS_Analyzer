from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QPushButton,
)


class MetadataDialog(QDialog):
    """Edit project-level metadata for one test without changing its CSV."""

    def __init__(self, test, parent=None):
        super().__init__(parent)
        self.test = test
        self.setWindowTitle("Test Metadata")
        self.resize(620, 760)

        root = QVBoxLayout(self)

        notice = QLabel(
            "These values are stored in the RMCS project and are used by "
            "applicable analysis calculations. The original CSV is not modified."
        )
        notice.setWordWrap(True)
        notice.setObjectName("graphDescription")
        root.addWidget(notice)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        host = QWidget()
        host_layout = QVBoxLayout(host)
        host_layout.setSpacing(12)
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

        self.fields = {}

        self._add_group(
            host_layout,
            "Test Identification",
            [
                ("test_number", "Test Number"),
                ("motor_designation", "Motor Designation"),
                ("motor_type", "Motor Type"),
                ("manufacturer", "Manufacturer"),
                ("builder", "Builder"),
                ("case_material", "Case Material"),
                ("test_date", "Test Date"),
                ("test_stand", "Test Stand"),
                ("test_operator", "Test Operator"),
                ("location", "Location"),
            ],
        )

        self._add_group(
            host_layout,
            "Motor",
            [
                ("motor_diameter_mm", "Diameter (mm)"),
                ("motor_length_mm", "Length (mm)"),
                ("initial_mass_g", "Initial Mass (g)"),
                ("propellant_mass_g", "Propellant Mass (g)"),
                ("propellant_type", "Propellant Type"),
            ],
        )

        self._add_group(
            host_layout,
            "Nozzle",
            [
                ("nozzle_throat_in", "Throat Diameter (in)"),
                ("nozzle_exit_in", "Exit Diameter (in)"),
                ("nozzle_material", "Material"),
            ],
        )

        self._add_group(
            host_layout,
            "Instrumentation",
            [
                ("load_cell", "Load Cell"),
                ("load_cell_calibration", "Load Cell Calibration"),
                ("pressure_sensor", "Pressure Sensor"),
                ("pressure_sensor_calibration", "Pressure Calibration"),
                ("sample_rate_hz", "Sample Rate (Hz)"),
                ("case_pressure_limit_psi", "Case Pressure Limit (psi)"),
            ],
        )

        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText("Optional notes about this test...")
        notes_layout.addWidget(self.notes)
        host_layout.addWidget(notes_group)

        source = QLabel(f"Source CSV: {test.filename or test.source_file}")
        source.setWordWrap(True)
        source.setObjectName("graphDescription")
        host_layout.addWidget(source)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.reset_button = QPushButton("Reset to CSV Metadata")
        buttons.addButton(
            self.reset_button,
            QDialogButtonBox.ButtonRole.ResetRole,
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        self.reset_button.clicked.connect(self._reset)
        root.addWidget(buttons)

        self._load_from_test()

    def _add_group(self, parent_layout, title, fields):
        group = QGroupBox(title)
        form = QFormLayout(group)
        form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )
        for key, label in fields:
            field = QLineEdit()
            field.setPlaceholderText("Not specified")
            form.addRow(label, field)
            self.fields[key] = field
        parent_layout.addWidget(group)

    @staticmethod
    def _display(value):
        if value is None:
            return ""
        if isinstance(value, float):
            return f"{value:g}"
        return str(value)

    def _load_from_test(self):
        for key, field in self.fields.items():
            field.setText(self._display(getattr(self.test, key)))
        self.notes.setPlainText(self.test.notes or "")

    def _reset(self):
        source = self.test.data.metadata
        source_values = {
            "test_number": source.test_number if source.test_number is not None else "",
            "motor_designation": source.motor_designation,
            "motor_type": source.motor_type,
            "manufacturer": source.manufacturer,
            "builder": source.builder,
            "case_material": source.case_material,
            "test_date": source.test_date,
            "test_stand": source.test_stand,
            "test_operator": source.test_operator,
            "location": source.location,
            "motor_diameter_mm": source.motor_diameter,
            "motor_length_mm": source.motor_length,
            "initial_mass_g": source.initial_mass,
            "propellant_mass_g": source.propellant_mass,
            "propellant_type": source.propellant_type,
            "nozzle_throat_in": source.nozzle_throat,
            "nozzle_exit_in": source.nozzle_exit,
            "nozzle_material": source.nozzle_material,
            "load_cell": source.load_cell,
            "load_cell_calibration": source.load_cell_calibration,
            "pressure_sensor": source.pressure_sensor,
            "pressure_sensor_calibration": source.pressure_sensor_calibration,
            "sample_rate_hz": source.sample_rate_hz,
            "case_pressure_limit_psi": source.case_pressure_limit_psi,
        }
        for key, value in source_values.items():
            self.fields[key].setText(self._display(value))
        self.notes.setPlainText(source.notes or "")

    @staticmethod
    def _optional_float(value, label):
        value = value.strip()
        if not value:
            return None
        try:
            number = float(value)
        except ValueError:
            raise ValueError(f"{label} must be a number.")
        if number <= 0:
            raise ValueError(f"{label} must be greater than zero.")
        return number

    def values(self):
        result = {}
        for key, field in self.fields.items():
            value = field.text().strip()
            if key == "test_number":
                if not value:
                    result[key] = ""
                else:
                    try:
                        int(value)
                    except ValueError:
                        raise ValueError("Test Number must be a whole number.")
                    result[key] = value
            elif key in {
                "motor_diameter_mm",
                "motor_length_mm",
                "initial_mass_g",
                "propellant_mass_g",
                "nozzle_throat_in",
                "nozzle_exit_in",
                "sample_rate_hz",
                "case_pressure_limit_psi",
            }:
                result[key] = self._optional_float(
                    value,
                    next(
                        label for k, label in (
                            ("motor_diameter_mm", "Diameter"),
                            ("motor_length_mm", "Length"),
                            ("initial_mass_g", "Initial Mass"),
                            ("propellant_mass_g", "Propellant Mass"),
                            ("nozzle_throat_in", "Nozzle Throat"),
                            ("nozzle_exit_in", "Nozzle Exit"),
                            ("sample_rate_hz", "Sample Rate"),
                            ("case_pressure_limit_psi", "Case Pressure Limit"),
                        )
                        if k == key
                    ),
                )
            else:
                result[key] = value

        result["notes"] = self.notes.toPlainText().strip()
        return result

    def _accept(self):
        try:
            values = self.values()
        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Metadata",
                str(error),
            )
            return

        for key, value in values.items():
            setattr(self.test, key, value)

        self.accept()
