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


    
class CodeEditor(QsciScintilla):
    def __init__(self, window):
        logging.info("Entering CodeEditor.__init__")
        try:
            logging.debug("Calling QsciScintilla.__init__")
            super().__init__(window)
            logging.debug("QsciScintilla.__init__ completed")
            
            self.window = window
            logging.debug("Window assigned to self.window")
            
            logging.debug("Setting up basic editor properties")
            self.setUtf8(True)
            self.setIndentationsUseTabs(False)
            self.setTabWidth(4)
            self.setIndentationGuides(True)
            self.setTabIndents(True)
            self.setAutoIndent(True)
            self.setCaretLineVisible(True)
            self.setCaretWidth(2)
            logging.debug("Basic editor properties set")
            
            logging.debug("Setting up margins")
            self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
            self.setMarginWidth(0, "0000")
            self.setMarginsForegroundColor(QColor("#ff888888"))
            self.setMarginLineNumbers(1, True)
            logging.debug("Margins set up")
            
            logging.debug("Setting up lexer")
            self.lexer_manager = Lexers.LexerManager(window)
            logging.debug("LexerManager created")
            
            logging.debug("Applying default lexer")
            self.lexer_manager.apply_lexer("python", self)  # Pass self as the editor
            logging.debug("Default lexer applied")
            
            logging.debug("Setting up autocompletion")
            apis = QsciAPIs(self.lexer())
            self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
            self.setAutoCompletionThreshold(1)
            self.setAutoCompletionCaseSensitivity(True)
            self.setAutoCompletionFillupsEnabled(True)
            logging.debug("Autocompletion set up")
            
            logging.debug("Setting up wrapping and scrollbars")
            self.setWrapMode(QsciScintilla.WrapMode.WrapNone)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            logging.debug("Wrapping and scrollbars set up")
            
            logging.debug("Applying theming")
            self.setPaper(QColor(window._themes["editor_theme"]))
            self.setColor(QColor(window._themes["editor_fg"]))
            self.setFont(QFont(window._themes["font"]))
            logging.debug("Theming applied")
            
            logging.info("CodeEditor initialized successfully")
        except Exception as e:
            logging.exception(f"Error initializing CodeEditor: {e}")
            raise  # Re-raise the exception to propagate it

    def show_context_menu(self, point):
        self.context_menu.popup(self.mapToGlobal(point))

    def show_search_dialog(self):
        search_dialog = Search(self)
        search_dialog.exec()

    def calculate(self):
        ModuleFile.calculate(self)

    def encode(self):
        ModuleFile.encypt(self)

    def decode(self):
        ModuleFile.decode(self)

    # noinspection ReturnValueFromInit
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

    # noinspection
    def _search(
            self,
            string: str,
            cs: bool = False,
            forward: bool = True,
            start: int = -1,
            end: int = -1,
    ) -> None:
        """Sets search for the string"""
        search = self.SendScintilla
        search(self.SCI_SETTARGETSTART, start if forward else end)
        search(self.SCI_SETTARGETEND, end if forward else start)
        search(self.SCI_SETSEARCHFLAGS, self.SCFIND_MATCHCASE if cs else 0)
        return search(self.SCI_SEARCHINTARGET, len(string), bytes(string, "utf-8"))
