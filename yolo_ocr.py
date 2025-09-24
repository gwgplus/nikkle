# yolo_ocr.py
# -*- coding: utf-8 -*-

import os
import cv2
import torch
import time
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from PIL import Image, ImageOps

from ultralytics import YOLO
from transformers import TrOCRProcessor, VisionEncoderDecoderModel


class YOLOOCR:
    """YOLO + TrOCR OCR 處理類別"""
    
    def __init__(self, 
                 yolo_weights: str = "./best.pt",
                 model_dir: str = "./trocr-384x384-finetuned",
                 processor_dir: str = "./trocr-384x384-processor",
                 stage1_w: int = 360,
                 stage1_h: int = 128,
                 stage1_fill: Tuple[int, int, int] = (0, 0, 0),
                 stage2_size: int = 384,
                 stage2_fill: Tuple[int, int, int] = (255, 255, 255),
                 gen_max_len: int = 32,
                 gen_beams: int = 1,
                 use_fp16: bool = True,
                 optimize_memory: bool = True):
        """
        初始化 YOLO OCR 處理器
        
        Args:
            yolo_weights: YOLO 模型權重檔案路徑
            model_dir: TrOCR 模型目錄
            processor_dir: TrOCR 處理器目錄
            stage1_w: 第一階段寬度
            stage1_h: 第一階段高度
            stage1_fill: 第一階段填充顏色
            stage2_size: 第二階段尺寸
            stage2_fill: 第二階段填充顏色
            gen_max_len: 生成最大長度
            gen_beams: 生成束搜索數量 (1=greedy, 更快)
            use_fp16: 是否使用 FP16 精度 (GPU 優化)
            optimize_memory: 是否啟用記憶體優化
        """
        self.yolo_weights = yolo_weights
        self.model_dir = model_dir
        self.processor_dir = processor_dir
        self.stage1_w = stage1_w
        self.stage1_h = stage1_h
        self.stage1_fill = stage1_fill
        self.stage2_size = stage2_size
        self.stage2_fill = stage2_fill
        self.gen_max_len = gen_max_len
        self.gen_beams = gen_beams
        self.use_fp16 = use_fp16
        self.optimize_memory = optimize_memory
        
        # 模型和設備
        self.det_model = None
        self.processor = None
        self.trocr_model = None
        self.device = None
        self._initialized = False
        
    def _initialize_models(self):
        """初始化模型（延遲載入）"""
        if self._initialized:
            return
            
        try:
            print(">> Loading YOLO...")
            self.det_model = YOLO(self.yolo_weights)
            
            print(">> Loading TrOCR...")
            self.processor = TrOCRProcessor.from_pretrained(self.processor_dir)
            
            # ✅ 修正：設定合法 size，避免 ValueError
            if hasattr(self.processor, "image_processor"):
                ip = self.processor.image_processor
                ip.do_center_crop = False
                ip.do_resize = False
                ip.size = {"height": self.stage2_size, "width": self.stage2_size}
            
            # ✅ 使用 FP16 加速推論
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.trocr_model = VisionEncoderDecoderModel.from_pretrained(self.model_dir)
            
            if self.use_fp16 and self.device.type == "cuda":
                self.trocr_model = self.trocr_model.half()
                print(">> Using FP16 precision for GPU acceleration")
            
            self.trocr_model.to(self.device).eval()
            
            # 記憶體優化
            if self.optimize_memory and self.device.type == "cuda":
                torch.cuda.empty_cache()
                print(">> GPU memory optimized")
            
            self._initialized = True
            print(">> Models loaded successfully")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize models: {str(e)}")
    
    def _letterbox_36128(self, img: Image.Image) -> Image.Image:
        """Stage1：等比縮放 + 補邊到指定尺寸"""
        img = img.convert("RGB")
        r = min(self.stage1_w / img.width, self.stage1_h / img.height)
        nw, nh = max(1, int(round(img.width * r))), max(1, int(round(img.height * r)))
        resized = img.resize((nw, nh), Image.LANCZOS)
        dw, dh = self.stage1_w - nw, self.stage1_h - nh
        padding = (dw // 2, dh // 2, dw - dw // 2, dh - dh // 2)
        return ImageOps.expand(resized, padding, fill=self.stage1_fill)
    
    def _to_384_square(self, img_36128: Image.Image) -> Image.Image:
        """Stage2：把第一階段結果置中貼到正方形"""
        w, h = img_36128.size
        if w > self.stage2_size or h > self.stage2_size:
            s = min(self.stage2_size / w, self.stage2_size / h)
            img_36128 = img_36128.resize(
                (max(1, int(round(w * s))), max(1, int(round(h * s)))),
                Image.BICUBIC
            )
            w, h = img_36128.size
        canvas = Image.new("RGB", (self.stage2_size, self.stage2_size), self.stage2_fill)
        canvas.paste(img_36128, ((self.stage2_size - w)//2, (self.stage2_size - h)//2))
        return canvas
    
    def _clip_box(self, x1: float, y1: float, x2: float, y2: float, w: int, h: int) -> Tuple[int, int, int, int]:
        """裁剪邊界框到圖片範圍內"""
        x1 = max(0, min(int(x1), w - 1))
        y1 = max(0, min(int(y1), h - 1))
        x2 = max(0, min(int(x2), w - 1))
        y2 = max(0, min(int(y2), h - 1))
        return x1, y1, x2, y2
    
    def access_ocr(self, image_path: str) -> Dict[str, Any]:
        """
        對單張圖片進行 OCR 處理
        
        Args:
            image_path: 圖片檔案路徑
            
        Returns:
            Dict 包含:
                - success: bool, 是否成功
                - results: list, OCR 結果列表，每個元素包含:
                    - bbox: [x1, y1, x2, y2], 邊界框座標
                    - text: str, 識別的文字
                    - confidence: float, 置信度
                - timing: dict, 時間統計:
                    - total_ms: float, 總處理時間 (毫秒)
                    - yolo_ms: float, YOLO 檢測時間 (毫秒)
                    - trocr_ms: float, TrOCR 識別時間 (毫秒)
                    - text_count: int, 識別的文字數量
                - error: str, 錯誤訊息（如果失敗）
        """
        try:
            # 開始計時
            start_time = time.perf_counter()
            
            # 延遲初始化模型
            self._initialize_models()
            
            # 檢查檔案是否存在
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "results": [],
                    "timing": {"total_ms": 0, "yolo_ms": 0, "trocr_ms": 0, "text_count": 0},
                    "error": f"Image file not found: {image_path}"
                }
            
            # 讀取圖片
            bgr = cv2.imread(image_path)
            if bgr is None:
                return {
                    "success": False,
                    "results": [],
                    "timing": {"total_ms": 0, "yolo_ms": 0, "trocr_ms": 0, "text_count": 0},
                    "error": f"Cannot read image: {image_path}"
                }
            
            # YOLO 檢測計時
            yolo_start = time.perf_counter()
            results = self.det_model(image_path)[0]
            yolo_time = (time.perf_counter() - yolo_start) * 1000  # 轉換為毫秒
            
            # 轉換為 PIL 圖片
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            
            ocr_results = []
            trocr_start = time.perf_counter()
            
            with torch.no_grad():
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    class_name = self.det_model.names.get(cls_id, str(cls_id))
                    
                    # 只處理 'text' 類別
                    if class_name != "text":
                        continue
                    
                    # 取得邊界框座標
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = self._clip_box(x1, y1, x2, y2, pil_img.width, pil_img.height)
                    
                    # 檢查邊界框有效性
                    if x2 <= x1 or y2 <= y1:
                        continue
                    
                    # 裁剪文字區域
                    crop = pil_img.crop((x1, y1, x2, y2))
                    
                    # 兩段式幾何處理
                    img_36128 = self._letterbox_36128(crop)
                    img_384 = self._to_384_square(img_36128)
                    
                    # TrOCR 推論（GPU 優化）
                    inputs = self.processor(images=img_384, return_tensors="pt").to(self.device)
                    
                    # 🧠 強制轉為 FP16（如果啟用）
                    if self.use_fp16 and self.device.type == "cuda":
                        inputs = {k: v.half() for k, v in inputs.items()}
                    
                    with torch.no_grad():
                        pred_ids = self.trocr_model.generate(
                            **inputs,
                            max_length=self.gen_max_len,
                            num_beams=self.gen_beams,  # ⚡ greedy 解碼，更快
                            early_stopping=True
                        )
                    pred_text = self.processor.batch_decode(pred_ids, skip_special_tokens=True)[0].strip()
                    
                    # 取得置信度
                    confidence = float(box.conf[0]) if hasattr(box, 'conf') else 0.0
                    
                    # 添加到結果
                    ocr_results.append({
                        "bbox": [x1, y1, x2, y2],
                        "text": pred_text,
                        "confidence": confidence
                    })
            
            # 計算 TrOCR 時間
            trocr_time = (time.perf_counter() - trocr_start) * 1000  # 轉換為毫秒
            total_time = (time.perf_counter() - start_time) * 1000  # 轉換為毫秒
            
            return {
                "success": True,
                "results": ocr_results,
                "timing": {
                    "total_ms": round(total_time, 2),
                    "yolo_ms": round(yolo_time, 2),
                    "trocr_ms": round(trocr_time, 2),
                    "text_count": len(ocr_results)
                },
                "error": None
            }
            
        except Exception as e:
            total_time = (time.perf_counter() - start_time) * 1000 if 'start_time' in locals() else 0
            return {
                "success": False,
                "results": [],
                "timing": {"total_ms": round(total_time, 2), "yolo_ms": 0, "trocr_ms": 0, "text_count": 0},
                "error": f"OCR processing failed: {str(e)}"
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """取得模型資訊"""
        return {
            "yolo_weights": self.yolo_weights,
            "model_dir": self.model_dir,
            "processor_dir": self.processor_dir,
            "device": str(self.device) if self.device else "Not initialized",
            "initialized": self._initialized,
            "stage1_size": (self.stage1_w, self.stage1_h),
            "stage2_size": self.stage2_size,
            "use_fp16": self.use_fp16,
            "optimize_memory": self.optimize_memory,
            "gen_beams": self.gen_beams
        }


# 使用範例
if __name__ == "__main__":
    # 創建 OCR 處理器
    ocr = YOLOOCR()
    
    # 處理單張圖片
    result = ocr.access_ocr("./test_image.jpg")
    
    if result["success"]:
        print("OCR 處理成功!")
        
        # 顯示時間統計
        timing = result["timing"]
        print(f"\n⏱️  時間統計:")
        print(f"  總處理時間: {timing['total_ms']} ms")
        print(f"  YOLO 檢測: {timing['yolo_ms']} ms")
        print(f"  TrOCR 識別: {timing['trocr_ms']} ms")
        print(f"  識別文字數量: {timing['text_count']}")
        
        if timing['text_count'] > 0:
            avg_per_text = timing['trocr_ms'] / timing['text_count']
            print(f"  平均每文字: {avg_per_text:.2f} ms")
        
        # 顯示識別結果
        print(f"\n📝 識別結果:")
        for i, res in enumerate(result["results"]):
            print(f"  結果 {i+1}:")
            print(f"    文字: {res['text']}")
            print(f"    邊界框: {res['bbox']}")
            print(f"    置信度: {res['confidence']:.3f}")
    else:
        print(f"OCR 處理失敗: {result['error']}")
        if "timing" in result:
            timing = result["timing"]
            print(f"處理時間: {timing['total_ms']} ms")
    
    # 顯示模型資訊
    print("\n模型資訊:")
    info = ocr.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
