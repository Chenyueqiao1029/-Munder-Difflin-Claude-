# 逐模型美术提示词包（图由人来出）

> 用法：找到模型 → 复制"中文提示词"整段 → 粘给出图 AI → 出图另存为 **`<id>.sheet.png`**（504×324）
> 再出一张头像另存为 **`<id>.portrait.png`**（144×216）→ 丢进 `assets/chars/` → 跑 `python art/check_assets.py` 自检。

> 想省事：只画一张大图（一行一个角色、左侧留 100px 标签栏，1536×1024 起），然后 `python import_assets.py sheet --image assets/source/cast-sheet.png --map assets/cast-map.example.json`。

> 硬性规格与禁止项见 `assets/ART-SPEC.md`。

---

## 通用风格块（每段提示词都已包含，不用手动拼）

```
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

## DeepSeek（`deepseek`）　深度求索 · 国产 · ✅ 已接入

| 项 | 值 |
|---|---|
| 配色 | 深海蓝 #1B4B8F + 电光青 #38E1C6 |
| 发型 | 深蓝短发带一缕青光 |
| 服装 | 深蓝工装夹克 + 耳机 |
| 道具 | 手提发光终端板 |
| 气质 | 冷静、算得快、主力干将 |
| 特色 | 性价比之王：中文强、代码强、我们全办公室的主力 |
| 综合评分 | **4.33** / 5 ｜ 中文 5 · 代码 5 · 接入难度 1 · 免费额度：注册送额度，日常便宜 |
| 文件名 | `deepseek.sheet.png` + `deepseek.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「DeepSeek」，深蓝短发带一缕青光，穿深蓝工装夹克 + 耳机，手提发光终端板，气质冷静、算得快、主力干将。
主色调：深海蓝 #1B4B8F + 电光青 #38E1C6。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "DeepSeek" by 深度求索. Give it a distinctive signature prop that hints at its strength (性价比之王), and a confident personality. Palette: 深海蓝 #1B4B8F + 电光青 #38E1C6. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## GLM（智谱）（`glm`）　智谱 AI · 国产 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 纯白 #FFFFFF + 青绿 #2ED3A8 |
| 发型 | 银白发扎小马尾 |
| 服装 | 白衬衫 + 青绿围裙 |
| 道具 | 抱着一个写着"免费"的小木箱 |
| 气质 | 热心、爱帮忙、白干活也不抱怨 |
| 特色 | 免费额度最狠、中文最好，最适合当"白干活的杂务" |
| 综合评分 | **4.05** / 5 ｜ 中文 5 · 代码 4 · 接入难度 1 · 免费额度：GLM-4.7-Flash 完全免费 |
| 文件名 | `glm.sheet.png` + `glm.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「GLM（智谱）」，银白发扎小马尾，穿白衬衫 + 青绿围裙，抱着一个写着"免费"的小木箱，气质热心、爱帮忙、白干活也不抱怨。
主色调：纯白 #FFFFFF + 青绿 #2ED3A8。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "GLM（智谱）" by 智谱 AI. Give it a distinctive signature prop that hints at its strength (免费额度最狠、中文最好), and a confident personality. Palette: 纯白 #FFFFFF + 青绿 #2ED3A8. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## Kimi（`kimi`）　月之暗面 · 国产 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 夜空紫 #4B3A8F + 淡金 #E8D6A0 |
| 发型 | 紫色长发戴圆眼镜 |
| 服装 | 深紫毛衣 + 书袋 |
| 道具 | 抱一摞几乎举不动的厚书 |
| 气质 | 安静、博闻、抱着整本书也能记住 |
| 特色 | 超长上下文，适合吞整本代码/长文档 |
| 综合评分 | **3.85** / 5 ｜ 中文 5 · 代码 4 · 接入难度 2 · 免费额度：部分免费额度 |
| 文件名 | `kimi.sheet.png` + `kimi.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「Kimi」，紫色长发戴圆眼镜，穿深紫毛衣 + 书袋，抱一摞几乎举不动的厚书，气质安静、博闻、抱着整本书也能记住。
主色调：夜空紫 #4B3A8F + 淡金 #E8D6A0。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "Kimi" by 月之暗面. Give it a distinctive signature prop that hints at its strength (超长上下文), and a confident personality. Palette: 夜空紫 #4B3A8F + 淡金 #E8D6A0. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## 通义千问 Qwen（`qwen`）　阿里 · 国产 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 藏青 #1F3A5F + 橙 #F0803C |
| 发型 | 短黑发束发带 |
| 服装 | 藏青工程师马甲 + 卷起袖子 |
| 道具 | 扳手 + 卷起的图纸 |
| 气质 | 踏实、标准件、最可靠的工程派 |
| 特色 | 开源生态最全（本地也能跑），工程化最稳 |
| 综合评分 | **3.85** / 5 ｜ 中文 5 · 代码 4 · 接入难度 2 · 免费额度：有免费额度 |
| 文件名 | `qwen.sheet.png` + `qwen.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「通义千问 Qwen」，短黑发束发带，穿藏青工程师马甲 + 卷起袖子，扳手 + 卷起的图纸，气质踏实、标准件、最可靠的工程派。
主色调：藏青 #1F3A5F + 橙 #F0803C。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "通义千问 Qwen" by 阿里. Give it a distinctive signature prop that hints at its strength (开源生态最全（本地也能跑）), and a confident personality. Palette: 藏青 #1F3A5F + 橙 #F0803C. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## 豆包 Doubao（`doubao`）　字节 · 国产 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 暖黄 #F5C542 + 奶白 #FFF3D6 |
| 发型 | 蓬松黄短发 |
| 服装 | 明黄卫衣 + 斜挎小包 |
| 道具 | 抱一堆待办小纸条 |
| 气质 | 活泼、手脚快、专干批量杂活 |
| 特色 | 便宜量大，适合当"批量杂活" |
| 综合评分 | **3.55** / 5 ｜ 中文 4 · 代码 4 · 接入难度 2 · 免费额度：有免费额度 |
| 文件名 | `doubao.sheet.png` + `doubao.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「豆包 Doubao」，蓬松黄短发，穿明黄卫衣 + 斜挎小包，抱一堆待办小纸条，气质活泼、手脚快、专干批量杂活。
主色调：暖黄 #F5C542 + 奶白 #FFF3D6。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "豆包 Doubao" by 字节. Give it a distinctive signature prop that hints at its strength (便宜量大), and a confident personality. Palette: 暖黄 #F5C542 + 奶白 #FFF3D6. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## 文心一言 ERNIE（`ernie`）　百度 · 国产 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 墨绿 #1F5C4A + 青花白 #EDF6F2 |
| 发型 | 黑发束冠 |
| 服装 | 中式立领长衫 + 卷轴袋 |
| 道具 | 手持毛笔与展开的卷轴 |
| 气质 | 斯文、中文语感极好 |
| 特色 | 中文语感好，代码中等 |
| 综合评分 | **3.30** / 5 ｜ 中文 5 · 代码 3 · 接入难度 3 · 免费额度：有免费额度 |
| 文件名 | `ernie.sheet.png` + `ernie.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「文心一言 ERNIE」，黑发束冠，穿中式立领长衫 + 卷轴袋，手持毛笔与展开的卷轴，气质斯文、中文语感极好。
主色调：墨绿 #1F5C4A + 青花白 #EDF6F2。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "文心一言 ERNIE" by 百度. Give it a distinctive signature prop that hints at its strength (中文语感好), and a confident personality. Palette: 墨绿 #1F5C4A + 青花白 #EDF6F2. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## 混元 Hunyuan（`hunyuan`）　腾讯 · 国产 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 深蓝 #12294A + 金 #D8B24C |
| 发型 | 黑发整齐背头 |
| 服装 | 深蓝制服 + 金边肩章 |
| 道具 | 齿轮徽章 + 太极纹样腰带 |
| 气质 | 稳重、体系内、讲流程 |
| 特色 | 与腾讯生态贴，CodeBuddy 同源 |
| 综合评分 | **3.65** / 5 ｜ 中文 5 · 代码 4 · 接入难度 3 · 免费额度：有免费额度 |
| 文件名 | `hunyuan.sheet.png` + `hunyuan.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「混元 Hunyuan」，黑发整齐背头，穿深蓝制服 + 金边肩章，齿轮徽章 + 太极纹样腰带，气质稳重、体系内、讲流程。
主色调：深蓝 #12294A + 金 #D8B24C。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "混元 Hunyuan" by 腾讯. Give it a distinctive signature prop that hints at its strength (与腾讯生态贴), and a confident personality. Palette: 深蓝 #12294A + 金 #D8B24C. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## MiMo（`mimo`）　小米 · 国产 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 橙红 #E8552F + 灰白 #E9E4DC |
| 发型 | 栗色短发戴运动帽 |
| 服装 | 橙红冲锋衣 + 大背包 |
| 道具 | 背上一个超大的文件背包 |
| 气质 | 耐力强、能扛超大文件 |
| 特色 | 长上下文+大文件处理，活动期可白嫖 |
| 综合评分 | **3.35** / 5 ｜ 中文 4 · 代码 4 · 接入难度 3 · 免费额度：活动期免费 |
| 文件名 | `mimo.sheet.png` + `mimo.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「MiMo」，栗色短发戴运动帽，穿橙红冲锋衣 + 大背包，背上一个超大的文件背包，气质耐力强、能扛超大文件。
主色调：橙红 #E8552F + 灰白 #E9E4DC。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "MiMo" by 小米. Give it a distinctive signature prop that hints at its strength (长上下文+大文件处理), and a confident personality. Palette: 橙红 #E8552F + 灰白 #E9E4DC. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## MiniMax（`minimax`）　MiniMax · 国产 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 粉紫 #C46BD8 + 深紫 #3A1E4F |
| 发型 | 粉紫长卷发 |
| 服装 | 紫色长裙 + 披肩 |
| 道具 | 抽出极长的纸条卷轴 |
| 气质 | 温柔、话多、擅长长文本 |
| 特色 | 长文本与角色扮演见长 |
| 综合评分 | **3.35** / 5 ｜ 中文 4 · 代码 4 · 接入难度 3 · 免费额度：有免费额度 |
| 文件名 | `minimax.sheet.png` + `minimax.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「MiniMax」，粉紫长卷发，穿紫色长裙 + 披肩，抽出极长的纸条卷轴，气质温柔、话多、擅长长文本。
主色调：粉紫 #C46BD8 + 深紫 #3A1E4F。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "MiniMax" by MiniMax. Give it a distinctive signature prop that hints at its strength (长文本与角色扮演见长), and a confident personality. Palette: 粉紫 #C46BD8 + 深紫 #3A1E4F. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## 百川 Baichuan（`baichuan`）　百川智能 · 国产 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 湖蓝 #2C7A9E + 米白 #F2EAD8 |
| 发型 | 黑发束巾 |
| 服装 | 湖蓝学者袍 + 书箱 |
| 道具 | 抱一摞古籍 |
| 气质 | 博学、讲究出处 |
| 特色 | 中文医疗/法律域有优势 |
| 综合评分 | **3.30** / 5 ｜ 中文 5 · 代码 3 · 接入难度 3 · 免费额度：有免费额度 |
| 文件名 | `baichuan.sheet.png` + `baichuan.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「百川 Baichuan」，黑发束巾，穿湖蓝学者袍 + 书箱，抱一摞古籍，气质博学、讲究出处。
主色调：湖蓝 #2C7A9E + 米白 #F2EAD8。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "百川 Baichuan" by 百川智能. Give it a distinctive signature prop that hints at its strength (中文医疗/法律域有优势), and a confident personality. Palette: 湖蓝 #2C7A9E + 米白 #F2EAD8. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## 讯飞星火（`spark`）　科大讯飞 · 国产 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 科技蓝 #1560BD + 白 #F5F9FF |
| 发型 | 黑发戴头戴耳机 |
| 服装 | 蓝白运动服 + 麦克风胸针 |
| 道具 | 头戴耳机 + 录音笔 |
| 气质 | 耳朵灵、听说都强 |
| 特色 | 语音+中文强 |
| 综合评分 | **3.30** / 5 ｜ 中文 5 · 代码 3 · 接入难度 3 · 免费额度：有免费额度 |
| 文件名 | `spark.sheet.png` + `spark.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「讯飞星火」，黑发戴头戴耳机，穿蓝白运动服 + 麦克风胸针，头戴耳机 + 录音笔，气质耳朵灵、听说都强。
主色调：科技蓝 #1560BD + 白 #F5F9FF。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "讯飞星火" by 科大讯飞. Give it a distinctive signature prop that hints at its strength (语音+中文强), and a confident personality. Palette: 科技蓝 #1560BD + 白 #F5F9FF. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## 零一万物 Yi（`yi`）　零一万物 · 国产 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 石板灰 #5A6B7C + 天青 #7FC8E8 |
| 发型 | 灰色短发 |
| 服装 | 灰蓝工装 + 工具腰带 |
| 道具 | 抱着一个贴着开源标签的木箱 |
| 气质 | 务实、愿意共享、可私有部署 |
| 特色 | 开源权重，可本地私有化 |
| 综合评分 | **3.47** / 5 ｜ 中文 4 · 代码 4 · 接入难度 2 · 免费额度：开源可本地 |
| 文件名 | `yi.sheet.png` + `yi.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「零一万物 Yi」，灰色短发，穿灰蓝工装 + 工具腰带，抱着一个贴着开源标签的木箱，气质务实、愿意共享、可私有部署。
主色调：石板灰 #5A6B7C + 天青 #7FC8E8。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "零一万物 Yi" by 零一万物. Give it a distinctive signature prop that hints at its strength (开源权重), and a confident personality. Palette: 石板灰 #5A6B7C + 天青 #7FC8E8. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## OpenAI GPT（`openai`）　OpenAI · 国外 · ✅ 已接入

| 项 | 值 |
|---|---|
| 配色 | 墨绿 #0F3D33 + 亮金 #C8A94A |
| 发型 | 深色卷发 |
| 服装 | 墨绿长外套 + 白衬衫 |
| 道具 | 手持一支发光钢笔 |
| 气质 | 职业、稳、代码功底扎实 |
| 特色 | 代码最稳之一，但额度锁会卡人（我们踩过） |
| 综合评分 | **3.83** / 5 ｜ 中文 4 · 代码 5 · 接入难度 2 · 免费额度：按订阅，额度有硬锁 |
| 文件名 | `openai.sheet.png` + `openai.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「OpenAI GPT」，深色卷发，穿墨绿长外套 + 白衬衫，手持一支发光钢笔，气质职业、稳、代码功底扎实。
主色调：墨绿 #0F3D33 + 亮金 #C8A94A。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "OpenAI GPT" by OpenAI. Give it a distinctive signature prop that hints at its strength (代码最稳之一), and a confident personality. Palette: 墨绿 #0F3D33 + 亮金 #C8A94A. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## Anthropic Claude（`claude`）　Anthropic · 国外 · ✅ 已接入

