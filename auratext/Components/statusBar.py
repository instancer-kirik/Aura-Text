import json
import os
import time
import sys
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QStatusBar, QWidget

# Determine app data directory
if sys.platform == "win32":
    local_app_data = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "AuraText")
elif sys.platform == "darwin":
    local_app_data = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "AuraText")
else:
    local_app_data = os.path.join(os.path.expanduser("~"), ".local", "share", "AuraText")

# Ensure directories exist
os.makedirs(os.path.join(local_app_data, "data"), exist_ok=True)

# Path to theme file
theme_file = os.path.join(local_app_data, "data", "theme.json")

# Create default theme if it doesn't exist
if not os.path.exists(theme_file):
    default_theme = {
        "sidebar_bg": "#1E1E1E",
        "text_color":"#F0F0F0",
        "accent_color": "#007ACC",
        "editor_bg": "#1E1E1E",
        "editor_text": "#D4D4D4",
        "line_number_bg": "#252526",
        "line_number_text": "#858585",
        "selection_bg": "#264F78",
        "current_line_bg": "#282828",
        "matching_bracket_bg": "#3D3D3D",
        "search_result_bg": "#613214",
        "find_match_bg": "#515C6A"
    }
    
    with open(theme_file, "w") as f:
        json.dump(default_theme, f, indent=4)

# Load theme
with open(theme_file, "r") as themes_file:
    _themes = json.load(themes_file)

class Separator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)


class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        #self.current_editor = parent.current_editor
        self.current_widget = parent.tab_widget.currentWidget()
        self.setStyleSheet(
            f"""
            QStatusBar {{
                background-color: {_themes['sidebar_bg']};
                color: {_themes['text_color']};
                padding-bottom: 2px;
                position: absolute;
                bottom: 0;
            }}
            QStatusBar::item {{
                border: none;
            }}
            QLabel {{
                padding: 0 2px;
            }}
            """
        )

        self.lineLabel = QLabel("▼ Line:")
        self.lineValueLabel = QLabel("0")
        self.columnLabel = QLabel("▲ Column:")
        self.columnValueLabel = QLabel("0")
        self.totalLinesLabel = QLabel("∑ Total Lines:")
        self.totalLinesValueLabel = QLabel("0")
        self.wordsLabel = QLabel("⌁ Words:")
        self.wordsValueLabel = QLabel("0")

        smallFont = QFont()
        smallFont.setPointSize(8)

        for label in [
            self.lineLabel,
            self.columnLabel,
            self.totalLinesLabel,
            self.wordsLabel,
        ]:
            label.setFont(smallFont)
            #label.setStyleSheet(f"color: {};")

        for label in [
            self.lineValueLabel,
            self.columnValueLabel,
            self.totalLinesValueLabel,
            self.wordsValueLabel,
        ]:
            label.setFont(smallFont)
            #label.setStyleSheet(f"color: ""/;")

        rightWidget = QWidget()
        rightLayout = QHBoxLayout(rightWidget)
        rightLayout.setContentsMargins(0, 0, 0, 5)
        rightLayout.setSpacing(1)

        rightLayout.addWidget(Separator())
        rightLayout.addWidget(self.lineLabel)
        rightLayout.addWidget(self.lineValueLabel)
        rightLayout.addWidget(Separator())
        rightLayout.addWidget(self.columnLabel)
        rightLayout.addWidget(self.columnValueLabel)
        rightLayout.addWidget(Separator())
        rightLayout.addWidget(self.totalLinesLabel)
        rightLayout.addWidget(self.totalLinesValueLabel)
        rightLayout.addWidget(Separator())
        rightLayout.addWidget(self.wordsLabel)
        rightLayout.addWidget(self.wordsValueLabel)
        rightLayout.addWidget(Separator())

        self.addPermanentWidget(rightWidget)


        self.editModeLabel = QLabel("ReadOnly")
        self.editModeLabel.setFont(smallFont)
        self.editModeLabel.setStyleSheet(
            f"""
            color: {"#FFFFFF;"};
            font-weight: bold;
            margin-bottom: 5px;
            """
        )

        self.addWidget(self.editModeLabel)

    def updateStats(self, line, column, total_lines, words):
        self.lineValueLabel.setText(str(line))
        self.columnValueLabel.setText(str(column))
        self.totalLinesValueLabel.setText(str(total_lines))
        self.wordsValueLabel.setText(str(words))

    def updateEditMode(self, mode):
        self.editModeLabel.setText(mode)
        #if mode == "ReadOnly":
        #    self.current_widget.setReadOnly(True)
        #else:
        #    self.current_widget.setReadOnly(False)
