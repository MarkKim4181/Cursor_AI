import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PIL import Image
import io

class ImageProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.selected_image_path = None
        self.preview_images = []  # 미리보기 이미지들 (PIL)

    def initUI(self):
        self.setWindowTitle('이미지 처리 프로그램')
        self.setGeometry(100, 100, 1200, 700)

        # 중앙 위젯 생성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 미리보기 레이아웃
        self.preview_layout = QHBoxLayout()
        layout.addLayout(self.preview_layout)

        # 이미지 선택 버튼
        self.select_button = QPushButton('이미지 선택')
        self.select_button.clicked.connect(self.select_image)
        layout.addWidget(self.select_button)

        # 파일 생성 버튼 (처음엔 비활성화)
        self.save_button = QPushButton('파일을 생성하시겠습니까?')
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_files)
        layout.addWidget(self.save_button)

    def select_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "이미지 선택", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_name:
            self.selected_image_path = file_name
            self.make_previews()
            # 다운로드 폴더 열기 (Windows)
            try:
                download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
                if os.path.exists(download_path):
                    subprocess.Popen(f'explorer "{download_path}"')
            except Exception as e:
                print(f"다운로드 폴더 열기 오류: {e}")

    def make_previews(self):
        # 기존 미리보기 제거
        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.preview_images = []

        # 이미지 열기
        img = Image.open(self.selected_image_path).convert('RGBA')
        # 80% 크기(800x800)로 리사이즈
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        img_w, img_h = img.size
        y_margin = (1000 - img_h) // 2

        # 1개: 중앙 배치
        canvas = Image.new('RGBA', (1000, 1000), 'white')
        x = (1000 - img_w) // 2
        canvas.paste(img, (x, y_margin), img)
        self.preview_images.append(canvas)
        self.preview_layout.addLayout(self.make_preview_box(canvas, '1개 썸네일'))

        # 2개: 좌/우 배치 (좌우 100px 여백, 800픽셀 내에서)
        canvas2 = Image.new('RGBA', (1000, 1000), 'white')
        w = (800 - 40) // 2
        h = int(img_h * (w / img_w))
        img2 = img.resize((w, h), Image.Resampling.LANCZOS)
        y2 = (1000 - h) // 2
        canvas2.paste(img2, (100, y2), img2)
        canvas2.paste(img2, (100 + w + 40, y2), img2)
        self.preview_images.append(canvas2)
        self.preview_layout.addLayout(self.make_preview_box(canvas2, '2개 썸네일'))

        # 3개: 좌/중/우 배치 (좌우 100px, 이미지간 30px, 800픽셀 내에서)
        canvas3 = Image.new('RGBA', (1000, 1000), 'white')
        w = (800 - 2 * 30) // 3
        h = int(img_h * (w / img_w))
        img3 = img.resize((w, h), Image.Resampling.LANCZOS)
        y3 = (1000 - h) // 2
        for i in range(3):
            x3 = 100 + i * (w + 30)
            canvas3.paste(img3, (x3, y3), img3)
        self.preview_images.append(canvas3)
        self.preview_layout.addLayout(self.make_preview_box(canvas3, '3개 썸네일'))

        self.save_button.setEnabled(True)

    def make_preview_box(self, pil_img, text):
        # 미리보기 이미지와 텍스트를 세로로 쌓는 레이아웃 반환
        vbox = QVBoxLayout()
        label_img = self.pil_to_label(pil_img)
        label_txt = QLabel(text)
        label_txt.setAlignment(Qt.AlignHCenter)
        vbox.addWidget(label_img)
        vbox.addWidget(label_txt)
        return vbox

    def pil_to_label(self, pil_img):
        # PIL 이미지를 QPixmap으로 변환하여 QLabel에 표시
        buf = io.BytesIO()
        pil_img.convert('RGB').save(buf, format='PNG')
        qimg = QImage.fromData(buf.getvalue())
        pixmap = QPixmap.fromImage(qimg).scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label = QLabel()
        label.setPixmap(pixmap)
        label.setFixedSize(260, 260)
        label.setStyleSheet("border: 1px solid #aaa; background: #eee;")
        label.setAlignment(Qt.AlignHCenter)
        return label

    def save_files(self):
        reply = QMessageBox.question(self, '파일 생성', '썸네일 파일을 생성하시겠습니까?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for idx, img in enumerate(self.preview_images, 1):
                img.convert('RGB').save(f'{idx}.jpg')
            QMessageBox.information(self, '완료', '파일이 성공적으로 저장되었습니다.')
        else:
            QMessageBox.information(self, '취소', '파일 저장이 취소되었습니다.')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageProcessor()
    ex.show()
    sys.exit(app.exec_())
