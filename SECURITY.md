# 安全说明

- 本仓库**不包含任何密钥**（已用严格正则扫描：`sk-*` / `ghp_*` / `github_pat_*` / JWT / `AIza*` 均无命中）。
- 运行需要你自己提供凭据，例如 `DEEPSEEK_API_KEY`（天枢/DSH 引擎）与 ChatGPT 账号（Codex）。
- 不要把 `chat/`、`_source/`、`pack/`、`driver-*.json`、`*.bak*` 提交进来（已在 `.gitignore` 中排除）：
  它们可能包含对话记录、本机路径与个人素材。
- 若你在 fork 里加了密钥，请用环境变量或本地未跟踪文件，**不要**写进代码。

> 本项目是 **Munder Difflin 的二次开发**（仓库名 `munder-difflin-starhive`）：只提供补丁与编排层，不分发上游代码与资源。
