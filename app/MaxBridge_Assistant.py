import os
import sys
import requests
import tempfile
import zipfile
import shutil
import datetime
import hashlib
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QProgressBar,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, url, dest, name, expected_hash=None):
        super().__init__()
        self.url = url
        self.dest = dest
        self.name = name
        self.expected_hash = expected_hash

    def run(self):
        try:
            if os.path.exists(self.dest):
                local_hash = self.calculate_file_hash(self.dest)

                if self.expected_hash and local_hash == self.expected_hash:
                    self.status.emit(f"Skipped: {self.name} (already downloaded and verified)")
                    self.progress.emit(100)
                    self.finished.emit(self.name)
                    return
                else:
                    self.status.emit(f"Hash mismatch or file not found: {self.name}, redownloading...")

            # Start downloading the file
            self.status.emit(f"Downloading: {self.name}")
            with requests.get(self.url, stream=True) as response:
                response.raise_for_status()
                total_length = int(response.headers.get("content-length", 0))
                downloaded = 0

                with open(self.dest, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                            downloaded += len(chunk)
                            percent = int(downloaded * 100 / total_length)
                            self.progress.emit(percent)

            # Verify the file hash after download
            if self.expected_hash:
                downloaded_hash = self.calculate_file_hash(self.dest)
                if downloaded_hash != self.expected_hash:
                    self.status.emit(f"Error: {self.name} - Hash mismatch after download.")
                    self.progress.emit(0)
                    self.finished.emit(self.name)
                    return

            self.status.emit(f"Completed: {self.name}")
        except Exception as e:
            self.status.emit(f"Error: {self.name}: {e}")
            self.progress.emit(0)
        finally:
            self.finished.emit(self.name)

    def calculate_file_hash(self, file_path):
        # Calculate the SHA256 hash of the file
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(byte_block)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.status.emit(f"Error calculating hash for {file_path}: {e}")
            return None
        
class MaxBridgeAssistant(QWidget):
    def __init__(self):
        super().__init__()
        self.temp_folder = self.setup_temp_folder()
        self.max_versions = self.detect_max_versions()
        self.checkboxes = []
        self.json_url = "https://github.com/mohseni-mr/MaxBridge-Assistant/raw/refs/heads/main/resources/download_urls.json"
        self.plugin_version = None
        self.megascans_library = None
        self.file_list = []
        self.threads = []
        self.initUI()
        self.temp_folder = self.setup_temp_folder()
        self.log_file = os.path.normpath(os.path.join(self.temp_folder, "process_log.txt"))

    def log_message(self, message, update_status=True):
        """
        Logs a message to the log file and optionally updates the status label.
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"

            with open(self.log_file, "a", encoding="utf-8") as log:
                log.write(log_entry)

            if update_status:
                self.status_label.setText(message)

        except Exception as e:
            print(f"Failed to log message: {message}. Error: {e}")

    def setup_temp_folder(self):
        temp_dir = os.path.normpath(os.path.join(tempfile.gettempdir(), "maxbridge_assistant_temp"))
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def detect_max_versions(self):
        max_versions_dir = os.path.normpath(os.path.join(os.getenv("LOCALAPPDATA"), "Autodesk", "3dsMax"))
        if not os.path.exists(max_versions_dir):
            return []

        return [folder for folder in os.listdir(max_versions_dir) if os.path.isdir(os.path.join(max_versions_dir, folder))]

    def initUI(self):
        self.setWindowTitle("MaxBridge Assistant")
        self.setFixedSize(400, 260)

        # Layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # 3ds Max Versions Section
        self.add_version_checkboxes()

        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("Path: -", self)
        self.folder_label.setWordWrap(True)
        folder_layout.addWidget(self.folder_label)

        self.select_folder_button = QPushButton("Select Megascans Library", self)
        self.select_folder_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.select_folder_button)
        self.main_layout.addLayout(folder_layout)

        # Process Button
        self.process_button = QPushButton("Start Setup", self)
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.start_process)
        self.main_layout.addWidget(self.process_button)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        self.main_layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel("Status: Waiting", self)
        self.main_layout.addWidget(self.status_label)

        # Name
        self.name_label = QLabel(self)
        self.name_label.setText('<a href="https://bio.mohseni.info">Mohammadreza Mohseni</a>')
        self.name_label.setOpenExternalLinks(True)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setFont(QFont("Segoe UI", 8))
        self.main_layout.addWidget(self.name_label)

        self.setLayout(self.main_layout)

    def add_version_checkboxes(self):
        self.max_versions_label = QLabel("Detected 3ds Max Versions:")
        self.main_layout.addWidget(self.max_versions_label)

        self.max_versions_grid = QGridLayout()
        self.max_versions_grid.setSpacing(5)
        column_count = 4

        for index, version in enumerate(self.max_versions):
            checkbox = QCheckBox(version, self)
            checkbox.setChecked(True)
            row = index // column_count
            col = index % column_count
            self.max_versions_grid.addWidget(checkbox, row, col)
            self.checkboxes.append(checkbox)

        self.main_layout.addLayout(self.max_versions_grid)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Megascans Library Folder")
        if folder:
            self.folder_label.setText(f"Path: {folder}")
            self.megascans_library = folder
            self.process_button.setEnabled(True)
        else:
            self.folder_label.setText("Path: -")
            self.megascans_library = None
            self.process_button.setEnabled(False)

    def start_process(self):
        if not self.megascans_library:
            self.log_message("Error: Please select a library folder.")
            return

        self.fetch_plugin_version()
        self.create_quixel_files()
        self.download_files()

    def fetch_plugin_version(self):
        try:
            response = requests.get(self.json_url)
            response.raise_for_status()
            data = response.json()
            self.plugin_version = data.get("plugin_version", "unknown")
            self.log_message(f"Plugin version fetched: {self.plugin_version}")
        except Exception as e:
            self.log_message(f"Error fetching plugin version: {e}")

    def prepare_library(self):
        """
        Prepares the library by:
        1. Clearing and creating the plugin folder.
        2. Removing the plugin_versions_12.json file if it exists.
        3. Extracting the plugin ZIP file to the plugin folder.
        4. Replacing the MS_API.py file in the extracted folder.
        5. Replacing or copying plugin_versions_12.json.
        """
        if not self.plugin_version or not self.megascans_library:
            self.log_message("Error: Missing required data.")
            return

        plugin_path = os.path.normpath(os.path.join(self.megascans_library, "support", "plugins", "max", self.plugin_version))
        plugin_versions_file = os.path.normpath(os.path.join(self.megascans_library, "support", "plugins", "plugin_versions_12.json"))

        try:
            # Step 1: Clear plugin folder
            self.log_message(f"Clearing plugin folder: {plugin_path}")
            QApplication.processEvents()  # Update UI immediately
            if os.path.exists(plugin_path):
                for root, dirs, files in os.walk(plugin_path, topdown=False):
                    for file in files:
                        os.remove(os.path.normpath(os.path.join(root, file)))
                    for dir in dirs:
                        os.rmdir(os.path.normpath(os.path.join(root, dir)))
            os.makedirs(plugin_path, exist_ok=True)

            # Step 2: Remove plugin_versions_12.json if it exists
            self.log_message(f"Removing: {plugin_versions_file}")
            QApplication.processEvents()
            if os.path.exists(plugin_versions_file):
                os.remove(plugin_versions_file)

            # Step 3: Extract the ZIP file to the plugin folder
            self.log_message(f"Extracting ZIP file to: {plugin_path}")
            QApplication.processEvents()
            zip_file = os.path.normpath(os.path.join(self.temp_folder, f"{self.plugin_version}.zip"))
            if os.path.exists(zip_file):
                with zipfile.ZipFile(zip_file, "r") as zip_ref:
                    zip_ref.extractall(plugin_path)
            else:
                self.log_message(f"Error: ZIP file {zip_file} not found.")
                return

            # Step 4: Replace MS_API.py in the extracted folder
            self.log_message(f"Replacing MS_API.py in: {plugin_path}")
            QApplication.processEvents()
            downloaded_api_path = os.path.normpath(os.path.join(self.temp_folder, "MS_API.py"))
            destination_api_path = os.path.normpath(os.path.join(plugin_path, "MSLiveLink", "MS_API.py"))
            if os.path.exists(downloaded_api_path):
                os.makedirs(os.path.dirname(destination_api_path), exist_ok=True)
                try:
                    shutil.copy(downloaded_api_path, destination_api_path)
                except Exception as e:
                    self.log_message(f"Error replacing MS_API.py: {e}")
                    return
            else:
                self.log_message(f"Error: MS_API.py not found in temp folder.")
                return
        
            # Step 5: Replace or copy plugin_versions_12.json
            self.log_message(f"Replacing plugin_versions_12.json in: {plugin_versions_file}")
            QApplication.processEvents()
            downloaded_versions_path = os.path.normpath(os.path.join(self.temp_folder, "plugin_versions_12.json"))
            if os.path.exists(downloaded_versions_path):
                try:
                    shutil.copy(downloaded_versions_path, plugin_versions_file)
                except Exception as e:
                    self.log_message(f"Error replacing plugin_versions_12.json: {e}")
                    return
            else:
                self.log_message(f"Error: plugin_versions_12.json not found in temp folder.")

            # Final update
            self.log_message("Library preparation complete!")

        except Exception as e:
            self.log_message(f"Error during library preparation: {e}")

    def create_quixel_files(self):
        if not self.megascans_library or not self.plugin_version:
            self.log_message("Error: Megascans Library or plugin version missing.")
            return
        
        base_dir = os.path.normpath(os.path.join(os.getenv("LOCALAPPDATA"), "Autodesk", "3dsMax"))
        selected_versions = [cb.text() for cb in self.checkboxes if cb.isChecked()]

        for version in selected_versions:
            version_path = os.path.normpath(os.path.join(base_dir, version))
            if not os.path.exists(version_path):
                self.log_message(f"Skipped: {version} (Folder not found)")
                continue

            for lang in os.listdir(version_path):
                lang_path = os.path.normpath(os.path.join(version_path, lang, "scripts", "startup"))
                try:
                    os.makedirs(lang_path, exist_ok=True)

                    # File content
                    file_content = (
                        f"python.Execute \"filePath = u'{self.megascans_library}/support/plugins/max/{self.plugin_version}/MSLiveLink/MS_API.py'; "
                        "exec(open(filePath).read(), {'__file__': filePath})\""
                    )

                    file_path = os.path.normpath(os.path.join(lang_path, "Quixel.ms"))
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(file_content)

                    self.log_message(f"Created: {file_path}")
                except Exception as e:
                    self.log_message(f"Error in {lang_path}: {e}")

    def download_files(self):
        try:
            response = requests.get(self.json_url)
            if response.status_code != 200:
                self.log_message(f"Failed to load download URLs")
                response.raise_for_status()

            data = response.json()
            self.file_list = data.get("files", [])

            for file_info in self.file_list:
                file_url = file_info["url"]
                file_name = file_info["name"]
                file_hash = file_info.get("hash")
                file_path = os.path.join(self.temp_folder, os.path.basename(file_url))

                thread = DownloadThread(file_url, file_path, file_name, file_hash)
                self.threads.append(thread)
                thread.progress.connect(self.update_progress)
                thread.status.connect(self.update_status)
                thread.finished.connect(self.handle_download_complete)
                thread.start()

        except Exception as e:
            self.log_message(f"Error downloading files: {e}")

    def handle_download_complete(self):
        self.threads = [t for t in self.threads if t.isRunning()]
        if not self.threads:
            self.log_message("All downloads completed. Preparing the library...")
            QApplication.processEvents()
            self.prepare_library()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.log_message(f"Status: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    root = os.path.normpath(os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.normpath(os.path.join(root, 'resources', 'mohseni.ico'))
    app.setWindowIcon(QIcon(icon_path))
    window = MaxBridgeAssistant()
    window.show()
    sys.exit(app.exec_())
