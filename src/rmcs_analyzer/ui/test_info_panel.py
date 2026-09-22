from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

class TestInfoPanel(QFrame):
    """Display-only summary of the active test metadata.

    Detailed metadata editing is intentionally handled by the
    ``Edit Metadata...`` dialog. The values shown here are read-only
    and reflect the active TestModel.
    """

    # Retained for MainWindow compatibility. This display-only panel does not emit it.
    metadata_changed = Signal()
    edit_metadata_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("TEST INFORMATION")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self.test_number = self.add_display_row(layout, "Test Number", "")
        self.motor = self.add_display_row(layout, "Motor Designation", "")
        self.date = self.add_display_row(layout, "Test Date", "")
        self.propellant_type = self.add_display_row(layout, "Propellant Type", "")
        self.diameter = self.add_display_row(layout, "Diameter (mm)", "")
        self.length = self.add_display_row(layout, "Length (mm)", "")
        self.throat_diameter = self.add_display_row(layout, "Throat Diameter (in)", "")

        self.edit_metadata_button = QPushButton("Edit Metadata...")
        self.edit_metadata_button.clicked.connect(self.edit_metadata_requested.emit)
        layout.addWidget(self.edit_metadata_button)
        layout.addStretch()

    def add_display_row(self, layout, label_text, value_text):
        """Create a read-only metadata display row."""
        row = QFrame()
        row.setObjectName("infoRow")

        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(2)

        label = QLabel(label_text)
        label.setObjectName("infoLabel")

        value = QLineEdit(value_text)
        value.setObjectName("infoValueEdit")
        value.setReadOnly(True)
        value.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        value.setPlaceholderText("Not specified")

        row_layout.addWidget(label)
        row_layout.addWidget(value)
        layout.addWidget(row)
        return value

    def set_test_model(self, test):
        """Populate the panel from a TestModel without allowing inline edits."""
        self._set_field(self.test_number, test.test_number)
        self._set_field(self.motor, test.motor_designation)
        self._set_field(self.date, test.test_date)
        self._set_field(self.propellant_type, test.propellant_type)
        self._set_numeric_field(self.diameter, test.motor_diameter_mm)
        self._set_numeric_field(self.length, test.motor_length_mm)
        self._set_numeric_field(self.throat_diameter, test.nozzle_throat_in)

    def set_test_data(self, test_data):
        """Populate the panel from a TestData object."""
        metadata = test_data.metadata
        self._set_field(
            self.test_number,
            str(metadata.test_number) if metadata.test_number is not None else "",
        )
        self._set_field(self.motor, metadata.motor_designation or "")
        self._set_field(self.date, metadata.test_date or "")
        self._set_field(self.propellant_type, metadata.propellant_type or "")
        self._set_numeric_field(self.diameter, metadata.motor_diameter)
        self._set_numeric_field(self.length, metadata.motor_length)
        self._set_numeric_field(self.throat_diameter, metadata.nozzle_throat)

    @staticmethod
    def _set_field(field, value):
        field.blockSignals(True)
        field.setText("" if value is None else str(value))
        field.setStyleSheet("")
        field.setToolTip("")
        field.blockSignals(False)

    @staticmethod
    def _set_numeric_field(field, value):
        field.blockSignals(True)
        field.setText("" if value is None else f"{value:g}")
        field.setStyleSheet("")
        field.setToolTip("")
        field.blockSignals(False)

    def clear(self):
        """Reset the panel to its unloaded state."""
        for field in (
            self.test_number, self.motor, self.date, self.propellant_type,
            self.diameter, self.length, self.throat_diameter,
        ):
            field.blockSignals(True)
            field.clear()
            field.setStyleSheet("")
            field.setToolTip("")
            field.blockSignals(False)
