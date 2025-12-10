"""
학교 강의 자동 재생 프로그램

사용법:
    python lecture_player.py

기능:
    1. 학교 로그인 페이지 접속 및 로그인
    2. 강의 페이지 URL 입력
    3. iframe 내 비디오 자동 재생 및 스킵
    4. 다음 비디오로 자동 이동
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time


class LecturePlayer:
    """강의 자동 재생 클래스"""
    
    def __init__(self):
        """Selenium WebDriver 초기화"""
        print("🚀 브라우저 초기화 중...")
        
        # Chrome 옵션 설정
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  # 백그라운드 실행 (필요시 주석 해제)
        
        # WebDriver 초기화 (Chrome 사용)
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.wait = WebDriverWait(self.driver, 10)
        
        print("✅ 브라우저 준비 완료")
    
    def login(self, login_url: str, username: str, password: str):
        """
        학교 로그인 페이지에서 로그인
        
        Args:
            login_url: 로그인 페이지 URL
            username: 학번 또는 ID
            password: 비밀번호
        """
        print(f"\n🔐 로그인 중: {login_url}")
        
        try:
            self.driver.get(login_url)
            
            # 사용자가 수동으로 로그인할 수 있도록 대기
            print("\n⏸️  브라우저에서 수동으로 로그인해주세요...")
            print("로그인 완료 후 Enter를 누르세요: ", end='')
            input()
            
            print("✅ 로그인 완료")
            
        except Exception as e:
            print(f"❌ 로그인 실패: {e}")
            raise
    
    def play_video(self, page_url: str):
        """
        강의 페이지에서 비디오 재생 및 자동 스킵
        
        Args:
            page_url: 강의 비디오 페이지 URL
        """
        print(f"\n📺 비디오 페이지 접속: {page_url}")
        
        try:
            self.driver.get(page_url)
            time.sleep(3)  # 페이지 로딩 대기
            
            print("▶️ 비디오 재생 시작 중...")
            
            # video 요소 찾아서 클릭
            video = self.driver.find_element(By.CSS_SELECTOR, 'video.jw-video')
            video.click()
            print("✅ video 클릭 - 재생 시작")
            
            # 재생이 시작될 때까지 잠시 대기
            time.sleep(2)
            
            # JavaScript로 비디오 스킵 (끝 0.5초 전으로 이동)
            print("⏩ 비디오 스킵 중...")
            self.driver.execute_script("""
                var vid = document.querySelector('video');
                if (vid) {
                    vid.currentTime = vid.duration - 0.5;
                }
            """)
            print("✅ 비디오 스킵 완료")
            
            print("⏱️  비디오 종료 대기 중...")
            
            # 비디오가 끝날 때까지 반복 체크
            max_wait_time = 7200  # 최대 2시간 (초 단위)
            check_interval = 2  # 2초마다 체크
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                # 비디오가 끝났는지 체크
                is_ended = self.driver.execute_script("""
                    var vid = document.querySelector('video');
                    if (vid) {
                        return vid.ended;
                    }
                    return false;
                """)
                
                if is_ended:
                    print("✅ 비디오 재생 완료!")
                    break
                
                time.sleep(check_interval)
                elapsed_time += check_interval
            
            return True
            
        except Exception as e:
            print(f"❌ 비디오 재생 실패: {e}")
            return False
    
    def find_next_button(self):
        """다음 강의 버튼 찾기"""
        try:
            # 일반적인 '다음' 버튼 텍스트들
            next_keywords = ['다음', 'next', 'Next', '다음 강의', '다음강의']
            
            for keyword in next_keywords:
                try:
                    # 버튼 또는 링크 찾기
                    next_btn = self.driver.find_element(
                        By.XPATH, 
                        f"//button[contains(text(), '{keyword}')] | //a[contains(text(), '{keyword}')]"
                    )
                    return next_btn
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"  ⚠️ 다음 버튼 찾기 실패: {e}")
            return None
    
    def extract_viewer_links(self, index_url: str):
        """
        index.php 페이지에서 viewer.php 링크들을 추출
        
        Args:
            index_url: 강의 목록 페이지 URL 
            
        Returns:
            list: viewer.php URL 리스트
        """
        print(f"\n🔍 강의 링크 추출 중: {index_url}")
        
        try:
            self.driver.get(index_url)
            time.sleep(2)  # 페이지 로딩 대기
            
            # 모든 링크 찾기
            all_links = self.driver.find_elements(By.TAG_NAME, 'a')
            
            # vod/view.php가 포함된 링크 찾기 및 viewer.php로 변환
            viewer_links = []
            for link in all_links:
                href = link.get_attribute('href')
                if href and 'vod/view.php' in href:
                    # view.php를 viewer.php로 변경
                    viewer_url = href.replace('vod/view.php', 'vod/viewer.php')
                    viewer_links.append(viewer_url)
            
            # 중복 제거
            viewer_links = list(set(viewer_links))
            
            print(f"✅ 총 {len(viewer_links)}개의 강의 링크 발견")
            
            # 링크 미리보기 출력
            if viewer_links:
                print("\n발견된 강의 링크:")
                for i, link in enumerate(viewer_links[:5], 1):
                    print(f"  {i}. {link}")
                if len(viewer_links) > 5:
                    print(f"  ... 외 {len(viewer_links) - 5}개")
            
            return viewer_links
            
        except Exception as e:
            print(f"❌ 링크 추출 실패: {e}")
            return []
    
    def auto_play_sequence(self, index_url: str, max_videos: int = 100):
        """
        자동으로 연속 재생
        
        Args:
            index_url: 강의 목록 페이지 URL (index.php)
            max_videos: 최대 재생할 비디오 수
        """
        print(f"\n🎬 자동 연속 재생 시작 (최대 {max_videos}개)")
        print("="*50)
        
        # 1. index.php에서 모든 viewer.php 링크 추출
        viewer_links = self.extract_viewer_links(index_url)
        
        if not viewer_links:
            print("❌ 강의 링크를 찾을 수 없습니다")
            return
        
        # max_videos만큼만 처리
        links_to_process = viewer_links[:max_videos]
        
        # 2. 각 링크를 순회하며 비디오 재생
        for i, video_url in enumerate(links_to_process, 1):
            print(f"\n📚 [{i}/{len(links_to_process)}] 강의 재생 중...")
            print(f"URL: {video_url}")
            
            # 비디오 재생 및 스킵
            success = self.play_video(video_url)
            
            if not success:
                print("⚠️ 비디오 재생 실패, 다음으로 넘어갑니다")
            
            # 다음 비디오로 이동하기 전 잠시 대기
            time.sleep(1)
        
        print("\n" + "="*50)
        print(f"✅ 총 {len(links_to_process)}개 강의 완료!")
    
    def close(self):
        """브라우저 종료"""
        print("\n👋 브라우저 종료 중...")
        self.driver.quit()
        print("✅ 종료 완료")


def main():
    """메인 함수"""
    print("="*50)
    print("🎓 학교 강의 자동 재생 프로그램")
    print("="*50)
    
    player = None
    
    try:
        player = LecturePlayer()
        
        # 로그인 (URL 하드코딩)
        login_url = "https://tls.kku.ac.kr/"
        player.login(login_url, "", "")
        
        # 재생 모드 선택
        print("\n📺 재생 모드 선택:")
        print("  1. 단일 강의 재생 (viewer.php)")
        print("  2. 자동 연속 재생 (강의페이지의 모든 강의)")
        mode = input("선택 (1 또는 2): ").strip()
        
        if mode == '1':
            # 단일 재생
            print("\n📝 단일 강의 정보 입력")
            video_url = input("강의 비디오 페이지 URL: ").strip()
            
            if not video_url:
                print("❌ URL이 입력되지 않았습니다")
                return
            
            player.play_video(video_url)
            
        elif mode == '2':
            # 연속 재생
            print("\n📝 강의 목록 페이지 입력")
            index_url = input("강의 목록 페이지 URL: ").strip()
            
            if not index_url:
                print("❌ URL이 입력되지 않았습니다")
                return
            
            max_count = input("최대 재생 개수 (기본: 100): ").strip()
            max_count = int(max_count) if max_count.isdigit() else 100
            player.auto_play_sequence(index_url, max_count)
        else:
            print("❌ 잘못된 선택입니다")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자가 중단했습니다")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    finally:
        if player:
            player.close()


if __name__ == "__main__":
    main()
