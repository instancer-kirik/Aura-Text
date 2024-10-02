import os
import sys
import traceback
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from qt_material import list_themes


# Set up logging
logging.basicConfig(filename='auratext_log.txt', level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def excepthook(exc_type, exc_value, exc_traceback):
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    print("An uncaught exception occurred. Please check auratext_log.txt for details.")

def global_exception_handler(exctype, value, tb):
    with open('crash_log.txt', 'w') as f:
        f.write(f"An unhandled exception occurred:\n")
        f.write(f"Type: {exctype}\n")
        f.write(f"Value: {value}\n")
        f.write("Traceback:\n")
        traceback.print_tb(tb, file=f)
    # Also print to console
    print("An unhandled exception occurred:")
    print("Type:", exctype)
    print("Value:", value)
    traceback.print_tb(tb)

sys.excepthook  = global_exception_handler

def main():
    configure_logging()
    sys.excepthook = exception_hook
    logging.debug("Logging configured")

    try:
        import qt_material
        themes_dir = os.path.join(os.path.dirname(qt_material.__file__), 'themes')
        os.makedirs(os.path.join(themes_dir, 'dark'), exist_ok=True)
        logging.info("Qt Material themes directory created")

        app = QApplication(sys.argv)
        logging.info("QApplication created")
        
        available_themes = list_themes()
        logging.info(f"Available themes: {', '.join(available_themes)}")
        
        # logging.info("Creating Window instance")
        # ex = QWidget()
        # logging.info("Window instance created")
        
        # ex.show()
        # logging.info("Window shown")
        
        # # Test opening a file after a short delay
        # QTimer.singleShot(1000, lambda: test_open_file(ex))
        
        logging.info("Entering Qt event loop")
        sys.exit(app.exec())
    except Exception as e:
        logging.exception(f"An error occurred in main: {e}")
        print(f"An error occurred. Please check auratext_log.txt for details.")
        input("Press Enter to exit...")

def test_open_file(window):
    logging.info("Testing file open functionality")
    try:
        # Replace with an actual file path on your system
        test_file_path = "X:/_Work/a.py"
        window.open_file(test_file_path)
    except Exception as e:
        logging.exception(f"Error in test_open_file: {e}")
def exception_hook(exctype, value, tb):
    logging.error("Uncaught exception", exc_info=(exctype, value, tb))
    traceback.print_exception(exctype, value, tb)



def configure_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)

if __name__ == "__main__":
    main()
