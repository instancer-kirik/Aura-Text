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
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPushButton, QInputDialog, QMessageBox

from PyQt6.QtGui import QColor, QFont
from PyQt6.Qsci import QsciScintilla
import logging
from GUX.ai_chat import AIChatWidget
from GUX.diff_merger import DiffMergerWidget

class AuraTextWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logging.info("Starting AuraTextWindow initialization")
        try:
            self.local_app_data = local_app_data
            
            # Load configurations
            self.load_configurations()
            
            # Set up the main layout
            self.main_layout = QVBoxLayout(self)
            self.setLayout(self.main_layout)
            
            # Create and set up the tab widget
            self.tab_widget = QTabWidget(self)
            self.main_layout.addWidget(self.tab_widget)
            
            # Create AI Chat Widget (initialize only once)
            self.ai_chat_widget = AIChatWidget(self)
            self.main_layout.addWidget(self.ai_chat_widget)
            
            # Button to edit instructions
            edit_instructions_button = QPushButton("Edit AI Instructions")
            edit_instructions_button.clicked.connect(self.edit_instructions)
            self.main_layout.addWidget(edit_instructions_button)
            
            self.editors = []
            self.current_editor = None
            
            logging.info("Setting up UI components")
            self.setup_ui()
            
            logging.info("Loading plugins")
            self.load_plugins()
            
            logging.info("AuraTextWindow initialization complete")
        except Exception as e:
            logging.exception(f"Error during AuraTextWindow initialization: {e}")

    def load_configurations(self):
        # Load theme, config, terminal history, and shortcuts
        # (Keep your existing configuration loading code here)
        pass

    def setup_ui(self):
        logging.info("Starting UI setup")
        try:
            # Set up tab widget
            self.tab_widget.setTabsClosable(True)
            self.tab_widget.tabCloseRequested.connect(self.remove_editor)
            self.tab_widget.currentChanged.connect(self.change_text_editor)
            
            # Create initial editor
            self.new_document()
            
            # Create a button to open the Diff Merger
            self.diff_merger_button = QPushButton("Open Diff Merger")
            self.diff_merger_button.clicked.connect(self.open_diff_merger)
            self.main_layout.addWidget(self.diff_merger_button)
            
            # Add a button to create a new reference
            self.add_reference_button = QPushButton("Add Reference")
            self.add_reference_button.clicked.connect(self.add_new_reference)
            self.main_layout.addWidget(self.add_reference_button)
            
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
        # Set up editor properties, margins, lexer, etc.
        # (Keep your existing editor setup code here)
        pass

    def new_document(self, title="Untitled"):
        logging.info(f"Creating new document: {title}")
        try:
            editor = QsciScintilla()
            # Set up your QsciScintilla editor here (e.g., lexer, margins, etc.)
            
            self.editors.append(editor)
            index = self.tab_widget.addTab(editor, title)
            self.tab_widget.setCurrentIndex(index)
            self.current_editor = editor
            
            # Connect the text changed signal
            editor.textChanged.connect(self.on_text_changed)
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
                    self.ai_chat_widget.set_current_file(path, content)

                    # Apply lexer based on file extension
                    _, ext = os.path.splitext(path)
                    self.apply_lexer_for_extension(ext)
                else:
                    raise Exception("Failed to create a new editor")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")

    def apply_lexer_for_extension(self, ext):
        # This method should be implemented to apply the appropriate lexer
        # based on the file extension
        pass

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

    def find_in_editor(self):
        # Implement find functionality
        pass
    
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

    def edit_instructions(self):
        if self.ai_chat_widget:
            current_instructions = self.ai_chat_widget.get_instructions()
            new_instructions, ok = QInputDialog.getMultiLineText(
                self, "Edit AI Instructions", "Enter new instructions:", current_instructions)
            if ok:
                self.ai_chat_widget.set_instructions(new_instructions)
        else:
            QMessageBox.warning(self, "Error", "AI Chat Widget not initialized")

    def get_selected_text(self):
        if self.current_editor:
            return self.current_editor.selectedText()
        return ""
    def get_open_files(self):
            return [self.tab_widget.tabText(i) for i in range(self.tab_widget.count())]
