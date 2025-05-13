from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
from datetime import datetime, timedelta
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import requests
import re

def setup_driver():
    try:
        options = Options()
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-blink-features=AutomationControlled')  # 자동화 감지 방지
        options.add_argument('--start-maximized')  # 브라우저 최대화
        options.add_argument('--disable-notifications')  # 알림 비활성화
        options.add_argument('--disable-popup-blocking')  # 팝업 차단 비활성화
        options.add_argument('--disable-save-password-bubble')  # 비밀번호 저장 팝업 비활성화
        options.add_argument('--disable-infobars')  # 정보 표시줄 비활성화
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])  # 로깅 비활성화 추가
        options.add_experimental_option('useAutomationExtension', False)  # 자동화 확장 비활성화
        options.add_experimental_option('prefs', {
            'credentials_enable_service': False,  # 비밀번호 저장 서비스 비활성화
            'profile.password_manager_enabled': False,  # 비밀번호 관리자 비활성화
            'profile.default_content_setting_values.notifications': 2  # 알림 차단
        })
        options.page_load_strategy = 'eager'
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(5)
        return driver
        
    except Exception as e:
        print(f"드라이버 설정 중 오류 발생: {str(e)}")
        raise

def handle_popups(driver):
    try:
        # 팝업창 처리
        main_window = driver.current_window_handle
        for handle in driver.window_handles:
            if handle != main_window:
                driver.switch_to.window(handle)
                driver.close()
        driver.switch_to.window(main_window)
        return True
    except Exception as e:
        print(f"팝업창 처리 중 오류: {str(e)}")
        return False

def login_to_ggsan(driver, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            print(f"로그인 시도 {attempt + 1}/{max_attempts}")
            driver.get("https://m.ggsan.com/member/login.php")
            time.sleep(3)  # 페이지 로딩 대기 시간 증가
            
            # 팝업창 처리
            handle_popups(driver)
            
            wait = WebDriverWait(driver, 10)  # 대기 시간 증가
            
            # ID 입력
            id_input = wait.until(EC.presence_of_element_located((By.ID, "loginId")))
            id_input.clear()
            time.sleep(1)  # 입력 간격 추가
            id_input.send_keys("bt0123")
            time.sleep(1)  # 입력 간격 추가
            
            # 비밀번호 입력
            pwd_input = wait.until(EC.presence_of_element_located((By.ID, "loginPwd")))
            pwd_input.clear()
            time.sleep(1)  # 입력 간격 추가
            pwd_input.send_keys("oo00ppll!!@@")
            time.sleep(2)  # 로그인 전 대기 시간 추가
            
            # 로그인 폼 제출
            form = wait.until(EC.presence_of_element_located((By.ID, "formLogin")))
            form.submit()
            
            time.sleep(3)  # 로그인 후 대기 시간 증가
            
            # 팝업창 다시 한번 처리
            handle_popups(driver)
            
            # 로그인 성공 확인
            if "로그아웃" in driver.page_source or "마이페이지" in driver.page_source:
                print("로그인 성공!")
                return True
            
            print(f"로그인 시도 {attempt + 1} 실패, 재시도 중...")
            time.sleep(3)  # 재시도 전 대기 시간 증가
            
        except Exception as e:
            print(f"로그인 시도 {attempt + 1} 중 오류 발생: {str(e)}")
            if attempt < max_attempts - 1:
                time.sleep(3)
                continue
            return False
    
    print("모든 로그인 시도 실패")
    return False

def extract_product_code(url):
    try:
        # URL에서 상품 코드 추출
        match = re.search(r'goodsNo=(\d+)', url)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"상품 코드 추출 중 오류: {str(e)}")
        return None

