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
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from .file_outline_widget import FileOutlineWidget
from GUX.search_dialog import SearchDialog
from HMC.action_handlers import ActionHandlers
import AuraText
from auratext.Components.shortcuts_dialog import ShortcutsDialog
local_app_data = os.path.join(os.getenv("LocalAppData"), "AuraText")
cpath = open(f"{local_app_data}/data/CPath_Project.txt", "r+").read()
cfile = open(f"{local_app_data}/data/CPath_File.txt", "r+").read()

class Sidebar(QDockWidget):
    def __init__(self, title, parent=None, ai_chat_widget=None):
        super().__init__(title, parent)
        self.setFixedWidth(40)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.ai_chat_widget = ai_chat_widget


# noinspection PyUnresolvedReferences
# no inspection for unresolved references as pylance flags inaccurately sometimes

    def toggle_ai_chat(self):
        if self.ai_chat_widget is None:
            logging.error("AI Chat widget is not initialized.")
            return  # Prevent further actions if the widget is not initialized
        self.ai_chat_widget.setVisible(not self.ai_chat_widget.isVisible())


class AuraTextWindow(QWidget):
    def __init__(self, mm, parent=None):
        super().__init__(parent)
        logging.info("Initializing AuraTextWindow")
        self.mm = mm
#        self.additional_prefs = mm.AdditionalPrefs()
        self.action_group = QActionGroup(self)
        self.action_handlers = ActionHandlers(mm)
        self.setup_ui()
        # self.auratext = AuraText(self.mm)
        self.setup_connections()
        self.ai_chat_widget = None
        self.settings_sidebar = None
        self.explorer_sidebar = None
        self.layout = QVBoxLayout(self)
        # self.layout.addWidget(self)
        logging.info("AuraTextWindow initialization complete")

    def setup_ui(self):
        logging.info("main contentSetup start")
        main_layout = QVBoxLayout(self)
        self.setup_menu_bar(main_layout)
        self.setup_toolbar(main_layout)
        self.setup_main_content(main_layout)

    def setup_menu_bar(self, layout):
        menu_bar = QMenuBar(self)
        layout.addWidget(menu_bar)
        MenuConfig.do_configure_menuBar(self, menu_bar)

    def setup_toolbar(self, layout):
        toolbar = QToolBar()
        layout.addWidget(toolbar)
        self.create_tool_bar(toolbar)

    def setup_main_content(self, layout):
        content_layout = QHBoxLayout()
        layout.addLayout(content_layout)

        self.setup_file_tree(content_layout)
        self.setup_editor_area(content_layout)
        self.setup_ai_chat(content_layout)
        logging.info("main contentSetup complete")
    def setup_file_tree(self, layout):
        self.file_tree_view = QTreeView()
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath(QDir.rootPath())
        self.file_tree_view.setModel(self.file_system_model)
        self.file_tree_view.setRootIndex(self.file_system_model.index(QDir.rootPath()))
        layout.addWidget(self.file_tree_view, 1)

    def setup_editor_area(self, layout):
        right_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.file_outline_widget = FileOutlineWidget()
        right_layout.addWidget(self.tab_widget)
        right_layout.addWidget(self.file_outline_widget)
        layout.addLayout(right_layout, 3)

    def setup_ai_chat(self, layout):
        self.ai_chat_widget = AIChatWidget(
            parent=self,
            model_manager=self.mm.model_manager,
            download_manager=self.mm.download_manager,
            settings_manager=self.mm.settings_manager
        )
        self.toggle_ai_chat_button = QPushButton("Toggle AI Chat")
        layout.addWidget(self.toggle_ai_chat_button)
        layout.addWidget(self.ai_chat_widget)
        self.ai_chat_widget.hide()

    def setup_connections(self):
        self.tab_widget.tabCloseRequested.connect(self.action_handlers.close_file)
        self.file_tree_view.clicked.connect(self.file_tree_item_clicked)
        self.toggle_ai_chat_button.clicked.connect(self.toggle_ai_chat)

    def create_tool_bar(self, toolbar):
        toolbar.addAction(QIcon("path/to/new_icon.png"), "New", self.action_handlers.new_file)
        toolbar.addAction(QIcon("path/to/open_icon.png"), "Open", self.action_handlers.open_file)
        toolbar.addAction(QIcon("path/to/save_icon.png"), "Save", self.action_handlers.save_file)

    # UI update methods
    def update_file_outline(self):
        if self.mm.editor_manager.current_editor:
            text = self.mm.editor_manager.current_editor.text()
            self.file_outline_widget.populate_file_outline(text)

    def toggle_ai_chat(self):
        self.ai_chat_widget.setVisible(not self.ai_chat_widget.isVisible())

    def file_tree_item_clicked(self, index):
        path = self.file_system_model.filePath(index)
        if os.path.isfile(path):
            self.action_handlers.open_file(path)

    def show_search_dialog(self):
        if self.mm.editor_manager.current_editor:
            SearchDialog(self.mm.editor_manager.current_editor).exec()

    def apply_theme(self, theme):
        self.mm.editor_manager.apply_theme_to_all_editors(theme)
        self.mm.theme_manager.apply_theme_to_widget(self, theme)
        self.mm.theme_manager.apply_theme_to_widget(self.file_tree_view, theme)
        self.mm.theme_manager.apply_theme_to_widget(self.ai_chat_widget, theme)

    def code_formatting(self):
        self.mm.editor_manager.code_formatting()

    def goto_line(self):
        line_number, ok = QInputDialog.getInt(self, "Goto Line", "Line:")
        if ok:
            self.mm.editor_manager.goto_line(line_number)

    def import_theme(self):
        theme_file, _ = QFileDialog.getOpenFileName(self, "Open JSON File", "", "JSON Files (*.json)")
        if theme_file:
            self.mm.theme_manager.import_theme(theme_file)
            self.apply_theme(self.mm.theme_manager.current_theme)

    def show_shortcuts(self):
        shortcuts_dialog = ShortcutsDialog(self)
        shortcuts_dialog.exec()

    def load_plugins(self):
        self.mm.plugin_manager.load_plugins()

    def new_project(self):
        # Implement the new project functionality
        project_name, ok = QInputDialog.getText(self, "New Project", "Enter project name:")
        if ok and project_name:
            # Create a new project with the given name
            # This is a placeholder implementation. You should replace it with your actual project creation logic.
            project_path = os.path.join(os.path.expanduser("~"), "AuraTextProjects", project_name)
            os.makedirs(project_path, exist_ok=True)
            QMessageBox.information(self, "New Project", f"Created new project: {project_name}\nPath: {project_path}")
            # You might want to open the new project in the file tree view
            self.file_system_model.setRootPath(project_path)
            self.file_tree_view.setRootIndex(self.file_system_model.index(project_path))

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.file_system_model.setRootPath(folder)
            self.file_tree_view.setRootIndex(self.file_system_model.index(folder))

    def save_as(self):
        if self.mm.editor_manager.current_editor:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save As")
            if file_path:
                with open(file_path, 'w') as f:
                    f.write(self.mm.editor_manager.current_editor.text())
                self.mm.editor_manager.current_editor.setModified(False)
           
    def save_all(self):
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if editor.isModified():
                self.tab_widget.setCurrentIndex(i)
                self.save_file()

    def close_file(self):
        if self.tab_widget.count() > 0:
            self.close_tab(self.tab_widget.currentIndex())

    def close_all(self):
        while self.tab_widget.count() > 0:
            self.close_tab(0)

    def print_file(self):
        if self.mm.editor_manager.current_editor:
            QMessageBox.information(self, "Print", "Print functionality not implemented yet.")

    def exit_app(self):
        self.close()

    def open_project(self):
        project_path = QFileDialog.getExistingDirectory(self, "Open Project")
        if project_path:
            self.file_system_model.setRootPath(project_path)
            self.file_tree_view.setRootIndex(self.file_system_model.index(project_path))
            QMessageBox.information(self, "Open Project", f"Opened project at: {project_path}")

    def open_project_as_treeview(self):
        project_path = QFileDialog.getExistingDirectory(self, "Open Project as Treeview")
        if project_path:
            dock = QDockWidget("Project Tree", self)
            tree_view = QTreeView(dock)
            tree_model = QFileSystemModel()
            tree_model.setRootPath(project_path)
            tree_view.setModel(tree_model)
            tree_view.setRootIndex(tree_model.index(project_path))
            dock.setWidget(tree_view)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
            QMessageBox.information(self, "Open Project", f"Opened project as treeview: {project_path}")

    def expandSidebar__Settings(self):
        if self.settings_sidebar is None:
            self.settings_sidebar = QDockWidget("Settings", self)
            settings_widget = QWidget()
            settings_layout = QVBoxLayout(settings_widget)
            
            # Add settings options here
            theme_button = QPushButton("Change Theme")
            theme_button.clicked.connect(self.change_theme)
            settings_layout.addWidget(theme_button)
            
            font_button = QPushButton("Change Font")
            font_button.clicked.connect(self.change_font)
            settings_layout.addWidget(font_button)
            
            # Add more settings options as needed
            
            self.settings_sidebar.setWidget(settings_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.settings_sidebar)
        else:
            self.settings_sidebar.setVisible(not self.settings_sidebar.isVisible())
    
    def expandSidebar__Explorer(self):
        if self.explorer_sidebar is None:
            self.explorer_sidebar = QDockWidget("Project Directory", self)
            explorer_widget = QWidget()
            explorer_layout = QVBoxLayout(explorer_widget)
            
            # Add project directory view here
            self.file_system_model = QFileSystemModel()
            self.file_system_model.setRootPath(QDir.rootPath())
            self.file_tree_view = QTreeView()
            self.file_tree_view.setModel(self.file_system_model)
            self.file_tree_view.setRootIndex(self.file_system_model.index(QDir.rootPath()))
            explorer_layout.addWidget(self.file_tree_view)
            
            self.explorer_sidebar.setWidget(explorer_widget)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.explorer_sidebar)
        else:
            self.explorer_sidebar.setVisible(not self.explorer_sidebar.isVisible())

    def change_theme(self):
        # Implement theme change functionality
        pass

    def change_font(self):
        # Implement font change functionality
        pass
    def close_all(self):
        while self.tab_widget.count() > 0:
            self.editor_manager.close_tab(0)
    def fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
           
    def save_all(self):
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if editor.isModified():
                self.tab_widget.setCurrentIndex(i)
                self.save_file()

    def close_file(self):
        if self.tab_widget.count() > 0:
            self.close_tab(self.tab_widget.currentIndex())

    def close_all(self):
        while self.tab_widget.count() > 0:
            self.close_tab(0)

    def print_file(self):
        if self.mm.editor_manager.current_editor:
            QMessageBox.information(self, "Print", "Print functionality not implemented yet.")

    def exit_app(self):
        self.close()

    def open_project(self):
        project_path = QFileDialog.getExistingDirectory(self, "Open Project")
        if project_path:
            self.file_system_model.setRootPath(project_path)
            self.file_tree_view.setRootIndex(self.file_system_model.index(project_path))
            QMessageBox.information(self, "Open Project", f"Opened project at: {project_path}")

    def open_project_as_treeview(self):
        project_path = QFileDialog.getExistingDirectory(self, "Open Project as Treeview")
        if project_path:
            dock = QDockWidget("Project Tree", self)
            tree_view = QTreeView(dock)
            tree_model = QFileSystemModel()
            tree_model.setRootPath(project_path)
            tree_view.setModel(tree_model)
            tree_view.setRootIndex(tree_model.index(project_path))
            dock.setWidget(tree_view)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
            QMessageBox.information(self, "Open Project", f"Opened project as treeview: {project_path}")

    def expandSidebar__Settings(self):
        if self.settings_sidebar is None:
            self.settings_sidebar = QDockWidget("Settings", self)
            settings_widget = QWidget()
            settings_layout = QVBoxLayout(settings_widget)
            
            # Add settings options here
            theme_button = QPushButton("Change Theme")
            theme_button.clicked.connect(self.change_theme)
            settings_layout.addWidget(theme_button)
            
            font_button = QPushButton("Change Font")
            font_button.clicked.connect(self.change_font)
            settings_layout.addWidget(font_button)
            
            # Add more settings options as needed
            
            self.settings_sidebar.setWidget(settings_widget)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.settings_sidebar)
        else:
            self.settings_sidebar.setVisible(not self.settings_sidebar.isVisible())
    
    def expandSidebar__Explorer(self):
        if self.explorer_sidebar is None:
            self.explorer_sidebar = QDockWidget("Project Directory", self)
            explorer_widget = QWidget()
            explorer_layout = QVBoxLayout(explorer_widget)
            
            # Add project directory view here
            self.file_system_model = QFileSystemModel()
            self.file_system_model.setRootPath(QDir.rootPath())
            self.file_tree_view = QTreeView()
            self.file_tree_view.setModel(self.file_system_model)
            self.file_tree_view.setRootIndex(self.file_system_model.index(QDir.rootPath()))
            explorer_layout.addWidget(self.file_tree_view)
            
            self.explorer_sidebar.setWidget(explorer_widget)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.explorer_sidebar)
        else:
            self.explorer_sidebar.setVisible(not self.explorer_sidebar.isVisible())

    def change_theme(self):
        # Implement theme change functionality
        pass

    def change_font(self):
        # Implement font change functionality
        pass
    def close_all(self):
        while self.tab_widget.count() > 0:
            self.editor_manager.close_tab(0)
    def fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()