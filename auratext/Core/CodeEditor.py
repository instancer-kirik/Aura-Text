
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QColor
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QTextEdit, QPlainTextEdit
from PyQt6.QtGui import QPainter, QTextFormat
from PyQt6.QtCore import QSize
import os
import re
import markdown
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QFileDialog, QTextBrowser
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from PyQt6.QtCore import QTimer
from .file_outline_widget import FileOutlineWidget
from .search_and_line_number import Search
from .Modules import ModulesFile
from PyQt6.Qsci import QsciAPIs
from PyQt6.QtCore import QRect
from PyQt6.QtGui import QKeySequence
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QComboBox, QLabel

class CodeEditor(QsciScintilla):
    def __init__(self, mm, parent=None):
        
        logging.info("Starting CodeEditor initialization")
        
        try:
            logging.debug("Calling QsciScintilla.__init__")
            super().__init__(parent)
            logging.debug("QsciScintilla.__init__ completed")
            
            self.mm = mm
            self.current_language = None
            self.image_map = {}
            self.vault_path = None
            self.markdown_preview = QTextBrowser(parent)
            self.markdown_preview.hide()
            self.update_timer = QTimer(self)
            self.update_timer.timeout.connect(self.update_markdown_preview)
            self.update_timer.setInterval(1000)
            
            self.mm.lsp_manager.completionsReceived.connect(self.handle_completions)
       
            # Set up QScintilla features
            self.setUtf8(True)
            self.setIndentationsUseTabs(False)
            self.setTabWidth(4)
            self.setIndentationGuides(True)
            self.setAutoIndent(True)
            self.setCaretLineVisible(True)
            # Enable line numbers
            logging.debug("Enabling line numbers")
            self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
            self.setMarginWidth(0, "0000")
            self.setMarginsForegroundColor(QColor("#ff888888"))
            
            # Set up margins
            self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
            self.setMarginWidth(0, "0000")
            self.setMarginsForegroundColor(QColor("#ff888888"))

            # Create fileset selection dropdown
            self.fileset_selector = QComboBox(self)
            self.fileset_selector.currentTextChanged.connect(self.on_fileset_changed)

            # Create a widget to hold the dropdown and the editor
            self.main_widget = QWidget(self)
            main_layout = QVBoxLayout(self.main_widget)

            # Create a horizontal layout for the dropdown
            dropdown_layout = QHBoxLayout()
            dropdown_layout.addWidget(QLabel("Fileset:"))
            dropdown_layout.addWidget(self.fileset_selector)
            dropdown_layout.addStretch()

            # Add the dropdown layout and the editor to the main layout
            main_layout.addLayout(dropdown_layout)
            main_layout.addWidget(self)

            # Set the main widget as the central widget of the CodeEditor
            self.setCentralWidget(self.main_widget)

            # Populate the fileset dropdown
            self.populate_fileset_dropdown()

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
            self.mm.theme_manager.apply_theme_to_editor(self)
            
            logging.info("CodeEditor initialized successfully")
        except Exception as e:
            logging.exception(f"Error initializing CodeEditor: {e}")
            raise

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

    def index_vault_images(self, vault_index):
        self.image_map = {}
        for rel_path, info in vault_index.items():
            if info['type'] == 'image':
                self.image_map[os.path.basename(rel_path)] = os.path.join(self.vault_path, rel_path)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        # Interact with the language server
        self.mm.lsp_manager.send_request("textDocument/didChange", {"text": self.text()})
        self.mm.lsp_manager.request_completions(self.file_path, self.cursorPosition())

    
    def handle_completions(self, completions):
        # Use completions to update the editor (e.g., show autocomplete popup)
        pass
    def load_file(self, file_path):
        with open(file_path, 'r') as f:
            self.setText(f.read())
        self.language_server.open_document(file_path)
        
        file_extension = file_path.split('.')[-1].lower()
        language_map = {
            'py': 'python',
            'md': 'markdown',
            'cpp': 'cpp',
            'js': 'javascript',
            'html': 'html',
            # Add more mappings as needed
        }
        language = language_map.get(file_extension, 'python')  # Default to Python if unknown
        self.set_language(language)

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
        # Use the lexer manager from mm
        self.mm.lexer_manager.apply_lexer("python", self)

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
        ModulesFile.calculate(self)

    def encode(self):
        ModulesFile.encrypt(self)

    def decode(self):
        ModulesFile.decode(self)

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

    def update_markdown_preview(self):
        md_text = self.text()
        html = self.markdown_to_html(md_text)
        self.markdown_preview.setHtml(html)

    def markdown_to_html(self, md_text):
        def image_handler(match):
            image_name = match.group(1)
            if image_name in self.image_map:
                return f'<img src="{self.image_map[image_name]}">'
            return match.group(0)  # Return original text if image not found

        # Replace wikilinks style image tags
        md_text = re.sub(r'!\[\[(.*?)\]\]', image_handler, md_text)
        
        # Convert to HTML
        html = markdown.markdown(md_text)
        return html

    def loadResource(self, type, name):
        if type == QTextDocument.ResourceType.ImageResource:
            image = QImage(name)
            if not image.isNull():
                return image
        return super().loadResource(type, name)

    def insert_image_link(self):
        if not self.vault_path:
            return  # Handle this case appropriately (e.g., show an error message)

        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif)")
        file_dialog.setDirectory(self.vault_path)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                image_path = selected_files[0]
                image_name = os.path.basename(image_path)
                self.insert(f"![[{image_name}]]")
                
                # Add to image map if not already present
                if image_name not in self.image_map:
                    self.image_map[image_name] = image_path

    def setup_shortcuts(self):
        radial_menu_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        radial_menu_shortcut.activated.connect(self.show_radial_menu)

    def show_radial_menu(self):
        cursor_pos = self.cursorRect().center()
        global_pos = self.mapToGlobal(cursor_pos)
        self.parent().file_manager.show_radial_menu(global_pos)

    def populate_fileset_dropdown(self):
        # Get all filesets from the fileset manager
        filesets = self.mm.fileset_manager.get_all_filesets()
        self.fileset_selector.addItem("Select Fileset")  # Default option
        self.fileset_selector.addItems(filesets)

    def on_fileset_changed(self, fileset_name):
        if fileset_name != "Select Fileset":
            # Get the files in the selected fileset
            files = self.mm.fileset_manager.get_fileset(fileset_name)
            # Open the files in the editor (you may want to implement this in a separate method)
            self.open_files_in_fileset(files)

    def open_files_in_fileset(self, files):
        # Implement the logic to open the files in the editor
        # This might involve creating new tabs or updating existing ones
        pass
    def update_fileset_dropdown(self):
        self.fileset_selector.clear()
        self.fileset_selector.addItem("Select Fileset")
        filesets = self.mm.fileset_manager.get_all_filesets()
        self.fileset_selector.addItems(filesets)
    def initialize_filesets(self):
        logging.info("Starting initialize_filesets")
        try:
            filesets = self.mm.fileset_manager.get_all_filesets()
            logging.info(f"Retrieved {len(filesets)} filesets")
            for fileset in filesets:
                logging.info(f"Adding fileset tab: {fileset}")
                self.add_fileset_tab(fileset)
        except Exception as e:
            logging.error(f"Error in initialize_filesets: {str(e)}")
        logging.info("initialize_filesets complete")