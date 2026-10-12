# 美术需求书 · ART SPEC

> 给"出图的人 / AI"看的一页纸。**照这个做出来的图，可以直接进管线，不用返工。**
> 自检命令：`python art/check_assets.py`（通不过的会被打回）

---

## 0. 一句话需求

**Q 版（chibi）像素风角色 + 一间俯视办公室**，透明背景，风格统一，严格按下面的网格切割。
不需要文字、对话框、名字牌、阴影贴地——那些由引擎自己画。

---

## 1. 总览（硬性规格）

| 素材 | 尺寸 | 网格 | 格式 | 命名 |
|---|---|---|---|---|
| **角色图集** | **504 × 324** | **7 列 × 3 行**，单元格 **72 × 108** | PNG · RGBA（**透明背景**） | `<id>.sheet.png` |
| **角色头像** | **144 × 216** | 单图 | PNG · RGBA（透明背景） | `<id>.portrait.png` |
| **办公室地图**（可选） | **1488 × 1057**（尺寸可不同，我们会适配） | 俯视整图 | PNG（可不透明） | `office-atlas.png` |
| **多角色源表**（可选，最省事） | 1536 × 1024 起，可更高 | 一行一个角色，**左侧留 ≥100px 标签栏**，其余分 15 列 | PNG · RGBA | `cast-sheet.png` |

### 单元格内部构图（关键，别做错）
- 角色**正对镜头略微 3/4 侧**，全身可见（头到脚）。
- **脚底贴单元格下边缘**（留 0~3px）；**头顶留 8~24px 空白**。
- 左右**各留 1~3px**，**不要顶满**——顶满会把隔壁角色的手臂切进来。
- 角色高度约占单元格的 **90%**。

---

## 2. 图集的行列含义（务必按这个顺序画）

| 行 | 内容 | 说明 |
|---|---|---|
| **第 1 行** | **正面** | 7 帧：第 1~4 帧为行走（左腿→中→右腿→中），第 5~7 帧为站立/工作/阅读 |
| **第 2 行** | **背面** | 同样的 7 帧节奏 |
| **第 3 行** | **侧面（朝右）** | 同样的 7 帧节奏；**朝右**画（引擎向左走时自己水平翻转） |

> 帧不需要大幅位移——轻微的重心和腿部位移即可，引擎会做"上下微跳"。

---

## 3. 画风要求（和现有 7 个角色保持一致）

- **风格**：Q 版三头身、柔和的渐变着色（**不是**强限色的 8-bit 像素）、**深色描边**（轮廓清楚）。
- **细节**：头发有高光、眼睛大而清晰、衣服有简单材质分区（领口/袖口/下摆）。
- **配色**：每个角色**主色相明显不同**（发色/服装色即可），但**整体色温统一**（都偏柔和、不要纯荧光色）。
- **禁止**：文字、水印、对话气泡、名字牌、地面阴影、外发光、模糊/抗锯齿噪点、纯白底（必须透明）。
- **一致性**：同一角色的 21 帧必须**完全同一套配色与轮廓**；不同角色之间**身高比例一致**。

---

## 4. 可直接粘给出图 AI 的提示词

**中文版：**
```
请画一张透明背景的 Q 版像素风角色图集，PNG，尺寸正好 504×324 像素，切成 7 列 3 行、
每个单元格 72×108 像素。第 1 行是同一个角色的正面，第 2 行是背面，第 3 行是侧身朝右。
每行 7 帧：前 4 帧是行走（左腿、中间、右腿、中间），后 3 帧是站立、伏案工作、阅读。
角色为三头身 Q 版，深色描边，柔和的渐变着色，头发有高光，眼睛大而清晰。
角色要占满单元格高度的 90%，脚底贴住单元格下边缘，左右各留 2 像素空隙，
不要顶到相邻格子。不要任何文字、水印、名字牌、对话气泡、地面阴影、白色背景。
整张图必须是纯透明背景。角色主色调用 [填写颜色]，服装与发型自定但保持风格统一。
```

