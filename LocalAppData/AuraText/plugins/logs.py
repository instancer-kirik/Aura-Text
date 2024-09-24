import logging
from auratext.Core.plugin_interface import Plugin

class LogsPlugin(Plugin):
    def __init__(self):
        logging.debug("Entering LogsPlugin.__init__")
        try:
            
            logging.debug("LogsPlugin: Additional initialization completed")
        except Exception as e:
            logging.exception(f"Error in LogsPlugin.__init__: {e}")
        finally:
            logging.debug("Exiting LogsPlugin.__init__")

    def log(self, message):
        logging.debug(f"LogsPlugin.log called with message: {message}")

    def initialize(self):
        logging.debug("Entering LogsPlugin.initialize")
        try:
            super().initialize()
            logging.debug("LogsPlugin: super().initialize() completed")
            # Add any additional initialization here
            logging.debug("LogsPlugin: Additional initialization in initialize() completed")
        except Exception as e:
            logging.exception(f"Error in LogsPlugin.initialize: {e}")
        finally:
            logging.debug("Exiting LogsPlugin.initialize")