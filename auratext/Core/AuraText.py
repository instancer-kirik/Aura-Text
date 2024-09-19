from __future__ import annotations
from typing import TYPE_CHECKING
from PyQt6.Qsci import QsciScintilla, QsciAPIs
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QShortcut, QKeySequence, QAction
from PyQt6.QtWidgets import QMenu, QLineEdit, QCheckBox, QPushButton, QLabel, QMessageBox, QDialog
from . import Lexers
from . import Modules as ModuleFile

import logging

if TYPE_CHECKING:
    from .window import Window


class Search(QDialog):
    def __init__(self, editor: CodeEditor) -> None:
        super().__init__()
        self.setObjectName("Search")
        self.editor = editor

        self.textBox = QLineEdit(self)
        self.textBox.setObjectName("Textbox")
        self.textBox.setGeometry(QRect(10, 30, 251, 21))
        self.textBox.setPlaceholderText("Enter text to find")

        self.cs = QCheckBox(self)
        self.cs.setObjectName("Case")
        self.cs.setGeometry(QRect(10, 70, 41, 17))
        self.cs.setText("Case sensitive")

        self.next = QPushButton(self)
        self.next.setObjectName("Next")
        self.next.setGeometry(QRect(190, 70, 71, 23))
        self.next.setText("Next")
        self.next.clicked.connect(self.find_next)

        self.previous = QPushButton(self)
        self.previous.setObjectName("Previous")
        self.previous.setText("Previous")
        self.previous.setGeometry(QRect(110, 70, 75, 23))
        self.previous.clicked.connect(self.find_previous)

        self.label = QLabel(self)
        self.label.setObjectName("Label")
        self.label.setGeometry(QRect(10, 10, 91, 16))
        self.label.setText("Enter Text to Find")

        self.setWindowTitle("Find")

    def find_next(self):
        search_text = self.textBox.text()
        case_sensitive = self.cs.isChecked()
        if search_text:
            self.editor.search(search_text, case_sensitive, forward=True)
        else:
            QMessageBox.warning(self, "Warning", "Please enter text to find.")

    def find_previous(self):
        search_text = self.textBox.text()
        case_sensitive = self.cs.isChecked()
        if search_text:
            self.editor.search(search_text, case_sensitive, forward=False)
        else:
            QMessageBox.warning(self, "Warning", "Please enter text to find.")

from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QColor
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QTextEdit
from PyQt6.QtGui import QPainter, QTextFormat
from PyQt6.QtCore import QSize

class CodeEditor(QsciScintilla):
    def __init__(self, window):
        logging.info("Entering CodeEditor.__init__")
        try:
            logging.debug("Calling QsciScintilla.__init__")
            super().__init__(window)
            logging.debug("QsciScintilla.__init__ completed")
            
            self.window = window
            
            # Set up basic editor properties
            self.setup_editor()
            
            # Set up lexer
            self.setup_lexer()
            
            # Set up autocompletion
            self.setup_autocompletion()
            
            # Set up line number area
            self.line_number_area = LineNumberArea(self)
            
            # Set up file outline
            self.file_outline_widget = FileOutlineWidget()
            
            # Set up layout
            layout = QVBoxLayout(self)
            hbox = QHBoxLayout()
            hbox.addWidget(self.line_number_area)
            hbox.addWidget(self)
            layout.addLayout(hbox)
            layout.addWidget(self.file_outline_widget)
            
            # Connect signals
            self.textChanged.connect(self.update_file_outline)
            self.cursorPositionChanged.connect(self.highlight_current_line)
            
            # Apply initial theme
            self.window.apply_theme_to_editor(self)
            
            logging.info("CodeEditor initialized successfully")
        except Exception as e:
            logging.exception(f"Error initializing CodeEditor: {e}")
            raise

    def setup_editor(self):
        self.setUtf8(True)
        self.setIndentationsUseTabs(False)
        self.setTabWidth(4)
        self.setIndentationGuides(True)
        self.setTabIndents(True)
        self.setAutoIndent(True)
        self.setCaretLineVisible(True)
        self.setCaretWidth(2)
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setMarginsForegroundColor(QColor("#ff888888"))
        self.setMarginLineNumbers(1, True)
        self.setWrapMode(QsciScintilla.WrapMode.WrapNone)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def setup_lexer(self):
        self.lexer_manager = Lexers.LexerManager(self.window)
        self.lexer_manager.apply_lexer("python", self)

    def setup_autocompletion(self):
        apis = QsciAPIs(self.lexer())
        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionCaseSensitivity(True)
        self.setAutoCompletionFillupsEnabled(True)

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.GlobalColor.yellow).lighter(160)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def update_file_outline(self):
        text = self.text()
        self.file_outline_widget.populate_file_outline(text)

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.lines())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setMarginWidth(0, self.line_number_area_width())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.GlobalColor.lightGray)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.GlobalColor.black)
                painter.drawText(0, int(top), self.line_number_area.width(), self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def show_context_menu(self, point):
        logging.info("Showing context menu- not fully implemented")
        self.context_menu.popup(self.mapToGlobal(point))

    def show_search_dialog(self):
        search_dialog = Search(self)
        search_dialog.exec()

    def calculate(self):
        ModuleFile.calculate(self)

    def encode(self):
        ModuleFile.encrypt(self)

    def decode(self):
        ModuleFile.decode(self)

    def search(self, string: str, cs: bool = False, forward: bool = True) -> None:
        """Seaches for string in the editor

        Parameters
        ----------
        string : `str`
            The string to search for
        cs : `bool`
            Case sensitive, by default False
        forward : `bool`
            Check ahead for behind the cursor, by default True
        """
        if not string:
            return
        if self.hasSelectedText():
            pos = self.getSelection()[2:] if forward else self.getSelection()[:2]
        else:
            pos = self.getCursorPosition()
        start = self.positionFromLineIndex(*pos) if forward else 0
        end = len(self.text()) if forward else self.positionFromLineIndex(*pos)
        pos = self._search(string, cs, forward, start, end)
        if pos >= 0:
            return self._highlight(len(string), pos)
        pos = self._search(string, cs, forward, 0, len(self.text()))
        if pos >= 0:
            return self._highlight(len(string), pos)
        if self.hasSelectedText():
            pos = self.getSelection()[2:] if forward else self.getSelection()[:2]
            return self.setCursorPosition(*pos)

    def _highlight(self, length: int, pos: int) -> None:
        """Highlights the searched text if found

        Parameters
        ----------
        length: `int`
            The string being
        pos: `int`
            The starting position of the highlight
        """
        self.SendScintilla(self.SCI_SETSEL, pos, pos + length)

    def _search(self, string: str, cs: bool = False, forward: bool = True, start: int = -1, end: int = -1) -> None:
        search = self.SendScintilla
        search(self.SCI_SETTARGETSTART, start if forward else end)
        search(self.SCI_SETTARGETEND, end if forward else start)
        search(self.SCI_SETSEARCHFLAGS, self.SCFIND_MATCHCASE if cs else 0)
        return search(self.SCI_SEARCHINTARGET, len(string), bytes(string, "utf-8"))

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

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
