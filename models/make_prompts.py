# -*- coding: utf-8 -*-
"""按模型注册表生成"逐模型美术提示词包"（图由人来做，这里只出提示词）。

产物：assets/PROMPTS.md —— 每个模型一段：
  · 中文提示词（可直接粘给出图 AI）
  · 英文提示词
  · 配色 / 人设 / 道具 / 文件名
所有提示词共享同一段"通用风格块"，保证 19 个角色风格统一（这是能拼成一间办公室的关键）。
"""
import io
import json
import os

R = r'D:\徐\星域蜂巢'
REG = os.path.join(R, 'models', 'registry.json')
OUT = os.path.join(R, 'assets', 'PROMPTS.md')

# 每个模型的视觉设定：颜色 / 发色 / 服装 / 道具 / 气质
LOOK = {
    'deepseek':      ('深海蓝 #1B4B8F + 电光青 #38E1C6', '深蓝短发带一缕青光', '深蓝工装夹克 + 耳机',
                      '手提发光终端板', '冷静、算得快、主力干将'),
    'glm':           ('纯白 #FFFFFF + 青绿 #2ED3A8', '银白发扎小马尾', '白衬衫 + 青绿围裙',
                      '抱着一个写着"免费"的小木箱', '热心、爱帮忙、白干活也不抱怨'),
    'kimi':          ('夜空紫 #4B3A8F + 淡金 #E8D6A0', '紫色长发戴圆眼镜', '深紫毛衣 + 书袋',
                      '抱一摞几乎举不动的厚书', '安静、博闻、抱着整本书也能记住'),
    'qwen':          ('藏青 #1F3A5F + 橙 #F0803C', '短黑发束发带', '藏青工程师马甲 + 卷起袖子',
                      '扳手 + 卷起的图纸', '踏实、标准件、最可靠的工程派'),
    'doubao':        ('暖黄 #F5C542 + 奶白 #FFF3D6', '蓬松黄短发', '明黄卫衣 + 斜挎小包',
                      '抱一堆待办小纸条', '活泼、手脚快、专干批量杂活'),
    'ernie':         ('墨绿 #1F5C4A + 青花白 #EDF6F2', '黑发束冠', '中式立领长衫 + 卷轴袋',
                      '手持毛笔与展开的卷轴', '斯文、中文语感极好'),
    'hunyuan':       ('深蓝 #12294A + 金 #D8B24C', '黑发整齐背头', '深蓝制服 + 金边肩章',
                      '齿轮徽章 + 太极纹样腰带', '稳重、体系内、讲流程'),
    'mimo':          ('橙红 #E8552F + 灰白 #E9E4DC', '栗色短发戴运动帽', '橙红冲锋衣 + 大背包',
                      '背上一个超大的文件背包', '耐力强、能扛超大文件'),
    'minimax':       ('粉紫 #C46BD8 + 深紫 #3A1E4F', '粉紫长卷发', '紫色长裙 + 披肩',
                      '抽出极长的纸条卷轴', '温柔、话多、擅长长文本'),
    'baichuan':      ('湖蓝 #2C7A9E + 米白 #F2EAD8', '黑发束巾', '湖蓝学者袍 + 书箱',
                      '抱一摞古籍', '博学、讲究出处'),
    'spark':         ('科技蓝 #1560BD + 白 #F5F9FF', '黑发戴头戴耳机', '蓝白运动服 + 麦克风胸针',
                      '头戴耳机 + 录音笔', '耳朵灵、听说都强'),
    'yi':            ('石板灰 #5A6B7C + 天青 #7FC8E8', '灰色短发', '灰蓝工装 + 工具腰带',
                      '抱着一个贴着开源标签的木箱', '务实、愿意共享、可私有部署'),
    'openai':        ('墨绿 #0F3D33 + 亮金 #C8A94A', '深色卷发', '墨绿长外套 + 白衬衫',
                      '手持一支发光钢笔', '职业、稳、代码功底扎实'),
    'claude':        ('陶土橙 #D97757 + 深灰 #2B2B2B', '亚麻色短发', '橙棕长开衫 + 衬衫',
                      '拿着红笔批注的稿纸', '审慎、爱挑错、长篇任务之王'),
    'gemini':        ('蓝紫渐变 #4285F4→#9B72CB', '银蓝短发', '渐变蓝紫风衣',
                      '手持望远镜 + 星图', '看得最远、上下文最长'),
    'grok':          ('哑黑 #1A1A1A + 金 #E0B84C', '黑发挑染金', '黑色皮夹克 + 铆钉',
                      '手指顶着一个小火箭模型', '叛逆、直率、消息灵通'),
    'mistral':       ('蓝白红三色 #2B4C8C / #FFFFFF / #C8102E', '亚麻色中长发', '蓝白红配色风衣 + 贝雷帽',
                      '身边绕着一阵风', '轻盈、快、欧洲开源派'),
    'llama':         ('棕金 #8A5A2B + 米 #EFE3CE', '栗色卷发', '棕金厚毛衣 + 背带裤',
                      '脚边一台小机柜（本地机房）', '憨厚、力气大、能本地扛'),
    'ollama':        ('灰白 #E6E6E6 + 可可色 #7A4B2A', '灰白乱发', '灰白连帽衫 + 围裙',
                      '身边一只小羊驼玩偶', '佛系、断网也能干、零成本'),
}

