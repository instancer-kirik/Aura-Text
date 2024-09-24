from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

class FileOutlineWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)

    def populate_file_outline(self, text):
        self.clear()
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip().startswith('class ') or line.strip().startswith('def '):
                item = QTreeWidgetItem([f"{i + 1}: {line.strip()}"])
                self.addTopLevelItem(item)
