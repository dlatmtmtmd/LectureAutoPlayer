"""
강의 자동 재생 프로그램 - GUI 버전
PyQt6를 사용한 Bright Flat GUI 인터페이스
"""

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QProgressBar, QFrame, QSizePolicy, QGroupBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# 스타일시트 (Formal & Professional 디자인)
STYLESHEET = """
QMainWindow {
    background-color: #F5F7FA;
}
QWidget {
    background-color: #F5F7FA;
    color: #2C3E50;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #D5DCE4;
    border-radius: 4px;
    margin-top: 18px;
    font-weight: 600;
    color: #34495E;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #BDC3C7;
    border-radius: 3px;
    padding: 10px 12px;
    color: #2C3E50;
    selection-background-color: #3498DB;
    selection-color: white;
}
QLineEdit:focus {
    border: 1px solid #3498DB;
}
QPushButton {
    border: none;
    border-radius: 4px;
    padding: 11px 20px;
    font-weight: 600;
    font-size: 13px;
    color: white;
}
/* 시작 버튼 - Professional Blue */
QPushButton#start_btn {
    background-color: #3498DB;
}
QPushButton#start_btn:hover {
    background-color: #2980B9;
}
QPushButton#start_btn:pressed {
    background-color: #2472A4;
}
QPushButton#start_btn:disabled {
    background-color: #BDC3C7;
    color: #ECF0F1;
}

/* 중지 버튼 - Muted Red */
QPushButton#stop_btn {
    background-color: #95A5A6;
}
QPushButton#stop_btn:hover {
    background-color: #E74C3C;
}
QPushButton#stop_btn:pressed {
    background-color: #C0392B;
}
QPushButton#stop_btn:disabled {
    background-color: #D5DBDB;
    color: #F2F4F4;
}

QProgressBar {
    border: 1px solid #D5DCE4;
    background-color: #ECF0F1;
    border-radius: 3px;
    height: 22px;
    text-align: center;
    color: #2C3E50;
    font-weight: 500;
}
QProgressBar::chunk {
    background-color: #3498DB;
    border-radius: 2px;
}

QTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #D5DCE4;
    border-radius: 4px;
    color: #2C3E50;
    padding: 10px;
    font-family: 'Consolas', 'D2Coding', monospace;
    font-size: 12px;
    line-height: 1.4;
}

/* 타이틀 라벨 */
QLabel#title_label {
    font-size: 18px;
    font-weight: 700;
    color: #2C3E50;
    letter-spacing: -0.5px;
}

QLabel#status_label {
    font-weight: 600;
    color: #7F8C8D;
    font-size: 12px;
}

/* 구분선 */
QFrame#line {
    color: #D5DCE4;
}
"""

