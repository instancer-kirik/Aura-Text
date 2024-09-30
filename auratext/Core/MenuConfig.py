import importlib
import json
import os
import sys
from typing import Dict, Optional
from AuraText.auratext.Core.Modules import ModulesFile
from PyQt6.QtWidgets import QMenu, QWidget, QDockWidget
from PyQt6.QtGui import QAction, QIcon
from .plugin_interface import MenuPluginInterface
import logging
from PyQt6.QtWidgets import QMenuBar
local_app_data = os.path.join(os.getenv("LocalAppData", ""), "AuraText")
cpath = ""
_themes = {}

# try:
#     with open(f"{local_app_data}/data/CPath_Project.txt", "r") as f:
#         cpath = f.read().strip()

#     with open(f"{local_app_data}/data/theme.json", "r") as themes_file:
#         _themes = json.load(themes_file)
# except FileNotFoundError as e:
#     logging.error(f"File not found: {e}")
# except json.JSONDecodeError as e:
#     logging.error(f"JSON decode error: {e}")

class LanguageMenuManager:
    def __init__(self, window: QWidget):
        self.window = window
        self.languages = [
            "Python", "C++", "Java", "Fortran", "JavaScript", "Bash", "C#", "Ruby", 
            "Pascal", "Perl", "MakeFile", "Markdown", "HTML", "YAML", "JSON", "SQL", 
            "CSS", "XML", "Lua", "TCL", "Spice", "VHDL", "Octave", "Fortran77", 
            "Verilog", "TeX", "CoffeeScript", "CMake", "Batch", "AVS", "ASM",
            "PostScript"
        ]
        self.icon_path = "Resources/language_icons"

    def create_language_menu(self, parent_menu: QMenu) -> QMenu:
        language_menu = QMenu("&Languages", parent_menu)
        
        submenus: Dict[str, QMenu] = {}
        for lang in self.languages:
            action = QAction(lang, self.window, checkable=True)
            action.triggered.connect(lambda checked, l=lang.lower(): self.window.lexer_manager.apply_lexer(l))
            self.window.action_group.addAction(action)

            icon_path = os.path.join(self.icon_path, f"logo_{lang.lower()}.png")
            if os.path.exists(icon_path):
                action.setIcon(QIcon(icon_path))

            first_letter = lang[0].upper()
            if first_letter not in submenus:
                submenus[first_letter] = QMenu(f"&{first_letter}", language_menu)
                language_menu.addMenu(submenus[first_letter])
            submenus[first_letter].addAction(action)

        return language_menu

def do_configure_menuBar(window: QWidget, menu_bar: QMenuBar) -> Optional[QMenu]:
    try:
        menubar = menu_bar

        menus = {
            "File": create_file_menu(window),
            "Edit": create_edit_menu(window),
            "View": create_view_menu(window),
            "Code": create_code_menu(window),
            "Tools": create_tools_menu(window),
            "Preferences": create_preferences_menu(window),
            "Help": create_help_menu(window)
        }

        if is_git_repo(cpath):
            menus["Git"] = create_git_menu(window)

        for menu_name, menu in menus.items():
            menubar.addMenu(menu)

        load_plugins(window, menus)

        return menubar
    except Exception as e:
        logging.exception(f"Error in configure_menuBar: {e}")
    finally:
        logging.info("Exiting configure_menuBar function")

