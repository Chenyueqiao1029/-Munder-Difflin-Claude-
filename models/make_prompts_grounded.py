# -*- coding: utf-8 -*-
"""按"网上对它们的真实评价与特色"生成出图提示词 —— 只做我们【还没有】的 16 个模型。
每个模型都带「依据」（可点开的来源链接），不靠我编。产物：assets/PROMPTS.md
"""
import io
import os

R = r'D:\徐\星域蜂巢'
OUT = os.path.join(R, 'assets', 'PROMPTS.md')

SHARED_CN = ('尺寸正好 504×324 像素，7 列 × 3 行，每格 72×108；第 1 行正面、第 2 行背面、'
             '第 3 行侧面朝右；每行 7 帧：前 4 帧行走、后 3 帧站立 / 伏案工作 / 阅读。'
             '三头身 Q 版，深色描边，柔和渐变着色，头发有高光，眼睛大而清晰；'
             '角色占满格子高度的 90%，脚底贴下边缘，左右各留 2 像素不要顶到相邻格子；'
             '纯透明背景，不要文字/水印/名字牌/对话气泡/地面阴影/白底。')

# (id, 显示名, 属地, 真实特色, 依据链接, 视觉设定, 道具, 气质)
M = [
 ('glm', 'GLM（智谱）', '国产',
  'GLM-4.7-Flash 完全免费、200K 上下文，零成本调用',
  'https://ofox.ai/zh/blog/glm-4-7-flash-free-api-china-guide-2026/',
  '青绿 #2ED3A8 与纯白，银白发扎小马尾，白衬衫 + 青绿围裙',
  '抱着一卷极长、写着「FREE」的卷轴（象征 200K 长上下文 + 免费）',
  '热心、来者不拒、白干活也不抱怨'),
 ('kimi', 'Kimi', '国产',
  '以超长上下文著称，适合整本书/整仓库',
  'https://wapbaike.baidu.com/item/Kimi%20K2/66209805',
  '夜空紫 #4B3A8F 与淡金，紫色长发戴圆眼镜，深紫毛衣 + 书袋',
  '抱一摞几乎举不动的厚书，脚边还有一本翻开的',
  '安静、博闻、把整本书装进脑子里'),
 ('qwen', '通义千问 Qwen', '国产',
  '开源生态标杆，新一代模型成本大幅下降',
  'https://www.alibabacloud.com/tc/press-room/alibaba-introduces-qwen3-setting-new-benchmark',
  '藏青 #1F3A5F 与橙 #F0803C，短黑发束发带，工程师马甲 + 卷袖',
  '一手扳手、一手摊开的开源图纸，腰间挂着开源盒子',
  '踏实、标准件、最可靠的工程派'),
 ('doubao', '豆包 Doubao', '国产',
  '2.1 版本，便宜量大，性价比路线',
  'http://rss.jingjiribao.cn/static/detail.jsp?id=665423',
  '暖黄 #F5C542 与奶白，蓬松黄短发，明黄卫衣 + 斜挎小包',
  '两手各抓一把待办小纸条，脚边堆着更多',
  '活泼、手脚极快、专干批量杂活'),
 ('hunyuan', '混元 Hunyuan', '国产',
  'Hy3 主打 Agent 能力与高性价比，「参数做减法、智能做加法」',
  'https://www.stdaily.com/web/gdxw/2026-07/06/content_542974.html',
  '深蓝 #12294A 与金 #D8B24C，黑发背头，深蓝制服 + 金边肩章',
  '手里只拿一个极简齿轮（象征参数做减法），却在驱动一台大机器',
  '稳重、精炼、不讲废话'),
 ('mimo', 'MiMo（小米）', '国产',
  '小米基座大模型，尺寸小、可本地运行',
  'https://baike.baidu.com/item/%E5%B0%8F%E7%B1%B3%E5%A4%A7%E6%A8%A1%E5%9E%8B/69005522',
  '橙红 #E8552F 与灰白，栗色短发戴运动帽，橙红冲锋衣 + 小背包',
  '背着轻便小包轻松小跑（象征小尺寸高能效）',
  '轻快、耐力好、不挑机器'),
 ('minimax', 'MiniMax', '国产',
  'MiniMax-M2 开源并跻身全球前五，定位 agent 模型',
  'http://www.xinhuanet.com.cn/tech/20251029/2f3ad6e3a5164af28b19e19b681a1549/c.html',
  '粉紫 #C46BD8 与深紫，粉紫长卷发，紫色长裙 + 竞技披风',
  '胸前一枚「TOP 5」徽章，一手举开源旗帜',
  '好胜、温柔但能打、爱比赛'),
 ('ernie', '文心一言 ERNIE', '国产',
  '百度千帆生态，中文语感好',
  'https://cloud.baidu.com/doc/qianfan/s/rmh4stp0j',
  '墨绿 #1F5C4A 与青花白，黑发束冠，中式立领长衫 + 卷轴袋',
  '手持毛笔与展开的中文卷轴',
  '斯文、讲究措辞、中文语感极佳'),
 ('baichuan', '百川 Baichuan', '国产',
  '医疗方向见长，新模型幻觉率低至 2.6%',
  'https://36kr.com/p/3650704809369728',
  '湖蓝 #2C7A9E 与米白，黑发束巾，白大褂 + 湖蓝内衬',
  '脖子上挂着写有「2.6%」的听诊器，另一只手拿病例夹',
  '严谨、较真、绝不说没把握的话'),
 ('spark', '讯飞星火', '国产',
  '语音与中文见长，Spark-X2.5-4B 等小尺寸 + API 矩阵',
  'https://www.xfyun.cn/site/1610.html',
  '科技蓝 #1560BD 与白，黑发戴头戴耳机，蓝白运动服',
  '头戴耳机 + 手持录音笔，说着话就把活干了',
  '耳朵灵、听说都强、边聊边做'),
 ('yi', '零一万物 Yi', '国产',
  '务实转型，收起超大模型、转向应用与落地',
  'https://www.c114.net.cn/industry/53393.html',
  '石板灰 #5A6B7C 与天青 #7FC8E8，灰色短发，灰蓝工装 + 工具腰带',
  '把一只写着「超大」的大箱子合上放一边，手里拿着趁手的小工具',
  '务实、果断、该收就收'),
 ('ollama', 'Ollama（本地）', '本地',
  '本地大模型工具爆火，用户破 900 万，零依赖私有部署',
  'https://news.qiniu.com/archives/1783932835347',
  '灰白 #E6E6E6 与可可色，灰白乱发，灰白连帽衫 + 围裙',
  '脚边一台小机柜 + 怀里一只小羊驼玩偶（离线也能干活）',
  '佛系、可靠、断网也在岗'),
 ('gemini', 'Google Gemini', '国外',
  '上下文极长（百万级 token），适合整仓库投喂',
  'https://deepmind.google/technologies/gemini/',
  '蓝紫渐变 #4285F4 → #9B72CB，银蓝短发，渐变风衣',
  '手持望远镜与一张铺开的星图',
  '看得最远、视野最广'),
 ('grok', 'xAI Grok', '国外',
  '实时信息与直率风格，国内不可直连',
  'https://x.ai/',
  '哑黑 #1A1A1A 与金 #E0B84C，黑发挑染金，黑色皮夹克 + 铆钉',
  '手指顶着一枚小火箭模型，另一手刷着实时信息流',
  '叛逆、直率、消息最灵通'),
 ('mistral', 'Mistral AI', '国外',
  '欧洲开源派，轻量高效（名字来自西北风）',
  'https://mistral.ai/',
  '蓝白红三色 #2B4C8C / #FFFFFF / #C8102E，亚麻色中长发，风衣 + 贝雷帽',
  '身边卷着一阵风，衣角被吹起',
  '轻盈、干脆、快得没影'),
 ('llama', 'Meta Llama', '国外',
  '开源权重代表，可完全本地部署',
  'https://www.llama.com/',
  '棕金 #8A5A2B 与米白，栗色卷发，棕金厚毛衣 + 背带裤',
  '身边一台自己装好的机柜，手里抱着开源权重硬盘',
  '憨厚、力气大、自己家就能跑'),
]