**English version:**
```
A chibi pixel-art character sprite sheet, transparent background, PNG, exactly 504x324 px,
cut into 7 columns x 3 rows, each cell 72x108 px. Row 1 = front view, Row 2 = back view,
Row 3 = side view facing RIGHT. 7 frames per row: frames 1-4 walking (left leg, neutral,
right leg, neutral), frames 5-7 standing, working at a desk, reading. Chibi proportions
(3 heads tall), thick dark outlines, soft gradient shading, glossy hair highlights,
large clear eyes. The character fills 90% of the cell height, feet touch the bottom edge,
2 px margin on left and right so nothing bleeds into the neighbour cell. No text, no watermark,
no name plate, no speech bubble, no ground shadow, no white background — fully transparent PNG.
Main colour: [YOUR COLOR]. Keep the same palette across all 21 frames.
```

> 出图 AI 常见问题是"给了 1024×1024"或"每格不齐"——我们的自检工具会按整数倍缩放，但**格线必须对齐**，否则角色会被切掉。

---

## 5. 交付什么、怎么放

```
assets/chars/<id>.sheet.png        ← 每个角色一张（504×324）
assets/chars/<id>.portrait.png     ← 每个角色一张（144×216）
assets/map/office-atlas.png        ← 可选：换整间办公室
```
`<id>` 用清单里的 id（见第 7 节），全小写、用连字符。

**可选但最省事**：只交一张 `cast-sheet.png`（一行一个角色、左侧 100px 标签栏），
然后跑：
```bash
python import_assets.py sheet --image assets/source/cast-sheet.png --map assets/cast-map.example.json
```
它会自动做连通块抠图（防止把邻格"半个人"带进来）、侧面镜像、缩放对齐。

---

## 6. 自检（我会先跑这个，通不过不打回重做、只打回小改）

```bash
python art/check_assets.py                 # 检查 assets/chars/ 全部角色
python art/check_assets.py <某个sheet>     # 只检查一张
python art/recolor_cast.py                 # 需要 31 个角色时，用 7 个基础角色派生配色变体
```
**打回标准（错误）**：尺寸不是 504×324 的整数倍（或宽高倍数不一致）；没有透明背景；某格全空；头像尺寸不对。
**提醒（不阻塞）**：内容贴到单元格左右边；脚底没贴底；头顶留白不在 8~24px；侧面朝向不明显。

---

## 7. 需要 31 个角色时的清单（id → 中文名 / 英文角色）

| # | id | 中文名 | 英文角色 | # | id | 中文名 | 英文角色 |
|---|---|---|---|---|---|---|---|
| 1 | explore | 探索者 | Explore | 17 | refactor | 重构师 | Refactor |
| 2 | analyst | 分析师 | Analyst | 18 | perf | 性能官 | Perf |
| 3 | architect | 架构师 | Architect | 19 | security | 安全官 | Security |
| 4 | executor | 执行者 | Executor | 20 | debug | 排障师 | Debug |
| 5 | verifier | 验证者 | Verifier | 21 | devops | 运维官 | DevOps |
| 6 | reviewer | 代码评审 | Code Reviewer | 22 | data | 数据官 | Data |
| 7 | cleaner | 清理工 | Code Cleaner | 23 | ui | 界面工 | UI |
| 8 | simplifier | 简化师 | Code Simplifier | 24 | i18n | 多语官 | i18n |
| 9 | research | 研究员 | Code Research | 25 | ci | 流水线官 | CI |
| 10 | api | 接口工 | API Agent | 26 | deps | 依赖官 | Deps |
| 11 | auth | 权限官 | Auth Agent | 27 | migration | 迁移官 | Migration |
| 12 | db | 数据库官 | DB Agent | 28 | observability | 观测官 | Observability |
| 13 | frontend | 前端工 | Frontend Agent | 29 | planner | 规划师 | Planner |
| 14 | backend | 后端工 | Backend Agent | 30 | coordinator | 协调员 | Coordinator |
| 15 | tester | 测试工 | Test Agent | 31 | steward | 管家 | Steward |
| 16 | docs | 文档官 | Docs Agent | | | | |

> 这份 id 列表与 `assets/roster.example.json`、`build/roster31.json` 一致。
> **只想画 7 个**也行——现有的 7 个（yueqiao / workbuddy / codex / harness / tianshu-exec / tianshu-approve / tianshu-fix）就是标准样例。
