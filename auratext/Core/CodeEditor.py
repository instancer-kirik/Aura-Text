from PyQt6.Qsci import QsciScintilla, QsciAPIs
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QTextBrowser, QComboBox, QLabel
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QImage, QKeySequence, QShortcut, QKeyEvent
from PyQt6.QtCore import Qt, QTimer, QRect, QSize
import logging
import os
import re
import time
import markdown
from GUX.markdown_viewer import MarkdownViewer
from .file_outline_widget import FileOutlineWidget
from .search_and_line_number import Search
from .Modules import ModulesFile

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

        self.text_edit = QsciScintilla(self)
        self.file_outline_widget = FileOutlineWidget(self)
        self.markdown_preview = QTextBrowser(self)
        self.fileset_selector = QComboBox(self)

        self._is_modified = False
        self.text_edit.textChanged.connect(self._handle_text_changed)

        self.setup_ui()
        self.setup_editor()
        self.setup_connections()
        self.setup_shortcuts()

        logging.info("CodeEditor initialization complete")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.text_edit = QsciScintilla(self)
        layout.addWidget(self.text_edit)

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
        self.text_edit.cursorPositionChanged.connect(self.highlight_current_line)
        self.text_edit.textChanged.connect(self.update_file_outline)
        self.text_edit.textChanged.connect(self.on_text_changed)   
        self.fileset_selector.currentTextChanged.connect(self.on_fileset_changed)
       
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_markdown_preview)
        self.update_timer.setInterval(1000)

        if hasattr(self.mm, 'lsp_manager'):
            self.mm.lsp_manager.completionsReceived.connect(self.handle_completions)

    def setup_shortcuts(self):
        radial_menu_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        radial_menu_shortcut.activated.connect(self.show_radial_menu)

    def update_file_outline(self):
        text = self.text_edit.text()
        self.file_outline_widget.populate_file_outline(text)

    def highlight_current_line(self):
        self.text_edit.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 0)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICATORCLEARRANGE, 0, self.text_edit.length())
        line, _ = self.text_edit.getCursorPosition()
        self.text_edit.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 0)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETSTYLE, 0, QsciScintilla.INDIC_STRAIGHTBOX)
        highlight_color = QColor(Qt.GlobalColor.yellow)
        highlight_color.setAlpha(40)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETFORE, 0, highlight_color.rgb() & 0xFFFFFF)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICSETALPHA, 0, highlight_color.alpha())
        line_start = self.text_edit.positionFromLineIndex(line, 0)
        line_end = self.text_edit.positionFromLineIndex(line + 1, 0)
        self.text_edit.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, line_start, line_end - line_start)

    def update_markdown_preview(self):
        if self.current_language == 'markdown':
            md_text = self.text_edit.text()
            self.markdown_viewer.setHtml(self.markdown_to_html(md_text))

    def set_language(self, language):
        if self.current_language != language:
            self.current_language = language
            self.mm.lexer_manager.apply_lexer(language, self)
            self.toggle_markdown_preview(language == 'markdown')

    def toggle_markdown_preview(self, show):
        if show:
            self.markdown_preview.show()
            self.update_timer.start()
        else:
            self.markdown_preview.hide()
            self.update_timer.stop()

    def load_file(self, file_path):
        with open(file_path, 'r') as f:
            self.text_edit.setText(f.read())
        self.file_path = file_path
        self.set_language_from_file_path(file_path)

    def set_language_from_file_path(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()
        language_map = {
            '.py': 'python', '.md': 'markdown', '.cpp': 'cpp',
            '.js': 'javascript', '.html': 'html',
        }
        language = language_map.get(file_extension, 'text')
        self.set_language(language)
        if language == 'markdown':
            self.markdown_viewer.load_markdown(file_path)
            self.markdown_viewer.show()
        else:
            self.markdown_viewer.hide()
    def update_fileset_dropdown(self):
        self.fileset_selector.clear()
        self.fileset_selector.addItem("Select Fileset")
        filesets = self.mm.vault_manager.get_all_filesets()
        self.fileset_selector.addItems(filesets)
    def set_language(self, language):
        if self.current_language != language:
            self.current_language = language
            self.mm.lexer_manager.apply_lexer(language, self.text_edit)

    def on_fileset_changed(self, fileset_name):
        if fileset_name != "Select Fileset":
            files = self.mm.vault_manager.get_fileset(fileset_name)
            self.open_files_in_fileset(files)
    def on_text_changed(self):
        # Handle text changes, e.g., update file outline, markdown preview, etc.
        pass
    def open_files_in_fileset(self, files):
        for file in files:
            file_path = os.path.join(self.vault_path, file)
            self.load_file(file_path)
    def isModified(self):
        return self.text_edit.isModified()
    def set_file_path(self, path):
        self.file_path = path
        logging.info(f"File path set to: {path}")
    def open_files_in_fileset(self, fileset_name):
        files = self.mm.vault_manager.get_fileset(fileset_name)
        if not files:
            logging.warning(f"No files in the fileset: {fileset_name}")
            return

        for file_path in files:
            full_path = os.path.join(self.mm.vault_manager.vault_path, file_path)
            if not os.path.exists(full_path):
                logging.warning(f"File not found: {full_path}")
                continue

            existing_editor = self.find_editor_by_file_path(full_path)
            if existing_editor:
                self.mm.editor_manager.set_current_editor(existing_editor)
            else:
                new_editor = self.mm.editor_manager.new_document()
                new_editor.load_file(full_path)
                self.mm.editor_manager.set_current_editor(new_editor)

        logging.info(f"Opened {len(files)} files from fileset {fileset_name}.")

    def find_editor_by_file_path(self, file_path):
        for editor in self.mm.editor_manager.editors:
            if editor.file_path == file_path:
                return editor
        return None

    def show_context_menu(self, point):
        logging.info("Showing context menu- not fully implemented")
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

    def show_radial_menu(self):
        cursor_pos = self.text_edit.cursorRect().center()
        global_pos = self.mapToGlobal(cursor_pos)
        self.parent().file_manager.show_radial_menu(global_pos)
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
        # Handle special key combinations first
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Space:
                self.show_radial_menu()
                return
            # Add more Ctrl+ combinations here if needed

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
        # Implement this method to handle completions
        pass

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

    
    def update_file_outline(self):
        # Implement this method to update the file outline
        pass
    def update_markdown_preview(self):
        # Implement this method to update the markdown preview
        pass
    def show_radial_menu(self):
        cursor_pos = self.text_edit.cursorRect().center()
        global_pos = self.mapToGlobal(cursor_pos)
        self.parent().file_manager.show_radial_menu(global_pos)
    def isModified(self):
        return self._is_modified

    def setModified(self, modified):
        self._is_modified = modified