def create_file_menu(window: QWidget) -> QMenu:
    file_menu = QMenu("&File", window)
    file_menu.addAction("New", window.action_handlers.new_file).setWhatsThis("Create a New File")
    
    new_menu = QMenu("New", file_menu)
    file_types = [".py", ".cpp"]  # Add more file types as needed
    for file_type in file_types:
        new_menu.addAction(file_type, lambda ft=file_type: window.create_file_from_template(ft))
    file_menu.addMenu(new_menu)

    file_menu.addAction("Open", window.action_handlers.open_file).setWhatsThis("Open an existing file")
    file_menu.addSeparator()
    if hasattr(window, 'new_project'):
        file_menu.addAction("New Project", window.new_project).setWhatsThis("Create a new project")
    if hasattr(window, 'gitClone'):
        file_menu.addAction("New Project from VCS", window.gitClone).setWhatsThis("Clone GIT repo")
    if hasattr(window, 'open_project'):
        file_menu.addAction("Open Project", window.open_project).setWhatsThis("Open an existing project")
    file_menu.addAction("Open Project as Treeview", window.open_project_as_treeview).setWhatsThis("Open an existing project as a treeview dock")
    file_menu.addSeparator()
    file_menu.addAction("Save", window.action_handlers.save_file).setWhatsThis("Save the current file")
    file_menu.addAction("Save As", window.action_handlers.save_file_as).setWhatsThis("Save the current file with a new name")
    file_menu.addAction("Close", window.action_handlers.close_file).setWhatsThis("Close the current file")
    file_menu.addAction("Close All", window.action_handlers.close_all_files).setWhatsThis("Close all open files")
    file_menu.addSeparator()
    file_menu.addAction("Summary", ModulesFile.summary).setWhatsThis("Get basic info of a file (Eg: Number of lines)")
    file_menu.addSeparator()
    # file_menu.addAction("Settings", pr)
    file_menu.addAction("Exit", window.close).setWhatsThis("Exit Aura Text")
    return file_menu

def create_edit_menu(window: QWidget) -> QMenu:
    edit_menu = QMenu("&Edit", window)
    edit_menu.addAction("Cut", window.action_handlers.cut_document).setWhatsThis("Cut selected text")
    edit_menu.addAction("Copy", window.action_handlers.copy_document).setWhatsThis("Copy selected text")
    edit_menu.addAction("Paste", window.action_handlers.paste_document).setWhatsThis("Paste selected text")
    edit_menu.addAction("Undo", window.action_handlers.undo).setWhatsThis("Undo last edit")
    edit_menu.addAction("Redo", window.action_handlers.redo).setWhatsThis("Redo last edit")
    edit_menu.addSeparator()
    #edit_menu.addAction("Find", window.find_in_editor).setWhatsThis("Find a specific word inside the editor")
    edit_menu.addAction("Search", window.show_search_dialog).setWhatsThis("Find a specific word inside the editor")
   
    return edit_menu

def create_view_menu(window: QWidget) -> QMenu:
    view_menu = QMenu("&View", window)
    view_menu.addAction("Full Screen", window.fullscreen).setWhatsThis("Makes the window full screen")
    view_menu.addAction("Project Directory", window.toggle_explorer_sidebar).setWhatsThis("Shows the files and folder in your project as treeview")
    view_menu.addSeparator()

    toggle_terminal_action = QAction("AT Terminal", window)
    toggle_terminal_action.setCheckable(True)
    toggle_terminal_action.triggered.connect(lambda: toggle_terminal(window, toggle_terminal_action))
    view_menu.addAction(toggle_terminal_action)

    view_menu.addAction("Powershell", window.action_handlers.setup_powershell)

    toggle_pyconsole_action = QAction("Python Console", window)
    toggle_pyconsole_action.setCheckable(True)
    toggle_pyconsole_action.triggered.connect(lambda: toggle_pyconsole(window, toggle_pyconsole_action))
    view_menu.addAction(toggle_pyconsole_action)

    toggle_read_only_action = QAction("Read-Only", window)
    toggle_read_only_action.setCheckable(True)
    toggle_read_only_action.triggered.connect(lambda: read_only(window, toggle_read_only_action))
    view_menu.addAction(toggle_read_only_action)

    return view_menu

def create_code_menu(window: QWidget) -> QMenu:
    code_menu = QMenu("&Code", window)
    snippet_menu = QMenu("&Code Snippets", window)
    snippet_menu.addAction("Create a Code Snippet from the Selection", window.action_handlers.create_snippet)
    snippet_menu.addAction("Import a Code Snippet", window.action_handlers.import_snippet)
    code_menu.addAction("Code Formatting", window.action_handlers.code_formatting).setWhatsThis("Beautifies and Formats the code in your current tab with pep-8 standard")
    code_menu.addAction("Boilerplates", window.action_handlers.boilerplates)
    code_menu.addMenu(snippet_menu)
    return code_menu

def create_tools_menu(window: QWidget) -> QMenu:
    tools_menu = QMenu("&Tools", window)
    tools_menu.addAction("Upload to Pastebin", window.action_handlers.pastebin).setWhatsThis("Uploads the entire text content in your current editor to Pastebin and automatically copies the link")
    tools_menu.addAction("Notes", window.action_handlers.notes).setWhatsThis("Creates a new dock to write down ideas and temporary stuffs. The contents will be erased if you close the dock or the app")
 
    return tools_menu

