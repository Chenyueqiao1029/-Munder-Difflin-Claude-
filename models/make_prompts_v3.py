# -*- coding: utf-8 -*-
"""v3：外形依据分两类——
   A. 有公开二创：直接采用二创设定（附来源链接）
   B. 无公开二创：本仓库原创设定，并**明确标注**（只锚定官方品牌色 + 功能特色）
   配色统一用实测/官方品牌色（models/brand-colors.json）。只做我们还没接入的 16 个。
"""
import io
import json
import os

R = r'D:\徐\星域蜂巢'
BRAND = json.load(io.open(os.path.join(R, 'models', 'brand-colors.json'), encoding='utf-8'))['data']
OUT = os.path.join(R, 'assets', 'PROMPTS.md')

SHARED_CN = ('尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、'
             '第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。'
             '三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；'
             '角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；'
             '纯透明背景，不要文字/水印/名字牌/对话气泡/地面阴影/白底。')

OPENPET = 'https://github.com/AwesomeHou/openpet-ai-girls'
QIANWEN = 'https://zhuanlan.zhihu.com/p/2075877853825069166'
DSCHAN = 'https://github.com/Mentha-Azure/deepseek-chan-qqbot'

# id, 名, 属地, 真实特色, 评价来源, 二创依据(链接或 None), 外形, 道具, 气质
M = [
 ('glm', 'GLM（智谱）', '国产', 'GLM-4.7-Flash 完全免费、200K 上下文，零成本调用',
  'https://ofox.ai/zh/blog/glm-4-7-flash-free-api-china-guide-2026/', None,
  '银白发扎小马尾，白衬衫 + 围裙（原创）', '抱一卷极长、写着「FREE」的卷轴', '热心、来者不拒'),
 ('kimi', 'Kimi', '国产', '以超长上下文著称（月之暗面 Moonshot），适合整本书/整仓库',
  'https://wapbaike.baidu.com/item/Kimi%20K2/66209805', None,
  '深蓝长发、发梢一点月光银，深蓝毛衣 + 书袋（原创，锚定「月之暗面」）',
  '抱一摞厚书，肩上落一弯月牙', '安静、博闻'),
 ('qwen', '通义千问 Qwen', '国产', '开源生态标杆，新一代模型成本大幅下降',
  'https://www.alibabacloud.com/tc/press-room/alibaba-introduces-qwen3-setting-new-benchmark', QIANWEN,
  '蓝发中文少女（**采用「千问娘」二创方向**），束发带 + 工程师马甲',
  '一手扳手、一手摊开的开源图纸', '踏实、标准件'),
 ('doubao', '豆包 Doubao', '国产', '2.1 版本，便宜量大，性价比路线',
  'http://rss.jingjiribao.cn/static/detail.jsp?id=665423', OPENPET,
  '**黑白洛丽塔风 + 短深色发型**（采用 openpet-ai-girls 的二创设定）',
  '两手各抓一把待办小纸条', '活泼、手脚极快'),
 ('hunyuan', '腾讯混元', '国产', 'Hy3 主打 Agent 能力与高性价比，「参数做减法、智能做加法」',
  'https://www.stdaily.com/web/gdxw/2026-07/06/content_542974.html', None,
  '黑发背头，腾讯蓝制服 + 金边肩章（原创）',
  '手里只拿一个极简齿轮，却驱动一台大机器', '稳重、精炼'),
 ('mimo', '小米 MiMo', '国产', '小米基座大模型，尺寸小、可本地运行',
  'https://baike.baidu.com/item/%E5%B0%8F%E7%B1%B3%E5%A4%A7%E6%A8%A1%E5%9E%8B/69005522', None,
  '栗色短发戴运动帽，橙色冲锋衣 + 轻便小包（原创）',
  '背着轻便小包轻松小跑', '轻快、耐力好'),
 ('minimax', 'MiniMax', '国产', 'MiniMax-M2 开源并跻身全球前五，定位 agent 模型',
  'http://www.xinhuanet.com.cn/tech/20251029/2f3ad6e3a5164af28b19e19b681a1549/c.html', None,
  '橙红短发 + 品红挑染，竞技披风（原创，锚定海螺 AI 橙红）',
  '胸前「TOP 5」徽章，一手举开源旗帜', '好胜、能打'),
 ('ernie', '文心一言 ERNIE', '国产', '百度千帆生态，中文语感好',
  'https://cloud.baidu.com/doc/qianfan/s/rmh4stp0j', None,
  '黑发束冠，文心蓝中式立领长衫（原创）',
  '手持毛笔与展开的中文卷轴', '斯文、讲究措辞'),
 ('baichuan', '百川 Baichuan', '国产', '医疗方向见长，新模型幻觉率低至 2.6%',
  'https://36kr.com/p/3650704809369728', None,
  '黑发束巾，白大褂 + 品牌橙内衬（原创）',
  '脖子上挂写有「2.6%」的听诊器，另一手拿病例夹', '严谨、绝不说没把握的话'),
 ('spark', '讯飞星火', '国产', '语音与中文见长，Spark-X2.5-4B 等小尺寸 + API 矩阵',
  'https://www.xfyun.cn/site/1610.html', None,
  '黑发戴头戴耳机，品牌青蓝运动服 + 火焰红滚边（原创）',
  '头戴耳机 + 手持录音笔', '耳朵灵、边聊边做'),
 ('yi', '零一万物 Yi', '国产', '务实转型，收起超大模型、转向应用与落地',
  'https://www.c114.net.cn/industry/53393.html', None,
  '灰色短发，品牌墨青工装 + 工具腰带（原创）',
  '把写着「超大」的箱子合上放一边，手里拿趁手小工具', '务实、果断'),
 ('ollama', 'Ollama（本地）', '本地', '本地大模型工具爆火，用户破 900 万，零依赖私有部署',
  'https://news.qiniu.com/archives/1783932835347', None,
  '黑白极简，灰白乱发，连帽衫 + 围裙，**羊驼**（llama 谐音，社区通用形象）',
  '脚边一台小机柜 + 怀里一只小羊驼玩偶', '佛系、断网也在岗'),
 ('gemini', 'Google Gemini', '国外', '上下文极长（百万级 token），适合整仓库投喂',
  'https://deepmind.google/technologies/gemini/', OPENPET,
  '**彩虹发色 + 明亮活泼**（采用 openpet-ai-girls 的二创设定）',
  '手持望远镜与铺开的星图', '看得最远'),
 ('grok', 'xAI Grok', '国外', '实时信息与直率风格，国内不可直连',
  'https://x.ai/', None,
  '纯黑皮夹克 + 金色铆钉，黑发挑染金（原创）',
  '手指顶着一枚小火箭，另一手刷实时信息流', '叛逆、直率'),
 ('mistral', 'Mistral AI', '国外', '欧洲开源派，轻量高效（名字来自西北风）',
  'https://mistral.ai/', None,
  '品牌红橙渐变风衣 + 贝雷帽，亚麻色中长发（原创）',
  '身边卷着一阵风，衣角被吹起', '轻盈、干脆'),
 ('llama', 'Meta Llama', '国外', '开源权重代表，可完全本地部署',
  'https://www.llama.com/', None,
  '栗色卷发，Meta 蓝厚毛衣 + 背带裤，**羊驼**（社区通用形象）',
  '身边一台自己装好的机柜，抱着开源权重硬盘', '憨厚、力气大'),
]

