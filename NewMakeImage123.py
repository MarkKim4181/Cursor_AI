import os
import subprocess
import re
import cv2
import numpy as np
import pytesseract
from tkinter import Tk, filedialog, Button, Label, Canvas, PhotoImage, Frame, Scale, HORIZONTAL, colorchooser, StringVar, Entry, Scrollbar, Text
from PIL import Image, ImageTk, ImageDraw, ImageColor, ImageFilter

# 전역 변수 추가
output_dir = None
overlap_scale_value_1 = 90  #1.jpg용 겹침 값
overlap_scale_value = 90  # 2.jpg용 겹침 값
overlap_scale_value_3 = 85  # 3.jpg용 겹침 값
last_uploaded_file = None  # 마지막으로 업로드된 파일 경로 저장
pastel_color_1 = '#CCFFCC'  # 1.jpg용 기본 파스텔톤 색상

# 20가지 연한 파스텔톤 색상 리스트
PASTEL_COLORS = [
    ('민트', '#CCFFCC'),
    ('베이비블루', '#D6F5FF'),
    ('라벤더', '#E6E6FA'),
    ('연한 핑크', '#FFE6F2'),
    ('연노랑', '#FFFFCC'),
    ('연살구', '#FFE5CC'),
    ('연보라', '#E0CCFF'),
    ('연하늘', '#E0FFFF'),
    ('연두', '#E5FFCC'),
    ('연주황', '#FFF2CC'),
    ('연회색', '#F2F2F2'),
    ('연코랄', '#FFD6CC'),
    ('연청록', '#CCFFF5'),
    ('연살구핑크', '#FFD9B3'),
    ('연연두', '#F0FFF0'),
    ('연라임', '#F9FFCC'),
    ('연보라핑크', '#F8E6FF'),
    ('연카키', '#F5FFE6'),
    ('연베이지', '#FFF9E3'),
    ('연블루그레이', '#E3F0FF'),
]

def get_script_dir():
    return os.path.dirname(os.path.abspath(__file__))

def get_download_path():
    return os.path.join(os.path.expanduser('~'), 'Downloads', '썸네일_자동생성')

def select_output_directory():
    global output_dir
    selected_dir = filedialog.askdirectory()
    if selected_dir:
        output_dir = selected_dir
        os.makedirs(output_dir, exist_ok=True)
        label_output_dir.config(text=f'출력 경로: {output_dir}')
    else:
        output_dir = get_download_path()
        os.makedirs(output_dir, exist_ok=True)
        label_output_dir.config(text=f'출력 경로: {output_dir}')

def set_pastel_color_1(hex_color):
    global pastel_color_1
    pastel_color_1 = hex_color
    label_color_1.config(text=f'왼쪽 배경색: {pastel_color_1}', bg=pastel_color_1)
    if last_uploaded_file and output_dir:
        create_thumbnails(last_uploaded_file, output_dir)
        load_previews()

def add_shadow(image, offset=(10, 10), background_color=(255,255,255), shadow_color=(0,0,0,80), blur_radius=12):
    total_width = image.width + abs(offset[0]) + blur_radius*2
    total_height = image.height + abs(offset[1]) + blur_radius*2
    shadow_image = Image.new('RGBA', (total_width, total_height), background_color + (0,))
    shadow_layer = Image.new('RGBA', image.size, shadow_color)
    shadow_image.paste(shadow_layer, (blur_radius+max(offset[0],0), blur_radius+max(offset[1],0)), image)
    shadow_image = shadow_image.filter(ImageFilter.GaussianBlur(blur_radius))
    shadow_image.paste(image, (blur_radius, blur_radius), image)
    return shadow_image

