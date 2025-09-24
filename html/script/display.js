/**
 * display.js - 頁面顯示控制模組
 * 根據傳入的參數控制各頁面中選單和元件的顯示/隱藏狀態
 */

// 全域變數定義

    // 功能模組顯示控制
    const sl_showHistory = true;
    const sl_showCabinet = true;
    const sl_showGroup = true;
    const sl_showMember = true;
    const sl_showRule = true;
    const sl_showLocker = true;
    const sl_showUser = true;
    const sl_showSettings = true;
    const sl_showSetup = true;
    const sl_showWifi = true;
    
    // 操作權限控制
    const sl_canEdit = true;
    const sl_canDelete = true;
    const sl_canAdd = true;
    const sl_canView = true;
    
    // 特殊功能控制
    const sl_showAdminPanel = false;
    const sl_showDebugInfo = false;
    const sl_showAdvancedOptions = false;


$document.ready(function() {
    if (!sl_showHistory && $('#btnKeyHistory').length) {
        $('#btnKeyHistory').hide();
    }
    if (!sl_showCabinet && $('#btnCabinet').length) {
        $('#btnCabinet').hide();
    }
    if (!sl_showGroup && $('#btnGroup').length) {
        $('#btnGroup').hide();
    }
    if (!sl_showMember && $('#btnMember').length) {
        $('#btnMember').hide();
    }
    if (!sl_showRule && $('#btnRule').length) {
        $('#btnRule').hide();
    }
    if (!sl_showLocker && $('#btnLocker').length) {
        $('#btnLocker').hide();
    }
    if (!sl_showUser && $('#btnUser').length) {
        $('#btnUser').hide();
    }
    if (!sl_showSettings && $('#btnParameter').length) {
        $('#btnParameter').hide();
    }
    if (!sl_showSetup && $('#btnSetup').length) {
        $('#btnSetup').hide();
    }
    if (!sl_showWifi && $('#btnWifi').length) {
        $('#btnWifi').hide();
    }
    if (!sl_canEdit && $('.btn-edit').length) {
        $('.btn-edit').hide();
    }
    if (!sl_canDelete && $('.btn-delete').length) {
        $('.btn-delete').hide();
    }
    if (!sl_canAdd && $('.btn-add').length) {
        $('.btn-add').hide();
    }
    if (!sl_canView && $('.btn-view').length) {
        $('.btn-view').hide();
    }
    if (!sl_showAdminPanel && $('.admin-panel').length) {
        $('.admin-panel').hide();
    }
    if (!sl_showDebugInfo && $('.debug-info').length) {
        $('.debug-info').hide();
    }
    if (!sl_showAdvancedOptions && $('.advanced-options').length) {
        $('.advanced-options').hide();
    }
    
});