class LecturePlayerThread(QThread):
    """별도 스레드에서 강의 재생을 실행"""
    
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(str)
    
    def __init__(self, target_url):
        super().__init__()
        self.target_url = target_url
        self.is_running = True
        self.driver = None
        self.wait = None
    
    def log(self, message):
        self.log_signal.emit(message)
    
    def run(self):
        try:
            self.log("[INFO] 브라우저 초기화 중...")
            options = webdriver.ChromeOptions()
            # options.add_argument("--start-maximized")
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            self.wait = WebDriverWait(self.driver, 10)
            
            self.log("[OK] 브라우저 준비 완료\n")
            
            # 1. 로그인
            login_url = "https://tls.kku.ac.kr/"
            self.log(f"[INFO] 로그인 페이지 접속: {login_url}")
            self.driver.get(login_url)
            
            self.log("[WAIT] 브라우저에서 수동으로 로그인해주세요.")
            self.log("       로그인 완료 시 자동 인식 또는 30초 후 진행합니다.\n")
            
            # 로그인 대기 (URL 변경 감지 또는 시간 대기)
            elapsed = 0
            while elapsed < 30 and "login.php" in self.driver.current_url:
                time.sleep(1)
                elapsed += 1
                if not self.is_running:
                    return
            
            self.log("[OK] 로그인/대기 완료\n")
            
            # 2. 강의 목록 구성
            links_to_process = []
            
            # 단일 강의 URL인지 목록 URL인지 판단
            # viewer.php 또는 vod/view.php가 포함되어야 단일 강의
            # course/view.php는 강의 목록임
            if "vod/viewer.php" in self.target_url or "vod/view.php" in self.target_url:
                # view.php라면 viewer.php로 변환
                target = self.target_url
                if "vod/view.php" in target:
                    target = target.replace("vod/view.php", "vod/viewer.php")
                links_to_process = [target]
                self.log(f"[MODE] 단일 강의 - 1개 영상")
            else:
                self.log(f"[MODE] 강의 목록 - URL 분석 중...")
                viewer_links = self.extract_viewer_links(self.target_url)
                if not viewer_links:
                    self.log("[ERROR] 강의 링크를 찾을 수 없습니다.")
                    self.finished_signal.emit("실패: 링크 없음")
                    return
                links_to_process = viewer_links
                self.log(f"[OK] 총 {len(links_to_process)}개의 강의 발견\n")
            
            # 3. 재생 시작
            total = len(links_to_process)
            for i, video_url in enumerate(links_to_process, 1):
                if not self.is_running:
                    self.log("\n[STOP] 사용자에 의해 중단됨")
                    break
                
                self.log(f"\n[{i}/{total}] 강의 재생 중...")
                # self.log(f"URL: {video_url}")
                
                self.progress_signal.emit(i, total)
                
                success = self.play_video(video_url)
                
                if not success:
                    self.log("[WARN] 재생 실패 - 다음 항목으로 진행")
                
                if i < total:
                    time.sleep(1)
            
            self.log("\n" + "="*40)
            self.log(f"[COMPLETE] 모든 작업 완료 ({len(links_to_process)}개 처리)")
            self.finished_signal.emit("모든 강의 완료")
            
        except Exception as e:
            self.log(f"\n[FATAL] 오류 발생: {e}")
            import traceback
            self.log(traceback.format_exc())
            self.finished_signal.emit("오류 발생")
        finally:
            if self.driver:
                self.log("\n[INFO] 브라우저 종료 중...")
                self.driver.quit()
    
    def extract_viewer_links(self, index_url):
        try:
            self.driver.get(index_url)
            time.sleep(2)
            all_links = self.driver.find_elements(By.TAG_NAME, 'a')
            viewer_links = []
            for link in all_links:
                href = link.get_attribute('href')
                if href and 'vod/view.php' in href:
                    viewer_url = href.replace('vod/view.php', 'vod/viewer.php')
                    viewer_links.append(viewer_url)
                elif href and 'vod/viewer.php' in href:
                    viewer_links.append(href)
            return list(set(viewer_links))
        except Exception as e:
            self.log(f"[ERROR] 링크 추출 실패: {e}")
            return []
    
    def play_video(self, page_url):
        try:
            self.driver.get(page_url)
            time.sleep(3)
            
            self.log("[PLAY] 재생 시도...")
            
            # video 요소 찾아서 클릭
            try:
                # 1. JW Player 방식 시도
                video = self.driver.find_element(By.CSS_SELECTOR, 'video.jw-video')
                video.click()
                self.log("[OK] Video 클릭 성공")
            except:
                try:
                    # 2. 일반 Video 태그 시도
                    video = self.driver.find_element(By.TAG_NAME, 'video')
                    video.click()
                    self.log("[OK] Video 클릭 성공")
                except:
                    # 3. JS 강제 실행
                    self.log("[WARN] Click 실패 - JS 강제 재생 시도")
                    self.driver.execute_script("var v=document.querySelector('video'); if(v){v.muted=true;v.play();}")

            time.sleep(3)
            
            # 스킵 로직
            self.log("[SKIP] 종료 직전으로 이동...")
            self.driver.execute_script("""
                var vid = document.querySelector('video');
                if (vid) {
                    vid.currentTime = vid.duration - 0.5;
                }
            """)
            
            self.log("[WAIT] 종료 확인 대기 중...")
            
            # 완료 체크 (폴링)
            max_wait = 3600
            elapsed = 0
            while elapsed < max_wait and self.is_running:
                is_ended = self.driver.execute_script("""
                    var vid = document.querySelector('video');
                    return vid ? vid.ended : false;
                """)
                
                if is_ended:
                    self.log("[OK] 재생 완료")
                    return True
                
                time.sleep(1)
                elapsed += 1
                
            return False
            
        except Exception as e:
            self.log(f"[ERROR] {e}")
            return False
    
    def stop(self):
        self.is_running = False


class LecturePlayerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.player_thread = None
        self.init_ui()
        self.init_style()
        
    def init_style(self):
        self.setStyleSheet(STYLESHEET)
    
    def init_ui(self):
        self.setWindowTitle("Lecture Auto Player")
        self.resize(550, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        central_widget.setLayout(layout)
        
        # 1. 헤더 (타이틀)
        header_layout = QHBoxLayout()
        # 아이콘이 있다면 좋겠지만 텍스트로 대체
        title = QLabel("Lecture Auto Player")
        title.setObjectName("title_label")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setObjectName("line")
        layout.addWidget(line)
        
        # 2. 컨트롤 패널 (흰색 박스 느낌)
        control_group = QGroupBox("설정 및 실행")
        control_layout = QVBoxLayout()
        control_layout.setSpacing(15)
        control_layout.setContentsMargins(15, 20, 15, 15)
        
        # URL 입력
        url_label = QLabel("강의 URL 입력 (목록 또는 단일 강의)")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("예: https://tls.kku.ac.kr/course/view.php?id=...")
        
        control_layout.addWidget(url_label)
        control_layout.addWidget(self.url_input)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.start_button = QPushButton("자동 재생 시작")
        self.start_button.setObjectName("start_btn")
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_button.clicked.connect(self.start_automation)
        self.start_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.stop_button = QPushButton("중지")
        self.stop_button.setObjectName("stop_btn")
        self.stop_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_button.clicked.connect(self.stop_automation)
        self.stop_button.setEnabled(False)
        self.stop_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # 동일한 정책 적용
        
        # 1:1 비율로 추가
        btn_layout.addWidget(self.start_button)
        btn_layout.addWidget(self.stop_button)
        control_layout.addLayout(btn_layout)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 3. 진행 상황 패널
        status_layout = QHBoxLayout()
        self.status_label = QLabel("준비됨")
        self.status_label.setObjectName("status_label")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 4. 로그 영역 (하단)
        log_label = QLabel("실행 로그")
        log_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
    def start_automation(self):
        url = self.url_input.text().strip()
        if not url:
            self.status_label.setText("URL을 입력해주세요")
            self.status_label.setStyleSheet("color: #EF5350;")
            return
            
        self.status_label.setStyleSheet("color: #66BB6A;")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.url_input.setEnabled(False)
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.status_label.setText("시작 준비 중...")
        
        self.player_thread = LecturePlayerThread(url)
        self.player_thread.log_signal.connect(self.append_log)
        self.player_thread.progress_signal.connect(self.update_progress)
        self.player_thread.finished_signal.connect(self.on_finished)
        self.player_thread.start()
    
    def stop_automation(self):
        if self.player_thread:
            self.status_label.setText("중지 요청됨...")
            self.status_label.setStyleSheet("color: #EF5350;")
            self.player_thread.stop()
            self.stop_button.setEnabled(False)
    
    def append_log(self, message):
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_progress(self, current, total):
        progress = int((current / total) * 100)
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"진행 중: {current} / {total} ({progress}%)")
    
    def on_finished(self, message):
        self.status_label.setText(message)
        if "완료" in message:
            self.status_label.setStyleSheet("color: #66BB6A;") # 성공 색상
        else:
            self.status_label.setStyleSheet("color: #EF5350;") # 실패 색상
            
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.url_input.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = LecturePlayerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
