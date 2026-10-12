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
