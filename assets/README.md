# 像素素材说明

本目录随仓库附带**一套可直接用的素材**，同时也是**导入你自己素材的示例**。

## 自带素材

| 文件 | 内容 | 用途 |
|---|---|---|
| `chars/<key>.sheet.png` | 每个角色 3 行 × 7 列（行 = 正面/背面/侧面；列 = 行走 4 帧 + 工作/阅读姿态） | 引擎按 `window.__MD_CAST` 读取 |
| `chars/<key>.portrait.png` | 144×216 头像 | 界面里员工栏的头像 |
| `map/office-atlas.png` | 整间办公室的贴图集（Tiled 用） | `patches/patch_map.py` 会把它换成办公室底图 |
| `source/cast-sheet.png` | 原始角色表（一行一个角色，含左侧标签牌） | 用 `import_assets.py sheet` 重新切图的输入 |

角色 key 与工位的对应关系见 `cast-map.example.json`。

## 导入你自己的素材（三种方式）

```bash
# A) 单个角色（一张立绘即可）
python import_assets.py char --image my-hero.png --name "我的英雄" --key hero --install

# B) 一整张角色表（一行一个角色）——改 cast-map.json 里的 rows_map
python import_assets.py sheet --image my-sheet.png --map my-cast-map.json --install

# C) 换掉整间办公室的贴图
python import_assets.py map --image my-office.png --uniform 50
```

产物默认落在 `build/assets/`，加 `--install` 才会调用 `patches/patch_renderer.py` 生效（**会自动备份 + 过 esbuild 语法门**）。

## 素材规格（想自己画就照这个）

- 单元尺寸：**72 × 108**（宽 × 高），按角色实际高度自动缩放并底部对齐。
- 行顺序：**第 1 行正面、第 2 行背面、第 3 行侧面**（侧面向右，引擎向左走时自动水平翻转）。
- 列顺序建议：`[走1, 走2, 走3, 工作1, 工作2, 阅读1, 阅读2]`（本仓库的切图脚本会自动合成微动帧）。
- 背景：**透明**。若原图是浅色棋盘格/纯色底，`art/build_cast2.py` 的洪水填充会去掉，并做连通块清理（防止把邻格的"半个人"带进来）。
- 说话气泡、名字标签、座位朝向都由引擎负责，不需要画在图里。

## 版权与授权

- 本目录素材由仓库作者创作（AI 辅助生成后人工筛选/清理），随本仓库以 **MIT** 授权分发。
- 若你替换为自己的素材，请保留你自己的授权说明；**不要**提交来源不明或含他人版权角色的素材。
