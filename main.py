import os
import sys
from PyQt6.QtWidgets import QApplication
from auratext.Core.window import Window
from qt_material import list_themes

""" 
This file includes the code to run the app. It also scans if the app is being opened for the first time in order to show the
setup instructions.
"""

def main():
    print("Starting main function")
    
    import qt_material
    themes_dir = os.path.join(os.path.dirname(qt_material.__file__), 'themes')
    os.makedirs(os.path.join(themes_dir, 'dark'), exist_ok=True)

    app = QApplication(sys.argv)
    
    available_themes = list_themes()
    print(f"Available themes: {', '.join(available_themes)}")
    
    print("Creating Window instance")
    try:
        ex = Window()
        print("Created Window instance")
        ex.show()
        print("Window shown")
        sys.exit(app.exec())
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")  # This will keep the console open

    
if __name__ == "__main__":
    main()
