/**
 * Canvas 圖片處理模組
 * 負責處理圖片顯示、繪製、縮放、旋轉等功能
 */

// 圖片操作相關變數
let canvas = null;
let ctx = null;
let currentImage = null;
let workStatus = "none"; // none, drawing, normal, startScale, zoomAndRotate
let startPoint = { x: 0, y: 0 };
let endPoint = { x: 0, y: 0 };
let scale = 1.0;
let offsetX = 0;
let offsetY = 0;
let angle = 0;
let rate = 1.0;

/**
 * 初始化 Canvas
 */
function initCanvas() {
  canvas = document.getElementById("imageCanvas");
  ctx = canvas.getContext("2d");

  // 設定 Canvas 樣式
  canvas.style.display = "none";
  canvas.style.border = "1px solid #ccc";

  // 動態調整 Canvas 尺寸以填滿容器
  resizeCanvasToFill();

  // 綁定滑鼠事件
  canvas.addEventListener("mousedown", handleMouseDown);
  canvas.addEventListener("mouseup", handleMouseUp);
  canvas.addEventListener("mousemove", handleMouseMove);

  // 監聽視窗大小變化
  window.addEventListener("resize", resizeCanvasToFill);

  // 左鍵連按兩下事件（備用功能）
  canvas.addEventListener("dblclick", function (e) {
    if (workStatus === "zoomAndRotate" || workStatus === "startScale") {
      workStatus = "normal";
      drawImage();
    }
  });

  // 禁用右鍵選單
  canvas.addEventListener("contextmenu", function (e) {
    e.preventDefault();
    return false;
  });

  // 為整個頁面禁用右鍵選單（確保不會出現瀏覽器選單）
  document.addEventListener("contextmenu", function (e) {
    e.preventDefault();
    return false;
  });
}

/**
 * 動態調整 Canvas 尺寸以填滿容器
 */
function resizeCanvasToFill() {
  const imagePanel = document.getElementById("imagePanel");
  if (!imagePanel) return;

  const rect = imagePanel.getBoundingClientRect();
  const panelWidth = rect.width;
  const panelHeight = rect.height;

  // 設定 Canvas 的實際繪製尺寸等於容器尺寸
  canvas.width = Math.floor(panelWidth);
  canvas.height = Math.floor(panelHeight);

  // 重新繪製
  if (currentImage) {
    drawImage();
  }
}

/**
 * 顯示圖片
 * @param {string} imagePath - 圖片路徑
 * @param {Object} scaleParams - 縮放參數 {scale, offsetX, offsetY}
 */
function showImage(imagePath, scaleParams = null) {
  if (!imagePath) {
    alert("圖片路徑不存在");
    showNoImage();
    return;
  }

  // 修復路徑格式，將反斜線轉換為正斜線
  const fixedPath = imagePath.replace(/\\/g, "/");
  console.log("原始路徑:", imagePath);
  console.log("修復後路徑:", fixedPath);
  
  // 如果有傳入縮放參數，則應用它們
  if (scaleParams) {
    scale = scaleParams.scale || 1.0;
    offsetX = scaleParams.offsetX || 0;
    offsetY = scaleParams.offsetY || 0;
    console.log("應用縮放參數:", {scale, offsetX, offsetY});
  }
  
  const img = new Image();
  img.onload = function () {
    currentImage = img;
    // OCR 完成後，圖片載入時直接進入 StartScale 狀態
    workStatus = "startScale";
    canvas.style.display = "block";
    document.getElementById("imagePlaceholder").style.display = "none";

    // 重新調整 Canvas 尺寸
    resizeCanvasToFill();
    drawImage();
    
    console.log("圖片載入完成，進入 StartScale 狀態，縮放參數:", {scale, offsetX, offsetY});
  };
  img.onerror = function () {
    console.error("圖片載入失敗:", fixedPath);
    console.error("原始路徑:", imagePath);
    showNoImage();
  };
  img.src = fixedPath;
}

/**
 * 顯示無圖片狀態
 */
function showNoImage() {
  workStatus = "none";
  currentImage = null;
  canvas.style.display = "none";
  document.getElementById("imagePlaceholder").style.display = "block";
}

