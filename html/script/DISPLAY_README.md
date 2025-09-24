# Display.js 使用說明

## 概述

`display.js` 是一個頁面顯示控制模組，用於根據傳入的參數控制各頁面中選單和元件的顯示/隱藏狀態。它使用 jQuery 來操作 DOM 元素，並在頁面載入後自動套用顯示設定。

## 功能特點

### 🎯 核心功能
- **選單項目控制**：控制各種功能選單的顯示/隱藏
- **操作權限控制**：控制編輯、刪除、新增、檢視等操作按鈕的啟用/禁用
- **特殊功能控制**：控制管理員面板、除錯資訊、進階選項等特殊功能的顯示
- **角色基礎權限**：提供預設的管理員、使用者、訪客三種角色權限設定

### 🔧 技術特點
- 使用 jQuery 進行 DOM 操作
- 支援多種選擇器（ID、Class、data 屬性）
- 自動等待 DOM 載入完成
- 提供全域函數供其他頁面調用

## 安裝與使用

### 1. 引入檔案
```html
<script src="script/jquery-3.7.1.slim.min.js"></script>
<script src="script/display.js"></script>
```

### 2. 基本使用
```javascript
$(document).ready(function() {
    // 初始化顯示控制
    initDisplayControl();
});
```

## 配置參數

### 功能模組顯示控制
| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `showHistory` | boolean | true | 是否顯示歷史記錄選單 |
| `showCabinet` | boolean | true | 是否顯示櫃位管理選單 |
| `showGroup` | boolean | true | 是否顯示群組管理選單 |
| `showMember` | boolean | true | 是否顯示會員管理選單 |
| `showRule` | boolean | true | 是否顯示規則管理選單 |
| `showLocker` | boolean | true | 是否顯示鎖櫃管理選單 |
| `showUser` | boolean | true | 是否顯示使用者功能選單 |
| `showSettings` | boolean | true | 是否顯示設定選單 |
| `showSetup` | boolean | true | 是否顯示系統設定選單 |
| `showWifi` | boolean | true | 是否顯示WiFi設定選單 |

### 操作權限控制
| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `canEdit` | boolean | true | 是否允許編輯操作 |
| `canDelete` | boolean | true | 是否允許刪除操作 |
| `canAdd` | boolean | true | 是否允許新增操作 |
| `canView` | boolean | true | 是否允許檢視操作 |

### 特殊功能控制
| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `showAdminPanel` | boolean | false | 是否顯示管理員面板 |
| `showDebugInfo` | boolean | false | 是否顯示除錯資訊 |
| `showAdvancedOptions` | boolean | false | 是否顯示進階選項 |

## API 函數

### 主要函數

#### `initDisplayControl(config)`
初始化顯示控制模組
```javascript
// 基本初始化
initDisplayControl();

// 帶參數初始化
initDisplayControl({
    showHistory: false,
    showCabinet: true,
    canEdit: false
});
```

#### `updateDisplayConfig(newConfig)`
動態更新顯示設定
```javascript
updateDisplayConfig({
    showHistory: false,
    canEdit: true
});
```

#### `getDisplayConfig()`
取得目前顯示配置
```javascript
const config = getDisplayConfig();
console.log('目前設定:', config);
```

#### `resetDisplayConfig()`
重置顯示配置為預設值
```javascript
resetDisplayConfig();
```

#### `setDisplayByRole(role)`
根據使用者角色設定顯示權限
```javascript
// 可用的角色：'admin', 'user', 'guest'
setDisplayByRole('admin');
setDisplayByRole('user');
setDisplayByRole('guest');
```

## HTML 元素標記

### 選單項目
使用以下任一方式標記選單項目：

```html
<!-- 使用按鈕 ID (推薦) -->
<button type="button" class="btn btn-admin" id="btnKeyHistory">歷史記錄</button>
<button type="button" class="btn btn-admin" id="btnCabinet">櫃位管理</button>
<button type="button" class="btn btn-admin" id="btnGroup">群組管理</button>
<button type="button" class="btn btn-admin" id="btnMember">會員管理</button>
<button type="button" class="btn btn-admin" id="btnRule">規則管理</button>
<button type="button" class="btn btn-admin" id="btnLocker">鎖櫃管理</button>
<button type="button" class="btn btn-admin" id="btnUser">使用者功能</button>
<button type="button" class="btn btn-admin" id="btnSettings">設定</button>
<button type="button" class="btn btn-admin" id="btnSetup">系統設定</button>
<button type="button" class="btn btn-admin" id="btnWifi">WiFi設定</button>

<!-- 使用一般 ID -->
<div id="menu-history">歷史記錄</div>

<!-- 使用 Class -->
<div class="menu-history">歷史記錄</div>

<!-- 使用 data 屬性 -->
<div data-menu="history">歷史記錄</div>
```

