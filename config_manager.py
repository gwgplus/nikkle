#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 版本的 ConfigManager，用於讀取 config.yaml 設定檔
"""

import os
import yaml
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MySqlConfig:
    """MySQL 資料庫設定"""
    Host: str = "localhost"
    Port: int = 3306
    Database: str = "ocr_compare"
    User: str = "root"
    Password: str = ""
    Charset: str = "utf8mb4"
    ConnectTimeout: int = 10
    PoolSize: int = 5
    PoolTimeout: int = 30

@dataclass
class UiConfig:
    """UI 介面設定"""
    Language: str = "zh_TW"
    Theme: str = "default"
    FontSize: str = "normal"
    FullScreen: bool = False
    AutoLogout: int = 300
    TableRowsPerPage: int = 10

@dataclass
class PathsConfig:
    """路徑設定"""
    OCR_Image_Save_Path: str = "E:\\OCR_Images\\Source"
    DB_Image_Save_Path: str = "E:\\OCR_Images\\Database"
    Export_Default_Path: str = "E:\\OCR_Export"
    OCR_Backup_Path: str = "E:\\OCR_Backup"

@dataclass
class CognexConfig:
    """PV200 設備設定"""
    IP: str = "127.0.0.1"
    Port: int = 502
    Port_Cmd: int = 503

@dataclass
class ImageProcessingConfig:
    """影像處理設定"""
    Offset_X: int = 0
    Offset_Y: int = 0
    Scale: float = 1.0

@dataclass
class TimingConfig:
    """時間設定"""
    OCR_Retry_Time: int = 3
    Pic_Wait_Time: int = 2000

@dataclass
class SystemConfig:
    """系統設定"""
    Debug_Mode: bool = False
    Log_Level: str = "INFO"
    Log_File_Path: str = "C:\\OCR_Logs\\ocr_compare.log"

@dataclass
class SecurityConfig:
    """安全設定"""
    Enable_Password_Validation: bool = True
    Min_Password_Length: int = 6
    Password_Complexity: dict = None
    
    def __post_init__(self):
        if self.Password_Complexity is None:
            self.Password_Complexity = {
                'require_uppercase': True,
                'require_lowercase': True,
                'require_numbers': True,
                'require_special_chars': False
            }

@dataclass
class BackupConfig:
    """備份設定"""
    Enable_Auto_Backup: bool = True
    Backup_Interval_Hours: int = 24
    Backup_Retention_Days: int = 30

@dataclass
class ExportConfig:
    """匯出設定"""
    Default_Format: str = "EXCEL"
    Include_Image_Path: bool = True
    Include_Timestamp: bool = True

@dataclass
class NotificationsConfig:
    """通知設定"""
    Enable_Error_Notifications: bool = True
    Enable_Success_Notifications: bool = False
    Notification_Method: str = "NONE"
    Email: dict = None
    
    def __post_init__(self):
        if self.Email is None:
            self.Email = {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_address': '',
                'to_addresses': []
            }

@dataclass
class PerformanceConfig:
    """效能設定"""
    Max_Concurrent_Processes: int = 4
    Memory_Limit_MB: int = 1024
    Image_Cache_Size_MB: int = 100

@dataclass
class DevelopmentConfig:
    """開發者設定"""
    Verbose_Logging: bool = False
    Enable_Performance_Monitoring: bool = False
    Test_Mode: bool = False

@dataclass
class SettingsConfig:
    """系統設定"""
    Paths: PathsConfig = None
    Cognex: CognexConfig = None
    Image_Processing: ImageProcessingConfig = None
    Timing: TimingConfig = None
    System: SystemConfig = None
    Security: SecurityConfig = None
    Backup: BackupConfig = None
    Export: ExportConfig = None
    Notifications: NotificationsConfig = None
    Performance: PerformanceConfig = None
    Development: DevelopmentConfig = None
    
    def __post_init__(self):
        if self.Paths is None:
            self.Paths = PathsConfig()
        if self.Cognex is None:
            self.Cognex = CognexConfig()
        if self.Image_Processing is None:
            self.Image_Processing = ImageProcessingConfig()
        if self.Timing is None:
            self.Timing = TimingConfig()
        if self.System is None:
            self.System = SystemConfig()
        if self.Security is None:
            self.Security = SecurityConfig()
        if self.Backup is None:
            self.Backup = BackupConfig()
        if self.Export is None:
            self.Export = ExportConfig()
        if self.Notifications is None:
            self.Notifications = NotificationsConfig()
        if self.Performance is None:
            self.Performance = PerformanceConfig()
        if self.Development is None:
            self.Development = DevelopmentConfig()

@dataclass
class AppConfig:
    """應用程式設定"""
    MySql: MySqlConfig = None
    Ui: UiConfig = None
    Settings: SettingsConfig = None
    
    def __post_init__(self):
        if self.MySql is None:
            self.MySql = MySqlConfig()
        if self.Ui is None:
            self.Ui = UiConfig()
        if self.Settings is None:
            self.Settings = SettingsConfig()

class ConfigManager:
    """設定管理器"""
    
    _instance = None
    _config_file = "config.yaml"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._config = AppConfig()
        self._load_config()
        self._initialized = True
    
    @property
    def Config(self) -> AppConfig:
        """取得設定物件"""
        return self._config
    
    def _load_config(self):
        """載入設定檔"""
        try:
            if not os.path.exists(self._config_file):
                logger.warning(f"設定檔 {self._config_file} 不存在，使用預設設定")
                return
            
            with open(self._config_file, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
            
            if not config_data:
                logger.warning("設定檔為空，使用預設設定")
                return
            
            # 載入 MySQL 設定
            if 'mysql' in config_data:
                mysql_data = config_data['mysql']
                self._config.MySql = MySqlConfig(
                    Host=mysql_data.get('host', 'localhost'),
                    Port=mysql_data.get('port', 3306),
                    Database=mysql_data.get('database', 'ocr_compare'),
                    User=mysql_data.get('user', 'root'),
                    Password=mysql_data.get('password', ''),
                    Charset=mysql_data.get('charset', 'utf8mb4'),
                    ConnectTimeout=mysql_data.get('connect_timeout', 10),
                    PoolSize=mysql_data.get('pool_size', 5),
                    PoolTimeout=mysql_data.get('pool_timeout', 30)
                )
            
            # 載入 UI 設定
            if 'ui' in config_data:
                ui_data = config_data['ui']
                self._config.Ui = UiConfig(
                    Language=ui_data.get('language', 'zh_TW'),
                    Theme=ui_data.get('theme', 'default'),
                    FontSize=ui_data.get('font_size', 'normal'),
                    FullScreen=ui_data.get('full_screen', False),
                    AutoLogout=ui_data.get('auto_logout', 300),
                    TableRowsPerPage=ui_data.get('table_rows_per_page', 10)
                )
            
            # 載入路徑設定
            if 'paths' in config_data:
                paths_data = config_data['paths']
                self._config.Settings.Paths = PathsConfig(
                    OCR_Image_Save_Path=paths_data.get('ocr_image_save_path', 'E:\\OCR_Images\\Source'),
                    DB_Image_Save_Path=paths_data.get('db_image_save_path', 'E:\\OCR_Images\\Database'),
                    Export_Default_Path=paths_data.get('export_default_path', 'E:\\OCR_Export'),
                    OCR_Backup_Path=paths_data.get('ocr_backup_path', 'E:\\OCR_Backup')
                )
            
            # 載入 Cognex 設定
            if 'cognex' in config_data:
                cognex_data = config_data['cognex']
                self._config.Settings.Cognex = CognexConfig(
                    IP=cognex_data.get('ip', '127.0.0.1'),
                    Port=cognex_data.get('port', 502),
                    Port_Cmd=cognex_data.get('port_cmd', 503)
                )
            
            # 載入影像處理設定
            if 'image_processing' in config_data:
                img_data = config_data['image_processing']
                self._config.Settings.Image_Processing = ImageProcessingConfig(
                    Offset_X=img_data.get('offset_x', 0),
                    Offset_Y=img_data.get('offset_y', 0),
                    Scale=img_data.get('scale', 1.0)
                )
            
            # 載入時間設定
            if 'timing' in config_data:
                timing_data = config_data['timing']
                self._config.Settings.Timing = TimingConfig(
                    OCR_Retry_Time=timing_data.get('ocr_retry_time', 3),
                    Pic_Wait_Time=timing_data.get('pic_wait_time', 2000)
                )
            
            # 載入系統設定
            if 'system' in config_data:
                system_data = config_data['system']
                self._config.Settings.System = SystemConfig(
                    Debug_Mode=system_data.get('debug_mode', False),
                    Log_Level=system_data.get('log_level', 'INFO'),
                    Log_File_Path=system_data.get('log_file_path', 'C:\\OCR_Logs\\ocr_compare.log')
                )
            
            # 載入安全設定
            if 'security' in config_data:
                security_data = config_data['security']
                self._config.Settings.Security = SecurityConfig(
                    Enable_Password_Validation=security_data.get('enable_password_validation', True),
                    Min_Password_Length=security_data.get('min_password_length', 6),
                    Password_Complexity=security_data.get('password_complexity', {
                        'require_uppercase': True,
                        'require_lowercase': True,
                        'require_numbers': True,
                        'require_special_chars': False
                    })
                )
            
            # 載入備份設定
            if 'backup' in config_data:
                backup_data = config_data['backup']
                self._config.Settings.Backup = BackupConfig(
                    Enable_Auto_Backup=backup_data.get('enable_auto_backup', True),
                    Backup_Interval_Hours=backup_data.get('backup_interval_hours', 24),
                    Backup_Retention_Days=backup_data.get('backup_retention_days', 30)
                )
            
            # 載入匯出設定
            if 'export' in config_data:
                export_data = config_data['export']
                self._config.Settings.Export = ExportConfig(
                    Default_Format=export_data.get('default_format', 'EXCEL'),
                    Include_Image_Path=export_data.get('include_image_path', True),
                    Include_Timestamp=export_data.get('include_timestamp', True)
                )
            
            # 載入通知設定
            if 'notifications' in config_data:
                notif_data = config_data['notifications']
                self._config.Settings.Notifications = NotificationsConfig(
                    Enable_Error_Notifications=notif_data.get('enable_error_notifications', True),
                    Enable_Success_Notifications=notif_data.get('enable_success_notifications', False),
                    Notification_Method=notif_data.get('notification_method', 'NONE'),
                    Email=notif_data.get('email', {
                        'smtp_server': 'smtp.gmail.com',
                        'smtp_port': 587,
                        'username': '',
                        'password': '',
                        'from_address': '',
                        'to_addresses': []
                    })
                )
            
            # 載入效能設定
            if 'performance' in config_data:
                perf_data = config_data['performance']
                self._config.Settings.Performance = PerformanceConfig(
                    Max_Concurrent_Processes=perf_data.get('max_concurrent_processes', 4),
                    Memory_Limit_MB=perf_data.get('memory_limit_mb', 1024),
                    Image_Cache_Size_MB=perf_data.get('image_cache_size_mb', 100)
                )
            
            # 載入開發者設定
            if 'development' in config_data:
                dev_data = config_data['development']
                self._config.Settings.Development = DevelopmentConfig(
                    Verbose_Logging=dev_data.get('verbose_logging', False),
                    Enable_Performance_Monitoring=dev_data.get('enable_performance_monitoring', False),
                    Test_Mode=dev_data.get('test_mode', False)
                )
            
            logger.info("設定檔載入成功")
            
        except Exception as e:
            logger.error(f"載入設定檔失敗: {e}")
            logger.info("使用預設設定")
    
    def reload_config(self):
        """重新載入設定檔"""
        logger.info("重新載入設定檔")
        self._config = AppConfig()
        self._load_config()
    
    def save_config(self):
        """儲存設定到檔案"""
        try:
            config_data = {
                'mysql': {
                    'host': self._config.MySql.Host,
                    'port': self._config.MySql.Port,
                    'database': self._config.MySql.Database,
                    'user': self._config.MySql.User,
                    'password': self._config.MySql.Password,
                    'charset': self._config.MySql.Charset,
                    'connect_timeout': self._config.MySql.ConnectTimeout,
                    'pool_size': self._config.MySql.PoolSize,
                    'pool_timeout': self._config.MySql.PoolTimeout
                },
                'ui': {
                    'language': self._config.Ui.Language,
                    'theme': self._config.Ui.Theme,
                    'font_size': self._config.Ui.FontSize,
                    'full_screen': self._config.Ui.FullScreen,
                    'auto_logout': self._config.Ui.AutoLogout,
                    'table_rows_per_page': self._config.Ui.TableRowsPerPage
                },
                'paths': {
                    'ocr_image_save_path': self._config.Settings.Paths.OCR_Image_Save_Path,
                    'db_image_save_path': self._config.Settings.Paths.DB_Image_Save_Path,
                    'export_default_path': self._config.Settings.Paths.Export_Default_Path,
                    'ocr_backup_path': self._config.Settings.Paths.OCR_Backup_Path
                },
                'cognex': {
                    'ip': self._config.Settings.Cognex.IP,
                    'port': self._config.Settings.Cognex.Port,
                    'port_cmd': self._config.Settings.Cognex.Port_Cmd
                },
                'image_processing': {
                    'offset_x': self._config.Settings.Image_Processing.Offset_X,
                    'offset_y': self._config.Settings.Image_Processing.Offset_Y,
                    'scale': self._config.Settings.Image_Processing.Scale
                },
                'timing': {
                    'ocr_retry_time': self._config.Settings.Timing.OCR_Retry_Time,
                    'pic_wait_time': self._config.Settings.Timing.Pic_Wait_Time
                },
                'system': {
                    'debug_mode': self._config.Settings.System.Debug_Mode,
                    'log_level': self._config.Settings.System.Log_Level,
                    'log_file_path': self._config.Settings.System.Log_File_Path
                },
                'security': {
                    'enable_password_validation': self._config.Settings.Security.Enable_Password_Validation,
                    'min_password_length': self._config.Settings.Security.Min_Password_Length,
                    'password_complexity': self._config.Settings.Security.Password_Complexity
                },
                'backup': {
                    'enable_auto_backup': self._config.Settings.Backup.Enable_Auto_Backup,
                    'backup_interval_hours': self._config.Settings.Backup.Backup_Interval_Hours,
                    'backup_retention_days': self._config.Settings.Backup.Backup_Retention_Days
                },
                'export': {
                    'default_format': self._config.Settings.Export.Default_Format,
                    'include_image_path': self._config.Settings.Export.Include_Image_Path,
                    'include_timestamp': self._config.Settings.Export.Include_Timestamp
                },
                'notifications': {
                    'enable_error_notifications': self._config.Settings.Notifications.Enable_Error_Notifications,
                    'enable_success_notifications': self._config.Settings.Notifications.Enable_Success_Notifications,
                    'notification_method': self._config.Settings.Notifications.Notification_Method,
                    'email': self._config.Settings.Notifications.Email
                },
                'performance': {
                    'max_concurrent_processes': self._config.Settings.Performance.Max_Concurrent_Processes,
                    'memory_limit_mb': self._config.Settings.Performance.Memory_Limit_MB,
                    'image_cache_size_mb': self._config.Settings.Performance.Image_Cache_Size_MB
                },
                'development': {
                    'verbose_logging': self._config.Settings.Development.Verbose_Logging,
                    'enable_performance_monitoring': self._config.Settings.Development.Enable_Performance_Monitoring,
                    'test_mode': self._config.Settings.Development.Test_Mode
                }
            }
            
            with open(self._config_file, 'w', encoding='utf-8') as file:
                yaml.dump(config_data, file, default_flow_style=False, allow_unicode=True)
            
            logger.info("設定檔儲存成功")
            
        except Exception as e:
            logger.error(f"儲存設定檔失敗: {e}")

# 全域實例
Instance = ConfigManager()

if __name__ == "__main__":
    # 測試 ConfigManager
    logging.basicConfig(level=logging.INFO)
    
    config_manager = ConfigManager()
    config = config_manager.Config
    
    print("=== MySQL 設定 ===")
    print(f"主機: {config.MySql.Host}")
    print(f"埠號: {config.MySql.Port}")
    print(f"資料庫: {config.MySql.Database}")
    print(f"使用者: {config.MySql.User}")
    print(f"密碼: {'*' * len(config.MySql.Password) if config.MySql.Password else '未設定'}")
    print(f"字元編碼: {config.MySql.Charset}")
    
    print("\n=== UI 設定 ===")
    print(f"語言: {config.Ui.Language}")
    print(f"主題: {config.Ui.Theme}")
    print(f"字體大小: {config.Ui.FontSize}")
    print(f"全螢幕: {config.Ui.FullScreen}")
    print(f"自動登出: {config.Ui.AutoLogout} 秒")
    print(f"表格每頁筆數: {config.Ui.TableRowsPerPage}")
    
    print("\n=== 路徑設定 ===")
    print(f"OCR 圖片來源路徑: {config.Settings.Paths.OCR_Image_Save_Path}")
    print(f"資料庫圖片儲存路徑: {config.Settings.Paths.DB_Image_Save_Path}")
    print(f"匯出預設路徑: {config.Settings.Paths.Export_Default_Path}")
    print(f"OCR 備份路徑: {config.Settings.Paths.OCR_Backup_Path}")
    
    print("\n=== Cognex 設定 ===")
    print(f"IP 位址: {config.Settings.Cognex.IP}")
    print(f"通訊埠: {config.Settings.Cognex.Port}")
    print(f"命令埠: {config.Settings.Cognex.Port_Cmd}")
    
    print("\n=== 影像處理設定 ===")
    print(f"偏移量 X: {config.Settings.Image_Processing.Offset_X}")
    print(f"偏移量 Y: {config.Settings.Image_Processing.Offset_Y}")
    print(f"放大比例: {config.Settings.Image_Processing.Scale}")
    
    print("\n=== 時間設定 ===")
    print(f"OCR 重試次數: {config.Settings.Timing.OCR_Retry_Time}")
    print(f"圖片檢查等待時間: {config.Settings.Timing.Pic_Wait_Time} 毫秒")
    
    print("\n=== 系統設定 ===")
    print(f"除錯模式: {config.Settings.System.Debug_Mode}")
    print(f"日誌等級: {config.Settings.System.Log_Level}")
    print(f"日誌檔案路徑: {config.Settings.System.Log_File_Path}")
    
    print("\n=== 安全設定 ===")
    print(f"啟用密碼驗證: {config.Settings.Security.Enable_Password_Validation}")
    print(f"密碼最小長度: {config.Settings.Security.Min_Password_Length}")
    print(f"密碼複雜度要求: {config.Settings.Security.Password_Complexity}")
    
    print("\n=== 備份設定 ===")
    print(f"啟用自動備份: {config.Settings.Backup.Enable_Auto_Backup}")
    print(f"備份頻率: {config.Settings.Backup.Backup_Interval_Hours} 小時")
    print(f"保留備份天數: {config.Settings.Backup.Backup_Retention_Days}")
    
    print("\n=== 匯出設定 ===")
    print(f"預設匯出格式: {config.Settings.Export.Default_Format}")
    print(f"包含圖片路徑: {config.Settings.Export.Include_Image_Path}")
    print(f"包含時間戳記: {config.Settings.Export.Include_Timestamp}")
    
    print("\n=== 通知設定 ===")
    print(f"啟用錯誤通知: {config.Settings.Notifications.Enable_Error_Notifications}")
    print(f"啟用成功通知: {config.Settings.Notifications.Enable_Success_Notifications}")
    print(f"通知方式: {config.Settings.Notifications.Notification_Method}")
    
    print("\n=== 效能設定 ===")
    print(f"最大並行處理數: {config.Settings.Performance.Max_Concurrent_Processes}")
    print(f"記憶體使用限制: {config.Settings.Performance.Memory_Limit_MB} MB")
    print(f"圖片快取大小: {config.Settings.Performance.Image_Cache_Size_MB} MB")
    
    print("\n=== 開發者設定 ===")
    print(f"詳細日誌: {config.Settings.Development.Verbose_Logging}")
    print(f"效能監控: {config.Settings.Development.Enable_Performance_Monitoring}")
    print(f"測試模式: {config.Settings.Development.Test_Mode}")