def download_image(url, save_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        return False
    except Exception as e:
        print(f"이미지 다운로드 중 오류: {str(e)}")
        return False

def is_product_soldout(product_element):
    try:
        soldout = product_element.find_element(By.CSS_SELECTOR, ".goods_prd_item .goods_prd_content .goods_prd_soldout img")
        return True
    except:
        return False

def is_expiry_valid(expiry_date_str):
    try:
        # 날짜 형식 변환 (예: "2025-11-15" -> datetime 객체)
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        # 현재 날짜
        current_date = datetime.now()
        # 1년 후 날짜
        one_year_later = current_date + timedelta(days=365)
        
        # 소비기한이 1년 이상 남았는지 확인
        return expiry_date >= one_year_later
    except:
        return False

def get_product_details(driver, url):
    try:
        driver.get(url)
        handle_popups(driver)
        wait = WebDriverWait(driver, 10)
        product_info = {}
        
        # 상품 코드 추출
        product_code = extract_product_code(url)
        if not product_code:
            print("상품 코드를 찾을 수 없습니다.")
            return None
            
        # 구매불가 상품 체크
        try:
            no_buy_btn = driver.find_element(By.CSS_SELECTOR, ".detail_prd_no_btn")
            if no_buy_btn and "구매불가" in no_buy_btn.text:
                print(f"구매불가 상품 스킵: {url}")
                return None
        except:
            pass  # 구매불가 버튼이 없으면 정상 상품
            
        # 품절 상품 체크
        try:
            soldout = driver.find_element(By.CSS_SELECTOR, ".goods_prd_item .goods_prd_content .goods_prd_soldout img")
            print(f"품절 상품 제외: {url}")
            return None
        except:
            pass  # 품절 상품이 아님
        
        # 이미지 저장 폴더 생성
        save_dir = f"product_images/{product_code}"
        os.makedirs(save_dir, exist_ok=True)
        
        # 상품명 수집
        try:
            name_elem = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, ".goods_view .detail_info h3")))
            product_info['상품명'] = name_elem.text.strip()
        except:
            print(f"상품명 추출 실패: {url}")
            product_info['상품명'] = "정보 없음"
            
        # 판매가 수집
        try:
            price_elem = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, ".goods_view .detail_info .detail_info_top .price_box .price")))
            price_text = price_elem.text.strip().replace(',', '')
            product_info['판매가'] = f"{price_text}원"
        except:
            print(f"가격 추출 실패: {url}")
            product_info['판매가'] = "정보 없음"
        
        # 소비/유통기한 수집
        try:
            expiry_elem = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, ".openblock_content dl dd")))
            expiry_info = expiry_elem.text.strip()
            if not expiry_info:
                expiry_info = "정보 없음"
            product_info['소비/유통기한'] = expiry_info
            
            # 소비기한이 1년 미만인 경우 None 반환
            if not is_expiry_valid(expiry_info):
                print(f"소비기한이 1년 미만인 상품 제외: {expiry_info}")
                return None
                
        except:
            print(f"유통기한 추출 실패: {url}")
            product_info['소비/유통기한'] = "정보 없음"
            
        # 썸네일 이미지 다운로드
        try:
            thumbnail = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, ".slider-wrap .slick-slide img")))
            thumbnail_url = thumbnail.get_attribute("src")
            if thumbnail_url:
                save_path = f"{save_dir}/1.jpg"
                if download_image(thumbnail_url, save_path):
                    print(f"썸네일 이미지 저장 완료: {save_path}")
                else:
                    print("썸네일 이미지 다운로드 실패")
        except Exception as e:
            print(f"썸네일 이미지 처리 중 오류: {str(e)}")
            
        # 상세 이미지 다운로드
        try:
            detail_images = driver.find_elements(By.CSS_SELECTOR, ".goods_view .detail_info_box .view_box0 img")
            for idx, img in enumerate(detail_images, 1):
                img_url = img.get_attribute("src")
                if img_url:
                    save_path = f"{save_dir}/a{idx}.jpg"
                    if download_image(img_url, save_path):
                        print(f"상세 이미지 저장 완료: {save_path}")
                    else:
                        print(f"상세 이미지 {idx} 다운로드 실패")
        except Exception as e:
            print(f"상세 이미지 처리 중 오류: {str(e)}")
        
        # 터미널에 출력
        print("\n=== 상품 정보 ===")
        print(f"상품코드: {product_code}")
        print(f"상품명: {product_info['상품명']}")
        print(f"판매가: {product_info['판매가']}")
        print(f"소비/유통기한: {product_info['소비/유통기한']}")
        print("================\n")
        
        return product_info
        
    except Exception as e:
        print(f"상품 정보 추출 중 오류 발생 ({url}): {str(e)}")
        return None

