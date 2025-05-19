import os
import subprocess
from tempfile import NamedTemporaryFile

def create_delivery_note():
    # 배송 정보 텍스트
    delivery_info = """택배사: CJ대한통운
송장번호: 510241087055
받는 사람: 김미옥
배송지: 충북 충주시 풍동동막길 50 나동 604호 (풍동, 신한강변아파트)
주문 상품: 비피젠 퓨어 비피더스 프리미엄 100억 CFU 30캡슐 2box 2개월분
배송 예정일: 2025. 05. 17.(토) 도착 예정"""

    try:
        # 임시 텍스트 파일 생성
        with NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(delivery_info)
            temp_path = temp_file.name

        # 메모장으로 파일 열기
        subprocess.Popen(['notepad.exe', temp_path])

    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    create_delivery_note() 