SHARED_CN = (
    '尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、第 3 行侧面朝右；'
    '每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。'
    '三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；'
    '角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；'
    '纯透明背景，**不要**文字/水印/名字牌/对话气泡/地面阴影/白底。'
)
SHARED_EN = ('exactly 504x324 px, 7 columns x 3 rows, 72x108 per cell; row1 front, row2 back, '
             'row3 side facing RIGHT; 7 frames per row (1-4 walking, 5-7 standing / working / reading); '
             'chibi 3-heads-tall, thick dark outlines, soft gradient shading, glossy hair highlight, '
             'large clear eyes; character fills 90% of cell height, feet on the bottom edge, '
             '2 px margin left/right; fully transparent background; no text, watermark, name plate, '
             'speech bubble, ground shadow or white background.')

reg = json.load(io.open(REG, encoding='utf-8'))
L = []
L.append('# 逐模型美术提示词包（图由人来出）\n')
L.append('> 用法：找到模型 → 复制"中文提示词"整段 → 粘给出图 AI → 出图另存为 **`<id>.sheet.png`**（504×324）')
L.append('> 再出一张头像另存为 **`<id>.portrait.png`**（144×216）→ 丢进 `assets/chars/` → 跑 `python art/check_assets.py` 自检。\n')
L.append('> 想省事：只画一张大图（一行一个角色、左侧留 100px 标签栏，1536×1024 起），'
         '然后 `python import_assets.py sheet --image assets/source/cast-sheet.png --map assets/cast-map.example.json`。\n')
L.append('> 硬性规格与禁止项见 `assets/ART-SPEC.md`。\n')
L.append('---\n')
L.append('## 通用风格块（每段提示词都已包含，不用手动拼）\n')
L.append('```')
L.append(SHARED_CN)
L.append('```\n')

for m in reg['models']:
    mid = m['id']
    colors, hair, outfit, prop, vibe = LOOK.get(mid, ('自定义配色', '自定义发型', '自定义服装', '自定义道具', '自定义气质'))
    L.append('## %s（`%s`）　%s · %s · %s\n' % (m['name'], mid, m['vendor'], m['region'],
                                            '✅ 已接入' if m['connected'] else '⏳ 待接入'))
    L.append('| 项 | 值 |')
    L.append('|---|---|')
    L.append('| 配色 | %s |' % colors)
    L.append('| 发型 | %s |' % hair)
    L.append('| 服装 | %s |' % outfit)
    L.append('| 道具 | %s |' % prop)
    L.append('| 气质 | %s |' % vibe)
    L.append('| 特色 | %s |' % m['note'])
    L.append('| 综合评分 | **%.2f** / 5 ｜ 中文 %d · 代码 %d · 接入难度 %d · 免费额度：%s |'
             % (m['score'], m['cn'], m['code'], m['difficulty'], m['free']))
    L.append('| 文件名 | `%s.sheet.png` + `%s.portrait.png` |\n' % (mid, mid))
    L.append('**中文提示词：**\n')
    L.append('```')
    L.append('请画一张透明背景的 Q 版像素风角色图集：角色是「%s」，%s，穿%s，%s，气质%s。'
             % (m['name'], hair, outfit, prop, vibe))
    L.append('主色调：%s。' % colors)
    L.append(SHARED_CN)
    L.append('```\n')
    L.append('**English prompt:**\n')
    L.append('```')
    L.append('A chibi pixel-art character sprite sheet of a mascot for the AI model "%s" by %s. '
             'Give it a distinctive signature prop that hints at its strength (%s), and a confident personality. '
             'Palette: %s. %s'
             % (m['name'], m['vendor'], m['note'].split('：')[0].split('，')[0][:24], colors, SHARED_EN))
    L.append('```\n')
    L.append('---\n')

L.append('## 自定义模型（你自己上传的图）\n')
L.append('任何一张图都能变成办公室里的一个"模型/员工"：\n')
L.append('```bash')
L.append('# 单张立绘（自动切成 3 行 × 7 列 + 头像）')
L.append('python tools/add_custom_agent.py --image D:\\我的图.png --name "我的模型" --key mymodel --model glm')
L.append('# 只想先看看产物、不安装：去掉 --install 即可')
L.append('```\n')

io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
print('  已生成 %s（%d 个模型，%d 行）' % (OUT, len(reg['models']), len(L)))
print('  已接入 %d ｜ 待接入 %d' % (sum(1 for m in reg['models'] if m['connected']),
                                sum(1 for m in reg['models'] if not m['connected'])))
