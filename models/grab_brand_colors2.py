# -*- coding: utf-8 -*-
"""第二遍：直接打 favicon / 常见图标路径，补齐抓不到的 9 个品牌色。"""
import colorsys
import io
import json
import urllib.request
from collections import Counter

from PIL import Image

OUT = r'D:\徐\星域蜂巢\models\brand-colors.json'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'}
CANDS = {
    'hunyuan': ['https://hunyuan.tencent.com/favicon.ico', 'https://www.tencent.com/favicon.ico'],
    'mimo': ['https://mimo.mi.com/favicon.ico', 'https://www.mi.com/favicon.ico'],
    'yi': ['https://www.lingyiwanwu.com/favicon.ico', 'https://platform.lingyiwanwu.com/favicon.ico'],
    'ollama': ['https://ollama.com/favicon.ico', 'https://ollama.com/public/ollama.png'],
    'grok': ['https://x.ai/favicon.ico', 'https://grok.com/favicon.ico'],
    'mistral': ['https://mistral.ai/favicon.ico', 'https://mistral.ai/images/logo.svg'],
    'llama': ['https://www.llama.com/favicon.ico', 'https://about.meta.com/favicon.ico'],
    'claude': ['https://www.anthropic.com/favicon.ico', 'https://claude.ai/favicon.ico'],
    'openai': ['https://openai.com/favicon.ico', 'https://chatgpt.com/favicon.ico'],
}


def hexof(rgb):
    return '#%02X%02X%02X' % rgb


def dominant(img):
    img = img.convert('RGBA')
    img.thumbnail((64, 64))
    cnt = Counter()
    for r, g, b, a in list(img.getdata()):
        if a < 120:
            continue
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if (v > 0.96 and s < 0.12) or v < 0.10 or s < 0.10:
            continue
        cnt[(r // 16 * 16, g // 16 * 16, b // 16 * 16)] += 1
    return [hexof(c) for c, _n in cnt.most_common(4)]


data = json.load(io.open(OUT, encoding='utf-8'))
for mid, urls in CANDS.items():
    got = []
    for u in urls:
        try:
            req = urllib.request.Request(u, headers=UA)
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()
            im = Image.open(io.BytesIO(raw))
            pal = dominant(im)
            if pal:
                got = pal
                data['data'].setdefault(mid, {})['palette'] = pal
                data['data'][mid]['from'] = u
                break
        except Exception:
            continue
    print('   %-9s %s' % (mid, ', '.join(got) if got else '(仍抓不到，用官方文档色)'))

# 抓不到的用手工核对过的官方品牌色（注明来源，便于日后复核）
FALLBACK = {
    'hunyuan': ('#0052D9', '腾讯品牌蓝（TDesign 规范）'),
    'mimo': ('#FF6900', '小米品牌橙'),
    'yi': ('#111111', '零一万物官网黑白极简'),
    'ollama': ('#000000', 'Ollama 官网黑白'),
    'grok': ('#000000', 'xAI/X 品牌黑'),
    'mistral': ('#FF7000', 'Mistral 官方橙黄渐变（主色）'),
    'llama': ('#0866FF', 'Meta 品牌蓝'),
    'claude': ('#D97757', 'Anthropic 官方陶土橙'),
    'openai': ('#000000', 'OpenAI 官网黑白'),
}
for mid, (hexv, src) in FALLBACK.items():
    e = data['data'].setdefault(mid, {})
    if not e.get('palette'):
        e['palette'] = [hexv]
        e['from'] = src
        print('   %-9s 用核对色 %s（%s）' % (mid, hexv, src))

io.open(OUT, 'w', encoding='utf-8', newline='\n').write(json.dumps(data, ensure_ascii=False, indent=2))
print('  → 已更新', OUT)