### 操作按鈕
使用以下任一方式標記操作按鈕：

```html
<!-- 使用 Class -->
<button class="btn-edit">編輯</button>
<button class="btn-delete">刪除</button>
<button class="btn-add">新增</button>
<button class="btn-view">檢視</button>

<!-- 使用 data 屬性 -->
<button data-action="edit">編輯</button>
<button data-action="delete">刪除</button>
<button data-action="add">新增</button>
<button data-action="view">檢視</button>
```

### 特殊功能區域
使用以下方式標記特殊功能區域：

```html
<!-- 管理員面板 -->
<div class="admin-panel" data-admin="true">
    管理員專用內容
</div>

<!-- 除錯資訊 -->
<div class="debug-info" data-debug="true">
    除錯資訊內容
</div>

<!-- 進階選項 -->
<div class="advanced-options" data-advanced="true">
    進階選項內容
</div>
```

## 使用範例

### 1. 基本頁面使用
```html
<!DOCTYPE html>
<html>
<head>
    <script src="script/jquery-3.7.1.slim.min.js"></script>
    <script src="script/display.js"></script>
</head>
<body>
    <!-- 選單項目 (使用按鈕樣式) -->
    <button type="button" class="btn btn-admin" id="btnKeyHistory">
        <div class="icon-bg">
            <svg class="nav-icon">...</svg>
        </div>
        <span>歷史記錄</span>
    </button>
    <button type="button" class="btn btn-admin" id="btnCabinet">
        <div class="icon-bg">
            <svg class="nav-icon">...</svg>
        </div>
        <span>櫃位管理</span>
    </button>
    
    <!-- 操作按鈕 -->
    <button class="btn-edit">編輯</button>
    <button class="btn-delete">刪除</button>
    
    <script>
        $(document).ready(function() {
            // 初始化顯示控制
            initDisplayControl({
                showHistory: false,
                canEdit: false
            });
        });
    </script>
</body>
</html>
```

### 2. 角色基礎權限
```javascript
// 根據登入的使用者角色設定權限
function setUserPermissions(userRole) {
    setDisplayByRole(userRole);
}

// 使用範例
setUserPermissions('admin');  // 管理員權限
setUserPermissions('user');   // 使用者權限
setUserPermissions('guest');  // 訪客權限
```

### 3. 動態權限控制
```javascript
// 根據某些條件動態調整權限
function updatePermissions(hasEditPermission, hasAdminAccess) {
    updateDisplayConfig({
        canEdit: hasEditPermission,
        showAdminPanel: hasAdminAccess
    });
}
```

## 角色權限對照表

### 管理員 (admin)
- ✅ 所有功能模組顯示
- ✅ 所有操作權限
- ✅ 特殊功能顯示

### 使用者 (user)
- ✅ 歷史記錄、鎖櫃管理、使用者功能
- ❌ 櫃位管理、群組管理、會員管理、規則管理
- ❌ 設定、系統設定、WiFi設定
- ❌ 編輯、刪除、新增權限
- ✅ 檢視權限
- ❌ 特殊功能

### 訪客 (guest)
- ❌ 所有功能模組
- ❌ 所有操作權限
- ❌ 特殊功能

## 注意事項

1. **jQuery 依賴**：必須先載入 jQuery 再載入 display.js
2. **DOM 載入**：建議在 `$(document).ready()` 中初始化
3. **選擇器優先級**：ID > Class > data 屬性
4. **CSS 樣式**：按鈕禁用時會自動添加 `disabled` class
5. **全域函數**：所有函數都會暴露到 `window` 物件

## 故障排除

### 常見問題

**Q: 選單項目沒有隱藏？**
A: 檢查 HTML 元素是否使用了正確的 ID、Class 或 data 屬性

**Q: 按鈕沒有禁用？**
A: 確認按鈕有正確的 class 或 data-action 屬性

**Q: 函數未定義？**
A: 確認 display.js 已正確載入，且載入順序正確

### 除錯技巧
```javascript
// 檢查目前配置
console.log(getDisplayConfig());

// 檢查元素是否存在
console.log($('#menu-history').length);
console.log($('.btn-edit').length);
``` 