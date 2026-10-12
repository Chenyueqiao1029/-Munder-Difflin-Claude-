# -*- coding: utf-8 -*-
"""按「包围盒宽度」判定侧向是否太窄 → 太窄则整行改用正面视图。"""
import os
from PIL import Image

PACK = r'D:\徐\MunderDifflin\custom-cast\pack'
CELL_W, CELL_H = 36, 64
NAMES = ['stanley', 'dwight', 'angela', 'oscar', 'jim', 'kevin', 'michael']


def row_width(im, row):
    a = im.getchannel('A').crop((0, row * CELL_H, im.width, (row + 1) * CELL_H))
    bb = a.getbbox()
    return 0 if not bb else bb[2] - bb[0]


for n in NAMES:
    f = os.path.join(PACK, '%s.sheet.png' % n)
    if not os.path.exists(f):
        continue
    im = Image.open(f).convert('RGBA')
    w0, w1, w2 = row_width(im, 0), row_width(im, 1), row_width(im, 2)
    ratio = w2 / max(1, w0)
    if ratio < 0.72:
        front_row = im.crop((0, 0, im.width, CELL_H))
        im.paste(front_row, (0, 2 * CELL_H))
        im.save(f)
        print('  %-9s 侧宽 %d/%d = %.0f%% -> 改用正面视图' % (n, w2, w0, ratio * 100))
    else:
        print('  %-9s 侧宽 %d/%d = %.0f%% -> 保留侧视图' % (n, w2, w0, ratio * 100))
