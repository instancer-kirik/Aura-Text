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
sys.path.insert(0, parent_dir)
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
from .theme_manager import ThemeManager, ThemeDownloader
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


# noinspection PyUnresolvedReferences
# no inspection for unresolved references as pylance flags inaccurately sometimes
class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("Starting Window initialization")
        try:
            self.local_app_data = local_app_data
            # self._terminal_history = ""

            # theme file
            with open(f"{local_app_data}/data/theme.json", "r") as themes_file:
                self._themes = json.load(themes_file)

            # config file
            with open(f"{local_app_data}/data/config.json", "r") as config_file:
                self._config = json.load(config_file)

            # terminal history file
            with open(f"{local_app_data}/data/terminal_history.txt", "r+") as thfile:
                self.terminal_history = thfile.readlines()

            # keymap file
            with open(f"{local_app_data}/data/shortcuts.json", "r+") as kmfile:
                self._shortcuts = json.load(kmfile)

            self._config["show_setup_info"] = "False"

            def splashScreen():
                # Splash Screen
                splash_pix = ""
                current_time = datetime.datetime.now().time()
                sunrise_time = current_time.replace(hour=6, minute=0, second=0, microsecond=0)
                sunset_time = current_time.replace(hour=18, minute=0, second=0, microsecond=0)

                # Check which time interval the current time falls into
                if sunrise_time <= current_time < sunrise_time.replace(hour=12):
                    splash_pix = QPixmap(f"{local_app_data}/icons/splash_morning.png")
                elif sunrise_time.replace(hour=12) <= current_time < sunset_time:
                    splash_pix = QPixmap(f"{local_app_data}/icons/splash_afternoon.png")
                else:
                    splash_pix = QPixmap(f"{local_app_data}/icons/splash_night.png")

                splash = QSplashScreen(splash_pix)
                splash.show()
                time.sleep(1)
                splash.hide()

            if self._config["splash"] == "True":
                splashScreen()
            else:
                pass

            logging.info("Setting up UI components")
            self.setup_ui()
            
            logging.info("Configuring menu bar")
            self.configure_menuBar()
            
            logging.info("Loading plugins")
            sys.path.append(f"{local_app_data}/plugins")
            try:
                self.load_plugins()
            except Exception as e:
                logging.exception(f"Error during plugin loading: {e}")
        
            
            logging.info("Showing window")
            self.show()
            
            logging.info("Window initialization complete")
        except Exception as e:
            logging.exception(f"Error during Window initialization: {e}")

    def setup_ui(self):
        logging.info("Starting UI setup")
        try:
            self.tab_widget = TabWidget()

            self.current_editor = ""

            if self._config["explorer_default_open"] == "True":
                self.expandSidebar__Explorer()
            else:
                pass

            if cpath == "" or cpath == " ":
                welcome_widget = WelcomeScreen.WelcomeWidget(self)
                self.tab_widget.addTab(welcome_widget, "Welcome")
            else:
                pass

            self.tab_widget.setTabsClosable(True)

            self.md_dock = QDockWidget("Markdown Preview")
            self.mdnew = QDockWidget("Markdown Preview")
            self.ps_dock = QDockWidget("Powershell")

            # Sidebar
            self.sidebar_main = Sidebar("", self)
            self.sidebar_main.setTitleBarWidget(QWidget())
            self.sidebar_widget = QWidget(self.sidebar_main)
            self.sidebar_widget.setStyleSheet(f"QWidget{{background-color: {self._themes['sidebar_bg']};}}")
            self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
            self.sidebar_main.setWidget(self.sidebar_widget)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar_main)


            self.bottom_bar = QStatusBar()
            # self.setStatusBar(self.bottom_bar)

            self.leftBar = Sidebar("", self)
            self.leftBar.setTitleBarWidget(QWidget())
            self.leftBar_widget = QWidget(self.leftBar)
            self.leftBar_widget.setStyleSheet(f"QWidget{{background-color: {self._themes['sidebar_bg']};}}")
            self.leftBar_layout = QVBoxLayout(self.leftBar_widget)
            self.leftBar_layout.addStretch()
            self.leftBar_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.leftBar.setWidget(self.leftBar_widget)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.leftBar)

            self.statusBar = statusBar.StatusBar(self)
            self.setStatusBar(self.statusBar)

            explorer_icon = QIcon(f"{local_app_data}/icons/explorer_unfilled.png")
            self.explorer_button = QPushButton(self)
            self.explorer_button.setIcon(explorer_icon)
            self.explorer_button.setIconSize(QSize(23, 23))
            self.explorer_button.setFixedSize(28, 28)
            self.explorer_button.setStyleSheet(
                """
                QPushButton {
                    border: none;
                    border-radius: 10px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #4e5157;
                }
                """
            )

            plugin_icon = QIcon(f"{local_app_data}/icons/extension_unfilled.png")
            self.plugin_button = QPushButton(self)
            self.plugin_button.setIcon(plugin_icon)
            self.plugin_button.setIconSize(QSize(21, 21))
            self.plugin_button.setFixedSize(30, 30)
            self.plugin_button.setStyleSheet(
                """
                QPushButton {
                    border: none;
                    border-radius: 10px;
                    text-align: bottom;
                }
                QPushButton:hover {
                    background-color: #4e5157;
                }
                """
            )

            commit_icon = QIcon(f"{local_app_data}/icons/commit_unselected.png")
            self.commit_button = QPushButton(self)
            self.commit_button.setIcon(commit_icon)
            self.commit_button.clicked.connect(self.gitCommit)
            self.commit_button.setIconSize(QSize(25, 25))
            self.commit_button.setFixedSize(30, 30)
            self.commit_button.setStyleSheet(
                """
                QPushButton {
                    border: none;
                    border-radius: 10px;
                    text-align: bottom;
                }
                QPushButton:hover {
                    background-color: #4e5157;
                }
                """
            )

            self.sidebar_layout.insertWidget(0, self.explorer_button)
            self.sidebar_layout.insertWidget(1, self.plugin_button)

            if self.is_git_repo():
                self.sidebar_layout.insertWidget(2, self.commit_button)
            else:
                pass

            self.sidebar_layout.addStretch()
            self.leftBar_layout.addStretch()
            self.leftBar_layout.addSpacing(45)

            # Connect the button's clicked signal to the slot
            self.explorer_button.clicked.connect(self.expandSidebar__Explorer)
            self.plugin_button.clicked.connect(self.expandSidebar__Plugins)

            self.setCentralWidget(self.tab_widget)
            self.editors = []

            if self._config["open_last_file"] == "True":
                if cfile != "" or cfile != " ":
                    self.open_last_file()
                else:
                    pass
            else:
                pass

            self.action_group = QActionGroup(self)
            self.action_group.setExclusive(True)

            self.tab_widget.setStyleSheet("QTabWidget {border: none;}")

            self.tab_widget.currentChanged.connect(self.change_text_editor)
            self.tab_widget.tabCloseRequested.connect(self.remove_editor)
            # self.new_document()
            self.setWindowTitle("Aura Text")
            self.setWindowIcon(QIcon(f"{local_app_data}/icons/icon.ico"))
           
            
            self.showMaximized()

            # Initialize theme manager
            self.theme_manager = ThemeManager(self.local_app_data)
            
            # Apply theme
            self.theme_manager.apply_theme(self)

            # Initialize theme downloader
            self.theme_downloader = ThemeDownloader(self.theme_manager)

            # Set up the main window
            self.setWindowTitle("AuraText")
            self.setGeometry(100, 100, 800, 600)

            # Add a simple label to verify the window is working
            self.label = QLabel("Welcome to AuraText", self)
            self.label.setGeometry(50, 50, 200, 30)

            logging.info("UI setup complete")
        except Exception as e:
            logging.exception(f"Error during UI setup: {e}")

        self.lexer_manager = LexerManager(self)
        self.show()

    def apply_lexer(self, language):
        logging.info(f"Applying lexer for language: {language}")
        if self.current_editor:
            method = getattr(self.lexer_manager, language, None)
            if method:
                method()
            else:
                logging.info(f"No lexer found for language: {language}")
        else:
            logging.warning("No current editor to apply lexer to")

    def create_editor(self):
        logging.info("Entering create_editor method")
        try:
            logging.debug("Attempting to import CodeEditor")
            from .AuraText import CodeEditor
            logging.debug("CodeEditor imported successfully")
            
            logging.debug("Attempting to create CodeEditor instance")
            try:
                editor = CodeEditor(self)
                logging.debug(f"CodeEditor instance created: {editor}")
            except Exception as e:
                logging.exception(f"Error creating CodeEditor instance: {e}")
                return None
            
            if editor is None:
                logging.error("CodeEditor constructor returned None")
                return None
            
            self.current_editor = editor
            logging.info("Editor created and set as current_editor successfully")
            return editor
        except ImportError as ie:
            logging.exception(f"Error importing CodeEditor: {ie}")
        except Exception as e:
            logging.exception(f"Unexpected error in create_editor: {e}")
        
        logging.error("Failed to create editor")
        return None

    def getTextStats(self, widget):
        if isinstance(widget, QTextEdit):
            cursor = widget.textCursor()
            text = widget.toPlainText()
            return (
                cursor.blockNumber() + 1,
                cursor.columnNumber() + 1,
                widget.document().blockCount(),
                len(text.split()),
            )
        elif isinstance(widget, QsciScintilla):
            lineNumber, columnNumber = widget.getCursorPosition()
            text = widget.text()
            return (
                lineNumber + 1,
                columnNumber + 1,
                widget.lines(),
                len(text.split()),
            )

    def updateStatusBar(self):
        currentWidget = self.tab_widget.currentWidget()
        if isinstance(currentWidget, (QTextEdit, QsciScintilla)):
            lineNumber, columnNumber, totalLines, words = self.getTextStats(
                currentWidget
            )
            self.statusBar.updateStats(lineNumber, columnNumber, totalLines, words)

            if self.current_editor == "":
                editMode = "Edit" if not currentWidget.isReadOnly() else "ReadOnly"
                if self.current_editor != "":
                    self.statusBar.updateEditMode(editMode)
                else:
                    pass
            else:
                editMode = "Edit" if not self.current_editor.isReadOnly() else "ReadOnly"
                if self.current_editor != "":
                    self.statusBar.updateEditMode(editMode)
                else:
                    pass

    def load_plugins(self):
        logging.debug("Entering load_plugins method")
        try:
            self.plugins = []
            plugin_dir = f"{local_app_data}/plugins"
            if not os.path.exists(plugin_dir):
                logging.warning(f"Plugin directory does not exist: {plugin_dir}")
                return

            sys.path.insert(0, plugin_dir)
            plugin_files = [f.split(".")[0] for f in os.listdir(plugin_dir) if f.endswith(".py")]
            logging.info(f"Found plugin files: {plugin_files}")
            
            for plugin_file in plugin_files:
                try:
                    self.load_single_plugin(plugin_file)
                except Exception as e:
                    logging.exception(f"Failed to load plugin {plugin_file}: {e}")
        except Exception as e:
            logging.exception(f"Error in load_plugins method: {e}")
        finally:
            logging.debug("Exiting load_plugins method")

    def load_single_plugin(self, plugin_file):
        logging.debug(f"Entering load_single_plugin for {plugin_file}")
        try:
            logging.info(f"Attempting to import plugin: {plugin_file}")
            module = importlib.import_module(plugin_file)
            logging.info(f"Successfully imported {plugin_file}")
            
            for plugin_name, plugin_class in module.__dict__.items():
                if isinstance(plugin_class, type) and issubclass(plugin_class, Plugin) and plugin_class != Plugin:
                    logging.info(f"Found plugin class: {plugin_name}")
                    
                    try:
                        logging.debug(f"Attempting to instantiate {plugin_name}")
                        logging.debug(f"failed plugin_instance = plugin_class(self)")
                        
                       # plugin_instance = plugin_class(self)
                        logging.debug(f"Successfully instantiated {plugin_name}")
                    except Exception as e:
                        logging.exception(f"Error instantiating {plugin_name}: {e}")
                        continue  # Skip to the next plugin if instantiation fails

                    logging.debug(f"Plugin instance created: {type(plugin_instance)}")
                    
                    try:
                        logging.debug(f"Calling initialize for {plugin_name}")
                        plugin_instance.initialize()
                        logging.debug(f"Initialize completed for {plugin_name}")
                    except Exception as e:
                        logging.exception(f"Error initializing {plugin_name}: {e}")
                        continue  # Skip to the next plugin if initialization fails

                    try:
                        logging.debug(f"Attempting to append {plugin_name} to self.plugins")
                        if not hasattr(self, 'plugins'):
                            self.plugins = []
                        self.plugins.append(plugin_instance)
                        logging.info(f"Successfully added {plugin_name} to self.plugins")
                    except Exception as e:
                        logging.exception(f"Error adding {plugin_name} to self.plugins: {e}")

                    logging.info(f"Loaded and initialized plugin: {plugin_name}")
        except Exception as e:
            logging.exception(f"Error loading plugin {plugin_file}: {e}")
        finally:
            logging.debug(f"Exiting load_single_plugin for {plugin_file}")

    def onPluginDockVisibilityChanged(self, visible):
        if visible:
            self.plugin_button.setIcon(QIcon(f"{local_app_data}/icons/extension_filled.png"))
        else:
            self.plugin_button.setIcon(QIcon(f"{local_app_data}/icons/extension_unfilled.png"))

    def onExplorerDockVisibilityChanged(self, visible):
        if visible:
            self.explorer_button.setIcon(QIcon(f"{local_app_data}/icons/explorer_filled.png"))
        else:
            self.explorer_button.setIcon(QIcon(f"{local_app_data}/icons/explorer_unfilled.png"))

    def onCommitDockVisibilityChanged(self, visible):
        if visible:
            self.commit_button.setIcon(QIcon(f"{local_app_data}/icons/commit_selected.png"))
        else:
            self.commit_button.setIcon(QIcon(f"{local_app_data}/icons/commit_unselected.png"))

    def treeview_project(self, path):
        self.dock = QDockWidget("Explorer", self)
        self.dock.visibilityChanged.connect(
            lambda visible: self.onExplorerDockVisibilityChanged(visible)
        )
        # dock.setStyleSheet("QDockWidget { background-color: #191a1b; color: white;}")
        self.dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        tree_view = QTreeView()
        self.model = QFileSystemModel()
        bg = self._themes["sidebar_bg"]
        tree_view.setStyleSheet(
            f"QTreeView {{background-color: {bg}; color: white; border: none; }}"
        )
        tree_view.setModel(self.model)
        tree_view.setRootIndex(self.model.index(path))
        self.model.setRootPath(path)
        self.dock.setWidget(tree_view)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)

        tree_view.setFont(QFont("Consolas"))

        tree_view.setColumnHidden(1, True)  # File type column
        tree_view.setColumnHidden(2, True)  # Size column
        tree_view.setColumnHidden(3, True)  # Date modified column

        tree_view.doubleClicked.connect(self.open_file)

    def expandSidebar__Explorer(self):
        self.dock = QDockWidget("Explorer", self)
        self.dock.setMinimumWidth(200)
        self.dock.visibilityChanged.connect(
            lambda visible: self.onExplorerDockVisibilityChanged(visible)
        )
        self.dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        tree_view = QTreeView()

        self.model = QFileSystemModel()
        bg = self._themes["sidebar_bg"]
        tree_view.setStyleSheet(
            f"QTreeView {{background-color: {bg}; color: white; border: none; }}"
        )
        tree_view.setModel(self.model)
        tree_view.setRootIndex(self.model.index(cpath))
        self.model.setRootPath(cpath)
        self.dock.setWidget(tree_view)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)

        tree_view.setFont(QFont("Consolas"))

        tree_view.setColumnHidden(1, True)  # File type column
        tree_view.setColumnHidden(2, True)  # Size column
        tree_view.setColumnHidden(3, True)  # Date modified column

        tree_view.doubleClicked.connect(self.open_file)

    def create_snippet(self):
        ModuleFile.CodeSnippets.snippets_gen(self.current_editor)

    def import_snippet(self):
        ModuleFile.CodeSnippets.snippets_open(self.current_editor)

    def expandSidebar__Settings(self):
        self.settings_dock = QDockWidget("Settings", self)

        self.settings_dock.setStyleSheet("QDockWidget {background-color : #1b1b1b; color : white;}")
        self.settings_dock.setFixedWidth(200)
        self.settings_widget = config_page.ConfigPage(self)
        self.settings_layout = QVBoxLayout(self.settings_widget)
        self.settings_dock.setWidget(self.settings_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.settings_dock)
        self.splitDockWidget(self.sidebar_main, self.settings_dock, Qt.Orientation.Horizontal)

    def expandSidebar__Plugins(self):
        self.plugin_dock = QDockWidget("Extensions", self)
        self.theme_dock = QDockWidget("Themes", self)
        background_color = (
            self.plugin_button.palette().color(self.plugin_button.backgroundRole()).name()
        )
        if background_color == "#3574f0":
            self.plugin_dock.destroy()
            self.theme_dock.destroy()
        else:
            self.plugin_dock.visibilityChanged.connect(
                lambda visible: self.onPluginDockVisibilityChanged(visible)
            )
            self.plugin_dock.setMinimumWidth(300)
            self.plugin_widget = PluginDownload.FileDownloader(self)
            self.plugin_layout = QVBoxLayout()
            self.plugin_layout.addStretch(1)
            self.plugin_layout.addWidget(self.plugin_widget)
            self.plugin_dock.setWidget(self.plugin_widget)

            self.theme_widget = ThemeDownload.ThemeDownloader(self)
            self.theme_layout = QVBoxLayout()
            self.theme_layout.addStretch(1)
            self.theme_layout.addWidget(self.theme_widget)
            self.theme_dock.setWidget(self.theme_widget)

            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.plugin_dock)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.theme_dock)
            self.tabifyDockWidget(self.theme_dock, self.plugin_dock)

    def new_project(self):
        new_folder_path = filedialog.askdirectory(
            title="Create New Folder", initialdir="./", mustexist=False
        )
        with open(f"{self.local_app_data}/data/CPath_Project.txt", "w") as file:
            file.write(new_folder_path)


    def code_jokes(self):
        a = pyjokes.get_joke(language="en", category="neutral")
        QMessageBox.information(self, "A Byte of Humour!", a)

    def terminal_widget(self):
        self.terminal_dock = QDockWidget("AT Terminal", self)
        terminal_widget = terminal.AuraTextTerminalWidget(self)
        self.terminal_dock.setWidget(terminal_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.terminal_dock)

    def hideTerminal(self):
        self.terminal_dock.hide()

    def setupPowershell(self):
        self.ps_dock = QDockWidget("Powershell")
        self.terminal = powershell.TerminalEmulator()
        self.terminal.setMinimumHeight(100)
        self.ps_dock.setWidget(self.terminal)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.ps_dock)

    def python_console(self):
        self.console_dock = QDockWidget("Python Console", self)
        console_widget = PythonConsole()
        console_widget.eval_in_thread()
        # self.sidebar_layout_Terminal = QVBoxLayout()
        self.console_dock.setWidget(console_widget)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)

    def hide_pyconsole(self):
        self.console_dock.hide()

    def closeEvent(self, event):
        if self.tab_widget.count() > 0:
            reply = QMessageBox.question(
                self,
                "Save File",
                random.choice(ModuleFile.emsg_save_list),
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )
            if reply == QMessageBox.StandardButton.Save:
                self.save_document()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def gitClone(self):
        messagebox = QMessageBox()
        global path
        try:
            from git import Repo

            repo_url, ok = QInputDialog.getText(self, "Git Repo", "URL of the Repository")
            try:
                path = filedialog.askdirectory(title="Repo Path", initialdir="./", mustexist=False)
            except:
                messagebox.setWindowTitle("Path Error"), messagebox.setText(
                    "The folder should be EMPTY! Please try again with an EMPTY folder"
                )
                messagebox.exec()

            try:
                Repo.clone_from(repo_url, path)
                with open(f"{self.local_app_data}/data/CPath_Project.txt", "w") as file:
                    file.write(path)
                messagebox.setWindowTitle("Success!"), messagebox.setText(
                    "The repository has been cloned successfully!"
                )
                messagebox.exec()
                self.treeview_project(path)
            except git.GitCommandError:
                pass

        except ImportError:
            messagebox = QMessageBox()
            messagebox.setWindowTitle("Git Import Error"), messagebox.setText(
                "Aura Text can't find Git in your PC. Make sure Git is installed and has been added to PATH."
            )
            messagebox.exec()

    def markdown_open(self, path_data):
        ModuleFile.markdown_open(self, path_data)

    def markdown_new(self):
        ModuleFile.markdown_new(self)

    def gitCommit(self):
        self.gitCommitDock = GitCommit.GitCommitDock(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.gitCommitDock)

    def gitPush(self):
        self.gitPushDialog = GitPush.GitPushDialog(self)
        self.gitPushDialog.exec()

    def is_git_repo(self):
        return os.path.isdir(os.path.join(cpath, '.git'))
    def save_document(self):
        ModuleFile.savedocument(self)
    def open_file(self, path=None):
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                self.new_document(title=os.path.basename(path))
                logging.info("New document created successfully")
                if self.current_editor:
                    self.current_editor.setText(content)
                    
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

    def new_document(self, checked=False, title="Scratch 1"):
        logging.info(f"Creating new document: {title}")
        try:
            logging.info("Step 1: Creating new editor")
            self.current_editor = self.create_editor()
            if self.current_editor:
                logging.info("Step 2: Adding editor to list and tab widget")
                self.current_editor.textChanged.connect(self.updateStatusBar)
                self.current_editor.cursorPositionChanged.connect(self.updateStatusBar)
                self.editors.append(self.current_editor)
                self.tab_widget.addTab(self.current_editor, title)
                self.tab_widget.setCurrentWidget(self.current_editor)
                self.theme_manager.apply_theme_to_editor(self.current_editor)
                
                logging.info("Step 3: Applying default lexer")
                self.apply_lexer("text")  # Apply a default "text" lexer, or choose another default
                
                logging.info("New document created successfully")
            else:
                logging.error("Failed to create new document: create_editor returned None")
        except Exception as e:
            logging.exception(f"Error creating new document: {e}")

    def custom_new_document(self, title, checked=False):
        self.current_editor = self.create_editor()
        self.current_editor.textChanged.connect(self.updateStatusBar)
        self.current_editor.cursorPositionChanged.connect(self.updateStatusBar)
        self.editors.append(self.current_editor)
        self.tab_widget.addTab(self.current_editor, title)
        if ".html" in title:
            self.html_temp()
        self.tab_widget.setCurrentWidget(self.current_editor)

    def boilerplates(self):
        self.boilerplate_dialog = boilerplates.BoilerPlate(current_editor=self.current_editor)
        self.boilerplate_dialog.show()

    def cs_new_document(self, checked=False):
        text, ok = QInputDialog.getText(None, "New File", "Filename:")
        if text != "":
            ext = text.split(".")[-1]
            self.current_editor = self.create_editor()
            self.current_editor.cursorPositionChanged.connect(self.updateStatusBar)
            self.current_editor.textChanged.connect(self.updateStatusBar)
            self.editors.append(self.current_editor)
            self.tab_widget.addTab(self.current_editor, text)
            if ".html" in text:
                self.html_temp()
                self.apply_lexer("html")
            if ".py" in text:
                self.py_temp()
                self.apply_lexer("python")
            if ".css" in text:
                self.css_temp()
                self.apply_lexer("css")
            if ".php" in text:
                self.php_temp()
            if ".tex" in text:
                self.tex_temp()
                self.apply_lexer("tex")
            if ".java" in text:
                self.java_temp()
                self.apply_lexer("java")
            self.load_plugins()
            if os.path.isfile(f"{local_app_data}/plugins/Markdown.py"):
                self.markdown_new()
            else:
                pass
            self.tab_widget.setCurrentWidget(self.current_editor)
            self.apply_lexer(ext)
        else:
            pass

    def change_text_editor(self, index):
        if index < len(self.editors):
            # Set the previous editor as read-only
            if self.current_editor:
                self.current_editor.setReadOnly(True)

            self.current_editor = self.editors[index]

            self.current_editor.setReadOnly(False)

    def undo_document(self):
        self.current_editor.undo()

    def html_temp(self):
        text = file_templates.generate_html_template()
        self.current_editor.append(text)

    def py_temp(self):
        text = file_templates.generate_python_template()
        if self.current_editor:
            self.current_editor.setText(text)
        else:
            self.new_document(title="Untitled.py")
            self.current_editor.setText(text)
        self.apply_lexer("python")

    def create_file_from_template(self, file_type):
        if file_type == ".py":
            text = file_templates.generate_python_template()
        elif file_type == ".cpp":
            text = file_templates.generate_cpp_template()
        # Add more elif statements for other file types as needed
        else:
            text = ""  # Empty template for unknown file types

        if self.current_editor:
            self.current_editor.setText(text)
        else:
            self.new_document(title=f"Untitled{file_type}")
            self.current_editor.setText(text)
        
        self.apply_lexer(file_type[1:])  # Remove the dot from the file extension

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
    @staticmethod
    def getting_started():
        webbrowser.open_new_tab("https://github.com/rohankishore/Aura-Text/wiki")

    @staticmethod
    def buymeacoffee():
        webbrowser.open_new_tab("https://ko-fi.com/rohankishore")
    def fullscreen(self):
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

    # def fullscreen(self):
    #     if not self.isFullScreen():
    #         self.showFullScreen()
    #     else:
    #         self.showMaximized()

    @staticmethod
    def bug_report():
        webbrowser.open_new_tab("https://github.com/rohankishore/Aura-Text/issues/new/choose")

    @staticmethod
    def discord():
        pass
    
    @staticmethod
    def about_github():
        webbrowser.open_new_tab("https://github.com/rohankishore/Aura-Notes")

    @staticmethod
    def version():
        text_ver = (
                "Aura Text"
                + "\n"
                + "Current Version: "
                + "4.8"
                + "\n"
                + "\n"
                + "Copyright © 2023 Rohan Kishore."
        )
        msg_box = QMessageBox()
        msg_box.setWindowTitle("About")
        msg_box.setText(text_ver)
        msg_box.exec()