def expand_product_list(driver):
    try:
        wait = WebDriverWait(driver, 5)  # 대기 시간 감소
        click_count = 0
        max_clicks = 3  # 최대 클릭 횟수를 3회로 제한
        
        # 페이지를 스크롤하여 더보기 버튼이 보이도록 함
        try:
            # 페이지 끝까지 스크롤
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # 스크롤 후 잠시 대기
            
            # 다시 위로 조금 스크롤 (더보기 버튼이 보이도록)
            driver.execute_script("window.scrollBy(0, -200);")
            time.sleep(1)
        except Exception as e:
            print(f"스크롤 중 오류: {str(e)}")
        
        # 초기 상품 수 확인
        initial_products = len(driver.find_elements(By.CSS_SELECTOR, ".goods_prd_item, .goods_prd_item1, .goods_prd_item2"))
        print(f"초기 상품 수: {initial_products}개")
        
        # more 버튼이 없을 때까지 클릭
        while click_count < max_clicks:
            try:
                # 더보기 버튼 찾기 (여러 선택자 시도)
                selectors = [
                    ".goods_list .btn_more",
                    ".goods_list .btn_box a",
                    ".goods_list .btn_box button",
                    ".goods_list .btn_box",
                    ".btn_more",
                    ".btn_box"
                ]
                
                more_btn = None
                for selector in selectors:
                    try:
                        more_btn = wait.until(EC.presence_of_element_located((
                            By.CSS_SELECTOR, selector)))
                        if more_btn.is_displayed():
                            print(f"더보기 버튼을 찾았습니다: {selector}")
                            break
                    except:
                        continue
                
                if not more_btn or not more_btn.is_displayed():
                    print("더보기 버튼을 찾을 수 없습니다.")
                    break
                
                # 버튼이 클릭 가능한 상태가 될 때까지 대기
                wait.until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, selector)))
                
                # JavaScript로 클릭 실행
                driver.execute_script("arguments[0].click();", more_btn)
                
                click_count += 1
                print(f"더보기 버튼 클릭 ({click_count}/{max_clicks})")
                
                # 3초 대기 (로딩 시간 증가)
                time.sleep(3)
                
                # 새로운 상품이 로드되었는지 확인
                try:
                    # 현재 상품 수 확인
                    current_products = len(driver.find_elements(By.CSS_SELECTOR, ".goods_prd_item, .goods_prd_item1, .goods_prd_item2"))
                    print(f"현재 상품 수: {current_products}개")
                    
                    # 새로운 상품이 로드되었는지 확인 (최소 1개 이상 증가)
                    if current_products > initial_products:
                        print(f"새로운 상품 {current_products - initial_products}개가 로드되었습니다.")
                        initial_products = current_products
                    else:
                        print("새로운 상품이 로드되지 않았습니다.")
                        break
                        
                except Exception as e:
                    print(f"상품 로드 확인 중 오류: {str(e)}")
                    break
                    
            except Exception as e:
                print(f"더보기 버튼 클릭 중 오류: {str(e)}")
                break
                
        print(f"총 {click_count}번의 더보기 버튼 클릭 완료")
        
    except Exception as e:
        print(f"상품 목록 펼치기 중 오류: {str(e)}")

def get_category_products(driver, category_name, num_products):
    try:
        # 장건강 카테고리 페이지로 직접 이동
        category_url = "https://m.ggsan.com/goods/goods_list.php?cateCd=001"
        driver.get(category_url)
        time.sleep(2)  # 페이지 로딩 대기
        
        # 상품 목록 펼치기
        expand_product_list(driver)
        
        # 상품 목록 가져오기
        products = []
        wait = WebDriverWait(driver, 5)  # 대기 시간 감소
        
        try:
            # 상품 목록이 로드될 때까지 대기
            wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, ".goods_prd_item, .goods_prd_item1, .goods_prd_item2")))
            
            # 잠시 대기하여 모든 상품이 로드되도록 함
            time.sleep(1)
            
            product_elements = driver.find_elements(By.CSS_SELECTOR, 
                ".goods_prd_item, .goods_prd_item1, .goods_prd_item2")
            
            print(f"\n총 {len(product_elements)}개의 상품이 발견되었습니다.")
            
            # 모든 상품 URL 수집
            all_products = []
            for product in product_elements:
                try:
                    # 상품 링크 가져오기
                    link = product.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    all_products.append(link)
                except Exception as e:
                    continue
            
            return all_products[:num_products]
            
        except Exception as e:
            print(f"상품 목록 처리 중 오류 발생: {str(e)}")
            return []
            
    except Exception as e:
        print(f"카테고리 상품 수집 중 오류 발생: {str(e)}")
        return []

