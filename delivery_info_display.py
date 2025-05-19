import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer

class DeliveryInfoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('택배 송장 정보')
        self.setGeometry(100, 100, 600, 400)

        # 중앙 위젯 생성
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 배송 정보 텍스트
        delivery_info = """택배사: CJ대한통운
송장번호: 510241087055
받는 사람: 김미옥
배송지: 충북 충주시 풍동동막길 50 나동 604호 (풍동, 신한강변아파트)
주문 상품: 비피젠 퓨어 비피더스 프리미엄 100억 CFU 30캡슐 2box 2개월분
배송 예정일: 2025. 05. 17.(토) 도착 예정"""

        # 텍스트 에디트 위젯 생성
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont('맑은 고딕', 11))
        self.text_edit.setPlainText(delivery_info)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        # 복사 버튼 생성
        copy_button = QPushButton('전체 텍스트 복사')
        copy_button.clicked.connect(self.copy_text)
        layout.addWidget(copy_button)

        # 복사 상태 라벨
        self.status_label = QLabel('')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        self.status_label.setText('텍스트가 클립보드에 복사되었습니다!')
        # 2초 후 상태 메시지 제거
        QTimer.singleShot(2000, lambda: self.status_label.setText(''))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DeliveryInfoWindow()
    window.show()
    sys.exit(app.exec_()) 