| 项 | 值 |
|---|---|
| 配色 | 陶土橙 #D97757 + 深灰 #2B2B2B |
| 发型 | 亚麻色短发 |
| 服装 | 橙棕长开衫 + 衬衫 |
| 道具 | 拿着红笔批注的稿纸 |
| 气质 | 审慎、爱挑错、长篇任务之王 |
| 特色 | 长任务与代码审查的标杆；国内可用性不稳 |
| 综合评分 | **4.12** / 5 ｜ 中文 5 · 代码 5 · 接入难度 2 · 免费额度：按订阅/API |
| 文件名 | `claude.sheet.png` + `claude.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「Anthropic Claude」，亚麻色短发，穿橙棕长开衫 + 衬衫，拿着红笔批注的稿纸，气质审慎、爱挑错、长篇任务之王。
主色调：陶土橙 #D97757 + 深灰 #2B2B2B。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "Anthropic Claude" by Anthropic. Give it a distinctive signature prop that hints at its strength (长任务与代码审查的标杆；国内可用性不稳), and a confident personality. Palette: 陶土橙 #D97757 + 深灰 #2B2B2B. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## Google Gemini（`gemini`）　Google · 国外 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 蓝紫渐变 #4285F4→#9B72CB |
| 发型 | 银蓝短发 |
| 服装 | 渐变蓝紫风衣 |
| 道具 | 手持望远镜 + 星图 |
| 气质 | 看得最远、上下文最长 |
| 特色 | 上下文最长，适合"整仓库喂进去" |
| 综合评分 | **3.35** / 5 ｜ 中文 4 · 代码 4 · 接入难度 3 · 免费额度：有免费额度 |
| 文件名 | `gemini.sheet.png` + `gemini.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「Google Gemini」，银蓝短发，穿渐变蓝紫风衣，手持望远镜 + 星图，气质看得最远、上下文最长。
主色调：蓝紫渐变 #4285F4→#9B72CB。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "Google Gemini" by Google. Give it a distinctive signature prop that hints at its strength (上下文最长), and a confident personality. Palette: 蓝紫渐变 #4285F4→#9B72CB. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## xAI Grok（`grok`）　xAI · 国外 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 哑黑 #1A1A1A + 金 #E0B84C |
| 发型 | 黑发挑染金 |
| 服装 | 黑色皮夹克 + 铆钉 |
| 道具 | 手指顶着一个小火箭模型 |
| 气质 | 叛逆、直率、消息灵通 |
| 特色 | 实时信息强，国内不可达（需代理） |
| 综合评分 | **2.77** / 5 ｜ 中文 3 · 代码 4 · 接入难度 4 · 免费额度：按量 |
| 文件名 | `grok.sheet.png` + `grok.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「xAI Grok」，黑发挑染金，穿黑色皮夹克 + 铆钉，手指顶着一个小火箭模型，气质叛逆、直率、消息灵通。
主色调：哑黑 #1A1A1A + 金 #E0B84C。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "xAI Grok" by xAI. Give it a distinctive signature prop that hints at its strength (实时信息强), and a confident personality. Palette: 哑黑 #1A1A1A + 金 #E0B84C. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## Mistral（`mistral`）　Mistral AI · 国外 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 蓝白红三色 #2B4C8C / #FFFFFF / #C8102E |
| 发型 | 亚麻色中长发 |
| 服装 | 蓝白红配色风衣 + 贝雷帽 |
| 道具 | 身边绕着一阵风 |
| 气质 | 轻盈、快、欧洲开源派 |
| 特色 | 欧洲开源派，轻量高效 |
| 综合评分 | **2.88** / 5 ｜ 中文 2 · 代码 4 · 接入难度 2 · 免费额度：开源可本地 |
| 文件名 | `mistral.sheet.png` + `mistral.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「Mistral」，亚麻色中长发，穿蓝白红配色风衣 + 贝雷帽，身边绕着一阵风，气质轻盈、快、欧洲开源派。
主色调：蓝白红三色 #2B4C8C / #FFFFFF / #C8102E。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "Mistral" by Mistral AI. Give it a distinctive signature prop that hints at its strength (欧洲开源派), and a confident personality. Palette: 蓝白红三色 #2B4C8C / #FFFFFF / #C8102E. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## Meta Llama（`llama`）　Meta · 国外 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 棕金 #8A5A2B + 米 #EFE3CE |
| 发型 | 栗色卷发 |
| 服装 | 棕金厚毛衣 + 背带裤 |
| 道具 | 脚边一台小机柜（本地机房） |
| 气质 | 憨厚、力气大、能本地扛 |
| 特色 | 完全本地零 API 费，但吃硬件 |
| 综合评分 | **2.70** / 5 ｜ 中文 3 · 代码 3 · 接入难度 3 · 免费额度：开源免费（吃显卡） |
| 文件名 | `llama.sheet.png` + `llama.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「Meta Llama」，栗色卷发，穿棕金厚毛衣 + 背带裤，脚边一台小机柜（本地机房），气质憨厚、力气大、能本地扛。
主色调：棕金 #8A5A2B + 米 #EFE3CE。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "Meta Llama" by Meta. Give it a distinctive signature prop that hints at its strength (完全本地零 API 费), and a confident personality. Palette: 棕金 #8A5A2B + 米 #EFE3CE. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## Ollama（本地）（`ollama`）　开源 · 本地 · ⏳ 待接入

| 项 | 值 |
|---|---|
| 配色 | 灰白 #E6E6E6 + 可可色 #7A4B2A |
| 发型 | 灰白乱发 |
| 服装 | 灰白连帽衫 + 围裙 |
| 道具 | 身边一只小羊驼玩偶 |
| 气质 | 佛系、断网也能干、零成本 |
| 特色 | 断网也能干活、零 API 成本；质量看硬件 |
| 综合评分 | **2.90** / 5 ｜ 中文 3 · 代码 3 · 接入难度 2 · 免费额度：完全免费 |
| 文件名 | `ollama.sheet.png` + `ollama.portrait.png` |

**中文提示词：**

```
请画一张透明背景的 Q 版像素风角色图集：角色是「Ollama（本地）」，灰白乱发，穿灰白连帽衫 + 围裙，身边一只小羊驼玩偶，气质佛系、断网也能干、零成本。
主色调：灰白 #E6E6E6 + 可可色 #7A4B2A。
尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。
```

**English prompt:**

```
A chibi pixel-art character sprite sheet of a mascot for the AI model "Ollama（本地）" by 开源. Give it a distinctive signature prop that hints at its strength (断网也能干活、零 API 成本；质量看硬件), and a confident personality. Palette: 灰白 #E6E6E6 + 可可色 #7A4B2A. exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, large clear eyes; character fills 90% of cell height, feet on the bottom edge, 2 px margin left/right; fully transparent background; no text, watermark, name plate, speech bubble, ground shadow or white background.
```

---

## 自定义模型（你自己上传的图）

任何一张图都能变成办公室里的一个"模型/员工"：

```bash
# 单张立绘（自动切成 3 行 × 7 列 + 头像）
python tools/add_custom_agent.py --image D:\我的图.png --name "我的模型" --key mymodel --model glm
# 只想先看看产物、不安装：去掉 --install 即可
```
