# trocr_gpu_optimized.py
# -*- coding: utf-8 -*-

import os
import cv2
import torch
import tkinter as tk
from tkinter import Label, Button
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageOps
from ultralytics import YOLO
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from pathlib import Path

# ======== 幾何設定 ========
TARGET_W, TARGET_H = 360, 128
STAGE1_FILL = (0, 0, 0)
STAGE2_SIZE = 384
STAGE2_FILL = (255, 255, 255)

# ======== 模型與處理器路徑 ========
MODEL_DIR = "./trocr-384x384-finetuned"
PROCESSOR_DIR = "./trocr-384x384-processor"

# ======== 幫助函式 ========
def letterbox_36128(img: Image.Image, W=TARGET_W, H=TARGET_H, fill=STAGE1_FILL) -> Image.Image:
    img = img.convert("RGB")
    r = min(W / img.width, H / img.height)
    nw, nh = max(1, int(round(img.width * r))), max(1, int(round(img.height * r)))
    resized = img.resize((nw, nh), Image.LANCZOS)
    dw, dh = W - nw, H - nh
    padding = (dw // 2, dh // 2, dw - dw // 2, dh - dh // 2)
    return ImageOps.expand(resized, padding, fill=fill)

def to_384_square(img: Image.Image, size=STAGE2_SIZE, fill=STAGE2_FILL) -> Image.Image:
    w, h = img.size
    if w > size or h > size:
        s = min(size / w, size / h)
        img = img.resize((max(1, int(round(w * s))), max(1, int(round(h * s)))), Image.BICUBIC)
    canvas = Image.new("RGB", (size, size), fill)
    canvas.paste(img, ((size - img.width)//2, (size - img.height)//2))
    return canvas

def get_font(size=48):
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/mingliu.ttc",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

# ======== 載入模型 ========
model = YOLO('./best.pt')

if not Path(MODEL_DIR).exists():
    raise FileNotFoundError(f"找不到 TrOCR 模型目錄：{MODEL_DIR}")
if not Path(PROCESSOR_DIR).exists():
    raise FileNotFoundError(f"找不到 Processor 目錄：{PROCESSOR_DIR}")

processor = TrOCRProcessor.from_pretrained(PROCESSOR_DIR)

# ✅ 修正：設定合法 size，避免 ValueError
if hasattr(processor, "image_processor"):
    ip = processor.image_processor
    ip.do_center_crop = False
    ip.do_resize = False
    ip.size = {"height": 384, "width": 384}

# ✅ 使用 FP16 加速推論
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
trocr_model = VisionEncoderDecoderModel.from_pretrained(MODEL_DIR).half().to(device)
trocr_model.eval()

# ======== 載入圖像 ========
image_dir = './inference'
image_files = sorted([f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
if not image_files:
    raise FileNotFoundError(f"inference 資料夾內沒有圖片：{image_dir}")

# ======== GUI 初始化 ========
root = tk.Tk()
root.title("YOLO + TrOCR Viewer (GPU-Optimized)")

root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

img_label = Label(root, bg="#111111")
img_label.grid(row=0, column=0, sticky="nsew")

button_frame = tk.Frame(root)
button_frame.grid(row=1, column=0, pady=10)

current_index = 0
font = get_font(48)

def show_image_with_ocr(index):
    image_path = os.path.join(image_dir, image_files[index])
    original = cv2.imread(image_path)
    if original is None:
        return

    results = model(image_path)[0]

    img_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)

    for box in results.boxes:
        cls_id = int(box.cls[0])
        class_name = model.names.get(cls_id, str(cls_id))
        if class_name != 'text':
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        x1, x2 = max(0, min(x1, pil_img.width - 1)), max(0, min(x2, pil_img.width - 1))
        y1, y2 = max(0, min(y1, pil_img.height - 1)), max(0, min(y2, pil_img.height - 1))
        if x2 <= x1 or y2 <= y1:
            continue

        cropped = pil_img.crop((x1, y1, x2, y2))
        img_36128 = letterbox_36128(cropped)
        img_384 = to_384_square(img_36128)

        # TrOCR 推論（FP16）
        inputs = processor(images=img_384, return_tensors="pt").to(device)
        inputs = {k: v.half() for k, v in inputs.items()}  # 🧠 強制轉為 FP16

        with torch.no_grad():
            pred_ids = trocr_model.generate(
                **inputs,
                max_length=32,
                num_beams=1,  # ⚡ greedy 解碼，更快
                early_stopping=True
            )
        pred_text = processor.batch_decode(pred_ids, skip_special_tokens=True)[0].strip()

        draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
        ty = max(0, y1 - 50)
        text_bg_w = max(1, int(len(pred_text) * 20))
        draw.rectangle([x1, ty, x1 + text_bg_w, ty + 50], fill=(0, 0, 0))
        draw.text((x1 + 4, ty + 8), pred_text, font=font, fill=(0, 255, 0))

    # 顯示圖像
    avail_w = img_label.winfo_width()
    if avail_w <= 1:
        avail_w = 1200
    ratio = min(1.0, avail_w / max(1, pil_img.width))
    disp_w = int(pil_img.width * ratio)
    disp_h = int(pil_img.height * ratio)
    pil_img = pil_img.resize((disp_w, disp_h), Image.LANCZOS)

    tk_img = ImageTk.PhotoImage(pil_img)
    img_label.configure(image=tk_img)
    img_label.image = tk_img

def next_image():
    global current_index
    current_index = (current_index + 1) % len(image_files)
    show_image_with_ocr(current_index)

def prev_image():
    global current_index
    current_index = (current_index - 1) % len(image_files)
    show_image_with_ocr(current_index)

def exit_program():
    root.destroy()

# 按鈕列
Button(button_frame, text="Prev", command=prev_image, width=10).pack(side='left', padx=10)
Button(button_frame, text="Next", command=next_image, width=10).pack(side='left', padx=10)
Button(button_frame, text="Exit", command=exit_program, width=10).pack(side='left', padx=10)

# 初始顯示
show_image_with_ocr(current_index)
root.mainloop()

