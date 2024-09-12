import importlib
import json
import os
import sys
from auratext.Core.Modules import summary
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction, QIcon
from .plugin_interface import MenuPluginInterface
import logging

local_app_data = os.path.join(os.getenv("LocalAppData"), "AuraText")
cpath = open(f"{local_app_data}/data/CPath_Project.txt", "r+").read()

with open(f"{local_app_data}/data/theme.json", "r") as themes_file:
    _themes = json.load(themes_file)

class LanguageMenuManager:
    def __init__(self, window):
        self.window = window
        self.languages = [
            "Python", "C++", "Java", "Fortran", "JavaScript", "Bash", "C#", "Ruby", 
            "Pascal", "Perl", "MakeFile", "Markdown", "HTML", "YAML", "JSON", "SQL", 
            "CSS", "XML", "Lua", "TCL", "Spice", "VHDL", "Octave", "Fortran77", 
            "Verilog", "TeX", "CoffeeScript", "CMake", "Batch", "AVS", "ASM",
            "PostScript"
        ]
        self.icon_path = "Resources/language_icons"

    def create_language_menu(self, parent_menu):
        language_menu = QMenu("&Languages", parent_menu)
        
        submenus = {}
        for lang in self.languages:
            action = QAction(lang, self.window, checkable=True)
            action.triggered.connect(lambda checked, l=lang.lower(): self.window.lexer_manager.apply_lexer(l))
            self.window.action_group.addAction(action)

            # Set icon if available
            icon_path = os.path.join(self.icon_path, f"logo_{lang.lower()}.png")
            if os.path.exists(icon_path):
                action.setIcon(QIcon(icon_path))

            first_letter = lang[0].upper()
            if first_letter not in submenus:
                submenus[first_letter] = QMenu(f"&{first_letter}", language_menu)
                language_menu.addMenu(submenus[first_letter])
            submenus[first_letter].addAction(action)

        return language_menu

