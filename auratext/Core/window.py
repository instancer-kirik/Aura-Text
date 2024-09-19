import datetime
import importlib
import json
import os
import random
import sys
import logging
import traceback
import time
import webbrowser
from tkinter import filedialog
import git
import pyjokes
from pyqtconsole.console import PythonConsole
from PyQt6.QtCore import Qt, QSize, QTimer, QObject
from PyQt6.QtGui import QColor, QFont, QActionGroup, QFileSystemModel, QPixmap, QIcon
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtWidgets import (
    QMainWindow,
    QInputDialog,
    QDockWidget,
    QTextEdit,
    QTreeView,
    QFileDialog,
    QSplashScreen,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QStatusBar,
    QLabel)
# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from auratext.Misc import shortcuts, WelcomeScreen, boilerplates, file_templates
from . import MenuConfig
from . import additional_prefs
from . import Modules as ModuleFile
from . import PluginDownload
from . import ThemeDownload
from . import config_page
from ..Components import powershell, terminal, statusBar, GitCommit, GitPush
from .AuraText import CodeEditor
from auratext.Components.TabWidget import TabWidget
from .plugin_interface import Plugin
from .theme_manager import ThemeDownloader
from .theme_manager import ThemeManager
from .Lexers import LexerManager
from HMC.download_manager import DownloadManager
from GUX.ai_chat import AIChatWidget
from PyQt6.QtWidgets import QTabWidget
from GUX.diff_merger import DiffMergerWidget
from PyQt6.QtWidgets import  QMenu, QLineEdit, QCheckBox, QHBoxLayout, QPushButton, QDialog
from PyQt6.Qsci import QsciAPIs
from . import Lexers
from PyQt6.QtGui import QKeySequence, QAction
from PyQt6.QtWidgets import QMenuBar, QToolBar
from PyQt6.QtCore import QDir
local_app_data = os.path.join(os.getenv("LocalAppData"), "AuraText")
cpath = open(f"{local_app_data}/data/CPath_Project.txt", "r+").read()
cfile = open(f"{local_app_data}/data/CPath_File.txt", "r+").read()