/**
 * 繪製圖片
 */
function drawImage() {
  if (!currentImage) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  switch (workStatus) {
    case "none":
      drawNoImageState();
      break;

    case "drawing":
    case "normal":
      drawNormalImage();
      if (workStatus === "drawing") {
        drawDrawingLine();
      }
      break;

    case "startScale":
      drawScaledImage();
      break;

    case "zoomAndRotate":
      drawRotatedImage();
      break;
  }
}

/**
 * 繪製無圖片狀態
 */
function drawNoImageState() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#d3d3d3";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "#0066cc";
  ctx.font = "32px 微軟正黑體";
  ctx.fontWeight = "bold";

  const text = "目前沒有影像";
  const textMetrics = ctx.measureText(text);
  const textX = (canvas.width - textMetrics.width) / 2;
  const textY = canvas.height / 2;

  ctx.fillText(text, textX, textY);
}

/**
 * 繪製正常圖片（Normal 狀態）
 */
function drawNormalImage() {
  if (!currentImage) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 計算圖片的最佳顯示尺寸（填滿 Canvas）
  const canvasAspectRatio = canvas.width / canvas.height;
  const imageAspectRatio = currentImage.width / currentImage.height;

  let drawWidth, drawHeight, imageOffsetX, imageOffsetY;

  if (canvasAspectRatio > imageAspectRatio) {
    // Canvas 較寬，以高度填滿
    drawHeight = canvas.height;
    drawWidth = canvas.height * imageAspectRatio;
    imageOffsetX = (canvas.width - drawWidth) / 2;
    imageOffsetY = 0;
  } else {
    // Canvas 較高，以寬度填滿
    drawWidth = canvas.width;
    drawHeight = canvas.width / imageAspectRatio;
    imageOffsetX = 0;
    imageOffsetY = (canvas.height - drawHeight) / 2;
  }

  // 繪製圖片（居中顯示）
  ctx.drawImage(currentImage, imageOffsetX, imageOffsetY, drawWidth, drawHeight);

  // 更新縮放比例
  rate = drawWidth / currentImage.width;
  
  console.log("Normal 狀態：圖片居中顯示");
}

/**
 * 繪製繪製中的線條（Drawing 狀態）
 */
function drawDrawingLine() {
  ctx.strokeStyle = "#ff0000";
  ctx.lineWidth = 3;
  ctx.beginPath();

  // 計算圖片在 Canvas 中的實際位置
  const canvasAspectRatio = canvas.width / canvas.height;
  const imageAspectRatio = currentImage.width / currentImage.height;

  let drawWidth, drawHeight, imageOffsetX, imageOffsetY;

  if (canvasAspectRatio > imageAspectRatio) {
    drawHeight = canvas.height;
    drawWidth = canvas.height * imageAspectRatio;
    imageOffsetX = (canvas.width - drawWidth) / 2;
    imageOffsetY = 0;
  } else {
    drawWidth = canvas.width;
    drawHeight = canvas.width / imageAspectRatio;
    imageOffsetX = 0;
    imageOffsetY = (canvas.height - drawHeight) / 2;
  }

  // 將滑鼠座標轉換為圖片座標系統
  const imageStartX = (startPoint.x - imageOffsetX) / rate;
  const imageStartY = (startPoint.y - imageOffsetY) / rate;
  const imageEndX = (endPoint.x - imageOffsetX) / rate;
  const imageEndY = (endPoint.y - imageOffsetY) / rate;

  // 繪製紅色線條
  ctx.moveTo(imageOffsetX + imageStartX * rate, imageOffsetY + imageStartY * rate);
  ctx.lineTo(imageOffsetX + imageEndX * rate, imageOffsetY + imageEndY * rate);
  ctx.stroke();
  
  console.log(`Drawing 狀態：繪製紅色線條從 (${startPoint.x}, ${startPoint.y}) 到 (${endPoint.x}, ${endPoint.y})`);
}

/**
 * 繪製縮放圖片（StartScale 狀態）
 */
