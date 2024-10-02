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
from HMC.vault_manager import Vault
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
from .theme_manager import ThemeDownloader
from .theme_manager import ThemeManager
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
from PyQt6.QtWidgets import QMenuBar, QToolBar
from PyQt6.QtCore import QDir
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from .file_outline_widget import FileOutlineWidget
from GUX.search_dialog import SearchDialog
from HMC.action_handlers import ActionHandlers
from AuraText.auratext.Core.CodeEditor import CodeEditor
from PyQt6.QtWidgets import QComboBox, QListWidget
from AuraText.auratext.Components.shortcuts_dialog import ShortcutsDialog
local_app_data = os.path.join(os.getenv("LocalAppData"), "AuraText")
cpath = open(f"{local_app_data}/data/CPath_Project.txt", "r+").read()
cfile = open(f"{local_app_data}/data/CPath_File.txt", "r+").read()
from PyQt6.QtGui import QShortcut, QMouseEvent
from GUX.file_tree_view import FileTreeView
from PyQt6.QtWidgets import QStackedWidget
from HMC.project_manager import ProjectsManagerWidget
class CircularTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setUsesScrollButtons(True)
        self.setDocumentMode(True)

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.setCurrentIndex((self.currentIndex() - 1) % self.count())
        else:
            self.setCurrentIndex((self.currentIndex() + 1) % self.count())

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        size.setWidth(min(200, size.width()))  # Limit max width to 200 pixels
        return size

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            if opt.text:
                text_rect = self.style().subElementRect(QStyle.SubElement.SE_TabBarTabText, opt, self)
                painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, opt)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextShowMnemonic, opt.text)
            else:
                painter.drawControl(QStyle.ControlElement.CE_TabBarTab, opt)

class ImprovedTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabBar(CircularTabBar(self))
        self.setTabPosition(QTabWidget.TabPosition.North)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.filesets = {}  # Dictionary to store filesets

    def add_to_fileset(self, fileset_name, file_path):
        if fileset_name not in self.filesets:
            self.filesets[fileset_name] = []
        if file_path not in self.filesets[fileset_name]:
            self.filesets[fileset_name].append(file_path)
        self.update_fileset_tabs()

    def update_fileset_tabs(self):
        self.clear()
        for fileset_name, files in self.filesets.items():
            for file_path in files:
                self.add_new_tab(file_path), os.path.basename(file_path)
        self.addTab(QWidget(), "+")  # Add tab for creating new filesets

