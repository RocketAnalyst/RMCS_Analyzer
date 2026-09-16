from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)


class TestInfoPanel(QFrame):
    """
    Displays information associated with the currently loaded test.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("TEST INFORMATION")
        title.setObjectName("sectionTitle")

        layout.addWidget(title)

        self.test_number = self.add_info_row(
            layout,
            "Test Number",
            "—",
        )

        self.motor = self.add_info_row(
            layout,
            "Motor",
            "No test loaded",
        )

        self.date = self.add_info_row(
            layout,
            "Date",
            "—",
        )

        self.diameter = self.add_info_row(
            layout,
            "Diameter",
            "—",
        )

        self.length = self.add_info_row(
            layout,
            "Length",
            "—",
        )

        self.initial_mass = self.add_info_row(
            layout,
            "Initial Mass",
            "—",
        )

        self.propellant_mass = self.add_info_row(
            layout,
            "Propellant Mass",
            "—",
        )

        layout.addStretch()

    def add_info_row(
        self,
        layout,
        label_text,
        value_text,
    ):
        """Create and add an information row."""

        row = QFrame()
        row.setObjectName("infoRow")

        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(
            0,
            4,
            0,
            4,
        )
        row_layout.setSpacing(2)

        label = QLabel(label_text)
        label.setObjectName("infoLabel")

        value = QLabel(value_text)
        value.setObjectName("infoValue")

        row_layout.addWidget(label)
        row_layout.addWidget(value)

        layout.addWidget(row)

        return value

    def set_test_data(self, test_data):
        """
        Update the panel from a TestData object.
        """

        metadata = test_data.metadata

        if metadata.test_number is not None:
            self.test_number.setText(
                str(metadata.test_number)
            )
        else:
            self.test_number.setText("—")

        self.motor.setText(
            metadata.motor_designation
            if metadata.motor_designation
            else "Not specified"
        )

        self.date.setText(
            metadata.test_date
            if metadata.test_date
            else "—"
        )

        if metadata.motor_diameter is not None:
            self.diameter.setText(
                f"{metadata.motor_diameter:g}"
            )
        else:
            self.diameter.setText("—")

        if metadata.motor_length is not None:
            self.length.setText(
                f"{metadata.motor_length:g}"
            )
        else:
            self.length.setText("—")

        if metadata.initial_mass is not None:
            self.initial_mass.setText(
                f"{metadata.initial_mass:g}"
            )
        else:
            self.initial_mass.setText("—")

        if metadata.propellant_mass is not None:
            self.propellant_mass.setText(
                f"{metadata.propellant_mass:g}"
            )
        else:
            self.propellant_mass.setText("—")

    def clear(self):
        """Reset the panel to its unloaded state."""

        self.test_number.setText("—")
        self.motor.setText("No test loaded")
        self.date.setText("—")
        self.diameter.setText("—")
        self.length.setText("—")
        self.initial_mass.setText("—")
        self.propellant_mass.setText("—")