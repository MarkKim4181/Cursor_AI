import tkinter as tk
from PIL import Image, ImageTk
import re
from io import BytesIO
import win32clipboard # type: ignore
import struct
import numpy as np
import cv2
import os
from tkinter import messagebox

try:
    import pytesseract
except ImportError:
    pytesseract = None

# PNG 포맷 클립보드 상수 (윈도우 10 이상)
CF_PNG = None
try:
    CF_PNG = win32clipboard.RegisterClipboardFormat('PNG')
except Exception:
    pass

# Tesseract 설치 확인
def check_tesseract():
    if pytesseract is None:
        return None
        
    paths_to_check = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        os.path.join(os.getenv('LOCALAPPDATA', ''), 'Programs', 'Tesseract-OCR', 'tesseract.exe'),
        r'D:\Tesseract-OCR\tesseract.exe'
    ]
    
    for path in paths_to_check:
        if os.path.isfile(path):
            return path
    return None

def get_clipboard_image():
    """클립보드에서 이미지를 가져오는 함수"""
    image = None
    
    try:
        formats = []
        win32clipboard.OpenClipboard()
        
        # 사용 가능한 형식 확인
        format_index = 0
        while True:
            try:
                format_id = win32clipboard.EnumClipboardFormats(format_index)
                if format_id == 0:
                    break
                formats.append(format_id)
                format_index = format_id
            except:
                break
        
        # PNG 형식 확인
        try:
            CF_PNG = win32clipboard.RegisterClipboardFormat('PNG')
            if CF_PNG in formats:
                data = win32clipboard.GetClipboardData(CF_PNG)
                if isinstance(data, bytes):
                    image = Image.open(BytesIO(data))
                    win32clipboard.CloseClipboard()
                    return image
        except:
            pass

        # DIB 형식 확인
        if win32clipboard.CF_DIB in formats:
            try:
                data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                # 기본 방식으로 시도
                try:
                    image = Image.open(BytesIO(data))
                except:
                    # DIB 헤더 분석
                    header_size = struct.unpack_from('I', data, 0)[0]
                    width = struct.unpack_from('i', data, 4)[0]
                    height = struct.unpack_from('i', data, 8)[0]
                    bits = struct.unpack_from('H', data, 14)[0]
                    
                    # 음수 높이 처리 (상하 반전)
                    height = abs(height)
                    
                    # 채널 수 계산
                    channels = bits // 8
                    if channels not in [3, 4]:
                        channels = 4  # 기본값으로 BGRA 사용
                    
                    # 픽셀 데이터 추출
                    pixel_data = data[header_size:]
                    
                    # 이미지 데이터 크기 계산
                    stride = ((width * bits + 31) // 32) * 4  # 4바이트 정렬
                    expected_size = stride * height
                    
                    if len(pixel_data) >= expected_size:
                        # 이미지 배열 생성
                        img_array = np.frombuffer(pixel_data[:expected_size], dtype=np.uint8)
                        try:
                            # 채널별로 처리
                            if channels == 4:
                                img_array = img_array.reshape(height, stride // 4, 4)
                                img_array = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGB)
                            else:
                                img_array = img_array.reshape(height, stride // 3, 3)
                                img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                            
                            # 실제 너비로 자르기
                            img_array = img_array[:, :width]
                            image = Image.fromarray(img_array)
                        except Exception as e:
                            print("이미지 변환 오류:", e)
                            
            except Exception as e:
                print("DIB 처리 오류:", e)
        
        win32clipboard.CloseClipboard()
        return image
        
    except Exception as e:
        print("클립보드 접근 오류:", e)
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
        return None

class TrackingNumberExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("카카오톡 송장번호 추출기")
        self.root.geometry("500x800")
        
        # 안내 라벨
        self.instruction_label = tk.Label(
            self.root, 
            text="1. 카카오톡/GPT에서 송장번호 이미지를 복사\n2. 아래 버튼을 클릭하거나 Ctrl+V를 누르세요",
            font=("맑은 고딕", 10),
            wraplength=450
        )
        self.instruction_label.pack(pady=10)

        # 이미지 표시 영역
        self.image_label = tk.Label(self.root)
        self.image_label.pack(pady=10)

        # 붙여넣기 버튼
        self.paste_button = tk.Button(
            self.root, 
            text="이미지 붙여넣기 (Ctrl+V)", 
            command=self.paste_image,
            font=("맑은 고딕", 11)
        )
        self.paste_button.pack(pady=5)

        # OCR 결과 프레임
        ocr_frame = tk.LabelFrame(self.root, text="추출된 텍스트", font=("맑은 고딕", 10))
        ocr_frame.pack(pady=10, padx=10, fill='x')
        
        self.ocr_text = tk.Text(ocr_frame, height=4, font=("맑은 고딕", 10))
        self.ocr_text.pack(pady=5, padx=5, fill='x')

        # 결과 프레임
        result_frame = tk.LabelFrame(self.root, text="인식 결과", font=("맑은 고딕", 10))
        result_frame.pack(pady=10, padx=10, fill='x')

        # 택배사 프레임
        courier_frame = tk.Frame(result_frame)
        courier_frame.pack(pady=5, fill='x')
        
        self.courier_label = tk.Label(courier_frame, text="택배사:", font=("맑은 고딕", 11))
        self.courier_label.pack(side=tk.LEFT, padx=5)
        
        self.courier_result = tk.Label(courier_frame, text="-", font=("맑은 고딕", 11, "bold"))
        self.courier_result.pack(side=tk.LEFT)

        # 송장번호 프레임
        tracking_frame = tk.Frame(result_frame)
        tracking_frame.pack(pady=5, fill='x')
        
        self.tracking_label = tk.Label(tracking_frame, text="송장번호:", font=("맑은 고딕", 11))
        self.tracking_label.pack(side=tk.LEFT, padx=5)
        
        self.tracking_result = tk.Label(tracking_frame, text="-", font=("맑은 고딕", 11, "bold"))
        self.tracking_result.pack(side=tk.LEFT)
        
        self.copy_button = tk.Button(
            tracking_frame,
            text="복사",
            command=self.copy_tracking_number,
            font=("맑은 고딕", 10),
            width=6,
            state=tk.DISABLED
        )
        self.copy_button.pack(side=tk.RIGHT, padx=5)

        # 현재 송장번호 저장
        self.current_tracking_number = None

        # 키보드 바인딩 추가
        self.root.bind('<Control-v>', lambda e: self.paste_image())
        
        # 창 크기 조절 가능하도록 설정
        self.root.resizable(True, True)
        
        # 창 크기가 변경될 때 최소 크기 제한
        self.root.minsize(400, 600)

    def copy_tracking_number(self):
        if self.current_tracking_number and self.current_tracking_number != '-':
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_tracking_number)
            original_text = self.copy_button['text']
            self.copy_button.config(text="✓")
            self.root.after(1000, lambda: self.copy_button.config(text=original_text))
            
            # 복사 성공 메시지를 상태 라벨에 표시
            self.tracking_result.config(text=f"{self.current_tracking_number} (복사됨)")
            self.root.after(2000, lambda: self.tracking_result.config(text=f"{self.current_tracking_number}"))

    def extract_text_from_image(self, image):
        """이미지에서 텍스트 추출"""
        try:
            # 이미지 전처리
            img_array = np.array(image)
            
            # 이미지 크기 조정 (3배 확대)
            img_array = cv2.resize(img_array, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
            
            # 그레이스케일 변환
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # 이미지 전처리 강화
            # 노이즈 제거
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # 대비 향상
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # 적응형 이진화
            binary = cv2.adaptiveThreshold(
                enhanced,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                15,
                5
            )
            
            # 모폴로지 연산으로 텍스트 선명도 향상
            kernel = np.ones((1,1), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 이미지 선명도 향상
            sharpened = cv2.filter2D(binary, -1, np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]]))
            
            # OCR 설정
            custom_config = r'--oem 3 --psm 6 -l kor+eng --tessdata-dir "C:\Program Files\Tesseract-OCR\tessdata"'
            
            # OCR 수행 - 다양한 설정으로 여러 번 시도
            texts = []
            
            # 1. 기본 설정 (개선된 이미지)
            text1 = pytesseract.image_to_string(sharpened, lang='kor+eng', config=custom_config)
            texts.append(text1)
            
            # 2. 원본 이미지
            text2 = pytesseract.image_to_string(img_array, lang='kor+eng', config=custom_config)
            texts.append(text2)
            
            # 3. 반전 이미지
            inverted = cv2.bitwise_not(sharpened)
            text3 = pytesseract.image_to_string(inverted, lang='kor+eng', config=custom_config)
            texts.append(text3)
            
            # 4. 다른 PSM 모드 시도
            text4 = pytesseract.image_to_string(enhanced, lang='kor+eng', config=r'--oem 3 --psm 3 -l kor+eng')
            texts.append(text4)
            
            # 모든 텍스트 결합 및 중복 제거
            all_lines = []
            for text in texts:
                lines = text.split('\n')
                for line in lines:
                    clean_line = line.strip()
                    if clean_line and clean_line not in all_lines and len(clean_line) > 1:
                        # 특수 문자 제거 및 공백 정리
                        clean_line = re.sub(r'[^\w\s가-힣]', ' ', clean_line)
                        clean_line = ' '.join(clean_line.split())
                        if clean_line and clean_line not in all_lines:
                            all_lines.append(clean_line)
            
            # 결과 텍스트 생성
            final_text = '\n'.join(all_lines)
            
            return final_text
            
        except Exception as e:
            print("이미지 처리 오류:", e)
            return ""

    def paste_image(self):
        try:
            # 클립보드에서 이미지 가져오기
            image = get_clipboard_image()
            
            if image is not None:
                # 이미지 크기 조정 (최대 350x500)
                max_w, max_h = 350, 500
                w, h = image.size
                scale = min(max_w/w, max_h/h, 1.0)
                disp_w, disp_h = int(w*scale), int(h*scale)
                display_img = image.resize((disp_w, disp_h), Image.LANCZOS)
                
                # 이미지 표시
                photo = ImageTk.PhotoImage(display_img)
                self.image_label.configure(image=photo)
                self.image_label.image = photo

                # 텍스트 추출
                text = self.extract_text_from_image(image)
                print("추출된 원본 텍스트:", text)
                
                # OCR 결과 표시 - 줄 번호 추가
                self.ocr_text.delete(1.0, tk.END)
                for i, line in enumerate(text.split('\n'), 1):
                    self.ocr_text.insert(tk.END, f"{i}. {line}\n")
                
                # 택배사 및 송장번호 인식
                carrier, tracking_number = self.analyze_text(text)
                
                # 결과 표시
                self.courier_result.config(text=carrier if carrier else "-")
                self.tracking_result.config(text=tracking_number if tracking_number else "-")
                self.current_tracking_number = tracking_number if tracking_number else "-"
                self.copy_button.config(state=tk.NORMAL if tracking_number else tk.DISABLED)
                
            else:
                self.courier_result.config(text="-")
                self.tracking_result.config(text="-")
                self.ocr_text.delete(1.0, tk.END)
                self.ocr_text.insert(tk.END, "이미지를 찾을 수 없습니다\n카카오톡/GPT에서 이미지를 복사해주세요")
                self.copy_button.config(state=tk.DISABLED)
                
        except Exception as e:
            print("에러 발생:", e)
            self.courier_result.config(text="-")
            self.tracking_result.config(text="-")
            self.ocr_text.delete(1.0, tk.END)
            self.ocr_text.insert(tk.END, f"이미지 처리 중 오류 발생: {str(e)}")
            self.copy_button.config(state=tk.DISABLED)

    def analyze_text(self, text):
        """추출된 텍스트에서 택배사와 송장번호 분석"""
        # 택배사 정보
        courier_info = {
            '롯데택배': {
                'keywords': ['롯데택배', '롯데', 'lotte'],
                'pattern': r'2\d{11}|6\d{11}'  # 2 또는 6으로 시작하는 12자리
            },
            'CJ대한통운': {
                'keywords': ['cj대한통운', 'cj택배', '대한통운택배'],
                'pattern': r'51\d{9}'  # 51로 시작하는 11자리
            },
            '우체국': {
                'keywords': ['우체국택배', '우체국', '우편', '등기'],
                'pattern': r'[0-9]{13}'
            },
            '한진택배': {
                'keywords': ['한진택배', '한진', 'hanjin'],
                'pattern': r'[0-9]{12}'
            },
            '로젠택배': {
                'keywords': ['로젠택배', '로젠', 'logen'],
                'pattern': r'[0-9]{11}'
            }
        }

        # 줄별로 분석
        lines = text.split('\n')
        found_company = None
        tracking_number = None

        # 모든 줄의 텍스트를 하나로 합침 (공백 제거)
        full_text = ''.join(text.split())

        # 1. 송장번호 패턴 먼저 검사
        for company, info in courier_info.items():
            matches = re.findall(info['pattern'], full_text)
            for match in matches:
                if company == '롯데택배' and (match.startswith('2') or match.startswith('6')):
                    return company, match
                elif company == 'CJ대한통운' and match.startswith('51'):
                    return company, match
                elif company not in ['롯데택배', 'CJ대한통운']:
                    tracking_number = match
                    found_company = company

        # 2. 키워드로 택배사 찾기
        if not found_company:
            for line in lines:
                clean_line = line.lower().replace(' ', '')
                for company, info in courier_info.items():
                    if any(keyword.lower() in clean_line for keyword in info['keywords']):
                        found_company = company
                        # 해당 택배사의 패턴으로 다시 검색
                        matches = re.findall(info['pattern'], full_text)
                        for match in matches:
                            if company == '롯데택배' and (match.startswith('2') or match.startswith('6')):
                                return company, match
                            elif company == 'CJ대한통운' and match.startswith('51'):
                                return company, match
                            elif company not in ['롯데택배', 'CJ대한통운']:
                                tracking_number = match
                                return company, match

        return found_company, tracking_number

if __name__ == "__main__":
    root = tk.Tk()
    app = TrackingNumberExtractor(root)
    root.mainloop()
