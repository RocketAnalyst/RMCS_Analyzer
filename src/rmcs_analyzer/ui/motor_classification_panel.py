from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout
from ..analysis.motor_class import MotorClassCalculator


class MotorClassificationPanel(QFrame):
    """Motor impulse-class carousel for the dashboard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("motorClassificationPanel")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 9)
        layout.setSpacing(7)

        title = QLabel("Motor Classification")
        title.setObjectName("motorClassificationTitle")
        layout.addWidget(title)

        self.class_cards = QHBoxLayout()
        self.class_cards.setContentsMargins(0, 0, 0, 0)
        self.class_cards.setSpacing(2)
        layout.addLayout(self.class_cards)

        self.left_card = self._make_card("—", "neighbor")
        self.center_card = self._make_card("—", "selected")
        self.right_card = self._make_card("—", "neighbor")

        self.class_cards.addWidget(self.left_card, 1)
        self.class_cards.addWidget(self.center_card, 1)
        self.class_cards.addWidget(self.right_card, 1)

        self.impulse_label = QLabel("Measured Impulse: —")
        self.impulse_label.setObjectName("motorClassificationImpulse")
        self.impulse_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.impulse_label)

        self.result_label = QLabel("—")
        self.result_label.setObjectName("motorClassificationResult")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)

        self.range_label = QLabel("Range: —")
        self.range_label.setObjectName("motorClassificationRange")
        self.range_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.range_label)

        self.note_label = QLabel(
            "Motor class based on measured total impulse."
        )
        self.note_label.setObjectName("motorClassificationNote")
        self.note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.note_label.setWordWrap(True)
        layout.addWidget(self.note_label)

        self.setMinimumHeight(190)

    def _make_card(self, text, role):
        frame = QFrame()
        frame.setObjectName(f"motorClassCard_{role}")
        frame.setMinimumHeight(44)
        frame.setMaximumHeight(48)

        v = QVBoxLayout(frame)
        v.setContentsMargins(2, 2, 2, 2)
        v.setSpacing(0)

        label = QLabel(text)
        label.setObjectName("motorClassCardLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(label)

        frame._label = label
        return frame

    @staticmethod
    def _neighbors(current):
        names = [name for name, _ in MotorClassCalculator.CLASS_LIMITS]
        if current not in names:
            return "—", "—", "—"
        index = names.index(current)
        return (
            names[index - 1] if index > 0 else "—",
            current,
            names[index + 1] if index + 1 < len(names) else "—",
        )

    def set_result(self, classification, impulse_Ns=None, designation=None):
        current = classification.motor_class
        left, center, right = self._neighbors(current)

        self.left_card._label.setText(left)
        self.center_card._label.setText(center)
        self.right_card._label.setText(right)

        self.impulse_label.setText(
            f"Measured Impulse: {impulse_Ns:,.1f} N·s"
            if impulse_Ns is not None else "Measured Impulse: —"
        )

        if current is None:
            self.result_label.setText("—")
            self.range_label.setText("Range: —")
            return

        self.result_label.setText(designation if designation else current)

        lower = classification.lower_limit_Ns
        upper = classification.upper_limit_Ns
        self.range_label.setText(
            f"Range: {lower:,.0f} – {upper:,.0f} N·s"
            if lower is not None and upper is not None
            else "Range: —"
        )
