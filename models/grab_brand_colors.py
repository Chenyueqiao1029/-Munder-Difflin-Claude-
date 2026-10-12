# -*- coding: utf-8 -*-
"""抓每个模型官方站点/App 的真实品牌色（favicon 主色 + theme-color），
   作为出图配色的依据（不再靠我编）。只读，不写入任何第三方站点。
产物：models/brand-colors.json + 控制台表格
"""
import colorsys
import io
import json
import os
import re
import urllib.request
from collections import Counter

from PIL import Image

OUT = r'D:\徐\星域蜂巢\models\brand-colors.json'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'}

SITES = [
    ('deepseek', 'DeepSeek', ['https://chat.deepseek.com/', 'https://www.deepseek.com/']),
    ('glm', '智谱 GLM', ['https://chatglm.cn/', 'https://www.zhipuai.cn/']),
    ('kimi', 'Kimi', ['https://kimi.moonshot.cn/', 'https://www.moonshot.cn/']),
    ('qwen', '通义千问', ['https://tongyi.aliyun.com/', 'https://qwen.ai/']),
    ('doubao', '豆包', ['https://www.doubao.com/']),
    ('hunyuan', '腾讯混元', ['https://hunyuan.tencent.com/']),
    ('mimo', '小米 MiMo', ['https://mimo.mi.com/', 'https://www.mi.com/']),
    ('minimax', 'MiniMax', ['https://www.minimaxi.com/', 'https://hailuoai.com/']),
    ('ernie', '文心一言', ['https://yiyan.baidu.com/']),
    ('spark', '讯飞星火', ['https://xinghuo.xfyun.cn/']),
    ('yi', '零一万物', ['https://www.lingyiwanwu.com/']),
    ('ollama', 'Ollama', ['https://ollama.com/']),
    ('gemini', 'Google Gemini', ['https://gemini.google.com/']),
    ('grok', 'xAI Grok', ['https://x.ai/', 'https://grok.com/']),
    ('mistral', 'Mistral', ['https://mistral.ai/']),
    ('llama', 'Meta Llama', ['https://www.llama.com/']),
    ('claude', 'Anthropic Claude', ['https://claude.ai/', 'https://www.anthropic.com/']),
    ('openai', 'OpenAI', ['https://openai.com/']),
]


def fetch(url, binary=False, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read() if binary else r.read().decode('utf-8', 'replace')


def hexof(rgb):
    return '#%02X%02X%02X' % rgb


def dominant(img):
    """取主色：排除近白/近黑/透明，按出现次数排。"""
    img = img.convert('RGBA')
    img.thumbnail((64, 64))
    cnt = Counter()
    for r, g, b, a in img.getdata():
        if a < 120:
            continue
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if v > 0.96 and s < 0.12:      # 近白
            continue
        if v < 0.10:                   # 近黑
            continue
        if s < 0.10:                   # 灰
            continue
        cnt[(r // 16 * 16, g // 16 * 16, b // 16 * 16)] += 1
    return [hexof(c) for c, _n in cnt.most_common(4)]


result = {}
for mid, name, urls in SITES:
    entry = {'name': name, 'url': urls[0], 'theme': None, 'icon': None, 'palette': [], 'from': None}
    for u in urls:
        try:
            html = fetch(u)
            m = re.search(r'<meta[^>]+name=["\']theme-color["\'][^>]+content=["\']([^"\']+)', html, re.I)
            if m:
                entry['theme'] = m.group(1)
            icons = re.findall(r'<link[^>]+rel=["\'][^"\']*icon[^"\']*["\'][^>]*>', html, re.I)
            href = None
            for tag in icons:
                mm = re.search(r'href=["\']([^"\']+)', tag)
                if mm:
                    href = mm.group(1)
                    if 'svg' in href or 'png' in href:
                        break
            if href:
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = '/'.join(u.split('/')[:3]) + href
                elif not href.startswith('http'):
                    href = u.rstrip('/') + '/' + href
                entry['icon'] = href
                try:
                    data = fetch(href, binary=True)
                    im = Image.open(io.BytesIO(data))
                    pal = dominant(im)
                    if pal:
                        entry['palette'] = pal
                        entry['from'] = href
                        break
                except Exception as e:
                    entry['err'] = str(e)[:60]
            if entry['palette'] and entry['theme']:
                break
        except Exception as e:
            entry['err'] = str(e)[:60]
    result[mid] = entry
    pal = ', '.join(entry['palette']) or '(抓不到)'
    print('   %-9s %-14s theme=%-9s 主色: %s' % (mid, name, entry['theme'] or '-', pal))

io.open(OUT, 'w', encoding='utf-8', newline='\n').write(
    json.dumps({'_说明': '各模型官方站点/App 的真实品牌色：favicon 主色（按像素频次）+ theme-color。出图配色以此为准。',
                '抓取时间': '2026-10-12', 'data': result}, ensure_ascii=False, indent=2))
print('  → %s' % OUT)
