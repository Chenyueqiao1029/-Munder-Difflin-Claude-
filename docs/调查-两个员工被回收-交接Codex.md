# 调查交接：Codex 与 DeepSeek Harness 被周期回收

> 交接人：DSH（DeepSeek Harness）　时间：2026-10-11 11:40　交办：Codex
> 结论先行：**不是额度、不是网络、不是引擎、不是命令**。两个特定 agent 在 spawn 后
> **1分37秒 ~ 2分56秒** 之间被**外部回收**，app 自己的日志里**没有任何回收记录**。

---

## 一、现象（可复现）

| 时间 | spawn | 死亡 | 存活 |
|---|---|---|---|
| 10:14:5x | 10:13:00-02 | **10:14:59** | ~2m |
| 10:23:2x | 10:21:48-50 | **10:23:29** | ~1m39s |
| 10:32:0x | 10:30:21-23 | **10:32:00** | ~1m37s |
| 10:38:4x | 10:36:53-55 | **10:38:49** | ~1m54s |
| 10:59:1x | 10:56:21-22 | **10:59:14** | ~2m52s |
| 11:07:4x | 11:05:17-19 | **11:07:45** | ~2m26s |
| 11:31:3x | 11:29:40-42 | **11:31:36** | ~1m54s |

- **只有这两个**：`codex-mv2h4arh`（Codex）、`harness-mv3d0001`（DSH）。
- **另外 5 个一直稳定**：`god`、`workbuddy-mv135oq0`、`tianshu-mv3d0002/approve/fix`。
- 两者**同一秒**死亡（说明是同一个外部动作，不是各自崩溃）。
- hive 日志形态（`hive/log.jsonl`）：

```json
{"kind":"agent-exit","agentId":"codex-mv2h4arh","exitCode":-1,"signal":null,"abnormal":true,
 "tailPath":"…\\hive\\crashes\\2026-10-11T02-59-14-814Z-codex-mv2h4arh.log"}
{"kind":"archive","agentId":"codex-mv2h4arh","archived":true}
```

- 崩溃尾巴显示它们**死前一切正常**：
  - Codex 最后一行：`◦ Working (34s • esc to interrupt) · Running hook`（**正在跑 hook**）
  - DSH 最后一行：TUI 停在输入提示符（`❯说点…`），即**空闲待命**
- 收件箱/发件箱**没有**新的 `act:"done"`。

---

## 二、已排除（每条都有实测证据）

| # | 假设 | 排除方式 | 结果 |
|---|---|---|---|
| 1 | ChatGPT 额度用尽 | `codex exec -m gpt-6-astra "只回复OK"` | **31s 正常返回，退出码 0** |
| 2 | 网络不通 | `Test-NetConnection chatgpt.com:443` | True；猎豹加速器 + clash-verge-service 都在跑 |
| 3 | npm 垫片被解码成 node 直启不稳 | 新建**普通 .cmd 包装**（`md-codex.cmd` / `md-dsh-tui.cmd`，强制回退 cmd.exe） | **仍死** |
| 4 | 引擎自身问题 | 把 DSH 换成 `tianshu-agent`（与 god/天枢同引擎，稳定） | **仍死**；Codex 换最朴素 `codex` 也**仍死** |
| 5 | 并发上限 | `maxConcurrentWorkers` 4 → **8** | 仍死 |
| 6 | 电路闸（circuit breaker） | `config.json` 的 `circuitBreaker.enabled = false` | 仍死 |
| 7 | 临时工完工信号 | 查 outbox（含 `.sent`）无新 `act:"done"`；且已加规则禁止写 | 仍死 |
| 8 | 空闲回收 | `workerIdleTimeoutMinutes` 20 → **1440** | 仍死 |
| 9 | 我自己的进程树（作业对象） | 改用 **WMI `Win32_Process.Create`** 脱离式启动 | 仍死 |
| 10 | agent id 被记入回收名单 | 换新 id + 清 roster/registry + 归档旧 hive 目录 | 未测干净：app 又从**自己的持久状态**把旧 id 恢复了（见怀疑 5） |

---

## 三、剩余怀疑（建议按此顺序查）

### S1（最高）app 的 `[resume]` 路径
启动日志里有一条：
```
[resume] codex resume 01a12628-8bbd-7530-ba63-1e60c37b0d3c in C:\…\hive\agents\codex-mv2h4arh\.codex
```
怀疑：**app 用 `codex resume <id>` 恢复会话，一次回合跑完后 CLI 正常退出**，而 app 把这种退出判为
异常（`exitCode: -1, abnormal: true`）→ 归档。
查：主进程 bundle 里搜 `[resume]`，看它怎么处理 resume 结束；对照 `codex` 交互 TUI 与 `codex resume` 的退出行为。
（注意：这条**只能解释 Codex**，解释不了 dsh-tui。）

