from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import datetime
import logging
from models import Base, Account, Ocrlog

class DatabaseManager:
    """
    資料庫管理類別，提供 Account 和 Ocrlog 表格的 CRUD 操作
    """
    
    def __init__(self, connection_string: str):
        """
        初始化資料庫管理器
        
        Args:
            connection_string: 資料庫連線字串
        """
        self.connection_string = connection_string
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
        
    def _setup_database(self):
        """設定資料庫連線和建立表格"""
        try:
            self.engine = create_engine(self.connection_string, echo=False)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # 建立所有表格
            Base.metadata.create_all(bind=self.engine)
            logging.info("資料庫連線建立成功")
            
        except Exception as e:
            logging.error(f"資料庫連線失敗: {e}")
            raise
    
    def get_session(self) -> Session:
        """取得資料庫會話"""
        return self.SessionLocal()
    
    # =====================================================
    # Account 表格操作
    # =====================================================
    
    def get_accounts(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        查詢帳戶列表
        
        Args:
            limit: 限制回傳筆數
            offset: 偏移量
            
        Returns:
            帳戶列表
        """
        try:
            with self.get_session() as session:
                accounts = session.query(Account).limit(limit).offset(offset).all()
                return [self._account_to_dict(account) for account in accounts]
        except SQLAlchemyError as e:
            logging.error(f"查詢帳戶列表失敗: {e}")
            return []
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        根據帳戶ID查詢帳戶
        
        Args:
            account_id: 帳戶ID
            
        Returns:
            帳戶資料或 None
        """
        try:
            with self.get_session() as session:
                account = session.query(Account).filter(Account.Account == account_id).first()
                return self._account_to_dict(account) if account else None
        except SQLAlchemyError as e:
            logging.error(f"查詢帳戶失敗: {e}")
            return None
    
    def create_account(self, account_data: Dict[str, Any]) -> bool:
        """
        新增帳戶
        
        Args:
            account_data: 帳戶資料
            
        Returns:
            是否成功
        """
        try:
            with self.get_session() as session:
                account = Account(
                    Account=account_data['Account'],
                    Name=account_data['Name'],
                    Password=account_data['Password'],
                    NeedPassword=account_data.get('NeedPassword', 1),
                    IsAdmin=account_data.get('IsAdmin', 0)
                )
                session.add(account)
                session.commit()
                logging.info(f"新增帳戶成功: {account_data['Account']}")
                return True
        except SQLAlchemyError as e:
            logging.error(f"新增帳戶失敗: {e}")
            return False
    
    def update_account(self, account_id: str, account_data: Dict[str, Any]) -> bool:
        """
        修改帳戶
        
        Args:
            account_id: 帳戶ID
            account_data: 更新的帳戶資料
            
        Returns:
            是否成功
        """
        try:
            with self.get_session() as session:
                account = session.query(Account).filter(Account.Account == account_id).first()
                if not account:
                    logging.warning(f"帳戶不存在: {account_id}")
                    return False
                
                # 更新欄位
                if 'Name' in account_data:
                    account.Name = account_data['Name']
                if 'Password' in account_data:
                    account.Password = account_data['Password']
                if 'NeedPassword' in account_data:
                    account.NeedPassword = account_data['NeedPassword']
                if 'IsAdmin' in account_data:
                    account.IsAdmin = account_data['IsAdmin']
                
                session.commit()
                logging.info(f"修改帳戶成功: {account_id}")
                return True
        except SQLAlchemyError as e:
            logging.error(f"修改帳戶失敗: {e}")
            return False
    
    def delete_account(self, account_id: str) -> bool:
        """
        刪除帳戶
        
        Args:
            account_id: 帳戶ID
            
        Returns:
            是否成功
        """
        try:
            with self.get_session() as session:
                account = session.query(Account).filter(Account.Account == account_id).first()
                if not account:
                    logging.warning(f"帳戶不存在: {account_id}")
                    return False
                
                session.delete(account)
                session.commit()
                logging.info(f"刪除帳戶成功: {account_id}")
                return True
        except SQLAlchemyError as e:
            logging.error(f"刪除帳戶失敗: {e}")
            return False
    
    def search_accounts(self, keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        搜尋帳戶
        
        Args:
            keyword: 搜尋關鍵字
            limit: 限制回傳筆數
            
        Returns:
            符合條件的帳戶列表
        """
        try:
            with self.get_session() as session:
                accounts = session.query(Account).filter(
                    (Account.Account.contains(keyword)) |
                    (Account.Name.contains(keyword))
                ).limit(limit).all()
                return [self._account_to_dict(account) for account in accounts]
        except SQLAlchemyError as e:
            logging.error(f"搜尋帳戶失敗: {e}")
            return []
    
    # =====================================================
    # Ocrlog 表格操作
    # =====================================================
    
    def get_ocr_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        查詢 OCR 記錄列表
        
        Args:
            limit: 限制回傳筆數
            offset: 偏移量
            
        Returns:
            OCR 記錄列表
        """
        try:
            with self.get_session() as session:
                logs = session.query(Ocrlog).order_by(Ocrlog.Time.desc()).limit(limit).offset(offset).all()
                return [self._ocrlog_to_dict(log) for log in logs]
        except SQLAlchemyError as e:
            logging.error(f"查詢 OCR 記錄列表失敗: {e}")
            return []
    
    def get_ocr_log_by_id(self, log_id: int) -> Optional[Dict[str, Any]]:
        """
        根據記錄ID查詢 OCR 記錄
        
        Args:
            log_id: 記錄ID
            
        Returns:
            OCR 記錄資料或 None
        """
        try:
            with self.get_session() as session:
                log = session.query(Ocrlog).filter(Ocrlog.Id == log_id).first()
                return self._ocrlog_to_dict(log) if log else None
        except SQLAlchemyError as e:
            logging.error(f"查詢 OCR 記錄失敗: {e}")
            return None
    
    def create_ocr_log(self, log_data: Dict[str, Any]) -> Optional[int]:
        """
        新增 OCR 記錄
        
        Args:
            log_data: OCR 記錄資料
            
        Returns:
            新增的記錄ID或 None
        """
        try:
            with self.get_session() as session:
                log = Ocrlog(
                    Account_=log_data['Account'],
                    Time=log_data.get('Time', datetime.datetime.now()),
                    Source=log_data['Source'],
                    OCRResult=log_data['OCRResult'],
                    OK=log_data['OK'],
                    Image=log_data['Image'],
                    Manual=log_data['Manual'],
                    Judgment=log_data['Judgment'],
                    KeyInResult=log_data.get('KeyInResult'),
                    Processor=log_data.get('Processor'),
                    IsExteriorOK=log_data.get('IsExteriorOK'),
                    ExteriorClass=log_data.get('ExteriorClass'),
                    ExteriorErrReason=log_data.get('ExteriorErrReason')
                )
                session.add(log)
                session.commit()
                session.refresh(log)
                logging.info(f"新增 OCR 記錄成功: {log.Id}")
                return log.Id
        except SQLAlchemyError as e:
            logging.error(f"新增 OCR 記錄失敗: {e}")
            return None
    
    def update_ocr_log(self, log_id: int, log_data: Dict[str, Any]) -> bool:
        """
        修改 OCR 記錄
        
        Args:
            log_id: 記錄ID
            log_data: 更新的記錄資料
            
        Returns:
            是否成功
        """
        try:
            with self.get_session() as session:
                log = session.query(Ocrlog).filter(Ocrlog.Id == log_id).first()
                if not log:
                    logging.warning(f"OCR 記錄不存在: {log_id}")
                    return False
                
                # 更新欄位
                if 'Account' in log_data:
                    log.Account_ = log_data['Account']
                if 'Time' in log_data:
                    log.Time = log_data['Time']
                if 'Source' in log_data:
                    log.Source = log_data['Source']
                if 'OCRResult' in log_data:
                    log.OCRResult = log_data['OCRResult']
                if 'OK' in log_data:
                    log.OK = log_data['OK']
                if 'Image' in log_data:
                    log.Image = log_data['Image']
                if 'Manual' in log_data:
                    log.Manual = log_data['Manual']
                if 'Judgment' in log_data:
                    log.Judgment = log_data['Judgment']
                if 'KeyInResult' in log_data:
                    log.KeyInResult = log_data['KeyInResult']
                if 'Processor' in log_data:
                    log.Processor = log_data['Processor']
                if 'IsExteriorOK' in log_data:
                    log.IsExteriorOK = log_data['IsExteriorOK']
                if 'ExteriorClass' in log_data:
                    log.ExteriorClass = log_data['ExteriorClass']
                if 'ExteriorErrReason' in log_data:
                    log.ExteriorErrReason = log_data['ExteriorErrReason']
                
                session.commit()
                logging.info(f"修改 OCR 記錄成功: {log_id}")
                return True
        except SQLAlchemyError as e:
            logging.error(f"修改 OCR 記錄失敗: {e}")
            return False
    
    def delete_ocr_log(self, log_id: int) -> bool:
        """
        刪除 OCR 記錄
        
        Args:
            log_id: 記錄ID
            
        Returns:
            是否成功
        """
        try:
            with self.get_session() as session:
                log = session.query(Ocrlog).filter(Ocrlog.Id == log_id).first()
                if not log:
                    logging.warning(f"OCR 記錄不存在: {log_id}")
                    return False
                
                session.delete(log)
                session.commit()
                logging.info(f"刪除 OCR 記錄成功: {log_id}")
                return True
        except SQLAlchemyError as e:
            logging.error(f"刪除 OCR 記錄失敗: {e}")
            return False
    
    def get_ocr_logs_by_account(self, account_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        根據帳戶查詢 OCR 記錄
        
        Args:
            account_id: 帳戶ID
            limit: 限制回傳筆數
            
        Returns:
            OCR 記錄列表
        """
        try:
            with self.get_session() as session:
                logs = session.query(Ocrlog).filter(
                    Ocrlog.Account_ == account_id
                ).order_by(Ocrlog.Time.desc()).limit(limit).all()
                return [self._ocrlog_to_dict(log) for log in logs]
        except SQLAlchemyError as e:
            logging.error(f"根據帳戶查詢 OCR 記錄失敗: {e}")
            return []
    
    def get_ocr_logs_by_date_range(self, start_date: datetime.datetime, end_date: datetime.datetime, limit: int = 100) -> List[Dict[str, Any]]:
        """
        根據日期範圍查詢 OCR 記錄
        
        Args:
            start_date: 開始日期
            end_date: 結束日期
            limit: 限制回傳筆數
            
        Returns:
            OCR 記錄列表
        """
        try:
            with self.get_session() as session:
                logs = session.query(Ocrlog).filter(
                    Ocrlog.Time >= start_date,
                    Ocrlog.Time <= end_date
                ).order_by(Ocrlog.Time.desc()).limit(limit).all()
                return [self._ocrlog_to_dict(log) for log in logs]
        except SQLAlchemyError as e:
            logging.error(f"根據日期範圍查詢 OCR 記錄失敗: {e}")
            return []
    
    def get_ocr_statistics(self, start_date: Optional[datetime.datetime] = None, end_date: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        取得 OCR 統計資料
        
        Args:
            start_date: 開始日期 (可選)
            end_date: 結束日期 (可選)
            
        Returns:
            統計資料
        """
        try:
            with self.get_session() as session:
                query = session.query(Ocrlog)
                
                if start_date and end_date:
                    query = query.filter(
                        Ocrlog.Time >= start_date,
                        Ocrlog.Time <= end_date
                    )
                
                total_count = query.count()
                ok_count = query.filter(Ocrlog.OK == 1).count()
                ng_count = query.filter(Ocrlog.OK == 0).count()
                
                pass_rate = (ok_count / total_count * 100) if total_count > 0 else 0
                
                return {
                    'total_count': total_count,
                    'ok_count': ok_count,
                    'ng_count': ng_count,
                    'pass_rate': round(pass_rate, 2)
                }
        except SQLAlchemyError as e:
            logging.error(f"取得 OCR 統計資料失敗: {e}")
            return {'total_count': 0, 'ok_count': 0, 'ng_count': 0, 'pass_rate': 0}
    
    # =====================================================
    # 輔助方法
    # =====================================================
    
    def _account_to_dict(self, account: Account) -> Dict[str, Any]:
        """將 Account 物件轉換為字典"""
        return {
            'Account': account.Account,
            'Name': account.Name,
            'Password': account.Password,
            'NeedPassword': account.NeedPassword,
            'IsAdmin': account.IsAdmin
        }
    
    def _ocrlog_to_dict(self, log: Ocrlog) -> Dict[str, Any]:
        """將 Ocrlog 物件轉換為字典"""
        return {
            'Id': log.Id,
            'Account': log.Account_,
            'Time': log.Time.isoformat() if log.Time else None,
            'Source': log.Source,
            'OCRResult': log.OCRResult,
            'OK': log.OK,
            'Image': log.Image,
            'Manual': log.Manual,
            'Judgment': log.Judgment,
            'KeyInResult': log.KeyInResult,
            'Processor': log.Processor,
            'IsExteriorOK': log.IsExteriorOK,
            'ExteriorClass': log.ExteriorClass,
            'ExteriorErrReason': log.ExteriorErrReason
        }
    
    def close(self):
        """關閉資料庫連線"""
        if self.engine:
            self.engine.dispose()
            logging.info("資料庫連線已關閉")


# =====================================================
# 使用範例
# =====================================================

if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 從 config.yaml 取得 MySQL 設定
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        mysql_config = config_manager.Config.MySql
        
        # 建立資料庫連線字串
        connection_string = f"mysql+pymysql://{mysql_config.User}:{mysql_config.Password}@{mysql_config.Host}:{mysql_config.Port}/{mysql_config.Database}?charset={mysql_config.Charset}"
        
        logger.info(f"使用資料庫連線: {mysql_config.Host}:{mysql_config.Port}/{mysql_config.Database}")
        
        # 建立資料庫管理器
        db_manager = DatabaseManager(connection_string)
        
    except ImportError:
        logger.error("無法匯入 ConfigManager，使用預設連線設定")
        connection_string = "mysql+pymysql://root:Gwgplus24294096@localhost:3306/ocr_compare?charset=utf8mb4"
        db_manager = DatabaseManager(connection_string)
    
    try:
        # Account 操作範例
        print("=== Account 操作範例 ===")
        
        # 新增帳戶
        account_data = {
            'Account': 'test001',
            'Name': '測試使用者',
            'Password': 'password123',
            'NeedPassword': 1,
            'IsAdmin': 0
        }
        success = db_manager.create_account(account_data)
        print(f"新增帳戶: {'成功' if success else '失敗'}")
        
        # 查詢帳戶列表
        accounts = db_manager.get_accounts(limit=10)
        print(f"帳戶列表: {len(accounts)} 筆")
        
        # 查詢特定帳戶
        account = db_manager.get_account_by_id('test001')
        print(f"查詢帳戶: {account}")
        
        # OCR Log 操作範例
        print("\n=== OCR Log 操作範例 ===")
        
        # 新增 OCR 記錄
        log_data = {
            'Account': 'test001',
            'Source': 'TEST001',
            'OCRResult': '2A-ABCD-12345',
            'OK': 1,
            'Image': '/path/to/image.bmp',
            'Manual': 0,
            'Judgment': 0,
            'Processor': 'test001'
        }
        log_id = db_manager.create_ocr_log(log_data)
        print(f"新增 OCR 記錄: ID {log_id}")
        
        # 查詢 OCR 記錄列表
        logs = db_manager.get_ocr_logs(limit=10)
        print(f"OCR 記錄列表: {len(logs)} 筆")
        
        # 取得統計資料
        stats = db_manager.get_ocr_statistics()
        print(f"統計資料: {stats}")
        
    except Exception as e:
        print(f"執行範例時發生錯誤: {e}")
    
    finally:
        # 關閉資料庫連線
        db_manager.close()