L = []
L.append('# 逐模型出图提示词（**只做我们还没有的 16 个**）\n')
L.append('> 依据：网上对每个模型的**真实评价与特色**（每条都附可点开的来源），不是我编的人设。')
L.append('> 已有的 3 个（DeepSeek / Claude / OpenAI GPT）不再出提示词。\n')
L.append('> 出图后另存为 `<id>.sheet.png`（504×324）与 `<id>.portrait.png`（144×216），'
         '丢进 `assets/chars/`，再跑 `python art\\check_assets.py` 自检。\n')
L.append('> 硬性规格与禁止项见 `assets/ART-SPEC.md`。\n')
L.append('---\n')

for (mid, name, region, trait, src, look, prop, vibe) in M:
    L.append('## %s（`%s`）　%s\n' % (name, mid, region))
    L.append('**真实特色**：%s　｜　依据：[%s](%s)\n' % (trait, src.split('/')[2], src))
    L.append('**视觉设定**：%s ｜ 道具：%s ｜ 气质：%s\n' % (look, prop, vibe))
    L.append('**文件名**：`%s.sheet.png` + `%s.portrait.png`\n' % (mid, mid))
    L.append('```')
    L.append('请画一张透明背景的 Q 版像素风角色图集：角色代表「%s」这个 AI 模型。' % name)
    L.append('它的特点是：%s。' % trait)
    L.append('外形：%s；%s；气质%s。' % (look, prop, vibe))
    L.append(SHARED_CN)
    L.append('```\n')
    L.append('---\n')

L.append('## 自定义模型（你自己上传的图）\n')
L.append('```powershell')
L.append('python tools\\add_custom_agent.py --image D:\\我的图.png --name "我的模型" --key mymodel --model glm --install')
L.append('```\n')
L.append('## 来源汇总\n')
for (mid, name, region, trait, src, *_rest) in M:
    L.append('- **%s**：%s —— %s' % (name, trait, src))

io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
print('  已生成 %s：%d 个模型（只含我们还没接入的）｜ %d 行' % (OUT, len(M), len(L)))
print('  已跳过：DeepSeek / Claude / OpenAI GPT（我们已有）')
