# 05 已知限制与回滚

## 已知限制

| 限制 | 说明 |
| --- | --- |
| 开机自启动 | MIUI 会拦截 `BOOT_COMPLETED`，应用进程在重启后不存在；`pm enable` 改组件状态会被系统拒绝，`cmd package set-home-activity` 设默认桌面后重启仍会被系统桌面抢回。未 root 且非 device owner，暂时无解 |
| 返回键 / HOME | 仍可退回系统桌面，无法锁定任务 |
| WebView 天花板 | Android 7.0 最高 119，达不到 HA 现代前端要求的 Chrome 131，只能靠 UA 技巧或换设备 |
| UA 兼容性 | 属于客户端侧的技巧，HA 升级后可能失效 |
| 亮度基准 | 屏保会写系统亮度设置，异常中断后需按 [04](04-screensaver-power.md) 的顺序重置 |

## 回滚清单

### 回滚 UA（回到 ES5 兼容包）

把 User Agent 设置改回「默认 / 系统 UA」，重启 Kiosk 浏览器即可。

```bash
adb logcat -c
adb shell am force-stop de.ozerov.fully
adb shell am start -n de.ozerov.fully/.FullyActivity
adb logcat -d | grep -oE 'frontend_(es5|latest)/[^ ]+\.js' | sort -u
# 期望回到 frontend_es5
```

代价：CPU 回到约 78%，但兼容性最保守。

### 回滚 WebView（回到系统原版）

```bash
adb shell pm uninstall com.google.android.webview
adb shell dumpsys package com.google.android.webview | grep -E 'versionName|codePath'
# codePath 应回到 /system/app/WebViewGoogle
```

注意：回到 Chrome 64 后 HA 会再次出现布局错乱，一般不建议。

### 回滚屏保 / 亮度

- `timeToScreensaverV2` 设回 `0`；
- `screensaverWallpaperURL` 设回应用默认值；
- `settings put system screen_brightness 167` 后重启应用。

## 升级 HA 时的检查顺序

1. 看 `adb logcat -d | grep INFO:CONSOLE`，确认没有新增硬错误；
2. 确认加载的是 `frontend_latest` 还是 `frontend_es5`；
3. 跑一次 `python tools/perf_sample.py 12`，对比 CPU 基线；
4. 若前端报错或白屏，先回滚 UA，再排查 WebView 版本。

## 若要换设备

最省事的是把系统升到 Android 8+ 的设备：WebView 可到 131+，不需要任何 UA 技巧，HA 直接下发现代前端，自启动和 Kiosk 锁定也更可控。
