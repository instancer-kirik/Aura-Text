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
from typing import Optional, Dict
from PyQt6.QtCore import QPointF
import time
from ..scripts.def_path import resource
from GUX.visual_effects import ParticleEffect, ParticleOverlay
import random
from PyQt6.QtCore import QProcessEnvironment
import platform
from PyQt6.QtWidgets import QLabel
import logging
import math
from GUX.overlay import Overlay
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
        
        # Initialize logger first
        self.logger = logging.getLogger(__name__)
        
        # Initialize attributes
        self.processes = []
        self.current_process_index = -1
        self.current_env = None
        self.current_command = ""
        self.command_history = []
        self.history_index = 0
        self.prompt = "> "
        self.last_key_press_time = None
        self.typing_speed = 0
        
        # Create UI components in correct order
        self.shell_combo = QComboBox()  # Create combo box first
        self.available_shells = self.detect_available_shells()  # Then detect shells
        
        # Setup UI components
        self.terminal = QPlainTextEdit()
        self.setup_terminal()
        
        # Create toolbars in correct order
        self.setup_shell_toolbar()
        self.setup_main_toolbar()
        
        # Add terminal to layout
        self.layout.addWidget(self.terminal)
        
        # Initialize particle effects
        self.particle_effect = None
        self.particle_overlay = None
        self.particle_timer = None
        self.typing_effect_enabled = False
        
        if self.should_enable_particles():
            self.init_particle_effects()
        self.load_typing_effect_settings()
        
        # Add initial terminal tab
        self.addNewTab()

    def setup_main_toolbar(self):
        """Setup main toolbar with terminal controls"""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 0, 5, 0)

        # Terminal selector
        self.terminal_selector = QComboBox()
        self.terminal_selector.setStyleSheet("QComboBox { min-width: 150px; }")
        self.terminal_selector.currentIndexChanged.connect(self.switchTab)

        # Terminal control buttons
        new_terminal_button = QPushButton(QIcon(newTerminalIcon), "")
        kill_terminal_button = QPushButton(QIcon(killTerminalIcon), "")
        toggle_effect_button = QPushButton("Toggle Effect")

        for btn in [new_terminal_button, kill_terminal_button, toggle_effect_button]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    border: none;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)

        new_terminal_button.clicked.connect(self.addNewTab)
        kill_terminal_button.clicked.connect(self.killCurrentTerminal)
        toggle_effect_button.clicked.connect(self.toggle_typing_effect)

        toolbar_layout.addWidget(self.terminal_selector)
        toolbar_layout.addWidget(new_terminal_button)
        toolbar_layout.addWidget(kill_terminal_button)
        toolbar_layout.addWidget(toggle_effect_button)
        toolbar_layout.addStretch()

        self.layout.addWidget(toolbar)

    

    def addNewTab(self):
        """Add new terminal tab with current shell and environment"""
        index = self.terminal_selector.count()
        self.terminal_selector.addItem(f"Terminal {index + 1}")
        
        process = QProcess(self)
        process.readyReadStandardOutput.connect(self.handle_stdout)
        process.readyReadStandardError.connect(self.handle_stderr)
        
        self.processes.append(process)
        self.terminal_selector.setCurrentIndex(index)
        
        # Start shell with current settings
        shell_name = self.shell_combo.currentText()
        self.start_shell(index=index, shell_name=shell_name)

    def start_shell(self, index: Optional[int] = None, shell_name: Optional[str] = None):
        """Start or restart shell process with current environment
        
        Args:
            index (Optional[int]): Process index for multi-tab support. If None, uses single process mode
            shell_name (Optional[str]): Name of shell to start. If None, uses current selection
        """
        try:
            # Get shell path
            shell_path = self.available_shells.get(
                shell_name or self.shell_combo.currentText()
            )
            
            if not shell_path:
                raise ValueError(f"Shell not found: {shell_name}")
                
            # Set up environment
            env = QProcess.systemEnvironment()
            process_env = QProcessEnvironment.systemEnvironment()
            if self.current_env:
                for k, v in self.current_env.items():
                    process_env.insert(k, v)
            
            # Handle single vs multi-process mode
            if index is not None:
                # Multi-tab mode
                process = self.processes[index]
                process.setProcessEnvironment(process_env)
                process.start(shell_path)
                self.terminal.appendPlainText(f"Started {shell_name} shell\n")
            else:
                # Single process mode (legacy support)
                if hasattr(self, 'process'):
                    self.process.terminate()
                    self.process.waitForFinished()
                    
                self.process = QProcess()
                self.process.readyReadStandardOutput.connect(self.handle_output)
                self.process.readyReadStandardError.connect(self.handle_error)
                self.process.setProcessEnvironment(process_env)
                self.process.start(shell_path)
                
        except Exception as e:
            error_msg = f"Error starting shell: {e}"
            self.terminal.appendPlainText(f"{error_msg}\n")
            self.logger.error(error_msg)

    def should_enable_particles(self) -> bool:
        """Check if particle effects should be enabled"""
        try:
            # First check if we have the required components
            if not hasattr(self, 'mm') or not self.mm:
                return False
            
            if not hasattr(self.mm, 'config_manager'):
                return False
            
            # Then check the configuration
            return self.mm.config_manager.get_typing_effect_enabled()
        except Exception as e:
            self.logger.error(f"Error checking particle settings: {e}")
            return False

    def init_particle_effects(self):
        """Initialize particle effects using the existing overlay system"""
        try:
            self.logger.debug("Starting particle effects initialization")
            
            if not self.should_enable_particles():
                self.logger.debug("Particles disabled by configuration")
                self.typing_effect_enabled = False
                return
            
            # Ensure CCCore has an overlay
            if not hasattr(self.mm, 'overlay'):
                self.logger.debug("Creating new CompositeOverlay for CCCore")
                from GUX.overlay import CompositeOverlay
                overlay = CompositeOverlay(
                    self.mm,
                    flashlight_size=200,
                    flashlight_power=0.6,
                    serial_port=None
                )
                self.mm.set_overlay(overlay)
                overlay.show()
                overlay.raise_()
            
            self.logger.debug(f"Using overlay: {self.mm.overlay}")
            
            # Create particle layer
            class ParticleLayer(QWidget):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.particle_effect = None
                    self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                    self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                                      Qt.WindowType.WindowStaysOnTopHint |
                                      Qt.WindowType.Tool)
                    
                def paintEvent(self, event):
                    if not self.particle_effect:
                        return
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    self.particle_effect.draw(painter)
                    
            # Create particle effect
            self.particle_effect = ParticleEffect(self)
            
            # Add particle layer to composite overlay
            self.particle_layer = ParticleLayer(self.mm.overlay)
            self.particle_layer.particle_effect = self.particle_effect
            self.particle_layer.resize(self.size())
            
            # Add to overlay's layout
            if not self.mm.overlay.layout():
                layout = QVBoxLayout(self.mm.overlay)
                self.mm.overlay.setLayout(layout)
            self.mm.overlay.layout().addWidget(self.particle_layer)
            
            # Show layers
            self.particle_layer.show()
            self.particle_layer.raise_()
            
            # Configure update timer
            self.particle_timer = QTimer()
            self.particle_timer.timeout.connect(self.update_particles)
            self.particle_timer.start(16)  # 60 FPS
            
            self.typing_effect_enabled = True
            self.logger.debug("Particle effects initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize particle effects: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def disable_particle_effects(self):
        """Safely disable and cleanup particle effects"""
        self.typing_effect_enabled = False
        
        if self.particle_timer:
            self.particle_timer.stop()
            self.particle_timer = None
            
        if self.particle_overlay:
            self.particle_overlay.hide()
            self.particle_overlay.deleteLater()
            self.particle_overlay = None
            
        if self.particle_effect:
            self.particle_effect = None
            
        self.logger.debug("Particle effects disabled")

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        if hasattr(self, 'particle_layer'):
            self.particle_layer.resize(self.size())
            self.particle_layer.move(self.mapToGlobal(self.rect().topLeft()))

    def moveEvent(self, event):
        """Handle move events"""
        super().moveEvent(event)
        if hasattr(self, 'particle_layer'):
            self.particle_layer.move(self.mapToGlobal(self.rect().topLeft()))

    def cleanup(self):
        """Cleanup resources before destruction"""
        try:
            if hasattr(self, 'particle_overlay'):
                self.disable_particle_effects()
                
            if hasattr(self, 'processes'):
                for process in self.processes:
                    if process and process.state() != QProcess.ProcessState.NotRunning:
                        process.terminate()
                        process.waitForFinished(1000)  # Wait up to 1 second
                        
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error during cleanup: {e}")
            else:
                logging.error(f"Error during cleanup: {e}")

    def closeEvent(self, event):
        """Handle close event"""
        try:
            self.cleanup()
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error in close event: {e}")
            else:
                logging.error(f"Error in close event: {e}")
        super().closeEvent(event)

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
        self.logger.debug(f"Key pressed: {str(event.text())}")
        self.keyPressed.emit(str(event.text()))
        try:
            current_time = time.time()
            if self.last_key_press_time:
                time_diff = current_time - self.last_key_press_time
                self.typing_speed = 1 / time_diff if time_diff > 0 else 0
            self.last_key_press_time = current_time

            cursor = self.terminal.textCursor()
            
            # Ensure cursor is at the end
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.terminal.setTextCursor(cursor)

            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                self.execute_command()
                self.queue_particles(cursor.position(), QColor(0, 255, 0), 20)
            elif event.key() == Qt.Key.Key_Backspace:
                if len(self.current_command) > 0:
                    self.current_command = self.current_command[:-1]
                    cursor.deletePreviousChar()
                    self.queue_particles(cursor.position(), QColor(255, 0, 0), 15)
                    self.shake(200)
            elif event.key() == Qt.Key.Key_Up:
                self.show_previous_command()
            elif event.key() == Qt.Key.Key_Down:
                self.show_next_command()
            else:
                if event.text().isprintable():
                    self.current_command += str(event.text())
                    if self.typing_effect_enabled:
                        self.type_with_effect(str(event.text()))
                    else:
                        self.insert_character(str(event.text()))

            self.terminal.ensureCursorVisible()
            event.accept()
        except Exception as e:
            self.logger.error(f"Error in terminal_key_press_event: {str(e)}")

    def type_with_effect(self, text):
        for char in text:
            self.logger.debug(f"Typing with_effect: {char}")
            QTimer.singleShot(random.randint(50, self.typing_effect_speed), lambda c=char: self.insert_character(c))

    def insert_character(self, char):
        """Safely insert character with optional effects"""
        try:
            # Basic character insertion
            cursor = self.terminal.textCursor()
            cursor.insertText(char)
            self.terminal.setTextCursor(cursor)
            self.terminal.ensureCursorVisible()
            
            # Only add particles if effects are enabled and properly initialized
            if (self.typing_effect_enabled and 
                self.particle_effect is not None and 
                self.particle_overlay is not None):
                
                # Get cursor position in global coordinates
                rect = self.terminal.cursorRect(cursor)
                global_pos = self.terminal.mapToGlobal(rect.center())
                local_pos = self.particle_overlay.mapFromGlobal(global_pos)
                
                # Add particles with random dispersion
                if self.particle_overlay and not self.particle_overlay.isHidden():
                    self.queue_particles(local_pos, QColor(255, 255, 255), 
                                      self.typing_effect_particle_count)
                    
        except Exception as e:
            self.logger.error(f"Error in insert_character: {e}")

    def queue_particles(self, pos, color, count):
        """Safely queue particle effects"""
        try:
            if not self.typing_effect_enabled or not self.particle_effect:
                return
            
            QTimer.singleShot(0, lambda: self.add_particles(pos, color, count))
        except Exception as e:
            self.logger.error(f"Error queueing particles: {e}")

    def add_particles(self, pos, color, count):
        """Add particles at the specified position"""
        try:
            if not self.typing_effect_enabled or not self.particle_effect:
                return
            
            # Convert terminal coordinates to screen coordinates
            screen_pos = self.mapToGlobal(pos)
            self.logger.debug(f"Screen position: {screen_pos}")
            
            # Convert screen coordinates to overlay coordinates
            if hasattr(self, 'particle_layer'):
                overlay_pos = self.particle_layer.mapFromGlobal(screen_pos)
                self.logger.debug(f"Overlay position: {overlay_pos}")
                
                # Add particles with random dispersion
                for _ in range(count):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(1, 5)
                    velocity = QPointF(
                        math.cos(angle) * speed,
                        math.sin(angle) * speed
                    )
                    self.particle_effect.add_particle(overlay_pos, color, velocity)
                    self.logger.debug(f"Added particle at {overlay_pos}")
                
        except Exception as e:
            self.logger.error(f"Error adding particles: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def update_particles(self):
        """Update particle positions and redraw"""
        if not self.typing_effect_enabled:
            return
        
        try:
            if self.particle_effect and self.particle_layer:
                self.particle_effect.update()
                self.particle_layer.update()
                self.logger.debug("Particles updated")
        except Exception as e:
            self.logger.error(f"Error updating particles: {e}")
            self.typing_effect_enabled = False
            import traceback
            self.logger.error(traceback.format_exc())

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
        """Load typing effect settings with proper defaults"""
        try:
            if hasattr(self, 'mm') and hasattr(self.mm, 'config_manager'):
                settings_manager = self.mm.config_manager
                self.typing_effect_enabled = settings_manager.get_typing_effect_enabled()
                self.typing_effect_speed = settings_manager.get_typing_effect_speed()
                self.typing_effect_particle_count = settings_manager.get_typing_effect_particle_count()
            else:
                # Default values if settings_manager is not available
                self.typing_effect_enabled = False  # Changed to False by default
                self.typing_effect_speed = 100
                self.typing_effect_particle_count = 10
                self.logger.warning("Using default typing effect settings")
        except Exception as e:
            self.logger.error(f"Error loading typing effect settings: {e}")
            self.typing_effect_enabled = False

    def setup_shell_toolbar(self):
        """Setup shell and environment selection toolbar"""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 0, 5, 0)

        # Configure existing shell selector
        self.shell_combo.setStyleSheet("QComboBox { min-width: 120px; }")
        self.shell_combo.addItems(self.available_shells.keys())
        self.shell_combo.currentTextChanged.connect(self.change_shell)

        # Environment selector
        self.env_combo = QComboBox()
        self.env_combo.setStyleSheet("QComboBox { min-width: 120px; }")
        self.env_combo.currentTextChanged.connect(self.change_environment)

        # Refresh button
        refresh_btn = QPushButton("⟳")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 1px solid white;
                padding: 2px 5px;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_environments)

        # Add widgets to layout
        for label, widget in [
            ("Shell:", self.shell_combo),
            ("Environment:", self.env_combo),
            (None, refresh_btn)
        ]:
            if label:
                toolbar_layout.addWidget(QLabel(label))
            toolbar_layout.addWidget(widget)

        toolbar_layout.addStretch()
        self.layout.addWidget(toolbar)
        self.refresh_environments()

    def detect_available_shells(self) -> Dict[str, str]:
        """Detect available shells on the system"""
        shells = {}
        
        if platform.system() == "Windows":
            shells["PowerShell"] = "powershell.exe"
            shells["CMD"] = "cmd.exe"
            if os.path.exists("C:\\Program Files\\Git\\bin\\bash.exe"):
                shells["Git Bash"] = "C:\\Program Files\\Git\\bin\\bash.exe"
        else:
            # Check common Unix shells
            for shell in ["/bin/bash", "/bin/zsh", "/bin/fish", "/bin/sh"]:
                if os.path.exists(shell):
                    name = os.path.basename(shell)
                    shells[name] = shell
        
        # Update shell selector
        self.shell_combo.clear()
        self.shell_combo.addItems(shells.keys())
        
        return shells

    def refresh_environments(self):
        """Refresh available project environments"""
        try:
            self.env_combo.clear()
            self.env_combo.addItem("System Default")
            
            if self.mm and hasattr(self.mm, 'project_manager'):
                # Get environments from project manager
                for env_name in self.mm.project_manager.get_environments():
                    self.env_combo.addItem(env_name)
                    
                # Add current project environment if exists
                current_project = self.mm.project_manager.get_current_project()
                if current_project:
                    self.env_combo.addItem(f"Project: {current_project.name}")
                    
        except Exception as e:
            logging.error(f"Error refreshing environments: {e}")

    def change_shell(self, shell_name: str):
        """Change current shell"""
        if shell_name in self.available_shells:
            self.restart_shell(shell_name)

    def change_environment(self, env_name: str):
        """Change current environment"""
        try:
            if env_name == "System Default":
                self.current_env = None
            elif env_name.startswith("Project: "):
                project_name = env_name.replace("Project: ", "")
                self.current_env = self.mm.project_manager.get_project_env(project_name)
            else:
                self.current_env = self.mm.project_manager.get_environment(env_name)
                
            self.restart_shell(self.shell_combo.currentText())
            
        except Exception as e:
            logging.error(f"Error changing environment: {e}")

    def restart_shell(self, shell_name: str):
        """Restart shell with new settings"""
        self.terminal.clear()
        if self.current_process_index >= 0:
            self.start_shell(index=self.current_process_index, shell_name=shell_name)
        else:
            self.start_shell(shell_name=shell_name)

    def handle_output(self):
        """Handle shell output"""
        data = self.process.readAllStandardOutput().data().decode()
        self.terminal.appendPlainText(data)

    def handle_error(self):
        """Handle shell errors"""
        data = self.process.readAllStandardError().data().decode()
        self.terminal.appendPlainText(data)
      