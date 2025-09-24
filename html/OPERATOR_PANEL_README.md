# 操作員面板功能說明

## 概述
操作員面板功能允許用戶選擇一位或多位操作員，用於系統操作記錄和權限管理。

## 功能特性

### 主要功能
- **操作員列表載入**: 從後端 API 取得所有可用的操作員資訊
- **多選操作員**: 支援選擇多位操作員
- **必選驗證**: 確保至少選擇一位操作員
- **當前操作員顯示**: 更新系統顯示的當前操作員

### 操作流程
1. 點擊頂部「操作員」按鈕
2. 系統自動載入操作員列表
3. 用戶選擇一位或多位操作員
4. 點擊「確定」按鈕確認選擇
5. 系統驗證選擇並更新顯示

## API 介面

### 後端 API
- **方法**: `load_processor`
- **參數**: 空字串
- **回應格式**:
```json
{
  "success": true,
  "data": [
    {
      "account": "操作員帳號",
      "name": "操作員姓名",
      "checked": true/false
    }
  ]
}
```

### 前端函數

#### `showOperatorPanel()`
顯示操作員選擇面板並載入操作員列表。

#### `hideOperatorPanel()`
隱藏操作員面板並清除選擇狀態。

#### `loadOperatorList()`
呼叫後端 API 載入操作員列表。

#### `updateOperatorList(operatorList)`
更新操作員列表的顯示內容。

#### `confirmOperatorSelection()`
確認操作員選擇，驗證至少選擇一位操作員。

## UI 元件

### HTML 結構
```html
<div class="operator-panel" id="operatorPanel">
  <div class="operator-label">操作員</div>
  <div class="operator-buttons">
    <button class="operator-btn" id="btnOperator_OK">確定</button>
    <button class="operator-btn" id="btnOperator_Cancel">取消</button>
  </div>
  <div class="operator-select">
    <table class="scroll-table">
      <thead>
        <tr>
          <th>選擇</th>
          <th>操作員</th>
        </tr>
      </thead>
      <tbody id="operator-list">
        <!-- 動態生成的操作員列表 -->
      </tbody>
    </table>
  </div>
</div>
```

### CSS 樣式
- **面板樣式**: 居中顯示的彈出式面板
- **表格樣式**: 可滾動的表格，支援懸停效果
- **按鈕樣式**: 統一的按鈕設計，支援禁用狀態

## 事件處理

### 按鈕事件
- **操作員按鈕**: 顯示操作員選擇面板
- **確定按鈕**: 確認選擇並關閉面板
- **取消按鈕**: 取消選擇並關閉面板

### 驗證邏輯
- 檢查是否至少選擇一位操作員
- 顯示相應的錯誤訊息
- 成功時更新當前操作員顯示

## 錯誤處理

### 常見錯誤情況
1. **API 未初始化**: 顯示「系統未初始化」訊息
2. **載入失敗**: 顯示具體的錯誤訊息
3. **未選擇操作員**: 提示「請至少選擇一位操作員」
4. **解析錯誤**: 顯示「載入操作員列表失敗」

### 錯誤訊息顯示
使用現有的 `showAlert()` 函數顯示錯誤訊息，確保與系統其他部分的一致性。

## 整合說明

### 與現有系統的整合
- 使用現有的 API 物件進行後端通訊
- 整合現有的錯誤處理機制
- 使用統一的 UI 樣式和訊息顯示

### 資料流
1. 用戶點擊操作員按鈕
2. 前端呼叫 `api.load_processor()`
3. 後端返回操作員列表
4. 前端更新 UI 顯示
5. 用戶選擇操作員
6. 前端驗證並更新系統狀態

## 使用方式

### 基本使用
```javascript
// 顯示操作員面板
showOperatorPanel();

// 隱藏操作員面板
hideOperatorPanel();

// 載入操作員列表
loadOperatorList();
```

### 自訂操作
可以修改 `confirmOperatorSelection()` 函數來添加自訂的後端 API 調用，用於保存選擇的操作員資訊。

## 注意事項

1. **API 依賴**: 需要後端提供 `load_processor` API
2. **權限控制**: 可能需要根據用戶權限限制可選擇的操作員
3. **資料同步**: 選擇的操作員資訊可能需要同步到後端
4. **UI 響應**: 面板會覆蓋在主視窗上方，確保 z-index 設定正確

## 版本資訊
- **版本**: 1.0.0
- **建立日期**: 2024年
- **相容性**: 支援現代瀏覽器
