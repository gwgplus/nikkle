// 全域變數
let currentState = 'idle'; // idle, processing, success, error
let testCounter = 50;
let ngCounter = 5;

// DOM 載入完成後初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    updateDateTime();
    setInterval(updateDateTime, 1000);
});

// 初始化應用程式
function initializeApp() {
    // 綁定事件監聽器
    bindEventListeners();
    
    // 初始化狀態
    resetAllPanels();
    
    // 更新計數器顯示
    updateCounters();
}

// 綁定事件監聽器
function bindEventListeners() {
    // 條碼輸入框事件
    document.getElementById('txtCode1').addEventListener('input', validateInputs);
    document.getElementById('txtCode2').addEventListener('input', validateInputs);
    
    // 執行檢測按鈕
    document.getElementById('btnStart').addEventListener('click', startDetection);
    
    // 確認按鈕
    document.getElementById('btnSave').addEventListener('click', saveResult);
    
    // 錯誤處理按鈕
    document.getElementById('btnAllow').addEventListener('click', () => handleJudgment('allow'));
    document.getElementById('btnBack').addEventListener('click', () => handleJudgment('back'));
    
    // 錯誤選擇按鈕
    document.getElementById('btnMark').addEventListener('click', () => handleErrorSelect('fold'));
    document.getElementById('btnCheckError').addEventListener('click', () => handleErrorSelect('error'));
    document.getElementById('btnCantOCR').addEventListener('click', () => handleErrorSelect('noOCR'));
    
    // 外觀判定按鈕
    document.getElementById('btnOK').addEventListener('click', () => handleAppearance('ok'));
    document.getElementById('btnNG').addEventListener('click', () => handleAppearance('ng'));
    document.getElementById('btnClass1').addEventListener('click', () => toggleClass('class1'));
    document.getElementById('btnClass2').addEventListener('click', () => toggleClass('class2'));
    
    // 原因選擇按鈕
    document.getElementById('btnReason1').addEventListener('click', () => selectReason('oxidation'));
    document.getElementById('btnReason2').addEventListener('click', () => selectReason('leakage'));
    document.getElementById('btnReason3').addEventListener('click', () => selectReason('foreign'));
    document.getElementById('btnReason4').addEventListener('click', () => selectReason('hole'));
    
    // 鍵盤事件
    document.addEventListener('keydown', handleKeyDown);
}

// 更新日期時間
function updateDateTime() {
    const now = new Date();
    document.getElementById('currentDate').textContent = now.toLocaleDateString('zh-TW');
    document.getElementById('currentTime').textContent = now.toLocaleTimeString('zh-TW');
}

// 驗證輸入
function validateInputs() {
    const code1 = document.getElementById('txtCode1').value;
    const code2 = document.getElementById('txtCode2').value;
    const startBtn = document.getElementById('btnStart');
    
    if (code1.length > 0 && code2.length > 0 && code1 === code2) {
        startBtn.disabled = false;
        startBtn.style.opacity = '1';
    } else {
        startBtn.disabled = true;
        startBtn.style.opacity = '0.5';
    }
}

// 開始檢測
function startDetection() {
    const code1 = document.getElementById('txtCode1').value;
    const code2 = document.getElementById('txtCode2').value;
    
    if (code1 !== code2) {
        showAlert('條碼不一致');
        return;
    }
    
    // 更新狀態
    currentState = 'processing';
    testCounter++;
    
    // 顯示條碼
    document.getElementById('lblBarCode1').textContent = code1;
    document.getElementById('lblBarCode2').textContent = code2;
    document.getElementById('lblBarCode1').style.display = 'block';
    document.getElementById('lblBarCode2').style.display = 'block';
    
    // 禁用輸入
    document.getElementById('txtCode1').readOnly = true;
    document.getElementById('txtCode2').readOnly = true;
    document.getElementById('btnStart').disabled = true;
    
    // 模擬檢測過程
    simulateDetection();
}

// 模擬檢測過程
function simulateDetection() {
    const ocrResult = document.getElementById('txtOCRResult');
    const code1 = document.getElementById('txtCode1').value;
    
    // 模擬檢測步驟
    setTimeout(() => {
        ocrResult.value = '登入並觸發拍照';
    }, 500);
    
    setTimeout(() => {
        ocrResult.value = '等待FTP圖檔';
    }, 1500);
    
    setTimeout(() => {
        ocrResult.value = '取得OCR結果';
    }, 2500);
    
    setTimeout(() => {
        // 模擬OCR結果
        const randomResult = Math.random() > 0.3 ? code1 : 'OCR_ERROR_' + Math.random().toString(36).substr(2, 8);
        ocrResult.value = randomResult;
        
        // 判斷結果
        if (randomResult === code1) {
            showSuccess();
        } else {
            showError();
        }
    }, 3500);
}

// 顯示成功結果
function showSuccess() {
    currentState = 'success';
    resetAllPanels();
    showPanel('okPanel');
    
    // 顯示Halcon標籤（隨機）
    if (Math.random() > 0.5) {
        document.getElementById('halconLabel').style.display = 'block';
    }
    
    // 自動重置
    setTimeout(() => {
        resetForm();
    }, 3000);
}

// 顯示錯誤結果
function showError() {
    currentState = 'error';
    ngCounter++;
    resetAllPanels();
    showPanel('errorPanel');
    updateCounters();
}

// 顯示警告
function showAlert(message) {
    document.getElementById('alertMessage').textContent = message;
    showPanel('alertPanel');
    
    setTimeout(() => {
        hidePanel('alertPanel');
    }, 3000);
}

