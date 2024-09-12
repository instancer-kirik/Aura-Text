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

class LexerManager:
    def __init__(self, window):
        self.window = window
        self.editor = window.current_editor
        self.themes = window._themes

    def apply_lexer(self, lexer_class, custom_settings=None):
        lexer = lexer_class()
        lexer.setDefaultColor(QColor("#FFFFFF"))
        self.editor.setLexer(lexer)
        lexer.setPaper(QColor(self.themes["editor_theme"]))
        
        # Apply common settings
        lexer.setColor(QColor("#808080"), lexer.Comment)
        lexer.setColor(QColor("#FFA500"), lexer.Keyword)
        lexer.setFont(QFont(self.themes["font"]))

        # Apply custom settings if provided
        if custom_settings:
            for style, color in custom_settings.items():
                lexer.setColor(QColor(color), style)

        self.editor.setMarginsBackgroundColor(QColor(self.themes["margin_theme"]))
        self.editor.setMarginsForegroundColor(QColor("#FFFFFF"))

    def python(self):
        custom_settings = {
            QsciLexerPython.ClassName: "#FFFFFF",
            QsciLexerPython.TripleSingleQuotedString: "#59ff00",
            QsciLexerPython.TripleDoubleQuotedString: "#59ff00",
            QsciLexerPython.SingleQuotedString: "#3ba800",
            QsciLexerPython.DoubleQuotedString: "#3ba800"
        }
        self.apply_lexer(QsciLexerPython, custom_settings)

    def cpp(self):
        custom_settings = {
            QsciLexerCPP.Identifier: "#ffffff"
        }
        self.apply_lexer(QsciLexerCPP, custom_settings)

    def javascript(self):
        custom_settings = {
            QsciLexerJavaScript.Default: "#ffffff"
        }
        self.apply_lexer(QsciLexerJavaScript, custom_settings)

    def html(self):
        custom_settings = {
            QsciLexerHTML.Tag: "#808080"
        }
        self.apply_lexer(QsciLexerHTML, custom_settings)

    def markdown(self):
        custom_settings = {
            QsciLexerMarkdown.Header1: "#808080",
            QsciLexerMarkdown.Header2: "#FFA500",
            QsciLexerMarkdown.Header3: "#ffffff"
        }
        self.apply_lexer(QsciLexerMarkdown, custom_settings)

    # Define methods for other languages
    def csharp(self): self.apply_lexer(QsciLexerCSharp)
    def avs(self): self.apply_lexer(QsciLexerAVS)
    def asm(self): self.apply_lexer(QsciLexerAsm)
    def coffeescript(self): self.apply_lexer(QsciLexerCoffeeScript)
    def json(self): self.apply_lexer(QsciLexerJSON)
    def fortran(self): self.apply_lexer(QsciLexerFortran)
    def java(self): self.apply_lexer(QsciLexerJava)
    def bash(self): self.apply_lexer(QsciLexerBash)
    def yaml(self): self.apply_lexer(QsciLexerYAML)
    def xml(self): self.apply_lexer(QsciLexerXML)
    def ruby(self): self.apply_lexer(QsciLexerRuby)
    def perl(self): self.apply_lexer(QsciLexerPerl)
    def css(self): self.apply_lexer(QsciLexerCSS)
    def lua(self): self.apply_lexer(QsciLexerLua)
    def sql(self): self.apply_lexer(QsciLexerSQL)
    def tex(self): self.apply_lexer(QsciLexerTeX)
    def bat(self): self.apply_lexer(QsciLexerBatch)
    def cmake(self): self.apply_lexer(QsciLexerCMake)
    def postscript(self): self.apply_lexer(QsciLexerPostScript)
    def makefile(self): self.apply_lexer(QsciLexerMakefile)
    def pascal(self): self.apply_lexer(QsciLexerPascal)
    def tcl(self): self.apply_lexer(QsciLexerTCL)
    def verilog(self): self.apply_lexer(QsciLexerVerilog)
    def spice(self): self.apply_lexer(QsciLexerSpice)
    def vhdl(self): self.apply_lexer(QsciLexerVHDL)
    def octave(self): self.apply_lexer(QsciLexerOctave)
    def fortran77(self): self.apply_lexer(QsciLexerFortran77)

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
