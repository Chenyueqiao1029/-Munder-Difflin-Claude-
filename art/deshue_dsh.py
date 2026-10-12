# -*- coding: utf-8 -*-
"""DSH(jim) 去紫：整只转成黑/灰/白（保留 alpha），头像同步。"""
import os
from PIL import Image, ImageEnhance

PACK = r'D:\徐\MunderDifflin\custom-cast\pack'


def to_gray(path):
    im = Image.open(path).convert('RGBA')
    # 先稍微提对比，避免灰度后发闷
    r, g, b, a = im.split()
    rgb = Image.merge('RGB', (r, g, b))
    rgb = ImageEnhance.Contrast(rgb).enhance(1.15)
    gray = rgb.convert('L')
    out = Image.merge('RGBA', (gray, gray, gray, a))
    out.save(path)
    ex = out.convert('RGB').getextrema()
    return out.size, ex


for f in ('jim.sheet.png', 'jim.portrait.png'):
    p = os.path.join(PACK, f)
    if not os.path.exists(p):
        print('  缺', f)
        continue
    size, ex = to_gray(p)
    print('  %-18s -> 灰度 %s  RGB 范围 %s' % (f, size, ex))