L = []
L.append('# 逐模型出图提示词 v3\n')
L.append('> 只做我们**还没有**的 16 个模型（DeepSeek / Claude / OpenAI GPT 已接入，跳过）。\n')
L.append('')
L.append('## 本次两个依据都去查了（不再凭印象）\n')
L.append('**① 官方品牌色**：抓各家官网 favicon 主色 + theme-color 实测（8 个实测、8 个官方文档色），'
         '明细见 `models/brand-colors.json`，每段都写明了取色来源。\n')
L.append('**② 二创（网上别人的拟人设定）**：去 GitHub 仓库与中文社区搜过，**结论如下**——\n')
L.append('| 模型 | 二创情况 | 来源 |')
L.append('|---|---|---|')
L.append('| DeepSeek | **有**：鲸鱼娘，蓝发 + 星空感 + 优雅；社区人设「嘴毒心软、有脾气有记性」 | '
         '[openpet-ai-girls](%s)、[deepseek-chan-qqbot](%s)、[网易](https://m.163.com/dy/article/L4RDL7210511805E.html) |' % (OPENPET, DSCHAN))
L.append('| 豆包 | **有**：黑白洛丽塔风 + 短深色发 | [openpet-ai-girls](%s) |' % OPENPET)
L.append('| Gemini | **有**：彩虹发色 + 明亮活泼 | [openpet-ai-girls](%s) |' % OPENPET)
L.append('| ChatGPT | **有**：薄荷绿主色 + 白绿服饰 | [openpet-ai-girls](%s) |' % OPENPET)
L.append('| Claude | **有**：橙粉长发 + 白色荷叶边裙 + 橙缎带 | [openpet-ai-girls](%s) |' % OPENPET)
L.append('| 通义千问 | **有（图文）**：社区存在「千问娘」 | [知乎：千问娘](%s) |' % QIANWEN)
L.append('| GLM / Kimi / 混元 / MiMo / MiniMax / 文心 / 百川 / 星火 / Yi / Ollama / Grok / Mistral / Llama | '
         '**没搜到成型的公开二创仓库**：这些的二创主要散在 B站/小红书/知乎的图和视频里，'
         '没有可引用的统一设定 → 因此**下面的外形是本仓库原创**，只锚定官方品牌色与功能特色 | '
         '[中文社区「AI 娘小剧场」示例](https://linux.do/t/topic/2052255/4) |')
