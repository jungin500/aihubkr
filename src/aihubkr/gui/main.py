import datetime
import os
import re
import sys

from aihubkr.core.auth import AIHubAuth
from aihubkr.core.config import AIHubConfig
from aihubkr.core.downloader import AIHubDownloader
from aihubkr.core.filelist_parser import AIHubResponseParser, sizeof_fmt
from natsort import natsorted
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QMainWindow,
                             QMessageBox, QProgressBar, QPushButton,
                             QTableWidget, QTableWidgetItem, QTextEdit,
                             QVBoxLayout, QWidget)


class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)

    def __init__(
            self, downloader: AIHubDownloader, dataset_key: str, file_keys: str, output_dir: str):
        super().__init__()
        self.downloader = downloader
        self.dataset_key = dataset_key
        self.file_keys = file_keys
        self.output_dir = output_dir

    def run(self):
        self.progress.emit(0)
        success = self.downloader.download_and_process_dataset(
            self.dataset_key, self.file_keys, self.output_dir
        )
        self.finished.emit(success)


class AIHubDownloaderGUI(QMainWindow):

    DATASET_SEARCH_DEFAULT_QUERY = ".*"  # Default search query

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIHub Dataset Downloader")
        self.setGeometry(100, 100, 800, 900)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Dataset database & search filtering
        self.dataset_db = []
        self.search_query = AIHubDownloaderGUI.DATASET_SEARCH_DEFAULT_QUERY
        self.file_db = {}
        self.is_downloading = False

        self.current_dataset_id = None
        self.current_dataset_title = None
        self.current_total_file_size = 0

        # Authentication
        self.auth = AIHubAuth(None, None)
        self.auth.load_credentials()

        auth_layout = QHBoxLayout()
        auth_layout.addWidget(QLabel("AIHub ID:"))
        self.id_input = QLineEdit()
        auth_layout.addWidget(self.id_input)
        auth_layout.addWidget(QLabel("Password:"))
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        auth_layout.addWidget(self.pw_input)
        self.auth_button = QPushButton("Authenticate")
        self.auth_button.clicked.connect(self.authenticate)
        auth_layout.addWidget(self.auth_button)
        self.layout.addLayout(auth_layout)

        # Dataset key and file keys
        dataset_layout = QHBoxLayout()
        dataset_layout.addWidget(QLabel("Dataset Key:"))
        self.dataset_key_input = QLineEdit()
        dataset_layout.addWidget(self.dataset_key_input)
        dataset_layout.addWidget(QLabel("File Keys:"))
        self.file_keys_input = QLineEdit()
        self.file_keys_input.setText("all")
        dataset_layout.addWidget(self.file_keys_input)
        self.layout.addLayout(dataset_layout)

        # Output directory
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Directory:"))
        self.output_dir_input = QLineEdit()
        output_layout.addWidget(self.output_dir_input)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.browse_button)
        self.layout.addLayout(output_layout)

        # Download button
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setEnabled(False)
        self.layout.addWidget(self.download_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        # Status log
        self.status_log = QTextEdit()
        self.status_log.setFixedHeight(160)
        self.status_log.setReadOnly(True)
        self.layout.addWidget(self.status_log)

        # Add Dataset List button
        update_btn_layout = QHBoxLayout()
        self.dataset_list_button = QPushButton("Update Dataset List")
        self.dataset_list_button.clicked.connect(self.update_dataset_list)
        update_btn_layout.addWidget(self.dataset_list_button)
        self.dataset_list_csv_save_button = QPushButton("Save to CSV")
        self.dataset_list_csv_save_button.clicked.connect(self.save_to_csv)
        self.dataset_list_csv_save_button.setFixedWidth(100)
        update_btn_layout.addWidget(self.dataset_list_csv_save_button)
        self.layout.addLayout(update_btn_layout)

        # Dataset ID/Name search function
        self.dataset_search_query = QLineEdit()
        self.dataset_search_query.setPlaceholderText("Search dataset by ID or Name")
        self.dataset_search_query.textChanged.connect(self.search_dataset)
        self.layout.addWidget(self.dataset_search_query)

        # Table for dataset list
        self.dataset_table = QTableWidget()
        self.dataset_table.setColumnCount(2)
        self.dataset_table.setHorizontalHeaderLabels(["Dataset Key", "Dataset Name"])
        dataset_table_headers = self.dataset_table.horizontalHeader()
        dataset_table_headers.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        dataset_table_headers.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.dataset_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.dataset_table.itemActivated.connect(self.choose_dataset)
        self.layout.addWidget(self.dataset_table)

        # Table for file list
        self.file_list_table = QTableWidget()
        self.file_list_table.setColumnCount(4)  # Select checkbox, Key, Filename, Estimated Size (Max size)
        self.file_list_table.setHorizontalHeaderLabels(["", "File Key", "File Name", "File Size"])
        file_list_headers = self.file_list_table.horizontalHeader()
        file_list_headers.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        file_list_headers.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        file_list_headers.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        file_list_headers.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.file_list_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.file_list_table.cellChanged.connect(self.on_checkbox_changed)
        self.file_list_table.keyPressEvent = self.toggle_filekey
        self.layout.addWidget(self.file_list_table)

        # Data description
        dataset_description_layout = QHBoxLayout()
        self.dataset_description = QLabel("Dataset: Please choose dataset from above list.")
        self.dataset_size_description = QLabel("N/A")
        self.dataset_size_description.setAlignment(Qt.AlignmentFlag.AlignRight)
        dataset_description_layout.addWidget(self.dataset_description)
        dataset_description_layout.addWidget(self.dataset_size_description)
        self.layout.addLayout(dataset_description_layout)

        # Disable normal close behaviour (X button, or ALT+F4)
        self.closeEvent = self.on_close

        # Update button based on initial status
        if self.auth.aihub_id:
            self.id_input.setText(self.auth.aihub_id)
        if self.auth.aihub_pw:
            self.pw_input.setText(self.auth.aihub_pw)

        if self.auth.aihub_id and self.auth.aihub_pw:
            self.download_button.setEnabled(True)
            self.id_input.setDisabled(True)
            self.pw_input.setDisabled(True)
            self.auth_button.setText("Logout")
            self.auth_button.clicked.disconnect(self.authenticate)
            self.auth_button.clicked.connect(self.reset_credential)

        config_manager = AIHubConfig.get_instance()
        config_manager.load_from_disk()
        if config_manager.config_db.get("last_output_dir") is not None:
            last_output_dir = config_manager.config_db.get("last_output_dir")
            self.output_dir_input.setText(last_output_dir)

        auth_headers = {}
        if self.auth.aihub_id and self.auth.aihub_pw:
            auth_headers = {"id": self.auth.aihub_id, "pass": self.auth.aihub_pw}
        self.downloader = AIHubDownloader(auth_headers)

        # Automatically click the update button
        self.update_dataset_list()

        self.log_status("Usage: Welcome! Select dataset by double clicking item,")
        self.log_status("- then select files to download and click 'Download' button.")
        self.log_status("Tip: While choosing files, press SPACE to toggle selection.")
        self.log_status("- You can also select multiple items by holding SHIFT or CTRL.")
        self.log_status("- CTRL+A selects all items.")

    def on_close(self, event):
        if self.is_downloading:
            # Create a dialog to confirm exit
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Exit Confirmation")
            dialog.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            dialog.setIcon(QMessageBox.Icon.Question)
            dialog.setText("Warning: Download in progress!\nAre you sure you want to exit?")
            button = dialog.exec()
            if button == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def on_checkbox_changed(self, row, column):
        self.update_filekey_list()

    def update_filekey_list(self):
        # If all items are checked, set file_keys_input to "all"
        table_item_counts = self.file_list_table.rowCount()
        checked_items = sum([1 for row_idx in range(table_item_counts)
                             if self.file_list_table.item(row_idx, 0).checkState() == Qt.CheckState.Checked])
        if checked_items == table_item_counts:
            self.file_keys_input.setText("all")
            self.dataset_description.setText(
                f"Selected Dataset: ({self.current_dataset_id}) {self.current_dataset_title}")
            self.dataset_size_description.setText(
                f"Selected: {sizeof_fmt(self.current_total_file_size)} / Total: {sizeof_fmt(self.current_total_file_size)}"
            )
            return

        file_keys = []
        selected_file_size = 0
        for row_idx in range(table_item_counts):
            if self.file_list_table.item(row_idx, 0).checkState() == Qt.CheckState.Checked:
                file_key = self.file_list_table.item(row_idx, 1).text()
                file_keys.append(file_key)
                selected_file_size += self.file_db.get(file_key, (None, 0, 0, 0))[1]

        self.dataset_description.setText(
            f"Selected Dataset: ({self.current_dataset_id}) {self.current_dataset_title}")
        self.dataset_size_description.setText(
            f"Selected: {sizeof_fmt(selected_file_size)} / Total: {sizeof_fmt(self.current_total_file_size)}"
        )
        self.file_keys_input.setText(",".join(file_keys))

    def toggle_filekey(self, event):
        QTableWidget.keyPressEvent(self.file_list_table, event)
        if event.key() == Qt.Key.Key_Space:
            selected_items = self.file_list_table.selectedItems()
            if not selected_items:
                return

            checkbox_items = [item for item in selected_items if item.column() == 0]
            if not checkbox_items:
                return
            first_item_state = checkbox_items[0].checkState()

            for item in checkbox_items:
                item.setCheckState(Qt.CheckState.Checked if first_item_state ==
                                   Qt.CheckState.Unchecked else Qt.CheckState.Unchecked)
            self.update_filekey_list()

    def choose_dataset(self):
        # Update dataset ID to selectd items
        selected_items = self.dataset_table.selectedItems()
        if not selected_items:
            return

        # Update input form
        self.current_dataset_id = selected_items[0].text()
        self.current_dataset_title = selected_items[1].text()
        self.dataset_description.setText(f"Selected Dataset: ({self.current_dataset_id}) {self.current_dataset_title}")
        self.dataset_key_input.setText(self.current_dataset_id)

        # Fetch file list
        file_tree = self.downloader.get_file_tree(self.current_dataset_id)
        if file_tree:
            # Unlink the signal first
            self.file_list_table.cellChanged.disconnect(self.on_checkbox_changed)

            # Clear contents first
            self.file_list_table.clearContents()

            # Parse file tree
            parser = AIHubResponseParser()
            tree, paths = parser.parse_tree_output(file_tree)

            if paths:
                # Get file path without folders
                file_paths = [item for item in paths if item[1]]  # Filter only is_file=True

                self.file_list_table.setRowCount(len(file_paths))
                self.file_db.clear()

                self.current_total_file_size = 0
                for row, (path, _, file_key, (file_display_size, file_min_size, file_max_size)) in enumerate(file_paths):
                    self.current_total_file_size += file_display_size
                    # Append to File DB
                    self.file_db[file_key] = (path, file_display_size, file_min_size, file_max_size)

                    wit_checkbox = QTableWidgetItem()   # Checkbox
                    wit_checkbox.setFlags(wit_checkbox.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    wit_checkbox.setFlags(wit_checkbox.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    wit_checkbox.setCheckState(Qt.CheckState.Checked)
                    wit_checkbox.setData(Qt.ItemDataRole.UserRole, file_key)

                    self.file_list_table.setItem(row, 0, wit_checkbox)
                    wit_key = QTableWidgetItem(file_key)  # Key
                    wit_key.setFlags(wit_key.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    self.file_list_table.setItem(row, 1, wit_key)
                    wit_filename = QTableWidgetItem(path)  # Filename
                    wit_filename.setFlags(wit_filename.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    self.file_list_table.setItem(row, 2, wit_filename)
                    # Display size (from AIHub API)
                    wit_size = QTableWidgetItem(sizeof_fmt(file_display_size, ignore_float=True))
                    wit_size.setFlags(wit_size.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    self.file_list_table.setItem(row, 3, wit_size)

                # Update total file size
                self.dataset_description.setText(
                    f"Selected Dataset: ({self.current_dataset_id}) {self.current_dataset_title}")
                self.dataset_size_description.setText(
                    f"Selected Total: {sizeof_fmt(self.current_total_file_size)}"
                )
        else:
            # Failed fetching file tree
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Error")
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.setIcon(QMessageBox.Icon.Warning)
            dialog.setText(
                f"Failed fetching '({self.current_dataset_id}) {self.current_dataset_title}'."
            )
            dialog.exec()
        self.file_list_table.cellChanged.connect(self.on_checkbox_changed)

    def search_dataset(self, value):
        # Search for dataset ID/Name by the query "self.dataset_search_query" and filter the results on
        if value == "":
            self.search_query = AIHubDownloaderGUI.DATASET_SEARCH_DEFAULT_QUERY
        else:
            self.search_query = value
        self.update_dataset_list_table()

    def reset_credential(self):
        self.auth.aihub_id = None
        self.auth.aihub_pw = None
        self.auth.clear_credential()
        self.id_input.clear()
        self.pw_input.clear()
        self.download_button.setEnabled(False)
        self.id_input.setDisabled(False)
        self.pw_input.setDisabled(False)
        self.auth_button.setText("Authenticate")
        self.auth_button.clicked.disconnect(self.reset_credential)
        self.auth_button.clicked.connect(self.authenticate)
        self.log_status("Credential reset.")

    def authenticate(self):
        self.auth.aihub_id = self.id_input.text()
        self.auth.aihub_pw = self.pw_input.text()

        auth_headers = self.auth.authenticate()
        if auth_headers:
            self.downloader = AIHubDownloader(auth_headers)
            self.download_button.setEnabled(True)
            self.id_input.setDisabled(True)
            self.pw_input.setDisabled(True)
            self.auth_button.setText("Logout")
            self.auth_button.clicked.disconnect(self.authenticate)
            self.auth_button.clicked.connect(self.reset_credential)
            self.log_status("Authentication successful.")

            # Check whether to save
            if not self.auth.autosave_enabled:
                dialog = QMessageBox(self)
                dialog.setWindowTitle("Credential Alert")
                dialog.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                dialog.setIcon(QMessageBox.Icon.Question)
                dialog.setText(
                    f"Do you want AIHubDownloader to save credential to '{AIHubConfig.CONFIG_PATH}'?"
                )
                button = dialog.exec()
                if button == QMessageBox.StandardButton.Yes:
                    self.auth.autosave_enabled = True
                    self.auth.save_credential()

        else:
            self.log_status("Authentication failed.")

    def browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_input.setText(directory)
            config_manager = AIHubConfig.get_instance()
            config_manager.config_db["last_output_dir"] = directory
            config_manager.save_to_disk()

    def start_download(self):
        dataset_key = self.dataset_key_input.text()
        file_keys = self.file_keys_input.text()
        output_dir = self.output_dir_input.text()

        if not dataset_key or not output_dir:
            self.log_status("Please provide dataset key and output directory.")
            return

        if not file_keys.strip():
            self.log_status("No file selected for download.")
            return

        # Estimate the file size
        min_total_size = 0
        max_total_size = 0
        for file_key in file_keys.split(","):
            _, display_size, min_size, max_size = self.file_db.get(file_key, (None, None, 0, 0))
            min_total_size += min_size
            max_total_size += max_size

        # Check for availabe disk space on args.output directory
        fstat = os.statvfs(output_dir)
        available_space = fstat.f_frsize * fstat.f_bavail

        self.log_status(
            f"Estimated download size: {sizeof_fmt(min_total_size)} ~ {sizeof_fmt(max_total_size)}"
        )
        self.log_status(
            f"Free disk space: {sizeof_fmt(available_space)}"
        )

        # Update progressbar total (in bytes)
        # self.progress_bar.setMinimum(0)
        # self.progress_bar.setMaximum(max_total_size)

        self.download_thread = DownloadThread(
            self.downloader, dataset_key, file_keys, output_dir
        )
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()

        self.is_downloading = True

        self.download_button.setEnabled(False)
        self.auth_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.dataset_list_button.setEnabled(False)
        self.dataset_search_query.setEnabled(False)
        self.dataset_list_csv_save_button.setEnabled(False)
        self.log_status(f"Downloading dataset {dataset_key}")

    def update_progress(self, value):
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(value)

    def download_finished(self, success):
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimum(100)
        self.progress_bar.setValue(100)

        if success:
            self.log_status("Download and extraction completed.")
        else:
            self.log_status("Download failed.")

        self.is_downloading = False
        self.download_button.setEnabled(True)
        self.auth_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.dataset_list_button.setEnabled(True)
        self.dataset_search_query.setEnabled(True)
        self.dataset_list_csv_save_button.setEnabled(True)

    def log_status(self, message):
        date_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_log.append(f"[{date_string}] {message}")

    def update_dataset_list_table(self):
        # Get the entries by the query (using regex)
        try:
            exp = re.compile(self.search_query, re.IGNORECASE)
        except re.error:
            exp = re.compile(re.escape(self.search_query), re.IGNORECASE)
        entries = [
            item
            for item in self.dataset_db
            if exp.search(item[0]) or exp.search(item[1])
        ]

        # Update table entries
        self.dataset_table.clearContents()
        self.dataset_table.setRowCount(len(entries))
        for row, (dataset_id, dataset_name) in enumerate(entries):
            wit_id = QTableWidgetItem(dataset_id)
            wit_id.setFlags(wit_id.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.dataset_table.setItem(row, 0, wit_id)
            wit_name = QTableWidgetItem(dataset_name)
            wit_name.setFlags(wit_name.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.dataset_table.setItem(row, 1, wit_name)

    def save_to_csv(self):
        datasets = self.update_dataset_list()
        if datasets:
            # Export to CSV
            csv_filename, _ = QFileDialog.getSaveFileName(
                self, "Save Dataset List", "", "CSV Files (*.csv)"
            )
            if csv_filename:
                self.downloader.export_dataset_list_to_csv(datasets, csv_filename)
                self.log_status(f"Dataset list exported to {csv_filename}")

    def update_dataset_list(self):
        self.dataset_db.clear()
        self.dataset_table.clearContents()

        datasets = self.downloader.get_dataset_info()
        if datasets:
            # Update dataset database
            for dataset_id, dataset_name in datasets:
                self.dataset_db.append((dataset_id, dataset_name))

            # Sort dataset by dataset id
            self.dataset_db = natsorted(self.dataset_db, key=lambda x: x[0])

            # Reset query and Update dataset list table
            self.update_dataset_list_table()
        else:
            self.log_status("Failed to fetch dataset information.")
        return datasets


def main():
    app = QApplication([])
    window = AIHubDownloaderGUI()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()