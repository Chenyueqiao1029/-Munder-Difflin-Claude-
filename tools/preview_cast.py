# -*- coding: utf-8 -*-
"""把某目录里的角色拼成一张预览接触表（用于肉眼验收抠图与缩放质量）。
用法：python tools/preview_cast.py [目录，默认 build/assets] [输出，默认 build/preview-cast.png]
"""
import io
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, 'build', 'assets')
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, 'build', 'preview-cast.png')

files = sorted(f for f in os.listdir(src) if f.endswith('.sheet.png'))
if not files:
    print('  没有 sheet')
    raise SystemExit(1)

cw, ch = 72, 108
scale = 1.5
tw, th = int(cw * scale), int(ch * scale)
cols = 6
rows = (len(files) + cols - 1) // cols
pad = 20
sheet = Image.new('RGBA', (cols * (tw + 8), rows * (th + pad + 8)), (26, 26, 34, 255))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(os.path.join(src, f)).convert('RGBA')
    # 取每行的第 1 帧（正面）拼成"角色总览"
    x = (i % cols) * (tw + 8) + 4
    y = (i // cols) * (th + pad + 8) + 4
    front = im.crop((0, 0, cw, ch))
    back = im.crop((0, ch, cw, 2 * ch))
    side = im.crop((0, 2 * ch, cw, 3 * ch))
    for j, cell in enumerate([front, back, side]):
        sheet.alpha_composite(cell.resize((int(tw / 3), th), Image.NEAREST),
                              (x + j * int(tw / 3), y))
    d.text((x, y + th + 3), f.replace('.sheet.png', ''), fill=(230, 230, 240, 255))
sheet.save(out)
print('  %d 个角色 → %s  (%dx%d)' % (len(files), out, sheet.size[0], sheet.size[1]))
