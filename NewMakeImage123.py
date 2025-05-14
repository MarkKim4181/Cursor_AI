import os
from tkinter import Tk, filedialog, Button, Label, Canvas, PhotoImage, Frame, Scale, HORIZONTAL
from PIL import Image, ImageTk

# 전역 변수 추가
output_dir = None
overlap_scale_value = 50  # 기본 겹침 값
last_uploaded_file = None  # 마지막으로 업로드된 파일 경로 저장

def select_output_directory():
    global output_dir
    output_dir = filedialog.askdirectory()
    if output_dir:
        label_output_dir.config(text=f'출력 경로: {output_dir}')
    else:
        label_output_dir.config(text='출력 경로가 선택되지 않았습니다.')

def get_desktop_path():
    return os.path.join(os.path.expanduser('~'), 'Desktop', '썸네일_자동생성')

def create_thumbnails(image_path, output_dir):
    global overlap_scale_value
    os.makedirs(output_dir, exist_ok=True)

    base_image = Image.open(image_path)
    if base_image.mode == 'RGBA':
        base_image = base_image.convert('RGB')  # JPEG 저장을 위해 RGBA를 RGB로 변환
    base_image.thumbnail((1000, 1000))  # 비율 유지하며 최대 크기 조정

    # 1.jpg: 중앙 배치 (캔버스의 80% 크기로 설정하되 원본 비율 유지)
    img1 = Image.new('RGB', (1000, 1000), (255, 255, 255))  # 흰색 배경 생성
    resized_image = base_image.copy()
    
    target_size = int(1000 * 0.8)  # 800x800이 최대 크기
    aspect_ratio = resized_image.width / resized_image.height
    
    if aspect_ratio > 1:  # 가로가 더 긴 경우
        new_width = target_size
        new_height = int(target_size / aspect_ratio)
    else:  # 세로가 더 긴 경우
        new_height = target_size
        new_width = int(target_size * aspect_ratio)
    
    resized_image = resized_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    img1.paste(resized_image, ((1000 - new_width) // 2, (1000 - new_height) // 2))
    img1.save(os.path.join(output_dir, '1.jpg'))

    # 2.jpg: 두 개 복제 배치 (이미지 크기에 따라 자동 조절)
    img2 = Image.new('RGB', (1000, 1000), (255, 255, 255))
    resized_image = base_image.copy()
    
    base_size = 500  # 기본 크기
    overlap_multiplier = (overlap_scale_value / 50)  # 50이 기본값일 때 1.0
    target_size = int(base_size * overlap_multiplier)
    
    aspect_ratio = resized_image.width / resized_image.height
    
    if aspect_ratio > 1:
        new_width = target_size
        new_height = int(target_size / aspect_ratio)
    else:
        new_height = target_size
        new_width = int(target_size * aspect_ratio)
    
    if base_image.width < 500 or base_image.height < 500:
        new_width = int(new_width * 1.3)
        new_height = int(new_height * 1.3)
    
    resized_image = resized_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    img2.paste(resized_image, (0, 0))
    
    margin = int(50 * (2 - overlap_multiplier))  # 겹침이 커질수록 마진이 작아짐
    x2 = 1000 - resized_image.width - margin
    y2 = 1000 - resized_image.height - margin
    img2.paste(resized_image, (x2, y2))
    
    img2.save(os.path.join(output_dir, '2.jpg'))

    # 3.jpg: 세 개 복제 배치
    # 두 번째 이미지는 오른쪽 하단에 배치 (살짝 더 떨어뜨림)
    x2 = 1000 - resized_image.width - 50  # 오른쪽에서 50픽셀 더 떨어뜨림
    y2 = 1000 - resized_image.height - 50  # 하단에서 50픽셀 더 떨어뜨림
    img2.paste(resized_image, (x2, y2))
    
    img2.save(os.path.join(output_dir, '2.jpg'))

    # 3.jpg: 세 개 복제 배치 (세 번째 이미지는 오른쪽 하단에 딱 붙이고, 가운데 이미지는 중앙에 정렬)
    img3 = Image.new('RGB', (1000, 1000), (255, 255, 255))
    resized_image = base_image.copy()
    resized_image.thumbnail((600, 600))  # 비율 유지하며 크기 확대
    img3.paste(resized_image, (0, 0))  # 첫 번째 이미지 위치 (왼쪽 상단)
    img3.paste(resized_image, ((1000 - resized_image.width) // 2, (1000 - resized_image.height) // 2))  # 두 번째 이미지 위치 (정확히 중앙)
    img3.paste(resized_image, (1000 - resized_image.width, 1000 - resized_image.height))  # 세 번째 이미지 위치 (오른쪽 하단)
    img3.save(os.path.join(output_dir, '3.jpg'))

    return output_dir

def on_overlap_change(value):
    global overlap_scale_value, last_uploaded_file
    overlap_scale_value = int(value)
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

# 파일 선택 및 처리 함수
def upload_image():
    global output_dir, last_uploaded_file
    if not output_dir:
        label_status.config(text='출력 경로를 먼저 선택하세요.')
        return

    file_path = filedialog.askopenfilename(filetypes=[('Image Files', '*.png;*.jpg')])
    if file_path:
        last_uploaded_file = file_path
        output_dir = create_thumbnails(file_path, output_dir)
        label_status.config(text=f'썸네일이 생성되었습니다! 경로: {output_dir}')
        load_previews()

# 다운로드 버튼 추가
def download_thumbnails():
    global output_dir
    if not output_dir:
        label_status.config(text='출력 경로를 먼저 선택하세요.')
        return

    file_path = filedialog.askopenfilename(filetypes=[('Image Files', '*.png;*.jpg')])
    if file_path:
        create_thumbnails(file_path, output_dir)
        label_status.config(text=f'썸네일이 생성되었습니다! 경로: {output_dir}')

# GUI 설정
root = Tk()
root.title('썸네일 생성 툴')
root.geometry('1200x800')  # 창 크기 증가

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
    
    # 캔버스 생성
    canvas = Canvas(frame, width=300, height=300, bg='white', 
                   highlightthickness=1, highlightbackground='black')
    canvas.pack(pady=5)
    
    # 2번째 이미지(인덱스 1)에만 겹침 조절 슬라이더 추가
    if i == 1:
        label = Label(frame, text='겹침 정도 조절')
        label.pack(pady=5)
        
        scale = Scale(frame, from_=10, to=100, orient=HORIZONTAL,
                     command=on_overlap_change, length=200)
        scale.set(50)  # 기본값 설정
        scale.pack()
    
    preview_frames.append(frame)
    preview_canvases.append(canvas)

# 출력 경로 선택 버튼 및 라벨
button_select_dir = Button(root, text='출력 경로 선택', command=select_output_directory)
button_select_dir.pack(pady=10)

label_output_dir = Label(root, text='출력 경로가 선택되지 않았습니다.', font=('Arial', 10))
label_output_dir.pack(pady=10)

# 이미지 업로드 버튼 추가
button_upload = Button(root, text='이미지 업로드', command=upload_image)
button_upload.pack(pady=10)

# 다운로드 버튼 추가
button_download = Button(root, text='다운로드', command=download_thumbnails)
button_download.pack(pady=10)

label_status = Label(root, text='', font=('Arial', 10))
label_status.pack(pady=10)

root.mainloop()