# 星域办公室 · Star-Domain Office

把一堆**互相协作的 AI agent** 放进一间**像素风办公室**里跑，并且——这是重点——**让它省钱、可观测、可验收**。

> 上游渲染与调度来自开源项目 **Munder Difflin**（Electron + Pixi.js 像素办公室，基于 Claude-Code 式 hook 协议）。
> 本仓库是围绕它做的**编排层 + 补丁集 + 工程纪律**：补齐它对「非 Claude 系引擎」的盲区。

## 它解决什么问题

上游 app 只认 Claude 式 hook 的 CLI；换成 `rivet(天枢)` / `dsh` / `codex` / `codebuddy` 之后会出现四个真实故障：

| 故障 | 现象 | 本仓库的解法 | 对应文件 |
|---|---|---|---|
| 终端拿不到 PTY | 界面显示「该智能体没有实时终端」 | 在 `pty:spawn` 入口补回 hive 记录并无条件登记 PTY↔agent | `patches/patch_main_ptybind.py` |
| 恢复流程不写 ptyId | 重启后员工没有终端 | 修 restore 的 ptyId 回写 | `patches/patch_u2_terminal_restore.py` |
| 异常退出即永久掉线 | 员工被反复归档 | 异常退出自动复活（带每小时上限） | `patches/patch_main_revive.py`、`patch_revive_cap.py` |
| 投递损耗 ~75% | 派活没人理 | 改用各引擎**原生无头通道**投递 + 去重账本 | `core/agent_driver2.py`、`task_ledger.py` |

## 核心设计（省钱的三件事）

1. **投递不走"往 TUI 盲打"**，改走各引擎原生通道：`rivet --goal` / `dsh headless` / `codex exec` / `codebuddy -p`。
2. **去重账本**（`task_ledger.py`）：同一 `dedupe_key` 只认领一次，掐掉"同一件事反复做"。
3. **限流 + 停止条件**：每次预算 4 轮、超时 600s、同一员工每小时最多投 3 次。

## 快速开始

```bash
# 0) 先看环境（Windows / PowerShell 5.1 为本仓库实测环境）
python core/who_works.py            # 一眼看有没有人在干活（退出码 0/1）

# 1) 把脚本里的作者本机路径换成你自己的
python setup_paths.py --apply

# 2) 修改 core/*.py 顶部的路径常量（应用目录、hive 目录、员工 roster 路径）
#    然后：启动
启动办公室.cmd
#    或
停止办公室.cmd
```

## 目录

```
core/      编排核心：投递驱动、去重账本、常驻守卫、监督器、状态/看板/对话台
patches/   对上游 app 的补丁（每个都带备份 + esbuild 语法门 + 回滚）
art/       像素人物/地图资产流水线（从角色表切图 → 连通块抠图 → 生成图集）
tests/     驱动安全与终端恢复的单测
docs/      工程纪律、故障复盘、验收清单、学习笔记
```

## 工程纪律（本仓库最值钱的部分）

`docs/我的工作纪律.md` 是从**实测**里提炼的硬规则：动手前先隔离实验拿 `exit 0` 实证 → 一次只改一处 → 改完立刻校验 → 给改动配测试 → 汇报固定四段「结论 / 证据 / 范围与影响 / 下一步」。
附**作者本人踩过的 7 个坑**（含"害用户窗口闪黑窗""按命令行过滤进程把自己杀掉"），开放出来给后来者省时间。

## 已知限制（不粉饰）

- **仅 Windows 实测**（PowerShell 5.1；脚本大量使用 `%APPDATA%`、`CreateProcess` 与 node-pty 行为）。
- 上游 app 的界面里**看不到非 Claude 系引擎的遥测**（它们不发 hook）；本仓库用「终端 REPL + 流式渲染」替代。
- 外部额度（ChatGPT / CodeBuddy）会直接决定某些员工能不能干活。
- 部分脚本需要在目标机上按其目录结构改路径常量。

## 许可

- 本仓库原创部分：**MIT**（见 `LICENSE`）。
- 上游 **Munder Difflin** 的代码与美术资源版权归其作者，本仓库**不分发**其二进制或资源，只提供**补丁脚本**，请自行获取上游。
- 本仓库**不含任何密钥**；请自备 `DEEPSEEK_API_KEY` 等凭据（见 `SECURITY.md`）。
