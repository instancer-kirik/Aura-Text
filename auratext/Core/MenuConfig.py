import importlib
import json
import os
import sys

from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction, QIcon
from .plugin_interface import MenuPluginInterface

local_app_data = os.path.join(os.getenv("LocalAppData"), "AuraText")
cpath = open(f"{local_app_data}/data/CPath_Project.txt", "r+").read()

with open(f"{local_app_data}/data/theme.json", "r") as themes_file:
    _themes = json.load(themes_file)


def configure_menuBar(window):
    
    try:
        menubar = window.menuBar()
   
        
        window.setMenuBar(menubar)
  

        whats_this_action = QAction(window)
        whats_this_action.setShortcut("Shift+F1")
        menubar.addAction(whats_this_action)
        file_menu = QMenu("&File", window)
        file_menu.addAction("New", window.cs_new_document).setWhatsThis("Create a New File")
   
        new_menu = QMenu("New(With Template)", window)
        new_menu.addAction(".html", window.html_temp)
        new_menu.addAction(".py", window.py_temp)
        new_menu.addAction(".cpp", window.cpp_temp)
        new_menu.addAction(".php", window.php_temp)
        new_menu.addAction(".tex", window.tex_temp)
        new_menu.addAction(".java", window.java_temp)

        file_menu.addAction("Open", window.open_document).setWhatsThis("Open an existing file")
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
        file_menu.addAction("Summary", window.summary).setWhatsThis(
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
        language_menu = QMenu("&Languages", prefernces_menu)
        a_menu = QMenu("&A", language_menu)
        b_menu = QMenu("&B", language_menu)
        c_menu = QMenu("&C", language_menu)
        d_menu = QMenu("&D", language_menu)
        e_menu = QMenu("&E", language_menu)
        f_menu = QMenu("&F", language_menu)
        g_menu = QMenu("&G", language_menu)
        h_menu = QMenu("&H", language_menu)
        i_menu = QMenu("&I", language_menu)
        j_menu = QMenu("&J", language_menu)
        k_menu = QMenu("&K", language_menu)
        l_menu = QMenu("&L", language_menu)
        m_menu = QMenu("&M", language_menu)
        n_menu = QMenu("&N", language_menu)
        o_menu = QMenu("&O", language_menu)
        p_menu = QMenu("&P", language_menu)
        q_menu = QMenu("&Q", language_menu)
        r_menu = QMenu("&R", language_menu)
        s_menu = QMenu("&S", language_menu)
        t_menu = QMenu("&T", language_menu)
        u_menu = QMenu("&U", language_menu)
        v_menu = QMenu("&V", language_menu)
        w_menu = QMenu("&W", language_menu)
        x_menu = QMenu("&X", language_menu)
        y_menu = QMenu("&Y", language_menu)
        z_menu = QMenu("&Z", language_menu)

        action_py = QAction("Python", window, checkable=True)
        action_py.triggered.connect(window.python)
        window.action_group.addAction(action_py)

        action_cpp = QAction("C++", window, checkable=True)
        action_cpp.triggered.connect(window.cpp)
        window.action_group.addAction(action_cpp)

        action_java = QAction("Java", window, checkable=True)
        action_java.triggered.connect(window.java)
        window.action_group.addAction(action_java)

        action_fortran = QAction("Fortran", window, checkable=True)
        action_fortran.triggered.connect(window.fortran)
        window.action_group.addAction(action_fortran)

        action_js = QAction("JavaScript", window, checkable=True)
        action_js.triggered.connect(window.javascript)
        window.action_group.addAction(action_js)

        action_bash = QAction("Bash", window, checkable=True)
        action_bash.triggered.connect(window.bash)
        window.action_group.addAction(action_bash)

        action_csharp = QAction("C#", window, checkable=True)
        action_csharp.triggered.connect(window.csharp)
        window.action_group.addAction(action_csharp)

        action_ruby = QAction("Ruby", window, checkable=True)
        action_ruby.triggered.connect(window.ruby)
        window.action_group.addAction(action_ruby)

        action_pascal = QAction("Pascal", window, checkable=True)
        action_pascal.triggered.connect(window.pascal)
        window.action_group.addAction(action_pascal)

        action_perl = QAction("Perl", window, checkable=True)
        action_perl.triggered.connect(window.perl)
        window.action_group.addAction(action_perl)

        action_mk = QAction("MakeFile", window, checkable=True)
        action_mk.triggered.connect(window.makefile)
        window.action_group.addAction(action_mk)

        action_md = QAction("Markdown", window, checkable=True)
        action_md.triggered.connect(window.markdown)
        window.action_group.addAction(action_md)

        action_html = QAction("HTML", window, checkable=True)
        action_html.triggered.connect(window.html)
        window.action_group.addAction(action_html)

        action_yaml = QAction("YAML", window, checkable=True)
        action_yaml.triggered.connect(window.yaml)
        window.action_group.addAction(action_yaml)

        action_json = QAction("JSON", window, checkable=True)
        action_json.triggered.connect(window.json)
        window.action_group.addAction(action_json)

        action_css = QAction("CSS", window, checkable=True)
        action_css.triggered.connect(window.css)
        window.action_group.addAction(action_css)

        action_batch = QAction("Batch", window, checkable=True)
        action_batch.triggered.connect(window.batch)
        window.action_group.addAction(action_batch)

        action_avs = QAction("AVS", window, checkable=True)
        action_avs.triggered.connect(window.avs)
        window.action_group.addAction(action_avs)

        action_asm = QAction("ASM", window, checkable=True)
        action_asm.triggered.connect(window.asm)
        window.action_group.addAction(action_asm)

        action_cmake = QAction("CMake", window, checkable=True)
        action_cmake.triggered.connect(window.cmake)
        window.action_group.addAction(action_cmake)

        action_postscript = QAction("PostScript", window, checkable=True)
        action_postscript.setIcon(QIcon("Resources/language_icons/logo_postscript.png"))
        action_postscript.triggered.connect(window.postscript)
        window.action_group.addAction(action_postscript)

        action_coffeescript = QAction("CoffeeScript", window, checkable=True)
        action_coffeescript.triggered.connect(window.coffeescript)
        window.action_group.addAction(action_coffeescript)

        # action_srec = QAction("SREC", self, checkable=True)
        # action_srec.triggered.connect(self.srec)
        # self.action_group.addAction(action_srec)

        action_sql = QAction("SQL", window, checkable=True)
        action_sql.triggered.connect(window.sql)
        window.action_group.addAction(action_sql)

        action_lua = QAction("Lua", window, checkable=True)
        action_lua.triggered.connect(window.lua)
        window.action_group.addAction(action_lua)

        # action_idl = QAction("IDL", self, checkable=True)
        # action_idl.triggered.connect(self.idl)
        # self.action_group.addAction(action_idl)

        # action_matlab = QAction("MATLAB", self, checkable=True)
        # action_matlab.triggered.connect(self.matlab)
        # self.action_group.addAction(action_matlab)

        action_spice = QAction("Spice", window, checkable=True)
        action_spice.triggered.connect(window.spice)
        window.action_group.addAction(action_spice)

        action_vhdl = QAction("VHDL", window, checkable=True)
        action_vhdl.triggered.connect(window.vhdl)
        window.action_group.addAction(action_vhdl)

        action_octave = QAction("Octave", window, checkable=True)
        action_octave.triggered.connect(window.octave)
        window.action_group.addAction(action_octave)

        action_fortran77 = QAction("Fortran77", window, checkable=True)
        action_fortran77.triggered.connect(window.fortran77)
        window.action_group.addAction(action_fortran77)

        action_tcl = QAction("Tcl", window, checkable=True)
        action_tcl.triggered.connect(window.tcl)
        window.action_group.addAction(action_tcl)

        action_verilog = QAction("Verilog", window, checkable=True)
        action_verilog.triggered.connect(window.verilog)
        window.action_group.addAction(action_verilog)

        action_tex = QAction("TeX", window, checkable=True)
        action_tex.triggered.connect(window.tex)
        window.action_group.addAction(action_tex)
        
        # p menu
        p_menu.addAction(action_pascal)
        p_menu.addAction(action_perl)
        p_menu.addAction(action_postscript)
        p_menu.addAction(action_py)

        # h menu
        h_menu.addAction(action_html)

        # y menu
        y_menu.addAction(action_yaml)

        # r menu
        r_menu.addAction(action_ruby)

        # v menu
        v_menu.addAction(action_verilog)
        v_menu.addAction(action_vhdl)

        # m menu
        m_menu.addAction(action_mk)
        m_menu.addAction(action_md)
       # m_menu.addAction(action_matlab)

        # c menu
        c_menu.addAction(action_cmake)
        c_menu.addAction(action_coffeescript)
        c_menu.addAction(action_cpp)
        c_menu.addAction(action_csharp)
        c_menu.addAction(action_css)

        # f menu
        f_menu.addAction(action_fortran)
        f_menu.addAction(action_fortran77)

        # b menu
        b_menu.addAction(action_bash)
        b_menu.addAction(action_batch)

        # j menu
        j_menu.addAction(action_java)
        j_menu.addAction(action_js)
        j_menu.addAction(action_json)

        # i menu
    #    i_menu.addAction(action_idl)

        # a menu
        a_menu.addAction(action_asm)
        a_menu.addAction(action_avs)

        # s menu
        s_menu.addAction(action_spice)
        s_menu.addAction(action_sql)
       # s_menu.addAction(action_srec)

        # t menu
        t_menu.addAction(action_tcl)
        t_menu.addAction(action_tex)

        # o menu
        o_menu.addAction(action_octave)

        # l menu
        l_menu.addAction(action_lua)

        language_menu.addMenu(a_menu)
        language_menu.addMenu(b_menu)
        language_menu.addMenu(c_menu)
        # language_menu.addMenu(d_menu)
        # language_menu.addMenu(e_menu)
        language_menu.addMenu(f_menu)
        # language_menu.addMenu(g_menu)
        language_menu.addMenu(h_menu)
        language_menu.addMenu(i_menu)
        language_menu.addMenu(j_menu)
        # language_menu.addMenu(k_menu)
        language_menu.addMenu(l_menu)
        language_menu.addMenu(m_menu)
        # language_menu.addMenu(n_menu)
        language_menu.addMenu(o_menu)
        language_menu.addMenu(p_menu)
        # language_menu.addMenu(q_menu)
        language_menu.addMenu(r_menu)
        language_menu.addMenu(s_menu)
        language_menu.addMenu(t_menu)
        # language_menu.addMenu(u_menu)
        language_menu.addMenu(v_menu)
        # language_menu.addMenu(w_menu)
        # language_menu.addMenu(x_menu)
        language_menu.addMenu(y_menu)
        # language_menu.addMenu(z_menu)

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
        print(f"Plugin directory: {plugin_dir}")
        if os.path.exists(plugin_dir):
            sys.path.append(plugin_dir)
            print(f"Added {plugin_dir} to sys.path")

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
        print(f"Unexpected error in configure_menuBar: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Exiting configure_menuBar function")