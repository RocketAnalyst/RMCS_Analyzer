from PySide6.QtCore import Qt
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
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            16,
            0,
            16,
            16,
        )
        layout.setSpacing(12)

        title = QLabel("TEST FILES")
        title.setObjectName("sectionTitle")

        layout.addWidget(title)

        self.file_list = QListWidget()
        self.file_list.setObjectName("fileList")

        self.show_empty_state()

        layout.addWidget(
            self.file_list,
            1,
        )

    def show_empty_state(self):
        """Display the empty file-list state."""

        self.file_list.clear()

        item = QListWidgetItem(
            "No test files loaded"
        )

        item.setFlags(
            Qt.ItemFlag.NoItemFlags
        )

        self.file_list.addItem(item)

    def add_file(
        self,
        filename,
    ):
        """Add a test filename to the list."""

        if (
            self.file_list.count() == 1
            and self.file_list.item(0).text()
            == "No test files loaded"
        ):
            self.file_list.clear()

        item = QListWidgetItem(filename)

        self.file_list.addItem(item)

        self.file_list.setCurrentItem(item)

    def clear(self):
        """Remove all loaded files."""

        self.show_empty_state()