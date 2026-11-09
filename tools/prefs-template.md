# 配置清单（脱敏模板）

> 这是一份**核对清单**，不是可直接导入的配置文件。所有 `<...>` 都需替换成你自己的值。
> **不要把填好凭据的版本提交到任何仓库。** 建议在 Kiosk 浏览器的设置界面 / 远程管理页里逐项填写。
> 涉及内部设置键名，用于排查「值被重置」类问题；不同版本界面文案可能略有差异。

## 页面与认证

| 设置项 | 值 | 备注 |
| --- | --- | --- |
| `startURL` | `http://<HA_HOST>:8123` | 局域网地址，也可用 HTTPS |
| `authUsername` | `<HA_USERNAME>` | 仅用于 HTTP 基础认证 |
| `authPassword` | `<HA_PASSWORD>` | **绝不外传** |
| `websiteIntegration` | `true` | 需要相应授权版本支持 |

## 显示与性能

| 设置项 | 值 | 备注 |
| --- | --- | --- |
| `initialScale` | `0` | 自动；不要靠缩放去修布局错乱 |
| `fontSize` | `100` | 百分比 |
| `useWideViewport` | `true` | |
| `desktopMode` | `false` | |
| `userAgent` | `custom` | 见 [性能调优](../docs/03-performance.md) |
| `customUserAgent` | 原 UA，仅把 `Chrome/<版本>` 改为 `Chrome/131.0.0.0` | 其余字段保持原样 |
| `injectJsCode` | 空 | 排障用的临时注入，正式配置应清空 |

## 屏保与省电

| 设置项 | 值 | 备注 |
| --- | --- | --- |
| `timeToScreensaverV2` | `30` | **秒**；`0` = 关闭 |
| `screensaverWallpaperURL` | `file:///sdcard/Download/clock.html` | 本地静态页 |
| `screensaverBrightness` | `60` | 0–255 |
| `screensaverPlaylist` | 单条，`type` 为整数 `0` | 写成字符串会解析失败 |
| `reloadOnScreensaverStop` | `false` | 关闭唤醒整页重载，壁挂场景更省电 |
| `skipReloadIfStartUrlShowing` | `true` | 已在首页时跳过无谓重载 |
| `stopScreensaverOnMotion` | `true` | 触摸唤醒 |
| `keepScreenOn` | `true` | |
| `sleepSchedule` | `[{"sleepTime":"08:00","wakeupTime":"18:00","dayOfWeek":9},{"sleepTime":"23:30","wakeupTime":"07:00","dayOfWeek":8}]` | 作息矩阵，见下 |

## 夜间定时休眠

`sleepSchedule` 是**一个 JSON 字符串**，不是布尔开关。本项目实际是两个条目的数组（格式与取值来自应用内 `dayofweek_array`，以本版本为准）：

```json
[
  {"sleepTime":"08:00","wakeupTime":"18:00","dayOfWeek":9},
  {"sleepTime":"23:30","wakeupTime":"07:00","dayOfWeek":8}
]
```

| 字段 | 说明 |
| --- | --- |
| `sleepTime` | 关屏时间 `HH:mm` |
| `wakeupTime` | 唤醒时间 `HH:mm`，**小写 u**；写成 `wakeUpTime` 会解析失败 |
| `dayOfWeek` | `0` 禁用、`1`–`7` 周日到周六、`8` **每天**、`9` 周一至周五、`10` 周末 |

- 数组可写多组规则；跨午夜不需要特殊处理，sleep 与 wakeup 会各自算出下一次闹钟。应用采用滚动排程，通常只提前排最近一次事件，到点后再排下一个。
- 需要设备管理员权限才能关屏；写完配置**必须重启应用**才会重排闹钟。
- 校验：`adb shell "dumpsys alarm | grep -E 'triggerTime=.*(08:00|18:00|23:30|07:00)'"`，日志里应有 `Alarm sleep set` / `Alarm wakeup set`。
- **休眠 ≠ 屏保**：休眠是真关屏，触摸点不亮，只能按电源键、等到定时闹钟或用 REST `screenOn`。详见 [04 坑 5](../docs/04-screensaver-power.md)。

