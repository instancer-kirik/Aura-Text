import os
import json
import requests
import shutil
from qt_material import list_themes, apply_stylesheet
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QMessageBox

class ThemeManager:
    def __init__(self, local_app_data):
        self.local_app_data = local_app_data
        self.theme_config = self.load_theme_config()

    def load_theme_config(self):
        with open(f"{self.local_app_data}/data/theme.json", "r") as themes_file:
            return json.load(themes_file)

    def apply_theme(self, widget):
        if self.theme_config["theming"] == "flat":
            theme_name = self.theme_config.get("theme_type", "dark_teal.xml")
            available_themes = list_themes()
            
            if theme_name not in available_themes:
                print(f"Warning: Invalid theme '{theme_name}'. Available themes: {', '.join(available_themes)}")
                print("Falling back to default theme.")
                theme_name = "dark_teal.xml"

            try:
                apply_stylesheet(widget, theme=theme_name)
                print(f"Applied theme: {theme_name}")
            except Exception as e:
                print(f"Error applying theme: {e}")
                print("Falling back to default styling.")
        else:
            print("Theming is not set to 'flat'. No theme applied.")

    def update_theme(self, new_theme):
        self.theme_config["theme_type"] = new_theme
        with open(f"{self.local_app_data}/data/theme.json", "w") as themes_file:
            json.dump(self.theme_config, themes_file, indent=4)

class ThemeDownloader(QWidget):
    def __init__(self, theme_manager):
        super().__init__()
        self.theme_manager = theme_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        self.setWindowTitle("Theme Downloader")
        self.get_theme_list()

    def get_theme_list(self):
        username = "rohankishore"
        repo = "AuraText-Themes"
        api_url = f"https://api.github.com/repos/{username}/{repo}/contents/Themes"
        response = requests.get(api_url)
        if response.status_code == 200:
            content = response.json()
            files_info = [file["name"].split(".")[0] for file in content if file["type"] == "file"]
            self.list_widget.clear() 
            for file_info in files_info:
                item = self.list_widget.addItem(file_info)
                download_button = QPushButton("Download", self)
                download_button.clicked.connect(lambda _, name=file_info: self.download_theme(name))
                self.list_widget.setItemWidget(self.list_widget.item(self.list_widget.count() - 1), download_button)

    def download_theme(self, file_name):
        username = "rohankishore"
        repo = "AuraText-Themes"
        selected_file = file_name + ".json"
        download_url = f"https://raw.githubusercontent.com/{username}/{repo}/main/Themes/{selected_file}"
        response = requests.get(download_url)

        if response.status_code == 200:
            local_file_path = os.path.join(self.theme_manager.local_app_data, "plugins", selected_file)
            with open(local_file_path, "wb") as file:
                file.write(response.content)

            theme_json_path = os.path.join(self.theme_manager.local_app_data, "data", "theme.json")
            shutil.copy(local_file_path, theme_json_path)

            self.theme_manager.load_theme_config()  # Reload the theme config
            self.theme_manager.apply_theme(self.parent())  # Apply the new theme

            QMessageBox.information(self, "Theme Downloaded", f"Theme '{selected_file}' has been applied successfully.")
        else:
            QMessageBox.critical(self, "Download Failed", f"Failed to download theme '{selected_file}'.")