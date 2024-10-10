from datetime import datetime
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
from AuraText.auratext.Components.powershell import TerminalEmulator
import pyjokes
import hashlib
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
    QGroupBox,
    QStatusBar,
    QLabel)
from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtCore import QEasingCurve
from HMC.vault_manager import Vault
from PyQt6.QtWidgets import QWidgetAction
from AuraText.auratext.Components.TabWidget import CircularTabBar, ImprovedTabWidget, TabWidget
from PyQt6.QtWidgets import QToolButton
import time
# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from AuraText.auratext.Misc import shortcuts, WelcomeScreen, boilerplates, file_templates
from . import MenuConfig
from . import additional_prefs
from . import Modules as ModuleFile
from . import PluginDownload
from . import ThemeDownload
from . import config_page
from ..Components import powershell, terminal, statusBar, GitCommit, GitPush
from PyQt6.QtCore import QEvent
from AuraText.auratext.Components.TabWidget import TabWidget
from .plugin_interface import Plugin

from .Lexers import LexerManager
from HMC.download_manager import DownloadManager
from GUX.ai_chat import AIChatWidget
from PyQt6.QtWidgets import QTabWidget, QTabBar, QStylePainter, QStyleOptionTab, QStyle
from PyQt6.QtCore import QRect, Qt, QPoint
from PyQt6.QtGui import QWheelEvent
from GUX.diff_merger import DiffMergerWidget
from PyQt6.QtWidgets import  QMenu, QLineEdit, QCheckBox, QHBoxLayout, QPushButton, QDialog
from PyQt6.Qsci import QsciAPIs
from . import Lexers
from PyQt6.QtGui import QKeySequence, QAction
from PyQt6.QtWidgets import QMenuBar, QToolBar, QDialogButtonBox
from PyQt6.QtCore import QDir
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from .file_outline_widget import FileOutlineWidget
from GUX.search_dialog import SearchDialog

from AuraText.auratext.Core.CodeEditor import CodeEditor
from PyQt6.QtWidgets import QComboBox, QListWidget
from AuraText.auratext.Components.shortcuts_dialog import ShortcutsDialog
local_app_data = os.path.join(os.getenv("LocalAppData"), "AuraText")
cpath = open(f"{local_app_data}/data/CPath_Project.txt", "r+").read()
cfile = open(f"{local_app_data}/data/CPath_File.txt", "r+").read()
from PyQt6.QtGui import QShortcut, QMouseEvent
from GUX.file_tree_view import FileTreeView
from PyQt6.QtWidgets import QStackedWidget
from HMC.project_manager import ProjectManagerWidget
from GUX.file_search_widget import FileSearchWidget

from pathlib import Path