def create_thumbnails(image_path, output_dir):
    global overlap_scale_value_1, overlap_scale_value, overlap_scale_value_3, pastel_color_1, text_2jpg_var
    os.makedirs(output_dir, exist_ok=True)

    # 이미지 전처리 및 OCR 수행
    base_image = Image.open(image_path)
    if base_image.mode != 'RGBA':
        base_image = base_image.convert('RGBA')
    
    # 이미지 전처리
    processed_image = preprocess_image(base_image)
    
    # OCR 수행
    ocr_text = improve_ocr_recognition(processed_image)
    
    # 송장번호 추출
    carrier, tracking_number = extract_tracking_number(ocr_text)
    
    # OCR 결과를 텍스트 위젯에 표시
    if hasattr(root, 'text_widget'):
        root.text_widget.delete(1.0, 'end')
        root.text_widget.insert('end', f'OCR 결과:\n{ocr_text}\n\n')
        if carrier and tracking_number:
            root.text_widget.insert('end', f'택배사: {carrier}\n송장번호: {tracking_number}')
    
    # 썸네일 생성 로직
    base_image.thumbnail((1000, 1000))

    # 1.jpg: 중앙 배치 (대각선 배경 적용, 대각선 반대 방향)
    img1 = Image.new('RGB', (1000, 1000), (255, 255, 255))
    pastel_rgb = ImageColor.getrgb(pastel_color_1)
    for y in range(1000):
        for x in range(1000):
            if x - y < 0:
                img1.putpixel((x, y), pastel_rgb)
    # 중앙 배치
    resized_image = base_image.copy()
    target_size = int(1000 * (overlap_scale_value_1 / 100))
    aspect_ratio = resized_image.width / resized_image.height
    if aspect_ratio > 1:
        new_width = target_size
        new_height = int(target_size / aspect_ratio)
    else:
        new_height = target_size
        new_width = int(target_size * aspect_ratio)
    resized_image = resized_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    # 선명하게
    resized_image = resized_image.filter(ImageFilter.UnsharpMask(radius=2, percent=180, threshold=3))
    # 그림자 추가 (오른쪽 하단, 아주 연하게)
    shadowed = add_shadow(resized_image)
    img1.paste(shadowed, ((1000 - shadowed.width) // 2, (1000 - shadowed.height) // 2), shadowed)
    img1.save(os.path.join(output_dir, '1.jpg'), 'JPEG', quality=95)

    # 2.jpg: 두 개 복제 배치 (이미지 크기에 따라 자동 조절)
    img2 = Image.new('RGB', (1000, 1000), (255, 255, 255))
    resized_image = base_image.copy()
    base_size = 400
    overlap_multiplier = (overlap_scale_value / 50)
    target_size = int(base_size * overlap_multiplier)
    aspect_ratio = resized_image.width / resized_image.height
    if aspect_ratio > 1:
        new_width = target_size
        new_height = int(target_size / aspect_ratio)
    else:
        new_height = target_size
        new_width = int(target_size * aspect_ratio)
    if base_image.width < 400 or base_image.height < 400:
        new_width = int(new_width * 1.2)
        new_height = int(new_height * 1.2)
    resized_image = resized_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    resized_image = resized_image.filter(ImageFilter.UnsharpMask(radius=2, percent=180, threshold=3))
    shadowed = add_shadow(resized_image)
    img2.paste(shadowed, (0, 0), shadowed)
    x2 = 1000 - shadowed.width
    y2 = 1000 - shadowed.height
    img2.paste(shadowed, (x2, y2), shadowed)

    # 텍스트 입력값이 있으면 그림자+이미지 모두 붙인 후 맨 마지막에 그리기!
    if text_2jpg_var.get().strip():
        from PIL import ImageFont
        try:
            font = ImageFont.truetype('GmarketSansTTFMedium.ttf', 60)
        except:
            font = ImageFont.truetype('arial.ttf', 60)
        text = text_2jpg_var.get().strip()
        
        # 텍스트 크기 계산
        draw_temp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        text_w, text_h = draw_temp.textsize(text, font=font)
        
        # 텍스트 이미지 생성
        text_img = Image.new('RGBA', (text_w + 20, text_h + 20), (0, 0, 0, 0))
        draw_text = ImageDraw.Draw(text_img)
        
        # 텍스트 그림자
        draw_text.text((12, 12), text, font=font, fill=(0, 0, 0, 128))
        # 텍스트 그리기
        draw_text.text((10, 10), text, font=font, fill=(255, 0, 0, 255))
        
        # 텍스트 이미지를 메인 이미지에 붙이기
        x = 20  # 왼쪽 여백
        y = 1000 - text_h - 20  # 하단 여백
        img2.paste(text_img, (x, y), text_img)

    img2.save(os.path.join(output_dir, '2.jpg'), 'JPEG', quality=95)

    # 3.jpg: 세 개 복제 배치
    img3 = Image.new('RGB', (1000, 1000), (255, 255, 255))
    resized_image = base_image.copy()
    base_size = 400
    overlap_multiplier = (overlap_scale_value_3 / 50)
    target_size = int(base_size * overlap_multiplier)
    aspect_ratio = resized_image.width / resized_image.height
    if aspect_ratio > 1:
        new_width = target_size
        new_height = int(target_size / aspect_ratio)
    else:
        new_height = target_size
        new_width = int(target_size * aspect_ratio)
    resized_image = resized_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    # 선명하게
    resized_image = resized_image.filter(ImageFilter.UnsharpMask(radius=2, percent=180, threshold=3))
    # 그림자 추가
    shadowed = add_shadow(resized_image)
    img3.paste(shadowed, (0, 0), shadowed)
    x2 = (1000 - shadowed.width) // 2
    y2 = (1000 - shadowed.height) // 2
    img3.paste(shadowed, (x2, y2), shadowed)
    x3 = 1000 - shadowed.width
    y3 = 1000 - shadowed.height
    img3.paste(shadowed, (x3, y3), shadowed)
    img3.save(os.path.join(output_dir, '3.jpg'), 'JPEG', quality=95)

    return output_dir

def on_overlap_change_1(value):
    global overlap_scale_value_1, last_uploaded_file
    overlap_scale_value_1 = int(value)
    if last_uploaded_file and output_dir:
        create_thumbnails(last_uploaded_file, output_dir)
        load_previews()

def on_overlap_change(value):
    global overlap_scale_value, last_uploaded_file
    overlap_scale_value = int(value)
    if last_uploaded_file and output_dir:
        create_thumbnails(last_uploaded_file, output_dir)
        load_previews()

def on_overlap_change_3(value):
    global overlap_scale_value_3, last_uploaded_file
    overlap_scale_value_3 = int(value)
    if last_uploaded_file and output_dir:
        create_thumbnails(last_uploaded_file, output_dir)
        load_previews()

def load_previews():
    if not output_dir:
        return
        
    preview_images = ['1.jpg', '2.jpg', '3.jpg']
    for idx, img_name in enumerate(preview_images):
        preview_image_path = os.path.join(output_dir, img_name)
        if os.path.exists(preview_image_path):
            preview_image = Image.open(preview_image_path)
            canvas_width, canvas_height = 300, 300
            preview_image_ratio = preview_image.width / preview_image.height
            canvas_ratio = canvas_width / canvas_height

            if preview_image_ratio > canvas_ratio:
                new_width = canvas_width
                new_height = int(canvas_width / preview_image_ratio)
            else:
                new_height = canvas_height
                new_width = int(canvas_height * preview_image_ratio)

            preview_image = preview_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            preview_photo = ImageTk.PhotoImage(preview_image)
            
            # Canvas 초기화 후 새 이미지 표시
            preview_canvases[idx].delete('all')
            x_offset = (canvas_width - new_width) // 2
            y_offset = (canvas_height - new_height) // 2
            preview_canvases[idx].create_image(x_offset, y_offset, anchor='nw', image=preview_photo)
            preview_canvases[idx].image = preview_photo

            # 스크롤 영역 조정
            preview_canvases[idx].config(scrollregion=(0, 0, preview_image.width, preview_image.height))

# 파일 선택 및 처리 함수
def upload_image():
    global output_dir, last_uploaded_file, overlap_scale_value_1, overlap_scale_value, overlap_scale_value_3
    if not output_dir:
        output_dir = get_download_path()
        os.makedirs(output_dir, exist_ok=True)
        label_output_dir.config(text=f'출력 경로: {output_dir}')

    file_path = filedialog.askopenfilename(filetypes=[('Image Files', '*.png;*.jpg')])
    if file_path:
        last_uploaded_file = file_path
        label_status.config(text='이미지가 선택되었습니다. 저장하기 버튼을 클릭하세요.')
        # 모든 슬라이더 값을 각 변수값으로 초기화
        overlap_scale_value_1 = 90
        overlap_scale_value = 90
        overlap_scale_value_3 = 85
        for i, frame in enumerate(preview_frames):
            for widget in frame.winfo_children():
                if isinstance(widget, Scale):
                    if i == 0:
                        widget.set(overlap_scale_value_1)
                    elif i == 1:
                        widget.set(overlap_scale_value)
                    elif i == 2:
                        widget.set(overlap_scale_value_3)
        create_thumbnails(last_uploaded_file, output_dir)
        load_previews()

def save_thumbnails():
    global output_dir, last_uploaded_file
    if not last_uploaded_file:
        label_status.config(text='먼저 이미지를 업로드해주세요.')
        return
        
    if not output_dir:
        output_dir = get_download_path()
        os.makedirs(output_dir, exist_ok=True)
        label_output_dir.config(text=f'출력 경로: {output_dir}')
    
    output_dir = create_thumbnails(last_uploaded_file, output_dir)
    label_status.config(text=f'썸네일이 생성되었습니다! 경로: {output_dir}')
    load_previews()

# GUI 설정
root = Tk()
root.title('썸네일 생성 툴')
root.geometry('1200x800')

text_2jpg_var = StringVar()
text_2jpg_var.set('')

label_title = Label(root, text='배경제거된 이미지를 업로드하세요', font=('Arial', 14))
label_title.pack(pady=10)

# 미리보기 프레임들 생성
preview_frames = []
preview_canvases = []

preview_frame = Frame(root)
preview_frame.pack(pady=10)

for i in range(3):
    frame = Frame(preview_frame)
    frame.pack(side='left', padx=20)

    # 스크롤바 추가
    canvas_frame = Frame(frame)
    canvas_frame.pack()
    vbar = Scrollbar(canvas_frame, orient='vertical')
    hbar = Scrollbar(canvas_frame, orient='horizontal')
    canvas = Canvas(canvas_frame, width=300, height=300, bg='white',
                   highlightthickness=1, highlightbackground='black',
                   yscrollcommand=vbar.set, xscrollcommand=hbar.set,
                   scrollregion=(0, 0, 1000, 1000))
    vbar.config(command=canvas.yview)
    hbar.config(command=canvas.xview)
    vbar.pack(side='right', fill='y')
    hbar.pack(side='bottom', fill='x')
    canvas.pack(side='left', expand=True, fill='both')

    # 각 미리보기에 겹침 조절 슬라이더 추가
    if i == 0:
        scale = Scale(frame, from_=10, to=100, orient=HORIZONTAL,
                     command=on_overlap_change_1, length=200, font=('맑은 고딕', 10))
        scale.set(overlap_scale_value_1)
        scale.pack()
    elif i == 1:
        scale = Scale(frame, from_=10, to=100, orient=HORIZONTAL,
                     command=on_overlap_change, length=200, font=('맑은 고딕', 10))
        scale.set(overlap_scale_value)
        scale.pack()
    elif i == 2:
        scale = Scale(frame, from_=10, to=100, orient=HORIZONTAL,
                     command=on_overlap_change_3, length=200, font=('맑은 고딕', 10))
        scale.set(overlap_scale_value_3)
        scale.pack()
    
    preview_frames.append(frame)
    preview_canvases.append(canvas)

# 색상 선택 버튼 및 라벨(1.jpg용)
color_frame_1 = Frame(root)
color_frame_1.place(x=10, rely=1.0, anchor='sw')
label_color_1 = Label(color_frame_1, text=f'왼쪽 배경색: {pastel_color_1}', bg=pastel_color_1, width=20, font=('맑은 고딕', 10))
label_color_1.grid(row=0, column=0, columnspan=5, pady=(0,2), sticky='w')

# 15가지 파스텔톤 색상 버튼 5개씩 3줄로 생성 (한글 텍스트 없이 색상만)
for idx, (name, hex_color) in enumerate(PASTEL_COLORS):
    row = idx // 5 + 1
    col = idx % 5
    btn = Button(color_frame_1, text='', bg=hex_color, width=6, height=2, command=lambda c=hex_color: set_pastel_color_1(c))
    btn.grid(row=row, column=col, padx=2, pady=2, sticky='w')

# 출력 경로 선택 버튼 및 라벨
button_select_dir = Button(root, text='출력 경로 선택', command=select_output_directory, font=('맑은 고딕', 10))
button_select_dir.pack(pady=10)

label_output_dir = Label(root, text='출력 경로가 선택되지 않았습니다.', font=('Arial', 10))
label_output_dir.pack(pady=10)

# 이미지 업로드 버튼 추가
button_upload = Button(root, text='이미지 업로드', command=upload_image, font=('맑은 고딕', 10))
button_upload.pack(pady=10)

# 저장하기 버튼 추가
button_save = Button(root, text='저장하기', command=save_thumbnails, font=('맑은 고딕', 10))
button_save.pack(pady=10)

label_status = Label(root, text='', font=('Arial', 10))
label_status.pack(pady=10)

# 텍스트 입력 프레임 추가
text_frame = Frame(root)
text_frame.pack(pady=5)
Label(text_frame, text='2.jpg 왼쪽하단 텍스트:', font=('맑은 고딕', 10)).pack(side='left')
entry_2jpg = Entry(text_frame, textvariable=text_2jpg_var, font=('맑은 고딕', 10), width=10)
entry_2jpg.pack(side='left', padx=5)

# 1. 함수 정의를 먼저!
def apply_text_2jpg():
    if not last_uploaded_file:
        label_status.config(text='먼저 이미지를 업로드해주세요.')
        return
    if not output_dir:
        output_dir = get_download_path()
        os.makedirs(output_dir, exist_ok=True)
        label_output_dir.config(text=f'출력 경로: {output_dir}')
    
    create_thumbnails(last_uploaded_file, output_dir)
    load_previews()
    label_status.config(text='텍스트가 적용되었습니다.')

# 2. 그 다음에 버튼 생성!
button_apply = Button(text_frame, text='적용', command=apply_text_2jpg, font=('맑은 고딕', 10))
button_apply.pack(side='left', padx=5)

# 초기 출력 경로 설정 (자동 팝업 제거)
#select_output_directory()

def preprocess_image(image):
    # 이미지 크기 3배 확대
    width, height = image.size
    image = image.resize((width*3, height*3), Image.Resampling.LANCZOS)
    
    # 가우시안 블러로 노이즈 제거
    image = image.filter(ImageFilter.GaussianBlur(radius=1))
    
    # 이미지 선명도 향상
    image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=250, threshold=3))
    
    return image

