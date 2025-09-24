import sys
import json
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
import os
from database_manager import DatabaseManager
from config_manager import ConfigManager



class AccountBridge(QObject):
    """
    帳號管理的橋接類別，處理 Python 和 JavaScript 之間的通信
    """
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        if not self.db_manager:
            raise ValueError("db_manager 不能為 None")
    
    @pyqtSlot(str, result=str)
    def get_accounts(self, params_json: str) -> str:
        """
        取得帳號列表
        
        Args:
            params_json: JSON 格式的參數 (limit, offset)
            
        Returns:
            JSON 格式的帳號列表
        """
        try:
            if not self.db_manager:
                return json.dumps({
                    'success': False,
                    'error': '資料庫管理器不可用'
                }, ensure_ascii=False)
            
            params = json.loads(params_json)
            limit = params.get('limit', 100)
            offset = params.get('offset', 0)
            
            accounts = self.db_manager.get_accounts(limit=limit, offset=offset)
            
            result = {
                'success': True,
                'data': accounts,
                'total': len(accounts)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def get_account_by_id(self, account_id: str) -> str:
        """
        根據 ID 取得帳號
        
        Args:
            account_id: 帳號 ID
            
        Returns:
            JSON 格式的帳號資料
        """
        try:
            if not self.db_manager:
                return json.dumps({
                    'success': False,
                    'error': '資料庫管理器不可用'
                }, ensure_ascii=False)
            
            account = self.db_manager.get_account_by_id(account_id)
            
            if account:
                result = {
                    'success': True,
                    'data': account
                }
            else:
                result = {
                    'success': False,
                    'error': '帳號不存在'
                }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def create_account(self, account_data_json: str) -> str:
        """
        新增帳號
        
        Args:
            account_data_json: JSON 格式的帳號資料
            
        Returns:
            JSON 格式的結果
        """
        try:
            if not self.db_manager:
                return json.dumps({
                    'success': False,
                    'error': '資料庫管理器不可用'
                }, ensure_ascii=False)
            
            account_data = json.loads(account_data_json)
            
            # 驗證必填欄位
            required_fields = ['Account', 'Name', 'Password']
            for field in required_fields:
                if not account_data.get(field):
                    return json.dumps({
                        'success': False,
                        'error': f'必填欄位 {field} 不能為空'
                    }, ensure_ascii=False)
            
            # 檢查帳號是否已存在
            existing_account = self.db_manager.get_account_by_id(account_data['Account'])
            if existing_account:
                return json.dumps({
                    'success': False,
                    'error': '帳號已存在'
                }, ensure_ascii=False)
            
            success = self.db_manager.create_account(account_data)
            
            if success:
                result = {
                    'success': True,
                    'message': '帳號新增成功'
                }
            else:
                result = {
                    'success': False,
                    'error': '帳號新增失敗'
                }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def update_account(self, update_data_json: str) -> str:
        """
        更新帳號
        
        Args:
            update_data_json: JSON 格式的更新資料 (包含 account_id 和更新欄位)
            
        Returns:
            JSON 格式的結果
        """
        try:
            if not self.db_manager:
                return json.dumps({
                    'success': False,
                    'error': '資料庫管理器不可用'
                }, ensure_ascii=False)
            
            update_data = json.loads(update_data_json)
            account_id = update_data.get('account_id')
            
            if not account_id:
                return json.dumps({
                    'success': False,
                    'error': '帳號 ID 不能為空'
                }, ensure_ascii=False)
            
            # 移除 account_id，只保留要更新的欄位
            account_data = {k: v for k, v in update_data.items() if k != 'account_id'}
            
            # 如果密碼欄位為空字串，則移除密碼欄位（不更新密碼）
            if 'Password' in account_data and not account_data['Password']:
                del account_data['Password']
            
            success = self.db_manager.update_account(account_id, account_data)
            
            if success:
                result = {
                    'success': True,
                    'message': '帳號更新成功'
                }
            else:
                result = {
                    'success': False,
                    'error': '帳號更新失敗'
                }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def delete_account(self, account_id: str) -> str:
        """
        刪除帳號
        
        Args:
            account_id: 帳號 ID
            
        Returns:
            JSON 格式的結果
        """
        try:
            if not self.db_manager:
                return json.dumps({
                    'success': False,
                    'error': '資料庫管理器不可用'
                }, ensure_ascii=False)
            
            success = self.db_manager.delete_account(account_id)
            
            if success:
                result = {
                    'success': True,
                    'message': '帳號刪除成功'
                }
            else:
                result = {
                    'success': False,
                    'error': '帳號刪除失敗'
                }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)
    
    @pyqtSlot(str, result=str)
    def search_accounts(self, params_json: str) -> str:
        """
        搜尋帳號
        
        Args:
            params_json: JSON 格式的搜尋參數 (keyword, limit)
            
        Returns:
            JSON 格式的搜尋結果
        """
        try:
            if not self.db_manager:
                return json.dumps({
                    'success': False,
                    'error': '資料庫管理器不可用'
                }, ensure_ascii=False)
            
            params = json.loads(params_json)
            keyword = params.get('keyword', '')
            limit = params.get('limit', 100)
            
            if not keyword:
                return json.dumps({
                    'success': False,
                    'error': '搜尋關鍵字不能為空'
                }, ensure_ascii=False)
            
            accounts = self.db_manager.search_accounts(keyword, limit=limit)
            
            result = {
                'success': True,
                'data': accounts,
                'total': len(accounts)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': str(e)
            }, ensure_ascii=False)