def do_configure_menuBar(window):
    
    try:
        menubar = window.menuBar()
   
        
        window.setMenuBar(menubar)
  

        whats_this_action = QAction(window)
        whats_this_action.setShortcut("Shift+F1")
        menubar.addAction(whats_this_action)
        file_menu = QMenu("&File", window)
        file_menu.addAction("New", window.new_document).setWhatsThis("Create a New File")
   
        new_menu = window.menuBar().addMenu("New")
        file_types = [".py", ".cpp"]  # Add more file types as needed
        for file_type in file_types:
            new_menu.addAction(file_type, lambda ft=file_type: window.create_file_from_template(ft))

        file_menu.addAction("Open", window.open_file).setWhatsThis("Open an existing file")
        file_menu.addSeparator()
        file_menu.addAction("New Project", window.new_project).setWhatsThis("Create a new project")
        file_menu.addAction("New Project from VCS", window.gitClone).setWhatsThis("Clone GIT repo")
        file_menu.addAction("Open Project", window.open_project).setWhatsThis("Open an existing project")
        file_menu.addAction("Open Project as Treeview", window.open_project_as_treeview).setWhatsThis(
            "Open an existing project as a treeview dock"
        )
      
        git_menu = QMenu("&Git", window)
        git_menu.addAction("Commit", window.gitCommit)
        git_menu.addAction("Push", window.gitPush)

        def is_git_repo(path):
            return os.path.isdir(os.path.join(path, '.git'))

        file_menu.addMenu(new_menu)
        file_menu.addSeparator()

        file_menu.addAction("Save As", window.save_document).setWhatsThis("Save the document")
        file_menu.addSeparator()
        file_menu.addAction("Summary", summary).setWhatsThis(
            "Get basic info of a file (Eg: Number of lines)"
        )
        file_menu.addSeparator()
        file_menu.addAction("Settings", window.expandSidebar__Settings)
        file_menu.addAction("Exit", sys.exit).setWhatsThis("Exit Aura Text")
        menubar.addMenu(file_menu)

        whats_this_action.setWhatsThis("Click on a menu item to see its help text")
        whats_this_action.setShortcut("Shift+F1")

        edit_menu = QMenu("&Edit", window)
        edit_menu.addAction("Cut               ", window.cut_document).setWhatsThis("Cut selected text")
        edit_menu.addAction("Copy", window.copy_document).setWhatsThis("Copy selected text")
        edit_menu.addAction("Paste", window.paste_document).setWhatsThis("Paste selected text")
        edit_menu.addAction("Undo Changes", window.undo_document).setWhatsThis("Undo last edit")
        edit_menu.addAction("Redo Changes", window.redo_document).setWhatsThis("Redo last edit")
        edit_menu.addSeparator()
        # edit_menu.addAction("Duplicate Line", self.duplicate_line).setWhatsThis("Duplicate a line to another line")
        # edit_menu.addAction("Reverse Line",).setWhatsThis("Reverse the alphabets of a line (Eg: Hello -->  olleH")
        # edit_menu.addSeparator()
        edit_menu.addAction("Find ", window.find_in_editor).setWhatsThis("Find a specific word inside the editor")
        menubar.addMenu(edit_menu)

        view_menu = QMenu("&View", window)
        view_menu.addAction("Full Screen", window.fullscreen).setWhatsThis("Makes the window full screen")
        view_menu.addAction("Project Directory", window.expandSidebar__Explorer).setWhatsThis(
            "Shows the files and folder in your project as treeview"
        )
        view_menu.addSeparator()
        #view_menu.addAction("AT Terminal", self.terminal_widget)
        #view_menu.addAction("Python Console", self.python_console)

        def toggle_terminal():
            if toggle_terminal_action.isChecked():
                window.terminal_widget()
            else:
                window.hideTerminal()


        def toggle_pyconsole():
            if toggle_pyconsole_action.isChecked():
                window.python_console()
            else:
                window.hide_pyconsole()
   
        toggle_terminal_action = QAction("AT Terminal", window)
        toggle_terminal_action.setCheckable(True)
        toggle_terminal_action.triggered.connect(toggle_terminal)
        view_menu.addAction(toggle_terminal_action)
     
        view_menu.addAction("Powershell", window.setupPowershell)

        toggle_pyconsole_action = QAction("Python Console", window)
        toggle_pyconsole_action.setCheckable(True)
        toggle_pyconsole_action.triggered.connect(toggle_pyconsole)
        view_menu.addAction(toggle_pyconsole_action)

        def read_only():
            if toggle_read_only_action.isChecked():
                window.toggle_read_only()
            else:
                window.read_only_reset()


        toggle_read_only_action = QAction("Read-Only", window)
        toggle_read_only_action.setCheckable(True)
        toggle_read_only_action.triggered.connect(read_only)
        view_menu.addAction(toggle_read_only_action)
        menubar.addMenu(view_menu)

        code_menu = QMenu("&Code", window)
        snippet_menu = QMenu("&Code Snippets", window)
        snippet_menu.addAction("Create a Code Snippet from the Selection", window.create_snippet)
        snippet_menu.addAction("Import a Code Snippet", window.import_snippet)
        code_menu.addAction("Code Formatting", window.code_formatting).setWhatsThis(
            "Beautifies and Formats the code in your current tab with pep-8 standard"
        )
        code_menu.addAction("Boilerplates", window.boilerplates)
        code_menu.addMenu(snippet_menu)
        menubar.addMenu(code_menu)

        tools_menu = QMenu("&Tools", window)
        
        tools_menu.addAction("Upload to Pastebin", window.pastebin).setWhatsThis(
            "Uploads the entire text content in your current editor to Pastebin and automatically copies the link"
        )
        tools_menu.addAction("Notes", window.notes).setWhatsThis(
            "Creates a new dock to write down ideas and temporary stuffs. The contents will be erased if you close the dock or the app"
        )

        menubar.addMenu(tools_menu)
    
        prefernces_menu = QMenu("&Preferences", window)
       
        language_menu_manager = LanguageMenuManager(window)
        language_menu = language_menu_manager.create_language_menu(prefernces_menu)
       
        if is_git_repo(cpath):
            menubar.addMenu(git_menu)
        else:
            pass
            
        prefernces_menu.addMenu(language_menu)
        prefernces_menu.addAction("Additional Preferences", window.additional_prefs)
        prefernces_menu.addAction("Import Theme", window.import_theme)
        menubar.addMenu(prefernces_menu)

        help_menu = QMenu("&Help", window)
        help_menu.addAction("Keyboard Shortcuts", window.shortcuts).setWhatsThis(
            "List of Keyboard Shortcuts supported by Aura Text"
        )
        help_menu.addAction("Getting Started", window.getting_started).setWhatsThis(
            "Manuals and tutorials on how to use Aura Text"
        )
        help_menu.addAction("Submit a Bug Report", window.bug_report).setWhatsThis(
            "Submit a bug report if you've faced any bug(s)"
        )
        help_menu.addAction("A Byte of Humour!", window.code_jokes).setWhatsThis(
            "Shows a joke to cheer you up!"
        )
        help_menu.addSeparator()
        help_menu.addAction("GitHub", window.about_github).setWhatsThis("GitHub repository")
        help_menu.addAction(
            "Contribute to Aura Text",
        ).setWhatsThis("For developers who are looking forward to make Aura Text even better")
        help_menu.addAction("Join Discord Server", window.discord).setWhatsThis(
            "Join Aura Text's Discord server"
        )
        help_menu.addAction("Buy Me A Coffee", window.buymeacoffee).setWhatsThis(
            "Donate to Aura Text developer"
        )
        help_menu.addAction("About", window.version).setWhatsThis("Shows current version of Aura Text")
        menubar.addMenu(help_menu)

        # Define a dictionary to map section names to corresponding QMenu instances
        sections = {
            "File": file_menu,
            "Edit": edit_menu,
            "View": view_menu,
            "Code": code_menu,
            "Tools": tools_menu,
            "Git": None,
            "Preferences": prefernces_menu,
            "?": help_menu,
        }
     
        if is_git_repo(cpath):
            sections["Git"] = git_menu
   
        # Load and categorize plugin
        plugin_dir = os.path.abspath(f"{local_app_data}/plugins")  # Path to your plugins directory
        logging.debug(f"Plugin directory: {plugin_dir}")
        if os.path.exists(plugin_dir):
            sys.path.append(plugin_dir)
            logging.info(f"Added {plugin_dir} to sys.path")

            for file_name in os.listdir(plugin_dir):
                if file_name.endswith(".py"):
                    plugin_module_name = os.path.splitext(file_name)[0]
                    try:
                      
                        plugin_module = importlib.import_module(plugin_module_name)
                        print(f"Successfully imported {plugin_module_name}")
                        for obj_name in dir(plugin_module):
                            obj = getattr(plugin_module, obj_name)
                            print(f"Checking object: {obj_name}")
                            if (isinstance(obj, type) and 
                                issubclass(obj, MenuPluginInterface) and 
                                obj != MenuPluginInterface):
                            
                                try:
                                    print(f"Creating instance of {obj_name}")
                                    plugin = obj(window.current_editor)
                                    section = plugin.section
                                    
                                    if section in sections:
                                        print(f"Adding menu items for section: {section}")
                                        plugin.add_menu_items(sections[section])
                                        print(f"Added menu items for {obj_name}")
                                    else:
                                        print(f"Section {section} not found in sections")
                                except Exception as e:
                                    print(f"Error creating or using plugin instance {obj_name}: {e}")
                                    import traceback
                                    traceback.print_exc()
                        print(f"Finished processing plugin: {plugin_module_name}")
                    except Exception as e:
                        print(f"Error loading plugin {plugin_module_name}: {e}")
                        import traceback
                        traceback.print_exc()
            print("Finished loading plugins")
        else:
            print(f"Plugin directory does not exist: {plugin_dir}")

        print("About to add submenus to menubar")
        for section, submenu in sections.items():
            if submenu is not None:
                print(f"Adding {section} submenu to menubar")
                menubar.addMenu(submenu)
            else:
                print(f"Skipping {section} submenu (None)")
        print("Finished adding submenus to menubar")

        print("Menu bar configuration completed successfully")
        return menubar
    except Exception as e:
        logging.exception(f"Error in configure_menuBar: {e}")
    finally:
        logging.info("Exiting configure_menuBar function")