class Sidebar(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setFixedWidth(40)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.ai_chat_widget = AIChatWidget(self)


# noinspection PyUnresolvedReferences
# no inspection for unresolved references as pylance flags inaccurately sometimes

    def toggle_ai_chat(self):
        if self.ai_chat_dock is None:
            # Create the ai_chat_dock if it doesn't exist
            self.ai_chat_dock = QDockWidget("AI Chat", self)
            # ... set up the dock widget ...
            self.addDockWidget(Qt.RightDockWidgetArea, self.ai_chat_dock)
        
        if self.ai_chat_dock.isVisible():
            self.ai_chat_dock.hide()
        else:
            self.ai_chat_dock.show()

   
class AuraTextWindow(QWidget):
    def __init__(self, parent=None, settings=None, download_manager=None, model_manager=None, diff_merger_widget=None, theme_manager=None):
        super().__init__(parent)
        self.settings = settings
        self.download_manager = download_manager
        self.model_manager = model_manager
        self.diff_merger_widget = diff_merger_widget
        self.theme_manager = theme_manager
        self.editors = []
        self.current_editor = None
        
        logging.info("Starting AuraTextWindow initialization")
        try:
            self.local_app_data = local_app_data
            
            # Load configurations
            self.load_configurations()
 
            self.lexer_manager = Lexers.LexerManager(self)
            logging.info("Setting up UI components")
            self.setup_ui()
            
            logging.info("Loading plugins")
            self.load_plugins()
            
            # Connect to theme changes
            if self.theme_manager:
                self.theme_manager.theme_changed.connect(self.apply_theme)
            
            logging.info("AuraTextWindow initialization complete")
        except Exception as e:
            logging.exception(f"Error during AuraTextWindow initialization: {e}")

    def apply_theme(self, theme=None):
        logging.info("Applying theme to AuraTextWindow")
        if theme is None and self.theme_manager:
            theme = self.theme_manager.current_theme
        
        if theme:
            for editor in self.editors:
                self.apply_theme_to_editor(editor, theme)
        else:
            logging.warning("No theme available to apply")
        logging.info("Theme applied to AuraTextWindow")

    def apply_theme_to_editor(self, editor, theme):
        if editor is not None:
            try:
                editor.setPaper(QColor(theme.get("editor_theme", "#CCCCCC")))
                editor.setColor(QColor(theme.get("editor_fg", "#000000")))
                editor.setFont(QFont(theme.get("font", "Courier")))
            except Exception as e:
                logging.error(f"Error applying theme to editor: {e}")
        else:
            logging.warning("Attempted to apply theme to a None editor")
    
    def load_configurations(self):
        # Load theme, config, terminal history, and shortcuts
        # (Keep your existing configuration loading code here)
        pass

    def setup_ui(self):
        logging.info("Starting UI setup")
        try:
            main_layout = QVBoxLayout(self)

            # Menu bar (now a widget instead of window menu bar)
            menu_bar = QMenuBar(self)
            main_layout.addWidget(menu_bar)
            self.create_menus(menu_bar)

            # Tool bar
            toolbar = QToolBar()
            main_layout.addWidget(toolbar)
            self.create_tool_bar(toolbar)

            # Main content area
            content_layout = QHBoxLayout()
            main_layout.addLayout(content_layout)

            # File tree
            self.file_tree_view = QTreeView()
            self.setup_file_tree()
            content_layout.addWidget(self.file_tree_view, 1)

            # Tab widget for multiple files
            self.tab_widget = QTabWidget()
            self.tab_widget.setTabsClosable(True)
            self.tab_widget.tabCloseRequested.connect(self.close_tab)
            content_layout.addWidget(self.tab_widget, 3)
     # Create AIChatWidget
            self.ai_chat_widget = AIChatWidget(settings=self.settings, model_manager=self.model_manager, download_manager=self.download_manager)
            
            # Create a button to toggle AI Chat visibility
            self.toggle_ai_chat_button = QPushButton("Toggle AI Chat")
            self.toggle_ai_chat_button.clicked.connect(self.toggle_ai_chat)
            content_layout.addWidget(self.toggle_ai_chat_button)
            
            # Add AI Chat widget to layout (initially hidden)
            content_layout.addWidget(self.ai_chat_widget)
            self.ai_chat_widget.hide()
            # Set up tab widget
            # Create initial editor
            self.new_document()
            
            logging.info("UI setup complete")
        except Exception as e:
            logging.exception(f"Error during UI setup: {e}")

    def create_editor(self):
        logging.info("Creating new editor")
        try:
            editor = QsciScintilla(self)
            self.setup_editor(editor)
            return editor
        except Exception as e:
            logging.exception(f"Error creating editor: {e}")
            return None

    def setup_editor(self, editor):
        try:
            # Set up basic properties
            editor.setUtf8(True)
            editor.setIndentationsUseTabs(False)
            editor.setTabWidth(4)
            editor.setIndentationGuides(True)
            editor.setTabIndents(True)
            editor.setAutoIndent(True)
            editor.setCaretLineVisible(True)
            editor.setCaretWidth(2)

            # Set up lexer
            self.lexer_manager.apply_lexer("python", editor)  # Default to Python lexer

            # Set up margins and folding
            editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
            editor.setMarginWidth(0, "0000")
            editor.setMarginLineNumbers(1, True)
            editor.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
            editor.setMarginSensitivity(2, True)

            # Apply theme
            if self.theme_manager and self.theme_manager.current_theme:
                self.apply_theme_to_editor(editor, self.theme_manager.current_theme)
            else:
                logging.warning("No theme available to apply to editor")

            # Set up context menu
            self.setup_context_menu(editor)

            # Connect signals
            editor.textChanged.connect(self.on_text_changed)

            return editor
        except Exception as e:
            logging.error(f"Error in setup_editor: {str(e)}")
            raise

    def setup_context_menu(self, editor):
        context_menu = QMenu(editor)
        context_menu.addAction("Cut").triggered.connect(editor.cut)
        context_menu.addAction("Copy").triggered.connect(editor.copy)
        context_menu.addAction("Paste").triggered.connect(editor.paste)
        context_menu.addAction("Select All").triggered.connect(editor.selectAll)
        context_menu.addSeparator()
        context_menu.addAction("Calculate", self.calculate)
        find_action = QAction("Find", editor)
        find_action.triggered.connect(self.show_search_dialog)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        context_menu.addAction(find_action)

        editor.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        editor.customContextMenuRequested.connect(lambda pos: context_menu.exec(editor.mapToGlobal(pos)))

    def show_search_dialog(self):
        if self.current_editor:
            search_dialog = Search(self.current_editor)
            search_dialog.exec()

    def calculate(self):
        if self.current_editor:
            ModuleFile.calculate(self.current_editor)

    def new_document(self, title="Untitled"):
        logging.info(f"Creating new document: {title}")
        try:
            editor = self.create_editor()
            if editor:
                editor.setMinimumSize(400, 300)  # Set minimum size
                self.editors.append(editor)
                index = self.tab_widget.addTab(editor, title)
                self.tab_widget.setCurrentIndex(index)
                self.current_editor = editor
                
                # Apply theme to the new editor
                if self.theme_manager and self.theme_manager.current_theme:
                    self.apply_theme_to_editor(editor, self.theme_manager.current_theme)
                
                # Connect the text changed signal
                editor.textChanged.connect(self.on_text_changed)
            else:
                logging.error("Failed to create editor")
        except Exception as e:
            logging.exception(f"Error creating new document: {e}")

    def change_text_editor(self, index):
        if 0 <= index < len(self.editors):
            self.current_editor = self.editors[index]
            if self.ai_chat_widget:
                self.ai_chat_widget.set_current_file(
                    self.tab_widget.tabText(index),
                    self.current_editor.text()
                )

    def remove_editor(self, index):
        if 0 <= index < len(self.editors):
            editor = self.editors.pop(index)
            self.tab_widget.removeTab(index)
            editor.deleteLater()
            if not self.editors:
                self.new_document()

    def load_plugins(self):
        # Load plugins
        # (Keep your existing plugin loading code here)
        pass

    def open_file(self, path=None):
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                self.new_document(title=os.path.basename(path))
                if self.current_editor:
                    self.current_editor.setText(content)
                    
                    # Update AI Chat Widget with the new file
                    if self.ai_chat_widget:
                        self.ai_chat_widget.set_current_file(path, content)

                    # Apply lexer based on file extension
                    _, ext = os.path.splitext(path)
                    self.apply_lexer_for_extension(ext)
                else:
                    raise Exception("Failed to create a new editor")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")

    def apply_lexer_for_extension(self, ext):
        lexer_name = self.lexer_manager.get_lexer_for_extension(ext)
        if lexer_name:
            self.lexer_manager.apply_lexer(lexer_name, self.current_editor)

    def create_menus(self, menu_bar):
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_document)
        file_menu.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction("Cut", self)
        cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)

        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)

        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        toggle_file_tree_action = QAction("Toggle File Tree", self)
        toggle_file_tree_action.triggered.connect(self.toggle_file_tree)
        view_menu.addAction(toggle_file_tree_action)

        # Tools menu
        tools_menu = menu_bar.addMenu("&Tools")
        
        find_action = QAction("Find", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self.find)
        tools_menu.addAction(find_action)

        replace_action = QAction("Replace", self)
        replace_action.setShortcut(QKeySequence.StandardKey.Replace)
        replace_action.triggered.connect(self.replace)
        tools_menu.addAction(replace_action)

    def create_tool_bar(self, toolbar):
        toolbar.addAction(QIcon("path/to/new_icon.png"), "New", self.new_document)
        toolbar.addAction(QIcon("path/to/open_icon.png"), "Open", self.open_file)
        toolbar.addAction(QIcon("path/to/save_icon.png"), "Save", self.save_file)

    def setup_file_tree(self):
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath(QDir.rootPath())
        self.file_tree_view.setModel(self.file_system_model)
        self.file_tree_view.setRootIndex(self.file_system_model.index(QDir.rootPath()))
        self.file_tree_view.clicked.connect(self.file_tree_item_clicked)

    def save_file(self):
        # Implement file saving logic
        # After saving, emit the signal
        # self.file_saved.emit(file_path)
        pass

    def save_file_as(self):
        # Implement "save as" logic
        pass

    def close_tab(self, index):
        # Implement tab closing logic
        pass

    def undo(self):
        if self.current_editor:
            self.current_editor.undo()

    def redo(self):
        if self.current_editor:
            self.current_editor.redo()

    def cut(self):
        if self.current_editor:
            self.current_editor.cut()

    def copy(self):
        if self.current_editor:
            self.current_editor.copy()

    def paste(self):
        if self.current_editor:
            self.current_editor.paste()

    def find(self):
        # Implement find functionality
        pass

    def replace(self):
        # Implement replace functionality
        pass

    def toggle_file_tree(self):
        if self.file_tree_view.isVisible():
            self.file_tree_view.hide()
        else:
            self.file_tree_view.show()

    def file_tree_item_clicked(self, index):
        path = self.file_system_model.filePath(index)
        if os.path.isfile(path):
            self.open_file(path)

    def configure_menuBar(self):
        try:
            logging.info("aaaaaaaaa")
            MenuConfig.do_configure_menuBar(self)
            logging.info("111111111")
        except Exception as e:
            logging.exception(f"Error in configure_menuBar: {e}")
            import traceback
            traceback.print_exc()
            input("Press Enter to continue...")  # This will keep the console open  
    def duplicate_line(self):
        ModuleFile.duplicate_line(self)
        self.current_editor.setMarginsBackgroundColor(QColor(self._themes["margin_theme"]))
        self.current_editor.setMarginsForegroundColor(QColor("#FFFFFF"))

    def toggle_read_only(self):
        self.current_editor.setReadOnly(True)
        self.statusBar.editModeLabel.setText("ReadOnly")

    def read_only_reset(self):
        self.current_editor.setReadOnly(False)
        self.statusBar.editModeLabel.setText("Edit")

    def pastebin(self):
        ModuleFile.pastebin(self)

    def code_formatting(self):
        ModuleFile.code_formatting(self)

    def goto_line(self):
        line_number, ok = QInputDialog.getInt(self, "Goto Line", "Line:")
        if ok:
            self.setCursorPosition(line_number - 1, 0)

    def import_theme(self):
        theme_open = filedialog.askopenfilename(title="Open JSON File", defaultextension='.json',
                                                filetypes=[('JSON file', '*.json')])
        theme_path = os.path.abspath(theme_open)

        import shutil

        shutil.copyfile(theme_path, f'{local_app_data}/data/theme.json')  # copy src to dst
        # Reload theme and apply it
        self.theme_manager.load_theme()
        self.apply_theme()

    def shortcuts(self):
        shortcut_dock = shortcuts.Shortcuts()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, shortcut_dock)

    def find_in_editor(self):
        self.current_editor.show_search_dialog()

    def open_project(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec():
            project_path = dialog.selectedFiles()[0]
            pathh = str(project_path)
            with open(f"{self.local_app_data}/data/CPath_Project.txt", "w") as file:
                file.write(pathh)
            messagebox = QMessageBox()
            messagebox.setWindowTitle("New Project"), messagebox.setText(
                f"New project created at {project_path}"
            )
            messagebox.exec()
            self.treeview_project(project_path)

    def open_project_as_treeview(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        if dialog.exec():
            project_path = dialog.selectedFiles()[0]
            self.treeview_project(project_path)

    def additional_prefs(self):
        settings = additional_prefs.SettingsWindow()
        settings.exec()

    def cut_document(self):
        if self.current_editor:
            self.current_editor.cut()

    def copy_document(self):
        if self.current_editor:
            self.current_editor.copy()

    def paste_document(self):
        if self.current_editor:
            self.current_editor.paste()

    def redo_document(self):
        if self.current_editor:
            self.current_editor.redo()

    def notes(self):
        notes_dock = QDockWidget("Notes", self)
        notes_text = QTextEdit()
        notes_dock.setWidget(notes_text)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, notes_dock)
    
    def addAction(self, action):
        logging.debug(f"Adding action: {action.text()}")
        super().addAction(action)
        logging.debug(f"Action added: {action.text()}")

    def on_text_changed(self):
        if self.current_editor and self.ai_chat_widget:
            current_index = self.tab_widget.currentIndex()
            self.ai_chat_widget.set_current_file(
                self.tab_widget.tabText(current_index),
                self.current_editor.text()
            )

    def open_diff_merger(self):
        if not self.diff_merger_widget:
            self.diff_merger_widget = DiffMergerWidget()
        
        if self.current_editor:
            current_text = self.current_editor.text()
            self.diff_merger_widget.x_box.text_edit.setPlainText(current_text)
        
        if self.ai_chat_widget:
            ai_suggested_text = self.ai_chat_widget.chat_display.toPlainText()
            self.diff_merger_widget.y_box.text_edit.setPlainText(ai_suggested_text)
        
        self.diff_merger_widget.show()
        self.diff_merger_widget.show_diff()

    def add_new_reference(self):
        if self.current_editor:
            cursor = self.current_editor.textCursor()
            selected_text = cursor.selectedText()
            if selected_text:
                self.ai_chat_widget.add_chat_reference(selected_text[:30] + "...", selected_text)
            else:
                QMessageBox.warning(self, "No Selection", "Please select some text to add as a reference.")

    def toggle_ai_chat(self):
        if self.ai_chat_widget.isVisible():
            self.ai_chat_widget.hide()
        else:
            self.ai_chat_widget.show()

class Search(QDialog):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.textBox = QLineEdit()
        self.textBox.setPlaceholderText("Enter text to find")
        layout.addWidget(self.textBox)

        self.cs = QCheckBox("Case sensitive")
        layout.addWidget(self.cs)

        button_layout = QHBoxLayout()
        self.previous = QPushButton("Previous")
        self.previous.clicked.connect(self.find_previous)
        button_layout.addWidget(self.previous)

        self.next = QPushButton("Next")
        self.next.clicked.connect(self.find_next)
        button_layout.addWidget(self.next)

        layout.addLayout(button_layout)

        self.setWindowTitle("Find")

    def find_next(self):
        self.search(forward=True)

    def find_previous(self):
        self.search(forward=False)

    def search(self, forward):
        search_text = self.textBox.text()
        case_sensitive = self.cs.isChecked()
        if search_text:
            self.editor.findFirst(search_text, False, case_sensitive, False, True, forward)
        else:
            QMessageBox.warning(self, "Warning", "Please enter text to find.")
