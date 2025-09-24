# HTML 訊息彈出視窗系統

## 概述

這是一個通用的訊息彈出視窗系統，提供三種不同類型的訊息顯示：警示、一般訊息、成功訊息。系統具有現代化的 UI 設計和流暢的動畫效果。

## 檔案結構

```
html/
├── css/
│   └── show-msg.css          # 訊息視窗樣式
├── script/
│   ├── html-msgbox.js        # 訊息視窗 JavaScript
│   └── MSGBOX_README.md      # 使用說明
└── msgbox-test.html          # 測試頁面
```

## 使用方法

### 1. 載入必要檔案

在 HTML 頁面的 `<head>` 區塊中載入 CSS 和 JavaScript：

```html
<link rel="stylesheet" href="./css/show-msg.css">
<script src="./script/html-msgbox.js"></script>
```

### 2. 顯示訊息

使用 `showMsg()` 函數來顯示訊息：

```javascript
showMsg(mode, title, message);
```

#### 參數說明

- **mode** (數字): 訊息類型
  - `1` = 警示 (橘色圖標)
  - `2` = 一般訊息 (藍色圖標)
  - `3` = 成功 (綠色圖標)

- **title** (字串): 標題文字，會以粗體顯示

- **message** (字串): 訊息內容

#### 使用範例

```javascript
// 警示訊息
showMsg(1, "系統警告", "請檢查您的輸入資料");

// 一般訊息
showMsg(2, "系統提示", "這是一個一般性的提示訊息");

// 成功訊息
showMsg(3, "操作成功", "資料已成功儲存");
```

## 功能特色

### 1. 三種訊息類型
- **警示** (mode=1): 橘色圖標，用於警告和錯誤訊息
- **一般訊息** (mode=2): 藍色圖標，用於一般提示和資訊
- **成功** (mode=3): 綠色圖標，用於成功操作確認

### 2. 現代化設計
- 圓角設計和陰影效果
- 漸層背景和懸停動畫
- 響應式設計，支援各種螢幕尺寸

### 3. 互動功能
- 點擊「確定」按鈕關閉
- 按 ESC 鍵關閉
- 點擊背景區域關閉
- 自動聚焦到確定按鈕

### 4. 動畫效果
- 顯示時的縮放和淡入動畫
- 關閉時的縮放和淡出動畫
- 背景模糊效果

## 整合到現有專案

### 在 go.py 中使用

可以在 Python 後端調用 JavaScript 來顯示訊息：

```python
# 顯示成功訊息
self.view.page().runJavaScript('showMsg(3, "成功", "操作已完成");')

# 顯示錯誤訊息
self.view.page().runJavaScript('showMsg(1, "錯誤", "操作失敗，請重試");')

# 顯示提示訊息
self.view.page().runJavaScript('showMsg(2, "提示", "請稍候...");')
```

### 替換現有的 alert()

可以將現有的 `alert()` 替換為更美觀的訊息視窗：

```javascript
// 原本的寫法
alert("操作成功");

// 替換為
showMsg(3, "成功", "操作成功");
```

## 自訂樣式

如果需要自訂樣式，可以修改 `show-msg.css` 檔案：

### 修改顏色主題

```css
/* 警示顏色 */
.msgbox-icon-warning {
    color: #ff9800;  /* 修改為您想要的顏色 */
}

/* 一般訊息顏色 */
.msgbox-icon-info {
    color: #2196f3;  /* 修改為您想要的顏色 */
}

/* 成功顏色 */
.msgbox-icon-success {
    color: #4caf50;  /* 修改為您想要的顏色 */
}
```

### 修改尺寸

```css
/* 修改視窗最大寬度 */
.msgbox-container {
    max-width: 600px;  /* 預設是 500px */
}

/* 修改標題字體大小 */
.msgbox-title {
    font-size: 28px;  /* 預設是 24px */
}
```

## 測試

可以使用 `msgbox-test.html` 來測試各種訊息類型：

1. 開啟 `html/msgbox-test.html`
2. 點擊不同的按鈕來測試各種訊息類型
3. 測試各種關閉方式（按鈕、ESC 鍵、背景點擊）

## 注意事項

1. **載入順序**: 確保 CSS 在 JavaScript 之前載入
2. **全域函數**: `showMsg()` 會自動註冊為全域函數
3. **重複顯示**: 如果已經有訊息視窗顯示，新的視窗會替換舊的
4. **瀏覽器相容性**: 支援所有現代瀏覽器

## 故障排除

### 訊息視窗不顯示
- 檢查 CSS 和 JavaScript 檔案是否正確載入
- 檢查瀏覽器控制台是否有錯誤訊息
- 確認 `showMsg()` 函數是否被正確調用

### 樣式不正確
- 檢查 CSS 檔案路徑是否正確
- 確認沒有其他 CSS 規則覆蓋訊息視窗樣式
- 檢查瀏覽器開發者工具中的樣式面板

### 動畫效果不順暢
- 確認瀏覽器支援 CSS transitions
- 檢查是否有其他 JavaScript 干擾動畫
- 嘗試在較新的瀏覽器中測試 