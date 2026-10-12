# 验收清单（交接 Codex）

生成：2026-10-11 21:06　　生成者：DeepSeek Harness　　验收对象：像素办公室（Munder Difflin 0.5.5-fixed）
后续复核：2026-10-11 22:16。下方 A/B 为原始交接快照；此行之后的“22:16 复核”记录当前修复结论。
所有验证均为**命令行/文件**方式，不需要截屏或操作用户桌面（用户硬约束）。

---

## A. 现在可以验的（已完成 · 附验证方法）

### A1. 7 名员工在岗，且终端连接由 app 自己保存
```powershell
Get-Process | ? ProcessName -like '*Munder*'            # 期望：有窗口 1 个
python -c "import json;d=json.load(open(r'C:\Users\徐\yueqiaochangetheworld\roster.json',encoding='utf-8'));print(all(a.get('ptyId') for a in d['agents']), len(d['agents']))"
```
**期望**：`True 7`。`ptyId` 由 app 的 restore 流程自己写入（U2 补丁 `__mdU2Reconcile/__mdU2AlreadyLive/__mdU2AddAgent`，已做**决定性验收**：手动清空 DSH 的 ptyId → 重启 → app 自己补回）。

### A2. 办公室【终端标签】可以像正常 AI 一样对话
- 界面：点员工 → 终端 → 直接打字 → Enter
- 命令行等价验证：
```powershell
"你好，用一句话说你是谁。" | python D:\徐\MunderDifflin\custom-cast\agent_chat_repl.py harness-mv3d0001
```
**期望**：打印头部（姓名/角色/状态）→ 实时输出该员工回答。

### A3. 实时显示"思考 / 工具调用 / 工具输出 / 最终回答"
**期望输出形态**（实测样例）：
```
💭 老板让我用一句话说我是谁，然后列一下工作目录里的文件…
🔧 bash {'command': 'ls -la'}
   ↳ total 1517 drwxr-xr-x 1 徐 197121 0 Oct 11 20:41 . …
💭 前 13 行被省略了。我需要看完整列表…
✅ （最终回答）
```
机制：各引擎开流式事件（`rivet --stream-json` / `dsh headless --json` / `codex exec --json` / `codebuddy -p --output-format stream-json`），由 `agent_chat_repl.py:render()` 渲染并合并同类增量。

### A4. 不再出现黑窗闪烁（用户硬约束）
```powershell
(Get-Process conhost,cmd -ErrorAction SilentlyContinue | ? MainWindowHandle -ne 0).Count
```
**期望**：`0`。全部常驻脚本已加 `CREATE_NO_WINDOW` 守卫（`md-nowindow`）+ 统一 `pythonw.exe` 启动。

### A5. 后台常驻 4 件 + 开机自启
```powershell
# 期望各 1 个，且解释器是 pythonw.exe
Get-CimInstance Win32_Process | ? { $_.CommandLine -like '*custom-cast\supervisor.py*' }
Get-CimInstance Win32_Process | ? { $_.CommandLine -like '*agent_driver2*' }
Get-CimInstance Win32_Process | ? { $_.CommandLine -like '*watchdog.py*' }
Get-CimInstance Win32_Process | ? { $_.CommandLine -like '*md_chat.py*' }
schtasks /Query /TN "MDSupervisor"            # 期望 State=Ready，每 10 分钟
Test-Path "$([Environment]::GetFolderPath('Startup'))\星域蜂巢-常驻.vbs"   # 期望 True
```

### A6. 崩溃已停（除 Codex 额度）
```powershell
python -c "import json,time;H=r'C:\Users\徐\yueqiaochangetheworld\hive';rows=[o for o in (json.loads(l) for l in open(H+r'\log.jsonl',encoding='utf-8',errors='replace')) if o.get('kind')=='agent-exit' and o['ts']/1000>time.time()-3600];print(len(rows), sorted({o['agentId'] for o in rows}))"
```
**原交接期望**：近 1 小时的非 Codex 退出 = 0（工作时段最长记录：**3 小时 14 分钟零死亡**，月桥自查）。22:16 复核发现 watchdog 误判旧进程名曾造成整个办公室反复重启，不能把原期望当成当前通过值；修复见文末。