class AuraTextWindow(QMainWindow):
    def __init__(self, mm, parent=None):
        super().__init__(parent)
        self.mm = mm
        self.setWindowOpacity(0)  # Start fully transparent
        self.editor_manager = mm.editor_manager
        self.current_vault = None
        if self.mm and self.mm.vault_manager:
            self.current_vault = self.mm.vault_manager.get_current_vault()
        self.action_handlers = mm.action_handlers
        self.action_group = QActionGroup(self)
        self.file_menu = None
        self.edit_menu = None
        self.view_menu = None
        self.project_menu = None
        self.code_menu = None
        self.tools_menu = None
        self.preferences_menu = None
        self.help_menu = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.recent_projects_menu = None
        self.file_search_widget = None
      
        
        if not self.current_vault:
            self.logger.warning("No current vault set during AuraTextWindow initialization")
        else:
            self.logger.debug(f"Current vault set to: {self.current_vault.name}")
        
        # Initialize attributes that might be used in setup_menu_bar
        self.project_manager = getattr(mm, 'project_manager', None)
        if self.project_manager is None:
            self.logger.warning("project_manager not found in mm, some features may be limited")
        
        self.file_system_model = self.mm.file_manager.create_file_system_model()
        self.workspace_selector = None
        self.fileset_selector = None
        self.project_selector = None
        
        # try: 
        #     self.setup_menu_bar()          #######its not showing the menu bar
        # except Exception as e:
        #     self.logger.error(f"Error in setup_menu_bar: {str(e)}")
        #     self.logger.error(traceback.format_exc())
        
        self.setup_ui()
        self.setup_ui_components()
        self.setup_connections()
        self.setup_shortcuts()
        self.setup_toolbar()
        
        self.mm.editor_manager.add_window(self)
        self.create_blank_editor()
        self.update_ui_for_vault()
        
        # Open the daily note when the window is created
        QTimer.singleShot(0, self.open_daily_note)
        
        self.fade_in()
        self.setup_vault_selector()
        self.setup_project_selector()
        self.mm.vault_manager.vault_changed.connect(self.on_vault_changed)
        self.mm.vault_manager.project_added.connect(self.on_project_changed)
        self.radial_menu = None  # Initialize radial menu as None
    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        self.tab_widget = ImprovedTabWidget(self)
        self.setCentralWidget(self.tab_widget)

    def setup_ui_components(self):
        
       
        self.cursor_manager = self.mm.cursor_manager

     
        self.file_tree_view = FileTreeView(self.file_system_model, self)
        self.file_tree_view.file_selected.connect(self.open_file)

        self.vault_explorer = FileTreeView(self.file_system_model, self)
        self.vault_explorer.file_selected.connect(self.open_file)
        self.tab_widget = ImprovedTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.terminal_emulator = TerminalEmulator(self)
        self.terminal_dock = QDockWidget("Terminal", self)
        self.terminal_dock.setWidget(self.terminal_emulator)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.terminal_dock)

        self.create_docks()
        self.setup_fileset_selector()
        self.setup_file_explorer()
        
        self.setup_workspace_selector()

        # Add Daily Note action to the File menu
        daily_note_action = QAction("Open Daily Note", self)
        daily_note_action.triggered.connect(self.open_daily_note)
      

        # Add a shortcut for opening daily note (e.g., Ctrl+Shift+D)
        daily_note_shortcut = QShortcut(QKeySequence("Ctrl+Shift+D"), self)
        daily_note_shortcut.activated.connect(self.open_daily_note)
        
   
    def toggle_file_explorer(self):
        if hasattr(self, 'file_explorer'):
            visible = self.file_explorer.isVisible()
            self.file_explorer.setVisible(not visible)
            self.view_actions["File Explorer"].setChecked(not visible)
        else:
            # Create and show the file explorer if it doesn't exist
            self.file_explorer = FileTreeView(self)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.file_explorer)
            self.view_actions["File Explorer"].setChecked(True)
    def set_vault(self, vault: Vault):
        if vault is None:
            logging.warning("Attempted to set None as the current vault.")
            return

        self.current_vault = vault
        self.update_ui_for_vault()
        
        self.setWindowTitle(f"AuraText - {vault.name}")
        if vault.path:
            loaded_vault = self.load_vault(str(vault.path))
            if loaded_vault:
                loaded_vault.load_index()
            else:
                logging.warning(f"Failed to load vault at path: {vault.path}")
        else:
            logging.warning("Vault has no path set.")
    def update_ui_for_vault(self):
        if self.current_vault:
            self.setWindowTitle(f"AuraText - {self.current_vault.name}")
            self.refresh_vault_explorer()
        else:
            self.setWindowTitle("AuraText - No Vault Selected")
        self.update_workspace_selector()
    
    def update_workspace_selector(self):
        if hasattr(self, 'workspace_selector') and self.current_vault:
            self.workspace_selector.clear()
            workspace_names = self.mm.workspace_manager.get_workspace_names(self.current_vault.path)
            self.workspace_selector.addItems(workspace_names)

    
   
   
   
    # def setup_view_menu(self):
    #     self.view_actions = {}
    #     widgets = [
    #         ("File Explorer", self.toggle_file_explorer),
    #         ("Project Manager", self.toggle_project_manager),
    #         ("Terminal", self.toggle_terminal),
    #         ("Python Console", self.toggle_python_console),
    #         # Add more widgets as needed
    #     ]

    #     for widget_name, toggle_function in widgets:
    #         action = QAction(widget_name, self, checkable=True)
    #         action.triggered.connect(toggle_function)
    #         self.view_menu.addAction(action)
    #         self.view_actions[widget_name] = action
    # def setup_menu_bar(self):
    #     self.menubar = QMenuBar(self)
    #     self.setMenuBar(self.menubar)

    #     # Use MenuConfig to set up the menus
    #     MenuConfig.do_configure_menuBar(self, self.menubar)

    #     # Set up the toolbar
    #     self.setup_toolbar()
    # def setup_menu_bar(self):
    #     self.menubar = QMenuBar(self)
    #     self.setMenuBar(self.menubar)

    #     # File menu
    #     file_menu = self.menubar.addMenu("&File")
    #     file_menu.addAction("New", self.action_handlers.new_file)
    #     file_menu.addAction("Open", self.action_handlers.open_file)
    #     file_menu.addAction("Save", self.action_handlers.save_file)
    #     file_menu.addAction("Save As", self.action_handlers.save_file_as)

    #     # Edit menu
    #     edit_menu = self.menubar.addMenu("&Edit")
    #     edit_menu.addAction("Cut", self.action_handlers.cut)
    #     edit_menu.addAction("Copy", self.action_handlers.copy)
    #     edit_menu.addAction("Paste", self.action_handlers.paste)

    #     # View menu
    #     self.view_menu = self.menubar.addMenu("&View")
    #     self.setup_view_menu()

    #     # Add other menus as needed
    #     MenuConfig.do_configure_menuBar(self, self.menubar)

    def setup_toolbar(self):
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(self.toolbar)

        # File button with dropdown
        file_button = self.create_toolbar_button("File", "path/to/file_icon.png")
        self.file_menu = QMenu(file_button)
        self.file_menu.addAction("New", self.action_handlers.new_file)
        self.file_menu.addAction("Open", self.action_handlers.open_file)
        self.file_menu.addAction("Save", self.action_handlers.save_file)
        self.file_menu.addAction("Save As", self.action_handlers.save_file_as)
        file_button.setMenu(self.file_menu)
        self.toolbar.addWidget(file_button)

        # Edit button with dropdown
        edit_button = self.create_toolbar_button("Edit", "path/to/edit_icon.png")
        self.edit_menu = QMenu(edit_button)
        self.edit_menu.addAction("Cut", self.action_handlers.cut)
        self.edit_menu.addAction("Copy", self.action_handlers.copy)
        self.edit_menu.addAction("Paste", self.action_handlers.paste)
        edit_button.setMenu(self.edit_menu)
        self.toolbar.addWidget(edit_button)

        # View button with dropdown
        view_button = self.create_toolbar_button("View", "path/to/view_icon.png")
        self.view_menu = QMenu(view_button)
        self.view_menu.addAction("Toggle File Explorer", self.toggle_file_explorer)
        self.view_menu.addAction("Toggle Terminal", self.action_handlers.toggle_terminal)
        self.view_menu.addAction("Toggle Python Console", self.action_handlers.toggle_python_console)
        view_button.setMenu(self.view_menu)
        self.toolbar.addWidget(view_button)

        # Project button with dropdown
        project_button = self.create_toolbar_button("Project", "path/to/project_icon.png")
        self.project_menu = QMenu(project_button)
        self.project_menu.addAction("New Project", self.action_handlers.new_project)
        self.project_menu.addAction("Open Project", self.action_handlers.open_project)
        self.project_menu.addAction("Project Settings", self.action_handlers.show_project_settings)
        project_button.setMenu(self.project_menu)
        self.toolbar.addWidget(project_button)

        # Code button with dropdown
        code_button = self.create_toolbar_button("Code", "path/to/code_icon.png")
        self.code_menu = QMenu(code_button)
        self.code_menu.addAction("Code Formatting", self.action_handlers.code_formatting)
        self.code_menu.addAction("Boilerplates", self.action_handlers.boilerplates)
        self.code_menu.addAction("Create Snippet", self.action_handlers.create_snippet)
        self.code_menu.addAction("Import Snippet", self.action_handlers.import_snippet)
        code_button.setMenu(self.code_menu)
        self.toolbar.addWidget(code_button)

        # Tools button with dropdown
        tools_button = self.create_toolbar_button("Tools", "path/to/tools_icon.png")
        self.tools_menu = QMenu(tools_button)
        self.tools_menu.addAction("Upload to Pastebin", self.action_handlers.pastebin)
        self.tools_menu.addAction("Notes", self.action_handlers.notes)
        self.tools_menu.addAction("File Search", self.show_file_search)
        tools_button.setMenu(self.tools_menu)
        self.toolbar.addWidget(tools_button)

        # Preferences button with dropdown
        preferences_button = self.create_toolbar_button("Preferences", "path/to/preferences_icon.png")
        self.preferences_menu = QMenu(preferences_button)
        language_menu = MenuConfig.LanguageMenuManager(self).create_language_menu(self.preferences_menu)
        self.preferences_menu.addMenu(language_menu)
        self.preferences_menu.addAction("Import Theme", self.import_theme)
        preferences_button.setMenu(self.preferences_menu)
        self.toolbar.addWidget(preferences_button)

        # Help button with dropdown
        help_button = self.create_toolbar_button("Help", "path/to/help_icon.png")
        self.help_menu = QMenu(help_button)
        self.help_menu.addAction("Keyboard Shortcuts", self.action_handlers.show_shortcuts)
        self.help_menu.addAction("Getting Started", self.action_handlers.getting_started)
        self.help_menu.addAction("Submit Bug Report", self.action_handlers.bug_report)
        self.help_menu.addAction("About", self.action_handlers.version)
        help_button.setMenu(self.help_menu)
        self.toolbar.addWidget(help_button)

        # Add separator
        self.toolbar.addSeparator()

        # Add vault selector
        self.setup_vault_selector()
        
        # Add separator
        self.toolbar.addSeparator()

        # Add project selector
        self.setup_project_selector()
        self.update_project_selector(self.mm.vault_manager.get_current_vault().name)
   
    def add_menu_buttons(self):#Visible
        # File button with dropdown
        file_button = self.create_toolbar_button("File", "path/to/file_icon.png")
        self.file_menu = QMenu(file_button)
        self.file_menu.addAction("New", self.action_handlers.new_file)
        self.file_menu.addAction("Open", self.action_handlers.open_file)
        self.file_menu.addAction("Save", self.action_handlers.save_file)
        self.file_menu.addAction("Save As", self.action_handlers.save_file_as)
        self.file_menu.addAction("Toggle Explorer View", self.toggle_explorer_view)
        file_button.setMenu(self.file_menu)
        self.toolbar.addWidget(file_button)

        # Edit button with dropdown
        edit_button = self.create_toolbar_button("Edit", "path/to/edit_icon.png")
        edit_menu = QMenu(edit_button)
        edit_menu.addAction("Cut", self.action_handlers.cut)
        edit_menu.addAction("Copy", self.action_handlers.copy)
        edit_menu.addAction("Paste", self.action_handlers.paste)
        edit_menu.addAction("Add Context", self.action_handlers.add_context)
        edit_button.setMenu(edit_menu)
        self.toolbar.addWidget(edit_button)

        # View button with dropdown
        view_button = self.create_toolbar_button("View", "path/to/view_icon.png")
        view_menu = QMenu(view_button)
        view_menu.addAction("Toggle File Explorer", self.toggle_file_explorer)
        view_menu.addAction("Toggle Terminal", self.toggle_terminal)
        view_button.setMenu(view_menu)
        self.toolbar.addWidget(view_button)

        # Project button with dropdown
        project_button = self.create_toolbar_button("Project", "path/to/project_icon.png")
        project_menu = QMenu(project_button)
        project_menu.addAction("New Project", self.new_project)
        project_menu.addAction("Open Project", self.open_project)
        project_button.setMenu(project_menu)
        self.toolbar.addWidget(project_button)

        # Code button with dropdown
        code_button = self.create_toolbar_button("Code", "path/to/code_icon.png")
        code_menu = QMenu(code_button)
        code_menu.addAction("Code Formatting", self.action_handlers.code_formatting)
        code_menu.addAction("Boilerplates", self.action_handlers.boilerplates)
        code_button.setMenu(code_menu)
        self.toolbar.addWidget(code_button)

        # Tools button with dropdown
        tools_button = self.create_toolbar_button("Tools", "path/to/tools_icon.png")
        tools_menu = QMenu(tools_button)
        tools_menu.addAction("Upload to Pastebin", self.action_handlers.pastebin)
        tools_menu.addAction("Notes", self.action_handlers.notes)
        tools_button.setMenu(tools_menu)
        self.toolbar.addWidget(tools_button)
        toggle_action = QAction("Toggle Highlight", self)
        toggle_action.triggered.connect(self.code_editor.toggle_highlight)
        self.toolbar.addAction(toggle_action)
        cycle_color_action = QAction("Cycle Debug Color", self)
        cycle_color_action.triggered.connect(self.code_editor.cycle_debug_color)
        self.toolbar.addAction(cycle_color_action)

    # def create_toolbar_button(self, text, icon_path):
    #     button = QToolButton()
    #     button.setText(text)
    #     button.setIcon(QIcon(icon_path))
    #     button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    #     button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    #     return button

    def setup_vault_selector(self):
        self.vault_selector = QComboBox()
        self.vault_selector.addItems(self.mm.vault_manager.get_vault_names())
        self.vault_selector.currentTextChanged.connect(self.on_vault_changed)
        
        vault_widget = QWidget()
        vault_layout = QHBoxLayout(vault_widget)
        vault_layout.setContentsMargins(0, 0, 0, 0)
        vault_layout.addWidget(QLabel("Vault:"))
        vault_layout.addWidget(self.vault_selector)
        
        self.toolbar.addWidget(vault_widget)

    def setup_project_selector(self):
        self.project_selector = QComboBox()
        self.project_selector.currentTextChanged.connect(self.on_project_changed)
        
        project_widget = QWidget()
        project_layout = QHBoxLayout(project_widget)
        project_layout.setContentsMargins(0, 0, 0, 0)
        project_layout.addWidget(QLabel("Project:"))
        project_layout.addWidget(self.project_selector)
        
        self.toolbar.addWidget(project_widget)

   
    def set_current_editor(self, editor):
        index = self.tab_widget.indexOf(editor)
        if index != -1:
            self.tab_widget.setCurrentIndex(index)
        else:
            logging.error("Attempted to set current editor that is not in the tab widget")
            self.tab_widget.setCurrentIndex(0)

    def set_project(self, project):
        # Implement method to set the current project
        pass

    
    def create_docks(self):
        self.projects_manager_widget = self.create_projects_manager_widget()
        self.explorer_dock = self.mm.widget_manager.create_dock("File Explorer", self.file_tree_view, self)
        self.projects_manager_dock = self.mm.widget_manager.create_dock("Projects Manager", self.projects_manager_widget, self)
        self.vaults_manager_dock = self.mm.widget_manager.create_dock("Vaults Manager", self.mm.widget_manager.VaultsManagerWidget(self.mm), self)
        self.ai_chat_dock = self.mm.widget_manager.create_dock("AI Chat", self.mm.widget_manager.AIChatWidget(self.mm), self)

        self.add_dock_widget(self.explorer_dock, "File Explorer", Qt.DockWidgetArea.LeftDockWidgetArea)
        self.add_dock_widget(self.projects_manager_dock, "Projects Manager", Qt.DockWidgetArea.LeftDockWidgetArea)
        self.add_dock_widget(self.vaults_manager_dock, "Vaults Manager", Qt.DockWidgetArea.RightDockWidgetArea)
        self.add_dock_widget(self.ai_chat_dock, "AI Chat", Qt.DockWidgetArea.RightDockWidgetArea)

    def setup_connections(self):
        if hasattr(self.mm, 'editor_manager') and self.mm.editor_manager is not None:
            self.tab_widget.tabCloseRequested.connect(self.mm.editor_manager.close_tab)
            self.tab_widget.tabBar().tabMoved.connect(self.mm.editor_manager.on_tab_moved)
            self.tab_widget.currentChanged.connect(self.mm.editor_manager.on_current_tab_changed)
        else:
            logging.warning("Editor manager not available. Some functionalities may be limited.")
        self.terminal_emulator.commandEntered.connect(self.handle_terminal_command)
        self.terminal_emulator.errorOccurred.connect(self.handle_terminal_error)
        self.file_tree_view.file_selected.connect(self.open_file_from_explorer)
        
        self.tab_widget.currentChanged.connect(self.on_current_tab_changed)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        if self.workspace_selector:
            self.workspace_selector.currentTextChanged.connect(self.on_workspace_changed)
        if self.fileset_selector is not None:
            self.fileset_selector.currentTextChanged.connect(self.on_fileset_changed)
        else:
            logging.warning("fileset_selector is None, skipping connection setup")
        
        if hasattr(self, 'file_explorer'):
            self.file_explorer.file_selected.connect(self.open_file_from_explorer)
        if hasattr(self, 'vault_explorer'):
            self.vault_explorer.file_selected.connect(self.open_file_from_explorer)
        
        if hasattr(self, 'toggle_ai_chat_button'):
            self.toggle_ai_chat_button.clicked.connect(self.toggle_ai_chat)
        
        self.tab_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.show_radial_menu)
        self.mm.vault_manager.project_added.connect(self.update_project_selector)
        # Connect signals
        self.mm.vault_manager.indexing_started.connect(self.show_loading_indicator)
        self.mm.vault_manager.indexing_finished.connect(self.hide_loading_indicator)


    def setup_shortcuts(self):
        # File operations
        QShortcut(QKeySequence.StandardKey.New, self, self.action_handlers.new_file)
        QShortcut(QKeySequence.StandardKey.Open, self, self.action_handlers.open_file)
        QShortcut(QKeySequence.StandardKey.Save, self, self.action_handlers.save_file)
        QShortcut(QKeySequence.StandardKey.SaveAs, self, self.action_handlers.save_file_as)
        QShortcut(QKeySequence.StandardKey.Close, self, self.action_handlers.close_file)

        # Edit operations
        QShortcut(QKeySequence.StandardKey.Cut, self, self.action_handlers.cut)
        QShortcut(QKeySequence.StandardKey.Copy, self, self.action_handlers.copy)
        QShortcut(QKeySequence.StandardKey.Paste, self, self.action_handlers.paste)
        QShortcut(QKeySequence.StandardKey.Undo, self, self.action_handlers.undo)
        QShortcut(QKeySequence.StandardKey.Redo, self, self.action_handlers.redo)

        # Custom shortcuts
        QShortcut(QKeySequence("Ctrl+F"), self, self.show_search_dialog)
        QShortcut(QKeySequence("Ctrl+G"), self, self.goto_line)
        QShortcut(QKeySequence("Ctrl+D"), self, self.action_handlers.duplicate_line)
        QShortcut(QKeySequence("Ctrl+/"), self, self.action_handlers.toggle_comment)

       
        self.radial_menu_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.radial_menu_shortcut.activated.connect(self.show_radial_menu)

        # Add Shift+Space shortcut to focus AI chat
        self.ai_chat_shortcut = QShortcut(QKeySequence("Shift+Space"), self)
        self.ai_chat_shortcut.activated.connect(self.focus_ai_chat)

   
    def setup_file_explorer(self):
        self.file_explorer_model = QFileSystemModel()
        self.file_explorer = FileTreeView(self.file_explorer_model, self.mm.theme_manager)
        self.file_explorer.file_selected.connect(self.open_file_from_explorer)
        
        # Get the current vault
        current_vault = self.mm.vault_manager.get_current_vault()
        if current_vault:
            root_path = current_vault.path
            # Convert WindowsPath to string
            root_path_str = str(root_path)
            
            # Set the root path
            root_index = self.file_explorer_model.setRootPath(root_path_str)
            self.file_explorer.set_root_index(root_index)
                
            # Set the current directory
            self.file_explorer_model.setRootPath(root_path_str)
        else:
            logging.warning("No current vault set for file explorer")
        self.vault_explorer = FileTreeView(self.file_system_model, self.mm.theme_manager)
         # Apply theme to the file explorer
        self.apply_theme_to_file_explorer()

        self.vault_explorer.file_selected.connect(self.open_file_from_explorer)
        self.explorer_stack = QStackedWidget()
        self.explorer_stack.addWidget(self.file_explorer)
        self.explorer_stack.addWidget(self.vault_explorer)

        self.explorer_dock = QDockWidget("Explorer", self)
        self.explorer_dock.setWidget(self.explorer_stack)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.explorer_dock)
      
        self.toggle_explorer_action = QAction("Toggle Explorer View", self)
        self.toggle_explorer_action.triggered.connect(self.toggle_explorer_view)
       
        self.update_explorer_views()

    def apply_theme_to_file_explorer(self):
        theme_data = self.mm.theme_manager.get_current_theme()
        
        if isinstance(theme_data, dict) and 'colors' in theme_data:
            colors = theme_data['colors']
        else:
            # Use default colors if theme data is not in the expected format
            colors = {
                'sidebarBackground': '#2E3440',
                'sidebarText': '#D8DEE9',
                'sidebarHighlight': '#3B4252'
            }

        stylesheet = f"""
            QTreeView {{
                background-color: {colors.get('sidebarBackground', '#2E3440')};
                color: {colors.get('sidebarText', '#D8DEE9')};
                border: none;
            }}
            QTreeView::item:selected {{
                background-color: {colors.get('sidebarHighlight', '#3B4252')};
            }}
            QTreeView::item:hover {{
                background-color: {colors.get('sidebarHover', '#434C5E')};
            }}
        """
        
        if hasattr(self, 'file_explorer') and isinstance(self.file_explorer, QTreeView):
            self.file_explorer.setStyleSheet(stylesheet)
        else:
            logging.warning("File explorer not found or is not a QTreeView")

   
    def on_vault_switch(self, new_vault_path):
        self.update_explorer_views()
        self.mm.editor_manager.on_vault_switch(new_vault_path)
    
    def update_explorer_views(self):
        self.mm.file_manager.update_explorer_views(self.file_explorer, self.vault_explorer)
 
    def setup_workspace_selector(self):
        self.workspace_selector = QComboBox(self)
        # Add workspaces to the selector
        if self.current_vault:
            workspaces = self.current_vault.get_workspace_names()
            self.workspace_selector.addItems(workspaces)
            # Set the current workspace
            current_workspace = self.mm.workspace_manager.get_active_workspace()
            if current_workspace in workspaces:
                self.workspace_selector.setCurrentText(current_workspace)                      
        else:
            self.workspace_selector.setEnabled(False)
            # Add the workspace selector to your UI (e.g., to a toolbar or status bar)
        # self.statusBar().addPermanentWidget(self.workspace_selector)

    def setup_fileset_selector(self):
        if self.fileset_selector is not None:
            filesets = self.mm.vault_manager.get_all_filesets()
            self.fileset_selector.clear()
            self.fileset_selector.addItems(filesets)
        # You might want to set a current fileset here if you have that concept
        
    def setup_ai_chat(self):
        self.ai_chat_widget = AIChatWidget(
            parent=self,
            editor_manager=self.mm.editor_manager,
            context_manager=self.mm.context_manager,
            model_manager=self.mm.model_manager,
            download_manager=self.mm.download_manager,
            settings_manager=self.mm.settings_manager,
            vault_manager=self.mm.vault_manager
        )
        self.ai_chat.file_clicked.connect(self.open_file_from_chat)
        self.ai_chat_widget.hide()
    
    def open_config_file(self):
        self.mm.open_vault_config_file()
    def toggle_vaults_manager(self):
        if self.vaults_manager_dock is None:
            self.create_vaults_manager_widget()
        
        if self.vaults_manager_dock:
            self.vaults_manager_dock.setVisible(not self.vaults_manager_dock.isVisible())
        else:
            QMessageBox.warning(self, "Error", "Failed to create Vaults Manager widget")

    def add_vault(self):
        name, ok = QInputDialog.getText(self, "Add Vault", "Enter vault name:")
        if ok and name:
            path = QFileDialog.getExistingDirectory(self, "Select Vault Directory")
            if path:
                if self.mm.vault_manager.add_vault(name, path):
                    QMessageBox.information(self, "Vault Added", f"Added new vault: {name}")
                    self.update_vault_selector()
                else:
                    QMessageBox.warning(self, "Error", "Failed to add vault. Name may already exist.")

    def remove_vault(self):
        vault_names = self.mm.vault_manager.get_vault_names()
        name, ok = QInputDialog.getItem(self, "Remove Vault", "Select vault to remove:", vault_names, 0, False)
        if ok and name:
            if self.mm.vault_manager.remove_vault(name):
                QMessageBox.information(self, "Vault Removed", f"Removed vault: {name}")
                self.update_vault_selector()
            else:
                QMessageBox.warning(self, "Error", "Failed to remove vault")

    def rename_vault(self):
        vault_names = self.mm.vault_manager.get_vault_names()
        old_name, ok = QInputDialog.getItem(self, "Rename Vault", "Select vault to rename:", vault_names, 0, False)
        if ok and old_name:
            new_name, ok = QInputDialog.getText(self, "Rename Vault", "Enter new vault name:")
            if ok and new_name:
                if self.mm.vault_manager.rename_vault(old_name, new_name):
                    QMessageBox.information(self, "Vault Renamed", f"Renamed vault from '{old_name}' to '{new_name}'")
                    self.update_vault_selector()
                else:
                    QMessageBox.warning(self, "Error", "Failed to rename vault. New name may already exist.")

    
    def on_tab_moved(self, from_index, to_index):
        self.mm.editor_manager.reorder_editors(from_index, to_index)

    def on_current_tab_changed(self, index):
        if index >= 0:
            editor = self.tab_widget.widget(index)
            self.mm.editor_manager.set_current_editor(editor)
    def on_fileset_changed(self, new_fileset_path):
        self.update_explorer_views()
    def add_new_tab(self, editor, title):
        index = self.tab_widget.addTab(editor, title)
        self.tab_widget.setCurrentIndex(index)
        
        # Ensure the editor fills the tab
        self.tab_widget.widget(index).setLayout(QVBoxLayout())
        self.tab_widget.widget(index).layout().addWidget(editor)
        self.tab_widget.widget(index).layout().setContentsMargins(0, 0, 0, 0)

        return index
    def add_new_tab(self, widget, title):
        return self.tab_widget.addTab(widget, title)

    def close_tab(self, index):
        self.mm.editor_manager.close_editor(index)

    def get_current_tab(self):
        return self.tab_widget.currentWidget()

    def set_tab_title(self, index, title):
        self.tab_widget.setTabText(index, title)
    def get_tab_count(self):
        return self.tab_widget.count()

    def toggle_ai_chat(self):
        if self.ai_chat_widget:
            self.ai_chat_widget.setVisible(not self.ai_chat_widget.isVisible())
        else:
           logging.error("AI Chat widget is not initialized.")
    def file_tree_item_clicked(self, index):
        path = self.file_system_model.filePath(index)
        if os.path.isfile(path):
            self.action_handlers.open_file(path)   
            
    def open_file_from_explorer(self, file_path):
        self.mm.file_manager.open_file(file_path)

   
    def toggle_explorer_view(self):
        current_index = self.explorer_stack.currentIndex()
        new_index = 1 if current_index == 0 else 0
        self.explorer_stack.setCurrentIndex(new_index)
   
    def show_search_dialog(self):
        if self.mm.editor_manager.current_editor:
            SearchDialog(self.mm.editor_manager.current_editor).exec()

    def apply_theme(self, theme):
        self.mm.editor_manager.apply_theme_to_all_editors(theme)
        self.mm.theme_manager.apply_theme_to_widget(self, theme)
        
        # Apply theme to specific widgets if needed
        if self.file_tree_view:
            self.mm.theme_manager.apply_theme_to_widget(self.file_tree_view, theme)
        if self.ai_chat_widget:
            self.mm.theme_manager.apply_theme_to_widget(self.ai_chat_widget, theme)
        
        # Apply theme to all dock widgets
        for dock in self.findChildren(QDockWidget):
            self.mm.theme_manager.apply_theme_to_widget(dock)
        # Apply theme to the menu bar and status bar
        self.mm.theme_manager.apply_theme_to_widget(self.menuBar(), theme)
        if self.statusBar():
            self.mm.theme_manager.apply_theme_to_widget(self.statusBar(), theme)
