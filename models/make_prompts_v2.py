# -*- coding: utf-8 -*-
"""v2：出图提示词的配色改为【实测/官方的真实品牌色】（models/brand-colors.json），
   角色外形仍基于网上真实评价。只做我们还没有的 16 个。
   产物：assets/PROMPTS.md
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

# id, 显示名, 属地, 真实特色, 依据链接, 二创/常识形象, 服装与外形, 道具, 气质
M = [
 ('glm', 'GLM（智谱）', '国产', 'GLM-4.7-Flash 完全免费、200K 上下文，零成本调用',
  'https://ofox.ai/zh/blog/glm-4-7-flash-free-api-china-guide-2026/',
  '「免费长卷」', '银白发扎小马尾，白衬衫 + 围裙', '抱一卷极长、写着「FREE」的卷轴', '热心、来者不拒'),
 ('kimi', 'Kimi', '国产', '以超长上下文著称（月之暗面 Moonshot），适合整本书/整仓库',
  'https://wapbaike.baidu.com/item/Kimi%20K2/66209805',
  '月亮（Moonshot=月之暗面）', '深蓝长发、发梢一点月光银，深蓝毛衣 + 书袋', '抱一摞厚书，肩上落一弯月牙', '安静、博闻'),
 ('qwen', '通义千问 Qwen', '国产', '开源生态标杆，新一代模型成本大幅下降',
  'https://www.alibabacloud.com/tc/press-room/alibaba-introduces-qwen3-setting-new-benchmark',
  '开源工具箱', '短黑发束发带，纯蓝工程师马甲 + 卷袖', '一手扳手、一手摊开的开源图纸', '踏实、标准件'),
 ('doubao', '豆包 Doubao', '国产', '2.1 版本，便宜量大，性价比路线',
  'http://rss.jingjiribao.cn/static/detail.jsp?id=665423',
  '「豆包」（包子）', '蓬松深棕短发，浅天蓝卫衣 + 斜挎小包', '两手各抓一把待办小纸条', '活泼、手脚极快'),
 ('hunyuan', '腾讯混元', '国产', 'Hy3 主打 Agent 能力与高性价比，「参数做减法、智能做加法」',
  'https://www.stdaily.com/web/gdxw/2026-07/06/content_542974.html',
  '太极/混沌', '黑发背头，腾讯蓝制服 + 金边肩章', '手里只拿一个极简齿轮，却驱动一台大机器', '稳重、精炼'),
 ('mimo', '小米 MiMo', '国产', '小米基座大模型，尺寸小、可本地运行',
  'https://baike.baidu.com/item/%E5%B0%8F%E7%B1%B3%E5%A4%A7%E6%A8%A1%E5%9E%8B/69005522',
  '小米橙', '栗色短发戴运动帽，橙色冲锋衣 + 轻便小包', '背着轻便小包轻松小跑', '轻快、耐力好'),
 ('minimax', 'MiniMax', '国产', 'MiniMax-M2 开源并跻身全球前五，定位 agent 模型',
  'http://www.xinhuanet.com.cn/tech/20251029/2f3ad6e3a5164af28b19e19b681a1549/c.html',
  '海螺（海螺 AI）', '橙红短发 + 品红挑染，竞技披风', '胸前「TOP 5」徽章，一手举开源旗帜', '好胜、能打'),
 ('ernie', '文心一言 ERNIE', '国产', '百度千帆生态，中文语感好',
  'https://cloud.baidu.com/doc/qianfan/s/rmh4stp0j',
  '文心/墨水', '黑发束冠，文心蓝中式立领长衫', '手持毛笔与展开的中文卷轴', '斯文、讲究措辞'),
 ('baichuan', '百川 Baichuan', '国产', '医疗方向见长，新模型幻觉率低至 2.6%',
  'https://36kr.com/p/3650704809369728',
  '百川入海', '黑发束巾，白大褂 + 湖蓝内衬', '脖子上挂写有「2.6%」的听诊器，另一手拿病例夹', '严谨、绝不说没把握的话'),
 ('spark', '讯飞星火', '国产', '语音与中文见长，Spark-X2.5-4B 等小尺寸 + API 矩阵',
  'https://www.xfyun.cn/site/1610.html',
  '火星（星火）', '黑发戴头戴耳机，青蓝运动服 + 红色滚边', '头戴耳机 + 手持录音笔', '耳朵灵、边聊边做'),
 ('yi', '零一万物 Yi', '国产', '务实转型，收起超大模型、转向应用与落地',
  'https://www.c114.net.cn/industry/53393.html',
  '零一（01）', '灰色短发，墨青工装 + 工具腰带', '把写着「超大」的箱子合上放一边，手里拿趁手小工具', '务实、果断'),
 ('ollama', 'Ollama（本地）', '本地', '本地大模型工具爆火，用户破 900 万，零依赖私有部署',
  'https://news.qiniu.com/archives/1783932835347',
  '羊驼（llama 谐音）', '黑白极简配色，灰白乱发，连帽衫 + 围裙', '脚边一台小机柜 + 怀里一只小羊驼玩偶', '佛系、断网也在岗'),
 ('gemini', 'Google Gemini', '国外', '上下文极长（百万级 token），适合整仓库投喂',
  'https://deepmind.google/technologies/gemini/',
  '双子（Gemini=双胞胎）', '银蓝短发，蓝紫渐变风衣', '手持望远镜与铺开的星图', '看得最远'),
 ('grok', 'xAI Grok', '国外', '实时信息与直率风格，国内不可直连',
  'https://x.ai/',
  '火箭/赛博', '纯黑皮夹克 + 金色铆钉，黑发挑染金', '手指顶着一枚小火箭，另一手刷实时信息流', '叛逆、直率'),
 ('mistral', 'Mistral AI', '国外', '欧洲开源派，轻量高效（名字来自西北风）',
  'https://mistral.ai/',
  '风（Mistral=西北风）', '红橙渐变风衣 + 贝雷帽，亚麻色中长发', '身边卷着一阵风，衣角被吹起', '轻盈、干脆'),
 ('llama', 'Meta Llama', '国外', '开源权重代表，可完全本地部署',
  'https://www.llama.com/',
  '羊驼（Llama）', '栗色卷发，Meta 蓝厚毛衣 + 背带裤', '身边一台自己装好的机柜，抱着开源权重硬盘', '憨厚、力气大'),
]

L = []
L.append('# 逐模型出图提示词 v2（**配色 = 实测/官方真实品牌色**）\n')
L.append('> 只做我们**还没有**的 16 个模型（DeepSeek / Claude / OpenAI GPT 已接入，跳过）。\n')
L.append('> **配色依据**：抓取各家官网 favicon 主色与 theme-color 实测（`models/brand-colors.json`），'
         '抓不到的用官方文档色并标注来源。角色外形依据网上真实评价。\n')
L.append('> 出图后另存为 `<id>.sheet.png`（504×324）与 `<id>.portrait.png`（144×216），'
         '丢进 `assets/chars/`，跑 `python art\\check_assets.py` 自检。硬性规格见 `assets/ART-SPEC.md`。\n')
L.append('---\n')

for (mid, name, region, trait, src, motif, look, prop, vibe) in M:
    b = BRAND.get(mid, {})
    pal = b.get('palette') or ['#888888']
    from_ = b.get('from') or '（未取到）'
    measured = not any(k in str(from_) for k in ('品牌', '官网黑白', '规范', '官方'))
    pal_txt = ' + '.join(pal[:3])
    L.append('## %s（`%s`）　%s\n' % (name, mid, region))
    L.append('| 项 | 内容 |')
    L.append('|---|---|')
    L.append('| **官方色（%s）** | %s |' % ('实测 favicon' if measured else '官方文档', pal_txt))
    L.append('| 取色来源 | `%s` |' % from_)
    L.append('| 真实特色 | %s |' % trait)
    L.append('| 评价来源 | [%s](%s) |' % (src.split('/')[2], src))
    L.append('| 二创/常识形象 | %s |' % motif)
    L.append('| 外形 | %s ｜ 道具：%s ｜ 气质：%s |' % (look, prop, vibe))
    L.append('| 文件名 | `%s.sheet.png` + `%s.portrait.png` |\n' % (mid, mid))
    L.append('```')
    L.append('请画一张透明背景的 Q 版像素风角色图集：角色代表「%s」这个 AI 模型。' % name)
    L.append('它的真实特点是：%s。' % trait)
    L.append('**配色必须用该品牌的官方色：主色 %s**（这是它官网/App 的品牌色，务必以此为准）。'
             % pal_txt)
    L.append('外形：%s；%s；气质%s。' % (look, prop, vibe))
    L.append(SHARED_CN)
    L.append('```\n')
    L.append('---\n')

L.append('## 自定义模型（你自己上传的图）\n')
L.append('```powershell')
L.append('python tools\\add_custom_agent.py --image D:\\我的图.png --name "我的模型" --key mymodel --model glm --install')
L.append('```\n')
L.append('## 全部品牌色一览（实测）\n')
L.append('| 模型 | 官方色 | 来源 |')
L.append('|---|---|---|')
for (mid, name, region, *_r) in M:
    b = BRAND.get(mid, {})
    L.append('| %s | %s | %s |' % (name, ' + '.join((b.get('palette') or ['-'])[:3]), b.get('from') or '-'))

io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
print('  已生成 %s：%d 个模型 ｜ %d 行' % (OUT, len(M), len(L)))
print('  配色来源：实测 favicon %d 个 ｜ 官方文档 %d 个' % (
    sum(1 for (mid, *_r) in M if 'favicon' in str(BRAND.get(mid, {}).get('from'))),
    sum(1 for (mid, *_r) in M if 'favicon' not in str(BRAND.get(mid, {}).get('from')))))
