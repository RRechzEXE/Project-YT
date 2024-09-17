import sys
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, 
                             QWidget, QMessageBox, QComboBox, QDialog, QRadioButton, QButtonGroup, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QMovie
import yt_dlp
import os

class ThemeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Theme")
        self.setGeometry(100, 100, 200, 100)
        layout = QVBoxLayout()

        self.dark_theme_radio = QRadioButton("Dark Theme")
        self.light_theme_radio = QRadioButton("Light Theme")
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.dark_theme_radio)
        self.button_group.addButton(self.light_theme_radio)

        layout.addWidget(self.dark_theme_radio)
        layout.addWidget(self.light_theme_radio)

        self.dark_theme_radio.setChecked(False)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.apply_theme)
        layout.addWidget(ok_button)
        self.setLayout(layout)

    def apply_theme(self):
        if self.dark_theme_radio.isChecked():
            self.parent().apply_dark_theme()
        elif self.light_theme_radio.isChecked():
            self.parent().apply_light_theme()
        self.accept()

class DownloadThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, url, format_id):
        super().__init__()
        self.url = url
        self.format_id = format_id
        self.log_file = 'download_logs.txt'
        self.init_log_file()

    def init_log_file(self):
        """Initialize the log file by creating or clearing it."""
        with open(self.log_file, 'w') as f:
            f.write('Download Logs\n')
            f.write('===============\n\n')

    def log(self, message):
        """Append a message to the log file."""
        with open(self.log_file, 'a') as f:
            f.write(f"{message}\n")

    def run(self):
        self.log(f"Starting download: URL={self.url}, Format={self.format_id}")
        ydl_opts = {
            'format': self.format_id,
            'outtmpl': '%(title)s.%(ext)s',
            'progress_hooks': [self.progress_hook],
            'quiet': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
                self.finished_signal.emit("Download completed successfully!")
                self.log("Download completed successfully!")
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            self.error_signal.emit(error_message)
            self.log(error_message)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('progress', 0)
            eta = d.get('eta', 0)
            speed = d.get('speed', 0)
            total = d.get('total_bytes', 0)
            progress_text = f"{percent:.1f}% of {total} at {speed / (1024 ** 2):.1f} MB/s ETA {eta}"
            self.progress_signal.emit(progress_text)
            self.log(progress_text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Project YT | OpenBETA V0.3.0")
        self.setGeometry(100, 100, 360, 640)

        self.current_theme = 'light'  # Initialize theme state
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        top_button_layout = QHBoxLayout()

        self.settings_btn = QPushButton("Settings")
        self.help_btn = QPushButton("Help")
        self.support_btn = QPushButton("Support")
        self.wallpapers_btn = QPushButton("Wallpapers")

        button_list = [self.settings_btn, self.help_btn, self.support_btn, self.wallpapers_btn]
        for btn in button_list:
            btn.setFixedSize(70, 25)

        top_button_layout.addWidget(self.settings_btn)
        top_button_layout.addWidget(self.help_btn)
        top_button_layout.addWidget(self.support_btn)
        top_button_layout.addWidget(self.wallpapers_btn)
        top_button_layout.addStretch()

        self.settings_btn.clicked.connect(self.open_settings_dialog)
        self.help_btn.clicked.connect(lambda: self.open_link("https://discord.gg/geDSnXCq"))
        self.support_btn.clicked.connect(lambda: self.open_link("https://discord.gg/geDSnXCq"))
        self.wallpapers_btn.clicked.connect(lambda: self.open_link("https://t.me/WallsHunterHQ"))

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter YouTube URL here")

        self.video_info = QLabel("Video information will appear here.")
        self.video_info.setAlignment(Qt.AlignCenter)

        self.video_format_combobox = QComboBox(self)
        self.audio_format_combobox = QComboBox(self)

        self.fetch_info_btn = QPushButton("Fetch Video Info")
        self.fetch_info_btn.clicked.connect(self.fetch_video_info)

        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)

        self.loading_label = QLabel(self)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_movie = QMovie("C:/ProjectYT-NightDownload/Animations/loading.gif")
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setVisible(False)

        # Modern progress bar setup
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(""" 
            QProgressBar { 
                border: 1px solid #bbb; 
                border-radius: 5px; 
                background-color: #f0f0f0; 
                height: 25px; 
            } 
            QProgressBar::chunk { 
                background-color: #5cb85c; 
                width: 10px; 
                margin: 1px; 
            } 
        """)
        self.progress_bar.setValue(0)

        # Speed and ETA labels
        self.speed_label = QLabel("Speed: 0 MB/s", self)
        self.speed_label.setAlignment(Qt.AlignCenter)

        self.eta_label = QLabel("ETA: calculating...", self)
        self.eta_label.setAlignment(Qt.AlignCenter)

        main_layout.addLayout(top_button_layout)
        main_layout.addWidget(self.url_input)
        main_layout.addWidget(self.fetch_info_btn)
        main_layout.addWidget(self.video_format_combobox)
        main_layout.addWidget(self.audio_format_combobox)
        main_layout.addWidget(self.download_btn)
        main_layout.addWidget(self.loading_label)
        main_layout.addWidget(self.video_info)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.speed_label)
        main_layout.addWidget(self.eta_label)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def fetch_video_info(self):
        url = self.url_input.text()
        self.start_loading_animation()

        video_title, video_duration, formats = self.get_video_info(url)

        if video_title:
            video_format_options = []
            audio_format_options = []

            for f in formats:
                format_note = f.get('format_note', 'Unknown format')
                format_id = f.get('format_id', 'Unknown ID')
                height = f.get('height')
                vcodec = f.get('vcodec', 'Unknown codec')
                acodec = f.get('acodec', 'Unknown codec')

                if height:
                    video_format_options.append(f"{format_note} - {height}p ({vcodec}) - {format_id}")
                else:
                    audio_format_options.append(f"{format_note} - ({acodec}) - {format_id}")

            self.video_format_combobox.clear()
            self.audio_format_combobox.clear()
            self.video_format_combobox.addItems(video_format_options)
            self.audio_format_combobox.addItems(audio_format_options)

            self.video_info.setText(f"Title: {video_title}\nDuration: {video_duration}s")
            self.stop_loading_animation()
        else:
            self.show_error_animation()

    def get_video_info(self, url):
        ydl_opts = {
            'skip_download': True,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=False)
                video_title = info_dict.get('title', 'No title available')
                video_duration = info_dict.get('duration', 'Unknown duration')
                formats = info_dict.get('formats', [])
                return video_title, video_duration, formats
            except Exception as e:
                return None, None, None

    def start_download(self):
        if self.video_format_combobox.currentIndex() == -1 or self.audio_format_combobox.currentIndex() == -1:
            QMessageBox.warning(self, "Error", "Please select both video and audio formats.")
            return

        video_format_id = self.video_format_combobox.currentText().split(' - ')[-1]
        audio_format_id = self.audio_format_combobox.currentText().split(' - ')[-1]
        url = self.url_input.text()

        self.start_loading_animation()

        self.download_thread = DownloadThread(url, f"{video_format_id}+{audio_format_id}")
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.error_signal.connect(self.show_error)
        self.download_thread.start()

    def update_progress(self, progress_text):
        try:
            # Parsing progress text
            percent = float(progress_text.split('%')[0].strip())
            percent_int = int(percent)  # convert to int for QProgressBar
            speed = progress_text.split('at')[1].split('/s')[0].strip()
            eta = progress_text.split('ETA')[1].strip()

            self.progress_bar.setValue(percent_int)
            self.speed_label.setText(f"Speed: {speed} MB/s")
            self.eta_label.setText(f"ETA: {eta}")
        except Exception as e:
            pass

    def on_download_finished(self, message):
        self.stop_loading_animation()
        self.progress_bar.setValue(100)
        self.speed_label.setText("Speed: Completed")
        self.eta_label.setText("ETA: 00:00:00")
        QMessageBox.information(self, "Download Completed", message)

    def show_error(self, error_message):
        self.stop_loading_animation()
        QMessageBox.critical(self, "Error", error_message)

    def start_loading_animation(self):
        self.loading_label.setVisible(True)
        self.loading_movie.start()

    def stop_loading_animation(self):
        self.loading_movie.stop()
        self.loading_label.setVisible(False)

    def show_error_animation(self):
        self.loading_label.setVisible(True)
        # Optional: implement an error animation or message.
        self.loading_movie.stop()

    def open_settings_dialog(self):
        dialog = ThemeDialog(self)
        dialog.exec_()

    def open_link(self, url):
        webbrowser.open(url)

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        self.setPalette(palette)

        # Button styles for dark theme
        self.settings_btn.setStyleSheet("background-color: #444; color: white;")
        self.help_btn.setStyleSheet("background-color: #444; color: white;")
        self.support_btn.setStyleSheet("background-color: #444; color: white;")
        self.wallpapers_btn.setStyleSheet("background-color: #444; color: white;")

        self.current_theme = 'dark'

    def apply_light_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, Qt.white)
        palette.setColor(QPalette.WindowText, Qt.black)
        palette.setColor(QPalette.Base, QColor(240, 240, 240))
        palette.setColor(QPalette.AlternateBase, Qt.white)
        palette.setColor(QPalette.ToolTipBase, Qt.black)
        palette.setColor(QPalette.ToolTipText, Qt.black)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.Button, QColor(200, 200, 200))
        palette.setColor(QPalette.ButtonText, Qt.black)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        self.setPalette(palette)

        # Button styles for light theme
        self.settings_btn.setStyleSheet("background-color: #eee; color: black;")
        self.help_btn.setStyleSheet("background-color: #eee; color: black;")
        self.support_btn.setStyleSheet("background-color: #eee; color: black;")
        self.wallpapers_btn.setStyleSheet("background-color: #eee; color: black;")

        self.current_theme = 'light'

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
