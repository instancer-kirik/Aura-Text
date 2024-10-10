import os
import re
import subprocess

from PyQt6.QtCore import QProcess, Qt, pyqtSignal, QStringListModel
from PyQt6.QtGui import QColor, QFont, QIcon, QKeyEvent, QTextCursor, QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import logging
from PyQt6.QtWidgets import QCompleter, QDialog, QVBoxLayout, QListView,  QPushButton
from AuraText.auratext.scripts.def_path import resource


newTerminalIcon = resource(r"../media/terminal/new.svg")
killTerminalIcon = resource(r"../media/terminal/remove.svg")


class TerminalEmulator(QWidget):
    commandEntered = pyqtSignal(str)
    errorOccurred = pyqtSignal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.setup_toolbar()

        self.terminal = QPlainTextEdit(self)
        self.set_terminal_font()
        self.terminal.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: white;
            }
        """
        )
        self.terminal.keyPressEvent = self.terminal_key_press_event

        self.layout.addWidget(self.terminal)

        self.processes = []
        self.current_process_index = -1

        self.command_history = []
        self.history_index = 0

        self.current_command = ""
        self.prompt = "> "

        self.addNewTab()

        self.local_app_data = os.path.join(os.getenv("LocalAppData"), "AuraText")
        self.history_file = os.path.join(self.local_app_data, "data", "terminal_history.txt")

        # Initialize the completer
        self.completer = QCompleter(self)
        self.completer.setModel(QStringListModel())
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

        self.load_command_history()
        self.update_completer()

    def set_terminal_font(self):
        font_families = [
            "Consolas",
            "Courier New",
            "Monospace",
        ]
        font = QFont(font_families[0], 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.terminal.setFont(font)

    def setup_toolbar(self):
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 0, 5, 0)

        toolbar_layout.addStretch(1)
        self.terminal_selector = QComboBox()
        self.terminal_selector.setStyleSheet("QComboBox { min-width: 150px; }")
        self.terminal_selector.currentIndexChanged.connect(self.switchTab)

        new_terminal_button = QPushButton()
        new_terminal_button.setIcon(QIcon(newTerminalIcon))
        new_terminal_button.setStyleSheet(
            """
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
                color: white;
                border: none;
                padding: 0;
            }
        """
        )
        new_terminal_button.setToolTip("New Terminal")
        new_terminal_button.clicked.connect(self.addNewTab)

        kill_terminal_button = QPushButton()
        kill_terminal_button.setIcon(QIcon(killTerminalIcon))
        kill_terminal_button.setToolTip("Kill Terminal")
        kill_terminal_button.setStyleSheet(
            """
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: transparent;
                color: white;
                border: none;
                padding: 0;
            }
        """
        )
        kill_terminal_button.clicked.connect(self.killCurrentTerminal)

        toolbar_layout.addWidget(self.terminal_selector)
        toolbar_layout.addWidget(new_terminal_button)
        toolbar_layout.addWidget(kill_terminal_button)
        toolbar_layout.addStretch()

        self.layout.addWidget(toolbar)

    def addNewTab(self):
        index = self.terminal_selector.count()
        self.terminal_selector.addItem(f"Terminal {index + 1}")
        process = QProcess(self)
        process.readyReadStandardOutput.connect(self.handle_stdout)
        process.readyReadStandardError.connect(self.handle_stderr)
        self.processes.append(process)
        self.terminal_selector.setCurrentIndex(index)

        local_app_data = os.path.join(os.getenv("LocalAppData"), "AuraText")
        #cpath = open(f"{local_app_data}/data/CPath_Project.txt", "r+").read()
        cpath = ""
        self.start_powershell(index, project_path=cpath)

    def killCurrentTerminal(self):
        if self.current_process_index >= 0:
            self.processes[self.current_process_index].kill()
            self.terminal_selector.removeItem(self.current_process_index)
            del self.processes[self.current_process_index]
            if self.terminal_selector.count() == 0:
                self.addNewTab()
            else:
                self.current_process_index = self.terminal_selector.currentIndex()

    def switchTab(self, index):
        self.current_process_index = index
        self.terminal.clear()
        self.terminal.appendPlainText("> ")

    def closeTab(self, index):
        if self.tabBar.count() > 1:
            self.processes[index].kill()
            del self.processes[index]
            self.tabBar.removeTab(index)
            if index == self.current_process_index:
                self.current_process_index = self.tabBar.currentIndex()

    def start_powershell(self, index, project_path=None):
        powershell_path = self.find_powershell_core()
        if project_path == "":
            project_path = os.getcwd()  # Default to current working directory

        self.processes[index].setWorkingDirectory(project_path)

        if powershell_path:
            self.processes[index].start(powershell_path)
            self.terminal.appendPlainText(
                f"PowerShell Core started at {powershell_path} in directory {project_path}.\n"
                "Type your commands below.\n"
            )
        else:
            self.processes[index].start("powershell.exe")
            self.terminal.appendPlainText(
                f"PowerShell started in directory {project_path}.\n"
                "Type your commands below.\n"
            )

        self.display_prompt()

    def find_powershell_core(self):
        possible_paths = [
            r"C:\Program Files\PowerShell\7\pwsh.exe",
            r"C:\Program Files (x86)\PowerShell\7\pwsh.exe",
            "/usr/local/bin/pwsh",
            "/usr/bin/pwsh",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        try:
            result = subprocess.run(
                ["where", "pwsh"] if os.name == "nt" else ["which", "pwsh"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def handle_stdout(self):
        data = (
            self.processes[self.current_process_index]
            .readAllStandardOutput()
            .data()
            .decode()
        )
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self.insert_colored_text(data)
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        if not data.endswith("\n"):
            self.terminal.insertPlainText("\n")
        self.display_prompt()

    def handle_stderr(self):
        data = (
            self.processes[self.current_process_index]
            .readAllStandardError()
            .data()
            .decode()
        )
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self.insert_colored_text(data, QColor(255, 0, 0))  # Red color for errors
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        if not data.endswith("\n"):
            self.terminal.insertPlainText("\n")
        self.display_prompt()
        self.errorOccurred.emit(data)  # Emit the error signal
        
    def display_prompt(self):
        self.terminal.appendPlainText(self.prompt)
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)

    def insert_colored_text(self, text, default_color=QColor(255, 255, 255)):
        cursor = self.terminal.textCursor()

        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        segments = ansi_escape.split(text)
        codes = ansi_escape.findall(text)

        current_color = default_color
        for i, segment in enumerate(segments):
            if segment:
                format = cursor.charFormat()
                format.setForeground(current_color)
                cursor.setCharFormat(format)
                cursor.insertText(segment)

            if i < len(codes):
                code = codes[i]
                if code == "\x1B[0m":  # Reset
                    current_color = default_color
                elif code.startswith("\x1B[38;2;"):  # RGB color
                    rgb = code[7:-1].split(";")
                    if len(rgb) == 3:
                        current_color = QColor(int(rgb[0]), int(rgb[1]), int(rgb[2]))

        self.terminal.setTextCursor(cursor)

    def terminal_key_press_event(self, event: QKeyEvent):
        cursor = self.terminal.textCursor()

        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.execute_command()
        elif event.key() == Qt.Key.Key_Backspace:
            if len(self.current_command) > 0:
                self.current_command = self.current_command[:-1]
                cursor.deletePreviousChar()
        elif event.key() == Qt.Key.Key_Up:
            self.show_previous_command()
        elif event.key() == Qt.Key.Key_Down:
            self.show_next_command()
        elif event.key() == Qt.Key.Key_Left:
            if cursor.positionInBlock() > len(self.prompt):
                cursor.movePosition(QTextCursor.MoveOperation.Left)
        elif event.key() == Qt.Key.Key_Home:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.MoveAnchor,
                len(self.prompt),
            )
        elif event.key() == Qt.Key.Key_Tab:
            self.handle_tab_completion()
            return
        else:
            if cursor.positionInBlock() >= len(self.prompt):
                self.current_command += event.text()
                QPlainTextEdit.keyPressEvent(self.terminal, event)

        self.update_current_command()

    def execute_command(self):
        command = self.current_command.strip()
        if command:
            if command.startswith(('ctheme', 'ctime', 'cdate', 'joke', 'ascii', 'key', 'cproject', 'cpath')):
                self.handle_custom_command(command)
            else:
                self.terminal.appendPlainText("")
                try:
                    # Modify the command to handle console width issues
                    wrapped_command = f"""
                    try {{
                        $consoleWidth = [System.Console]::WindowWidth
                    }} catch {{
                        $consoleWidth = 120  # Default width if unable to determine
                    }}
                    $ErrorActionPreference = 'Stop'
                    {command} | Out-String -Stream -Width $consoleWidth
                    """
                    self.processes[self.current_process_index].write(wrapped_command.encode() + b'\n')
                except Exception as e:
                    error_message = f"Error executing command: {str(e)}"
                    self.terminal.appendPlainText(error_message)
                    logging.error(error_message)
            
            if command not in self.command_history:
                self.command_history.append(command)
                self.history_index = len(self.command_history)
                self.save_command_history()
                self.update_completer()
            
        self.current_command = ""

    def show_previous_command(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.show_command_from_history()

    def show_next_command(self):
        if self.history_index < len(self.command_history):
            self.history_index += 1
            self.show_command_from_history()

    def show_command_from_history(self):
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        cursor.movePosition(
            QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor
        )
        cursor.removeSelectedText()

        if self.history_index < len(self.command_history):
            self.current_command = self.command_history[self.history_index]
        else:
            self.current_command = ""

        cursor.insertText(f"{self.prompt}{self.current_command}")

    def run_command(self, command):
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
        self.terminal.insertPlainText(f"{self.prompt}{command}\n")
        self.processes[self.current_process_index].write(command.encode() + b"\n")

    def run_file(self, file_path):
        file_name = os.path.basename(file_path)
        self.run_command(file_name)

    def change_directory(self, new_path):
        self.run_command(f"cd '{new_path}'")

    def parse_ansi_codes(self, text):
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    def load_command_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                self.command_history = [line.strip() for line in f.readlines()]
        self.history_index = len(self.command_history)
        self.update_completer()

    def save_command_history(self):
        with open(self.history_file, 'w') as f:
            f.write('\n'.join(self.command_history[-1000:]))  # Save last 1000 commands
        self.update_completer()

    def handle_custom_command(self, command):
        if command == "ctheme":
            self.terminal.appendPlainText(self._window._themes["theme"])
        # elif command == "ctime":
        #     self.terminal.appendPlainText(datetime.now().strftime("%H:%M:%S"))
        # elif command == "cdate":
        #     self.terminal.appendPlainText(str(datetime.now()))
        # elif command == "joke":
        #     self.terminal.appendPlainText(pyjokes.get_joke(language="en", category="neutral"))
        # elif command.startswith("ascii"):
        #     text = command.replace("ascii", "").strip()
        #     self.terminal.appendPlainText(text2art(text))
        elif command.startswith("key"):
            # ... (implement key emulation) ...
            pass
        elif command in ("cproject", "cpath"):
            # ... (implement project path display) ...
            pass

    def show_history_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Terminal History")
        dialog.setMinimumSize(400, 300)

        layout = QVBoxLayout(dialog)
        list_view = QListView(dialog)
        model = QStandardItemModel()
        for cmd in self.command_history:
            item = QStandardItem(cmd)
            model.appendRow(item)
        list_view.setModel(model)
        layout.addWidget(list_view)

        clear_button = QPushButton("Clear History", dialog)
        clear_button.clicked.connect(self.clear_history)
        layout.addWidget(clear_button)

        dialog.exec()

    def clear_history(self):
        self.command_history.clear()
        self.save_command_history()
        self.terminal.appendPlainText("Command history cleared.")

    def update_completer(self):
        custom_commands = ['ctheme', 'ctime', 'cdate', 'joke', 'ascii', 'key', 'cproject', 'cpath']
        all_commands = list(set(self.command_history + custom_commands))
        model = self.completer.model()
        if isinstance(model, QStringListModel):
            model.setStringList(all_commands)
        else:
            self.completer.setModel(QStringListModel(all_commands))

    def handle_tab_completion(self):
        current_word = self.get_current_word()
        self.completer.setCompletionPrefix(current_word)
        if self.completer.completionCount() > 0:
            self.completer.complete()

    def get_current_word(self):
        cursor = self.terminal.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()

    def insert_completion(self, completion):
        cursor = self.terminal.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        cursor.movePosition(QTextCursor.MoveOperation.Left)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfWord)
        cursor.insertText(completion[-extra:])
        self.terminal.setTextCursor(cursor)
        self.update_current_command()

    def update_current_command(self):
        cursor = self.terminal.textCursor()
        text = self.terminal.toPlainText()
        command_start = text.rfind(self.prompt) + len(self.prompt)
        self.current_command = text[command_start:].strip()
        self.completer.setCompletionPrefix(self.current_command)
    
    def update_output(self):
        try:
            output = self.process.readAllStandardOutput().data().decode()
            self.terminal.append(output)
        except Exception as e:
            error_message = f"Error reading output: {str(e)}"
            self.terminal.append(error_message)
            logging.error(error_message)

        try:
            error_output = self.process.readAllStandardError().data().decode()
            if error_output:
                self.terminal.append(error_output)
        except Exception as e:
            error_message = f"Error reading error output: {str(e)}"
            self.terminal.append(error_message)
            logging.error(error_message)