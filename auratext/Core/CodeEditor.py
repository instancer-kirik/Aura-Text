from PyQt6.Qsci import QsciScintilla, QsciAPIs
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QTextBrowser, QComboBox, QLabel
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QImage, QKeySequence, QShortcut, QKeyEvent, QAction
from PyQt6.QtCore import Qt, QTimer, QRect, QSize, QStringListModel
import logging
import os
import re
import time
import markdown
from GUX.markdown_viewer import MarkdownViewer
from .file_outline_widget import FileOutlineWidget
from .search_and_line_number import Search
from .Modules import ModulesFile
from HMC.settings_manager import SettingsManager
from PyQt6.QtWidgets import QMenu, QCompleter
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QKeySequence, QTextCursor
import random
class CustomQsciScintilla(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.forced_line_color = QColor("#222222")  # Bright red for debugging
        self.forced_line_alpha = 123  # More opaque for visibility
        self.sidebar_color = QColor("#2E3440")  # Dark color for sidebar
        self.sidebar_text_color = QColor("#D8DEE9")  # Light color for sidebar text

        # Set up the margin (sidebar)
        self.setMarginsForegroundColor(self.sidebar_text_color)
        self.setMarginsBackgroundColor(self.sidebar_color)
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")  # Adjust width as needed

    def paintEvent(self, event):
        super().paintEvent(event)
        self.SendScintilla(QsciScintilla.SCI_SETCARETLINEBACK, self.forced_line_color.rgb() & 0xFFFFFF)
        self.SendScintilla(QsciScintilla.SCI_SETCARETLINEBACKALPHA, self.forced_line_alpha)
        self.SendScintilla(QsciScintilla.SCI_SETCARETLINEVISIBLE, True)

        # Force sidebar color
        painter = QPainter(self.viewport())
        painter.fillRect(0, 0, self.marginWidth(0), self.height(), self.sidebar_color)
        painter.end()

        color = self.SendScintilla(QsciScintilla.SCI_GETCARETLINEBACK)
        alpha = self.SendScintilla(QsciScintilla.SCI_GETCARETLINEBACKALPHA)
        # logging.warning(f"Paint event - Forced line color: #{color:06x}, Alpha: {alpha}")

    def set_forced_line_color(self, color, alpha):
        self.forced_line_color = QColor(color)
        self.forced_line_alpha = alpha
        self.update()

class CodeEditor(QWidget):
    
    def __init__(self, mm, parent=None):
        super().__init__(parent)
        self.mm = mm
        self.file_path = None
        self.current_language = None
        self.image_map = {}
        self.vault_path = None
        self.vault_manager = mm.vault_manager
        self.markdown_viewer = MarkdownViewer(self.vault_path)
        self.current_lexer = None  # Add this line to track the current lexer
        self.highlight_enabled = True
        self.text_edit = CustomQsciScintilla(self)
        self.file_outline_widget = FileOutlineWidget(self)
        self.markdown_preview = QTextBrowser(self)
        self.fileset_selector = QComboBox(self)
        self.setup_fileset_selector()
        self.completer = QCompleter(self)
        self.import_completer = self.completer
        self._is_modified = False
        self.text_edit.textChanged.connect(self._handle_text_changed)

        self.setup_ui()
        self.setup_editor()
        self.setup_connections()
        self.setup_shortcuts()
        self.setup_indentation_guides()
        self.setup_block_selection()
        self.debug_colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF"]
        self.current_debug_color = 0
        
        self.settings_manager = mm.settings_manager
        self.load_typing_effect_settings()

        logging.info("CodeEditor initialization complete")
        self.setup_auto_import_completion()

        self.cursor_manager = mm.cursor_manager if hasattr(mm, 'cursor_manager') else None
        self.setup_lsp_connections()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove any margins
        layout.setSpacing(0)  # Remove spacing between widgets

        self.text_edit = CustomQsciScintilla(self)
        layout.addWidget(self.text_edit)

        # If you have other widgets in the CodeEditor, add them here
        # For example:
        # self.line_number_area = LineNumberArea(self.text_edit)
        # layout.addWidget(self.line_number_area)

        self.setLayout(layout)
    def setup_editor(self):
        self.text_edit.setUtf8(True)
        self.text_edit.setIndentationsUseTabs(False)
        self.text_edit.setTabWidth(4)
        self.text_edit.setIndentationGuides(True)
        self.text_edit.setTabIndents(True)
        self.text_edit.setAutoIndent(True)
        self.text_edit.setCaretLineVisible(True)
        self.text_edit.setCaretWidth(2)
        self.text_edit.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.text_edit.setMarginWidth(0, "0000")
        self.text_edit.setMarginsForegroundColor(QColor("#ff888888"))
        self.text_edit.setMarginLineNumbers(1, True)
        self.text_edit.setWrapMode(QsciScintilla.WrapMode.WrapNone)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def setup_connections(self):
        self.text_edit.textChanged.connect(self.update_file_outline)
        self.text_edit.textChanged.connect(self.on_text_changed)   
        self.fileset_selector.currentTextChanged.connect(self.on_fileset_changed)
       
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_markdown_preview)
        self.update_timer.setInterval(1000)
        
        self.completer.activated.connect(self.insert_completion)

    def setup_shortcuts(self):
        radial_menu_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        radial_menu_shortcut.activated.connect(self.show_radial_menu)

    def setup_indentation_guides(self):
        # Enable indentation guides
        self.text_edit.setIndentationGuides(True)
        
        # Set the indentation guide color
        self.text_edit.setIndentationGuidesBackgroundColor(QColor("#e0e0e0"))
        self.text_edit.setIndentationGuidesForegroundColor(QColor("#c0c0c0"))

        # Connect to the cursorPositionChanged signal to update indentation highlighting
        self.text_edit.cursorPositionChanged.connect(self.highlight_indentation_block)

    def highlight_indentation_block(self):
        # Clear previous highlighting
        self.text_edit.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 1)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICATORCLEARRANGE, 0, self.text_edit.length())

        # Get the current line and its indentation level
        current_line, _ = self.text_edit.getCursorPosition()
        current_indent = self.text_edit.indentation(current_line)

        # Set up the indicator style for indentation highlighting
        self.text_edit.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 1)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, 1, QsciScintilla.INDIC_ROUNDBOX)
        highlight_color = QColor(Qt.GlobalColor.lightGray)
        highlight_color.setAlpha(40)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETFORE, 1, highlight_color.rgb() & 0xFFFFFF)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETALPHA, 1, highlight_color.alpha())

        # Highlight the indentation block
        start_line = current_line
        end_line = current_line
        
        # Search upwards for the start of the block
        while start_line > 0 and self.text_edit.indentation(start_line - 1) >= current_indent:
            start_line -= 1

        # Search downwards for the end of the block
        total_lines = self.text_edit.lines()
        while end_line < total_lines - 1 and self.text_edit.indentation(end_line + 1) >= current_indent:
            end_line += 1

        # Apply the highlighting
        for line in range(start_line, end_line + 1):
            line_start = self.text_edit.positionFromLineIndex(line, 0)
            line_end = self.text_edit.positionFromLineIndex(line + 1, 0)
            self.text_edit.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, line_start, line_end - line_start)

    def update_file_outline(self):
        text = self.text_edit.text()
        self.file_outline_widget.populate_file_outline(text)

    def highlight_current_line(self):
        self.text_edit.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 0)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICATORCLEARRANGE, 0, self.text_edit.length())
        line, _ = self.text_edit.getCursorPosition()
        self.text_edit.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 0)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, 0, QsciScintilla.INDIC_STRAIGHTBOX)
        
        # Use the theme color instead of a hard-coded value
        highlight_color = self.settings_manager.get_current_theme_color("currentLineColor", QColor(230, 230, 230))
        highlight_color.setAlpha(40)  # Set transparency
        
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETFORE, 0, highlight_color.rgb() & 0xFFFFFF)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETALPHA, 0, highlight_color.alpha())
        line_start = self.text_edit.positionFromLineIndex(line, 0)
        line_end = self.text_edit.positionFromLineIndex(line + 1, 0)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, line_start, line_end - line_start)
        self.highlight_indentation_block()  # Add this line to update indentation highlighting

    def update_markdown_preview(self):
        if self.current_language == 'markdown':
            md_text = self.text_edit.text()
            self.markdown_viewer.setHtml(self.markdown_to_html(md_text))

    def set_language(self, language):
        if self.current_language != language:
            self.current_language = language
            self.mm.lexer_manager.apply_lexer(language, self)#wow what code
            self.toggle_markdown_preview(language == 'markdown')
            self.show_current_lexer()  # Add this line to update the lexer display

    def set_lexer(self, lexer):
        # Directly set the lexer on the QsciScintilla editor
        self.text_edit.setLexer(lexer)
        self.current_lexer = type(lexer).__name__  # Update the current lexer name
        self.show_current_lexer()  # Update the lexer display
    def set_language(self, language):
        if self.current_language != language:
            self.current_language = language
            self.set_lexer(language)
    def toggle_markdown_preview(self, show):
        if show:
            self.markdown_preview.show()
            self.update_timer.start()
        else:
            self.markdown_preview.hide()
            self.update_timer.stop()

    
    def load_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        self.text_edit.setText(content)
        self.file_path = file_path
        self.set_language_from_file_path(file_path)

    def set_language_from_file_path(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()
        language_map = {
            'py': 'python', 'md': 'md', 'cpp': 'cpp',
            'js': 'javascript', 'html': 'html', 'ex': 'elixir', 'exs': 'elixir',
        }
       
        language = language_map.get(file_extension, 'text')
        self.set_language(language)
        if language == 'markdown':
            self.markdown_viewer.load_markdown(file_path)
            self.markdown_viewer.show()
        else:
            self.markdown_viewer.hide()
   
    
    def on_file_path_changed(self, file_path):
        self.file_path = file_path
        self.set_language_from_file_path(file_path)
      
    def on_fileset_changed(self, file_path):
        self.file_path = file_path
        self.set_language_from_file_path(file_path)

    def on_text_changed(self):
        # Handle text changes, e.g., update file outline, markdown preview, etc.
        #TODO: add undo/redo functionality
        #TODO: suggestions
        #TODO: auto-import
        #TODO: auto-format
        #TODO: auto-lint
        #TODO: personal dictionary lookup
        pass
    def isModified(self):
        return self.text_edit.isModified()
    def set_file_path(self, path):
        self.file_path = path
        logging.info(f"File path set to: {path}")
   
    def show_context_menu(self, point):
        logging.warning("Showing context menu- not fully implemented")
        self.context_menu.popup(self.mapToGlobal(point))

    def show_search_dialog(self):
        search_dialog = Search(self)
        search_dialog.exec()

    def calculate(self):
        ModulesFile.calculate(self)

    def encode(self):
        ModulesFile.encrypt(self)

    def decode(self):
        ModulesFile.decode(self)

    def markdown_to_html(self, md_text):
        def image_handler(match):
            image_name = match.group(1)
            if image_name in self.image_map:
                return f'<img src="{self.image_map[image_name]}">'
            return match.group(0)
        md_text = re.sub(r'!\[\[(.*?)\]\]', image_handler, md_text)
        html = markdown.markdown(md_text)
        return html

    def insert_image_link(self):
        if not self.vault_path:
            return
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif)")
        file_dialog.setDirectory(self.vault_path)
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                image_path = selected_files[0]
                image_name = os.path.basename(image_path)
                self.text_edit.insert(f"![[{image_name}]]")
                if image_name not in self.image_map:
                    self.image_map[image_name] = image_path

    
    def setModified(self, modified):
        self.text_edit.setModified(modified)
    # Proxy methods to maintain compatibility with QsciScintilla
    def text(self):
        return self.text_edit.text()

    def setText(self, text):
        self.text_edit.setText(text)

    def setPlainText(self, text):
        self.text_edit.setText(text)

    def toPlainText(self):
        return self.text_edit.text()

    def insertPlainText(self, text):
        self.text_edit.insert(text)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Tab and self.import_completer.popup().isVisible():
            self.import_completer.setCurrentIndex(self.import_completer.currentIndex())
            self.import_completer.popup().setCurrentIndex(self.import_completer.completionModel().index(0,0))
            return

        # Handle multi-cursor editing
        if self.cursor_manager and len(self.cursor_manager.cursors) > 1:
            if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete, Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.cursor_manager.apply_edit_to_all_cursors(lambda c: self.apply_edit(c, event))
                event.accept()
                return

        super().keyPressEvent(event)

        if event.text() and self.text_edit.textCursor().positionInBlock() == len(event.text()):
            rect = self.text_edit.cursorRect()    
            rect.setWidth(self.import_completer.popup().sizeHintForColumn(0) + 
                          self.import_completer.popup().verticalScrollBar().sizeHint().width())
            self.import_completer.complete(rect)

        # Handle special key combinations first
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Space:
                self.show_radial_menu()
                return
            # Add more Ctrl+ combinations here
            if event.key() == Qt.Key.Key_I:
                self.insert_import()
                return
            if event.key() == Qt.Key.Key_O:
                self.show_radial_menu()
                return
            if event.key() == Qt.Key.Key_Q:
                self.show_q_menu()
                return
        # Let the QsciScintilla handle the event
        self.text_edit.keyPressEvent(event)

        # After the event is handled, update the LSP
        if hasattr(self.mm, 'lsp_manager'):
            # Only send updates for key events that modify the text
            if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete, Qt.Key.Key_Return, Qt.Key.Key_Enter) or event.text():
                self.mm.lsp_manager.send_request("textDocument/didChange", {
                    "textDocument": {"uri": f"file://{self.file_path}"},
                    "contentChanges": [{"text": self.text_edit.text()}]
                })

                # Request completions only if it's a character input
                if event.text().isalnum() or event.text() in "._":
                    line, index = self.text_edit.getCursorPosition()
                    self.mm.lsp_manager.request_completions(self.file_path, line, index)

        # Update the file outline
        self.update_file_outline()

        # If it's a markdown file, update the preview
        if self.current_language == 'markdown':
            self.update_markdown_preview()

    def handle_completions(self, completions):
        # Existing LSP completions handling
        # ...

        # Add import suggestions
        if hasattr(self.mm, 'lsp_manager') and self.mm.lsp_manager is not None:
            import_suggestions = self.mm.lsp_manager.get_import_suggestions(self.text_edit.text())
            all_completions = completions + [{"label": s, "kind": 9} for s in import_suggestions]

            # Update the completer with all completions
            self.completer.setModel(QStringListModel([c["label"] for c in all_completions]))
            self.completer.complete()
        else:
            logging.warning("LSP manager not available, import suggestions not added")

    def on_vault_switch(self, new_vault_path):
        self.vault_path = new_vault_path
        if self.markdown_viewer:
            self.markdown_viewer.set_vault_path(new_vault_path)
                # Update any other necessary state
    def set_file_path(self, path):
        self.file_path = path
        # You might want to update the UI or perform other actions here
        logging.info(f"File path set to: {path}")

    def _handle_text_changed(self):
        self._is_modified = True

    
    
   
    def show_radial_menu(self):
        cursor_pos = self.text_edit.cursorRect().center()
        global_pos = self.mapToGlobal(cursor_pos)
        self.parent().file_manager.show_radial_menu(global_pos)
    def isModified(self):
        return self._is_modified

    
    def setup_block_selection(self):
        # Connect mouse double click event to block selection method
        self.text_edit.mouseDoubleClickEvent = self.on_mouse_double_click

        # Define significant keywords for different languages
        self.significant_keywords = {
            'python': r'\b(def|class|if|for|while|try|with)\b',
            'javascript': r'\b(function|class|if|for|while|try|switch)\b',
            'java': r'\b(class|interface|enum|if|for|while|try|switch)\b',
            'cpp': r'\b(class|struct|enum|if|for|while|try|switch)\b',
            'elixir': r'\b(def|defp|defmodule|if|case|cond|for|with)\b',
        }
    def on_mouse_double_click(self, event):
        # Call the original mouse double click event
        QsciScintilla.mouseDoubleClickEvent(self.text_edit, event)

        # Check if it's a left double click
        if event.button() == Qt.MouseButton.LeftButton:
            # Get the position of the click
            pos = self.text_edit.SendScintilla(QsciScintilla.SCI_POSITIONFROMPOINT, event.x(), event.y())
            line, index = self.text_edit.lineIndexFromPosition(pos)

            # Check if the click is on a significant keyword
            if self.is_significant_line(line):
                self.highlight_code_block(line)

    def is_significant_line(self, line):
        import re
        text = self.text_edit.text(line)
        pattern = self.significant_keywords.get(self.current_language, r'')
        return re.match(pattern, text.strip()) is not None
           
    def toggle_highlight(self):
        self.highlight_enabled = not self.highlight_enabled
        if self.highlight_enabled:
            self.text_edit.SendScintilla(QsciScintilla.SCI_SETCARETLINEVISIBLE, True)
        else:
            self.text_edit.SendScintilla(QsciScintilla.SCI_SETCARETLINEVISIBLE, False)
        self.text_edit.update()
        logging.warning(f"Highlight toggled: {'enabled' if self.highlight_enabled else 'disabled'}")
    def highlight_code_block(self, start_line):
        # Clear previous block highlight
        self.text_edit.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 2)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICATORCLEARRANGE, 0, self.text_edit.length())

        # Set up the indicator style for block highlighting
        self.text_edit.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 2)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, 2, QsciScintilla.INDIC_ROUNDBOX)
        
        # Use the theme color instead of hard-coded yellow
        highlight_color = self.mm.theme_manager.get_current_theme_color("currentLineColor", QColor(230, 230, 230))
        highlight_color.setAlpha(40)
        
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETFORE, 2, highlight_color.rgb() & 0xFFFFFF)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETALPHA, 2, highlight_color.alpha())

        # Find the end of the block
        start_indent = self.text_edit.indentation(start_line)
        end_line = start_line
        total_lines = self.text_edit.lines()
        
        if self.current_language in ['python', 'elixir']:
            # For Python and Elixir, use indentation to determine block end
            while end_line < total_lines - 1:
                end_line += 1
                if self.text_edit.indentation(end_line) <= start_indent and self.text_edit.text(end_line).strip():
                    break
        else:
            # For other languages, use brace matching
            brace_count = 0
            for i in range(start_line, total_lines):
                line_text = self.text_edit.text(i)
                brace_count += line_text.count('{') - line_text.count('}')
                if brace_count == 0 and i > start_line:
                    end_line = i
                    break

        # Apply the highlighting
        start_pos = self.text_edit.positionFromLineIndex(start_line, 0)
        end_pos = self.text_edit.positionFromLineIndex(end_line + 1, 0)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, start_pos, end_pos - start_pos)
     
    def cycle_debug_color(self):
        self.current_debug_color = (self.current_debug_color + 1) % len(self.debug_colors)
        color = self.debug_colors[self.current_debug_color]
        self.text_edit.set_forced_line_color(color, 128)
        logging.warning(f"Debug color set to: {color}")
    def apply_theme(self, theme_data):
        logging.debug(f"Applying theme data: {theme_data}")
        # Apply general colors
        current_line_color = colors.get("currentLineColor", "#E8F2FF")
        current_line_alpha = colors.get("currentLineAlpha", 40)
        
        logging.warning(f"Applying theme - Current line color: {current_line_color}, Alpha: {current_line_alpha}")
        self.text_edit.set_forced_line_color(current_line_color, current_line_alpha)
        
        colors = theme_data.get("colors", {})
        self.text_edit.setPaper(QColor(colors.get("backgroundColor", "#151515")))
        self.text_edit.setColor(QColor(colors.get("textColor", "#000000")))

        # Apply sidebar colors
        sidebar_colors = theme_data.get("sidebar", {})
        sidebar_bg = sidebar_colors.get("sidebarBackground", "#F0F0F0")
        sidebar_text = sidebar_colors.get("sidebarText", "#000000")
        sidebar_highlight = sidebar_colors.get("sidebarHighlight", "#C0C0C0")

        # Apply to line number area
        self.text_edit.setMarginsForegroundColor(QColor(sidebar_text))
        self.text_edit.setMarginsBackgroundColor(QColor(sidebar_bg))

        # Apply to folding area if available
        if hasattr(self.text_edit, "setFoldMarginColors"):
            self.text_edit.setFoldMarginColors(QColor(sidebar_bg), QColor(sidebar_highlight))

        # Apply current line highlight
        current_line_color = QColor(colors.get("currentLineColor", "#E8F2FF"))
        current_line_color.setAlpha(40)  # Set transparency
        logging.warning(f"Attempting to set current line color: {current_line_color.name()}, Alpha: {current_line_color.alpha()}")
        
        # Directly set the current line color using Scintilla message
        self.text_edit.SendScintilla(QsciScintilla.SCI_SETCARETLINEBACK, current_line_color.rgb())
        self.text_edit.SendScintilla(QsciScintilla.SCI_SETCARETLINEBACKALPHA, current_line_color.alpha())
        
        # Enable the caret line visibility
        self.text_edit.SendScintilla(QsciScintilla.SCI_SETCARETLINEVISIBLE, True)
        
        # Force a redraw
        self.text_edit.update()
        
        # Check the color after setting
        actual_color = self.text_edit.SendScintilla(QsciScintilla.SCI_GETCARETLINEBACK)
        actual_alpha = self.text_edit.SendScintilla(QsciScintilla.SCI_GETCARETLINEBACKALPHA)
        logging.warning(f"Actual current line color set: #{actual_color:06x}, Alpha: {actual_alpha}")

        # Remove any existing highlight_current_line connections
        try:
            self.text_edit.cursorPositionChanged.disconnect(self.highlight_current_line)
        except TypeError:
            pass  # Connection didn't exist

        # Connect to cursorPositionChanged to update the highlight
        self.text_edit.cursorPositionChanged.connect(self.update_current_line_highlight)

        # Apply selection color
        selection_color = QColor(colors.get("selectionColor", "#ADD6FF"))
        self.text_edit.setSelectionBackgroundColor(selection_color)

        # Apply caret (cursor) color
        caret_color = QColor(colors.get("caretColor", "#000000"))
        self.text_edit.setCaretForegroundColor(caret_color)

        # Apply indentation guides color
        indent_guide_color = QColor(colors.get("indentGuideColor", "#E0E0E0"))
        self.text_edit.setIndentationGuidesBackgroundColor(indent_guide_color)
        self.text_edit.setIndentationGuidesForegroundColor(indent_guide_color)

        # Apply bracket matching color
        brace_match_color = QColor(colors.get("braceMatchingColor", "#B4EEB4"))
        self.text_edit.setMatchedBraceBackgroundColor(brace_match_color)
        self.text_edit.setMatchedBraceForegroundColor(QColor(colors.get("textColor", "#000000")))

        # Apply edge (long line indicator) color
        edge_color = QColor(colors.get("edgeColor", "#FF0000"))
        self.text_edit.setEdgeColor(edge_color)

        # Set edge mode and column
        self.text_edit.setEdgeMode(QsciScintilla.EdgeMode.EdgeLine)
        self.text_edit.setEdgeColumn(80)  # You can make this configurable

        # Apply fold margin colors
        fold_margin_color = QColor(colors.get("foldMarginColor", "#D0D0D0"))
        self.text_edit.setFoldMarginColors(fold_margin_color, fold_margin_color)

        # Apply whitespace visibility
        if colors.get("showWhitespace", False):
            self.text_edit.setWhitespaceVisibility(QsciScintilla.WhitespaceVisibility.WsVisible)
        else:
            self.text_edit.setWhitespaceVisibility(QsciScintilla.WhitespaceVisibility.WsInvisible)

        # Apply end-of-line visibility
        if colors.get("showEOL", False):
            self.text_edit.setEolVisibility(True)
        else:
            self.text_edit.setEolVisibility(False)

        # Apply lexer colors (syntax highlighting)
        if self.lexer:
            lexer_colors = theme_data.get("lexer", {})
            for style, color in lexer_colors.items():
                self.lexer.setColor(QColor(color), style)

        # Apply toolbar and context menu colors
        toolbar_color = QColor(theme_data.get("toolbar", {}).get("toolbarColor", "#f0f0f0"))
        toolbar_separator_color = QColor(theme_data.get("toolbar", {}).get("toolbarSeparatorColor", "#c0c0c0"))
        menu_color = QColor(theme_data.get("toolbar", {}).get("menuColor", "#f0f0f0"))
        menu_text_color = QColor(theme_data.get("toolbar", {}).get("menuTextColor", "#000000"))
        menu_border_color = QColor(theme_data.get("toolbar", {}).get("menuBorderColor", "#c0c0c0"))
        menu_hover_color = QColor(theme_data.get("toolbar", {}).get("menuHoverColor", "#c0c0c0"))

        # Ensure the changes are applied
        self.text_edit.update()

    def update_current_line_highlight(self):
        # current_line_color = self.text_edit.caretLineBackgroundColor()
        # logging.warning(f"Updating current line highlight: {current_line_color.name()}")
        # self.text_edit.setCaretLineBackgroundColor(current_line_color)
        self.check_current_line_color()
        # No need to set the color here, as it should persist
    def check_current_line_color(self):
        color = self.text_edit.SendScintilla(QsciScintilla.SCI_GETCARETLINEBACK)
        alpha = self.text_edit.SendScintilla(QsciScintilla.SCI_GETCARETLINEBACKALPHA)
        is_visible = self.text_edit.SendScintilla(QsciScintilla.SCI_GETCARETLINEVISIBLE)
        logging.warning(f"Check - Current line color: #{color:06x}, Alpha: {alpha}, Visible: {is_visible}")
    def load_typing_effect_settings(self):
        self.typing_effect_enabled = self.settings_manager.get_typing_effect_enabled()
        self.typing_effect_speed = self.settings_manager.get_typing_effect_speed()
        self.typing_effect_particle_count = self.settings_manager.get_typing_effect_particle_count()

    def type_with_effect(self, text):
        for char in text:
            QTimer.singleShot(random.randint(50, self.typing_effect_speed), lambda c=char: self.insert_character(c))

    def insert_character(self, char):
        cursor = self.text_edit.textCursor()
        cursor.insertText(char)
        self.text_edit.setTextCursor(cursor)

    def setup_fileset_selector(self):
        if self.fileset_selector is not None:
            self.fileset_selector.currentTextChanged.connect(self.on_fileset_changed)
            logging.debug("FileSet selector initialized and connected")
        else:
            logging.warning("FileSet selector is None, unable to set up")
            
    def show_current_lexer(self):
        if hasattr(self, 'lexer_label'):
            self.lexer_label.setText(f"Current Lexer: {self.current_language}")
        else:
            self.lexer_label = QLabel(f"Current Lexer: {self.current_language}", self)
            self.layout().addWidget(self.lexer_label)
    def check_current_line_color(self):
        color = self.text_edit.SendScintilla(QsciScintilla.SCI_GETCARETLINEBACK)
        alpha = self.text_edit.SendScintilla(QsciScintilla.SCI_GETCARETLINEBACKALPHA)
        logging.warning(f"Current line color: #{color:06x}, Alpha: {alpha}")     

    def setup_lsp_connections(self):
        if hasattr(self.mm, 'lsp_manager'):
            if self.mm.lsp_manager is not None:
                self.connect_lsp_manager()
            else:
                # If LSP manager is not initialized yet, connect to the initialization signal
                if hasattr(self.mm, 'lsp_manager_initialized') and isinstance(self.mm.lsp_manager_initialized, pyqtSignal):
                    self.mm.lsp_manager_initialized.connect(self.connect_lsp_manager)
                else:
                    logging.warning("LSP manager initialized signal not available or not a pyqtSignal")
        else:
            logging.warning("LSP manager not available in CCCore, some features may be limited")

    def connect_lsp_manager(self):
        if self.mm.lsp_manager is not None:
            self.mm.lsp_manager.completionsReceived.connect(self.handle_completions)
            self.mm.lsp_manager.importsIndexed.connect(self.update_import_completer)
            logging.info("LSP manager connections established")
        else:
            logging.warning("LSP manager is None, unable to establish connections")

    def setup_auto_import_completion(self):
        self.import_completer.setWidget(self.text_edit)
        self.import_completer.activated.connect(self.insert_import)
       

    def update_import_completer(self, import_index):
        self.import_completer.setModel(QStringListModel(list(import_index.values())))

    def insert_import(self, import_stmt):
        cursor = self.text_edit.textCursor()
        cursor.movePosition(cursor.Start)
        cursor.insertText(import_stmt + "\n")

    def show_q_menu(self):
        logging.warning("Showing Q menu")
        menu = QMenu(self)
        menu.setBackgroundColor(QColor(self.mm.theme_manager.get_current_theme_color("backgroundColor", QColor(222, 211, 111))))
        # Add actions to the menu
        actions = [
            ("Format Code", self.format_code, "Ctrl+Shift+F"),
            ("Toggle Comment", self.toggle_comment, "Ctrl+/"),
            ("Find/Replace", self.show_search_dialog, "Ctrl+F"),
            ("Go to Definition", self.goto_definition, "F12"),
            ("Show References", self.show_references, "Shift+F12"),
            ("Rename Symbol", self.rename_symbol, "F2"),
            ("Toggle Breakpoint", self.toggle_breakpoint, "F9"),
            ("Insert Image Link", self.insert_image_link, "Ctrl+Shift+I"),
            ("Toggle Markdown Preview", self.toggle_markdown_preview, "Ctrl+Shift+M"),
            ("Cycle Debug Color", self.cycle_debug_color, "Ctrl+Shift+C"),
        ]

        for text, slot, shortcut in actions:
            action = QAction(text, self)
            action.triggered.connect(slot)
            action.setShortcut(shortcut)
            menu.addAction(action)

        # Add a separator
        menu.addSeparator()

        # Add language selection submenu
        language_menu = menu.addMenu("Set Language")
        languages = ["Python", "JavaScript", "HTML", "CSS", "Markdown", "C++", "Java"]
        for lang in languages:
            action = QAction(lang, self)
            action.triggered.connect(lambda checked, l=lang: self.set_language(l.lower()))
            language_menu.addAction(action)

        # Show the menu at the cursor position
        cursor = self.text_edit.textCursor()
        rect = self.text_edit.cursorRect(cursor)
        pos = self.text_edit.mapToGlobal(rect.bottomRight())
        menu.exec(pos)

    def format_code(self):
        # Implement code formatting logic here
        pass

    def toggle_comment(self):
        # Implement comment toggling logic here
        pass

    def goto_definition(self):
        # Implement go to definition logic here
        pass
    def goto_line(self,line):
        self.text_edit.scroll(line,0)
    def show_references(self):
        # Implement show references logic here
        pass

    def rename_symbol(self):
        # Implement rename symbol logic here
        pass

    def toggle_breakpoint(self):
        # Implement breakpoint toggling logic here
        pass

    def insert_completion(self, completion):
        if self.cursor_manager:
            active_cursor = self.cursor_manager.get_active_cursor()
            if active_cursor:
                # Use CursorManager to move the cursor
                self.cursor_manager.move_cursor_left(len(self.completer.completionPrefix()), keep_anchor=True)
                
                # Insert the completion
                self.cursor_manager.insert_text(completion)
            else:
                # If no active cursor, fall back to default behavior
                cursor = self.text_edit.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, len(self.completer.completionPrefix()))
                cursor.insertText(completion)
                self.text_edit.setTextCursor(cursor)
                logging.warning("No active cursor, using default behavior")
                self.cursor_manager.synchronize_cursors()
        else:
            # If no cursor manager, use default behavior
            logging.warning("No cursor manager, using default behavior")
            cursor = self.text_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, len(self.completer.completionPrefix()))
            cursor.insertText(completion)
            self.text_edit.setTextCursor(cursor)

        # No need to explicitly synchronize cursors, as CursorManager methods should handle this

    def apply_edit(self, cursor, event):
        if event.key() == Qt.Key.Key_Backspace:
            cursor.deletePreviousChar()
        elif event.key() == Qt.Key.Key_Delete:
            cursor.deleteChar()
        elif event.text():
            cursor.insertText(event.text())
    def connect_lsp_manager(self):
        if hasattr(self.mm, 'lsp_manager') and self.mm.lsp_manager is not None:
            self.mm.lsp_manager.completionsReceived.connect(self.handle_completions)
            self.mm.lsp_manager.importsIndexed.connect(self.update_import_completer)
        else:
            logging.warning("LSP manager not available after initialization, some features may be limited.")
    def get_current_line_text(self):
        line, _ = self.text_edit.getCursorPosition()
        return self.text_edit.text(line)

    def get_all_text(self):
        return self.text_edit.text()

    def set_text(self, text):
        self.text_edit.setText(text)

    def insert_text(self, text):
        self.text_edit.insert(text)

    def get_selection(self):
        return self.text_edit.selectedText()

    def get_paragraph(self, line_number):
        start_line = line_number
        end_line = line_number
        
        # Find start of paragraph
        while start_line > 0 and self.text_edit.text(start_line - 1).strip():
            start_line -= 1
        
        # Find end of paragraph
        while end_line < self.text_edit.lines() - 1 and self.text_edit.text(end_line + 1).strip():
            end_line += 1
        
        # Combine lines into a paragraph
        paragraph = '\n'.join(self.text_edit.text(i) for i in range(start_line, end_line + 1))
        return paragraph

    def highlight_paragraph(self, line_number):
        start_line = line_number
        end_line = line_number
        
        # Find start and end of paragraph
        while start_line > 0 and self.text_edit.text(start_line - 1).strip():
            start_line -= 1
        while end_line < self.text_edit.lines() - 1 and self.text_edit.text(end_line + 1).strip():
            end_line += 1
        
        # Highlight the paragraph
        self.text_edit.setSelection(start_line, 0, end_line, len(self.text_edit.text(end_line)))