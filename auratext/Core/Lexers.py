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
    # QsciLexerElixir,
    # QsciLexerErlang,
    # QsciLexerFSharp,
    # QsciLexerGo,
    # QsciLexerGroovy,
    # QsciLexerHaskell,
)
from PyQt6.Qsci import (
    QsciLexerTeX,
    QsciLexerPython,
    QsciLexerXML,
    QsciLexerMakefile,
    QsciLexerMarkdown,
    QsciLexerFortran,
   
    QsciLexerHTML,
    QsciLexerJava,
    QsciLexerJSON,
    
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
    def __init__(self, mm):
        logging.debug("Initializing LexerManager")
        self.mm = mm
        self.lexers = {
            "py": QsciLexerPython,
            "cpp": QsciLexerCPP,
            "javascript": QsciLexerJavaScript,
            "html": QsciLexerHTML,
           # "markdown": QsciLexerMarkdown,
            "md": QsciLexerMarkdown,
            "json": QsciLexerJSON,
            "yaml": QsciLexerYAML,
            "css": QsciLexerCSS,
            "lua": QsciLexerLua,
            "sql": QsciLexerSQL,
            "pascal": QsciLexerPascal,
            "postscript": QsciLexerPostScript,
            "tcl": QsciLexerTCL,
            "srec": QsciLexerSRec,
            "spice": QsciLexerSpice,
            "fortran": QsciLexerFortran,
            
            "makefile": QsciLexerMakefile,
            "verilog": QsciLexerVerilog,
            "vhdl": QsciLexerVHDL,
            "asm": QsciLexerAsm,
            "bash": QsciLexerBash,
            "batch": QsciLexerBatch,
            "cmake": QsciLexerCMake,
            "coffeescript": QsciLexerCoffeeScript,
            # "elixir": QsciLexerElixir,
            # "erlang": QsciLexerErlang,
            # "fsharp": QsciLexerFSharp,
            # "go": QsciLexerGo,
            # "groovy": QsciLexerGroovy,
            # "haskell": QsciLexerHaskell,
            "html": QsciLexerHTML,
            "java": QsciLexerJava,
            "json": QsciLexerJSON,
            "markdown": QsciLexerMarkdown,
            
            
        }

    def get_available_lexers(self):
        return list(self.lexers.keys())

    def apply_lexer(self, language, editor):
        logging.debug(f"Attempting to apply lexer for language: {language}")
        if editor is None:
            logging.warning("No editor provided to apply lexer to")
            return

        lexer_class = self.lexers.get(language)
        if lexer_class:
            try:
                lexer = lexer_class(editor)
                editor.set_lexer(lexer)
                logging.info(f"Lexer for {language} applied successfully")
            except Exception as e:
                logging.exception(f"Error applying lexer for {language}: {e}")
        else:
            logging.warning(f"No lexer found for language: {language}")

    # Remove individual language methods like python, cpp, json, yaml
    # as they are no longer needed with the updated apply_lexer method.

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
