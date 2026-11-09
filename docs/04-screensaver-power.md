# 04 时钟屏保与省电

## 自建时钟页

`assets/clock.html` 是一个纯静态黑底中文时钟页，无外部依赖。把它放到设备本地，屏保 WebView 直接以 `file://` 加载，断网也能显示：

```bash
adb push assets/clock.html /sdcard/Download/clock.html
```

页面每秒 `tick()` 一次更新时间与中文星期，字号用 `vw` 自适应，底部有一行说明文字。

## 关键设置项

以下都能在 Kiosk 浏览器的设置界面 / 远程管理页找到对应项（名称以 Fully Kiosk 为例）：

| 设置项 | 建议值 | 说明 |
| --- | --- | --- |
| `startURL` | `http://<HA_HOST>:8123` | 启动页 |
| `authUsername` / `authPassword` | 你的 HA 凭据 | HTTP 基础认证自动填入，**不要写进任何公开文件** |
| `timeToScreensaverV2` | `30` | 单位是**秒**；`0` 表示不启用 |
| `screensaverWallpaperURL` | `file:///sdcard/Download/clock.html` | 屏保实际加载的地址 |
| `screensaverBrightness` | `60` | 0–255，写入 `Settings.System.screen_brightness` |
| `screensaverPlaylist` | 单条、`type` 为**整数** `0` | `type` 写成字符串会解析失败 |
| `reloadOnScreensaverStop` | `true` | 唤醒后重新加载 HA |
| `stopScreensaverOnMotion` | `true` | 触摸唤醒 |
| `keepScreenOn` | `true` | 保持屏幕常亮 |

完整的脱敏清单见 [`tools/prefs-template.md`](../tools/prefs-template.md)。

## 两个真实的坑

### 坑 1：屏保永远不触发，亮度也不变

现象：静置远超设定时间，亮度仍是正常值，画面没有切换。

原因：某些版本存在**旧配置键迁移逻辑**。如果配置里还残留旧键 `timeToScreensaver` 或 `screensaverURL`，应用启动时会把新键 `timeToScreensaverV2` 重写为 `0`，然后删除旧键——于是屏保被静默禁用。

排查与处理：

```bash
adb shell settings get system screen_brightness   # 静置后仍为正常值 = 屏保没触发
```

处理时**只写新键 `timeToScreensaverV2`，绝不写旧键**；改配置前先完全停止应用（`am force-stop`），否则内存中的配置会覆盖回去。

### 坑 2：唤醒后亮度回不到正常值

屏保会把 `60` 直接写进系统亮度设置。如果某次唤醒没恢复成功，下一次进入屏保时应用读到的「正常亮度」就变成了 60，形成卡在 60 的循环。

修复顺序（顺序不能乱）：

```bash
adb shell settings put system screen_brightness 167
adb shell am force-stop de.ozerov.fully
adb shell am start -n de.ozerov.fully/.FullyActivity
```

## 回归验证

```bash
adb shell settings put system screen_brightness 167
# 静置超过设定时间
adb shell "sleep 36; settings get system screen_brightness"   # 期望 60
adb shell screencap -p /sdcard/Download/saver.png             # 应为时钟屏保
adb shell input tap 1000 700
adb shell "sleep 6; settings get system screen_brightness"    # 期望 167
adb shell dumpsys activity activities | grep mResumedActivity # 应仍在 Kiosk 应用
```