class AuraTextWindow(QMainWindow):
    def __init__(self, mm, parent=None):
        super().__init__(parent)
        self.mm = mm
        self.current_vault = None
        if self.mm and self.mm.vault_manager:
            self.current_vault = self.mm.vault_manager.get_current_vault()
        self.action_handlers = mm.action_handlers
        self.setup_ui()

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
            self.update_workspace_selector()

    def update_workspace_selector(self):
        if hasattr(self, 'workspace_selector') and self.current_vault:
            self.workspace_selector.clear()
            workspace_names = self.mm.workspace_manager.get_workspace_names(self.current_vault.path)
            self.workspace_selector.addItems(workspace_names)

 
    def setup_ui(self):
        self.setWindowTitle("AuraText")
        self.setup_menu_bar()
        # Add other UI setup code here (e.g., central widget, status bar, etc.)

    def setup_menu_bar(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        MenuConfig.do_configure_menuBar(self, menubar)

    def set_project(self, project):
        # Implement method to set the current project
        pass

    def __init__(self, parent=None, mm=None):
        super().__init__(parent)
        self.mm = mm
        #STOP DELETING THIS
        self.action_handlers = ActionHandlers(self.mm)#
        #STOP DELETING THIS
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.current_vault = None
        if self.mm and self.mm.vault_manager:
            self.current_vault = self.mm.vault_manager.get_current_vault()
        # Initialize attributes that might be used in setup_menu_bar
        self.project_manager = getattr(mm, 'project_manager', None)
        if self.project_manager is None:
            self.logger.warning("project_manager not found in mm, some features may be limited")
        
        try:
            self.setup_menu_bar()
        except Exception as e:
            self.logger.error(f"Error in setup_menu_bar: {str(e)}")
            self.logger.error(traceback.format_exc())
        
        self.file_system_model = self.mm.file_manager.create_file_system_model()
        self.workspace_selector = None  # Initialize it as None
        self.fileset_selector = None  # Initialize it as None
        self.project_selector = None  # Initialize it as None
        self.setup_ui_components()
        self.setup_connections()
        self.setup_shortcuts()

    def setup_ui_components(self):
        
        self.action_group = QActionGroup(self)
        self.cursor_manager = self.mm.cursor_manager

     
        self.file_tree_view = FileTreeView(self.file_system_model, self)
        self.vault_explorer = FileTreeView(self.file_system_model, self)
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

        # Add more shortcuts as needed
        # ... (other shortcuts)
    
   
    def setup_file_explorer(self):
        self.file_explorer = FileTreeView(self.file_system_model)
        self.file_explorer.file_selected.connect(self.open_file_from_explorer)

        self.vault_explorer = FileTreeView(self.file_system_model)
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

    def open_file_from_explorer(self, file_path):
        self.mm.file_manager.open_file(file_path)
    def toggle_explorer_view(self):
        current_index = self.explorer_stack.currentIndex()
        new_index = 1 if current_index == 0 else 0
        self.explorer_stack.setCurrentIndex(new_index)
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
            settings_manager=self.mm.settings_manager
        )
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
        return index

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
        self.projects_manager_widget = ProjectsManagerWidget(parent=self, cccore=self.mm)
        #self.projects_manager_dock = self.mm.widget_manager.add_dock_widget(self.projects_manager_widget, "Projects Manager", Qt.DockWidgetArea.LeftDockWidgetArea)
    def show_recent_projects_menu(self):
        self.recent_projects_menu.exec(self.recent_projects_button.mapToGlobal(self.recent_projects_button.rect().bottomLeft()))

    
    def add_project(self):
        name, ok = QInputDialog.getText(self, "Add Project", "Enter project name:")
        if ok and name:
            path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
            if path:
                if self.mm.project_manager.add_project(name, path):
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

    
    def update_vault_selector(self):
        if hasattr(self, 'vault_selector'):
            self.vault_selector.clear()
            vault_names = self.mm.vault_manager.get_vault_names()
            self.vault_selector.addItems(vault_names)
            current_vault = self.mm.vault_manager.get_current_vault()
            if current_vault:
                self.vault_selector.setCurrentText(current_vault.name)

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
        self.mm.cursor_manager.set_transparent_cursor()
        self.mm.show_radial_menu(global_pos, context)

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

    def refresh_after_theme_change(self):
        # Refresh any elements that need special handling after a theme change
        # For example, update syntax highlighting, refresh file icons, etc.
        #self.refresh_syntax_highlighting()
        self.update_file_icons()
        # Add any other necessary refresh operations
    def update_file_icons(self):
        # Implement this method to update file icons if needed
        pass

    def open_file_from_explorer(self, file_path):
        self.mm.file_manager.open_file(file_path)

    def toggle_explorer_view(self):
        current_index = self.explorer_stack.currentIndex()
        new_index = 1 if current_index == 0 else 0
        self.explorer_stack.setCurrentIndex(new_index)

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
        self.recent_projects_menu.clear()
        recent_projects = self.mm.project_manager.get_recent_projects()
        for project in recent_projects:
            action = self.recent_projects_menu.addAction(project)
            action.triggered.connect(lambda checked, p=project: self.switch_project(p))
   
  
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
    def update_project_selector(self):
        if self.project_selector is not None:
            self.project_selector.clear()
            projects = self.mm.project_manager.get_projects()
            self.project_selector.addItems(projects)
            current_project = self.mm.project_manager.get_current_project()
            if current_project:
                self.project_selector.setCurrentText(current_project)
        self.update_recent_projects_menu()

    
    def handle_terminal_command(self, command):
        # Handle the command if neede
        
        logging.info(f"Terminal command: {command}")
        pass

    def handle_terminal_error(self, error_message):
        logging.error(f"Terminal error: {error_message}")
        # You might want to display this error in the UI as well
        QMessageBox.warning(self, "Terminal Error", error_message)
    def setup_menu_bar(self):
        self.menubar = self.menuBar()
        
        file_menu = self.menubar.addMenu("File")
        edit_menu = self.menubar.addMenu("Edit")
        view_menu = self.menubar.addMenu("View")
        project_menu = self.menubar.addMenu("Project")

        project_actions = [
            ("New Project", self.new_project),
            ("Open Project", self.open_project),
        ]
        
        if self.project_manager:
            project_actions.append(("Close Project", self.project_manager.close_project))
        else:
            self.logger.warning("project_manager not available, skipping Close Project action")
        
        project_actions.append(("Project Manager", self.toggle_project_manager))
        
        self.add_menu_actions(project_menu, project_actions)

        self.add_menu_actions(file_menu, [
            ("New", self.action_handlers.new_file),
            ("Open", self.action_handlers.open_file),
            ("Save", self.action_handlers.save_file),
        ])

        self.add_menu_actions(edit_menu, [
            ("Cut", self.action_handlers.cut),
            ("Copy", self.action_handlers.copy),
            ("Paste", self.action_handlers.paste),
        ])

        self.add_menu_actions(project_menu, [
            ("New Project", self.new_project),
            ("Open Project", self.open_project),
            ("Close Project", self.mm.project_manager.close_project),
            ("Project Manager", self.toggle_project_manager),
        ])

    def add_menu_actions(self, menu, actions):
        for action_text, action_handler in actions:
            action = QAction(action_text, self)
            action.triggered.connect(action_handler)
            menu.addAction(action)



       

    def setup_toolbar(self):
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        # Add some example actions to the toolbar
        new_action = QAction(QIcon("path/to/new_icon.png"), "New", self)
        self.toolbar.addAction(new_action)

        open_action = QAction(QIcon("path/to/open_icon.png"), "Open", self)
        self.toolbar.addAction(open_action)

        save_action = QAction(QIcon("path/to/save_icon.png"), "Save", self)
        self.toolbar.addAction(save_action)

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
            self.project_manager_widget = ProjectsManagerWidget(self.mm)
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
    def refresh_vault_explorer(self):
        logging.debug(f"Refreshing vault explorer. Current vault: {self.current_vault}")
        if hasattr(self, 'vault_explorer') and self.current_vault:
            logging.debug(f"Vault path: {self.current_vault.path}, Type: {type(self.current_vault.path)}")
            model = QFileSystemModel()
            vault_path = str(self.current_vault.path)  # Convert WindowsPath to string
            logging.debug(f"Converted vault path: {vault_path}, Type: {type(vault_path)}")
            model.setRootPath(vault_path)
            self.vault_explorer.setModel(model)
            
            # Use str(vault_path) to ensure we're passing a string
            index = model.index(str(vault_path))
            if index.isValid():
                self.vault_explorer.setRootIndex(index)
                logging.debug("Successfully set root index for vault explorer")
            else:
                logging.error(f"Invalid index for vault path: {vault_path}")
        else:
            logging.warning("Cannot refresh vault explorer: No current vault or vault explorer.")
            # Update any UI elements that depend on the index