def create_preferences_menu(window: QWidget) -> QMenu:
    preferences_menu = QMenu("&Preferences", window)
    language_menu_manager = LanguageMenuManager(window)
    language_menu = language_menu_manager.create_language_menu(preferences_menu)
    preferences_menu.addMenu(language_menu)
   # preferences_menu.addAction("Additional Preferences", window.additional_prefs)
    preferences_menu.addAction("Import Theme", window.import_theme)
    return preferences_menu

def create_git_menu(window: QWidget) -> QMenu:
    git_menu = QMenu("&Git", window)
    git_menu.addAction("Commit", window.action_handlers.git_commit)
    git_menu.addAction("Push", window.action_handlers.git_push)
    return git_menu

def create_help_menu(window: QWidget) -> QMenu:
    help_menu = QMenu("&Help", window)
    help_menu.addAction("Keyboard Shortcuts", window.action_handlers.show_shortcuts).setWhatsThis("List of Keyboard Shortcuts supported by Aura Text")
    help_menu.addAction("Getting Started", window.action_handlers.getting_started).setWhatsThis("Manuals and tutorials on how to use Aura Text")
    help_menu.addAction("Submit a Bug Report", window.action_handlers.bug_report).setWhatsThis("Submit a bug report if you've faced any bug(s)")
    help_menu.addAction("A Byte of Humour!", window.action_handlers.code_jokes).setWhatsThis("Shows a joke to cheer you up!")
    help_menu.addSeparator()
    help_menu.addAction("GitHub", window.action_handlers.about_github).setWhatsThis("GitHub repository")
    help_menu.addAction("Contribute to Aura Text", window.action_handlers.contribute).setWhatsThis("For developers who are looking forward to make this even better")
    help_menu.addAction("Join Discord Server", window.action_handlers.discord).setWhatsThis("Join Aura Text's Discord server")
    help_menu.addAction("Buy Me A Coffee", window.action_handlers.buymeacoffee).setWhatsThis("Donate to Aura Text developer")
    help_menu.addAction("About", window.action_handlers.version).setWhatsThis("Shows current version of Aura Text")
    return help_menu

def toggle_terminal(window: QWidget, action: QAction) -> None:
    if action.isChecked():
        window.terminal_widget()
    else:
        window.hideTerminal()

def toggle_pyconsole(window: QWidget, action: QAction) -> None:
    if action.isChecked():
        window.python_console()
    else:
        window.hide_pyconsole()

def read_only(window: QWidget, action: QAction) -> None:
    if action.isChecked():
        window.toggle_read_only()
    else:
        window.read_only_reset()

def is_git_repo(path: str) -> bool:
    return os.path.isdir(os.path.join(path, '.git'))

def load_plugins(window: QWidget, sections: Dict[str, QMenu]) -> None:
    plugin_dir = os.path.abspath(f"{local_app_data}/plugins")
    if not os.path.exists(plugin_dir):
        logging.warning(f"Plugin directory does not exist: {plugin_dir}")
        return

    logging.info(f"Loading plugins from directory: {plugin_dir}")
    sys.path.append(plugin_dir)
    for file_name in os.listdir(plugin_dir):
        if not file_name.endswith(".py"):
            continue
        
        plugin_module_name = os.path.splitext(file_name)[0]
        logging.info(f"Skipping Loading plugin module: {plugin_module_name}")
        # try:
        #     plugin_module = importlib.import_module(plugin_module_name)
        #     for obj_name in dir(plugin_module):
        #         obj = getattr(plugin_module, obj_name)
        #         if not (isinstance(obj, type) and issubclass(obj, MenuPluginInterface) and obj != MenuPluginInterface):
        #             continue
                
        #         try:
        #             plugin = obj()#window.mm.current_editor)
        #             section = plugin.section
        #             if section in sections:
        #                 plugin.add_menu_items(sections[section])
        #         except Exception as e:
        #             logging.error(f"Error creating or using plugin instance {obj_name}: {e}")
        # except Exception as e:
        #     logging.error(f"Error loading plugin {plugin_module_name}: {e}")
           
