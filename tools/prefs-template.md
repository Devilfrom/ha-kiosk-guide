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
| `reloadOnScreensaverStop` | `true` | 唤醒后回到 HA |
| `stopScreensaverOnMotion` | `true` | 触摸唤醒 |
| `keepScreenOn` | `true` | |

## 不要出现的旧键

旧版本残留的 `timeToScreensaver`、`screensaverURL` 会触发启动时的配置迁移，把 `timeToScreensaverV2` 重置为 `0`，导致屏保永不触发。核对时若发现这两个键，删掉，**只保留新键**。

## 亮度基准

正常亮度建议 `167`（0–255），屏保 `60`。若唤醒后停在 `60`，按 [04 的顺序](../docs/04-screensaver-power.md) 重置系统亮度并重启应用。
