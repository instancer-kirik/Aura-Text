import os
import re
import subprocess
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QProcess, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QKeyEvent, QTextCursor
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSplitter,
    
)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import QPointF
import time
from ..scripts.def_path import resource
from GUX.visual_effects import ParticleEffect, ParticleOverlay
import random
import logging
newTerminalIcon = resource(r"../media/terminal/new.svg")
killTerminalIcon = resource(r"../media/terminal/remove.svg")


class TerminalEmulator(QWidget):
    commandEntered = pyqtSignal(str)
    keyPressed = pyqtSignal(str)  # New signal for key presses

    def __init__(self, parent=None, mm=None):
        super().__init__(parent)
        self.mm = mm
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.terminal = QPlainTextEdit(self)
        self.layout.addWidget(self.terminal)
        
        try:
            self.particle_effect = ParticleEffect(self)
            self.particle_overlay = ParticleOverlay(self)
            self.particle_overlay.setGeometry(self.rect())
            self.particle_overlay.particle_effect = self.particle_effect
            self.layout.addWidget(self.particle_overlay)
        except Exception as e:
            logging.error(f"Error initializing particle effects: {e}")
            self.particle_effect = None
            self.particle_overlay = None
        
        self.shake_offset = QPointF(0, 0)
        self.shake_timer = QTimer(self)
        self.shake_timer.timeout.connect(self.update_shake)
        
        self.typing_effect_enabled = True
        self.typing_effect_speed = 100
        self.typing_effect_particle_count = 10
        self.last_key_press_time = 0
        self.typing_speed = 0
        
        self.setup_terminal()
        self.setup_toolbar()

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.layout.addWidget(self.splitter)

        self.splitter.addWidget(self.terminal)

        self.processes = []
        self.current_process_index = -1

        self.command_history = []
        self.history_index = 0

        self.current_command = ""
        self.prompt = "> "

        self.addNewTab()
        self.load_typing_effect_settings()

        # Add a timer for particle updates
        self.particle_timer = QTimer(self)
        self.particle_timer.timeout.connect(self.update_particles)
        self.particle_timer.start(16)  # 60 FPS

        # Set up logging for this class
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Connect the keyPressed signal to the InputManager if available
        if self.mm and hasattr(self.mm, 'input_manager'):
            self.keyPressed.connect(self.mm.input_manager.update_typing_speed)

    def setup_terminal(self):
        # Set up terminal appearance and behavior
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

        toggle_effect_button = QPushButton("Toggle Typing Effect")
        toggle_effect_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 1px solid white;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        toggle_effect_button.clicked.connect(self.toggle_typing_effect)

        toolbar_layout.addWidget(self.terminal_selector)
        toolbar_layout.addWidget(new_terminal_button)
        toolbar_layout.addWidget(kill_terminal_button)
        toolbar_layout.addWidget(toggle_effect_button)
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
        self.start_powershell(index)

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

    def start_powershell(self, index):
        powershell_path = self.find_powershell_core()
        if powershell_path:
            self.processes[index].start(powershell_path)
            self.terminal.appendPlainText(
                f"PowerShell Core started at {powershell_path}.\n"
                "Type your commands below.\n"
            )
        else:
            self.terminal.appendPlainText(
                "PowerShell Core not found. Using default PowerShell.\n"
            )
            self.processes[index].start("powershell.exe")

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
        self.logger.debug(f"Key pressed: {event.text()}")
        self.keyPressed.emit(event.text())  # Emit the keyPressed signal
        try:
            current_time = time.time()
            if self.last_key_press_time:
                time_diff = current_time - self.last_key_press_time
                self.typing_speed = 1 / time_diff if time_diff > 0 else 0
            self.last_key_press_time = current_time

            cursor = self.terminal.textCursor()
            
            # Ensure the cursor is at the end of the document
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.terminal.setTextCursor(cursor)

            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.execute_command()
                self.queue_particles(cursor.position(), QColor(0, 255, 0), 20)  # Green particles for execution
            elif event.key() == Qt.Key.Key_Backspace:
                if len(self.current_command) > 0:
                    self.current_command = self.current_command[:-1]
                    cursor.deletePreviousChar()
                    self.queue_particles(cursor.position(), QColor(255, 0, 0), 15)  # Red particles for deletion
                    self.shake(200)  # Short shake for deletion
            elif event.key() == Qt.Key.Key_Up:
                self.show_previous_command()
            elif event.key() == Qt.Key.Key_Down:
                self.show_next_command()
            else:
                if event.text().isprintable():
                    self.current_command += event.text()
                    if self.typing_effect_enabled:
                        self.type_with_effect(event.text())
                    else:
                        self.insert_character(event.text())

            self.terminal.ensureCursorVisible()
            event.accept()
        except Exception as e:
            print(f"Error in terminal_key_press_event: {e}")

    def type_with_effect(self, text):
        for char in text:
            self.logger.debug(f"Typing with_effect: {char}")
            QTimer.singleShot(random.randint(50, self.typing_effect_speed), lambda c=char: self.insert_character(c))

    def insert_character(self, char):
        self.logger.debug(f"Inserting character: {char}")
        try:
            cursor = self.terminal.textCursor()
            cursor.insertText(char)
            self.terminal.setTextCursor(cursor)
            
            rect = self.terminal.cursorRect(cursor)
            pos = self.terminal.mapTo(self.particle_overlay, rect.center())
            
            self.queue_particles(pos, QColor(255, 255, 255), self.typing_effect_particle_count)
            self.terminal.ensureCursorVisible()
        except Exception as e:
            print(f"Error in insert_character: {e}")

    def queue_particles(self, pos, color, count):
        QTimer.singleShot(0, lambda: self.add_particles(pos, color, count))

    def add_particles(self, pos, color, count):
        try:
            self.particle_effect.add_particles(pos, color, count)
        except Exception as e:
            print(f"Error in add_particles: {e}")

    def update_particles(self):
        try:
            self.particle_effect.update_particles()
            self.particle_overlay.update()
        except Exception as e:
            print(f"Error in update_particles: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.particle_overlay.setGeometry(self.rect())

    def update_shake(self):
        self.shake_offset = QPointF(random.uniform(-2, 2), random.uniform(-2, 2))
        if self.shake_timer.interval() > 16:
            self.shake_timer.setInterval(self.shake_timer.interval() - 16)
        else:
            self.shake_timer.stop()
            self.shake_offset = QPointF(0, 0)
        self.particle_overlay.set_shake_offset(self.shake_offset)
        self.update()

    def shake(self, duration=500):
        self.shake_timer.start(duration)

    def execute_command(self):
        self.terminal.appendPlainText("")
        self.processes[self.current_process_index].write(
            self.current_command.encode() + b"\n"
        )
        self.command_history.append(self.current_command)
        self.history_index = len(self.command_history)
        self.commandEntered.emit(self.current_command)
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

    def toggle_typing_effect(self):
        self.typing_effect_enabled = not self.typing_effect_enabled

    def load_typing_effect_settings(self):
        if hasattr(self, 'mm') and hasattr(self.mm, 'settings_manager'):
            settings_manager = self.mm.settings_manager
            self.typing_effect_enabled = settings_manager.get_typing_effect_enabled()
            self.typing_effect_speed = settings_manager.get_typing_effect_speed()
            self.typing_effect_particle_count = settings_manager.get_typing_effect_particle_count()
        else:
            # Default values if settings_manager is not available
            self.typing_effect_enabled = True
            self.typing_effect_speed = 100
            self.typing_effect_particle_count = 10