function drawScaledImage() {
  if (!currentImage) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 計算縮放後的圖片尺寸
  const scaledWidth = currentImage.width * scale;
  const scaledHeight = currentImage.height * scale;

  // 計算圖片在 Canvas 中的位置（考慮 offset）
  const imageX = -offsetX;
  const imageY = -offsetY;

  // 繪製縮放後的圖片
  ctx.drawImage(currentImage, imageX, imageY, scaledWidth, scaledHeight);
  
  console.log(`StartScale 狀態：scale=${scale}, offsetX=${offsetX}, offsetY=${offsetY}`);
}

/**
 * 繪製旋轉圖片（ZoomAndRotate 狀態）
 */
function drawRotatedImage() {
  if (!currentImage) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 計算圖片在 Canvas 中的實際位置和尺寸
  const canvasAspectRatio = canvas.width / canvas.height;
  const imageAspectRatio = currentImage.width / currentImage.height;

  let drawWidth, drawHeight, imageOffsetX, imageOffsetY;

  if (canvasAspectRatio > imageAspectRatio) {
    drawHeight = canvas.height;
    drawWidth = canvas.height * imageAspectRatio;
    imageOffsetX = (canvas.width - drawWidth) / 2;
    imageOffsetY = 0;
  } else {
    drawWidth = canvas.width;
    drawHeight = canvas.width / imageAspectRatio;
    imageOffsetX = 0;
    imageOffsetY = (canvas.height - drawHeight) / 2;
  }

  // 將滑鼠座標轉換為原圖座標系統
  const imageStartX = (startPoint.x - imageOffsetX) / rate;
  const imageStartY = (startPoint.y - imageOffsetY) / rate;
  const imageEndX = (endPoint.x - imageOffsetX) / rate;
  const imageEndY = (endPoint.y - imageOffsetY) / rate;

  // 計算畫線的中央點在原圖中的位置
  const centerPoint = {
    x: (imageStartX + imageEndX) / 2,
    y: (imageStartY + imageEndY) / 2,
  };

  // 計算旋轉後原圖的顯示區域
  const rotatedImageWidth = currentImage.width;
  const rotatedImageHeight = currentImage.height;

  // 計算旋轉後原圖在 Canvas 中的顯示位置
  const targetCenterX = canvas.width / 2;
  const targetCenterY = canvas.height / 2;

  // 計算旋轉後原圖的左上角位置，使紅線中心點位於 Canvas 正中間
  const rotatedOffsetX = targetCenterX - centerPoint.x;
  const rotatedOffsetY = targetCenterY - centerPoint.y;

  ctx.save();

  // 移動到 Canvas 正中間
  ctx.translate(targetCenterX, targetCenterY);

  // 旋轉
  ctx.rotate((-angle * Math.PI) / 180);

  // 移動回原點
  ctx.translate(-targetCenterX, -targetCenterY);

  // 繪製旋轉後的原圖（保持原尺寸，不縮放）
  ctx.drawImage(
    currentImage,
    rotatedOffsetX,
    rotatedOffsetY,
    rotatedImageWidth,
    rotatedImageHeight
  );

  ctx.restore();
  
  console.log(`ZoomAndRotate 狀態：角度=${angle}度，中心點=(${centerPoint.x}, ${centerPoint.y})`);
}

/**
 * 滑鼠按下事件
 * @param {MouseEvent} e - 滑鼠事件
 */
function handleMouseDown(e) {
  if (e.button === 0) {
    // 左鍵
    if (workStatus === "none") return;

    if (workStatus === "startScale") {
      // 在 StartScale 狀態下按左鍵：轉換到 Normal 狀態
      workStatus = "normal";
      console.log("從 StartScale 轉換到 Normal 狀態");
      drawImage();
      return;
    }

    if (workStatus === "normal") {
      // 在 Normal 狀態下按左鍵：開始畫線（Drawing 狀態）
      const rect = canvas.getBoundingClientRect();
      startPoint = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
      endPoint = { ...startPoint };
      workStatus = "drawing";
      console.log("開始畫線，起始點:", startPoint);
      drawImage();
    }

    if (workStatus === "zoomAndRotate") {
      // 在 ZoomAndRotate 狀態下按左鍵：回到 Normal 狀態
      workStatus = "normal";
      console.log("從 ZoomAndRotate 轉換到 Normal 狀態");
      drawImage();
      return;
    }
  } else if (e.button === 2) {
    // 右鍵
    if (workStatus === "startScale") {
      // 在 StartScale 狀態下按右鍵：轉換到 Normal 狀態
      workStatus = "normal";
      console.log("右鍵點擊：從 StartScale 轉換到 Normal 狀態");
      drawImage();
    } else if (workStatus === "zoomAndRotate") {
      // 在 ZoomAndRotate 狀態下按右鍵：回到 Normal 狀態
      workStatus = "normal";
      console.log("右鍵點擊：從 ZoomAndRotate 轉換到 Normal 狀態");
      drawImage();
    }
  }
}

