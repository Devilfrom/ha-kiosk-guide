# 03 性能调优：从 78% CPU 到 20%

## 先量化，别猜

```bash
adb shell dumpsys cpuinfo | head -12       # 各进程 CPU 占比
adb shell dumpsys meminfo de.ozerov.fully  # 应用内存 PSS
adb shell dumpsys gfxinfo de.ozerov.fully  # 帧率 / janky / 百分位
adb shell cat /proc/loadavg
adb shell cat /proc/meminfo | head -5
adb shell dumpsys battery | grep temperature
adb shell cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
```

本例实测：

| 指标 | 数值 | 结论 |
| --- | --- | --- |
| Fully 进程 CPU | **77~78%**（system_server 仅 10%） | 负载几乎全部来自 Kiosk 浏览器里的 HA 前端 |
| loadavg (1/5/15) | 10.47 / 9.70 / 8.94 | 六核设备明显过载 |
| 12 秒渲染帧数 | 70 帧（≈6 fps），janky 82.9% | 页面在持续、低效地重绘 |
| 累计 janky 比例 | 39.67%，p90 28ms / p99 69ms | 用户感知的「卡卡」 |
| 内存 | MemAvailable 2.4 GB，应用 PSS 285 MB | **不是内存不足** |
| 温度 / 频率 | 32°C，1105/1703 MHz | **没有热降频，硬件没毛病** |

所以答案是「软件负载」，不是设备老化。

## 根因：HA 给老浏览器发了兼容包

抓取 HA 首页 HTML，里面有一段浏览器能力判定：

```js
var isModern = /...Chrom(ium|e)\/(13[1-9]|1[4-9]\d|[2-9]\d{2}|\d{4,})\.\d+.../
  .test(navigator.userAgent) && "findLast" in Array.prototype;

isModern && (import("/frontend_latest/core.*.js"), import("/frontend_latest/app.*.js"), ...);
window.latestJS || (_ls("/frontend_es5/core.*.js", true), _ls("/frontend_es5/app.*.js", true));
```

也就是说 **Chrome ≥ 131 才走 `frontend_latest`**。WebView 109（甚至 Android 7.0 的上限 119）都够不到，只能拿到 `frontend_es5`：为老浏览器编译的兼容包，体积大、polyfill 多、持续重绘。这才是 CPU 大户。

## 解法：在 Kiosk 浏览器侧上报较新的 UA

这不是改 HA 服务端，也不需要 root：Fully Kiosk 的 **User Agent → Custom** 是官方设置项。做法是**只把 UA 里的 Chrome 版本号改成 `131.0.0.0`，其余字段一律保持原样**：

```text
Mozilla/5.0 (Linux; Android 7.0; <设备> Build/<ID>; wv) AppleWebKit/537.36
  (KHTML, like Gecko) Version/4.0 Chrome/131.0.0.0 Safari/537.36
```

判定里还要求 `"findLast" in Array.prototype`，Chrome 109 的 V8 已支持，所以能通过。设置后重启 Kiosk 浏览器即可。

验证是否生效：

```bash
adb logcat -c
# 重新打开 HA 后
adb logcat -d | grep -oE 'frontend_(es5|latest)/[^ ]+\.js' | sort -u
# 期望：frontend_latest/app.*.js
adb logcat -d | grep INFO:CONSOLE | grep -icE 'uncaught|not a function|not defined|syntaxerror'
# 期望：0
```

实测点击交互后硬错误仍为 0，页面反而更完整（区域网格、摘要列表全部渲染出来）。

## 前后对比

| | ES5 兼容包 | 现代前端 |
| --- | --- | --- |
| Fully CPU（单核当量） | 78.2% | **20.2%** |
| 内存 PSS | 285 MB | **168 MB** |
| 12 秒空闲重绘 | 70 帧 | **0 帧** |
| 硬 JS 错误 | 0 | 0 |

剩余约 20% 是 HA 的 WebSocket 心跳 + Kiosk 浏览器自身定时器，六核设备完全可接受。静止时不再重绘，是最直观的改善。

## 用 `tools/perf_sample.py` 自己复测

```bash
adb devices
python tools/perf_sample.py 12
```

脚本两次读取 `/proc/<pid>/stat` 的 `utime+stime` 计算单核当量 CPU，并重置后读取 `gfxinfo` 的帧数 / janky / p90。

```text
window=12s pid=5502
Fully CPU : 78.2% (single-core equivalent)
loadavg1  : 10.00
frames    : 70   janky: 82.86%   p90: 28ms
```

## 风险与备选

- **这是兼容性技巧，不是官方支持**。HA 未来升级可能提高浏览器阈值，或真正用上 Chrome 131+ 的 API；届时要么调高 UA 版本号，要么回滚到 ES5 包（代价是重新变卡）。
- Chrome 109 不支持 `popover` API，控制台会有 5 条无害警告，不影响功能。
- 更稳的补充：把 WebView 升到 **119**（Android 7.0 的最后一版），V8 更新、兼容警告更少，但仍拿不到现代前端。
- 如果 UA 方案失效，可退而求其次：降低渲染分辨率（`wm size` / `wm density`）、精简 Lovelace 仪表盘卡片、关闭实时图表。
