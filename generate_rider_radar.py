import json

# 1. 读取并压缩 1,830 个广州摄像头数据
with open('新建文本文档.txt', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

compact_points = []
for p in raw_data:
    compact_points.append([
        round(p['latitude'], 6),
        round(p['longitude'], 6),
        p['title'].strip()
    ])

points_json = json.dumps(compact_points, ensure_ascii=False)

html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>骑行巡航雷达 (广州 1,830监控)</title>
  
  <!-- iOS PWA Meta & Web App 配置 -->
  <link rel="manifest" href="manifest.json">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="骑行雷达">
  <meta name="theme-color" content="#0b0f19" media="(prefers-color-scheme: dark)">
  <meta name="format-detection" content="telephone=no,email=no,address=no">

  <!-- iOS 桌面高清应用图标 -->
  <link rel="apple-touch-icon" href="icons/icon-180.png">
  <link rel="apple-touch-icon" sizes="152x152" href="icons/icon-180.png">
  <link rel="apple-touch-icon" sizes="180x180" href="icons/icon-180.png">
  <link rel="apple-touch-icon" sizes="192x192" href="icons/icon-192.png">

  <!-- Leaflet CSS & MarkerCluster CSS -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
  
  <style>
    :root {
      --accent-cyan: #00f2fe;
      --accent-blue: #2563eb;
      --accent-green: #10b981;
      --accent-amber: #f59e0b;
      --accent-red: #ef4444;
      --font-stack: -apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", "Segoe UI", Roboto, sans-serif;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
      -webkit-user-select: none;
      font-family: var(--font-stack);
      touch-action: manipulation;
    }

    html, body {
      width: 100%;
      height: 100%;
      height: 100dvh;
      overflow: hidden;
      background-color: var(--bg-dark);
      color: var(--text-main);
      position: fixed;
      transition: background-color 0.3s ease, color 0.3s ease;
    }

    #map {
      width: 100%;
      height: 100%;
      position: absolute;
      top: 0;
      left: 0;
      z-index: 1;
    }

    /* ================= 1. 双主题配色系统 (日间模式 vs 夜间模式) ================= */
    /* 夜间暗黑模式 (18:30 ~ 次日 06:30 自动开启) */
    body.theme-night {
      --bg-dark: #080c16;
      --card-bg: rgba(13, 20, 36, 0.90);
      --card-blur: blur(20px);
      --card-border: 1px solid rgba(0, 242, 254, 0.22);
      --card-shadow: 0 12px 32px rgba(0, 0, 0, 0.65), 0 0 1px rgba(0, 242, 254, 0.35);
      --text-main: #f8fafc;
      --text-sub: #94a3b8;
      --text-value: #ffffff;
      --text-accent: #00f2fe;
      --border-subtle: rgba(255, 255, 255, 0.12);
      --btn-bg: rgba(255, 255, 255, 0.08);
      --btn-border: 1px solid rgba(255, 255, 255, 0.16);
      --btn-text: #f8fafc;
      --btn-active-bg: rgba(0, 242, 254, 0.22);
      --btn-active-border: 1.5px solid #00f2fe;
      --btn-active-text: #00f2fe;
      --radar-color: #00f2fe;
      --radar-fill: rgba(0, 242, 254, 0.16);
      --status-safe-border: #10b981;
      --status-safe-bg: rgba(16, 185, 129, 0.12);
      --status-warn-border: #f59e0b;
      --status-warn-bg: rgba(38, 25, 10, 0.94);
      --status-danger-border: #ef4444;
      --status-danger-bg: rgba(45, 12, 22, 0.96);
      --tile-filter: invert(100%) hue-rotate(180deg) brightness(88%) contrast(92%) saturate(120%);
    }

    /* 日光日间模式 (06:30 ~ 18:30 自动开启，高反差抗反光) */
    body.theme-sunlight {
      --bg-dark: #f8fafc;
      --card-bg: #ffffff;
      --card-blur: none;
      --card-border: 2.5px solid #000000;
      --card-shadow: 0 8px 0 #000000, 0 12px 28px rgba(0, 0, 0, 0.22);
      --text-main: #000000;
      --text-sub: #1e293b;
      --text-value: #000000;
      --text-accent: #0284c7;
      --border-subtle: rgba(0, 0, 0, 0.22);
      --btn-bg: #f8fafc;
      --btn-border: 2px solid #000000;
      --btn-text: #000000;
      --btn-active-bg: #000000;
      --btn-active-border: 2px solid #000000;
      --btn-active-text: #ffffff;
      --radar-color: #0284c7;
      --radar-fill: rgba(2, 132, 199, 0.20);
      --status-safe-border: #166534;
      --status-safe-bg: #f0fdf4;
      --status-warn-border: #b45309;
      --status-warn-bg: #fefce8;
      --status-danger-border: #b91c1c;
      --status-danger-bg: #fef2f2;
      --tile-filter: contrast(108%) saturate(112%);
    }

    #map .leaflet-tile-pane {
      filter: var(--tile-filter);
      transition: filter 0.35s ease;
    }

    /* ================= 2. HUD 全屏余光识别警示系统 ================= */
    .peripheral-alert-frame {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 9999;
      opacity: 0;
      transition: opacity 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease;
    }
    .peripheral-alert-frame.warning {
      opacity: 1;
      box-shadow: inset 0 0 50px rgba(245, 158, 11, 0.65), inset 0 0 18px rgba(245, 158, 11, 0.85);
      animation: peripheral-amber-breathe 1.25s infinite ease-in-out;
    }
    .peripheral-alert-frame.danger {
      opacity: 1;
      box-shadow: inset 0 0 85px rgba(239, 68, 68, 0.88), inset 0 0 30px rgba(255, 30, 70, 1);
      animation: peripheral-red-strobe 0.7s infinite ease-in-out;
    }
    .peripheral-alert-frame.danger::before,
    .peripheral-alert-frame.danger::after {
      content: '';
      position: absolute;
      left: 0;
      right: 0;
      height: 7px;
      background: repeating-linear-gradient(-45deg, #ef4444, #ef4444 14px, #ffffff 14px, #ffffff 28px);
      animation: hazard-stripe-shift 0.6s linear infinite;
    }
    .peripheral-alert-frame.danger::before { top: 0; }
    .peripheral-alert-frame.danger::after { bottom: 0; }

    @keyframes hazard-stripe-shift {
      0% { background-position: 0 0; }
      100% { background-position: 40px 0; }
    }
    @keyframes peripheral-amber-breathe {
      0%, 100% { box-shadow: inset 0 0 35px rgba(245, 158, 11, 0.45); }
      50% { box-shadow: inset 0 0 70px rgba(245, 158, 11, 0.85); }
    }
    @keyframes peripheral-red-strobe {
      0%, 100% { box-shadow: inset 0 0 45px rgba(239, 68, 68, 0.5); filter: brightness(1); }
      50% { box-shadow: inset 0 0 100px rgba(239, 68, 68, 1); filter: brightness(1.25); }
    }

    /* 拟触觉高光光效 */
    #haptic-visual-border {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 9998;
      box-shadow: inset 0 0 0 0 transparent;
    }
    #haptic-visual-border.haptic-approach { animation: hapticPulseApproach 0.45s ease-out forwards; }
    #haptic-visual-border.haptic-urgent { animation: hapticPulseUrgent 0.55s ease-out forwards; }
    #haptic-visual-border.haptic-pass { animation: hapticPulsePass 0.4s ease-out forwards; }

    @keyframes hapticPulseApproach {
      0% { box-shadow: inset 0 0 35px rgba(245, 158, 11, 0.85); }
      100% { box-shadow: inset 0 0 0 transparent; }
    }
    @keyframes hapticPulseUrgent {
      0% { box-shadow: inset 0 0 50px rgba(239, 68, 68, 0.95); }
      50% { box-shadow: inset 0 0 50px rgba(239, 68, 68, 0.95); }
      100% { box-shadow: inset 0 0 0 transparent; }
    }
    @keyframes hapticPulsePass {
      0% { box-shadow: inset 0 0 35px rgba(16, 185, 129, 0.85); }
      100% { box-shadow: inset 0 0 0 transparent; }
    }

    /* ================= 3. 顶部 HUD 卡片 ================= */
    .top-hud {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      z-index: 1000;
      pointer-events: none;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: max(10px, env(safe-area-inset-top)) 14px 0 14px;
    }

    .alert-card {
      pointer-events: auto;
      width: 100%;
      max-width: 440px;
      margin-top: 4px;
      background: var(--card-bg);
      backdrop-filter: var(--card-blur);
      -webkit-backdrop-filter: var(--card-blur);
      border: var(--card-border);
      border-radius: 20px;
      padding: 13px 18px;
      box-shadow: var(--card-shadow);
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .alert-card.status-safe {
      border-left: 6px solid var(--status-safe-border);
      background: var(--status-safe-bg);
    }
    .alert-card.status-warning {
      border-left: 6px solid var(--status-warn-border);
      background: var(--status-warn-bg);
      animation: pulse-border 1.5s infinite;
    }
    .alert-card.status-danger {
      border-left: 6px solid var(--status-danger-border);
      background: var(--status-danger-bg);
      animation: pulse-danger 0.9s infinite;
    }

    @keyframes pulse-border {
      0%, 100% { border-color: rgba(245, 158, 11, 0.5); }
      50% { border-color: rgba(245, 158, 11, 1); }
    }
    @keyframes pulse-danger {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.02); }
    }

    .hud-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      color: var(--text-sub);
    }

    .badge-status {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-weight: 700;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.1);
    }
    .badge-status .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent-green); }
    .badge-status.warning .dot { background: var(--accent-amber); }
    .badge-status.danger .dot { background: var(--accent-red); }

    .hud-main { display: flex; justify-content: space-between; align-items: center; }
    .hud-title-box { flex: 1; padding-right: 12px; overflow: hidden; }
    .hud-point-title {
      font-size: 17px;
      font-weight: 800;
      color: var(--text-main);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      letter-spacing: -0.3px;
    }
    .hud-point-sub { font-size: 12px; color: var(--text-sub); margin-top: 2px; }

    .hud-dist-box { text-align: right; min-width: 80px; }
    .hud-dist-value {
      font-size: 28px;
      font-weight: 900;
      line-height: 1;
      font-feature-settings: "tnum";
      font-variant-numeric: tabular-nums;
      color: var(--text-accent);
      letter-spacing: -1px;
    }
    .hud-dist-box.warning .hud-dist-value { color: var(--accent-amber); }
    .hud-dist-box.danger .hud-dist-value { color: var(--accent-red); }
    .hud-dist-unit { font-size: 11px; color: var(--text-sub); margin-top: 2px; }

    .hud-progress-bg {
      width: 100%;
      height: 4px;
      background: rgba(255, 255, 255, 0.12);
      border-radius: 2px;
      overflow: hidden;
      margin-top: 2px;
    }
    .hud-progress-bar {
      height: 100%;
      width: 0%;
      background: var(--text-accent);
      transition: width 0.3s ease;
      border-radius: 2px;
    }
    .warning .hud-progress-bar { background: var(--accent-amber); }
    .danger .hud-progress-bar { background: var(--accent-red); }

    /* ================= 4. 底部驾驶舱仪表盘与大触控区 ================= */
    .bottom-cockpit {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      z-index: 1000;
      pointer-events: none;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 0 14px max(14px, env(safe-area-inset-bottom)) 14px;
    }

    .cockpit-panel {
      pointer-events: auto;
      width: 100%;
      max-width: 440px;
      background: var(--card-bg);
      backdrop-filter: var(--card-blur);
      -webkit-backdrop-filter: var(--card-blur);
      border: var(--card-border);
      border-radius: 24px;
      padding: 14px 18px;
      box-shadow: var(--card-shadow);
      margin-bottom: 6px;
      transition: all 0.3s ease;
    }

    .instruments-row {
      display: flex;
      align-items: center;
      justify-content: space-around;
      margin-bottom: 12px;
    }

    .inst-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      flex: 1;
    }

    .inst-label { font-size: 11px; color: var(--text-sub); letter-spacing: 0.5px; margin-bottom: 4px; }
    .speed-value {
      font-size: 36px;
      font-weight: 900;
      line-height: 1;
      color: var(--text-value);
      font-feature-settings: "tnum";
      font-variant-numeric: tabular-nums;
      letter-spacing: -1.2px;
    }
    .speed-unit { font-size: 11px; color: var(--text-accent); font-weight: 700; margin-top: 3px; }

    .heading-arrow {
      font-size: 28px;
      color: var(--text-accent);
      transition: transform 0.2s linear;
      display: inline-block;
      line-height: 1;
    }
    .heading-text { font-size: 13px; font-weight: 700; color: var(--text-main); margin-top: 4px; }
    .target-count { font-size: 26px; font-weight: 800; line-height: 1; color: var(--text-main); }
    .inst-divider { width: 1px; height: 38px; background: var(--border-subtle); }

    .controls-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
    }

    .btn-act {
      min-height: 56px;
      border: var(--btn-border);
      background: var(--btn-bg);
      color: var(--btn-text);
      border-radius: 14px;
      padding: 8px 4px;
      font-size: 11.5px;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      transition: all 0.15s cubic-bezier(0.2, 0.9, 0.4, 1);
    }
    .btn-act:active { transform: translateY(2px) scale(0.96); }
    .btn-act.active {
      background: var(--btn-active-bg);
      border: var(--btn-active-border);
      color: var(--btn-active-text);
    }
    .btn-act svg { width: 18px; height: 18px; stroke-width: 2.3; }

    /* 浮动工具栏 */
    .floating-tools {
      position: absolute;
      right: 14px;
      top: 50%;
      transform: translateY(-50%);
      z-index: 1000;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .btn-tool {
      width: 50px;
      height: 50px;
      border-radius: 16px;
      background: var(--card-bg);
      backdrop-filter: var(--card-blur);
      -webkit-backdrop-filter: var(--card-blur);
      border: var(--btn-border);
      color: var(--text-main);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35);
      cursor: pointer;
      transition: all 0.15s ease;
      position: relative;
    }
    .btn-tool:active { transform: translateY(2px) scale(0.92); }

    /* 自动模式微标 */
    .badge-auto {
      position: absolute;
      bottom: 2px;
      right: 4px;
      font-size: 9px;
      font-weight: 900;
      background: var(--text-accent);
      color: #0b0f19;
      border-radius: 4px;
      padding: 1px 3px;
      line-height: 1;
    }

    /* ================= 5. 横屏宽屏车机双联屏适配 ================= */
    @media (orientation: landscape) {
      body { display: flex; flex-direction: row; }
      .top-hud {
        position: static;
        width: 380px;
        max-width: 44%;
        min-width: 320px;
        height: 100%;
        background: var(--card-bg);
        backdrop-filter: var(--card-blur);
        -webkit-backdrop-filter: var(--card-blur);
        border-right: var(--card-border);
        padding: max(10px, env(safe-area-inset-top)) 16px max(10px, env(safe-area-inset-bottom)) max(16px, env(safe-area-inset-left));
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        pointer-events: auto;
        z-index: 1000;
      }
      .bottom-cockpit {
        position: static;
        width: 100%;
        padding: 0;
        pointer-events: auto;
      }
      .cockpit-panel {
        width: 100%;
        max-width: none;
        background: transparent;
        border: none;
        box-shadow: none;
        padding: 0;
        margin: 0;
      }
      .speed-value { font-size: 52px; }
      #map {
        position: relative;
        flex: 1;
        height: 100%;
      }
      .floating-tools { right: max(14px, env(safe-area-inset-right)); }
    }

    /* ================= 6. 静态纯净前方雷达扇区 (彻底移除摇摆扫动，安定不晃眼) ================= */
    .leaflet-radar-cone {
      pointer-events: none;
      transition: stroke 0.3s ease, fill 0.3s ease;
      stroke-dasharray: 4, 4;
    }

    /* 摄像头图钉 */
    .camera-marker-pin {
      width: 28px;
      height: 28px;
      background: #0284c7;
      border: 2px solid #ffffff;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;
      position: relative;
    }
    .camera-marker-pin svg {
      transform: rotate(45deg);
      width: 14px;
      height: 14px;
      fill: #ffffff;
    }
    .camera-marker-pin.alerting {
      background: #ef4444 !important;
      border-color: #ffedd5;
      animation: alert-cam-pulse 1s infinite;
    }
    @keyframes alert-cam-pulse {
      0%, 100% { transform: rotate(-45deg) scale(1.1); }
      50% { transform: rotate(-45deg) scale(1.35); }
    }

    /* 聚合簇样式 */
    .marker-cluster-small { background-color: rgba(2, 132, 199, 0.6) !important; }
    .marker-cluster-small div { background-color: rgba(2, 132, 199, 0.9) !important; color: #fff !important; font-weight: 700 !important; }
    .marker-cluster-medium { background-color: rgba(14, 165, 233, 0.6) !important; }
    .marker-cluster-medium div { background-color: rgba(14, 165, 233, 0.9) !important; color: #fff !important; font-weight: 700 !important; }
    .marker-cluster-large { background-color: rgba(37, 99, 235, 0.6) !important; }
    .marker-cluster-large div { background-color: rgba(37, 99, 235, 0.9) !important; color: #fff !important; font-weight: 700 !important; }

    /* 车头标记 */
    .vehicle-core {
      width: 30px;
      height: 30px;
      background: #00f2fe;
      border: 3px solid #ffffff;
      border-radius: 50%;
      box-shadow: 0 0 18px rgba(0, 242, 254, 0.85);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform 0.2s ease;
    }
    .vehicle-pointer {
      width: 0;
      height: 0;
      border-left: 6px solid transparent;
      border-right: 6px solid transparent;
      border-bottom: 12px solid #041226;
      transform: translateY(-1px);
    }

    /* 启动手势遮罩 */
    #start-overlay {
      position: fixed;
      inset: 0;
      z-index: 10000;
      background: rgba(8, 12, 22, 0.96);
      backdrop-filter: blur(25px);
      -webkit-backdrop-filter: blur(25px);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
      text-align: center;
    }
    .start-box {
      max-width: 360px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
    }
    .start-icon {
      width: 76px;
      height: 76px;
      border-radius: 22px;
      background: linear-gradient(135deg, #00f2fe, #0099ff);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #0b0f19;
      box-shadow: 0 10px 25px rgba(0, 242, 254, 0.4);
    }
    .btn-start-main {
      width: 100%;
      background: linear-gradient(135deg, #00f2fe, #0099ff);
      color: #041226;
      border: none;
      padding: 16px;
      border-radius: 16px;
      font-size: 16px;
      font-weight: 800;
      cursor: pointer;
      box-shadow: 0 8px 24px rgba(0, 242, 254, 0.35);
      margin-top: 6px;
    }
    .btn-start-main:active { transform: scale(0.97); }

    #pwa-install-banner {
      display: none;
      position: fixed;
      bottom: max(16px, env(safe-area-inset-bottom));
      left: 16px;
      right: 16px;
      max-width: 440px;
      margin: 0 auto;
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid rgba(0, 242, 254, 0.3);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-radius: 16px;
      padding: 12px 16px;
      z-index: 5000;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
      align-items: center;
      gap: 12px;
      font-size: 13px;
      color: #ffffff;
    }
    #pwa-install-banner .close-btn {
      background: transparent;
      border: none;
      color: #94a3b8;
      font-size: 18px;
      cursor: pointer;
      padding: 4px;
    }
  </style>
</head>
<body class="theme-night">

  <!-- 全屏外周余光识别层 -->
  <div class="peripheral-alert-frame" id="peripheral-alert-frame"></div>
  <!-- 拟触觉高光光效层 -->
  <div id="haptic-visual-border"></div>

  <!-- 地图容器 -->
  <div id="map"></div>

  <!-- 浮动右侧快捷工具 -->
  <div class="floating-tools">
    <button class="btn-tool" id="btn-recenter" title="定位到车头">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><polygon points="3 11 22 2 13 21 11 13 3 11"/></svg>
    </button>
    <button class="btn-tool" id="btn-view-all" title="全览广州摄像头">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
    </button>
    <button class="btn-tool" id="btn-theme-toggle" title="主题模式 (东八区自动/手动)">
      <svg id="icon-theme-sun" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
      <svg id="icon-theme-moon" style="display:none;" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      <span class="badge-auto" id="theme-auto-badge">A</span>
    </button>
  </div>

  <!-- 顶部预警 HUD 卡片 -->
  <div class="top-hud">
    <div class="alert-card status-safe" id="alert-card">
      <div class="hud-header">
        <span class="badge-status" id="badge-status">
          <span class="dot"></span>
          <span id="status-text">巡航雷达运行中</span>
        </span>
        <span id="hud-sub-status">车速自适应预警</span>
      </div>
      <div class="hud-main">
        <div class="hud-title-box">
          <div class="hud-point-title" id="alert-title">前方道路通畅</div>
          <div class="hud-point-sub" id="alert-desc">航向正常 · 雷达守护中</div>
        </div>
        <div class="hud-dist-box" id="hud-dist-box">
          <div class="hud-dist-value" id="alert-distance">--</div>
          <div class="hud-dist-unit" id="alert-dist-unit">米</div>
        </div>
      </div>
      <div class="hud-progress-bg">
        <div class="hud-progress-bar" id="hud-progress"></div>
      </div>
    </div>

    <!-- 底部驾驶舱仪表 -->
    <div class="bottom-cockpit">
      <div class="cockpit-panel">
        <div class="instruments-row">
          <div class="inst-item">
            <span class="inst-label">当前时速</span>
            <div class="speed-value" id="inst-speed">0.0</div>
            <span class="speed-unit">KM/H</span>
          </div>
          <div class="inst-divider"></div>
          <div class="inst-item">
            <span class="inst-label">行驶航向</span>
            <div class="heading-arrow" id="inst-arrow">↑</div>
            <div class="heading-text" id="inst-heading">正西 270°</div>
          </div>
          <div class="inst-divider"></div>
          <div class="inst-item">
            <span class="inst-label">预计到达</span>
            <div class="target-count" id="inst-eta">--</div>
            <span class="speed-unit">秒</span>
          </div>
        </div>

        <div class="controls-grid">
          <button class="btn-act active" id="btn-mode-sim">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            <span>模拟骑行</span>
          </button>
          <button class="btn-act" id="btn-mode-gps">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8"/></svg>
            <span>真机GPS</span>
          </button>
          <button class="btn-act" id="btn-dist-toggle">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><line x1="12" y1="6" x2="12" y2="12"/></svg>
            <span id="lbl-dist-mode">自适应</span>
          </button>
          <button class="btn-act active" id="btn-voice-toggle">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
            <span id="lbl-voice">语音开</span>
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- iOS PWA 添加到主屏幕引导条 -->
  <div id="pwa-install-banner">
    <div style="flex:1;">
      <strong>添加到 iPhone 主屏幕</strong><br>
      轻点下方分享按钮 ⎋，选择<strong>「添加到主屏幕 ⊞」</strong>获得沉浸式车机与后台保活！
    </div>
    <button class="close-btn" id="btn-close-pwa-banner">✕</button>
  </div>

  <!-- iOS 首次交互遮罩 -->
  <div id="start-overlay">
    <div class="start-box">
      <div class="start-icon">
        <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="3 11 22 2 13 21 11 13 3 11"/></svg>
      </div>
      <h2 style="font-size:22px;font-weight:900;">骑行巡航雷达</h2>
      <p style="font-size:13.5px;color:#94a3b8;line-height:1.6;">
        专为 iPhone 骑行支架设计<br>
        行驶方向预测 · 接近语音提示 · 屏幕常亮 · 后台保活<br>
        <span style="color:#00f2fe;font-weight:700;">已载入 1,830 个广州道路监控点位</span>
      </p>
      <button class="btn-start-main" id="btn-start-experience">立即启程 · 解锁巡航</button>
    </div>
  </div>

  <!-- Leaflet & MarkerCluster JS -->
  <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>

  <script>
    /* ==========================================================================
       1. 监控点位数据 (广州 1,830 点)
       ========================================================================== */
    const ALL_POINTS = ''' + points_json + ''';

    /* ==========================================================================
       2. WGS-84 转 GCJ-02 高精度纠偏算法
       ========================================================================== */
    const CoordTransform = {
      PI: 3.1415926535897932384626,
      a: 6378245.0,
      ee: 0.00669342162296594323,
      transformLat: function(x, y) {
        let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
        ret += (20.0 * Math.sin(6.0 * x * this.PI) + 20.0 * Math.sin(2.0 * x * this.PI)) * 2.0 / 3.0;
        ret += (20.0 * Math.sin(y * this.PI) + 40.0 * Math.sin(y / 3.0 * this.PI)) * 2.0 / 3.0;
        ret += (160.0 * Math.sin(y / 12.0 * this.PI) + 320 * Math.sin(y * this.PI / 30.0)) * 2.0 / 3.0;
        return ret;
      },
      transformLng: function(x, y) {
        let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
        ret += (20.0 * Math.sin(6.0 * x * this.PI) + 20.0 * Math.sin(2.0 * x * this.PI)) * 2.0 / 3.0;
        ret += (20.0 * Math.sin(x * this.PI) + 40.0 * Math.sin(x / 3.0 * this.PI)) * 2.0 / 3.0;
        ret += (150.0 * Math.sin(x / 12.0 * this.PI) + 300.0 * Math.sin(x / 3.0 * this.PI)) * 2.0 / 3.0;
        return ret;
      },
      wgs84ToGcj02: function(lng, lat) {
        let dLat = this.transformLat(lng - 105.0, lat - 35.0);
        let dLng = this.transformLng(lng - 105.0, lat - 35.0);
        const radLat = lat / 180.0 * this.PI;
        let magic = Math.sin(radLat);
        magic = 1 - this.ee * magic * magic;
        const sqrtMagic = Math.sqrt(magic);
        dLat = (dLat * 180.0) / ((this.a * (1 - this.ee)) / (magic * sqrtMagic) * this.PI);
        dLng = (dLng * 180.0) / (this.a / sqrtMagic * Math.cos(radLat) * this.PI);
        return [lng + dLng, lat + dLat];
      }
    };

    /* ==========================================================================
       3. 地理几何与大圆航向推算
       ========================================================================== */
    const MathUtils = {
      DEG_TO_RAD: Math.PI / 180,
      RAD_TO_DEG: 180 / Math.PI,
      EARTH_RADIUS: 6371000,
      getDistance: function(lat1, lon1, lat2, lon2) {
        const dLat = (lat2 - lat1) * this.DEG_TO_RAD;
        const dLon = (lon2 - lon1) * this.DEG_TO_RAD;
        const a = Math.sin(dLat / 2) ** 2 +
                  Math.cos(lat1 * this.DEG_TO_RAD) * Math.cos(lat2 * this.DEG_TO_RAD) *
                  Math.sin(dLon / 2) ** 2;
        return this.EARTH_RADIUS * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      },
      getBearing: function(lat1, lon1, lat2, lon2) {
        const φ1 = lat1 * this.DEG_TO_RAD;
        const φ2 = lat2 * this.DEG_TO_RAD;
        const Δλ = (lon2 - lon1) * this.DEG_TO_RAD;
        const y = Math.sin(Δλ) * Math.cos(φ2);
        const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
        return (Math.atan2(y, x) * this.RAD_TO_DEG + 360) % 360;
      },
      getAngleDiff: function(a, b) {
        const diff = Math.abs(a - b) % 360;
        return diff > 180 ? 360 - diff : diff;
      },
      calculateDestinationPoint: function(lat, lng, distMeters, bearingDeg) {
        const rad = bearingDeg * this.DEG_TO_RAD;
        const dLat = (distMeters * Math.cos(rad)) / this.EARTH_RADIUS * this.RAD_TO_DEG;
        const dLng = (distMeters * Math.sin(rad)) / (this.EARTH_RADIUS * Math.cos(lat * this.DEG_TO_RAD)) * this.RAD_TO_DEG;
        return [lat + dLat, lng + dLng];
      },
      clamp: function(v, min, max) { return Math.max(min, Math.min(max, v)); }
    };

    function headingToText(deg) {
      const dirs = ['正北', '东北', '正东', '东南', '正南', '西南', '正西', '西北'];
      const index = Math.round(deg / 45) % 8;
      return `${dirs[index]} ${Math.round(deg)}°`;
    }

    /* ==========================================================================
       4. 算法核心 1: 点位语义方向识别与对向车道静音过滤
       ========================================================================== */
    const CARDINAL_HEADINGS = {
      '北': 0, '东北': 45, '东': 90, '东南': 135,
      '南': 180, '西南': 225, '西': 270, '西北': 315
    };

    class PointDirectionParser {
      constructor() {
        this.cache = new Map();
        this.regexPair = /(?:由)?(东北|东南|西北|西南|东|南|西|北)[往至到向](东北|东南|西北|西南|东|南|西|北)/g;
        this.regexXing = /(东北|东南|西北|西南|东|南|西|北)行/g;
        this.regexParenSingle = /[（(](?:往|向|朝)?(东北|东南|西北|西南|东|南|西|北)[)）]/;
        this.regexBi = /双向/;
      }

      parsePointDirection(title) {
        if (!title || typeof title !== 'string') {
          return { directionText: '全向/路口', controlledHeading: null, isOmnidirectional: true, toleranceDeg: 180 };
        }
        if (this.cache.has(title)) return this.cache.get(title);

        if (this.regexBi.test(title)) {
          const res = { directionText: '双向', controlledHeading: null, isOmnidirectional: true, toleranceDeg: 180 };
          this.cache.set(title, res);
          return res;
        }

        this.regexPair.lastIndex = 0;
        let mPair = null, match;
        while ((match = this.regexPair.exec(title)) !== null) mPair = match;

        if (mPair) {
          const res = {
            directionText: `${mPair[1]}往${mPair[2]}`,
            fromDir: mPair[1],
            toDir: mPair[2],
            controlledHeading: CARDINAL_HEADINGS[mPair[2]], // 东往西 => 西 270°
            isOmnidirectional: false,
            toleranceDeg: 45
          };
          this.cache.set(title, res);
          return res;
        }

        this.regexXing.lastIndex = 0;
        let mXing = null;
        while ((match = this.regexXing.exec(title)) !== null) mXing = match;
        if (mXing) {
          const res = {
            directionText: `${mXing[1]}行`,
            controlledHeading: CARDINAL_HEADINGS[mXing[1]],
            isOmnidirectional: false,
            toleranceDeg: 45
          };
          this.cache.set(title, res);
          return res;
        }

        const mParen = this.regexParenSingle.exec(title);
        if (mParen) {
          const res = {
            directionText: `往${mParen[1]}`,
            controlledHeading: CARDINAL_HEADINGS[mParen[1]],
            isOmnidirectional: false,
            toleranceDeg: 45
          };
          this.cache.set(title, res);
          return res;
        }

        const res = { directionText: '全向/路口', controlledHeading: null, isOmnidirectional: true, toleranceDeg: 180 };
        this.cache.set(title, res);
        return res;
      }

      evaluateRiderHeading(riderHeading, dirInfo) {
        if (!dirInfo || dirInfo.isOmnidirectional || dirInfo.controlledHeading === null) {
          return { shouldAlert: true, relation: 'omnidirectional' };
        }
        const diff = MathUtils.getAngleDiff(riderHeading, dirInfo.controlledHeading);
        if (diff <= dirInfo.toleranceDeg) {
          return { shouldAlert: true, relation: 'same_direction', diff: Math.round(diff) };
        } else if (diff >= 135) {
          return { shouldAlert: false, relation: 'opposite_direction', diff: Math.round(diff) };
        } else {
          return { shouldAlert: false, relation: 'cross_direction', diff: Math.round(diff) };
        }
      }
    }

    /* ==========================================================================
       5. 算法核心 2: 车速自适应预警距离引擎 (10~40 km/h 动态平滑)
       ========================================================================== */
    class SpeedAdaptiveWarningEngine {
      constructor() {
        this.targetLeadTimeSec = 13.5;
        this.minDistance = 60.0;
        this.maxDistance = 180.0;
        this.currentDistance = 120.0;
        this.filteredSpeedKmh = 28.0;
        this.speedAlpha = 0.25;
      }

      update(rawSpeedKmh) {
        const safeSpeed = Math.max(0, typeof rawSpeedKmh === 'number' && !isNaN(rawSpeedKmh) ? rawSpeedKmh : 0);
        this.filteredSpeedKmh = this.filteredSpeedKmh * (1 - this.speedAlpha) + safeSpeed * this.speedAlpha;

        const speedMs = this.filteredSpeedKmh / 3.6;
        const ideal = MathUtils.clamp(speedMs * this.targetLeadTimeSec + 8.0, this.minDistance, this.maxDistance);
        
        this.currentDistance += (ideal - this.currentDistance) * 0.2;
        return Math.round(this.currentDistance);
      }
    }

    /* ==========================================================================
       6. 算法核心 3: GPS 航向抗抖动与红绿灯静止锁存引擎
       ========================================================================== */
    class HeadingFilterAndLockEngine {
      constructor() {
        this.stopSpeedThreshold = 3.0;
        this.moveSpeedThreshold = 4.5;
        this.isStationary = true;
        this.heading = 270;
        this.lastCruisingHeading = 270;
        this.vecX = -1;
        this.vecY = 0;
      }

      update(rawHeading, speedKmh) {
        const currentSpeed = Math.max(0, typeof speedKmh === 'number' && !isNaN(speedKmh) ? speedKmh : 0);

        if (this.isStationary) {
          if (currentSpeed >= this.moveSpeedThreshold) this.isStationary = false;
        } else {
          if (currentSpeed < this.stopSpeedThreshold) {
            this.isStationary = true;
            this.lastCruisingHeading = this.heading;
          }
        }

        if (this.isStationary) {
          return this.lastCruisingHeading;
        }

        if (typeof rawHeading === 'number' && !isNaN(rawHeading) && rawHeading >= 0) {
          const targetRad = rawHeading * MathUtils.DEG_TO_RAD;
          const alpha = 0.35;
          this.vecX = (1 - alpha) * this.vecX + alpha * Math.sin(targetRad);
          this.vecY = (1 - alpha) * this.vecY + alpha * Math.cos(targetRad);
          const norm = Math.hypot(this.vecX, this.vecY);
          if (norm > 1e-6) {
            this.vecX /= norm;
            this.vecY /= norm;
          }
          this.heading = (Math.atan2(this.vecX, this.vecY) * MathUtils.RAD_TO_DEG + 360) % 360;
          this.lastCruisingHeading = this.heading;
        }
        return this.heading;
      }
    }

    /* ==========================================================================
       7. 专业声音工程: 车规级 Web Audio 双音和弦 + 释压通过音 + 文本精简
       ========================================================================== */
    class AudioEngine {
      constructor() {
        this.enabled = true;
        this.audioCtx = null;
        this.synth = window.speechSynthesis;
        this.lastSpokenText = '';
        this.lastSpokenTime = 0;
      }

      init() {
        try {
          const AudioContext = window.AudioContext || window.webkitAudioContext;
          if (!this.audioCtx) this.audioCtx = new AudioContext();
          if (this.audioCtx.state === 'suspended') this.audioCtx.resume();

          const buffer = this.audioCtx.createBuffer(1, 1, 22050);
          const src = this.audioCtx.createBufferSource();
          src.buffer = buffer;
          src.connect(this.audioCtx.destination);
          src.start(0);

          if (this.synth) {
            const dummy = new SpeechSynthesisUtterance('');
            dummy.volume = 0;
            this.synth.speak(dummy);
          }
        } catch (e) {}
      }

      resumeContext() {
        if (this.audioCtx && this.audioCtx.state === 'suspended') this.audioCtx.resume();
      }

      playApproachChime() {
        if (!this.enabled || !this.audioCtx) return;
        this.resumeContext();
        try {
          const ctx = this.audioCtx;
          const now = ctx.currentTime;
          const masterGain = ctx.createGain();
          masterGain.gain.setValueAtTime(0.5, now);

          const filter = ctx.createBiquadFilter();
          filter.type = 'lowpass';
          filter.frequency.setValueAtTime(4500, now);
          filter.Q.setValueAtTime(0.85, now);
          masterGain.connect(filter);
          filter.connect(ctx.destination);

          const playHarmonic = (freq, startTime, dur, vol) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, startTime);
            gain.gain.setValueAtTime(0.0001, startTime);
            gain.gain.exponentialRampToValueAtTime(vol, startTime + 0.005);
            gain.gain.exponentialRampToValueAtTime(0.0001, startTime + dur);
            osc.connect(gain);
            gain.connect(masterGain);
            osc.start(startTime);
            osc.stop(startTime + dur);

            const osc2 = ctx.createOscillator();
            const gain2 = ctx.createGain();
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(freq * 2, startTime);
            gain2.gain.setValueAtTime(0.0001, startTime);
            gain2.gain.exponentialRampToValueAtTime(vol * 0.25, startTime + 0.004);
            gain2.gain.exponentialRampToValueAtTime(0.0001, startTime + dur * 0.65);
            osc2.connect(gain2);
            gain2.connect(masterGain);
            osc2.start(startTime);
            osc2.stop(startTime + dur);
          };

          playHarmonic(880, now, 0.18, 0.45);
          playHarmonic(1174.66, now + 0.115, 0.26, 0.40);
        } catch (e) {}
      }

      playPassConfirmSound() {
        if (!this.enabled || !this.audioCtx) return;
        this.resumeContext();
        try {
          const ctx = this.audioCtx;
          const now = ctx.currentTime;
          const masterGain = ctx.createGain();
          masterGain.gain.setValueAtTime(0.4, now);

          const filter = ctx.createBiquadFilter();
          filter.type = 'lowpass';
          filter.frequency.setValueAtTime(1200, now);
          masterGain.connect(filter);
          filter.connect(ctx.destination);

          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(523.25, now);
          osc.frequency.exponentialRampToValueAtTime(392.00, now + 0.18);
          gain.gain.setValueAtTime(0.0001, now);
          gain.gain.exponentialRampToValueAtTime(0.35, now + 0.012);
          gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.24);
          osc.connect(gain);
          gain.connect(masterGain);
          osc.start(now);
          osc.stop(now + 0.25);
        } catch (e) {}
      }

      speak(text, priority = false) {
        if (!this.enabled || !this.synth) return;
        const now = Date.now();
        if (!priority && text === this.lastSpokenText && (now - this.lastSpokenTime) < 4000) return;
        this.lastSpokenText = text;
        this.lastSpokenTime = now;

        try {
          this.synth.cancel();
          const utter = new SpeechSynthesisUtterance(text);
          utter.lang = 'zh-CN';
          utter.rate = 1.12;
          utter.pitch = 1.05;
          this.synth.speak(utter);
        } catch (e) {}
      }
    }

    const audio = new AudioEngine();

    function cleanSpeechTitle(rawTitle) {
      if (!rawTitle || typeof rawTitle !== 'string') return '前方道路';
      let title = rawTitle.trim();
      title = title.replace(/\\([^)]*\\)/g, '').replace(/（[^）]*）/g, '').replace(/\\[[^\\]]*\\]/g, '');
      title = title.replace(/(未安装|待建|拆除|调试|测试|待启用|已停用|来源[^\\s,，。]+)/g, '');
      title = title.replace(/(东往西|西往东|南往北|北往南|东北往西南|西南往东北|东南往西北|西北往东南)/g, '');
      title = title.replace(/(东向西|西向东|南向北|北向南)/g, '');
      title = title.replace(/(下桥位|上桥位|下桥处|上桥处|对出路段|对出|对面路段|对面|路段|辅道|主道|主线|匝道口?)/g, '');
      title = title.replace(/交叉路口/g, '路口').replace(/路+路口/g, '路口').replace(/路+路/g, '路');
      title = title.replace(/广园快速路立交/g, '广园立交').replace(/东风[东南西北中]路/g, '东风路').replace(/环市[东南西北中]路/g, '环市路');
      title = title.replace(/^[\\s,，、_-]+|[\\s,，、_-]+$/g, '');
      return title.length < 2 ? '前方道路' : title;
    }

    class HapticsEngine {
      static vibrate(type = 'approach') {
        if ('vibrate' in navigator) {
          try {
            if (type === 'approach') navigator.vibrate([70, 70, 110]);
            else if (type === 'urgent') navigator.vibrate([120, 50, 120, 50, 160]);
            else if (type === 'pass') navigator.vibrate(45);
            else if (type === 'tap') navigator.vibrate(28);
            else if (type === 'toggle') navigator.vibrate([35, 30, 35]);
          } catch (e) {}
        }
        const el = document.getElementById('haptic-visual-border');
        if (el) {
          el.className = '';
          void el.offsetWidth;
          el.className = `haptic-${type}`;
        }
      }
    }

    /* ==========================================================================
       8. iOS Safari 深度保活机制
       ========================================================================== */
    class iOSBackgroundKeeper {
      constructor() {
        this.audioEl = null;
        this.isActive = false;
      }

      createSilentWavBlob(durationSec = 2, sampleRate = 8000) {
        const numFrames = durationSec * sampleRate;
        const bytesPerSample = 2;
        const dataSize = numFrames * bytesPerSample;
        const buffer = new ArrayBuffer(44 + dataSize);
        const view = new DataView(buffer);
        const writeStr = (offset, str) => { for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i)); };
        writeStr(0, 'RIFF');
        view.setUint32(4, 36 + dataSize, true);
        writeStr(8, 'WAVE');
        writeStr(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, 1, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * 2, true);
        view.setUint16(32, 2, true);
        view.setUint16(34, 16, true);
        writeStr(36, 'data');
        view.setUint32(40, dataSize, true);
        return new Blob([buffer], { type: 'audio/wav' });
      }

      start() {
        if (this.isActive) return;
        this.isActive = true;
        try {
          if (!this.audioEl) {
            this.audioEl = document.createElement('audio');
            this.audioEl.setAttribute('playsinline', '');
            this.audioEl.setAttribute('webkit-playsinline', '');
            this.audioEl.setAttribute('loop', '');
            this.audioEl.style.position = 'absolute';
            this.audioEl.style.opacity = '0.001';
            this.audioEl.src = URL.createObjectURL(this.createSilentWavBlob());
            document.body.appendChild(this.audioEl);
          }
          this.audioEl.volume = 0.001;
          this.audioEl.play().catch(() => {});
          this.setupMediaSession();
        } catch (e) {}
      }

      setupMediaSession() {
        if (!('mediaSession' in navigator)) return;
        navigator.mediaSession.metadata = new MediaMetadata({
          title: '骑行巡航雷达 · 运行中',
          artist: '广州 1,830 个监控点扫描中',
          album: 'iOS 后台保活导航',
          artwork: [{ src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' }]
        });
        navigator.mediaSession.playbackState = 'playing';
      }

      updateStatus(speedKmh, headingText, alertInfo) {
        if (!('mediaSession' in navigator) || !navigator.mediaSession.metadata) return;
        if (alertInfo) {
          navigator.mediaSession.metadata.title = `⚠️ 前方${alertInfo.dist}m: ${alertInfo.title}`;
          navigator.mediaSession.metadata.artist = `时速 ${speedKmh.toFixed(1)} km/h · 约 ${alertInfo.eta}秒后到达`;
        } else {
          navigator.mediaSession.metadata.title = `⚡ 时速: ${speedKmh.toFixed(1)} km/h · 道路通畅`;
          navigator.mediaSession.metadata.artist = `航向: ${headingText} · 卫导保活中`;
        }
      }
    }

    const bgKeeper = new iOSBackgroundKeeper();

    /* ==========================================================================
       9. 东八区时间 (UTC+8) 自动日夜主题调度器
       ========================================================================== */
    const TimeThemeManager = {
      // 获取东八区精准时间 (无论客户端设置什么时区，均准确定位 UTC+8 北京时间)
      getBeijingDate: function() {
        const now = new Date();
        const utcMs = now.getTime() + (now.getTimezoneOffset() * 60000);
        return new Date(utcMs + (8 * 3600000));
      },

      // 获取当前东八区对应主题: 06:30 ~ 18:30 为日间模式，其余为夜间模式
      getAutoTheme: function() {
        const bj = this.getBeijingDate();
        const minutes = bj.getHours() * 60 + bj.getMinutes();
        const isDaytime = (minutes >= 390 && minutes < 1110);
        return {
          theme: isDaytime ? 'sunlight' : 'night',
          isDaytime: isDaytime,
          timeStr: `${String(bj.getHours()).padStart(2, '0')}:${String(bj.getMinutes()).padStart(2, '0')}`
        };
      }
    };

    /* ==========================================================================
       10. 核心巡航雷达主应用
       ========================================================================== */
    class RadarCruiseApp {
      constructor() {
        this.map = null;
        this.clusterGroup = null;
        this.markerInstances = [];
        this.vehicleMarker = null;
        this.radarSector = null; // 纯净静态前方探测扇面 (不晃眼)

        // 算法组件
        this.directionParser = new PointDirectionParser();
        this.speedEngine = new SpeedAdaptiveWarningEngine();
        this.headingEngine = new HeadingFilterAndLockEngine();

        // 状态
        this.currentPos = { lat: 23.1315, lng: 113.2750 };
        this.heading = 270;
        this.speedKmh = 29.0;
        this.warningDistance = 120;
        this.fovAngle = 40;
        this.mode = 'sim';
        this.distMode = 'auto';
        this.mapFollow = true;

        // 主题模式: 'auto' (东八区时间自动), 'sunlight' (手动日间), 'night' (手动夜间)
        this.themeMode = 'auto';
        this.currentTheme = 'night';

        this.alertedMap = new Map();
        this.activeTarget = null;
        this.activeMarker = null;

        // 模拟路线
        this.simPath = [
          [23.1314, 113.2980],
          [23.1315, 113.2840],
          [23.1306, 113.2713],
          [23.1324, 113.2589],
          [23.1330, 113.2450]
        ];
        this.simStep = 0;
        this.simProgress = 0;
        this.simTimer = null;
        this.gpsWatchId = null;

        this.initDOM();
        this.initTheme();
        this.initMap();
        this.renderAllCameras();
        this.startTimeWatcher();
      }

      initDOM() {
        this.elSpeed = document.getElementById('inst-speed');
        this.elHeading = document.getElementById('inst-heading');
        this.elArrow = document.getElementById('inst-arrow');
        this.elEta = document.getElementById('inst-eta');

        this.elAlertCard = document.getElementById('alert-card');
        this.elAlertTitle = document.getElementById('alert-title');
        this.elAlertDesc = document.getElementById('alert-desc');
        this.elAlertDist = document.getElementById('alert-distance');
        this.elAlertProgress = document.getElementById('hud-progress');
        this.elBadgeStatus = document.getElementById('badge-status');
        this.elStatusText = document.getElementById('status-text');
        this.elDistBox = document.getElementById('hud-dist-box');
        this.elPeripheralFrame = document.getElementById('peripheral-alert-frame');

        document.getElementById('btn-mode-sim').onclick = () => this.setMode('sim');
        document.getElementById('btn-mode-gps').onclick = () => this.setMode('gps');
        document.getElementById('btn-dist-toggle').onclick = () => this.cycleWarningDistance();
        document.getElementById('btn-voice-toggle').onclick = () => this.toggleVoice();
        document.getElementById('btn-recenter').onclick = () => this.recenter();
        document.getElementById('btn-view-all').onclick = () => this.viewAllCameras();
        document.getElementById('btn-theme-toggle').onclick = () => this.cycleThemeMode();

        document.getElementById('btn-close-pwa-banner').onclick = () => {
          document.getElementById('pwa-install-banner').style.display = 'none';
        };
      }

      /* 初始化根据东八区自动设置主题 */
      initTheme() {
        const autoInfo = TimeThemeManager.getAutoTheme();
        this.themeMode = 'auto';
        this.applyTheme(autoInfo.theme, false);
      }

      /* 应用主题样式 */
      applyTheme(theme, announce = false) {
        this.currentTheme = theme;
        document.body.className = `theme-${theme}`;

        const iconSun = document.getElementById('icon-theme-sun');
        const iconMoon = document.getElementById('icon-theme-moon');
        const autoBadge = document.getElementById('theme-auto-badge');

        if (iconSun && iconMoon) {
          iconSun.style.display = (theme === 'sunlight') ? 'none' : 'block';
          iconMoon.style.display = (theme === 'sunlight') ? 'block' : 'none';
        }
        if (autoBadge) {
          autoBadge.style.display = (this.themeMode === 'auto') ? 'block' : 'none';
        }

        // 更新雷达扇面色泽
        if (this.radarSector) {
          const col = (theme === 'sunlight') ? '#0284c7' : '#00f2fe';
          const fill = (theme === 'sunlight') ? 'rgba(2, 132, 199, 0.20)' : 'rgba(0, 242, 254, 0.16)';
          this.radarSector.setStyle({ color: col, fillColor: fill });
        }

        if (announce) {
          const bj = TimeThemeManager.getBeijingDate();
          const timeStr = `${String(bj.getHours()).padStart(2, '0')}:${String(bj.getMinutes()).padStart(2, '0')}`;
          if (this.themeMode === 'auto') {
            audio.speak(`已开启东八区自动，北京时间${timeStr}，应用${theme === 'sunlight' ? '日间日光模式' : '夜间暗黑模式'}`);
          } else {
            audio.speak(theme === 'sunlight' ? '已手动设为日间日光模式' : '已手动设为夜间暗黑模式');
          }
        }
      }

      /* 循环切换主题模式: auto -> sunlight -> night -> auto */
      cycleThemeMode() {
        HapticsEngine.vibrate('toggle');
        if (this.themeMode === 'auto') {
          this.themeMode = 'sunlight';
          this.applyTheme('sunlight', true);
        } else if (this.themeMode === 'sunlight') {
          this.themeMode = 'night';
          this.applyTheme('night', true);
        } else {
          this.themeMode = 'auto';
          const autoInfo = TimeThemeManager.getAutoTheme();
          this.applyTheme(autoInfo.theme, true);
        }
      }

      /* 每 30 秒检查一次东八区时间，自动跨越日出/日落时切换 */
      startTimeWatcher() {
        setInterval(() => {
          if (this.themeMode === 'auto') {
            const autoInfo = TimeThemeManager.getAutoTheme();
            if (autoInfo.theme !== this.currentTheme) {
              this.applyTheme(autoInfo.theme, true);
            }
          }
        }, 30000);
      }

      initMap() {
        this.map = L.map('map', { zoomControl: false, attributionControl: false }).setView([this.currentPos.lat, this.currentPos.lng], 16);

        // 高德矢量街道瓦片
        L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
          subdomains: ['1', '2', '3', '4'],
          maxZoom: 19
        }).addTo(this.map);

        this.clusterGroup = L.markerClusterGroup({
          chunkedLoading: true,
          maxClusterRadius: 45,
          spiderfyOnMaxZoom: true,
          showCoverageOnHover: false,
          disableClusteringAtZoom: 17
        });
        this.map.addLayer(this.clusterGroup);

        // 车头标记
        const vehicleHtml = `<div class="vehicle-core" id="car-core"><div class="vehicle-pointer"></div></div>`;
        this.vehicleMarker = L.marker([this.currentPos.lat, this.currentPos.lng], {
          icon: L.divIcon({ html: vehicleHtml, className: 'custom-vehicle-icon', iconSize: [32, 32], iconAnchor: [16, 16] }),
          zIndexOffset: 2000
        }).addTo(this.map);

        // 静态纯净前方雷达扇面 (安定不晃眼)
        const isSun = (this.currentTheme === 'sunlight');
        this.radarSector = L.polygon([], {
          color: isSun ? '#0284c7' : '#00f2fe',
          weight: 1.8,
          fillColor: isSun ? 'rgba(2, 132, 199, 0.20)' : 'rgba(0, 242, 254, 0.16)',
          fillOpacity: 1,
          className: 'leaflet-radar-cone'
        }).addTo(this.map);

        this.updateRadarSector();

        window.addEventListener('resize', () => {
          setTimeout(() => { if (this.map) this.map.invalidateSize(); }, 200);
        });
      }

      renderAllCameras() {
        const camSvg = `
          <div class="camera-marker-pin">
            <svg viewBox="0 0 24 24"><path d="M4 4h3l2-2h6l2 2h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm8 3a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6z"/></svg>
          </div>
        `;
        const camIcon = L.divIcon({ className: 'custom-cam-icon', html: camSvg, iconSize: [28, 28], iconAnchor: [14, 28], popupAnchor: [0, -28] });

        const markers = [];
        this.markerInstances = [];

        ALL_POINTS.forEach((pt, idx) => {
          const m = L.marker([pt[0], pt[1]], { icon: camIcon });
          m.bindPopup(`
            <div style="font-weight:700;font-size:14px;color:#38bdf8;margin-bottom:4px;">📹 监控抓拍点</div>
            <div style="font-size:12px;color:#cbd5e1;line-height:1.5;">
              <strong>名称:</strong> ${pt[2]}<br>
              <strong>受控方向:</strong> ${this.directionParser.parsePointDirection(pt[2]).directionText}<br>
              <strong>坐标:</strong> ${pt[0].toFixed(5)}, ${pt[1].toFixed(5)}
            </div>
          `);
          m.pointIndex = idx;
          markers.push(m);
          this.markerInstances.push(m);
        });

        this.clusterGroup.addLayers(markers);
      }

      viewAllCameras() {
        this.mapFollow = false;
        this.map.fitBounds(this.clusterGroup.getBounds(), { padding: [40, 40] });
        audio.speak('已展开全广州摄像头分布');
      }

      /* 更新静态稳定雷达扇面 (跟随车头朝向平滑旋转，不再左右摇摆) */
      updateRadarSector() {
        const center = [this.currentPos.lat, this.currentPos.lng];
        const dist = this.warningDistance;
        const head = this.heading;
        const fov = this.fovAngle;
        const points = [center];
        const steps = 14;

        for (let i = 0; i <= steps; i++) {
          const deg = (head - fov + (fov * 2 * i / steps) + 360) % 360;
          points.push(MathUtils.calculateDestinationPoint(center[0], center[1], dist, deg));
        }
        points.push(center);
        this.radarSector.setLatLngs(points);

        const core = document.getElementById('car-core');
        if (core) core.style.transform = `rotate(${this.heading}deg)`;
      }

      /* 核心：航向预测、对向车道过滤与接近评估 */
      evaluateNearbyTargets() {
        let candidate = null;
        let candidateMarker = null;
        let minDistance = Infinity;
        const now = Date.now();

        if (this.distMode === 'auto') {
          this.warningDistance = this.speedEngine.update(this.speedKmh);
          document.getElementById('hud-sub-status').innerText = `自适应预警: ${this.warningDistance}米`;
        }

        for (let i = 0; i < ALL_POINTS.length; i++) {
          const p = ALL_POINTS[i];
          if (Math.abs(p[0] - this.currentPos.lat) > 0.012 || Math.abs(p[1] - this.currentPos.lng) > 0.012) continue;

          const dist = MathUtils.getDistance(this.currentPos.lat, this.currentPos.lng, p[0], p[1]);
          if (dist > this.warningDistance) continue;

          const bearingToPoint = MathUtils.getBearing(this.currentPos.lat, this.currentPos.lng, p[0], p[1]);
          const angleOffset = MathUtils.getAngleDiff(this.heading, bearingToPoint);
          if (angleOffset > this.fovAngle) continue;

          // 核心方向匹配: 对向车道反向静音过滤！
          const dirInfo = this.directionParser.parsePointDirection(p[2]);
          const matchResult = this.directionParser.evaluateRiderHeading(this.heading, dirInfo);
          if (!matchResult.shouldAlert) continue;

          if (dist < minDistance) {
            minDistance = dist;
            candidate = {
              index: i,
              lat: p[0],
              lng: p[1],
              title: p[2],
              cleanTitle: cleanSpeechTitle(p[2]),
              dist: Math.round(dist),
              angleOffset: Math.round(angleOffset)
            };
            candidateMarker = this.markerInstances[i];
          }
        }

        if (candidate) {
          if (this.activeMarker && this.activeMarker !== candidateMarker) {
            const el = this.activeMarker.getElement();
            if (el) {
              const pin = el.querySelector('.camera-marker-pin');
              if (pin) pin.classList.remove('alerting');
            }
          }

          this.activeTarget = candidate;
          this.activeMarker = candidateMarker;

          if (candidateMarker) {
            const el = candidateMarker.getElement();
            if (el) {
              const pin = el.querySelector('.camera-marker-pin');
              if (pin) pin.classList.add('alerting');
            }
          }

          const speedMs = Math.max((this.speedKmh * 1000 / 3600), 2.0);
          const etaSec = Math.round(candidate.dist / speedMs);

          this.updateAlertHUD(candidate, etaSec);
          bgKeeper.updateStatus(this.speedKmh, headingToText(this.heading), { dist: candidate.dist, title: candidate.cleanTitle, eta: etaSec });

          const lastAlert = this.alertedMap.get(candidate.index);
          if (!lastAlert || (now - lastAlert) > 30000) {
            this.alertedMap.set(candidate.index, now);
            audio.playApproachChime();
            HapticsEngine.vibrate(candidate.dist <= 50 ? 'urgent' : 'approach');
            audio.speak(`注意，前方${candidate.dist}米，${candidate.cleanTitle}`);
          }
        } else {
          if (this.activeMarker) {
            const el = this.activeMarker.getElement();
            if (el) {
              const pin = el.querySelector('.camera-marker-pin');
              if (pin) pin.classList.remove('alerting');
            }
            this.activeMarker = null;
          }

          if (this.activeTarget) {
            audio.playPassConfirmSound();
            HapticsEngine.vibrate('pass');
            this.activeTarget = null;
          }
          this.resetAlertHUD();
          bgKeeper.updateStatus(this.speedKmh, headingToText(this.heading), null);
        }
      }

      updateAlertHUD(target, etaSec) {
        this.elAlertTitle.innerText = target.cleanTitle;
        this.elAlertDesc.innerText = `前方同向路线 · 预计 ${etaSec} 秒后到达`;
        this.elAlertDist.innerText = target.dist;
        this.elEta.innerText = etaSec;

        const pct = Math.max(0, Math.min(100, (1 - target.dist / this.warningDistance) * 100));
        this.elAlertProgress.style.width = `${pct}%`;

        if (target.dist <= 50) {
          this.elAlertCard.className = 'alert-card status-danger';
          this.elBadgeStatus.className = 'badge-status danger';
          this.elStatusText.innerText = '即将通过 · 极近高危';
          this.elDistBox.className = 'hud-dist-box danger';
          this.elPeripheralFrame.className = 'peripheral-alert-frame danger';
          this.radarSector.setStyle({ color: '#ef4444', fillColor: 'rgba(239, 68, 68, 0.28)' });
        } else {
          this.elAlertCard.className = 'alert-card status-warning';
          this.elBadgeStatus.className = 'badge-status warning';
          this.elStatusText.innerText = '前方接近监控';
          this.elDistBox.className = 'hud-dist-box warning';
          this.elPeripheralFrame.className = 'peripheral-alert-frame warning';
          this.radarSector.setStyle({ color: '#f59e0b', fillColor: 'rgba(245, 158, 11, 0.25)' });
        }
      }

      resetAlertHUD() {
        this.elAlertCard.className = 'alert-card status-safe';
        this.elBadgeStatus.className = 'badge-status';
        this.elStatusText.innerText = '巡航雷达运行中';
        this.elDistBox.className = 'hud-dist-box';
        this.elAlertTitle.innerText = '前方道路通畅';
        this.elAlertDesc.innerText = `航向 ${headingToText(this.heading)} · 雷达守护中`;
        this.elAlertDist.innerText = '--';
        this.elEta.innerText = '--';
        this.elAlertProgress.style.width = '0%';
        this.elPeripheralFrame.className = 'peripheral-alert-frame';

        const isSun = (this.currentTheme === 'sunlight');
        const col = isSun ? '#0284c7' : '#00f2fe';
        const fill = isSun ? 'rgba(2, 132, 199, 0.20)' : 'rgba(0, 242, 254, 0.16)';
        this.radarSector.setStyle({ color: col, fillColor: fill });
      }

      updateCockpit() {
        this.elSpeed.innerText = this.speedKmh.toFixed(1);
        this.elHeading.innerText = headingToText(this.heading);
        this.elArrow.style.transform = `rotate(${this.heading}deg)`;
      }

      startSimulation() {
        this.stopSimulation();
        this.simStep = 0;
        this.simProgress = 0;
        this.speedKmh = 29.5;

        const tickInterval = 200;
        const speedMs = this.speedKmh * 1000 / 3600;
        const distPerTick = speedMs * (tickInterval / 1000);

        this.simTimer = setInterval(() => {
          if (this.simStep >= this.simPath.length - 1) {
            this.simStep = 0;
            this.simProgress = 0;
          }

          const p1 = this.simPath[this.simStep];
          const p2 = this.simPath[this.simStep + 1];

          const legDistance = MathUtils.getDistance(p1[0], p1[1], p2[0], p2[1]);
          const targetHeading = MathUtils.getBearing(p1[0], p1[1], p2[0], p2[1]);
          this.heading = this.headingEngine.update(targetHeading, this.speedKmh);

          this.simProgress += distPerTick / legDistance;
          if (this.simProgress >= 1.0) {
            this.simProgress = 0;
            this.simStep++;
          }

          const curLat = p1[0] + (p2[0] - p1[0]) * this.simProgress;
          const curLng = p1[1] + (p2[1] - p1[1]) * this.simProgress;

          this.currentPos = { lat: curLat, lng: curLng };
          this.vehicleMarker.setLatLng([curLat, curLng]);
          this.updateRadarSector();
          this.updateCockpit();
          this.evaluateNearbyTargets();

          if (this.mapFollow) this.map.panTo([curLat, curLng], { animate: false });
        }, tickInterval);
      }

      stopSimulation() {
        if (this.simTimer) {
          clearInterval(this.simTimer);
          this.simTimer = null;
        }
      }

      startGPS() {
        this.stopGPS();
        if (!('geolocation' in navigator)) {
          alert('当前浏览器不支持 GPS 定位');
          return;
        }

        let lastGpsPoint = null;

        this.gpsWatchId = navigator.geolocation.watchPosition(
          (pos) => {
            const wgsLat = pos.coords.latitude;
            const wgsLng = pos.coords.longitude;
            const [gcjLng, gcjLat] = CoordTransform.wgs84ToGcj02(wgsLng, wgsLat);

            if (pos.coords.speed !== null && pos.coords.speed >= 0) {
              this.speedKmh = pos.coords.speed * 3.6;
            }

            let rawH = pos.coords.heading;
            if (rawH === null || isNaN(rawH)) {
              if (lastGpsPoint) {
                const moveDist = MathUtils.getDistance(lastGpsPoint.lat, lastGpsPoint.lng, gcjLat, gcjLng);
                if (moveDist >= 2.0) {
                  rawH = MathUtils.getBearing(lastGpsPoint.lat, lastGpsPoint.lng, gcjLat, gcjLng);
                }
              }
            }

            this.heading = this.headingEngine.update(rawH, this.speedKmh);
            lastGpsPoint = { lat: gcjLat, lng: gcjLng };
            this.currentPos = { lat: gcjLat, lng: gcjLng };

            this.vehicleMarker.setLatLng([gcjLat, gcjLng]);
            this.updateRadarSector();
            this.updateCockpit();
            this.evaluateNearbyTargets();

            if (this.mapFollow) this.map.panTo([gcjLat, gcjLng], { animate: true });
          },
          (err) => console.warn('GPS Error:', err.message),
          { enableHighAccuracy: true, maximumAge: 1000, timeout: 10000 }
        );
      }

      stopGPS() {
        if (this.gpsWatchId !== null) {
          navigator.geolocation.clearWatch(this.gpsWatchId);
          this.gpsWatchId = null;
        }
      }

      setMode(mode) {
        this.mode = mode;
        const btnSim = document.getElementById('btn-mode-sim');
        const btnGps = document.getElementById('btn-mode-gps');
        if (mode === 'sim') {
          btnSim.classList.add('active');
          btnGps.classList.remove('active');
          this.stopGPS();
          this.startSimulation();
          audio.speak('已开启模拟骑行演练');
        } else {
          btnGps.classList.add('active');
          btnSim.classList.remove('active');
          this.stopSimulation();
          this.startGPS();
          audio.speak('已启动真机GPS高精巡航');
        }
      }

      cycleWarningDistance() {
        HapticsEngine.vibrate('toggle');
        const modes = ['auto', 80, 120, 160];
        let idx = modes.indexOf(this.distMode);
        this.distMode = modes[(idx + 1) % modes.length];

        const lbl = document.getElementById('lbl-dist-mode');
        if (this.distMode === 'auto') {
          lbl.innerText = '自适应';
          document.getElementById('hud-sub-status').innerText = '车速自适应预警';
          audio.speak('已切换为车速自适应预警模式');
        } else {
          this.warningDistance = this.distMode;
          lbl.innerText = `${this.distMode}米`;
          document.getElementById('hud-sub-status').innerText = `预警距离: ${this.distMode}米`;
          audio.speak(`预警距离已设为${this.distMode}米`);
        }
        this.updateRadarSector();
      }

      toggleVoice() {
        HapticsEngine.vibrate('toggle');
        audio.enabled = !audio.enabled;
        const btn = document.getElementById('btn-voice-toggle');
        const lbl = document.getElementById('lbl-voice');
        if (audio.enabled) {
          btn.classList.add('active');
          lbl.innerText = '语音开';
          audio.speak('语音播报已开启');
        } else {
          btn.classList.remove('active');
          lbl.innerText = '静音';
        }
      }

      recenter() {
        HapticsEngine.vibrate('tap');
        this.mapFollow = true;
        this.map.setView([this.currentPos.lat, this.currentPos.lng], 16, { animate: true });
      }
    }

    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js').catch(() => {});
      });
    }

    async function requestWakeLock() {
      if ('wakeLock' in navigator) {
        try { await navigator.wakeLock.request('screen'); } catch (e) {}
      }
    }
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') requestWakeLock();
    });

    let app = null;
    document.getElementById('btn-start-experience').addEventListener('click', () => {
      audio.init();
      audio.playApproachChime();
      audio.speak('骑行巡航雷达已启动，祝您骑行平安');

      bgKeeper.start();
      requestWakeLock();

      document.getElementById('start-overlay').style.display = 'none';

      const isIos = /iPad|iPhone|iPod/.test(navigator.userAgent);
      const isStandalone = window.navigator.standalone || window.matchMedia('(display-mode: standalone)').matches;
      if (isIos && !isStandalone) {
        setTimeout(() => { document.getElementById('pwa-install-banner').style.display = 'flex'; }, 3000);
      }

      app = new RadarCruiseApp();
      app.startSimulation();
    });
  </script>
</body>
</html>
'''

with open('rider_radar.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

print("rider_radar.html successfully regenerated! Size:", len(html_template), "bytes")
