# Canvas Image 模組說明

## 概述
`canvas-image.js` 是一個獨立的 JavaScript 模組，負責處理圖片顯示、繪製、縮放、旋轉等功能。此模組從原本的 `frmmain.html` 中提取出來，以提高程式碼的可維護性和模組化程度。

## 功能特性

### 主要功能
- **圖片顯示**: 支援載入和顯示圖片
- **Canvas 初始化**: 自動調整 Canvas 尺寸以填滿容器
- **圖片繪製**: 支援多種繪製模式（正常、繪製中、縮放、旋轉）
- **滑鼠互動**: 支援滑鼠繪製線條和圖片操作
- **響應式設計**: 自動適應視窗大小變化

### 繪製模式
1. **none**: 無圖片狀態
2. **normal**: 正常顯示模式
3. **drawing**: 繪製線條模式
4. **startScale**: 縮放模式
5. **zoomAndRotate**: 旋轉模式

## API 介面

### 主要函數

#### `initCanvas()`
初始化 Canvas 元素，設定事件監聽器和樣式。

#### `showImage(imagePath)`
顯示指定路徑的圖片。
- **參數**: `imagePath` (string) - 圖片檔案路徑
- **功能**: 載入並顯示圖片，自動調整 Canvas 尺寸

#### `showNoImage()`
顯示無圖片狀態。
- **功能**: 隱藏圖片，顯示佔位符

#### `setWorkStatus(status)`
設定工作狀態。
- **參數**: `status` (string) - 工作狀態
- **可用值**: "none", "normal", "drawing", "startScale", "zoomAndRotate"

#### `setScaleParams(newScale, newOffsetX, newOffsetY)`
設定縮放參數。
- **參數**: 
  - `newScale` (number) - 縮放比例
  - `newOffsetX` (number) - X 軸偏移量
  - `newOffsetY` (number) - Y 軸偏移量

#### `resizeCanvasToFill()`
重新調整 Canvas 尺寸以填滿容器。

## 使用方式

### 1. 引入模組
```html
<script src="script/canvas-image.js"></script>
```

### 2. 初始化
```javascript
// 在頁面載入完成後初始化
CanvasImage.initCanvas();
```

### 3. 使用功能
```javascript
// 顯示圖片
CanvasImage.showImage('path/to/image.jpg');

// 隱藏圖片
CanvasImage.showNoImage();

// 設定狀態
CanvasImage.setWorkStatus('normal');
```

## 全域變數

模組內部使用以下全域變數：
- `canvas`: Canvas DOM 元素
- `ctx`: Canvas 2D 繪圖上下文
- `currentImage`: 當前顯示的圖片物件
- `workStatus`: 當前工作狀態
- `startPoint`, `endPoint`: 繪製線條的起點和終點
- `scale`, `offsetX`, `offsetY`: 縮放和偏移參數
- `angle`: 旋轉角度
- `rate`: 縮放比例

## 事件處理

### 滑鼠事件
- **mousedown**: 開始繪製線條或切換狀態
- **mouseup**: 完成繪製線條
- **mousemove**: 更新繪製中的線條
- **dblclick**: 雙擊回到正常狀態
- **contextmenu**: 禁用右鍵選單

### 視窗事件
- **resize**: 自動調整 Canvas 尺寸

## 測試

可以使用 `test_canvas.html` 檔案來測試模組功能：
1. 開啟 `test_canvas.html` 在瀏覽器中
2. 點擊測試按鈕驗證各項功能
3. 檢查瀏覽器控制台的日誌訊息

## 注意事項

1. **依賴性**: 需要 HTML 中存在 `imageCanvas` 和 `imagePanel` 元素
2. **路徑格式**: 圖片路徑會自動將反斜線轉換為正斜線
3. **錯誤處理**: 圖片載入失敗時會自動顯示無圖片狀態
4. **效能**: 大量圖片操作時建議適當控制重新繪製頻率

## 重構說明

此次重構將原本在 `frmmain.html` 中的圖片處理程式碼（約 370 行）提取到獨立的 `canvas-image.js` 檔案中，帶來以下好處：

1. **模組化**: 圖片處理邏輯獨立，便於維護和測試
2. **可重用性**: 其他頁面也可以使用此模組
3. **程式碼整潔**: 主 HTML 檔案更加簡潔
4. **除錯便利**: 圖片相關問題可以專注在此模組中解決

## 版本資訊
- **版本**: 1.0.0
- **建立日期**: 2024年
- **相容性**: 支援現代瀏覽器
