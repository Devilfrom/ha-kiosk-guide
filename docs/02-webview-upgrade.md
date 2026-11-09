# 02 WebView 升级：修复 HA 显示错乱

## 症状

横屏 2048×1536 下，HA 概览退化成「左侧导航栏 + 中间一条窄卡片列 + 右侧约 38% 空白」，顶部工具栏不完整，卡片只显示一部分。

## 先排除「缩放」这个错误方向

用 Kiosk 浏览器打开一个本地探测页，读取真实视口：

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
<pre id="o"></pre>
<script>
var vv = window.visualViewport;
document.getElementById('o').textContent = [
  'innerWidth       = ' + innerWidth,
  'innerHeight      = ' + innerHeight,
  'devicePixelRatio = ' + devicePixelRatio,
  'visual scale     = ' + (vv ? vv.scale : 'n/a'),
  'UA               = ' + navigator.userAgent
].join('\n');
</script>
```

实测结果：

```text
innerWidth       = 1024
innerHeight      = 768
devicePixelRatio = 2
visual scale     = 1
UA               = ... Chrome/64.0.3282.137 ...
```

视口、DPR、缩放全部正常。改 `wm density`（试过 400）、关缩放、开「每次重置缩放」都没有根本改善——**问题不在布局尺寸，在 JS 没跑起来**。

## 真正的原因

`adb logcat -d | grep INFO:CONSOLE` 里，HA 的 `frontend_es5` 报了大量硬错误：

```text
Uncaught (in promise) TypeError: assignedElements is not a function
Uncaught (in promise) ReferenceError: AbortController is not defined
Uncaught InvalidStateError: Failed to construct 'HTMLElement'
Uncaught SyntaxError: Invalid or unexpected token
Failed to load extra module /hacsfiles/iconset.js
```

Chrome 64 缺少这些 API，自定义组件初始化失败，masonry 布局退化成单列窄条。

## 版本选择

| 项 | 说明 |
| --- | --- |
| 设备系统 | Android 7.0 / API 24，ARM64 |
| WebView 可用范围 | 支持 API 24 的最后一版是 **119.0.6045.194**；Chrome 131+ 需要 Android 8.0+ |
| 本例采用 | `109.0.5414.118`，versionCode `541411803`，minSdk 24 |
| 文件大小 / MD5 | `108,612,469` B / `e1bb9a3c149321ad1dd570b986173651` |

> 仓库不提供 APK。请从可信渠道获取与设备 ABI 匹配的官方签名包，并按下面的方法校验后再装。

## 安装前必须做的两项校验

**1. ABI**：64 位应用进程需要 64 位 WebView 库。解压检查：

```bash
python -c "import zipfile;z=zipfile.ZipFile('webview.apk');print(sorted({n.split('/')[1] for n in z.namelist() if n.startswith('lib/')}))"
# 期望包含 ['arm64-v8a', 'armeabi-v7a']
```

**2. 签名证书**：系统 WebView 属于系统应用，更新的签名证书必须与原版一致，否则安装会失败或导致所有 WebView 应用崩溃。

```bash
adb pull /system/app/WebViewGoogle/WebViewGoogle.apk sys-webview.apk
keytool -printcert -jarfile sys-webview.apk | grep SHA256
```

Google 官方 `CN=webview, O=Google Inc.` 证书指纹：

```text
SHA1:   1F:38:7C:B2:5E:00:69:EF:CA:49:0A:DE:28:C0:60:E0:9D:37:DD:45
SHA256: 6F:AF:3C:41:40:40:74:73:40:09:34:D1:17:81:5A:21:AF:1C:FE:FC:5C:0B:EE:61:C8:58:BC:3D:72:BA:6F:E5
```

新版 WebView 多为 v2/v3 签名（没有 `META-INF/CERT.RSA`），需要解析 APK Signing Block 才能取到证书；只要指纹与上表一致即可覆盖安装。

## 安装

部分环境下 `adb install -r` 的流式传输不稳定，更稳的是先推到设备再在设备端安装：

```bash
adb push webview.apk /sdcard/Download/webview.apk
adb shell "pm install -r /sdcard/Download/webview.apk"
# Success
```

新包会落到 `/data/app/com.google.android.webview-1`，`/system` 里的原版保持不变。

## 验证

```bash
adb shell dumpsys package com.google.android.webview | grep -E 'versionName|codePath'
adb logcat -d | grep -E 'WebViewFactory|cr_WebViewApkApp'
# WebViewFactory: Loading com.google.android.webview version 109.0.5414.118
```

再重新打开 HA，硬 JS 错误应归零，布局恢复成正常的两列 masonry。

**可回滚**：`adb shell pm uninstall com.google.android.webview` 会移除系统应用的更新，回到 `/system` 里的原版。