class AccountManagerWindow(QMainWindow):
    """
    帳號管理主視窗
    """
    
    # 定義信號
    window_closed = pyqtSignal()
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        if not self.db_manager:
            raise ValueError("db_manager 不能為 None")
        self.init_ui()
    
    def init_ui(self):
        """初始化使用者介面"""
        self.setWindowTitle('帳號管理系統')
        self.setGeometry(100, 100, 1200, 800)
        
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
        self.bridge = AccountBridge(self.db_manager)
        self.channel.registerObject('accountBridge', self.bridge)
        
        # 載入 HTML 檔案
        html_path = os.path.join(os.path.dirname(__file__), 'html', 'account.html')
        if os.path.exists(html_path):
            # 先載入 QWebChannel JavaScript 庫
            self.web_view.page().loadFinished.connect(self.on_load_finished)
            # 載入 HTML 檔案
            self.web_view.load(QUrl.fromLocalFile(html_path))
        else:
            # 如果 HTML 檔案不存在，顯示錯誤訊息
            self.web_view.setHtml("""
                <html>
                <body>
                    <h1>錯誤</h1>
                    <p>找不到 account.html 檔案</p>
                    <p>請確認檔案位於 html/account.html</p>
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
        pass
    
    def closeEvent(self, event):
        """關閉視窗事件"""
        # 發送視窗關閉信號
        self.window_closed.emit()
        # 不關閉 db_manager，因為它由主程式管理
        event.accept()
    
    def close_window(self):
        """手動關閉視窗"""
        # 不需要再次發送信號，因為 close() 會觸發 closeEvent
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
    
    def set_window_title(self, title: str):
        """設定視窗標題"""
        self.setWindowTitle(title)


def main():
    """主程式"""
    try:
        # 建立應用程式
        app = QApplication(sys.argv)
        
        # 從 config.yaml 取得 MySQL 設定
        config_manager = ConfigManager()
        mysql_config = config_manager.Config.MySql
        
        # 建立資料庫連線字串
        connection_string = f"mysql+pymysql://{mysql_config.User}:{mysql_config.Password}@{mysql_config.Host}:{mysql_config.Port}/{mysql_config.Database}?charset={mysql_config.Charset}"
        
        # 建立資料庫管理器
        db_manager = DatabaseManager(connection_string)
        
        # 建立主視窗
        window = AccountManagerWindow(db_manager)
        window.setWindowModality(Qt.ApplicationModal)
        window.show()
        
        # 執行應用程式
        sys.exit(app.exec_())
        
    except Exception as e:
        QMessageBox.critical(None, "錯誤", f"程式執行失敗: {e}")


if __name__ == "__main__":
    main()
