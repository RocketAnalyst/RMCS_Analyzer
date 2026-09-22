from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
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
    remove_requested = Signal(int)

    EMPTY_TEXT = "No test files loaded"

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            16,
            7,
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

        self.remove_button = QPushButton(
            "Remove Selected Test"
        )
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(
            self._on_remove_clicked
        )
        layout.addWidget(
            self.remove_button
        )

        self.show_empty_state()

    def _update_remove_button(self):
        """Enable removal only when a real test row is selected."""

        row = self.file_list.currentRow()
        item = self.file_list.item(row) if row >= 0 else None

        enabled = (
            item is not None
            and item.data(Qt.ItemDataRole.UserRole) is not None
        )
        self.remove_button.setEnabled(enabled)

    def _on_remove_clicked(self):
        """Request that the main window remove the selected test."""

        row = self.file_list.currentRow()
        item = self.file_list.item(row) if row >= 0 else None

        if item is None:
            return

        test_index = item.data(Qt.ItemDataRole.UserRole)
        if test_index is None:
            return

        self.remove_requested.emit(int(test_index))

    def remove_file(self, test_index):
        """Remove the list row associated with a TestSession index."""

        for row in range(self.file_list.count()):
            item = self.file_list.item(row)
            if item is None:
                continue

            if item.data(Qt.ItemDataRole.UserRole) == test_index:
                self.file_list.blockSignals(True)
                self.file_list.takeItem(row)
                self.file_list.blockSignals(False)
                break

        self._reindex_items()
        self._update_remove_button()

    def _reindex_items(self):
        """Keep UserRole session indices aligned after a removal."""

        for row in range(self.file_list.count()):
            item = self.file_list.item(row)
            if item is not None:
                item.setData(
                    Qt.ItemDataRole.UserRole,
                    row,
                )

        if self.file_list.count() == 0:
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
        self._update_remove_button()

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
        self._update_remove_button()

    def _on_current_row_changed(
        self,
        row,
    ):
        """Report the selected TestSession index."""

        self._update_remove_button()

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