def show_input_modal(driver):
    try:
        # 페이지가 완전히 로드될 때까지 대기
        time.sleep(2)
        
        # 모달 창 HTML과 CSS 추가
        modal_script = """
        try {
            // 기존 모달이 있다면 제거
            var existingModal = document.querySelector('.input-modal');
            var existingOverlay = document.querySelector('.modal-overlay');
            if (existingModal) existingModal.remove();
            if (existingOverlay) existingOverlay.remove();
            
            var modal = document.createElement('div');
            modal.className = 'input-modal';
            modal.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.2);
                z-index: 9999;
                text-align: center;
                font-family: Arial, sans-serif;
                min-width: 300px;
            `;
            
            var overlay = document.createElement('div');
            overlay.className = 'modal-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 9998;
            `;
            
            var title = document.createElement('h2');
            title.textContent = '크롤링할 상품 수를 입력하세요';
            title.style.cssText = `
                color: #333;
                margin-bottom: 20px;
                font-size: 20px;
            `;
            
            var input = document.createElement('input');
            input.type = 'number';
            input.min = '1';
            input.max = '100';
            input.placeholder = '1-100 사이의 숫자';
            input.style.cssText = `
                width: 200px;
                padding: 10px;
                margin: 10px 0;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                text-align: center;
            `;
            
            var button = document.createElement('button');
            button.textContent = '확인';
            button.style.cssText = `
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 10px;
            `;
            
            var error = document.createElement('div');
            error.style.cssText = `
                color: red;
                margin-top: 10px;
                font-size: 14px;
                display: none;
            `;
            
            modal.appendChild(title);
            modal.appendChild(input);
            modal.appendChild(button);
            modal.appendChild(error);
            document.body.appendChild(overlay);
            document.body.appendChild(modal);
            
            input.focus();
            
            return new Promise((resolve) => {
                function validateAndSubmit() {
                    var value = parseInt(input.value);
                    if (isNaN(value) || value < 1 || value > 100) {
                        error.textContent = '1에서 100 사이의 숫자를 입력해주세요.';
                        error.style.display = 'block';
                        return;
                    }
                    modal.remove();
                    overlay.remove();
                    resolve(value);
                }
                
                button.onclick = validateAndSubmit;
                input.onkeypress = function(e) {
                    if (e.key === 'Enter') {
                        validateAndSubmit();
                    }
                };
            });
        } catch (error) {
            console.error('모달 창 생성 중 오류:', error);
            return null;
        }
        """
        
        # JavaScript 실행하여 모달 창 표시 (최대 3번 시도)
        for attempt in range(3):
            try:
                result = driver.execute_script(modal_script)
                if result is not None:
                    return result
                time.sleep(1)
            except Exception as e:
                print(f"모달 창 표시 시도 {attempt + 1}/3 실패: {str(e)}")
                if attempt < 2:  # 마지막 시도가 아니면 대기 후 재시도
                    time.sleep(1)
                    continue
                raise
        
        return None
        
    except Exception as e:
        print(f"모달 창 표시 중 오류: {str(e)}")
        return None

def main():
    try:
        print("데이터 수집 시작...")
        start_time = time.time()
        
        # 드라이버 설정 및 로그인
        driver = setup_driver()
        if not login_to_ggsan(driver):
            print("로그인 실패")
            driver.quit()
            return
            
        # 장건강 카테고리 페이지로 이동
        category_url = "https://m.ggsan.com/goods/goods_list.php?cateCd=001"
        driver.get(category_url)
        time.sleep(2)  # 페이지 로딩 대기
        
        try:
            # 장건강 카테고리 상품 URL 수집
            product_urls = get_category_products(driver, "장건강", 100)  # 최대 상품 수로 먼저 수집
            
            if not product_urls:
                print("상품 URL을 찾을 수 없습니다.")
                driver.quit()
                return
                
            # 웹페이지 중앙에 모달 창으로 입력 받기 (최대 3번 시도)
            num_products = None
            for attempt in range(3):
                try:
                    num_products = show_input_modal(driver)
                    if num_products is not None:
                        break
                    print(f"모달 창 표시 시도 {attempt + 1}/3 실패, 재시도 중...")
                    time.sleep(1)
                except Exception as e:
                    print(f"모달 창 표시 시도 {attempt + 1}/3 실패: {str(e)}")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    break
            
            if not num_products:
                print("상품 수 입력이 취소되었습니다.")
                driver.quit()
                return
                
            # 요청한 수만큼 상품 선택
            product_urls = product_urls[:num_products]
            print(f"\n수집할 상품 URL: {len(product_urls)}개")
            
            # 상품 정보 수집
            for url in product_urls:
                try:
                    get_product_details(driver, url)
                except KeyboardInterrupt:
                    print("\n상품 정보 수집이 중단되었습니다.")
                    break
                except Exception as e:
                    print(f"상품 정보 수집 중 오류 발생: {str(e)}")
                    continue
                    
        except KeyboardInterrupt:
            print("\n프로그램이 중단되었습니다.")
        except Exception as e:
            print(f"프로그램 실행 중 오류 발생: {str(e)}")
        finally:
            driver.quit()
            end_time = time.time()
            print(f"\n작업 완료! 소요 시간: {end_time - start_time:.2f}초")
            
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {str(e)}")
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    main()