L.append('')
L.append('> ⚠️ 所以每段提示词都标了「采用二创设定」或「原创」——你出图时可以按需替换。\n')
L.append('---\n')

for (mid, name, region, trait, src, ref, look, prop, vibe) in M:
    b = BRAND.get(mid, {})
    pal = b.get('palette') or ['#888888']
    from_ = b.get('from') or '（未取到）'
    measured = 'favicon' in str(from_)
    pal_txt = ' + '.join(pal[:3])
    tag = '**采用二创设定**（[%s](%s)）' % (ref.split('/')[2] if ref else '', ref) if ref else '**本仓库原创设定**（无公开二创可依）'
    L.append('## %s（`%s`）　%s　%s\n' % (name, mid, region, tag))
    L.append('| 项 | 内容 |')
    L.append('|---|---|')
    L.append('| 官方色（%s） | %s |' % ('实测 favicon' if measured else '官方文档', pal_txt))
    L.append('| 取色来源 | `%s` |' % from_)
    L.append('| 真实特色 | %s |' % trait)
    L.append('| 评价来源 | [%s](%s) |' % (src.split('/')[2], src))
    L.append('| 外形 | %s ｜ 道具：%s ｜ 气质：%s |' % (look, prop, vibe))
    L.append('| 文件名 | `%s.sheet.png` + `%s.portrait.png` |\n' % (mid, mid))
    L.append('```')
    L.append('请画一张透明背景的 Q 版像素风角色图集：角色代表「%s」这个 AI 模型。' % name)
    L.append('它的真实特点是：%s。' % trait)
    L.append('配色必须用该品牌的官方色：主色 %s（官网/App 品牌色，以此为准）。' % pal_txt.replace('**', ''))
    L.append('外形：%s；%s；气质%s。' % (look.replace('**', ''), prop.replace('**', ''), vibe.replace('**', '')))
    L.append(SHARED_CN)
    L.append('```\n')
    L.append('---\n')

io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
n_ref = sum(1 for m in M if m[5])
print('  已生成 %s：%d 个模型 ｜ %d 行' % (OUT, len(M), len(L)))
print('  采用二创设定 %d 个 ｜ 本仓库原创 %d 个' % (n_ref, len(M) - n_ref))