/**
 * 滑鼠放開事件
 * @param {MouseEvent} e - 滑鼠事件
 */
function handleMouseUp(e) {
  if (workStatus !== "drawing") return;

  // 完成畫線，計算角度並進入 ZoomAndRotate 狀態
  if (startPoint.x !== endPoint.x || startPoint.y !== endPoint.y) {
    const xDiff = endPoint.x - startPoint.x;
    const yDiff = endPoint.y - startPoint.y;
    angle = (Math.atan2(yDiff, xDiff) * 180) / Math.PI;
    workStatus = "zoomAndRotate";
    console.log("完成畫線，角度:", angle, "轉換到 ZoomAndRotate 狀態");
    drawImage();
  } else {
    // 如果起始點和結束點相同，回到 Normal 狀態
    workStatus = "normal";
    console.log("起始點和結束點相同，回到 Normal 狀態");
    drawImage();
  }
}

/**
 * 滑鼠移動事件
 * @param {MouseEvent} e - 滑鼠事件
 */
function handleMouseMove(e) {
  if (workStatus !== "drawing") return;

  const rect = canvas.getBoundingClientRect();
  endPoint = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
  };

  drawImage();
}

/**
 * 設定工作狀態
 * @param {string} status - 工作狀態
 */
function setWorkStatus(status) {
  workStatus = status;
  drawImage();
}

/**
 * 設定縮放參數
 * @param {number} newScale - 新的縮放比例
 * @param {number} newOffsetX - 新的 X 偏移量
 * @param {number} newOffsetY - 新的 Y 偏移量
 */
function setScaleParams(newScale, newOffsetX, newOffsetY) {
  scale = newScale;
  offsetX = newOffsetX;
  offsetY = newOffsetY;
  workStatus = "startScale";
  drawImage();
}

/**
 * 從後端獲取設定並應用 Scale offset
 */
function loadAndApplySettings() {
  if (typeof api !== 'undefined' && api.get_settings) {
    api.get_settings(function(result) {
      try {
        const response = JSON.parse(result);
        if (response.success) {
          const settings = response.data;
          // 應用圖片設定
          if (settings.image) {
            scale = settings.image.scale || 1.0;
            offsetX = settings.image.offset_x || 0;
            offsetY = settings.image.offset_y || 0;
            console.log(`載入設定：scale=${scale}, offsetX=${offsetX}, offsetY=${offsetY}`);
          }
        }
      } catch (error) {
        console.error("載入設定失敗:", error);
      }
    });
  }
}

/**
 * 應用縮放參數到當前圖片
 */
function applyScaleParams(scaleParams) {
  if (scaleParams) {
    scale = scaleParams.scale || 1.0;
    offsetX = scaleParams.offsetX || 0;
    offsetY = scaleParams.offsetY || 0;
    console.log(`應用縮放參數：scale=${scale}, offsetX=${offsetX}, offsetY=${offsetY}`);
    
    // 如果當前有圖片，重新繪製
    if (currentImage) {
      drawImage();
    }
  }
}

/**
 * 重置圖片狀態到 StartScale
 */
function resetToStartScale() {
  workStatus = "startScale";
  drawImage();
  console.log("重置到 StartScale 狀態");
}

// 將函數暴露到全域範圍，以便其他模組可以調用
window.CanvasImage = {
  initCanvas,
  showImage,
  showNoImage,
  setWorkStatus,
  setScaleParams,
  resizeCanvasToFill,
  loadAndApplySettings,
  applyScaleParams,
  resetToStartScale
};
