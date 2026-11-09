# 04 时钟屏保与省电

## 自建时钟页

`assets/clock.html` 是一个纯静态黑底中文时钟页，无外部依赖。把它放到设备本地，屏保 WebView 直接以 `file://` 加载，断网也能显示：

```bash
adb push assets/clock.html /sdcard/Download/clock.html
```

页面每秒 `tick()` 一次更新时间与中文星期，字号用 `vw` 自适应，底部有一行说明文字。

## 背景图版时钟页（当前实机定稿）

`assets/clock-forest.html` 是进一步改造的版本：**全时段一张暗系背景图、原图直出、不加任何遮罩或模糊**，白色时钟常驻。背景本身偏暗，所以文字全天固定白色，不能再按 07:00/19:00 切成深色字；代码里没有任何时段或主题分支，白天夜里长得一模一样。

> 本仓库的 `.gitignore` 忽略所有图片文件，**背景图不包含在公开仓库里**。请自备一张 4:3 的暗系图片，命名为 `bg-forest.jpg` 放到同目录；图片缺失时页面会自动回退内置暗色渐变，右上角标签变成「森林车站 · 渐变兜底」，不会黑屏。请勿把网络下载的壁纸提交到公开仓库。

部署时沿用 `clock.html` 这个文件名，`screensaverWallpaperURL` 与 `screensaverPlaylist` 都无需改动：

```bash
MSYS_NO_PATHCONV=1 adb push assets/clock-forest.html /sdcard/Download/clock.html
MSYS_NO_PATHCONV=1 adb push bg-forest.jpg /sdcard/Download/bg-forest.jpg
MSYS_NO_PATHCONV=1 adb shell "am force-stop de.ozerov.fully"
MSYS_NO_PATHCONV=1 adb shell "am start -n de.ozerov.fully/.FullyActivity"
```

要点：

- 页面用 `Image` 依次尝试相对路径 `bg-forest.jpg` 和绝对路径 `file:///sdcard/Download/bg-forest.jpg`，两者都失败才保留渐变兜底。Android 7 + WebView 109 下 `file://` 同目录图片可正常加载，已实机验证。
- 背景图建议裁到 1536×1152（4:3）、压到 400 KB 以内；老设备直接解码 4K 原图会吃掉几十 MB 内存。
- **右上角标签就是排查信号**：显示「森林车站 · 常驻」= 图片加载成功；显示「…渐变兜底」= 图片路径或权限不对。
- 选图经验：主体不居中的风景图最合适；「主体占满中央的特写」会跟中央 22vw 大时钟抢位置，无遮罩下字容易压在脸上。
- `screensaverBrightness` 为 60/255，暗系壁纸在实机上会偏暗，觉得不够亮可调到 80–90（注意下面的坑 2）。
- `adb shell screencap` 抓的是 framebuffer，**不受背光亮度影响**，截图会比肉眼看到的亮，验收时以实机为准。

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
| `reloadOnScreensaverStop` | `false` | **关闭唤醒整页重载**，见坑 3 |
| `skipReloadIfStartUrlShowing` | `true` | 已在首页时跳过无谓重载 |
| `stopScreensaverOnMotion` | `true` | 触摸唤醒 |
| `keepScreenOn` | `true` | 保持屏幕常亮 |

完整的脱敏清单见 [`tools/prefs-template.md`](../tools/prefs-template.md)。

## 四个真实的坑

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

**根治**：把 Kiosk 应用的设置项「屏幕亮度」（`screenBrightness`）设为 `167`，留空才是跟随系统默认。应用启动时会把这个值写回系统设置，所以无论上次停在什么亮度，基准都会被拉回 167。实测 `100 →(启动) 167 →(屏保) 60 →(唤醒) 167`，屏保亮度不受影响。配置模板见 [`tools/prefs-template.md`](../tools/prefs-template.md)。

### 坑 3：每次点亮唤醒都重新「进入网站」

现象：进屏保后再唤醒，HA 会重走一遍加载流程（闪「加载中…」、重新拉前端资源），慢且费电，
壁挂大屏上尤其明显。

原因：`reloadOnScreensaverStop = true` 时，屏保停止会调用一次整页 reload 回到 `startURL`。
注意**进入屏保并不会重载 HA**——那只是屏保 WebView 加载本地 `clock.html`，
日志里是 `file://` 地址，很容易被误判成「又进了一次网站」。

处理：把 `reloadOnScreensaverStop` 设为 `false`，并把 `skipReloadIfStartUrlShowing`
设为 `true`（已经停在首页时，跳过其它路径触发的无谓重载）。屏保期间主 WebView 只是被
Fragment 覆盖、没有被销毁，HA 前端的 WebSocket 持续连接并自动重连，实体状态照常实时更新，
不需要靠整页刷新。

验证方法（临时探针，测完**务必清空** `injectJsCode`）：

```js
console.log('PAGE_BOOT|' + location.href + '|' + Date.now());
```

写入 `injectJsCode` 后重启应用，清空 logcat，静置触发屏保再唤醒：

```bash
adb logcat -c
adb shell "sleep 36"                        # 进屏保：日志只应有 file:///.../clock.html
adb shell "input tap 1000 700; sleep 6"
adb logcat -d | grep PAGE_BOOT             # 优化前有 1 条 HA URL，优化后应为 0 条
```

若确实需要「唤醒即强制刷新」，把 `reloadOnScreensaverStop` 改回 `true` 即可。

### 坑 4：重启应用后屏保一直不触发

现象：`am force-stop` + `am start` 冷启动后，静置远超 30 秒仍是 HA 首页，
系统亮度也没变成 60，日志里没有任何屏保相关记录。

原因：idle 计时器由用户交互启动/复位；冷启动后完全没有触摸事件时，计时器不会自己跑起来。
这不是配置错误，配置里 `timeToScreensaverV2` 仍是 30。

处理：启动后模拟一次轻触再静置，点在页面空白处避免误触卡片：

```bash
MSYS_NO_PATHCONV=1 adb shell "input tap 400 40"
MSYS_NO_PATHCONV=1 adb shell "sleep 38; settings get system screen_brightness"   # 60 = 已触发
```

实机闭环：先 `settings put system screen_brightness 167` → 轻触 → 静置 38 秒读到 60
→ 触摸唤醒读回 167。唤醒后的 HA 首页与初始首页几乎逐字节一致（无重载白屏）。

## 回归验证

```bash
adb shell settings put system screen_brightness 167
adb shell "input tap 400 40"                                # 冷启动后必须有这一次交互
# 静置超过设定时间
adb shell "sleep 38; settings get system screen_brightness"  # 期望 60
adb shell screencap -p /sdcard/Download/saver.png            # 应为时钟屏保
# 背景图版：右上角标签应为「森林车站 · 常驻」，出现「渐变兜底」说明图片没加载上
adb shell input tap 1000 700
adb shell "sleep 6; settings get system screen_brightness"   # 期望 167
adb shell dumpsys activity activities | grep mResumedActivity # 应仍在 Kiosk 应用
```