# Apply theme to specific widgets
        widgets_to_theme = [
            self.file_tree_view,
            self.ai_chat_widget,
            self.menuBar(),
            self.statusBar(),
            self.project_manager_widget,  # Add this line
        ] + self.findChildren(QDockWidget)

        for widget in widgets_to_theme:
            if widget:
                try:
                    self.mm.theme_manager.apply_theme_to_widget(widget, theme)
                except Exception as e:
                    logging.error(f"Error applying theme to widget {widget}: {e}")
                    logging.error(traceback.format_exc())

        # Refresh the entire window
        self.update()
    def apply_theme_to_widgets(self, theme):
        widgets_to_theme = [
            self,
            self.file_tree_view,
            self.ai_chat_widget,
            self.menuBar(),
            self.statusBar()
        ] + self.findChildren(QDockWidget)

        for widget in widgets_to_theme:
            if widget:
                try:
                    self.mm.theme_manager.apply_theme_to_widget(widget, theme)
                except Exception as e:
                    logging.error(f"Error applying theme to widget {widget}: {e}")
                    logging.error(traceback.format_exc())

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
        project_name, ok = QInputDialog.getText(self, "New Project", "Enter project name:")
        if ok and project_name:
            project_path = os.path.join(os.path.expanduser("~"), "AuraTextProjects", project_name)
            os.makedirs(project_path, exist_ok=True)
            QMessageBox.information(self, "New Project", f"Created new project: {project_name}\nPath: {project_path}")
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
        many_projects_dialog = QDialog(self)
        many_projects_dialog.setWindowTitle("Open Project")
        many_projects_dialog.setModal(True)

        layout = QVBoxLayout(many_projects_dialog)
        many_projects_widget = self.mm.widget_manager.ManyProjectsManagerWidget(self.mm)
        layout.addWidget(many_projects_widget)

        # Connect the project selection signal
        many_projects_widget.project_selected.connect(self.on_project_selected_from_dialog)

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(many_projects_dialog.accept)
        button_box.rejected.connect(many_projects_dialog.reject)
        layout.addWidget(button_box)

        many_projects_dialog.setLayout(layout)
        many_projects_dialog.exec()

    def on_project_selected_from_dialog(self, vault_name, project_name):
        # This method will be called when a project is selected in the ManyProjectsManagerWidget
        self.switch_project(project_name)
        QMessageBox.information(self, "Project Opened", f"Opened project: {project_name} in vault: {vault_name}")

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

    def toggle_explorer_sidebar(self):
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
            self.mm.editor_manager.close_tab(0)

    def fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def on_vault_switch(self, new_vault_path):
        # Update any necessary state or UI elements
        self.update_vault_related_ui(new_vault_path)
        self.file_explorer.set_root_path(new_vault_path)

    def open_vault_dialog(self):
        path = QFileDialog.getExistingDirectory(self, "Select Vault Directory")
        if path:
            if self.mm.switch_vault(path):
                QMessageBox.information(self, "Vault Switched", f"Switched to vault: {path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to switch vault")


    def create_projects_manager_widget(self):
        self.projects_manager_widget = ProjectManagerWidget(parent=self, cccore=self.mm , window=self)
        self.projects_manager_dock = self.mm.widget_manager.add_dock_widget(self.projects_manager_widget, "Projects Manager", Qt.DockWidgetArea.LeftDockWidgetArea)
    def show_recent_projects_menu(self):
        self.recent_projects_menu.exec(self.recent_projects_button.mapToGlobal(self.recent_projects_button.rect().bottomLeft()))

    
    def add_project(self):
        name, ok = QInputDialog.getText(self, "Add Project", "Enter project name:")
        if ok and name:
            path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
            if path:
                if self.mm.project_manager.add_project(project_name=name, project_path=path):
                    self.project_selector.addItem(name)
                    QMessageBox.information(self, "Success", f"Project '{name}' added successfully.")
                else:
                    QMessageBox.warning(self, "Error", f"Project '{name}' already exists.")

    def remove_project(self):
        current_project = self.project_selector.currentText()
        if current_project:
            reply = QMessageBox.question(self, "Remove Project", f"Are you sure you want to remove the project '{current_project}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self.mm.project_manager.remove_project(current_project):
                    index = self.project_selector.findText(current_project)
                    self.project_selector.removeItem(index)
                    QMessageBox.information(self, "Success", f"Project '{current_project}' removed successfully.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to remove project '{current_project}'.")

    
    def load_project_state(self, project_name):
        open_files = self.mm.settings_manager.get_value(f"open_files_{project_name}", [])
        for file_path in open_files:
            self.mm.editor_manager.open_file(file_path)
    def update_vault_selector(self):
        if self.vault_selector is not None:
            self.vault_selector.clear()
            vault_names = self.mm.vault_manager.get_vault_names()
            self.vault_selector.addItems(vault_names)
            current_vault = self.mm.vault_manager.get_current_vault()
            if current_vault:
                self.vault_selector.setCurrentText(current_vault.name)
   
    def switch_project(self, project_name):
        if self.mm.project_manager.set_current_project(project_name):
            project_path = self.mm.project_manager.get_project_path(project_name)
            self.update_project_related_ui(project_path)
            self.load_project_state(project_name)
        else:
            QMessageBox.warning(self, "Error", "Failed to switch project")

    def update_project_related_ui(self, project_path):
        # Update file explorer to show the new project path
        if project_path and os.path.exists(project_path):
            self.file_system_model.setRootPath(project_path)
            self.file_tree_view.setRootIndex(self.file_system_model.index(project_path))
        else:
            logging.warning(f"Project path does not exist: {project_path}")
   # Update any other UI elements that depend on the current project
        # For example, update workspace selector, open files, etc.
    def update_explorer_views(self):
        root_path = self.mm.vault_manager.get_vault_path()
        if root_path and os.path.exists(root_path):
            self.file_system_model.setRootPath(root_path)
            self.vault_explorer.set_root_path(root_path)
            self.file_explorer.set_root_path(root_path)
        else:
            default_path = os.path.expanduser("~")
            self.file_system_model.setRootPath(default_path)
            self.file_explorer.set_root_path(default_path)
            self.vault_explorer.set_root_path(default_path)

    def closeEvent(self, event):
        self.mm.project_manager.save_current_project_state()
        super().closeEvent(event)

    def update_explorer_views(self):
        self.mm.file_manager.update_explorer_views(self.file_tree_view)
    
   
    
    def rename_vault(self):
        vault_names = self.mm.vault_manager.get_vault_names()
        old_name, ok = QInputDialog.getItem(self, "Rename Vault", "Select vault to rename:", vault_names, 0, False)
        if ok and old_name:
            new_name, ok = QInputDialog.getText(self, "Rename Vault", "Enter new vault name:")
            if ok and new_name:
                if self.mm.vault_manager.rename_vault(old_name, new_name):
                    QMessageBox.information(self, "Vault Renamed", f"Renamed vault from '{old_name}' to '{new_name}'")
                    self.update_vault_selector()
                else:
                    QMessageBox.warning(self, "Error", "Failed to rename vault. New name may already exist.")

    
    
    
    
    def add_current_file_to_fileset(self):
        current_editor = self.mm.editor_manager.current_editor
        if current_editor and current_editor.file_path:
            fileset_name, ok = QInputDialog.getText(self, "Add to Fileset", "Enter fileset name:")
            if ok and fileset_name:
                self.tab_widget.add_to_fileset(fileset_name, current_editor.file_path)
                self.update_fileset_selector()
                QMessageBox.information(self, "File Added", f"Added {current_editor.file_path} to fileset {fileset_name}")
        else:
            QMessageBox.warning(self, "Error", "No file is currently open")

    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.show_radial_menu(event.pos())
        else:
            super().mousePressEvent(event)

    def show_radial_menu(self, pos):
        global_pos = self.mapToGlobal(pos)
        context = self.get_radial_menu_context(pos)
        
        if self.radial_menu is None:
            self.radial_menu = self.create_radial_menu(context)
        
        if self.radial_menu:
            self.radial_menu.popup(global_pos)
            logging.info(f"Radial menu shown at {global_pos} with context: {context}")
        else:
            logging.warning("Radial menu is None")

    def get_radial_menu_context(self, pos):
        widget = self.childAt(pos)
        if isinstance(widget, CodeEditor):
            return "editor"
        elif isinstance(widget, QTreeView):  # Assuming your file explorer is a QTreeView
            return "file_explorer"
        elif isinstance(widget, TabWidget):
            return "tab_bar"
        # Add more contexts as needed
        return "default"

    def create_radial_menu(self, context):
        menu = QMenu(self)
        
        if context == "editor":
            menu.addAction("Cut", self.action_handlers.cut)
            menu.addAction("Copy", self.action_handlers.copy)
            menu.addAction("Paste", self.action_handlers.paste)
            menu.addAction("Format Code", self.action_handlers.format_code)
        elif context == "file_explorer":
            menu.addAction("New File", self.action_handlers.new_file)
            menu.addAction("New Folder", self.action_handlers.new_folder)
            menu.addAction("Rename", self.action_handlers.rename_file)
            menu.addAction("Delete", self.action_handlers.delete_file)
        elif context == "tab_bar":
            menu.addAction("Close Tab", self.action_handlers.close_current_tab)
            menu.addAction("Close Other Tabs", self.action_handlers.close_other_tabs)
            menu.addAction("Close All Tabs", self.action_handlers.close_all_tabs)
        else:
            menu.addAction("New File", self.action_handlers.new_file)
            menu.addAction("Open File", self.action_handlers.open_file)
            menu.addAction("Save", self.action_handlers.save_file)
            menu.addAction("Save As", self.action_handlers.save_file_as)

        return menu

    def refresh_after_theme_change(self):
        # Refresh any elements that need special handling after a theme change
        # For example, update syntax highlighting, refresh file icons, etc.
        #self.refresh_syntax_highlighting()
        self.update_file_icons()
        # Add any other necessary refresh operations
    def create_blank_editor(self):
        editor = self.editor_manager.create_new_editor_tab()
        self.tab_widget.addTab(editor, "Untitled")
        self.tab_widget.setCurrentWidget(editor)
    def refresh_current_editor(self):
        current_editor = self.mm.editor_manager.current_editor
        if current_editor:
            current_editor.update()
    def update_file_icons(self):
        # Implement this method to update file icons if needed
        pass

    def open_file_from_explorer(self, file_path):
        self.mm.file_manager.open_file(file_path)

    def open_file(self, file_path):
        if hasattr(self, 'file_tree_view'):
            self.open_file_from_explorer(file_path)
        else:
            print(f"Cannot open file: {file_path}. No file_tree_view found.")

    
    def on_vault_switch(self, new_vault_path):
         # Update any necessary state or UI elements
        self.update_vault_related_ui(new_vault_path)
        self.file_explorer.set_root_path(new_vault_path)
        self.update_explorer_views()
    def on_project_switch(self, new_project_path):
        self.update_explorer_views()

   
    def on_workspace_changed(self, new_workspace_path):
        new_workspace_name = self.mm.workspace_manager.switch_workspace(new_workspace_path)
        self.mm.workspace_manager.set_active_workspace(new_workspace_name)
        logging.info(f"Workspace changed to: {new_workspace_path}")
        self.update_explorer_views()
    def closeEvent(self, event):
        self.save_current_project_state()
        super().closeEvent(event)

    def save_current_project_state(self):
        current_project = self.mm.project_manager.get_current_project()
        if current_project:
            self.mm.project_manager.add_recent_project(current_project)
        
        # Save open files for the current project
        open_files = self.mm.editor_manager.get_open_files()
        self.mm.settings_manager.set_value(f"open_files_{current_project}", open_files)

        self.mm.project_manager.save_projects()

    
    def update_recent_projects_menu(self):
        if self.recent_projects_menu is None:
            return
        
        self.recent_projects_menu.clear()
        recent_projects = self.mm.project_manager.get_recent_projects()
        for project in recent_projects:
            action = self.recent_projects_menu.addAction(project)
            action.triggered.connect(lambda checked, p=project: self.open_recent_project(p))
   
  
    def create_environment_manager_widget(self):
        env_widget = QWidget()
        layout = QVBoxLayout(env_widget)

        self.env_list = QListWidget()
        self.update_env_list()

        create_env_button = QPushButton("Create Environment")
        create_env_button.clicked.connect(self.create_environment)

        delete_env_button = QPushButton("Delete Environment")
        delete_env_button.clicked.connect(self.delete_environment)

        layout.addWidget(self.env_list)
        layout.addWidget(create_env_button)
        layout.addWidget(delete_env_button)

        return env_widget

    def update_env_list(self):
        self.env_list.clear()
        for env in self.mm.env_manager.environments:
            self.env_list.addItem(env)

    def create_environment(self):
        name, ok = QInputDialog.getText(self, "Create Environment", "Enter environment name:")
        if ok and name:
            language, ok = QInputDialog.getItem(self, "Select Language", "Choose language:", ["python", "kotlin", "csharp", "elixir"], 0, False)
            if ok:
                version, ok = QInputDialog.getText(self, "Enter Version", "Enter version:")
                if ok:
                    self.mm.env_manager.create_environment(name, language, version)
                    self.update_env_list()

    def delete_environment(self):
        selected = self.env_list.currentItem()
        if selected:
            reply = QMessageBox.question(self, "Delete Environment", f"Are you sure you want to delete {selected.text()}?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.mm.env_manager.delete_environment(selected.text())
                self.update_env_list()
    

    
    def handle_terminal_command(self, command):
        # Handle the command if neede
        
        logging.info(f"Terminal command: {command}")
        pass

    def handle_terminal_error(self, error_message):
        logging.error(f"Terminal error: {error_message}")
        # You might want to display this error in the UI as well
        QMessageBox.warning(self, "Terminal Error", error_message)
    
    def initialize_project(self):
        last_project = self.mm.settings_manager.get_value("last_project", "")
        if last_project:
            self.switch_project(last_project)
        else:
            logging.info("No last project found. Skipping project initialization.")

    def add_dock_widget(self, dock, name, area):
        if dock is not None:
            self.addDockWidget(area, dock)
        else:
            logging.error(f"Failed to add dock widget: {name}")

    def toggle_project_manager(self):
        if hasattr(self, 'project_manager_dock'):
            if self.project_manager_dock.isVisible():
                self.project_manager_dock.hide()
            else:
                self.project_manager_dock.show()
        else:
            self.project_manager_dock = QDockWidget("Project Manager", self)
            self.project_manager_widget = ProjectManagerWidget(self, cccore=self.mm)
            self.project_manager_dock.setWidget(self.project_manager_widget)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.project_manager_dock)
    def refresh_vault_index(self):
        if self.current_vault:
            self.current_vault.update_index()
    def load_vault(self, vault_path):
        if self.mm.vault_manager:
            self.current_vault = self.mm.vault_manager.get_vault_by_path(vault_path)
            if self.current_vault:
                self.update_ui_for_vault()
                self.refresh_vault_explorer()
            else:
                logging.warning(f"No vault found at path: {vault_path}")
        else:
            logging.error("Vault manager not initialized")
        return self.current_vault
    def create_toolbar_button(self, text, icon_path):
        button = QToolButton()
        button.setText(text)
        button.setIcon(QIcon(icon_path))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        return button
    
    def refresh_vault_explorer(self):
        logging.debug(f"Refreshing vault explorer. Current vault: {self.current_vault}")
        if hasattr(self, 'vault_explorer') and self.current_vault:
            logging.debug(f"Vault path: {self.current_vault.path}, Type: {type(self.current_vault.path)}")
            model = QFileSystemModel()
            vault_path = str(self.current_vault.path)  # Convert WindowsPath to string
            logging.debug(f"Converted vault path: {vault_path}, Type: {type(vault_path)}")
            model.setRootPath(vault_path)
            self.vault_explorer.setup_model(model)
            
            # Use str(vault_path) to ensure we're passing a string
            index = model.index(str(vault_path))
            if index.isValid():
                self.vault_explorer.set_root_index(index)
                logging.debug("Successfully set root index for vault explorer")
            else:
                logging.error(f"Invalid index for vault path: {vault_path}")
        else:
            logging.warning("Cannot refresh vault explorer: No current vault or vault explorer.")
            # Update any UI elements that depend on the index
   
    def setup_project_selector(self):
        self.project_selector = QComboBox()
        self.project_selector.currentTextChanged.connect(self.on_project_changed)
        
        project_widget = QWidget()
        project_layout = QHBoxLayout(project_widget)
        project_layout.setContentsMargins(0, 0, 0, 0)
        project_layout.addWidget(QLabel("Project:"))
        project_layout.addWidget(self.project_selector)
        
        self.toolbar.addWidget(project_widget)

    def on_vault_changed(self, vault_name):
        self.mm.vault_manager.set_current_vault(vault_name)
        self.update_project_selector(vault_name)
        
        self.refresh_file_explorer()
        self.refresh_vault_explorer()
    def on_project_changed(self, project_name):
        self.mm.project_manager.set_current_project(project_name)
        self.mm.project_manager.add_recent_project(project_name)
        self.refresh_file_explorer()
        self.update_recent_projects_menu()
        

    def refresh_file_explorer(self):
        current_vault = self.mm.vault_manager.get_current_vault()
        if current_vault and hasattr(self, 'file_explorer'):
            vault_path = str(current_vault.path)
            logging.warning(f"Refreshing file explorer with path: {vault_path}")
            try:
                self.file_explorer.set_root_path(vault_path)
            except Exception as e:
                logging.error(f"Error setting root path for file explorer: {str(e)}")
    def add_project_selector_to_menu_bar(self):
        self.project_selector = QComboBox()
        self.project_selector.setFixedWidth(200)
        self.project_selector.currentTextChanged.connect(self.on_project_changed)
        
        project_selector_action = QWidgetAction(self)
        project_selector_action.setDefaultWidget(self.project_selector)
        
        self.menubar.addAction(project_selector_action)
        
        self.update_project_selector()

    def create_project_selector_toolbar(self):
        self.project_toolbar = QToolBar("Project Selector")
        self.addToolBar(self.project_toolbar)

        selector_widget = QWidget()
        layout = QHBoxLayout(selector_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.vault_selector = QComboBox()
        layout.addWidget(QLabel("Vault:"))
        layout.addWidget(self.vault_selector)

        self.project_selector = QComboBox()
        layout.addWidget(QLabel("Project:"))
        layout.addWidget(self.project_selector)

        self.project_toolbar.addWidget(selector_widget)
        
        self.vault_selector.currentTextChanged.connect(self.on_vault_changed)
        self.project_selector.currentTextChanged.connect(self.on_project_changed)

        self.update_vault_selector()
    def update_ui_for_project(self, project_name):
        self.setWindowTitle(f"AuraTextIDE - {project_name}")
        # Update other UI elements as needed for the project
        # For example, you might want to update the file explorer, open relevant files,

    
    def update_project_selector(self, vault_name=None):
        if self.project_selector is not None:
            self.project_selector.clear()
            if vault_name:
                projects = self.mm.vault_manager.get_projects(vault_name)
            else:
                projects = self.mm.project_manager.get_all_projects()
            logging.warning(f"Projects for vault {vault_name}: {projects}")
            self.project_selector.addItems(projects)
            
            current_project = self.mm.project_manager.get_current_project()
            if current_project:
                index = self.project_selector.findText(current_project)
                if index >= 0:
                    self.project_selector.setCurrentIndex(index)
        self.update_recent_projects_menu()
     # Update the ProjectsManagerWidget if it exists
        if self.projects_manager_widget is not None:
            self.projects_manager_widget.update_project_list()
    def open_file_from_chat(self, file_path):
        self.mm.editor_manager.open_file(file_path)
    
    def open_daily_note(self):
        if not self.mm.vault_manager.get_current_vault():
            QMessageBox.warning(self, "No Vault", "Please select a vault first.")
            return

        current_vault = self.mm.vault_manager.get_current_vault()
        daily_notes_folder = os.path.join(current_vault.path, "Daily Notes")
        os.makedirs(daily_notes_folder, exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")
        file_name = f"{today}.md"
        file_path = os.path.join(daily_notes_folder, file_name)

        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Daily Note for {today}\n\n")
        else:#
            #file exists no op
            pass
        self.mm.editor_manager.open_file(file_path)

    def fade_in(self):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()
    def toggle_terminal(self):
        if hasattr(self, 'terminal'):
            self.terminal.setVisible(not self.terminal.isVisible())
        else:
            # Create and show terminal if it doesn't exist
            pass  # Implement terminal

    def create_new_tab(self, file_path=None, content=None):
        if not file_path:
            file_path = "Untitled"
        if content is None:
            content = ""
        
        editor = self.create_editor()
        editor.setText(content)
        
        file_name = os.path.basename(file_path)
        self.tab_widget.addTab(editor, file_name)
        self.tab_widget.setCurrentWidget(editor)
        
        if file_path != "Untitled":
            editor.file_path = file_path
            self.set_language_from_file_path(file_path, editor)

    def show_file_search(self):
        if not self.file_search_widget:
            self.file_search_widget = FileSearchWidget(self.mm.vault_manager, self)
            self.file_search_widget.file_selected.connect(self.open_file_from_search)
        self.file_search_widget.show_search_dialog()

    def open_file_from_search(self, file_path, line_number):
        editor = self.mm.editor_manager.open_file(file_path)
        if editor:
            editor.goto_line(line_number)

    def focus_ai_chat(self):
        if hasattr(self, 'ai_chat_widget') and self.ai_chat_widget:
            self.ai_chat_widget.focus_input()
        else:
            logging.warning("AI Chat widget not found or not initialized")
    def show_loading_indicator(self):
        # Implement this method to show a loading indicator in your UI
        pass

    def hide_loading_indicator(self):
        # Implement this method to hide the loading indicator in your UI
        pass