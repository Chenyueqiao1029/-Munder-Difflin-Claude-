# -*- coding: utf-8 -*-
"""头像统一从帧表前视图那一格放大（36×64 → 72×112，NEAREST），保证与游戏内一致、无抠图残留。"""
import os
from PIL import Image

PACK = r'D:\徐\MunderDifflin\custom-cast\pack'
CELL_W, CELL_H = 36, 64
PORT_W, PORT_H = 72, 112
NAMES = ['stanley', 'dwight', 'angela', 'oscar', 'jim', 'kevin', 'michael']

for n in NAMES:
    f = os.path.join(PACK, '%s.sheet.png' % n)
    if not os.path.exists(f):
        print('  %-9s 缺帧表' % n)
        continue
    im = Image.open(f).convert('RGBA')
    cell = im.crop((0, 0, CELL_W, CELL_H))          # 下/正面/站立
    # 裁到内容，再等比放进 72×112（底部对齐）
    bb = cell.getbbox()
    if bb:
        cell = cell.crop(bb)
    w, h = cell.size
    s = min(PORT_W / w, (PORT_H - 2) / h)
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    small = cell.resize((nw, nh), Image.NEAREST)
    canvas = Image.new('RGBA', (PORT_W, PORT_H), (0, 0, 0, 0))
    canvas.alpha_composite(small, ((PORT_W - nw) // 2, PORT_H - nh - 1))
    canvas.save(os.path.join(PACK, '%s.portrait.png' % n))
    print('  %-9s 头像重建 %s (来自 %s)' % (n, canvas.size, cell.size))

# 拼图核对
tiles = [(n, Image.open(os.path.join(PACK, '%s.portrait.png' % n))) for n in NAMES
         if os.path.exists(os.path.join(PACK, '%s.portrait.png' % n))]
W, H = PORT_W * 4, PORT_H * 4
canvas = Image.new('RGBA', (W * 4, H * 2), (28, 28, 36, 255))
for i, (n, im) in enumerate(tiles):
    canvas.alpha_composite(im.resize((W, H), Image.NEAREST), ((i % 4) * W, (i // 4) * H))
out = r'D:\徐\MunderDifflin\custom-cast\check-portraits.png'
canvas.save(out)
print('核对图 ->', out, canvas.size)
