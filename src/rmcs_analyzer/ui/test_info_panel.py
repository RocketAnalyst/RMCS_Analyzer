from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from ..project.validation import MetadataValidator


class TestInfoPanel(QFrame):
    """
    Displays and edits information associated with the
    currently active test.

    The panel validates editable metadata before notifying the
    application layer that the metadata has changed.
    """

    metadata_changed = Signal()
    edit_metadata_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            16,
            16,
            16,
            16,
        )
        layout.setSpacing(10)

        title = QLabel("TEST INFORMATION")
        title.setObjectName("sectionTitle")

        layout.addWidget(title)

        self.test_number = self.add_edit_row(
            layout,
            "Test Number",
            "",
        )

        self.motor = self.add_edit_row(
            layout,
            "Motor",
            "",
        )

        self.date = self.add_edit_row(
            layout,
            "Date (M-D-YYYY)",
            "",
        )

        self.diameter = self.add_edit_row(
            layout,
            "Diameter (in)",
            "",
        )

        self.length = self.add_edit_row(
            layout,
            "Length (in)",
            "",
        )

        self.initial_mass = self.add_edit_row(
            layout,
            "Initial Mass (g)",
            "",
        )

        self.propellant_mass = self.add_edit_row(
            layout,
            "Propellant Mass (g)",
            "",
        )

        self.edit_metadata_button = QPushButton(
            "Edit Metadata..."
        )
        self.edit_metadata_button.clicked.connect(
            self.edit_metadata_requested.emit
        )
        layout.addWidget(self.edit_metadata_button)

        layout.addStretch()

        self._connect_edit_signals()

    # =============================================================
    # UI CONSTRUCTION
    # =============================================================

    def add_edit_row(
        self,
        layout,
        label_text,
        value_text,
    ):
        """Create and add an editable information row."""

        row = QFrame()
        row.setObjectName("infoRow")

        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(
            0,
            2,
            0,
            2,
        )
        row_layout.setSpacing(2)

        label = QLabel(label_text)
        label.setObjectName("infoLabel")

        value = QLineEdit(value_text)
        value.setObjectName("infoValueEdit")
        value.setPlaceholderText("Not specified")

        row_layout.addWidget(label)
        row_layout.addWidget(value)

        layout.addWidget(row)

        return value

    def _connect_edit_signals(self):
        """
        Connect editing controls to their validation handlers.
        """

        self.test_number.editingFinished.connect(
            self._validate_test_number
        )

        self.motor.editingFinished.connect(
            self._validate_text_field
        )

        self.date.editingFinished.connect(
            self._validate_test_date
        )

        self.diameter.editingFinished.connect(
            self._validate_diameter
        )

        self.length.editingFinished.connect(
            self._validate_length
        )

        self.initial_mass.editingFinished.connect(
            self._validate_initial_mass
        )

        self.propellant_mass.editingFinished.connect(
            self._validate_propellant_mass
        )

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_test_number(self):
        """Validate the test number field."""

        result = MetadataValidator.test_number(
            self.test_number.text()
        )

        self._apply_validation(
            self.test_number,
            result.valid,
            result.message,
        )

        if result.valid:
            self.metadata_changed.emit()

    def _validate_text_field(self):
        """Validate a general text field."""

        sender = self.sender()

        if sender is None:
            return

        result = MetadataValidator.text(
            sender.text()
        )

        self._apply_validation(
            sender,
            result.valid,
            result.message,
        )

        if result.valid:
            self.metadata_changed.emit()

    def _validate_diameter(self):
        """Validate motor diameter."""

        result = MetadataValidator.motor_diameter(
            self.diameter.text()
        )

        self._apply_validation(
            self.diameter,
            result.valid,
            result.message,
        )

        if result.valid:
            self.metadata_changed.emit()

    def _validate_length(self):
        """Validate motor length."""

        result = MetadataValidator.motor_length(
            self.length.text()
        )

        self._apply_validation(
            self.length,
            result.valid,
            result.message,
        )

        if result.valid:
            self.metadata_changed.emit()

    def _validate_initial_mass(self):
        """Validate initial motor mass."""

        result = MetadataValidator.initial_mass(
            self.initial_mass.text()
        )

        self._apply_validation(
            self.initial_mass,
            result.valid,
            result.message,
        )

        if result.valid:
            self.metadata_changed.emit()

    def _validate_propellant_mass(self):
        """Validate propellant mass."""

        result = MetadataValidator.propellant_mass(
            self.propellant_mass.text()
        )

        self._apply_validation(
            self.propellant_mass,
            result.valid,
            result.message,
        )

        if result.valid:
            self.metadata_changed.emit()

    def _apply_validation(
        self,
        field,
        valid,
        message,
    ):
        """
        Apply the visual validation state to a field.
        """

        if valid:
            field.setStyleSheet("")
            field.setToolTip("")

        else:
            field.setStyleSheet(
                """
                QLineEdit#infoValueEdit {
                    border: 1px solid #d94a52;
                    background-color: #2a1518;
                }
                """
            )

            field.setToolTip(
                message
            )

    def _validate_test_date(self):
        """Validate the test date field."""

        result = MetadataValidator.test_date(
            self.date.text()
        )

        self._apply_validation(
            self.date,
            result.valid,
            result.message,
        )

        if result.valid:
            self.metadata_changed.emit()

    # =============================================================
    # TEST MODEL DISPLAY
    # =============================================================

    def set_test_model(self, test):
        """
        Populate the panel from a TestModel.

        Loading a test does not trigger metadata validation signals.
        """

        self._set_field(
            self.test_number,
            test.test_number,
        )

        self._set_field(
            self.motor,
            test.motor_designation,
        )

        self._set_field(
            self.date,
            test.test_date,
        )

        self._set_numeric_field(
            self.diameter,
            test.motor_diameter_in,
        )

        self._set_numeric_field(
            self.length,
            test.motor_length_in,
        )

        self._set_numeric_field(
            self.initial_mass,
            test.initial_mass_g,
        )

        self._set_numeric_field(
            self.propellant_mass,
            test.propellant_mass_g,
        )

    def set_test_data(self, test_data):
        """
        Populate the panel from a TestData object.

        This method is retained for compatibility with existing
        application code. New code should use set_test_model().
        """

        metadata = test_data.metadata

        self._set_field(
            self.test_number,
            (
                str(metadata.test_number)
                if metadata.test_number is not None
                else ""
            ),
        )

        self._set_field(
            self.motor,
            metadata.motor_designation or "",
        )

        self._set_field(
            self.date,
            metadata.test_date or "",
        )

        self._set_numeric_field(
            self.diameter,
            metadata.motor_diameter,
        )

        self._set_numeric_field(
            self.length,
            metadata.motor_length,
        )

        self._set_numeric_field(
            self.initial_mass,
            metadata.initial_mass,
        )

        self._set_numeric_field(
            self.propellant_mass,
            metadata.propellant_mass,
        )

    # =============================================================
    # FIELD HELPERS
    # =============================================================

    def _set_field(
        self,
        field,
        value,
    ):
        """Set a text field without triggering editing signals."""

        field.blockSignals(True)

        if value is None:
            field.setText("")
        else:
            field.setText(str(value))

        field.setStyleSheet("")
        field.setToolTip("")

        field.blockSignals(False)

    def _set_numeric_field(
        self,
        field,
        value,
    ):
        """Set a numeric field without triggering editing signals."""

        field.blockSignals(True)

        if value is None:
            field.setText("")
        else:
            field.setText(f"{value:g}")

        field.setStyleSheet("")
        field.setToolTip("")

        field.blockSignals(False)

    # =============================================================
    # CLEAR
    # =============================================================

    def clear(self):
        """Reset the panel to its unloaded state."""

        fields = (
            self.test_number,
            self.motor,
            self.date,
            self.diameter,
            self.length,
            self.initial_mass,
            self.propellant_mass,
        )

        for field in fields:
            field.blockSignals(True)
            field.clear()
            field.setStyleSheet("")
            field.setToolTip("")
            field.blockSignals(False)