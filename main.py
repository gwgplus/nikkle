import sys
import json
import os
import time
import socket
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox, QFileDialog, QDialog, QLabel, QProgressBar
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, QThread, pyqtSignal, Qt, QTimer, QCoreApplication

from PyQt5.QtGui import QIcon
from database_manager import DatabaseManager
from config_manager import ConfigManager
from account import AccountManagerWindow
from export import ExportWindow
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import base64
import io
from yolo_ocr import YOLOOCR

### 解決 英業達 電腦 開不了網頁問題
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
os.environ["QT_XCB_GL_INTEGRATION"] = "none"


def _env_truthy(v: str) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "on")

def _selected_from_env() -> str:
    flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    xcb = os.environ.get("QT_XCB_GL_INTEGRATION", "")
    if "swiftshader" in flags or os.environ.get("QT_OPENGL") == "software" or os.environ.get("LIBGL_ALWAYS_SOFTWARE") == "1":
        return "sw"
    if "egl" in flags or xcb == "xcb_egl":
        return "egl"
    if "desktop" in flags or xcb == "glx":
        return "glx"
    return "env"  # unknown/mixed, but keep hands off

def _select_gl_backend():
    """
    Priority:
      1) If user already provided key envs (e.g., in the long shell command),
         DO NOT override them — just ensure base vars exist.
      2) Else honor SMARTLOCKER_GL = egl|glx|sw.
      3) Else default to software.
    """
    # Always ensure these safe bases unless the user set them explicitly
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
    os.environ.setdefault("XDG_RUNTIME_DIR", "/tmp")

    # If the user already set any critical GL envs, don't touch them
    if any(os.environ.get(k) for k in (
        "QTWEBENGINE_CHROMIUM_FLAGS",
        "QT_XCB_GL_INTEGRATION",
        "QT_OPENGL",
        "LIBGL_ALWAYS_SOFTWARE",
    )):
        return _selected_from_env()

    # Optional legacy switch: SMARTLOCKER_FORCE_SWGL=1 means "force software"
    if _env_truthy(os.environ.get("SMARTLOCKER_FORCE_SWGL", "")):
        os.environ.setdefault("QT_XCB_GL_INTEGRATION", "none")
        os.environ.setdefault("QT_OPENGL", "software")
        os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
        os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--use-gl=swiftshader --disable-gpu --single-process")
        return "sw"

    # New switch: SMARTLOCKER_GL = egl|glx|sw
    mode = os.environ.get("SMARTLOCKER_GL", "").strip().lower()
    if mode == "egl":
        os.environ.setdefault("QT_XCB_GL_INTEGRATION", "xcb_egl")
        os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--use-gl=egl --ignore-gpu-blocklist")
        return "egl"
    if mode == "glx":
        os.environ.setdefault("QT_XCB_GL_INTEGRATION", "glx")
        os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--use-gl=desktop --ignore-gpu-blocklist")
        return "glx"

    # Default: software
    os.environ.setdefault("QT_XCB_GL_INTEGRATION", "none")
    os.environ.setdefault("QT_OPENGL", "software")
    os.environ.setdefault("LIBGL_ALWAYS_SOFTWARE", "1")
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--use-gl=swiftshader --disable-gpu --single-process")
    return "sw"
# 如果不是 Windows 系統,設定額外的環境變數
if os.name != 'nt':
    # # 設定 XDG 相關環境變數
    # os.environ.setdefault("XDG_SESSION_TYPE", "x11") 
    # os.environ.setdefault("XDG_CURRENT_DESKTOP", "GNOME")
    # os.environ.setdefault("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    # os.environ.setdefault("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    # os.environ.setdefault("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    
    # # 設定 Qt 相關環境變數
    # os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
    # os.environ.setdefault("QT_QPA_PLATFORMTHEME", "gtk3")
    # os.environ.setdefault("QT_STYLE_OVERRIDE", "gtk3")

    SMARTLOCKER_GL_SELECTED = _select_gl_backend()
    # -----------------------------------------------------------------------------



    # If software path was selected (either explicitly or inferred from env), hint Qt to use software GL.
    if SMARTLOCKER_GL_SELECTED == "sw":
        QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)

    # Share contexts for WebEngine stability
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

################################################################################

class CognexResult:
    """Cognex 結果枚舉"""
    ERROR = 0
    DISCONNECT = 1
    SUCCESS = 2
    FAIL = 3
    TIMEOUT = 4
    NOTRIGGER = 5
    WAIT = 6
    TIMEOUT_USER = 7
    TIMEOUT_PASS = 8
    TIMEOUT_SEND_OCR_STRING = 9
    TIMEOUT_GV = 10


class OCRResult:
    """OCR 結果枚舉"""
    SUCCEED = 0
    CONNECT_ERROR = 1
    OCR_ERROR = 2
    WAIT_PIC_TIMEOUT = 3


class WorkStatus:
    """工作狀態枚舉"""
    NONE = 0
    NORMAL = 1
    DRAWING = 2
    ZOOM_AND_ROTATE = 3
    START_SCALE = 4


class ExteriorCheckResult:
    """外觀檢查結果枚舉"""
    NONE = 0
    OK = 1
    NG = 2


class ErrAction:
    """錯誤動作枚舉"""
    NONE = 0
    ALLOW = 1 #允收
    BACK = 2 #退回


class ErrActionReason:
    """錯誤動作原因枚舉"""
    NONE = 0
    CANNOT_OCR = 1 #無法辯識
    OCR_CHECK_ERROR = 2 #辨識錯誤
    FOLD = 3 #摺痕


class ExteriorNGReason:
    """外觀 NG 原因枚舉"""
    NONE = 0
    OXIDATION = 1 #氧化
    LEAK = 2 #漏氣
    FOREIGN_MATTER = 3 #異物
    HOLE_ABNORMAL = 4 #孔洞異常


class OCRCheckInfo:
    """OCR 檢查資訊"""
    def __init__(self):
        self.is_correct = False
        self.err_action = ErrAction.NONE
        self.err_action_reason = ErrActionReason.NONE
        self.exterior = ExteriorCheckResult.NONE
        self.exterior_ng_reason = ExteriorNGReason.NONE
        self.class1 = False
        self.class2 = False
        self.source_code = ""
        self.source_image_path = ""

class MockDatabaseManager:
    """模擬資料庫管理器，用於測試或資料庫不可用時"""
    
    def get_account_by_id(self, account_id):
        """模擬取得帳號"""
        return {
            'Account': account_id,
            'Name': '管理員',
            'Password': 'admin',
            'IsAdmin': 1
        }
    
    def create_ocr_log(self, log_data):
        """模擬儲存 OCR 記錄"""
        print(f"模擬儲存記錄: {log_data}")
        return True
    
    def close(self):
        """關閉連接"""
        pass


