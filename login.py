import sys
import os
import json
import time
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from database_manager import DatabaseManager

class LoginBridge(QObject):
    """登入橋接類別，處理 Python 和 JavaScript 之間的通信"""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
    
    @pyqtSlot(str, result=str)
    def login(self, login_data_json: str) -> str:
        """登入驗證"""
        try:
            if not self.db_manager:
                result = {
                    'success': False,
                    'error': '資料庫連接不可用'
                }
                print(f"登入失敗: {result}")
                # 觸發認證失敗事件
                self.parent().trigger_authentication_failed('', '資料庫連接不可用')
                return json.dumps(result, ensure_ascii=False)
            
            login_data = json.loads(login_data_json)
            username = login_data.get('username', '').strip()
            password = login_data.get('password', '').strip()
            
            print(f"嘗試登入: username={username}, password={'*' * len(password)}")
            
            if not username or not password:
                result = {
                    'success': False,
                    'error': '請輸入帳號和密碼'
                }
                print(f"登入失敗: {result}")
                # 觸發認證失敗事件
                self.parent().trigger_authentication_failed(username, '請輸入帳號和密碼')
                return json.dumps(result, ensure_ascii=False)
            
            # 查詢資料庫驗證帳號密碼
            account = self.db_manager.get_account_by_id(username)
            
            if not account:
                result = {
                    'success': False,
                    'error': '帳號不存在'
                }
                print(f"登入失敗: {result}")
                # 觸發認證失敗事件
                self.parent().trigger_authentication_failed(username, '帳號不存在')
                return json.dumps(result, ensure_ascii=False)
            
            # 驗證密碼
            if account.get('Password') != password:
                result = {
                    'success': False,
                    'error': '密碼錯誤'
                }
                print(f"登入失敗: {result}")
                # 觸發認證失敗事件
                self.parent().trigger_authentication_failed(username, '密碼錯誤')
                return json.dumps(result, ensure_ascii=False)
            
            # 登入成功，返回帳號資訊
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
            self.parent().trigger_user_logged_in(user_data)
            
            # 觸發會話開始事件
            session_data = {
                'session_id': user_data['session_id'],
                'user_id': user_data['account_id'],
                'username': user_data['username'],
                'start_time': user_data['login_time'],
                'is_admin': user_data['is_admin']
            }
            self.parent().trigger_session_started(session_data)
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            result = {
                'success': False,
                'error': f'登入失敗: {str(e)}'
            }
            print(f"登入異常: {result}")
            # 觸發認證失敗事件
            self.parent().trigger_authentication_failed(username if 'username' in locals() else '', str(e))
            return json.dumps(result, ensure_ascii=False)
    
    @pyqtSlot(result=str)
    def get_login_status(self) -> str:
        """取得登入狀態"""
        try:
            return json.dumps({
                'success': True,
                'data': {
                    'status': 'ready'
                }
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(result=str)
    def close_window(self) -> str:
        """關閉登入視窗"""
        try:
            print("嘗試關閉登入視窗...")
            # 關閉視窗
            self.parent().close()
            print("視窗已關閉")
            return json.dumps({
                'success': True,
                'message': '視窗已關閉'
            }, ensure_ascii=False)
        except Exception as e:
            print(f"關閉視窗失敗: {e}")
            return json.dumps({
                'success': False,
                'error': f'關閉視窗失敗: {str(e)}'
            }, ensure_ascii=False)


class LoginWindow(QMainWindow):
    """登入視窗"""
    
    # 定義信號
    window_closed = pyqtSignal()
    login_success = pyqtSignal(dict)  # 登入成功信號，傳遞帳號資訊
    
    # 新增事件信號
    user_logged_in = pyqtSignal(dict)  # 用戶登入事件
    user_logout = pyqtSignal(dict)     # 用戶登出事件
    authentication_failed = pyqtSignal(str, str)  # 認證失敗事件 (username, error_message)
    session_started = pyqtSignal(dict)  # 會話開始事件
    session_ended = pyqtSignal(dict)    # 會話結束事件
    window_state_changed = pyqtSignal(str, dict)  # 視窗狀態改變事件 (state, info)
    data_transfer_requested = pyqtSignal(str, dict)  # 資料傳輸請求事件 (type, data)
    
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        if not self.db_manager:
            raise ValueError("db_manager 不能為 None")
        
        # 事件訂閱者列表
        self.event_subscribers = {
            'user_logged_in': [],
            'user_logout': [],
            'authentication_failed': [],
            'session_started': [],
            'session_ended': [],
            'window_state_changed': [],
            'data_transfer_requested': []
        }
        
        self.init_ui()
    
    def init_ui(self):
        """初始化使用者介面"""
        self.setWindowTitle('登入系統')
        self.setGeometry(100, 100, 800, 600)
        self.setFixedSize(800, 600)  # 固定視窗大小
        
        # 建立中央元件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 建立佈局
        layout = QVBoxLayout(central_widget)
        
        # 建立 WebEngine 視圖
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)
        
        # 建立 WebChannel
        self.channel = QWebChannel()
        self.web_view.page().setWebChannel(self.channel)
        
        # 建立橋接物件
        self.bridge = LoginBridge(self.db_manager)
        self.bridge.setParent(self)  # 設置父物件
        self.channel.registerObject('loginBridge', self.bridge)
        
        # 載入 HTML 檔案
        html_path = os.path.join(os.path.dirname(__file__), 'html', 'login.html')
        if os.path.exists(html_path):
            # 先載入 QWebChannel JavaScript 庫
            self.web_view.page().loadFinished.connect(self.on_load_finished)
            # 載入 HTML 檔案
            self.web_view.load(QUrl.fromLocalFile(html_path))
        else:
            # 如果 HTML 檔案不存在，顯示錯誤訊息
            self.web_view.setHtml("""
                <html>
                <head>
                    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
                </head>
                <body>
                    <h1>錯誤</h1>
                    <p>找不到 login.html 檔案</p>
                    <p>請確認檔案位於 html/login.html</p>
                </body>
                </html>
            """)
        
        # 設定視窗圖示
        try:
            self.setWindowIcon(QIcon('icon.ico'))
        except:
            pass
    
    def on_load_finished(self, success):
        """頁面載入完成後的回調"""
        if success:
            # 頁面載入完成後，注入 QWebChannel JavaScript 代碼
            self.inject_qwebchannel()
    
    def inject_qwebchannel(self):
        """注入 QWebChannel JavaScript 代碼"""
        try:
            # 注入 QWebChannel 初始化代碼
            js_code = """
            if (typeof QWebChannel === 'undefined') {
                console.log('QWebChannel 未定義，創建模擬版本');
                window.QWebChannel = function(transport, callback) {
                    console.log('模擬 QWebChannel 初始化');
                    setTimeout(function() {
                        if (callback) {
                            callback({
                                objects: {
                                    loginBridge: {
                                        login: function(data) {
                                            console.log('模擬登入調用:', data);
                                            return JSON.stringify({
                                                success: false,
                                                error: 'QWebChannel 未正確載入'
                                            });
                                        },
                                        get_login_status: function() {
                                            return JSON.stringify({
                                                success: false,
                                                error: 'QWebChannel 未正確載入'
                                            });
                                        }
                                    }
                                }
                            });
                        }
                    }, 100);
                };
            }
            """
            self.web_view.page().runJavaScript(js_code)
        except Exception as e:
            print(f"注入 QWebChannel 失敗: {e}")
    
    def closeEvent(self, event):
        """關閉視窗事件"""
        # 發送視窗關閉信號
        self.window_closed.emit()
        event.accept()
    
    def close_window(self):
        """手動關閉視窗"""
        self.close()
    
    def hide_window(self):
        """隱藏視窗"""
        self.hide()
    
    def show_window(self):
        """顯示視窗"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def is_visible(self):
        """檢查視窗是否可見"""
        return self.isVisible()
    
    def get_window_info(self):
        """取得視窗資訊"""
        return {
            'visible': self.isVisible(),
            'geometry': {
                'x': self.geometry().x(),
                'y': self.geometry().y(),
                'width': self.geometry().width(),
                'height': self.geometry().height()
            }
        }
    
    def set_window_geometry(self, x, y, width, height):
        """設定視窗幾何形狀"""
        self.setGeometry(x, y, width, height)
    
    def center_on_screen(self):
        """將視窗置中於螢幕"""
        screen = QApplication.desktop().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def maximize_window(self):
        """最大化視窗"""
        self.showMaximized()
    
    def minimize_window(self):
        """最小化視窗"""
        self.showMinimized()
    
    def restore_window(self):
        """還原視窗"""
        self.showNormal()
    
    def get_window_state(self):
        """取得視窗狀態"""
        if self.isMaximized():
            return 'maximized'
        elif self.isMinimized():
            return 'minimized'
        else:
            return 'normal'
    
    def get_window_title(self):
        """取得視窗標題"""
        return self.windowTitle()
    
    def set_window_title(self, title):
        """設定視窗標題"""
        self.setWindowTitle(title)
    
    # ==================== 事件管理方法 ====================
    
    def subscribe_to_event(self, event_type, callback):
        """訂閱事件
        
        Args:
            event_type (str): 事件類型
            callback (callable): 回調函數
        """
        if event_type in self.event_subscribers:
            if callback not in self.event_subscribers[event_type]:
                self.event_subscribers[event_type].append(callback)
                print(f"已訂閱事件: {event_type}")
            else:
                print(f"回調函數已存在於事件: {event_type}")
        else:
            print(f"未知的事件類型: {event_type}")
    
    def unsubscribe_from_event(self, event_type, callback):
        """取消訂閱事件
        
        Args:
            event_type (str): 事件類型
            callback (callable): 回調函數
        """
        if event_type in self.event_subscribers:
            if callback in self.event_subscribers[event_type]:
                self.event_subscribers[event_type].remove(callback)
                print(f"已取消訂閱事件: {event_type}")
            else:
                print(f"回調函數不存在於事件: {event_type}")
        else:
            print(f"未知的事件類型: {event_type}")
    
    def emit_event(self, event_type, *args, **kwargs):
        """發送事件給所有訂閱者
        
        Args:
            event_type (str): 事件類型
            *args: 位置參數
            **kwargs: 關鍵字參數
        """
        if event_type in self.event_subscribers:
            print(f"發送事件: {event_type}, 訂閱者數量: {len(self.event_subscribers[event_type])}")
            for callback in self.event_subscribers[event_type]:
                try:
                    if args and kwargs:
                        callback(*args, **kwargs)
                    elif args:
                        callback(*args)
                    elif kwargs:
                        callback(**kwargs)
                    else:
                        callback()
                except Exception as e:
                    print(f"事件回調執行失敗: {e}")
        else:
            print(f"未知的事件類型: {event_type}")
    
    def get_subscriber_count(self, event_type):
        """取得指定事件的訂閱者數量
        
        Args:
            event_type (str): 事件類型
            
        Returns:
            int: 訂閱者數量
        """
        return len(self.event_subscribers.get(event_type, []))
    
    def get_all_event_types(self):
        """取得所有可用的事件類型
        
        Returns:
            list: 事件類型列表
        """
        return list(self.event_subscribers.keys())
    
    def clear_all_subscribers(self):
        """清除所有事件訂閱者"""
        for event_type in self.event_subscribers:
            self.event_subscribers[event_type].clear()
        print("已清除所有事件訂閱者")
    
    def clear_event_subscribers(self, event_type):
        """清除指定事件的所有訂閱者
        
        Args:
            event_type (str): 事件類型
        """
        if event_type in self.event_subscribers:
            self.event_subscribers[event_type].clear()
            print(f"已清除事件 {event_type} 的所有訂閱者")
        else:
            print(f"未知的事件類型: {event_type}")
    
    # ==================== 業務事件觸發方法 ====================
    
    def trigger_user_logged_in(self, user_data):
        """觸發用戶登入事件
        
        Args:
            user_data (dict): 用戶資料
        """
        print(f"觸發用戶登入事件: {user_data}")
        self.emit_event('user_logged_in', user_data)
        # 同時發送 PyQt5 信號
        self.user_logged_in.emit(user_data)
    
    def trigger_authentication_failed(self, username, error_message):
        """觸發認證失敗事件
        
        Args:
            username (str): 用戶名
            error_message (str): 錯誤訊息
        """
        print(f"觸發認證失敗事件: {username}, {error_message}")
        self.emit_event('authentication_failed', username, error_message)
        # 同時發送 PyQt5 信號
        self.authentication_failed.emit(username, error_message)
    
    def trigger_session_started(self, session_data):
        """觸發會話開始事件
        
        Args:
            session_data (dict): 會話資料
        """
        print(f"觸發會話開始事件: {session_data}")
        self.emit_event('session_started', session_data)
        # 同時發送 PyQt5 信號
        self.session_started.emit(session_data)
    
    def trigger_data_transfer(self, data_type, data):
        """觸發資料傳輸事件
        
        Args:
            data_type (str): 資料類型
            data (dict): 資料內容
        """
        print(f"觸發資料傳輸事件: {data_type}, {data}")
        self.emit_event('data_transfer_requested', data_type, data)
        # 同時發送 PyQt5 信號
        self.data_transfer_requested.emit(data_type, data)


def main():
    """測試用主程式"""
    try:
        # 建立應用程式
        app = QApplication(sys.argv)
        
        # 建立模擬的資料庫管理器
        class MockDBManager:
            def get_account_by_username(self, username):
                # 不區分大小寫
                username_lower = username.lower()
                if username_lower == 'admin':
                    return {
                        'Account': 'admin',
                        'Name': '管理員',
                        'Password': 'admin',
                        'IsAdmin': 1
                    }
                elif username_lower == 'user':
                    return {
                        'Account': 'user',
                        'Name': '一般使用者',
                        'Password': 'user',
                        'IsAdmin': 0
                    }
                return None
        
        # 從 config.yaml 讀取資料庫設定
        mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'database': 'ocr_compare', 
            'user': 'root',
            'password': 'Gwgplus24294096',
            'charset': 'utf8mb4'
        }
        
        # 建立資料庫連線字串
        connection_str = f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}?charset={mysql_config['charset']}"
        
        # 建立登入視窗
        db_manager = DatabaseManager(connection_str)
        window = LoginWindow(db_manager)
        window.show()
        
        # 執行應用程式
        sys.exit(app.exec_())
        
    except Exception as e:
        QMessageBox.critical(None, "錯誤", f"程式執行失敗: {e}")


if __name__ == "__main__":
    main()
