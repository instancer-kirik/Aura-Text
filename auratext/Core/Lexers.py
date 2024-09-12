"""
This file includes lexer functions for all the languages supported by Aura Text. The lexer functionalities are implemented using QSciScintilla.
"""
import re

from PyQt6.Qsci import (
    QsciLexerCPP,
    QsciLexerVerilog,
    QsciLexerAVS,
    QsciLexerAsm,
    QsciLexerBash,
    QsciLexerBatch,
    QsciLexerJavaScript, QsciLexerCustom,
)
from PyQt6.Qsci import QsciLexerCSharp, QsciLexerFortran77, QsciLexerOctave, QsciLexerVHDL
from PyQt6.Qsci import (
    QsciLexerJava,
    QsciLexerJSON,
    QsciLexerYAML,
    QsciLexerHTML,
    QsciLexerRuby,
    QsciLexerCMake,
    QsciLexerCoffeeScript,
)
from PyQt6.Qsci import (
    QsciLexerPerl,
    QsciLexerCSS,
    QsciLexerLua,
    QsciLexerSQL,
    QsciLexerPascal,
    QsciLexerPostScript,
    QsciLexerTCL,
    QsciLexerSRec,
    QsciLexerSpice,
)
from PyQt6.Qsci import (
    QsciLexerTeX,
    QsciLexerPython,
    QsciLexerXML,
    QsciLexerMakefile,
    QsciLexerMarkdown,
    QsciLexerFortran,
)
from PyQt6.QtGui import QColor, QFont


class ColorCodeLexer(QsciLexerCustom):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColor(QColor("#000000"), 0)  # Default color
        self.setFont(QFont("Courier", 10))

    def language(self):
        return "ColorCode"

    def styleText(self, start, end):
        editor = self.editor()
        if not editor:
            return

        text = editor.text()[start:end]
        color_pattern = r'#[0-9a-fA-F]{6}\b'  # Regular expression to match hex color codes

        for match in re.finditer(color_pattern, text):
            start_index = match.start()
            end_index = match.end()
            self.startStyling(start + start_index, 0x11)  # Using style 17
            self.setStyling(end_index - start_index, 0)


"""This file includes lexer functions for all the languages supported by Aura Text. 
The lexer functionalities are implemented using QSciScintilla."""

import re
from PyQt6.Qsci import *
from PyQt6.QtGui import QColor, QFont

import logging

class LexerManager:
    def __init__(self, window):
        logging.debug("Initializing LexerManager")
        self.window = window
        self.lexers = {
            "python": QsciLexerPython,
            "cpp": QsciLexerCPP,
            "javascript": QsciLexerJavaScript,
            "html": QsciLexerHTML,
            "markdown": QsciLexerMarkdown,
            # Add more lexers here as needed
        }

    def get_available_lexers(self):
        return list(self.lexers.keys())

    def apply_lexer(self, language, editor):
        logging.debug(f"Attempting to apply lexer for language: {language}")
        if editor is None:
            logging.warning("No editor provided to apply lexer to")
            return

        try:
            method = getattr(self, language, None)
            if method:
                method(editor)
                logging.debug(f"Lexer for {language} applied successfully")
            else:
                logging.warning(f"No lexer method found for language: {language}")
        except Exception as e:
            logging.exception(f"Error applying lexer for {language}: {e}")

    def python(self, editor):
        logging.debug("Applying Python lexer")
        lexer = QsciLexerPython(editor)
        editor.setLexer(lexer)
        logging.debug("Python lexer applied")

    def cpp(self, editor):
        logging.debug("Applying C++ lexer")
        lexer = QsciLexerCPP(editor)
        editor.setLexer(lexer)
        logging.debug("C++ lexer applied")

    # Add more lexer methods as needed

class ColorCodeLexer(QsciLexerCustom):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColor(QColor("#000000"), 0)  # Default color
        self.setFont(QFont("Courier", 10))

    def language(self):
        return "ColorCode"

    def styleText(self, start, end):
        editor = self.editor()
        if not editor:
            return

        text = editor.text()[start:end]
        color_pattern = r'#[0-9a-fA-F]{6}\b'  # Regular expression to match hex color codes

        for match in re.finditer(color_pattern, text):
            start_index = match.start()
            end_index = match.end()
            self.startStyling(start + start_index, 0x11)  # Using style 17
            self.setStyling(end_index - start_index, 0)