class TcpClient:
    """TCP 客戶端"""
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.is_connected = False
        self.response = ""
        
    def connect(self, timeout=3):
        """連接到伺服器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            return True
        except Exception as e:
            print(f"TCP 連接失敗: {e}")
            self.is_connected = False
            return False
    
    def send(self, data):
        """發送資料"""
        if self.is_connected:
            try:
                self.socket.send(data.encode('ascii'))
                return True
            except Exception as e:
                print(f"發送資料失敗: {e}")
                return False
        return False
    
    def set_timeout(self, timeout):
        """設定超時時間"""
        if self.socket:
            self.socket.settimeout(timeout)
    
    def receive(self, timeout=5):
        """接收資料"""
        if self.is_connected:
            try:
                self.socket.settimeout(timeout)
                data = self.socket.recv(1024)
                self.response = data.decode('ascii')
                return self.response
            except Exception as e:
                print(f"接收資料失敗: {e}")
                return ""
        return ""
    
    def close(self):
        """關閉連接"""
        if self.socket:
            self.socket.close()
        self.is_connected = False
class PingHost:
    """Ping 主機"""
    def __init__(self, host):
        self.host = host
    def ping(self)->bool:
        """Ping 主機"""
        try:
            # Windows 使用 -n 參數, 其他系統使用 -c 參數
            param = '-n' if sys.platform.lower()=='win32' else '-c'
            # 執行 ping 指令並檢查回傳值
            response = os.system(f"ping {param} 1 {self.host}")
            return response == 0
        except Exception as e:
            print(f"Ping 失敗: {e}")
            return False

class InitDialog(QDialog):
    """初始化對話框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系統初始化")
        self.setFixedSize(400, 200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 設置樣式
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 14px;
                color: #333;
                padding: 10px;
            }
            QProgressBar {
                border: 2px solid #ccc;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
        # 創建佈局
        layout = QVBoxLayout()
        
        # 標題
        title_label = QLabel("系統正在初始化...")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 狀態標籤
        self.status_label = QLabel("等待初始化 TROCR...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 詳細資訊標籤
        self.detail_label = QLabel("")
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(self.detail_label)
        
        self.setLayout(layout)
        
        # 計時器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.progress_value = 0
        self.timer.start(100)  # 每100ms更新一次
        
    def update_progress(self):
        """更新進度條"""
        if self.progress_value < 90:
            self.progress_value += 2
            self.progress_bar.setValue(self.progress_value)
        else:
            self.progress_bar.setValue(90)
            
    def set_status(self, status: str, detail: str = ""):
        """設置狀態"""
        self.status_label.setText(status)
        self.detail_label.setText(detail)
        QApplication.processEvents()
        
    def set_progress(self, value: int):
        """設置進度"""
        self.progress_bar.setValue(value)
        QApplication.processEvents()
        
    def complete(self):
        """完成初始化"""
        self.progress_bar.setValue(100)
        self.status_label.setText("初始化完成！")
        self.detail_label.setText("系統已準備就緒")
        QApplication.processEvents()
        # 使用 QTimer 而不是 time.sleep 來避免阻塞
        QTimer.singleShot(1000, self.accept)  # 1秒後關閉對話框

class MainBridge(QObject):
    """主程式的橋接類別，處理 Python 和 JavaScript 之間的通信"""
    
    # 信號定義
    update_ui = pyqtSignal(str, str)  # 更新 UI 信號
    show_alert = pyqtSignal(str)      # 顯示警告信號
    show_result = pyqtSignal(str, bool)  # 顯示結果信號
    
    def __init__(self, config_manager: ConfigManager, view=None, main_window=None):
        super().__init__()
        self.config_manager = config_manager
        self.view = view
        self.main_window = main_window
        print(f"[{datetime.now().strftime('%H:%M:%S')}] MainBridge 初始化，main_window: {self.main_window}")
        self.tcp_client = None
        self.work_status = WorkStatus.NONE
        self.ocr_check_info = OCRCheckInfo()
        self.test_counter = 0
        self.ng_counter = 0
        self.today = datetime.today()
        self.account = ""
        self.selected_operator=""
        self.user_name = ""
        self.source_image_path = ""
        self.target_image_path = ""
        self.server_ip = "127.0.0.1"
        self.server_port = 8601
        self.server_port_cmd = 8604
        self.ocr_result = ""
        self.current_image = None
        self.is_halcon_ok = False
        self.start_time = datetime.now()
        self.account_window = None  # 帳號管理視窗
        self.export_window = None   # 匯出視窗
        self.is_full_screen = True
        
        # 載入設定
        self.load_settings()
        
        # 初始化資料庫
        self.init_database()
        
        # 顯示初始化視窗
        self.show_init_dialog()
        
    def show_init_dialog(self):
        """顯示初始化對話框"""
        import datetime
        
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 開始創建初始化對話框")
        # 創建初始化對話框
        init_dialog = InitDialog()
        
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 顯示初始化對話框")
        # 顯示對話框
        init_dialog.show()
        init_dialog.raise_()  # 將對話框提到最前面
        init_dialog.activateWindow()  # 激活對話框
        QApplication.processEvents()
        
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 設置對話框狀態")
        init_dialog.set_status("等待初始化 TROCR...", "正在載入 AI 模型...")
        QApplication.processEvents()
        
        # 使用定時器延遲一瞬間確保對話框完全顯示
        def delayed_init():
            try:
                # 初始化 TROCR
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 開始初始化 TROCR...")
                self.yolo_ocr = YOLOOCR()
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] TROCR 初始化完成")
                
                # 更新狀態為網路檢查
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 開始網路檢查")
                init_dialog.set_status("等待網路就緒...", f"正在檢查 {self.server_ip} 連線...")
                init_dialog.set_progress(50)
                QApplication.processEvents()
                
                # 檢查網路連線
                ping_host = PingHost(self.server_ip)
                retry_count = 0
                max_retries = 30  # 最多重試30次（30秒）
                
                while retry_count < max_retries:
                    if ping_host.ping():
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 網路連線成功: {self.server_ip}")
                        break
                    else:
                        retry_count += 1
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 網路連線失敗，第 {retry_count} 次重試...")
                        init_dialog.set_status("等待網路就緒...", f"連線失敗，第 {retry_count} 次重試... ({self.server_ip})")
                        QApplication.processEvents()
                        time.sleep(1)
                
                if retry_count >= max_retries:
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 網路連線超時: {self.server_ip}")
                    init_dialog.set_status("網路連線超時", f"無法連接到 {self.server_ip}，請檢查網路設定")
                    QApplication.processEvents()
                    time.sleep(3)  # 顯示錯誤訊息3秒
                
                # 完成初始化
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 初始化完成，準備關閉對話框")
                init_dialog.complete()
                
                # 連接對話框關閉信號到顯示主視窗
                def show_main_window():
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 準備顯示主視窗...")
                    if self.main_window:
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 以全螢幕模式顯示主視窗")
                        self.main_window.showFullScreen()  # 全螢幕顯示
                        self.main_window.raise_()  # 將視窗提到最前面
                        self.main_window.activateWindow()  # 激活視窗
                    else:
                        print("main_window 為 None")
                
                # 使用 QTimer 確保對話框完全關閉後再顯示主視窗
                QTimer.singleShot(1500, show_main_window)
                
            except Exception as e:
                import traceback
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 初始化失敗: {e}")
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 錯誤詳情: {traceback.format_exc()}")
                init_dialog.set_status("初始化失敗", str(e))
                QApplication.processEvents()
                
                # 即使初始化失敗也顯示主視窗
                def show_main_window_on_error():
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 初始化失敗，但仍顯示主視窗...")
                    if self.main_window:
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 顯示主視窗")
                        self.main_window.show()
                        self.main_window.raise_()
                        self.main_window.activateWindow()
                    else:
                        print("main_window 為 None")
                
                QTimer.singleShot(3500, show_main_window_on_error)
        
        # 延遲一點點時間確保對話框完全顯示
        QTimer.singleShot(100, delayed_init)
    
    def load_settings(self):
        """載入設定"""
        try:
            config = self.config_manager.Config
            # 使用新的設定結構
            self.source_image_path = config.Settings.Paths.OCR_Image_Save_Path
            self.target_image_path = config.Settings.Paths.DB_Image_Save_Path
            self.server_ip = config.Settings.Cognex.IP
            self.server_port = config.Settings.Cognex.Port
            self.server_port_cmd = config.Settings.Cognex.Port_Cmd
            
            # 確保目錄存在
            self.ensure_directories()
        except Exception as e:
            print(f"載入設定失敗: {e}")
            # 使用預設值
            self.source_image_path = 'E:\\OCR_Images\\Source'
            self.target_image_path = 'E:\\OCR_Images\\Database'
            self.server_ip = '127.0.0.1'
            self.server_port = 502
            self.server_port_cmd = 503
            self.ensure_directories()
    
    def ensure_directories(self):
        """確保必要目錄存在"""
        directories = [
            self.source_image_path,
            self.target_image_path,
            os.path.join(self.target_image_path, "OK"),
            os.path.join(self.target_image_path, "NG"),
            os.path.join(self.target_image_path, "Err"),
            os.path.join(self.target_image_path, "螢幕擷取")
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
    
    def normalize_path_for_web(self, file_path: str) -> str:
        """將路徑轉換為 Web 友好的格式"""
        if not file_path:
            return ""
        
        # 將反斜線轉換為正斜線
        normalized = file_path.replace('\\', '/')
        
        # 如果是絕對路徑，使用 file:// 協議
        if os.path.isabs(normalized):
            # 在 Windows 上，路徑可能是 E:/path 格式
            if ':' in normalized and len(normalized) > 2:
                # Windows 絕對路徑，使用 file:/// 協議
                normalized = f"file:///{normalized}"
            else:
                # Linux/Unix 絕對路徑，使用 file:// 協議
                normalized = f"file://{normalized}"
        
        return normalized
    def normalize_path_for_web2(self, file_path: str) -> str:
        """將路徑轉換為 Web 友好的格式"""
        if not file_path:
            return ""
        
        # 將反斜線轉換為正斜線
        normalized = file_path.replace('\\', '/')
        
        # 如果是絕對路徑，計算相對於 html 目錄的路徑
        if os.path.isabs(normalized):
            # 取得目前目錄下的 html 目錄路徑
            current_dir = os.path.dirname(os.path.abspath(__file__))
            html_dir = os.path.join(current_dir, 'html')
            
            try:
                # 計算相對路徑
                relative_path = os.path.relpath(normalized, html_dir)
                normalized = relative_path.replace('\\', '/')
            except ValueError:
                # 如果路徑不在 html 目錄下，保持原樣
                pass
                
        return normalized
    def image_to_base64(self, image_path: str) -> str:
        """將圖片檔案轉換為 base64 字串"""
        try:
            if not image_path or not os.path.exists(image_path):
                print(f"圖片檔案不存在: {image_path}")
                return None
            
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_string = base64.b64encode(image_data).decode('utf-8')
                
                # 根據檔案副檔名決定 MIME 類型
                ext = os.path.splitext(image_path)[1].lower()
                if ext in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                elif ext == '.png':
                    mime_type = 'image/png'
                elif ext == '.bmp':
                    mime_type = 'image/bmp'
                elif ext == '.gif':
                    mime_type = 'image/gif'
                else:
                    mime_type = 'image/jpeg'  # 預設
                
                return f"data:{mime_type};base64,{base64_string}"
        except Exception as e:
            print(f"轉換圖片為 base64 失敗: {e}")
            return None
    
    def init_database(self):
        """初始化資料庫"""
        try:
            mysql_config = self.config_manager.Config.MySql
            connection_string = f"mysql+pymysql://{mysql_config.User}:{mysql_config.Password}@{mysql_config.Host}:{mysql_config.Port}/{mysql_config.Database}?charset={mysql_config.Charset}"
            self.db_manager = DatabaseManager(connection_string)
        except Exception as e:
            print(f"資料庫初始化失敗: {e}")
            self.db_manager = None
            # 建立一個模擬的資料庫管理器，避免程式崩潰
            self.db_manager = MockDatabaseManager()
    @pyqtSlot(str, result=str)
    def toggle_full_screen(self, data: str) -> str:
        """切換全螢幕模式"""
        print(f"[toggle_full_screen] 被調用，data: {data}")
        print(f"[toggle_full_screen] main_window: {self.main_window}")
        print(f"[toggle_full_screen] is_full_screen: {self.is_full_screen}")
        
        try:
            if self.main_window:
                if self.is_full_screen:
                    # 從全螢幕切換到最大化視窗
                    print("[toggle_full_screen] 執行：全螢幕 → 最大化視窗")
                    self.main_window.showNormal()  # 先恢復正常
                    self.main_window.showMaximized()  # 再最大化
                    self.is_full_screen = False
                    result = json.dumps({'success': True, 'mode': 'maximized'}, ensure_ascii=False)
                    print(f"[toggle_full_screen] 返回結果: {result}")
                    return result
                else:
                    # 從最大化切換到全螢幕
                    print("[toggle_full_screen] 執行：最大化視窗 → 全螢幕")
                    self.main_window.showFullScreen()
                    self.is_full_screen = True
                    result = json.dumps({'success': True, 'mode': 'fullscreen'}, ensure_ascii=False)
                    print(f"[toggle_full_screen] 返回結果: {result}")
                    return result
            else:
                print("[toggle_full_screen] 錯誤：主視窗未初始化")
                return json.dumps({'success': False, 'error': '主視窗未初始化'}, ensure_ascii=False)
        except Exception as e:
            print(f"[toggle_full_screen] 異常: {e}")
            import traceback
            traceback.print_exc()
            return json.dumps({'success': False, 'error': str(e)}, ensure_ascii=False)
            
    @pyqtSlot(str, result=str)
    def update_processor(self, processor_data_json: str) -> str:
        """取得操作者(帳號)列表"""
        processor_data = json.loads(processor_data_json)
        self.selected_operator = processor_data.get('selected_operator', '')
        return json.dumps({
            'success': True,
            'data': self.selected_operator
        }, ensure_ascii=False)
        
    @pyqtSlot(result=str)
    def test_api(self) -> str:
        """測試 API 連接"""
        try:
            result = {
                'success': True,
                'message': 'API 連接正常',
                'timestamp': str(datetime.now())
            }
            print("API 測試成功")
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            print(f"API 測試失敗: {e}")
            return json.dumps({'success': False, 'error': str(e)}, ensure_ascii=False)
    
    @pyqtSlot(str)
    def login(self, login_data_json: str):
        """登入驗證"""
        try:
            print(f"[CRASH_DEBUG] 開始執行 login 方法，時間: {datetime.now()}")
            import traceback
            print(f"[CRASH_DEBUG] 當前調用堆疊:\n{traceback.format_stack()}")
            if not self.db_manager:
                result = {
                    'success': False,
                    'error': '資料庫連接不可用'
                }
                print(f"登入失敗: {result}")
                # 觸發認證失敗事件
                
                self.view.run_javascript('access_login_result(' + json.dumps(result, ensure_ascii=False) + ')')
                #return json.dumps(result, ensure_ascii=False)
            
            login_data = json.loads(login_data_json)
            username = login_data.get('username', '').strip()
            password = login_data.get('password', '').strip()
            
            print(f"嘗試登入: username={username}, password={'*' * len(password)}")
            
            if not username :
                result = {
                    'success': False,
                    'error': '請輸入帳號和密碼'
                }
                print(f"登入失敗: {result}")
                # 觸發認證失敗事件
                
                self.view.run_javascript('access_login_result(' + json.dumps(result, ensure_ascii=False) + ')')
                #return json.dumps(result, ensure_ascii=False)
            
            # 查詢資料庫驗證帳號密碼
            account = self.db_manager.get_account_by_id(username)
            
            if not account:
                result = {
                    'success': False,
                    'error': '帳號不存在'
                }
                print(f"登入失敗: {result}")
                # 觸發認證失敗事件
                
                self.view.run_javascript('access_login_result(' + json.dumps(result, ensure_ascii=False) + ')')
                #return json.dumps(result, ensure_ascii=False)
            
            # 驗證密碼
            if account.get('NeedPassword') == 1 and account.get('Password') != password:
                result = {
                    'success': False,
                    'error': '密碼錯誤'
                }
                print(f"登入失敗: {result}")
                # 觸發認證失敗事件
                
                self.view.run_javascript('access_login_result(' + json.dumps(result, ensure_ascii=False) + ')')
                #return json.dumps(result, ensure_ascii=False)
            
            # 登入成功，返回帳號資訊
            self.account = account.get('Account')
            self.selected_operator = account.get('Name')
            user_data = {
                'account_id': account.get('Account'),
                'username': account.get('Name'),
                'is_admin': bool(account.get('IsAdmin', 0)),
                'login_time': str(datetime.now()),
                'session_id': f"session_{int(time.time())}"
            }
            
            result = {
                'success': True,
                'data': user_data
            }
            print(f"登入成功: {result}")
            
            # 觸發用戶登入事件
            
            
            # 觸發會話開始事件
            session_data = {
                'session_id': user_data['session_id'],
                'user_id': user_data['account_id'],
                'username': user_data['username'],
                'start_time': user_data['login_time'],
                'is_admin': user_data['is_admin']
            }
            
            print(f"[CRASH_DEBUG] 準備執行 JavaScript，時間: {datetime.now()}")
            self.view.run_javascript('access_login_result(' + json.dumps(result, ensure_ascii=False) + ')')
            print(f"[CRASH_DEBUG] JavaScript 執行完成，時間: {datetime.now()}")
            #return json.dumps(result, ensure_ascii=False)
            
            
        except Exception as e:
            print(f"[CRASH_DEBUG] login 方法發生異常: {e}")
            import traceback
            print(f"[CRASH_DEBUG] 異常詳細信息:\n{traceback.format_exc()}")
            result = {
                'success': False,
                'error': f'登入失敗: {str(e)}'
            }
            print(f"登入異常: {result}")
            # 觸發認證失敗事件
           
            return json.dumps(result, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def start_ocr_test(self, test_data_json: str) -> str:
        """開始 OCR 測試"""
        try:
            test_data = json.loads(test_data_json)
            code1 = test_data.get('code1', '').strip()
            code2 = test_data.get('code2', '').strip()
            
            if not code1:
                return json.dumps({
                    'success': False,
                    'error': '請輸入靶材標籤'
                }, ensure_ascii=False)
            
            if code1 != code2:
                self.test_counter += 1
                self.ng_counter += 1
                self.update_counters()
                return json.dumps({
                    'success': False,
                    'error': '條碼不一致',
                    'result': 'error'
                }, ensure_ascii=False)
            
            # 設定來源條碼
            self.ocr_check_info.source_code = code1
            
            # 清空來源目錄
            self.ocr_check_info.source_image_path = ""
            
            # 清空來源目錄
            self.clear_source_directory()
            
            # 開始 OCR 檢測
            success, msg = self.perform_ocr_test(code1)
            
            return json.dumps({
                'success': success,
                'msg': msg
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    def perform_ocr_test(self, expected_code: str) -> tuple[bool, str]:
        """執行 OCR 測試"""
        try:
            # 連接 CCD
            self.start_time = datetime.now()
            
            # 計時開始
            start_connect = datetime.now()
            success, message = self.connect_ccd()
            connect_time = (datetime.now() - start_connect).total_seconds() * 1000
            print(f"連接 CCD 花費時間: {connect_time:.0f} ms")
            
            if not success:
                if self.view:
                    self.view.run_javascript('showAlert("'+message+'")')
                return False, message
            
            # 等待圖片檔案
            start_wait = datetime.now()
            image_file = self.wait_for_image()
            wait_time = (datetime.now() - start_wait).total_seconds() * 1000
            print(f"等待圖片檔案花費時間: {wait_time:.0f} ms")
            
            if not image_file:
                if self.view:
                    self.view.run_javascript('showAlert("等待圖片檔案超時")')
                return False, 'wait_pic_timeout'
            
            self.ocr_check_info.source_image_path = image_file
            
            # 顯示圖片
            start_show = datetime.now()
            if self.view and image_file:
                # 將路徑轉換為 Web 友好的格式
                image_url = self.normalize_path_for_web(image_file)
                print(f"顯示圖片: {image_file} -> {image_url}")
                self.view.run_javascript(f'showImage("{image_url}")')
            show_time = (datetime.now() - start_show).total_seconds() * 1000
            print(f"顯示圖片花費時間: {show_time:.0f} ms")
            
            # 取得 OCR 結果
            # 延遲1秒
            start_ocr = datetime.now()
            ocr_result = self.get_ocr_result()
            ocr_time = (datetime.now() - start_ocr).total_seconds() * 1000
            print(f"取得 OCR 結果花費時間: {ocr_time:.0f} ms")
            
            # 如果 OCR 失敗或結果不一致，嘗試使用 YOLO OCR
            if not ocr_result or ocr_result != expected_code:
                print(f"OCR 結果: {ocr_result}, 預期結果: {expected_code}")
                print("嘗試使用 YOLO OCR 進行識別...")
                
                try:
                    
                    yolo_result = self.yolo_ocr.access_ocr(image_file)
                    
                    if yolo_result['success'] and yolo_result['results']:
                        # 取得所有識別的文字並串接
                        ocr_result = yolo_result['results'][0]['text']
                        print(f"YOLO OCR 識別成功: {ocr_result}")
                        
                        # 輸出時間統計資訊
                        if 'timing' in yolo_result:
                            timing = yolo_result['timing']
                            print(f"總處理時間: {timing['total_ms']:.0f} ms")
                            print(f"YOLO 檢測: {timing['yolo_ms']:.0f} ms")
                            print(f"TrOCR 識別: {timing['trocr_ms']:.0f} ms")
                            print(f"識別文字數: {timing['text_count']}")
                    else:
                        print("YOLO OCR 識別失敗")
                        if 'error' in yolo_result:
                            print(f"錯誤訊息: {yolo_result['error']}")
                        
                except Exception as e:
                    print(f"YOLO OCR 執行失敗: {e}")
            
            if not ocr_result:
                if self.view:
                    self.view.run_javascript('showAlert("取得OCR字串失敗")')
                return False, 'ocr_error'
            else:
                if self.view:
                    self.view.run_javascript('setOCRResult("'+ocr_result+'")')
            self.ocr_result = ocr_result
            
            # 檢查結果
            start_check = datetime.now()
            if ocr_result == expected_code:
                self.test_counter += 1
                self.ocr_check_info.is_correct = True
                self.update_counters()
                if self.view:
                    self.view.run_javascript('showSuccessResult()')
                check_time = (datetime.now() - start_check).total_seconds() * 1000
                print(f"檢查結果花費時間: {check_time:.0f} ms")
                return True, 'success'
            else:
                self.test_counter += 1
                self.ng_counter += 1
                self.ocr_check_info.is_correct = False
                self.update_counters()
                if self.view:
                    self.view.run_javascript('showErrorResult()')
                check_time = (datetime.now() - start_check).total_seconds() * 1000
                print(f"檢查結果花費時間: {check_time:.0f} ms")
                return True, 'error'
                
        except Exception as e:
            print(f"OCR 測試失敗: {e}")
            if self.view:
                self.view.run_javascript('showAlert("'+str(e)+'")')
            return False, 'error'
    
    def connect_ccd(self) -> tuple[bool, str]:
        """連接 CCD"""
        try:
            self.tcp_client = TcpClient(self.server_ip, self.server_port)
            if not self.tcp_client.connect():
                return False, "CCD 連接失敗"
            
            self.tcp_client.set_timeout(5)
            
            # 等待初始回應
            response = self.wait_for_response("User:", 5)
            if not response:
                return False, "CCD 連接失敗: 等待 User: 提示超時"
            
            # 發送帳號
            self.tcp_client.send("admin\r\n")
            response = self.wait_for_response("PASSWORD", 5)
            if not response:
                return False, "CCD 連接失敗: 等待 PASSWORD 提示超時"
            
            # 發送密碼
            self.tcp_client.send("\r\n")
            response = self.wait_for_response("logged", 5)
            if not response:
                return False, "CCD 連接失敗: 等待登入確認超時"
            
            # 延遲 200 毫秒
            time.sleep(0.2)
            
            # 發送 OCR 觸發命令
            self.tcp_client.send("se8\r\n")
            response = self.wait_for_response("1", 5)
            if not response:
                return False, "CCD 連接失敗: se8 觸發失敗"
            
            return True, "CCD 連接成功"
            
        except Exception as e:
            print(f"連接 CCD 失敗: {e}")
            return False, f"CCD 連接失敗: {str(e)}"
    
    def wait_for_response(self, expected_text: str, timeout_seconds: int = 10, mode=0) -> str:
        """等待特定回應文字"""
        try:
            start_time = datetime.now()
            accumulated_response = ""
            count = 0
            
            while (datetime.now() - start_time).total_seconds() < timeout_seconds:
                # 嘗試接收資料
                response = self.tcp_client.receive()
                if response:
                    accumulated_response += response
                    print(f"[DEBUG] 接收到資料: {repr(response)}")
                    print(f"[DEBUG] 累積回應: {repr(accumulated_response)}")
                    
                    # 檢查是否包含預期的文字
                    if expected_text.lower() in accumulated_response.lower():
                        print(f"[DEBUG] 找到預期文字: {expected_text}")
                        # 找到關鍵字後,再等待1秒繼續接收資料
                        if mode == 0:
                            print(f"[DEBUG] mode=0，立即回傳")
                            return accumulated_response
                        wait_end = datetime.now() + timedelta(seconds=0.3)
                        while datetime.now() < wait_end:
                            # 檢查是否包含兩個 \r\n
                            if accumulated_response.count('\r\n') >= 2:
                                print(f"[DEBUG] 找到兩個 \\r\\n，回傳")
                                return accumulated_response
                            response = self.tcp_client.receive()
                            if response:
                                accumulated_response += response
                            time.sleep(0.05)
                        return accumulated_response
                
                # 減少等待時間，提高響應速度
                time.sleep(0.01)  # 從 0.1 秒減少到 0.01 秒
            
            # 超時
            print(f"[DEBUG] 等待回應超時，累積回應: {repr(accumulated_response)}")
            return ""
            
        except Exception as e:
            print(f"等待回應失敗: {e}")
            return ""
    
    def disconnect_ccd(self):
        """斷開 CCD 連接"""
        try:
            if self.tcp_client:
                self.tcp_client.close()
                self.tcp_client = None
        except Exception as e:
            print(f"斷開 CCD 連接失敗: {e}")
    def wait_for_image(self, timeout=30000) -> str:
        """等待圖片檔案"""
        try:
            start_time = datetime.now()
            while True:
                if (datetime.now() - start_time).total_seconds() * 1000 > timeout:
                    return ""
                
                files = [f for f in os.listdir(self.source_image_path) 
                        if f.lower().endswith('.bmp') and 
                        os.path.getctime(os.path.join(self.source_image_path, f)) > self.start_time.timestamp()]
                
                if files:
                    return os.path.join(self.source_image_path, files[0])
                
                time.sleep(0.2)
                
        except Exception as e:
            print(f"等待圖片失敗: {e}")
            return ""
    
    def get_ocr_result(self) -> str:
        """取得 OCR 結果"""
        try:
            if not self.tcp_client or not self.tcp_client.is_connected:
                print("[DEBUG] TCP 客戶端未連接")
                return ""
            
            print("[DEBUG] 發送 gvstring 命令")
            self.tcp_client.send("gvstring\r\n")
            
            print("[DEBUG] 開始等待回應...")
            response = self.wait_for_response("1\r", 10, 0)  # 等待 "1\r" 開頭的回應，找到後立即回傳
            
            if not response:
                print("[DEBUG] 沒有收到回應")
                return ""
            
            print(f"[DEBUG] 收到完整回應: {repr(response)}")
            lines = response.split('\r')
            print(f"[DEBUG] 分割後的行數: {len(lines)}")
            
            if len(lines) < 2:
                print("[DEBUG] 回應行數不足")
                return ""
            
            print(f"[DEBUG] 第一行: {repr(lines[0])}")
            if lines[0].strip() != "1":
                print("[DEBUG] 第一行不是 '1'")
                return ""
            
            result = lines[1].strip()
            print(f"[DEBUG] OCR 結果: {repr(result)}")
            return result
            
        except Exception as e:
            print(f"取得 OCR 結果失敗: {e}")
            return ""
    
    def clear_source_directory(self):
        """清空來源目錄"""
        try:
            for file in os.listdir(self.source_image_path):
                file_path = os.path.join(self.source_image_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"清空來源目錄失敗: {e}")
    
    def update_counters(self):
        """更新計數器"""
        try:
            # 檢查是否需要重置計數器（新的一天）
            current_date = datetime.today()
            if current_date.date() != self.today.date():
                self.today = current_date
                self.test_counter = 0
                self.ng_counter = 0
            
            # 這裡可以保存到資料庫或設定檔
            print(f"測試次數: {self.test_counter}, NG次數: {self.ng_counter}")
            
        except Exception as e:
            print(f"更新計數器失敗: {e}")
    
    @pyqtSlot(result=str)
    def get_current_info(self) -> str:
        """取得當前資訊"""
        try:
            return json.dumps({
                'success': True,
                'data': {
                    'date': datetime.now().strftime('%Y/%m/%d'),
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'total_count': self.test_counter,
                    'ng_count': self.ng_counter,
                    'user_name': self.user_name
                }
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def set_judgment(self, judgment_data_json: str) -> str:
        """設定判定結果"""
        try:
            judgment_data = json.loads(judgment_data_json)
            judgment_type = judgment_data.get('type', '')
            
            if judgment_type == 'allow':
                self.ocr_check_info.err_action = ErrAction.ALLOW
            elif judgment_type == 'back':
                self.ocr_check_info.err_action = ErrAction.BACK
            elif judgment_type == 'fold':
                self.ocr_check_info.err_action_reason = ErrActionReason.FOLD
            elif judgment_type == 'ocr_error':
                self.ocr_check_info.err_action_reason = ErrActionReason.OCR_CHECK_ERROR
            elif judgment_type == 'cannot_ocr':
                self.ocr_check_info.err_action_reason = ErrActionReason.CANNOT_OCR
            elif judgment_type == 'exterior_ok':
                self.ocr_check_info.exterior = ExteriorCheckResult.OK
            elif judgment_type == 'exterior_ng':
                self.ocr_check_info.exterior = ExteriorCheckResult.NG
            elif judgment_type == 'class1':
                self.ocr_check_info.class1 = not self.ocr_check_info.class1
            elif judgment_type == 'class2':
                self.ocr_check_info.class2 = not self.ocr_check_info.class2
            elif judgment_type == 'reason_oxidation':
                self.ocr_check_info.exterior_ng_reason = ExteriorNGReason.OXIDATION
            elif judgment_type == 'reason_leak':
                self.ocr_check_info.exterior_ng_reason = ExteriorNGReason.LEAK
            elif judgment_type == 'reason_foreign_matter':
                self.ocr_check_info.exterior_ng_reason = ExteriorNGReason.FOREIGN_MATTER
            elif judgment_type == 'reason_hole_abnormal':
                self.ocr_check_info.exterior_ng_reason = ExteriorNGReason.HOLE_ABNORMAL
            
            return json.dumps({
                'success': True,
                'message': '判定設定成功'
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def show_image(self, image_path: str) -> str:
        """顯示圖片"""
        try:
            if not image_path or not os.path.exists(image_path):
                if self.view:
                    self.view.run_javascript('showNoImage()')
                return json.dumps({
                    'success': False,
                    'error': '圖片檔案不存在'
                }, ensure_ascii=False)
            
            # 從設定檔讀取圖片處理參數
            image_config = self.config_manager.Config.ImageProcessing
            scale_params = {
                'scale': image_config.Scale,
                'offsetX': image_config.Offset_X,
                'offsetY': image_config.Offset_Y
            }
            
            print(f"圖片處理參數: scale={scale_params['scale']}, offsetX={scale_params['offsetX']}, offsetY={scale_params['offsetY']}")
            
            # 轉換為 Web 友好的路徑格式
            if self.view:
                # 將路徑轉換為 Web 友好的格式
                image_url = self.normalize_path_for_web(image_path)
                print(f"手動顯示圖片: {image_path} -> {image_url}")
                
                # 先設定縮放參數，再顯示圖片
                js_code = f"""
                CanvasImage.setScaleParams({scale_params['scale']}, {scale_params['offsetX']}, {scale_params['offsetY']});
                showImage("{image_url}", {{
                    scale: {scale_params['scale']},
                    offsetX: {scale_params['offsetX']},
                    offsetY: {scale_params['offsetY']}
                }});
                """
                self.view.run_javascript(js_code)
            
            return json.dumps({
                'success': True,
                'message': '圖片顯示成功',
                'scale_params': scale_params
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def set_work_status(self, status: str) -> str:
        """設定工作狀態"""
        try:
            if self.view:
                self.view.run_javascript(f'setWorkStatus("{status}")')
            
            return json.dumps({
                'success': True,
                'message': '工作狀態設定成功'
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def set_scale_params(self, scale_params_json: str) -> str:
        """設定縮放參數"""
        try:
            params = json.loads(scale_params_json)
            scale = params.get('scale', 1.0)
            offset_x = params.get('offset_x', 0)
            offset_y = params.get('offset_y', 0)
            
            if self.view:
                self.view.run_javascript(f'setScaleParams({scale}, {offset_x}, {offset_y})')
            
            return json.dumps({
                'success': True,
                'message': '縮放參數設定成功'
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(result=str)
    def save_log(self) -> str:
        """儲存記錄"""
        try:
            if not self.db_manager:
                return json.dumps({
                    'success': False,
                    'error': '資料庫未初始化'
                }, ensure_ascii=False)
            
            # 決定結果類型和關鍵字
            c_path = "Err"  # 預設為錯誤
            keyword = "OK"
            judgment_value = 0
            
            if self.ocr_check_info.is_correct:
                c_path = "OK"
                keyword = "OK"
                judgment_value = 0
            else:
                if self.ocr_check_info.err_action == ErrAction.BACK:
                    c_path = "NG"
                    keyword = "NG"
                    judgment_value = 1
                else:
                    # 根據錯誤原因決定關鍵字
                    if self.ocr_check_info.err_action_reason == ErrActionReason.CANNOT_OCR:
                        keyword = "NO_OCR"
                        judgment_value = 2
                    elif self.ocr_check_info.err_action_reason == ErrActionReason.OCR_CHECK_ERROR:
                        keyword = "OCR_Fail"
                        judgment_value = 3
                    elif self.ocr_check_info.err_action_reason == ErrActionReason.FOLD:
                        keyword = "OCR_Fold"
                        judgment_value = 4
            
            # 儲存圖片
            saved_image_path = ""
            if hasattr(self.ocr_check_info, 'source_image_path') and self.ocr_check_info.source_image_path:
                saved_image_path = self.save_image(
                    self.ocr_check_info.source_image_path, 
                    c_path, 
                    keyword
                )
            
            # 儲存螢幕擷取（針對 NG 和錯誤情況）
            if not self.ocr_check_info.is_correct:
                if self.ocr_check_info.err_action == ErrAction.BACK:
                    self.save_screen_to_file("NG")
                else:
                    # 根據錯誤原因儲存不同的螢幕擷取
                    if self.ocr_check_info.err_action_reason == ErrActionReason.CANNOT_OCR:
                        self.save_screen_to_file("Err_NoOCR")
                    elif self.ocr_check_info.err_action_reason == ErrActionReason.OCR_CHECK_ERROR:
                        self.save_screen_to_file("Err_Fail")
                    elif self.ocr_check_info.err_action_reason == ErrActionReason.FOLD:
                        self.save_screen_to_file("Err_Fold")
            
            # 建立記錄資料
            log_data = {
                'Account': self.account,
                'Time': datetime.now(),
                'OK': self.ocr_check_info.is_correct,
                'Source': getattr(self.ocr_check_info, 'source_code', ''),
                'OCRResult': self.ocr_result,
                'Manual': not self.ocr_check_info.is_correct,
                'KeyInResult': self.ocr_result,
                'Processor': self.selected_operator,
                'Judgment': judgment_value,
                'Image': saved_image_path,
                'ExteriorClass': self.get_exterior_class_value(),
                'IsExteriorOK': self.ocr_check_info.exterior != ExteriorCheckResult.NG,
                'ExteriorErrReason': self.ocr_check_info.exterior_ng_reason
            }
            
            # 儲存到資料庫
            success = self.db_manager.create_ocr_log(log_data)
            
            if success:
                # 重置檢查資訊
                self.ocr_check_info = OCRCheckInfo()
                return json.dumps({
                    'success': True,
                    'message': '記錄儲存成功'
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    'success': False,
                    'error': '記錄儲存失敗'
                }, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    def get_judgment_value(self) -> int:
        """取得判定值"""
        if self.ocr_check_info.is_correct:
            return 0
        elif self.ocr_check_info.err_action == ErrAction.BACK:
            return 1
        elif self.ocr_check_info.err_action_reason == ErrActionReason.CANNOT_OCR:
            return 2
        elif self.ocr_check_info.err_action_reason == ErrActionReason.OCR_CHECK_ERROR:
            return 3
        elif self.ocr_check_info.err_action_reason == ErrActionReason.FOLD:
            return 4
        return 0
    
    def get_exterior_class_value(self) -> int:
        """取得外觀類別值"""
        value = 0
        if self.ocr_check_info.class1:
            value += 1
        if self.ocr_check_info.class2:
            value += 2
        return value
    
    def save_image(self, source_image_path: str, result_type: str, keyword: str) -> str:
        """儲存圖片到指定路徑"""
        try:
            if not source_image_path or not os.path.exists(source_image_path):
                return ""
            
            # 根據結果類型決定目錄
            if result_type == "OK":
                c_path = "OK"
            elif result_type == "NG":
                c_path = "NG"
            else:
                c_path = "Err"
            
            # 建立目錄結構: Target_Image_Path/cPath/yyMM/yyMMdd/
            now = datetime.now()
            base_path = os.path.join(self.target_image_path, c_path)
            month_path = os.path.join(base_path, now.strftime("%y%m"))
            day_path = os.path.join(month_path, now.strftime("%y%m%d"))
            
            # 確保目錄存在
            os.makedirs(day_path, exist_ok=True)
            
            # 建立備份路徑（僅對 Err 類型）
            backup_path = ""
            if c_path == "Err" and hasattr(self.config_manager.Config.Settings.Paths, 'OCR_Backup_Path'):
                backup_base = self.config_manager.Config.Settings.Paths.OCR_Backup_Path
                if backup_base and os.path.exists(backup_base):
                    backup_path = os.path.join(backup_base, c_path)
                    backup_month = os.path.join(backup_path, now.strftime("%y%m"))
                    backup_day = os.path.join(backup_month, now.strftime("%y%m%d"))
                    os.makedirs(backup_day, exist_ok=True)
                    backup_path = backup_day
            
            # 儲存圖片
            return self.save_ccd_image(day_path, backup_path, keyword, source_image_path)
            
        except Exception as e:
            print(f"儲存圖片失敗: {e}")
            return ""
    
    def save_ccd_image(self, c_path: str, backup_path: str, keyword: str, source_image_path: str) -> str:
        """儲存 CCD 圖片，包含檔案命名和重複處理邏輯"""
        try:
            now = datetime.now()
            source_code = getattr(self.ocr_check_info, 'source_code', 'UNKNOWN')
            
            # 建立檔案名稱: {source_code}_{yyMMdd}_{HHmmss}_{keyword}.jpg
            filename = f"{source_code}_{now.strftime('%y%m%d')}_{now.strftime('%H%M%S')}_{keyword}.jpg"
            file_path = os.path.join(c_path, filename)
            
            # 處理檔案重複
            file_index = 2
            while os.path.exists(file_path):
                filename = f"{source_code}-{file_index}_{now.strftime('%y%m%d')}_{now.strftime('%H%M%S')}_{keyword}.jpg"
                file_path = os.path.join(c_path, filename)
                file_index += 1
            
            # 複製原始圖片到目標位置
            import shutil
            shutil.copy2(source_image_path, file_path)
            
            # 如果有備份路徑，也複製一份
            if backup_path:
                backup_file = os.path.join(backup_path, filename)
                shutil.copy2(source_image_path, backup_file)
            
            return file_path
            
        except Exception as e:
            print(f"儲存 CCD 圖片失敗: {e}")
            return ""
    
    def save_screen_to_file(self, keyword: str) -> str:
        """儲存螢幕擷取到檔案"""
        try:
            # 建立螢幕擷取目錄結構
            now = datetime.now()
            screen_path = os.path.join(self.target_image_path, "螢幕擷取")
            month_path = os.path.join(screen_path, now.strftime("%y%m"))
            day_path = os.path.join(month_path, now.strftime("%y%m%d"))
            
            # 確保目錄存在
            os.makedirs(day_path, exist_ok=True)
            
            # 建立檔案名稱
            source_code = getattr(self.ocr_check_info, 'source_code', 'UNKNOWN')
            filename = f"{source_code}_{now.strftime('%y%m%d')}_{now.strftime('%H%M%S')}_{keyword}.jpg"
            file_path = os.path.join(day_path, filename)
            
            # 實際執行螢幕擷取
            self.capture_screen(file_path)
            
            print(f"螢幕擷取已儲存: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"儲存螢幕擷取失敗: {e}")
            return ""
    
    def capture_screen(self, file_path: str):
        """實際擷取螢幕並儲存到指定路徑"""
        try:
            # 方法1: 使用 PyQt5 擷取螢幕（推薦，因為已經在使用 PyQt5）
            try:
                from PyQt5.QtWidgets import QApplication
                from PyQt5.QtGui import QPixmap, QScreen
                from PyQt5.QtCore import Qt
                from PIL import Image
                import io
                
                # 取得應用程式實例
                app = QApplication.instance()
                if app is None:
                    app = QApplication([])
                
                # 取得主螢幕
                screen = QApplication.primaryScreen()
                if screen is None:
                    raise Exception("無法取得螢幕")
                
                # 擷取整個螢幕
                pixmap = screen.grabWindow(0)
                
                # 轉換為 PIL Image
                qimg = pixmap.toImage()
                width = qimg.width()
                height = qimg.height()
                
                # 取得像素資料
                ptr = qimg.bits()
                ptr.setsize(qimg.byteCount())
                arr = np.array(ptr).reshape(height, width, 4)  # RGBA
                
                # 轉換為 RGB
                rgb_array = arr[:, :, [2, 1, 0]]  # BGR to RGB
                
                # 建立 PIL Image 並儲存
                img = Image.fromarray(rgb_array, 'RGB')
                img.save(file_path, 'JPEG', quality=95)
                return
                
            except Exception as e:
                print(f"PyQt5 螢幕擷取失敗: {e}")
            
            # 方法2: 使用 PIL 和 pyautogui 擷取整個螢幕
            try:
                import pyautogui
                from PIL import Image
                
                # 擷取整個螢幕
                screenshot = pyautogui.screenshot()
                # 儲存為 JPEG 格式
                screenshot.save(file_path, 'JPEG', quality=95)
                return
            except ImportError:
                print("pyautogui 未安裝，嘗試其他方法...")
            except Exception as e:
                print(f"pyautogui 螢幕擷取失敗: {e}")
            
            # 方法3: 使用 Windows API (僅限 Windows)
            try:
                import win32gui
                import win32ui
                import win32con
                from PIL import Image
                
                # 取得桌面視窗
                hdesktop = win32gui.GetDesktopWindow()
                
                # 取得螢幕尺寸
                left, top, right, bottom = win32gui.GetWindowRect(hdesktop)
                width = right - left
                height = bottom - top
                
                # 建立裝置內容
                hdesktop_dc = win32gui.GetWindowDC(hdesktop)
                img_dc = win32ui.CreateDCFromHandle(hdesktop_dc)
                mem_dc = img_dc.CreateCompatibleDC()
                
                # 建立點陣圖
                screenshot = win32ui.CreateBitmap()
                screenshot.CreateCompatibleBitmap(img_dc, width, height)
                mem_dc.SelectObject(screenshot)
                
                # 複製螢幕內容
                mem_dc.BitBlt((0, 0), (width, height), img_dc, (0, 0), win32con.SRCCOPY)
                
                # 轉換為 PIL Image
                bmpinfo = screenshot.GetInfo()
                bmpstr = screenshot.GetBitmapBits(True)
                img = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1
                )
                
                # 儲存圖片
                img.save(file_path, 'JPEG', quality=95)
                
                # 清理資源
                mem_dc.DeleteDC()
                win32gui.ReleaseDC(hdesktop, hdesktop_dc)
                win32gui.DeleteObject(screenshot.GetHandle())
                return
                
            except ImportError:
                print("pywin32 未安裝，無法使用 Windows API")
            except Exception as e:
                print(f"Windows API 螢幕擷取失敗: {e}")
            
            # 如果所有方法都失敗，建立一個佔位符檔案
            print("所有螢幕擷取方法都失敗，建立佔位符檔案")
            from PIL import Image, ImageDraw
            placeholder = Image.new('RGB', (800, 600), color='lightgray')
            draw = ImageDraw.Draw(placeholder)
            draw.text((50, 50), "螢幕擷取功能不可用", fill='black')
            placeholder.save(file_path, 'JPEG')
            
        except Exception as e:
            print(f"螢幕擷取失敗: {e}")
            # 建立錯誤佔位符
            try:
                from PIL import Image, ImageDraw
                error_img = Image.new('RGB', (800, 600), color='red')
                draw = ImageDraw.Draw(error_img)
                draw.text((50, 50), f"螢幕擷取失敗: {str(e)}", fill='white')
                error_img.save(file_path, 'JPEG')
            except:
                pass
    @pyqtSlot(str, result=str)
    def load_processor(self, data_json: str) -> str:
        """載入操作者(帳號)列表 含 Acoount Name Checked"""
        try:
            # 從資料庫查詢帳號資料
            accounts = self.db_manager.get_accounts()
            
            # 轉換成 ProcessorInfo 格式
            processor_list = []
            for acc in accounts:
                processor = {
                    'account': acc.get('Account', ''),
                    'name': acc.get('Name', ''),
                    'checked': acc.get('Account', '') == self.account
                }
                processor_list.append(processor)
                
            return json.dumps({
                'success': True,
                'data': processor_list
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def do_action(self, action_data_json: str) -> str:
        """執行動作"""
        try:
            action_data = json.loads(action_data_json)
            action_id = action_data.get('action_id')
            action_data_content = action_data.get('action_data', {})
            
            # 根據 action_id 執行不同的動作
            if action_id == 1:
                # 返回前台
                return json.dumps({
                    'success': True,
                    'message': '返回前台'
                }, ensure_ascii=False)
            elif action_id == 6:
                # 櫃子管理
                return json.dumps({
                    'success': True,
                    'message': '開啟櫃子管理'
                }, ensure_ascii=False)
            elif action_id == 8:
                # 歷史紀錄
                return json.dumps({
                    'success': True,
                    'message': '開啟歷史紀錄'
                }, ensure_ascii=False)
            elif action_id == 9:
                # 參數設定
                return json.dumps({
                    'success': True,
                    'message': '開啟參數設定'
                }, ensure_ascii=False)
            elif action_id == 10:
                # 會員管理
                return json.dumps({
                    'success': True,
                    'message': '開啟會員管理'
                }, ensure_ascii=False)
            elif action_id == 11:
                # 群組管理
                return json.dumps({
                    'success': True,
                    'message': '開啟群組管理'
                }, ensure_ascii=False)
            elif action_id == 17:
                # Wi-Fi 設定
                return json.dumps({
                    'success': True,
                    'message': '開啟 Wi-Fi 設定'
                }, ensure_ascii=False)
            elif action_id == 18:
                # 帳號管理
                return self.open_account_management()
            elif action_id == 19:
                # 關閉帳號管理
                return self.close_account_management()
            elif action_id == 23:
                # 隱藏帳號管理
                return self.hide_account_management()
            elif action_id == 24:
                # 顯示帳號管理
                return self.show_account_management()
            elif action_id == 25:
                # 取得帳號管理視窗狀態
                return self.get_account_window_status()
            elif action_id == 26:
                # 設定帳號管理視窗幾何形狀
                action_data = action_data_json if action_data_json else '{}'
                return self.set_account_window_geometry(action_data)
            elif action_id == 27:
                # 將帳號管理視窗置中
                return self.center_account_window()
            elif action_id == 28:
                # 控制帳號管理視窗狀態
                action_data = action_data_json if action_data_json else '{}'
                try:
                    data = json.loads(action_data)
                    control_type = data.get('control_type', 'restore')
                    return self.control_account_window(control_type)
                except:
                    return self.control_account_window('restore')
            elif action_id == 29:
                # 取得帳號管理視窗狀態
                return self.get_account_window_state()
            elif action_id == 30:
                # 設定帳號管理視窗標題
                action_data = action_data_json if action_data_json else '{}'
                try:
                    data = json.loads(action_data)
                    title = data.get('title', '帳號管理系統')
                    return self.set_account_window_title(title)
                except:
                    return self.set_account_window_title('帳號管理系統')
            elif action_id == 21:
                # 匯出功能
                return self.open_export_dialog()
            else:
                return json.dumps({
                    'success': False,
                    'error': f'未知的動作 ID: {action_id}'
                }, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    def open_account_management(self):
        """開啟帳號管理視窗"""
        try:
            # 檢查資料庫管理器是否可用
            if not self.db_manager:
                return json.dumps({
                    'success': False,
                    'error': '資料庫連接不可用'
                }, ensure_ascii=False)
            
            if not self.account_window:
                # 建立新的帳號管理視窗
                self.account_window = AccountManagerWindow(self.db_manager)
                # 設定為最上層視窗
                self.account_window.setWindowFlags(Qt.WindowStaysOnTopHint)
                # 使用非模態視窗，避免主視窗被卡住
                self.account_window.show()
                
                # 監聽視窗關閉信號
                self.account_window.window_closed.connect(self.on_account_window_closed)
                
                return json.dumps({
                    'success': True,
                    'message': '帳號管理視窗已開啟'
                }, ensure_ascii=False)
            else:
                # 如果視窗已存在，將其置前
                self.account_window.raise_()
                self.account_window.activateWindow()
                
                return json.dumps({
                    'success': True,
                    'message': '帳號管理視窗已置前'
                }, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'開啟帳號管理視窗失敗: {str(e)}'
            }, ensure_ascii=False)
    
    def close_account_management(self):
        """關閉帳號管理視窗"""
        try:
            if self.account_window:
                self.account_window.close_window()
                return json.dumps({
                    'success': True,
                    'message': '帳號管理視窗已關閉'
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    'success': False,
                    'error': '帳號管理視窗未開啟'
                }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'關閉帳號管理視窗失敗: {str(e)}'
            }, ensure_ascii=False)
    
    def hide_account_management(self):
        """隱藏帳號管理視窗"""
        try:
            if self.account_window:
                self.account_window.hide_window()
                return json.dumps({
                    'success': True,
                    'message': '帳號管理視窗已隱藏'
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    'success': False,
                    'error': '帳號管理視窗未開啟'
                }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'隱藏帳號管理視窗失敗: {str(e)}'
            }, ensure_ascii=False)
    
    def show_account_management(self):
        """顯示帳號管理視窗"""
        try:
            if self.account_window:
                self.account_window.show_window()
                return json.dumps({
                    'success': True,
                    'message': '帳號管理視窗已顯示'
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    'success': False,
                    'error': '帳號管理視窗未開啟'
                }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'顯示帳號管理視窗失敗: {str(e)}'
            }, ensure_ascii=False)
    
    def get_account_window_status(self):
        """取得帳號管理視窗狀態"""
        try:
            if self.account_window:
                window_info = self.account_window.get_window_info()
                return json.dumps({
                    'success': True,
                    'data': {
                        'exists': True,
                        'visible': window_info['visible'],
                        'geometry': window_info['geometry']
                    }
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    'success': True,
                    'data': {
                        'exists': False,
                        'visible': False,
                        'geometry': None
                    }
                }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'取得帳號管理視窗狀態失敗: {str(e)}'
            }, ensure_ascii=False)
    
    def set_account_window_geometry(self, geometry_data_json: str):
        """設定帳號管理視窗幾何形狀"""
        try:
            if not self.account_window:
                return json.dumps({
                    'success': False,
                    'error': '帳號管理視窗未開啟'
                }, ensure_ascii=False)
            
            geometry_data = json.loads(geometry_data_json)
            x = geometry_data.get('x', 100)
            y = geometry_data.get('y', 100)
            width = geometry_data.get('width', 1200)
            height = geometry_data.get('height', 800)
            
            self.account_window.set_window_geometry(x, y, width, height)
            
            return json.dumps({
                'success': True,
                'message': '視窗幾何形狀已設定'
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'設定視窗幾何形狀失敗: {str(e)}'
            }, ensure_ascii=False)
    
    def center_account_window(self):
        """將帳號管理視窗置中於螢幕"""
        try:
            if not self.account_window:
                return json.dumps({
                    'success': False,
                    'error': '帳號管理視窗未開啟'
                }, ensure_ascii=False)
            
            self.account_window.center_on_screen()
            
            return json.dumps({
                'success': True,
                'message': '視窗已置中'
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'置中視窗失敗: {str(e)}'
            }, ensure_ascii=False)
    
    def control_account_window(self, control_type: str):
        """控制帳號管理視窗狀態"""
        try:
            if not self.account_window:
                return json.dumps({
                    'success': False,
                    'error': '帳號管理視窗未開啟'
                }, ensure_ascii=False)
            
            if control_type == 'maximize':
                self.account_window.maximize_window()
                message = '視窗已最大化'
            elif control_type == 'minimize':
                self.account_window.minimize_window()
                message = '視窗已最小化'
            elif control_type == 'restore':
                self.account_window.restore_window()
                message = '視窗已還原'
            else:
                return json.dumps({
                    'success': False,
                    'error': f'未知的控制類型: {control_type}'
                }, ensure_ascii=False)
            
            return json.dumps({
                'success': True,
                'message': message
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'控制視窗狀態失敗: {str(e)}'
            }, ensure_ascii=False)
    
    def get_account_window_state(self):
        """取得帳號管理視窗狀態"""
        try:
            if not self.account_window:
                return json.dumps({
                    'success': True,
                    'data': {
                        'exists': False,
                        'state': 'none'
                    }
                }, ensure_ascii=False)
            
            window_state = self.account_window.get_window_state()
            window_title = self.account_window.get_window_title()
            
            return json.dumps({
                'success': True,
                'data': {
                    'exists': True,
                    'state': window_state,
                    'title': window_title
                }
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'取得視窗狀態失敗: {str(e)}'
            }, ensure_ascii=False)
    
    def set_account_window_title(self, title: str):
        """設定帳號管理視窗標題"""
        try:
            if not self.account_window:
                return json.dumps({
                    'success': False,
                    'error': '帳號管理視窗未開啟'
                }, ensure_ascii=False)
            
            self.account_window.set_window_title(title)
            
            return json.dumps({
                'success': True,
                'message': f'視窗標題已設定為: {title}'
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'設定視窗標題失敗: {str(e)}'
            }, ensure_ascii=False)
    
    def on_account_window_closed(self):
        """帳號管理視窗關閉事件"""
        print("帳號管理視窗已關閉")
        self.account_window = None
    
    def open_export_dialog(self):
        """開啟匯出對話框"""
        try:
            # 檢查資料庫管理器是否可用
            if not self.db_manager:
                return json.dumps({
                    'success': False,
                    'error': '資料庫連接不可用'
                }, ensure_ascii=False)
            
            if not self.export_window:
                # 建立新的匯出視窗
                try:
                    default_dir = getattr(self.config_manager.Config.Settings.Paths, 'Export_Default_Path', '')
                except AttributeError:
                    default_dir = ''
                
                try:
                    self.export_window = ExportWindow(default_dir, self.db_manager)
                    # 設定為最上層視窗
                    self.export_window.setWindowFlags(Qt.WindowStaysOnTopHint)
                    # 使用非模態視窗，避免主視窗被卡住
                    self.export_window.show()
                    
                    # 監聽視窗關閉信號
                    self.export_window.closeEvent = self.on_export_window_closed
                    
                    return json.dumps({
                        'success': True,
                        'message': '匯出視窗已開啟'
                    }, ensure_ascii=False)
                except Exception as export_error:
                    return json.dumps({
                        'success': False,
                        'error': f'建立匯出視窗失敗: {str(export_error)}'
                    }, ensure_ascii=False)
            else:
                # 如果視窗已存在，將其置前
                self.export_window.raise_()
                self.export_window.activateWindow()
                
                return json.dumps({
                    'success': True,
                    'message': '匯出視窗已置前'
                }, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'開啟匯出視窗失敗: {str(e)}'
            }, ensure_ascii=False)
    
    def on_export_window_closed(self, event):
        """匯出視窗關閉事件"""
        print("匯出視窗已關閉")
        self.export_window = None
        event.accept()
    
    @pyqtSlot(result=str)
    def get_settings(self) -> str:
        """取得當前設定"""
        try:
            config = self.config_manager.Config
            
            settings_data = {
                'cognex': {
                    'ip': config.Settings.Cognex.IP,
                    'port': config.Settings.Cognex.Port,
                    'port_cmd': getattr(config.Settings.Cognex, 'Port_Cmd', 8604)
                },
                'paths': {
                    'ocr_image_save_path': config.Settings.Paths.OCR_Image_Save_Path,
                    'db_image_save_path': config.Settings.Paths.DB_Image_Save_Path,
                    'export_default_path': config.Settings.Paths.Export_Default_Path,
                    'ocr_backup_path': config.Settings.Paths.OCR_Backup_Path
                },
                'image': {
                    'offset_x': config.Settings.Image_Processing.Offset_X,
                    'offset_y': config.Settings.Image_Processing.Offset_Y,
                    'scale': config.Settings.Image_Processing.Scale
                },
                'timing': {
                    'ocr_retry_time': config.Settings.Timing.OCR_Retry_Time,
                    'pic_wait_time': config.Settings.Timing.Pic_Wait_Time
                }
            }
            
            return json.dumps({
                'success': True,
                'data': settings_data
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(str)
    def show_alert_msg(self, message: str):
        """顯示警告訊息"""
        print(f"[DEBUG] {message}")
    
    @pyqtSlot(str, result=str)
    def save_settings(self, settings_data_json: str) -> str:
        """儲存設定"""
        try:
            settings_data = json.loads(settings_data_json)
            
            # 驗證路徑是否存在
            paths = settings_data.get('paths', {})
            required_paths = [
                paths.get('ocr_image_save_path', ''),
                paths.get('db_image_save_path', ''),
                paths.get('export_default_path', '')
            ]
            
            for path in required_paths:
                if path and not os.path.exists(path):
                    return json.dumps({
                        'success': False,
                        'error': f'路徑不存在: {path}'
                    }, ensure_ascii=False)
            
            # 驗證數值參數
            image_settings = settings_data.get('image', {})
            offset_x = image_settings.get('offset_x', 0)
            offset_y = image_settings.get('offset_y', 0)
            scale = image_settings.get('scale', 1.0)
            
            if not isinstance(offset_x, int):
                return json.dumps({
                    'success': False,
                    'error': '偏移量X需是整數'
                }, ensure_ascii=False)
            
            if not isinstance(offset_y, int):
                return json.dumps({
                    'success': False,
                    'error': '偏移量Y需是整數'
                }, ensure_ascii=False)
            
            if not isinstance(scale, (int, float)):
                return json.dumps({
                    'success': False,
                    'error': '放大比例需是數值'
                }, ensure_ascii=False)
            
            if scale <= 0 or scale > 3:
                return json.dumps({
                    'success': False,
                    'error': '放大比例需大於0且小於3'
                }, ensure_ascii=False)
            
            # 驗證重試次數
            timing_settings = settings_data.get('timing', {})
            retry_time = timing_settings.get('ocr_retry_time', 1)
            wait_time = timing_settings.get('pic_wait_time', 5000)
            
            if not isinstance(retry_time, int) or retry_time < 0:
                return json.dumps({
                    'success': False,
                    'error': '重試次數需為非負整數'
                }, ensure_ascii=False)
            
            if not isinstance(wait_time, int) or wait_time < 1000:
                return json.dumps({
                    'success': False,
                    'error': '圖片等待時間不得小於1000毫秒'
                }, ensure_ascii=False)
            
            # 更新設定
            config = self.config_manager.Config
            
            # 更新 Cognex 設定
            cognex_settings = settings_data.get('cognex', {})
            config.Settings.Cognex.IP = cognex_settings.get('ip', '192.168.1.5')
            config.Settings.Cognex.Port = cognex_settings.get('port', 8601)
            if hasattr(config.Settings.Cognex, 'Port_Cmd'):
                config.Settings.Cognex.Port_Cmd = cognex_settings.get('port_cmd', 8604)
            
            # 更新路徑設定
            config.Settings.Paths.OCR_Image_Save_Path = paths.get('ocr_image_save_path', '')
            config.Settings.Paths.DB_Image_Save_Path = paths.get('db_image_save_path', '')
            config.Settings.Paths.Export_Default_Path = paths.get('export_default_path', '')
            config.Settings.Paths.OCR_Backup_Path = paths.get('ocr_backup_path', '')
            
            # 更新圖片設定
            config.Settings.Image_Processing.Offset_X = offset_x
            config.Settings.Image_Processing.Offset_Y = offset_y
            config.Settings.Image_Processing.Scale = scale
            
            # 更新時間設定
            config.Settings.Timing.OCR_Retry_Time = retry_time
            config.Settings.Timing.Pic_Wait_Time = wait_time
            
            # 儲存設定檔
            self.config_manager.save_config()
            
            # 重新載入設定到記憶體
            self.load_settings()
            
            return json.dumps({
                'success': True,
                'message': '設定儲存成功'
            }, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'儲存設定失敗: {str(e)}'
            }, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def browse_folder(self, folder_type: str) -> str:
        """瀏覽資料夾"""
        try:
            from PyQt5.QtWidgets import QFileDialog, QApplication
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # 根據類型設定預設路徑
            default_paths = {
                'ocr_image': self.source_image_path,
                'db_image': self.target_image_path,
                'export': getattr(self.config_manager.Config.Settings.Paths, 'Export_Default_Path', ''),
                'backup': getattr(self.config_manager.Config.Settings.Paths, 'OCR_Backup_Path', '')
            }
            
            default_path = default_paths.get(folder_type, '')
            
            folder_path = QFileDialog.getExistingDirectory(
                None,
                f"選擇{folder_type}資料夾",
                default_path,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            
            if folder_path:
                return json.dumps({
                    'success': True,
                    'data': folder_path
                }, ensure_ascii=False)
            else:
                return json.dumps({
                    'success': False,
                    'error': '未選擇資料夾'
                }, ensure_ascii=False)
                
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'瀏覽資料夾失敗: {str(e)}'
            }, ensure_ascii=False)
        
        


class WebViewWrapper:
    """WebView 包裝類，提供 run_javascript 方法"""
    
    def __init__(self, web_view):
        self.web_view = web_view
    
    def run_javascript(self, js_code):
        """執行 JavaScript 代碼"""
        try:
            print(f"[CRASH_DEBUG] WebViewWrapper 開始執行 JavaScript: {datetime.now()}")
            print(f"[CRASH_DEBUG] JavaScript 代碼長度: {len(js_code)}")
            self.web_view.page().runJavaScript(js_code)
            print(f"[CRASH_DEBUG] WebViewWrapper JavaScript 執行完成: {datetime.now()}")
        except Exception as e:
            print(f"[CRASH_DEBUG] WebViewWrapper 執行 JavaScript 失敗: {e}")
            import traceback
            print(f"[CRASH_DEBUG] WebViewWrapper JavaScript 執行錯誤詳情:\n{traceback.format_exc()}")


class MainWindow(QMainWindow):
    """主視窗"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.bridge = None  # 先設為 None，在 init_ui 中創建
        self.init_ui()
        # 先隱藏主視窗，等初始化完成後再顯示
        self.hide()
    
    def init_ui(self):
        """初始化使用者介面"""
        self.setWindowTitle('靶材印字檢測OCR3.0')
        self.setGeometry(100, 100, 1400, 900)
        
        # 建立中央元件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 建立佈局
        layout = QVBoxLayout(central_widget)
        
        # 建立 WebEngine 視圖
        self.web_view = QWebEngineView()
        # 隱藏右鍵選單
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)
        layout.addWidget(self.web_view)
        
        # 建立 WebChannel
        self.channel = QWebChannel()
        self.web_view.page().setWebChannel(self.channel)
        
        # 監控 WebChannel 狀態
        def monitor_webchannel():
            try:
                print(f"[CRASH_DEBUG] WebChannel 狀態檢查: {datetime.now()}")
                # 檢查 WebChannel 是否正常
                if hasattr(self.channel, 'blockSignals'):
                    print(f"[CRASH_DEBUG] WebChannel 正常")
                else:
                    print(f"[CRASH_DEBUG] WebChannel 異常")
            except Exception as e:
                print(f"[CRASH_DEBUG] WebChannel 監控失敗: {e}")
        
        # 每5秒檢查一次 WebChannel 狀態
        # self.webchannel_timer = QTimer()
        # self.webchannel_timer.timeout.connect(monitor_webchannel)
        # self.webchannel_timer.start(5000)
        
        # 創建橋接物件，傳遞一個包裝物件，提供 run_javascript 方法
        web_wrapper = WebViewWrapper(self.web_view)
        print(f"創建 MainBridge，main_window: {self}")
        self.bridge = MainBridge(self.config_manager, web_wrapper, self)
        
        # 註冊橋接物件
        self.channel.registerObject('api', self.bridge)
        
        # 載入 HTML 檔案
        html_path = os.path.join(os.path.dirname(__file__), 'html', 'frmmain.html')
        if os.path.exists(html_path):
            self.web_view.load(QUrl.fromLocalFile(html_path))
        else:
            self.web_view.setHtml("""
                <html>
                <body>
                    <h1>錯誤</h1>
                    <p>找不到 frmmain.html 檔案</p>
                    <p>請確認檔案位於 html/frmmain.html</p>
                </body>
                </html>
            """)
        
        # 設定視窗圖示
        try:
            self.setWindowIcon(QIcon('icon.ico'))
        except:
            pass
        
        # 設定定時器更新時間
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 每秒更新一次
    
    def update_time(self):
        """更新時間"""
        try:
            current_time = datetime.now().strftime('%H:%M:%S')
            current_date = datetime.now().strftime('%Y/%m/%d')
            
            # 透過 JavaScript 更新時間，添加元素存在檢查
            js_code = f"""
            (function() {{
                var timeElement = document.getElementById('currentTime');
                var dateElement = document.getElementById('currentDate');
                if (timeElement) timeElement.textContent = '{current_time}';
                if (dateElement) dateElement.textContent = '{current_date}';
            }})();
            """
            self.web_view.page().runJavaScript(js_code)
        except Exception as e:
            print(f"更新時間失敗: {e}")
    
    def run_javascript(self, js_code):
        """執行 JavaScript 代碼"""
        try:
            print(f"[CRASH_DEBUG] MainWindow 開始執行 JavaScript: {datetime.now()}")
            print(f"[CRASH_DEBUG] JavaScript 代碼長度: {len(js_code)}")
            self.web_view.page().runJavaScript(js_code)
            print(f"[CRASH_DEBUG] MainWindow JavaScript 執行完成: {datetime.now()}")
        except Exception as e:
            print(f"[CRASH_DEBUG] MainWindow 執行 JavaScript 失敗: {e}")
            import traceback
            print(f"[CRASH_DEBUG] MainWindow JavaScript 執行錯誤詳情:\n{traceback.format_exc()}")
    
    def closeEvent(self, event):
        """關閉視窗事件"""
        try:
            if hasattr(self.bridge, 'db_manager') and self.bridge.db_manager:
                self.bridge.db_manager.close()
        except:
            pass
        event.accept()


def main():
    """主程式"""
    import traceback
    import logging
    
    # 設定詳細的日誌記錄
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('debug.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    try:
        print("程式開始執行...")
        logging.info("程式開始執行...")
        
        # 建立應用程式
        app = QApplication(sys.argv)
        logging.info("QApplication 建立成功")
        
        # 建立主視窗（會自動處理顯示邏輯）
        window = MainWindow()
        logging.info("MainWindow 建立成功")
        
        # 執行應用程式
        logging.info("開始執行應用程式主循環...")
        sys.exit(app.exec_())
        
    except Exception as e:
        error_msg = f"程式執行失敗: {e}"
        traceback_msg = traceback.format_exc()
        
        print(f"嚴重錯誤: {error_msg}")
        print(f"詳細錯誤: {traceback_msg}")
        logging.error(f"嚴重錯誤: {error_msg}")
        logging.error(f"詳細錯誤: {traceback_msg}")
        
        # 寫入錯誤檔案
        with open('crash_report.txt', 'w', encoding='utf-8') as f:
            f.write(f"程式崩潰報告\n")
            f.write(f"時間: {datetime.now()}\n")
            f.write(f"錯誤訊息: {error_msg}\n")
            f.write(f"詳細錯誤:\n{traceback_msg}\n")
        
        QMessageBox.critical(None, "錯誤", f"程式執行失敗: {e}\n詳細錯誤已記錄到 crash_report.txt")


if __name__ == "__main__":
    main()