### S2（次高）hook 注入
启动日志：
```
[hive] hook server listening on \\.\pipe\munder-difflin-<hash>
```
Codex 死前正停在 `Running hook`。怀疑 **hook 脚本在 codex/dsh 上返回非零或超时 → CLI 主动退出**。
查：hook 写进 agent 的 hook 配置（`hive\agents\<id>\.codex\` 下）、hook server 的返回码处理。

### S3 app 的 PTY 健康检查 / keepalive
日志里反复出现 `[worker-wake] holding … (mail pending XXXs, pty quiet Ys, last activity never)`。
怀疑存在一个**PTY 静默/健康判定**在 ~2 分钟量级上触发 `ptyManager.kill()`（而我们没看到对应日志，可能
是 `console.log` 没被重定向到文件）。
查：搜 `ptyManager.kill(`、`teardownPty(` 的所有调用点与 reason；搜 `strongKeepalive`、`heartbeatSeeded`。

### S4 app 的 renderer 持久状态把它们记为 worker/temp
我们已经清过 `roster.json`、`hive/registry.json`、`hive/agents/<id>`，**app 仍能把旧 id 拉回来** →
说明真值在**别处**：怀疑 renderer 的持久化状态（`%APPDATA%\munder-difflin\Local Storage\leveldb` 或
`config.json` 的某段）。查：`restoreTeam()` / `applyRestoreGate()` / `restorableAgents` 的数据来源。

### S5 `signInOffer` → `teardownPty(id, "revive")`
主进程里有：
```js
if (signInOffer) teardownPty(id, "revive"); else teardownPty(id, "exit");
```
若 CLI 弹出登录提示（token 过期），app 会先杀掉再"复活"。查 `loginWatcher` 的判定与 `signInOffer` 的来源。

---

## 四、复现与取证（照这个做）

```powershell
# 1) 带日志启动（app 的 stdout/stderr → custom-cast\app-console.log）
python D:\徐\MunderDifflin\custom-cast\start_office_logged.py     # 内部等 200s 后打印匹配行

# 2) 观察 ~3 分钟，看 app-console.log 在死亡时刻有没有
#    [worker] … / [pty] … / [resume] … / hook … / breaker …
Get-Content D:\徐\MunderDifflin\custom-cast\app-console.log -Tail 40

# 3) 崩溃尾巴（每次 8192 字节 PTY 输出 + 头部元信息）
Get-ChildItem C:\Users\徐\yueqiaochangetheworld\hive\crashes | Sort LastWriteTime -Desc | Select -First 4

# 4) 事件流
python - <<'PY'   # （PowerShell 里用 python -c 或存成 .py）
import json,time
H=r'C:\Users\徐\yueqiaochangetheworld\hive'
for l in open(H+r'\log.jsonl',encoding='utf-8',errors='replace'):
    o=json.loads(l)
    if o.get('kind') in ('spawn','agent-exit','archive'): print(time.strftime('%H:%M:%S',time.localtime(o['ts']/1000)),o['kind'],o.get('agentId'))
PY
```

**稳态启动（临时办法，保证全员在线）**：
`python D:\徐\MunderDifflin\custom-cast\start_office_detached.py`
（先补花名册 → WMI 脱离式启动 → 报告 spawn 名单）

---

## 五、关键代码位置

| 位置 | 说明 |
|---|---|
| `D:\徐\MunderDifflin\Munder-Difflin-0.5.5-fixed\resources\app\out\main\index.js` | **主进程 bundle（官方原版，我没有改过）**；PTY / hook / worker 回收 / restore-gate / circuit-breaker / resume 都在这里 |
| `…\out\renderer\assets\index-*.js` | UI 与恢复流程（`restoreTeam`、`applyRestoreGate`、`restorableAgents`、`splitRestorable`） |
| `…\out\renderer\assets\OfficeFloor-*.js` | 场景：角色取帧 / 座位 / 朝向（**被我的补丁改过**） |
| `…\out\renderer\assets\global-*.js` | `SpritePortrait` 等头像组件（**被我的补丁改过**） |

可在主进程 bundle 里按名字直接搜到：
`ephemeralWorkerTick`、`workerSignaledDone`、`teardownPty`、`RestoreGateStore`、
`captureEndedAtBoot`、`CircuitBreaker`、`breakerToast`、`loginWatcher`、`[resume]`、`[worker-wake]`、
`[migration] archived orphaned agent`、`hook server listening`。

**⚠️ 改 renderer 前先读我的两个补丁脚本，否则会被覆盖：**
- `D:\徐\MunderDifflin\custom-cast\patch_renderer.py`（自定义角色 + 头像 + 气泡高度 + 语法门）
- `D:\徐\MunderDifflin\custom-cast\patch_map.py`（地图/座位/固定分座/月桥朝向 + esbuild 语法门）
流程：`patch_renderer.py` → `patch_map.py` → 覆盖 `resources\app\out\renderer`（每次都会自动备份 `renderer.prev-*`）

---

## 六、判定标准（修好的标志）

1. Codex 与 DSH spawn 后**连续存活 ≥ 15 分钟**（当前是 ~2 分钟）；
2. `hive\log.jsonl` 在 15 分钟内**没有**它们的 `agent-exit`；
3. 两个 agent 的收件箱能被正常处理并回出消息（`kind=message`，`from=codex-mv2h4arh` / `harness-mv3d0001`）；
4. 重启 app 后 7 名员工全部自动上线，无需人工补花名册。

---

## 结论 / 证据 / 范围与影响 / 下一步

- **结论**：本文档所列内容截至 2026-10-12 10:32 已核对；需要执行的事项在上文对应章节中标注了责任方与判据。
- **证据**：文中每条断言均附有可复跑的命令、日志路径或文件路径（见各章节内联引用）。
- **范围与影响**：本文档只描述状态与计划，不改动任何生产代码与用户文件；引用路径均在 `D:\徐\MunderDifflin\custom-cast\` 与 `C:\Users\徐\yueqiaochangetheworld\hive\` 之内。
- **下一步**：按上文优先级推进；执行前先过一遍 `我的工作纪律.md` 的执行清单（现状 → 隔离实验 → 单点改动 → 校验 → 四段汇报）。