// 處理判定
function handleJudgment(type) {
    if (type === 'allow') {
        document.getElementById('judgmentText').textContent = '判定為允收';
        document.getElementById('judgmentText').style.display = 'block';
        showPanel('errorSelectPanel');
    } else if (type === 'back') {
        document.getElementById('judgmentText').textContent = '請退回前工程';
        document.getElementById('judgmentText').style.display = 'block';
        showPanel('appearancePanel');
    }
}

// 處理錯誤選擇
function handleErrorSelect(type) {
    const selectText = document.getElementById('selectText');
    
    switch(type) {
        case 'fold':
            selectText.textContent = '判定 摺痕';
            break;
        case 'error':
            selectText.textContent = '判定 辨識錯誤';
            break;
        case 'noOCR':
            selectText.textContent = '判定 無法辯識';
            break;
    }
    
    selectText.style.display = 'block';
    showPanel('appearancePanel');
}

// 處理外觀判定
function handleAppearance(type) {
    const okBtn = document.getElementById('btnOK');
    const ngBtn = document.getElementById('btnNG');
    
    // 移除所有active類別
    okBtn.classList.remove('active');
    ngBtn.classList.remove('active');
    
    if (type === 'ok') {
        okBtn.classList.add('active');
        hidePanel('reasonPanel');
    } else if (type === 'ng') {
        ngBtn.classList.add('active');
        showPanel('reasonPanel');
    }
}

// 切換類別
function toggleClass(className) {
    const btn = document.getElementById('btn' + className.charAt(0).toUpperCase() + className.slice(1));
    btn.classList.toggle('active');
}

// 選擇原因
function selectReason(reason) {
    const reasonBtns = document.querySelectorAll('.reason-btn');
    reasonBtns.forEach(btn => btn.classList.remove('active'));
    
    const btnMap = {
        'oxidation': 'btnReason1',
        'leakage': 'btnReason2',
        'foreign': 'btnReason3',
        'hole': 'btnReason4'
    };
    
    document.getElementById(btnMap[reason]).classList.add('active');
}

// 儲存結果
function saveResult() {
    // 模擬儲存過程
    console.log('儲存檢測結果...');
    
    // 重置表單
    resetForm();
}

// 重置表單
function resetForm() {
    document.getElementById('txtCode1').value = '';
    document.getElementById('txtCode2').value = '';
    document.getElementById('txtOCRResult').value = '';
    document.getElementById('lblBarCode1').style.display = 'none';
    document.getElementById('lblBarCode2').style.display = 'none';
    
    document.getElementById('txtCode1').readOnly = false;
    document.getElementById('txtCode2').readOnly = false;
    document.getElementById('btnStart').disabled = false;
    
    resetAllPanels();
    currentState = 'idle';
}

// 重置所有面板
function resetAllPanels() {
    const panels = [
        'alertPanel', 'okPanel', 'errorPanel', 
        'errorSelectPanel', 'appearancePanel', 'reasonPanel'
    ];
    
    panels.forEach(panel => {
        hidePanel(panel);
    });
    
    // 重置按鈕狀態
    document.querySelectorAll('.appearance-btn, .class-btn, .reason-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 隱藏文字
    document.getElementById('judgmentText').style.display = 'none';
    document.getElementById('selectText').style.display = 'none';
    document.getElementById('halconLabel').style.display = 'none';
    
}

// 顯示面板
function showPanel(panelId) {
    const panel = document.getElementById(panelId);
    if (panel) {
        panel.style.display = 'block';
        panel.classList.add('panel-enter');
    }
}

// 隱藏面板
function hidePanel(panelId) {
    const panel = document.getElementById(panelId);
    if (panel) {
        panel.classList.add('panel-exit');
        setTimeout(() => {
            panel.style.display = 'none';
            panel.classList.remove('panel-exit');
        }, 300);
    }
}

// 更新計數器
function updateCounters() {
    document.getElementById('totalCount').textContent = testCounter;
    document.getElementById('ngCount').textContent = ngCounter;
}

// 鍵盤事件處理
function handleKeyDown(event) {
    if (event.key === 'Enter') {
        if (document.activeElement.id === 'txtCode1') {
            document.getElementById('txtCode2').focus();
        } else if (document.activeElement.id === 'txtCode2') {
            if (!document.getElementById('btnStart').disabled) {
                startDetection();
            }
        }
    }
}

// 影像面板點擊事件
document.getElementById('imagePanel').addEventListener('click', function(event) {
    if (currentState === 'processing') {
        // 模擬影像處理
        console.log('影像面板被點擊:', event.offsetX, event.offsetY);
    }
});

// 視窗大小改變事件
window.addEventListener('resize', function() {
    // 重新計算佈局
    console.log('視窗大小改變');
});

// 匯出功能
function exportData() {
    console.log('匯出檢測資料...');
    // 這裡可以實現資料匯出功能
}

// 設定功能
function openSettings() {
    console.log('開啟設定...');
    // 這裡可以實現設定功能
}

// 帳號管理
function openAccountManagement() {
    console.log('開啟帳號管理...');
    // 這裡可以實現帳號管理功能
}

// 操作員管理
function openOperatorManagement() {
    console.log('開啟操作員管理...');
    // 這裡可以實現操作員管理功能
}

// 基準圖像登錄
function openImageRegistration() {
    console.log('開啟基準圖像登錄...');
    // 這裡可以實現基準圖像登錄功能
}

// 全域函數供HTML調用
window.exportData = exportData;
window.openSettings = openSettings;
window.openAccountManagement = openAccountManagement;
window.openOperatorManagement = openOperatorManagement;
window.openImageRegistration = openImageRegistration; 