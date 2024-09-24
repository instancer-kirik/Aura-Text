from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

class ShortcutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setGeometry(100, 100, 400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.shortcuts_table = QTableWidget(self)
        self.shortcuts_table.setColumnCount(2)
        self.shortcuts_table.setHorizontalHeaderLabels(["Action", "Shortcut"])
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.populate_shortcuts()
        
        layout.addWidget(self.shortcuts_table)

    def populate_shortcuts(self):
        shortcuts = [
            ("New File", "Ctrl+N"),
            ("Open File", "Ctrl+O"),
            ("Save File", "Ctrl+S"),
            ("Save As", "Ctrl+Shift+S"),
            ("Close Tab", "Ctrl+W"),
            ("Undo", "Ctrl+Z"),
            ("Redo", "Ctrl+Y"),
            ("Cut", "Ctrl+X"),
            ("Copy", "Ctrl+C"),
            ("Paste", "Ctrl+V"),
            ("Find", "Ctrl+F"),
            ("Replace", "Ctrl+H"),
            ("Go to Line", "Ctrl+G"),
            ("Toggle Comment", "Ctrl+/"),
            ("Indent", "Tab"),
            ("Unindent", "Shift+Tab"),
            ("Duplicate Line", "Ctrl+D"),
            ("Move Line Up", "Alt+Up"),
            ("Move Line Down", "Alt+Down"),
            ("Toggle AI Chat", "Ctrl+Shift+A"),
            ("Format Code", "Ctrl+Alt+L"),
            ("Run Code", "F5"),
            ("Toggle File Tree", "Ctrl+B"),
            ("Toggle File Outline", "Ctrl+O"),
            ("Switch to Next Tab", "Ctrl+Tab"),
            ("Switch to Previous Tab", "Ctrl+Shift+Tab"),
        ]

        self.shortcuts_table.setRowCount(len(shortcuts))
        for row, (action, shortcut) in enumerate(shortcuts):
            self.shortcuts_table.setItem(row, 0, QTableWidgetItem(action))
            self.shortcuts_table.setItem(row, 1, QTableWidgetItem(shortcut))