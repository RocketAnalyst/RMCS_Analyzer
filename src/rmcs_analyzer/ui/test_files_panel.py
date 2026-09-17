from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)


class TestFilesPanel(QFrame):
    """
    Displays the test files currently loaded into the application.

    The panel is responsible only for displaying the available tests
    and reporting which test the user selects. It does not perform
    test management or analysis itself.
    """

    test_selected = Signal(int)

    EMPTY_TEXT = "No test files loaded"

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            16,
            0,
            16,
            16,
        )

        layout.setSpacing(
            12
        )

        title = QLabel(
            "TEST FILES"
        )

        title.setObjectName(
            "sectionTitle"
        )

        layout.addWidget(
            title
        )

        self.file_list = QListWidget()

        self.file_list.setObjectName(
            "fileList"
        )

        self.file_list.currentRowChanged.connect(
            self._on_current_row_changed
        )

        layout.addWidget(
            self.file_list,
            1,
        )

        self.show_empty_state()

    def show_empty_state(self):
        """Display the empty file-list state."""

        self.file_list.blockSignals(
            True
        )

        self.file_list.clear()

        item = QListWidgetItem(
            self.EMPTY_TEXT
        )

        item.setFlags(
            Qt.ItemFlag.NoItemFlags
        )

        self.file_list.addItem(
            item
        )

        self.file_list.blockSignals(
            False
        )

    def add_file(
        self,
        filename,
        test_index=None,
    ):
        """
        Add a test filename to the list.

        The optional test_index identifies the corresponding test
        inside the TestSession.
        """

        self.file_list.blockSignals(
            True
        )

        if (
            self.file_list.count() == 1
            and self.file_list.item(0).text()
            == self.EMPTY_TEXT
        ):
            self.file_list.clear()

        item = QListWidgetItem(
            filename
        )

        if test_index is not None:
            item.setData(
                Qt.ItemDataRole.UserRole,
                test_index,
            )

        self.file_list.addItem(
            item
        )

        self.file_list.setCurrentItem(
            item
        )

        self.file_list.blockSignals(
            False
        )

        if test_index is not None:
            self.test_selected.emit(
                test_index
            )

    def set_current_test(
        self,
        test_index,
    ):
        """
        Select a test in the list by its TestSession index.
        """

        if (
            test_index < 0
            or test_index >= self.file_list.count()
        ):
            return

        self.file_list.blockSignals(
            True
        )

        self.file_list.setCurrentRow(
            test_index
        )

        self.file_list.blockSignals(
            False
        )

    def _on_current_row_changed(
        self,
        row,
    ):
        """Report the selected TestSession index."""

        if row < 0:
            return

        item = self.file_list.item(
            row
        )

        if item is None:
            return

        test_index = item.data(
            Qt.ItemDataRole.UserRole
        )

        if test_index is None:
            return

        self.test_selected.emit(
            int(test_index)
        )

    def clear(self):
        """Remove all loaded files."""

        self.show_empty_state()