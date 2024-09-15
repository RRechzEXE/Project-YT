import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QWidget, QMessageBox, QComboBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QMovie, QPixmap
import yt_dlp
import os
import re

class DownloadThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, url, format_id):
        super().__init__()
        self.url = url
        self.format_id = format_id

    def run(self):
        ydl_opts = {
            'format': self.format_id,
            'outtmpl': '%(title)s.%(ext)s',
            'progress_hooks': [self.progress_hook],
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([self.url])
                self.finished_signal.emit("Download completed successfully!")
            except Exception as e:
                self.error_signal.emit(f"An error occurred: {str(e)}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('progress', 0)
            eta = d.get('eta', 0)
            speed = d.get('speed', 0)
            total = d.get('total_bytes', 0)
            progress_text = f"{percent:.1f}% of {total} at {speed}/s ETA {eta}"
            self.progress_signal.emit(progress_text)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Ana pencereyi 9:16 oranında ayarlıyoruz
        self.setWindowTitle("Project YT")
        self.setGeometry(100, 100, 360, 640)  # 9:16 oranı

        # Ana widget ve layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Üst kısımda yatay bir layout (sol üst köşe butonları için)
        top_button_layout = QHBoxLayout()

        # Sol üst köşeye küçük boyutlu butonlar
        self.settings_btn = QPushButton("Settings")
        self.help_btn = QPushButton("Help")
        self.support_btn = QPushButton("Support")
        self.wallpapers_btn = QPushButton("Wallpapers")

        # Buton boyutlarını küçültme
        button_list = [self.settings_btn, self.help_btn, self.support_btn, self.wallpapers_btn]
        for btn in button_list:
            btn.setFixedSize(70, 25)  # Butonları küçültmek için sabit boyut verdik

        # Butonları yatay layout'a ekleyip sola hizalıyoruz
        top_button_layout.addWidget(self.settings_btn)
        top_button_layout.addWidget(self.help_btn)
        top_button_layout.addWidget(self.support_btn)
        top_button_layout.addWidget(self.wallpapers_btn)
        top_button_layout.addStretch()  # Butonları sola sabitlemek için boşluk bırakıyoruz

        # URL giriş alanı
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter YouTube URL here")

        # Video bilgisi göstermek için yer tutucu label
        self.video_info = QLabel("Video information will appear here.")
        self.video_info.setAlignment(Qt.AlignCenter)

        # Çözünürlük ve ses formatları seçimleri için combobox
        self.format_combobox = QComboBox(self)

        # Fetch Video Info butonu
        self.fetch_info_btn = QPushButton("Fetch Video Info")
        self.fetch_info_btn.clicked.connect(self.fetch_video_info)

        # Download butonu
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)

        # Yüklenme animasyonu için bir QLabel (başlangıçta boş olacak)
        self.loading_label = QLabel(self)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_movie = QMovie("C:/ProjectYT-NightDownload/Animations/loading.gif")  # Yüklenme animasyonu için bir GIF dosyası
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setVisible(False)  # Başlangıçta görünmez olacak

        # Ana layout'a eklemeler (buton layout'u ve diğer widget'lar)
        main_layout.addLayout(top_button_layout)  # Sol üst köşe butonları ekleniyor
        main_layout.addWidget(self.url_input)
        main_layout.addWidget(self.fetch_info_btn)
        main_layout.addWidget(self.format_combobox)  # Format combobox ekleniyor
        main_layout.addWidget(self.download_btn)  # Download butonu ekleniyor
        main_layout.addWidget(self.loading_label)  # Yüklenme animasyonunu ekliyoruz
        main_layout.addWidget(self.video_info)

        # Ana widget'ı ayarlıyoruz
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def fetch_video_info(self):
        url = self.url_input.text()

        # Yüklenme animasyonunu başlat
        self.start_loading_animation()

        video_title, video_duration, formats = self.get_video_info(url)

        if video_title:
            format_options = []
            for f in formats:
                format_note = f.get('format_note', 'No note available')
                format_id = f.get('format_id', 'No ID available')
                format_options.append(f"{format_note} - {format_id}")

            self.format_combobox.clear()
            self.format_combobox.addItems(format_options)

            self.video_info.setText(f"Title: {video_title}\nDuration: {video_duration}s")
            self.stop_loading_animation()  # Animasyonu durdur
        else:
            self.show_error_animation()  # Hata durumunda animasyonu değiştirme

    def get_video_info(self, url):
        ydl_opts = {
            'skip_download': True,  # Sadece bilgiyi almak için indirilmeyi atlıyoruz
            'quiet': True  # Konsolda çok fazla çıktı olmasın diye
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
        if self.format_combobox.currentIndex() == -1:
            QMessageBox.warning(self, "Error", "Please select a format before downloading.")
            return

        format_id = self.format_combobox.currentText().split(' - ')[-1]
        url = self.url_input.text()

        # Yüklenme animasyonunu başlat
        self.start_loading_animation()

        # DownloadThread ile indirme işlemini başlat
        self.download_thread = DownloadThread(url, format_id)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.on_download_finished)
        self.download_thread.error_signal.connect(self.show_error)
        self.download_thread.start()

    def update_progress(self, progress_text):
        self.video_info.setText(progress_text)

    def on_download_finished(self, message):
        self.stop_loading_animation()
        QMessageBox.information(self, "Download Finished", message)

    def show_error(self, error_message):
        self.stop_loading_animation()
        QMessageBox.critical(self, "Error", error_message)

    def start_loading_animation(self):
        self.video_info.clear()  # Mevcut video bilgisini temizle
        self.loading_label.setVisible(True)  # Yüklenme animasyonunu göster
        self.loading_movie.start()  # Animasyonu başlat

    def stop_loading_animation(self):
        self.loading_movie.stop()  # Animasyonu durdur
        self.loading_label.setVisible(False)  # Animasyonu gizle

    def show_error_animation(self):
        self.loading_movie.stop()  # Mevcut animasyonu durdur
        error_pixmap = QPixmap("C:\\ProjectYT-NightDownload\\Animations\\error.png")  # Kırmızı ünlem işareti (PNG dosyası)
        self.loading_label.setPixmap(error_pixmap)  # Hata simgesini göster

# Uygulamayı başlat
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