def improve_ocr_recognition(image):
    # 이미지를 OpenCV 형식으로 변환
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # 적응형 이진화 적용
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # 모폴로지 연산으로 노이즈 제거
    kernel = np.ones((2,2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # OCR 설정
    custom_config = r'--oem 3 --psm 4'
    text = pytesseract.image_to_string(binary, lang='kor+eng', config=custom_config)
    
    return text

def extract_tracking_number(text):
    # 택배사 키워드 확장
    carriers = {
        'CJ대한통운': r'\b\d{10,12}\b',
        '우체국택배': r'\b\d{13}\b',
        '한진택배': r'\b\d{12}\b',
        '롯데택배': r'\b\d{12}\b',
        '로젠택배': r'\b\d{11}\b'
    }
    
    # 텍스트를 줄 단위로 분석
    lines = text.split('\n')
    for i, line in enumerate(lines):
        # 택배사 키워드 검색
        for carrier, pattern in carriers.items():
            if carrier in line:
                # 현재 줄과 주변 줄에서 송장번호 검색
                search_range = lines[max(0, i-2):min(len(lines), i+3)]
                for search_line in search_range:
                    # 공백 제거 후 매칭
                    clean_line = search_line.replace(' ', '')
                    matches = re.findall(pattern, clean_line)
                    if matches:
                        # 연도 형식 제외
                        for match in matches:
                            if not re.match(r'20\d{2}', match):
                                return carrier, match
    
    return None, None

# 메인 프레임
main_frame = Frame(root)
main_frame.pack(fill='both', expand=True, padx=10, pady=5)

# OCR 결과 표시 영역
result_frame = Frame(main_frame)
result_frame.pack(fill='both', expand=True, padx=5, pady=5)

result_label = Label(result_frame, text='OCR 결과', font=('Arial', 12, 'bold'))
result_label.pack(pady=5)

# 스크롤바가 있는 텍스트 영역
root.text_widget = Text(result_frame, height=10, wrap='word')
scrollbar = Scrollbar(result_frame, command=root.text_widget.yview)
root.text_widget.configure(yscrollcommand=scrollbar.set)

root.text_widget.pack(side='left', fill='both', expand=True)
scrollbar.pack(side='right', fill='y')

# 기존 UI 요소들
control_frame = Frame(main_frame)
control_frame.pack(fill='x', padx=5, pady=5)

root.mainloop()