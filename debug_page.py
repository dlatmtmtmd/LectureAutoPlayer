"""
페이지 구조 디버깅 스크립트
iframe과 video 요소를 찾아서 출력합니다.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def debug_page(url):
    """페이지의 iframe과 video 요소 찾기"""
    print("🚀 브라우저 초기화 중...")
    
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    try:
        print(f"\n📺 페이지 접속: {url}")
        driver.get(url)
        
        print("\n⏸️  브라우저에서 수동으로 로그인해주세요...")
        print("로그인 완료 후 Enter를 누르세요: ", end='')
        input()
        
        # 현재 URL 확인
        print(f"\n현재 URL: {driver.current_url}")
        
        # 페이지 로딩 대기
        time.sleep(3)
        
        # 모든 iframe 찾기
        print("\n" + "="*60)
        print("🔍 iframe 요소 찾기")
        print("="*60)
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        print(f"\n총 {len(iframes)}개의 iframe 발견\n")
        
        for i, iframe in enumerate(iframes):
            print(f"📌 iframe #{i+1}:")
            print(f"   id: {iframe.get_attribute('id')}")
            print(f"   name: {iframe.get_attribute('name')}")
            print(f"   src: {iframe.get_attribute('src')}")
            print(f"   class: {iframe.get_attribute('class')}")
            print()
        
        # 모든 video 요소 찾기 (메인 페이지)
        print("\n" + "="*60)
        print("🔍 video 요소 찾기 (메인 페이지)")
        print("="*60)
        videos = driver.find_elements(By.TAG_NAME, 'video')
        print(f"\n메인 페이지에서 {len(videos)}개의 video 발견\n")
        
        for i, video in enumerate(videos):
            print(f"📌 video #{i+1}:")
            print(f"   id: {video.get_attribute('id')}")
            print(f"   src: {video.get_attribute('src')}")
            print(f"   class: {video.get_attribute('class')}")
            print()
        
        # 각 iframe 내부 확인
        if iframes:
            print("\n" + "="*60)
            print("🔍 iframe 내부 확인")
            print("="*60)
            
            for i, iframe in enumerate(iframes):
                try:
                    print(f"\n📌 iframe #{i+1} 내부 확인 중...")
                    driver.switch_to.frame(iframe)
                    
                    # iframe 내부의 video 찾기
                    iframe_videos = driver.find_elements(By.TAG_NAME, 'video')
                    print(f"   ✅ {len(iframe_videos)}개의 video 발견")
                    
                    for j, video in enumerate(iframe_videos):
                        print(f"   video #{j+1}:")
                        print(f"      id: {video.get_attribute('id')}")
                        print(f"      src: {video.get_attribute('src')}")
                        print(f"      class: {video.get_attribute('class')}")
                    
                    # 메인 프레임으로 복귀
                    driver.switch_to.default_content()
                    
                except Exception as e:
                    print(f"   ❌ 오류: {e}")
                    driver.switch_to.default_content()
        
        # 페이지의 전체 HTML 일부 출력
        print("\n" + "="*60)
        print("📄 페이지 HTML 샘플 (처음 500자)")
        print("="*60)
        page_source = driver.page_source[:500]
        print(page_source)
        print("...")
        
        print("\n✅ 디버깅 완료!")
        print("\n브라우저를 닫으려면 Enter를 누르세요: ", end='')
        input()
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    url = input("디버깅할 페이지 URL: ").strip()
    if url:
        debug_page(url)
    else:
        print("❌ URL이 입력되지 않았습니다")
