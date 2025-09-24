/**
 * HTML 訊息彈出視窗系統
 * 使用方式: showMsg(mode, title, message)
 * mode: 1=警示, 2=訊息, 3=成功
 */

console.log('開始載入 htmlMsgBox');

// 檢查是否已經載入過
if (typeof window.showMsg === 'function') {
    console.log('showMsg 函數已存在，跳過載入');
} else {
    // 創建訊息視窗 HTML
    function createMsgBox() {
        const msgBoxHTML = `
            <div id="msgbox-overlay" class="msgbox-overlay">
                <div class="msgbox-container">
                    <div class="msgbox-header">
                        <div class="msgbox-icon">
                            <svg class="msgbox-icon-svg" viewBox="0 0 24 24" fill="currentColor">
                                <!-- 圖標將由 JavaScript 動態設定 -->
                            </svg>
                        </div>
                        <h2 class="msgbox-title"></h2>
                    </div>
                    <div class="msgbox-content">
                        <p class="msgbox-message"></p>
                    </div>
                    <div class="msgbox-footer">
                        <button class="msgbox-btn msgbox-btn-confirm">確定</button>
                    </div>
                </div>
            </div>
        `;
        
        // 如果已經存在，先移除
        const existingOverlay = document.getElementById('msgbox-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }
        
        // 添加到 body
        document.body.insertAdjacentHTML('beforeend', msgBoxHTML);
    }
    
    // 設定圖標
    function setIcon(mode) {
        const iconSvg = document.querySelector('.msgbox-icon-svg');
        if (!iconSvg) return;
        
        let iconPath = '';
        let iconClass = '';
        let iconColor = '';
        
        switch(mode) {
            case 1: // 警示 - 警告圖標
                iconPath = 'M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z';
                iconClass = 'msgbox-icon-warning';
                iconColor = '#ff9800';
                break;
            case 2: // 訊息 - 信息圖標
                iconPath = 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z';
                iconClass = 'msgbox-icon-info';
                iconColor = '#2196f3';
                break;
            case 3: // 成功 - 勾選圖標
                iconPath = 'M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z';
                iconClass = 'msgbox-icon-success';
                iconColor = '#4caf50';
                break;
            default:
                iconPath = 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z';
                iconClass = 'msgbox-icon-info';
                iconColor = '#2196f3';
        }
        
        console.log('設定圖標:', mode, iconClass, iconColor);
        
        // 設定圖標路徑和顏色
        iconSvg.innerHTML = `<path d="${iconPath}" fill="${iconColor}"/>`;
        
        // 移除舊的類別並添加新的
        iconSvg.className = `msgbox-icon-svg ${iconClass}`;
        
        // 直接設定 SVG 的 fill 屬性
        iconSvg.style.fill = iconColor;
        iconSvg.style.color = iconColor;
    }
    
    // 設定容器樣式
    function setContainerStyle(mode) {
        const container = document.querySelector('.msgbox-container');
        if (!container) return;
        
        // 移除舊的樣式類別
        container.classList.remove('msgbox-warning', 'msgbox-info', 'msgbox-success');
        
        // 添加新的樣式類別
        switch(mode) {
            case 1:
                container.classList.add('msgbox-warning');
                break;
            case 2:
                container.classList.add('msgbox-info');
                break;
            case 3:
                container.classList.add('msgbox-success');
                break;
        }
    }
    
    // 顯示訊息視窗
    function showMsg(mode, title, message) {
        // 參數驗證
        if (typeof mode !== 'number' || mode < 1 || mode > 3) {
            mode = 2; // 預設為訊息模式
        }
        
        if (typeof title !== 'string') {
            title = '訊息';
        }
        
        if (typeof message !== 'string') {
            message = '沒有訊息內容';
        }
        
        console.log('顯示訊息:', mode, title, message);
        
        // 創建視窗
        createMsgBox();
        
        // 設定內容
        document.querySelector('.msgbox-title').textContent = title;
        document.querySelector('.msgbox-message').textContent = message;
        
        // 設定圖標和樣式
        setIcon(mode);
        setContainerStyle(mode);
        
        // 顯示視窗
        const overlay = document.getElementById('msgbox-overlay');
        overlay.style.display = 'flex';
        
        // 添加動畫效果
        setTimeout(() => {
            overlay.classList.add('msgbox-show');
        }, 10);
        
        // 綁定確定按鈕事件
        const confirmBtn = document.querySelector('.msgbox-btn-confirm');
        confirmBtn.onclick = function() {
            hideMsg();
        };
        
        // 綁定 ESC 鍵關閉
        const escHandler = function(e) {
            if (e.key === 'Escape') {
                hideMsg();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
        
        // 綁定點擊背景關閉
        overlay.onclick = function(e) {
            if (e.target === overlay) {
                hideMsg();
            }
        };
        
        // 聚焦到確定按鈕
        confirmBtn.focus();
    }
    
    // 隱藏訊息視窗
    function hideMsg() {
        const overlay = document.getElementById('msgbox-overlay');
        if (!overlay) return;
        
        // 添加隱藏動畫
        overlay.classList.remove('msgbox-show');
        overlay.classList.add('msgbox-hide');
        
        // 動畫結束後移除元素
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
        }, 300);
    }
    
    // 全域函數
    window.showMsg = showMsg;
    window.hideMsg = hideMsg;
    
    // 導出到全域物件
    window.htmlMsgBox = {
        show: showMsg,
        hide: hideMsg
    };
    
    console.log('htmlMsgBox 載入完成');
    console.log('showMsg 函數已註冊:', typeof window.showMsg);
} 