### A7. 投递通道（原生无头，替代 app 的盲打）
```powershell
# 各员工收件箱：待处理应为 0（Codex 例外，额度锁）
python -c "import os;H=r'C:\Users\徐\yueqiaochangetheworld\hive\agents';[print(a, len([f for f in os.listdir(os.path.join(H,a,'inbox')) if f.endswith('.json')])) for a in os.listdir(H) if os.path.isdir(os.path.join(H,a,'inbox'))]"
Get-Content D:\徐\MunderDifflin\custom-cast\driver-status.json
```
**期望**：待处理≈0；`driver-status.json` 里 `state=idle/ran`、`lastOk=true`（Codex 为 false，额度）。

### A8. 看板（统筹视图）
打开 `D:\徐\MunderDifflin\custom-cast\进度看板.html`（20 秒自动刷新）
**内容**：月桥→人类的最近 5 封汇报（置顶）· 全员在线/待办 · 投递与运行状态 · 每人产出清单与思考日志尾部 · 消息时间线。

### A9. 备份完整
`D:\徐\MunderDifflin\custom-cast\backup-20261011-182135\`（主进程 bundle + 整个 renderer + roster + registry，41.4 MB）；各处还有 `.bak-*` 时间戳备份。

---

## B. 未完成 / 未完美（逐条：现象 → 已确认 → 卡点 → 下一步）

| 编号 | 现象 | 已确认到哪 | 卡点 | 下一步 |
|---|---|---|---|---|
| **B1** | app **原生**界面里看不到这些引擎的实时思考/遥测 | app 靠 Claude 式 hook + 向 PTY 盲打；rivet/dsh 不发 hook → `last activity never`、`tokens=0`；盲打实测损耗 ~75%（`pty-submit 457 → delivered 113`） | 需要写 hook/stdin 桥（1~2 天） | 我目前用「终端 REPL + 流式渲染」绕过（A2/A3 已通），但那是替代路径；原生方案仍未做 |
| **B2** | Codex 每 ~20 秒被 archive→spawn 循环 | 22:01 后仍重启；22:15 已定位为 `md-chat` 包装器被误加原生 Codex `resume` 参数，加上批处理路径变成 `??` | 启动路径与主进程 provider 已修；额度仍是外部限制 | 观察稳定性和账号额度，见文末 22:16 复核 |
| **B3** | 派发链路多一跳 | 月桥写收件箱 → **我的外部驱动**（45 秒轮询）→ 引擎。不是月桥直连 | 依赖 B1 | B1 修好后可撤掉这一跳 |
| **B4** | 月桥的汇报不会主动出现在眼前 | 它发了 **6+ 封** `to: human`（16:02…19:10），写在 `hive\agents\god\outbox\.sent\*-human-*.json`；app 的「问我」板只收 `act=ask` | 与"禁止弹窗"冲突 | 已置顶到看板；如需进 app，可改月桥规则用 `act=ask`+`needs_human` |
| **B5** | 监督器曾出现多实例 | `children()` 曾按错误进程名过滤（已修）；启动项 + 计划任务可能双启 | 单实例守卫靠 `supervisor.pid` + 存活检测，**竞态未彻底排除** | 建议改成文件锁或命名互斥体 |
| **B6** | 星域终端**标题**由引擎自己渲染 | 我只能分开会话/人设/工作目录 | 引擎横幅不可控 | 若必须，需改引擎或包一层 |
| **B7** | WorkBuddy 不可用 | `codebuddy -p` 返回 `429 额度已用尽` | 外部额度 | 充值/等待 |
| **B8** | F12：headless 员工"能读不能写" | DSH 现场复现：`sandbox-local windows-acl temp grant materialization failed and its cleanup also failed`；读文件正常，跑命令即死 | rivet 引擎沙箱 ACL | 我手上有 `diagnose-windows-sandbox-acl` 技能，可一次性检查并修复该路径及其父目录 ACL |
| **B9** | 我无法验证 app 界面 | 用户禁止截屏/动桌面 | 约束 | 界面类验收必须由你或用户点击确认 |

---

## C. 给验收方的硬约束（违反会毁掉已完成的工作）

1. **改 renderer 前必须先跑**：`patch_renderer.py` → `patch_map.py`（否则自定义角色/地图/座位/气泡/月桥朝向会被覆盖）。
2. **不要重建 renderer 覆盖已装内容**：U2 补丁与对话终端注入是**就地改**的（`index.html` + `index-*.js`/`global-*.js` + `md-chat-overlay.js`），重建会丢；要重建就先跑 `patch_u2_terminal_restore.py` 等补丁脚本。
3. **主进程补丁**（`resources\app\out\main\index.js`）：`__mdPtyBind`、`__mdAutoRevive`、`__mdWakeForce`；`__mdWakeRestart` 已移除。备份在 `index.js.bak-*`。
4. **不要动** `E:\Downloads\lingshu-server`（比赛仓库）。
5. **禁止弹窗/抢焦点**（用户硬约束）：启动 Electron 前 `Remove-Item Env:\ELECTRON_RUN_AS_NODE`；后台一律隐藏窗口。
6. **禁止在 outbox 写 `act:"done"`**（会被 app 当临时工完工信号回收）；完工用 `act:"inform"`。

---

## D. 关键路径速查

| 用途 | 路径 |
|---|---|
| 自定义脚本总目录 | `D:\徐\MunderDifflin\custom-cast\` |
| 对话终端本体 | `custom-cast\agent_chat_repl.py` + `%APPDATA%\npm\md-chat.cmd` |
| 投递驱动 / 守卫 / 监督器 | `agent_driver2.py` / `watchdog.py` / `supervisor.py` |
| 备用网页对话台 | `md_chat.py`（127.0.0.1:8787，已从 app 界面移除，仍可独立使用） |
| 看板生成 | `progress_board.py` + `board_add_work.py` + `board_add_driver.py` + `board_add_god_brief.py` |
| 花名册 / 注册表 / 恢复门 | `hive\roster.json`（在 `C:\Users\徐\yueqiaochangetheworld\`）/ `hive\registry.json` / `restore-gate.json` |
| app 配置（含 godCommand） | `%APPDATA%\munder-difflin\config.json` |
| 事件流 / 崩溃日志 | `hive\log.jsonl` / `hive\crashes\*` |

---

## 22:16 复核（Codex 接手后的实测）

- **U2 持续有效**：当前安装版有 `__mdU2Reconcile/__mdU2AddAgent/__mdU2AlreadyLive`；主进程列出 7 个真实 PTY，7 名员工的 `ptyId` 均在花名册保存，重载后保持。7 项恢复链路回归检查通过。
- **U3 循环根因已找到**：22:01 后 Codex 仍每约 21 秒 `archive → spawn`。所有席位已改由 `md-chat.cmd` 启动，但主进程仍以 Codex provider 给包装器加 `resume <session id>`，导致包装器立即退出；批处理路径中的中文也已变成字面 `??`。已用 ASCII 启动器修复路径，并在 `patch_main_md_chat.py` 让主进程仅对 `md-chat` 使用 custom 启动逻辑；实际回答仍由包装器调用 headless Codex。
- **守卫误判已修**：watchdog 原来扫描 `node.exe` 的旧引擎名，实际终端为 `cmd.exe` 下的 `md-chat.cmd`，从而每几分钟重启整个办公室。现按当前 app 的子进程检查包装器；Codex 单独不可用时不重启全部席位。
- **重启后观察**：22:15:29 Codex 新终端启动，到 22:18:00 已连续约 2 分 31 秒，未再 archive；7 个包装器进程、7 个 PTY、4 个后台常驻进程均在。账号额度须单独确认。没有截屏或操作用户桌面。
- **注意 A7**：22:10 读取 `driver-status.json` 时天枢执行、天枢审批、Codex 的历史 `lastOk` 为 `false`，且各有待办；A7 的“全部 lastOk=true、待办≈0”属于原交接期望，不能据此判为当前全绿。

---

## 结论 / 证据 / 范围与影响 / 下一步

- **结论**：本文档所列内容截至 2026-10-12 10:32 已核对；需要执行的事项在上文对应章节中标注了责任方与判据。
- **证据**：文中每条断言均附有可复跑的命令、日志路径或文件路径（见各章节内联引用）。
- **范围与影响**：本文档只描述状态与计划，不改动任何生产代码与用户文件；引用路径均在 `D:\徐\MunderDifflin\custom-cast\` 与 `C:\Users\徐\yueqiaochangetheworld\hive\` 之内。
- **下一步**：按上文优先级推进；执行前先过一遍 `我的工作纪律.md` 的执行清单（现状 → 隔离实验 → 单点改动 → 校验 → 四段汇报）。