## 远程管理与光感联动

应用自身不读系统光线传感器（`screenOffInDarkness` 走摄像头帧亮度，不推荐）。可行方案是 HA 光照度实体 + 远程管理 REST 的 `screenOff` / `screenOn`，实测两条命令均返回 `200 OK` 且屏幕状态随之变化，定时休眠期间也能提前点亮。脱敏示例见 [`tools/ha-light-automation-example.yaml`](ha-light-automation-example.yaml)。

本项目已在平板上**常开远程管理**（仅本地网络），相关键：

| 设置项 | 值 | 备注 |
| --- | --- | --- |
| `remoteAdmin` | `true` | 启用远程管理与 REST 接口（默认端口 `2323`） |
| `remoteAdminLan` | `true` | 来自本地网络；配套 `cloudService=false` 不暴露公网 |
| `remoteAdminPassword` | 强随机串 | **绝不外传**，HA 自动化里用它调 REST |
| `cloudService` | `false` | 关闭公网远程，避免 2323 出公网 |
| `remoteAdminScreenshot` / `remoteAdminCamshot` | `true` / `false` | 按需；Camshot 需要开动作检测，本项目关 |

> 安全：REST 是 HTTP 明文，密码经过局域网。已关闭公网通道、仅开本地网络；建议路由器再限制只有 HA 主机可访问 `2323`。深夜深度 Doze 下 WiFi 省电可能让外部请求延迟，07:00 / 18:00 的 AlarmManager 唤醒仍是最可靠的一环。

## 无人值守稳定性（壁挂长期运行）

| 设置项 | 值 | 备注 |
| --- | --- | --- |
| `restartOnCrash` | `true` | 应用崩溃后自动重启 |
| `restartAfterUpdate` | `true` | 应用 / WebView 更新后自动重启 |
| `runInForeground` | `true` | 前台服务，降低被系统回收的概率，被结束后拉起 |
| `reloadPageFailure` | `30` | 页面加载失败 30 秒后自动重载 `startURL`；`0` = 禁用 |
| `errorURL` | `file:///sdcard/Download/offline.html?target=<URL 编码后的 HA 地址>` | 连接错误时显示本地提示页，见下 |
| `screenBrightness` | `167` | 固定亮度基准，**根治坑 2**；留空则跟随系统 |
| `enableZoom` | `false` | 防止误触双指缩放把 HA 放大 |
| `jsAlerts` | `false` | 防止 JS 警告框卡住壁挂操作 |

`assets/offline.html` 是纯静态断网提示页，页面本身不含任何内网地址：目标地址由 `errorURL`
的查询参数 `?target=`（URL 编码）传入，页面每 20 秒尝试跳回一次。配合
`reloadPageFailure` 形成双保险——HA 重启、路由器抽风时平板显示中文提示并自动重连，
而不是浏览器错误页或白屏。实机验证方法：临时把 `startURL` 改成 `http://127.0.0.1:9`，
重启应用应出现「服务暂不可用」倒计时页，改回 `startURL` 后自动恢复。

> `errorURL` 在部分版本标记为 PLUS 功能，是否可用请以实机为准（本项目的修改版实测可用）。

## 不要出现的旧键

旧版本残留的 `timeToScreensaver`、`screensaverURL` 会触发启动时的配置迁移，把 `timeToScreensaverV2` 重置为 `0`，导致屏保永不触发。核对时若发现这两个键，删掉，**只保留新键**。

## 亮度基准

正常亮度建议 `167`（0–255），屏保 `60`。若唤醒后停在 `60`，按 [04 的顺序](../docs/04-screensaver-power.md) 重置系统亮度并重启应用。
