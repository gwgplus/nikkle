#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO OCR 測試程式
使用 PyQt5 提供圖形界面來測試 YOLO OCR 功能
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QFileDialog, QMessageBox, QProgressBar, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap
from PIL import Image

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from yolo_ocr import YOLOOCR
    YOLO_AVAILABLE = True
except ImportError as e:
    YOLO_AVAILABLE = False
    print(f"YOLO OCR 模組導入失敗: {e}")


class OCRWorker(QThread):
    """OCR 處理工作線程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, image_path, yolo_ocr):
        super().__init__()
        self.image_path = image_path
        self.yolo_ocr = yolo_ocr
    
    def run(self):
        """執行 OCR 處理"""
        try:
            
            result = self.yolo_ocr.access_ocr(self.image_path)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class YOLOOCRTestWindow(QMainWindow):
    """YOLO OCR 測試視窗"""
    
    def __init__(self):
        super().__init__()
        self.yolo_ocr = None
        self.current_image_path = None
        self.worker_thread = None
        self.init_ui()
        self.init_yolo_ocr()
        
    def init_ui(self):
        """初始化使用者介面"""
        self.setWindowTitle("YOLO OCR 測試程式")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央 widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主佈局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 標題
        title_label = QLabel("YOLO OCR 測試程式")
        title_label.setFont(QFont("新細明體", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 狀態群組
        status_group = QGroupBox("狀態")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("準備就緒")
        self.status_label.setFont(QFont("新細明體", 10))
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(status_group)
        
        # 圖片選擇群組
        image_group = QGroupBox("圖片選擇")
        image_layout = QVBoxLayout(image_group)
        
        # 按鈕區域
        button_layout = QHBoxLayout()
        
        self.select_button = QPushButton("選擇圖片")
        self.select_button.setFont(QFont("新細明體", 12))
        self.select_button.clicked.connect(self.select_image)
        button_layout.addWidget(self.select_button)
        
        self.ocr_button = QPushButton("執行 OCR")
        self.ocr_button.setFont(QFont("新細明體", 12))
        self.ocr_button.clicked.connect(self.run_ocr)
        self.ocr_button.setEnabled(False)
        button_layout.addWidget(self.ocr_button)
        
        self.clear_button = QPushButton("清除結果")
        self.clear_button.setFont(QFont("新細明體", 12))
        self.clear_button.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        image_layout.addLayout(button_layout)
        
        # 圖片路徑顯示
        self.image_path_label = QLabel("未選擇圖片")
        self.image_path_label.setFont(QFont("新細明體", 10))
        self.image_path_label.setWordWrap(True)
        self.image_path_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
        image_layout.addWidget(self.image_path_label)
        
        main_layout.addWidget(image_group)
        
        # 結果顯示群組
        result_group = QGroupBox("OCR 結果")
        result_layout = QVBoxLayout(result_group)
        
        # 時間統計標籤
        self.timing_label = QLabel("⏱️ 時間統計: 等待處理...")
        self.timing_label.setFont(QFont("新細明體", 10, QFont.Bold))
        self.timing_label.setStyleSheet("QLabel { background-color: #e8f4fd; padding: 8px; border: 1px solid #b3d9ff; border-radius: 4px; }")
        self.timing_label.setWordWrap(True)
        result_layout.addWidget(self.timing_label)
        
        self.result_text = QTextEdit()
        self.result_text.setFont(QFont("Consolas", 10))
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(200)
        result_layout.addWidget(self.result_text)
        
        main_layout.addWidget(result_group)
        
        # 模型資訊群組
        model_group = QGroupBox("模型資訊")
        model_layout = QVBoxLayout(model_group)
        
        self.model_info_text = QTextEdit()
        self.model_info_text.setFont(QFont("Consolas", 9))
        self.model_info_text.setReadOnly(True)
        self.model_info_text.setMaximumHeight(100)
        model_layout.addWidget(self.model_info_text)
        
        main_layout.addWidget(model_group)
        
    def init_yolo_ocr(self):
        """初始化 YOLO OCR"""
        if not YOLO_AVAILABLE:
            self.status_label.setText("❌ YOLO OCR 模組不可用")
            self.select_button.setEnabled(False)
            self.model_info_text.setPlainText("YOLO OCR 模組導入失敗，請檢查依賴項")
            return
        
        try:
            self.yolo_ocr = YOLOOCR()
            self.status_label.setText("✅ YOLO OCR 已初始化")
            
            # 顯示模型資訊
            model_info = self.yolo_ocr.get_model_info()
            info_text = f"模型路徑: {model_info.get('model_path', 'N/A')}\n"
            info_text += f"TrOCR 路徑: {model_info.get('trocr_path', 'N/A')}\n"
            info_text += f"字體路徑: {model_info.get('font_path', 'N/A')}\n"
            info_text += f"模型載入狀態: {'已載入' if model_info.get('models_loaded', False) else '未載入'}"
            
            self.model_info_text.setPlainText(info_text)
            
        except Exception as e:
            self.status_label.setText(f"❌ YOLO OCR 初始化失敗: {str(e)}")
            self.select_button.setEnabled(False)
            self.model_info_text.setPlainText(f"初始化錯誤: {str(e)}")
    
    def select_image(self):
        """選擇圖片檔案"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇圖片檔案",
            "",
            "圖片檔案 (*.jpg *.jpeg *.png *.bmp *.tiff *.tif);;所有檔案 (*)"
        )
        
        if file_path:
            self.current_image_path = file_path
            self.image_path_label.setText(f"已選擇: {file_path}")
            self.ocr_button.setEnabled(True)
            self.status_label.setText("✅ 圖片已選擇，可以執行 OCR")
            
            # 顯示圖片資訊
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    mode = img.mode
                    self.status_label.setText(f"✅ 圖片已選擇 ({width}x{height}, {mode})")
            except Exception as e:
                self.status_label.setText(f"⚠️ 圖片已選擇，但無法讀取資訊: {str(e)}")
    
    def run_ocr(self):
        """執行 OCR"""
        if not self.current_image_path:
            QMessageBox.warning(self, "警告", "請先選擇圖片檔案")
            return
        
        if not self.yolo_ocr:
            QMessageBox.critical(self, "錯誤", "YOLO OCR 未初始化")
            return
        
        # 禁用按鈕
        self.select_button.setEnabled(False)
        self.ocr_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        
        # 顯示進度條
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 無限進度條
        
        self.status_label.setText("🔄 正在執行 OCR...")
        self.timing_label.setText("⏱️ 時間統計: 處理中...")
        
        # 在工作線程中執行 OCR
        self.worker_thread = OCRWorker(self.current_image_path, self.yolo_ocr)
        self.worker_thread.finished.connect(self.on_ocr_finished)
        self.worker_thread.error.connect(self.on_ocr_error)
        self.worker_thread.start()
    
    def on_ocr_finished(self, result):
        """OCR 完成處理"""
        # 隱藏進度條
        self.progress_bar.setVisible(False)
        
        # 啟用按鈕
        self.select_button.setEnabled(True)
        self.ocr_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
        # 顯示結果
        if result['success']:
            self.status_label.setText("✅ OCR 執行成功")
            
            # 更新時間統計標籤
            if 'timing' in result:
                timing = result['timing']
                timing_text = f"⏱️ 總時間: {timing['total_ms']} ms | "
                timing_text += f"YOLO: {timing['yolo_ms']} ms | "
                timing_text += f"TrOCR: {timing['trocr_ms']} ms | "
                timing_text += f"文字數: {timing['text_count']}"
                
                if timing['text_count'] > 0:
                    avg_per_text = timing['trocr_ms'] / timing['text_count']
                    timing_text += f" | 平均: {avg_per_text:.1f} ms/字"
                
                self.timing_label.setText(timing_text)
            else:
                self.timing_label.setText("⏱️ 時間統計: 無計時數據")
            
            # 格式化結果
            result_text = f"OCR 執行成功！\n"
            result_text += f"{'='*50}\n"
            
            # 顯示詳細時間統計
            if 'timing' in result:
                timing = result['timing']
                result_text += f"⏱️  詳細時間統計:\n"
                result_text += f"  總處理時間: {timing['total_ms']} ms\n"
                result_text += f"  YOLO 檢測: {timing['yolo_ms']} ms\n"
                result_text += f"  TrOCR 識別: {timing['trocr_ms']} ms\n"
                result_text += f"  識別文字數量: {timing['text_count']}\n"
                
                if timing['text_count'] > 0:
                    avg_per_text = timing['trocr_ms'] / timing['text_count']
                    result_text += f"  平均每文字: {avg_per_text:.2f} ms\n"
                
                # 計算各階段佔比
                if timing['total_ms'] > 0:
                    yolo_percent = (timing['yolo_ms'] / timing['total_ms']) * 100
                    trocr_percent = (timing['trocr_ms'] / timing['total_ms']) * 100
                    result_text += f"  時間佔比 - YOLO: {yolo_percent:.1f}%, TrOCR: {trocr_percent:.1f}%\n"
                
                result_text += f"{'='*50}\n"
            
            result_text += f"📝 檢測結果:\n"
            for i, item in enumerate(result['results'], 1):
                result_text += f"  結果 {i}:\n"
                result_text += f"    文字: {item['text']}\n"
                result_text += f"    位置: {item['bbox']}\n" 
                result_text += f"    信心度: {item['confidence']:.3f}\n"
                result_text += f"    {'-'*30}\n"
            result_text += f"{'='*50}\n"
            
            if 'bbox_results' in result and result['bbox_results']:
                result_text += f"檢測到的文字區域:\n"
                for i, bbox in enumerate(result['bbox_results'], 1):
                    result_text += f"  區域 {i}: {bbox.get('text', 'N/A')} (信心度: {bbox.get('confidence', 'N/A')})\n"
            
            result_text += f"\n原始結果:\n{result}"
            
            self.result_text.setPlainText(result_text)
            
            # 顯示成功訊息
            #QMessageBox.information(self, "成功", f"OCR 識別成功！\n結果: {result['ocr_result']}")
            
        else:
            self.status_label.setText("❌ OCR 執行失敗")
            error_msg = result.get('error', '未知錯誤')
            
            # 即使失敗也顯示時間統計（如果有）
            if 'timing' in result:
                timing = result['timing']
                self.timing_label.setText(f"⏱️ 處理時間: {timing['total_ms']} ms (失敗)")
            else:
                self.timing_label.setText("⏱️ 時間統計: 處理失敗")
            
            error_text = f"OCR 執行失敗: {error_msg}\n"
            if 'timing' in result:
                timing = result['timing']
                error_text += f"\n⏱️  處理時間: {timing['total_ms']} ms\n"
            
            self.result_text.setPlainText(error_text)
            QMessageBox.warning(self, "失敗", f"OCR 執行失敗: {error_msg}")
    
    def on_ocr_error(self, error_msg):
        """OCR 錯誤處理"""
        # 隱藏進度條
        self.progress_bar.setVisible(False)
        
        # 啟用按鈕
        self.select_button.setEnabled(True)
        self.ocr_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        
        self.status_label.setText("❌ OCR 執行錯誤")
        self.timing_label.setText("⏱️ 時間統計: 執行錯誤")
        self.result_text.setPlainText(f"OCR 執行錯誤: {error_msg}")
        QMessageBox.critical(self, "錯誤", f"OCR 執行錯誤: {error_msg}")
    
    def clear_results(self):
        """清除結果"""
        self.result_text.clear()
        self.timing_label.setText("⏱️ 時間統計: 等待處理...")
        self.status_label.setText("準備就緒")
        if self.current_image_path:
            self.status_label.setText("✅ 圖片已選擇，可以執行 OCR")


def main():
    """主程式"""
    app = QApplication(sys.argv)
    
    # 設定應用程式字體
    font = QFont("新細明體", 10)
    app.setFont(font)
    
    # 創建主視窗
    window = YOLOOCRTestWindow()
    window.show()
    
    # 執行應用程式
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
