# -*- coding: utf-8 -*-
"""把 16 段出图提示词合成【一份纯文本】，并附各平台 API 申请清单。
   数据来源：assets/PROMPTS.md（提示词原文）+ models/registry.json + models/brand-colors.json
   产物：assets/生图提示词-16模型.txt
"""
import io
import json
import os
import re

R = r'D:\徐\星域蜂巢'
MD = os.path.join(R, 'assets', 'PROMPTS.md')
OUT = os.path.join(R, 'assets', '生图提示词-16模型.txt')
reg = json.load(io.open(os.path.join(R, 'models', 'registry.json'), encoding='utf-8'))
brand = json.load(io.open(os.path.join(R, 'models', 'brand-colors.json'), encoding='utf-8'))['data']
md = io.open(MD, encoding='utf-8').read()

# 抽出每段：## 名称（`id`） ... 紧跟的 ``` 代码块
blocks = []
for sec in md.split('\n## ')[1:]:
    head = sec.split('\n', 1)[0]
    mid_m = re.search(r'`([^`]+)`', head)          # 小节标题里第一个反引号内容 = id
    pr_m = re.search(r'```\n(.*?)```', sec, re.S)  # 该小节第一个代码块 = 提示词
    if not (mid_m and pr_m):
        continue
    mid = mid_m.group(1).strip()
    name = re.sub(r'（`[^`]+`）', '', head).replace('**', '').strip()
    name = re.sub(r'\s+', ' ', name)
    blocks.append((mid, name, '', pr_m.group(1).strip()))

L = []
L.append('=' * 78)
L.append('星域蜂巢 · 16 个模型的出图提示词（一份就够）')
L.append('=' * 78)
L.append('')
L.append('【怎么用 · 3 步】')
L.append('  1) 复制下面任意一段完整提示词，粘进生图 AI（一次一段，不要合并）')
L.append('  2) 出图后另存为：   <id>.sheet.png   （必须正好 504x324 像素；7 列 x 3 行，每格 72x108）')
L.append('                      <id>.portrait.png（必须正好 144x216 像素）')
L.append('  3) 两个文件都丢进  D:\\徐\\星域蜂巢\\assets\\chars\\  →  跑  python art\\check_assets.py 自检')
L.append('')
L.append('【铁律（出图 AI 最容易做错的三点）】')
L.append('  · 尺寸：504x324 与 144x216，不能是 1024x1024 之类；格子必须对齐')
L.append('  · 背景：纯透明。不要白底、不要地面阴影')
L.append('  · 行序：第1行正面 / 第2行背面 / 第3行侧面朝右；每行前4帧走路、后3帧站立·工作·阅读')
L.append('  · 每个角色身上必须带自己的品牌标识（发夹/徽章/袖标/道具小标记），21 帧位置一致')
L.append('')
L.append('=' * 78)
L.append('')

for i, (mid, name, body, prompt) in enumerate(blocks, 1):
    b = brand.get(mid, {})
    pal = ' + '.join((b.get('palette') or ['-'])[:3])
    L.append('-' * 78)
    L.append('%02d. %s   （文件名前缀：%s）' % (i, name, mid))
    L.append('    官方品牌色：%s      取色来源：%s' % (pal, b.get('from') or '-'))
    L.append('    保存为：%s.sheet.png（504x324） + %s.portrait.png（144x216）' % (mid, mid))
    L.append('-' * 78)
    L.append(prompt)
    L.append('')

L.append('=' * 78)
L.append('附：各平台 API 申请清单（要"接"模型时才用；出图不需要）')
L.append('=' * 78)
L.append('')
PLATFORM = {
    'glm': ('https://open.bigmodel.cn/', '手机号注册；GLM-4.7-Flash 有完全免费档'),
    'kimi': ('https://platform.moonshot.cn/', '手机号注册；有免费额度'),
    'qwen': ('https://bailian.console.aliyun.com/', '支付宝/阿里云账号；有免费额度'),
    'doubao': ('https://console.volcengine.com/ark', '字节账号 + 实名；有免费额度'),
    'hunyuan': ('https://console.cloud.tencent.com/hunyuan', '腾讯云账号 + 实名；有免费额度'),
    'mimo': ('https://platform.mimo.mi.com/', '小米账号；活动期免费'),
    'minimax': ('https://platform.minimaxi.com/', '手机号注册；有免费额度'),
    'ernie': ('https://console.bce.baidu.com/qianfan/', '百度账号 + 实名；有免费额度'),
    'baichuan': ('https://platform.baichuan-ai.com/', '手机号注册；有免费额度'),
    'spark': ('https://console.xfyun.cn/', '讯飞账号 + 实名；有免费额度'),
    'yi': ('https://platform.lingyiwanwu.com/', '手机号注册；部分模型开源可本地'),
    'ollama': ('https://ollama.com/download', '不需要账号：本机装完即用，零成本'),
    'gemini': ('https://aistudio.google.com/apikey', 'Google 账号（国内需代理）；有免费额度'),
    'grok': ('https://console.x.ai/', 'X 账号 + 付费；国内不可直连'),
    'mistral': ('https://console.mistral.ai/', '邮箱注册；有免费额度'),
    'llama': ('https://www.llama.com/', '开源权重，可本地跑；或走云厂商托管'),
}
for mid, (url, note) in PLATFORM.items():
    L.append('  %-9s %-46s %s' % (mid, url, note))
L.append('')
L.append('  结论：注册几乎都要【手机号 + 实名/邮箱】，AI 不能代替人去申请；')
L.append('        但拿到 key 之后，接入与调用可以完全自动化（见 models/registry.json 的 how 字段）。')

io.open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
print('  已生成 %s' % OUT)
print('  提示词段数：%d ｜ 总行数：%d ｜ 大小：%.1f KB' % (len(blocks), len(L), os.path.getsize(OUT) / 1024))
