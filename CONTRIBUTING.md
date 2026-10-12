# 协作与评审

## 怎么让别人帮你看一眼（推荐用 PR，不直接推 main）

1. 仓库 Settings → Collaborators → Add people，填入对方的 GitHub 用户名并发送邀请。
2. 对方接受后 `git clone` 本仓库，开一个分支：
   ```bash
   git checkout -b review/你的名字
   git push -u origin review/你的名字
   ```
3. 在 GitHub 上对该分支发起 **Pull Request**，把要评审的点写进描述（例如"驱动限流逻辑是否有竞态"）。
4. 评审意见留在 PR 评论里，改动继续 push 到同一分支；通过后再合并。

## 评审重点（作者希望被挑刺的地方）

- `core/task_ledger.py` 的认领/释放是否可能死锁或重复认领。
- `core/agent_driver2.py` 的每小时投递上限在并发下是否守得住。
- `patches/patch_main_revive.py` + `patch_revive_cap.py` 的限流是否会被重启绕过。
- `core/supervisor.py` 的单实例守卫（靠 pid 文件）在竞态下是否需要换成文件锁/命名互斥体。

> 本项目是 **Munder Difflin 的二次开发**：只提供补丁与编排层，不分发上游代码与资源。

## 两人（或多人）联合开发：推荐配置

### 1. 把人加进来（Owner 操作，30 秒）
1. 仓库页 → **Settings** → 左侧 **Collaborators**（新版叫 *Collaborators and teams*）
2. **Add people** → 填对方的 **GitHub 用户名或注册邮箱** → 权限选 **Write** → **Add**
3. 对方在邮件/通知里点 **Accept invitation**（也可直接打开
   `https://github.com/Chenyueqiao1029/-Munder-Difflin-Claude-/invitations`）

> 三种方式的区别：
> - **Collaborator + Write**（推荐）：对方能直接建分支、push、开 PR、管 Issue —— 适合**联合开发**。
> - **只把仓库地址发给他**：公开仓库人人可 clone；他不持有写权限，想改只能 **Fork** 后给你发 PR —— 适合「只看一眼/评审」。
> - **建 Organization**：人多（≥3）或要长期做、要分团队权限时再上，可把仓库转移过去。

### 2. 保护 main（强烈建议，防止互相覆盖）
**Settings → Branches → Add branch protection rule** → 分支填 `main` → 勾选：
- Require a pull request before merging（至少 1 个 approving review）
- Do not allow bypassing the above settings

之后**谁都不能直接推 main**，改动一律走 PR。

### 3. 日常流程（双方都照这个走）
```bash
git clone git@github.com:Chenyueqiao1029/-Munder-Difflin-Claude-.git
cd --Munder-Difflin-Claude-
git checkout -b feat/简短描述          # 每件事一个分支
# …改代码…
git add -A && git commit -m "feat: 做了什么"
git push -u origin feat/简短描述
# 然后在 GitHub 上点 "Compare & pull request" 开 PR，等对方 review
```
- 合并前先同步主线，**不要 force push**：
  ```bash
  git fetch origin && git rebase origin/main
  git push --force-with-lease    # 仅在自己的功能分支上，且必须用 --force-with-lease
  ```
- 冲突在本地解决后再推；PR 里写清楚「改了什么 / 为什么 / 怎么验证」。

### 4. 对方第一次推送前
在 GitHub 加一把**自己的** SSH 公钥（`Settings → SSH and GPG keys → New SSH key`，公钥用 `ssh-keygen -t ed25519` 生成），
否则每次推送都要输账号密码（HTTPS 还要用 PAT）。
