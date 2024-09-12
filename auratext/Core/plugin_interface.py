# plugin_interface.py
from __future__ import annotations
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import QObject
import logging

if TYPE_CHECKING:
    from .window import Window


class ContextMenuPluginInterface:
    def add_menu_items(self, context_menu: QMenu):
        pass

    def add_context_menu_items(self, context_menu: QMenu):
        pass


class Plugin(QObject):
    def __init__(self, window):
        logging.debug(f"Entering Plugin.__init__ for {self.__class__.__name__}")
        try:
            super().__init__(window)
            logging.debug(f"Plugin.__init__ super() call completed for {self.__class__.__name__}")
            self.window = window
            logging.debug(f"Plugin.__init__ self.window assigned for {self.__class__.__name__}")
        except Exception as e:
            logging.exception(f"Exception in Plugin.__init__ for {self.__class__.__name__}: {e}")
        logging.debug(f"Exiting Plugin.__init__ for {self.__class__.__name__}")

    def initialize(self):
        logging.debug(f"{self.__class__.__name__}.initialize called")
        pass  # To be implemented by subclasses


class MenuPluginInterface(Plugin):
    section = ""  # To be set by subclasses

    def add_menu_items(self, menu):
        pass  # To be implemented by subclasses
    def add_context_menu_items(self, context_menu: QMenu):
        pass

#############################################
