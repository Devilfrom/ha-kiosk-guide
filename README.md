# 旧平板改造 Home Assistant 壁挂中枢：部署与性能调优笔记

把一台 **Xiaomi Mi Pad 3（Android 7.0 / API 24）** 做成常亮的 Home Assistant 控制面板的实践记录。重点不是「怎么装软件」，而是老设备上 **HA 前端显示错乱、CPU 吃满、卡顿、屏保不触发** 这几个问题的定位过程和可复现解法。

> **本仓库不包含任何第三方 APK、反编译代码、对第三方应用的二进制修改，也不包含账号凭据。**
> Fully Kiosk Browser 是商业软件，请从官方渠道获取并自行购买授权。本仓库只记录配置方法、诊断思路、自建页面与脚本；文中所有设置项都可通过应用的官方设置界面或远程管理页配置。

## 环境

| 项 | 值 |
| --- | --- |
| 设备 | Xiaomi Mi Pad 3 (`cappu`)，1536×2048，Android 7.0 / API 24，未 root |
| 智能家居平台 | Home Assistant 2026.x，局域网 HTTP 访问 |
| Kiosk 浏览器 | Fully Kiosk Browser 1.36.1（官方版本） |
| WebView | Android System WebView 109.0.5414.118（Android 7.0 的理论上限为 119） |
| 调试通道 | `adb`，无需 root |

## 三个问题，三句话结论

| 现象 | 真正原因 | 解法 |
| --- | --- | --- |
| HA 变成「左侧栏 + 中间窄列 + 右侧大片空白」 | 系统 WebView 停留在 Chrome 64，新版 HA 前端大量 JS 报错，masonry 布局退化 | 升级 WebView → [02](docs/02-webview-upgrade.md) |
| 修好显示后平板明显卡顿，Fully 独占约 78% CPU | HA 要求浏览器 Chrome ≥ 131 才下发现代前端，老 WebView 只能拿到 `frontend_es5` 兼容包 | 让浏览器上报较新的 UA → [03](docs/03-performance.md) |
| 屏保不触发、亮度恢复异常 | 旧配置键迁移把计时重置为 0；屏保把亮度写进系统设置污染了基准 | 见 [04](docs/04-screensaver-power.md) |

一个反直觉的点：**升级 WebView 之后才会觉得卡**。因为升级前 HA 组件根本没初始化成功，页面处于「半死」状态、负载很低；修好后所有卡片、WebSocket 订阅才真正跑起来，老硬件的性能上限就暴露了。

## 目录

- [01 目标与整体结构](docs/01-overview.md)
- [02 WebView 升级：修复 HA 显示错乱](docs/02-webview-upgrade.md)
- [03 性能调优：从 78% CPU 到 20%](docs/03-performance.md)
- [04 时钟屏保与省电](docs/04-screensaver-power.md)
- [05 已知限制与回滚](docs/05-limits-and-rollback.md)
- `assets/clock.html` — 自建黑底中文时钟屏保页
- `assets/clock-forest.html` — 背景图版时钟屏保页（背景图需自备，见 [04](docs/04-screensaver-power.md)）
- `tools/perf_sample.py` — 通过 adb 采样 CPU 与掉帧
- `tools/prefs-template.md` — 脱敏的配置清单

## 实测效果

| 指标 | 调优前（ES5 包） | 调优后（现代前端） |
| --- | --- | --- |
| HA 前端资源 | `frontend_es5/app.*.js` | `frontend_latest/app.*.js` |
| Fully CPU（单核当量） | 78.2% | 20.2% |
| 应用内存 PSS | 285 MB | 168 MB |
| 12 秒空闲重绘 | 70 帧，82.9% 掉帧 | 0 帧（不再空转） |
| 控制台硬错误 | 0（升级 WebView 后） | 0 |

> 更早的 Chrome 64 阶段有 30 条硬错误（`assignedElements is not a function`、`AbortController is not defined`、`Failed to construct 'HTMLElement'` 等），那才是显示错乱的根因。

## 免责声明

本文是个人设备上的实践记录，涉及系统组件升级和浏览器 UA 调整，操作前请自行备份数据。修改 UA 属于兼容性技巧，不保证未来版本的 Home Assistant 依然适用。
