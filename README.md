# 썸네일 생성기

이미지를 자동으로 썸네일로 변환하는 GUI 프로그램입니다.

## 주요 기능

- 이미지 업로드 및 썸네일 생성
- 3가지 다른 레이아웃 지원 (1개, 2개, 3개 이미지 배치)
- 파스텔톤 배경색 선택
- 텍스트 추가 기능
- 이미지 크기 조절
- 그림자 효과

## 사용 방법

1. `썸네일생성기.exe` 실행
2. '이미지 업로드' 버튼으로 이미지 선택
3. 원하는 설정 조정 (크기, 색상, 텍스트 등)
4. '저장하기' 버튼으로 썸네일 생성

## 시스템 요구사항

- Windows 10 이상
- 별도의 Python 설치 불필요

## 빌드 방법

```bash
pip install -r requirements.txt
pyinstaller NewMakeImage123.spec
```

## 라이선스

MIT License 

# 택배 송장번호 추출 프로그램

카카오톡이나 다른 앱에서 복사한 송장번호 이미지에서 택배사와 송장번호를 자동으로 추출하는 프로그램입니다.

## 설치 방법

1. **Python 패키지 설치**
```bash
pip install -r requirements.txt
```

2. **Tesseract OCR 설치**
- [Tesseract OCR 다운로드](https://github.com/UB-Mannheim/tesseract/wiki)에서 최신 버전 다운로드
  - Windows 64비트: `tesseract-ocr-w64-setup-v5.x.x.exe`
  - Windows 32비트: `tesseract-ocr-w32-setup-v5.x.x.exe`
- 설치 시 "Additional language data"에서 "Korean" 선택
- 기본 설치 경로: `C:\Program Files\Tesseract-OCR`

3. **환경 변수 설정**
- 시스템 환경 변수 편집 > 환경 변수 > 시스템 변수 > Path
- 새로 만들기 > `C:\Program Files\Tesseract-OCR` 추가
- 모든 창에서 "확인" 클릭

## 사용 방법

1. 카카오톡/GPT에서 송장번호가 있는 이미지를 복사
2. 프로그램에서 "이미지 붙여넣기" 버튼 클릭 또는 Ctrl+V
3. 자동으로 택배사와 송장번호가 인식됨
4. "복사" 버튼으로 송장번호 복사 가능

## 지원하는 택배사
- CJ대한통운
- 롯데택배
- 우체국택배
- 한진택배
- 로젠택배

## 문제 해결

### Tesseract 설치 확인
1. 명령 프롬프트(cmd)에서 다음 명령어 실행:
```bash
tesseract --version
```
2. 버전 정보가 표시되지 않는 경우:
   - Tesseract가 정상적으로 설치되었는지 확인
   - 환경 변수가 올바르게 설정되었는지 확인
   - PC 재시작 후 다시 시도 