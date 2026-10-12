# -*- coding: utf-8 -*-
"""量新办公室地图里工位的家具尺寸：裁一个工位放大看，并给出像素测量参考线。"""
import os
from PIL import Image, ImageDraw

OUT = r'D:\徐\MunderDifflin\custom-cast'
SRC = os.path.join(OUT, '_source', 'office-neon.png')
im = Image.open(SRC).convert('RGB')
print('  地图', im.size)

# WorkBuddy 工位（按标签位置估算：标签 x≈180,y≈680；工位在它上方）
box = (60, 470, 340, 700)
crop = im.crop(box)
crop = crop.resize((crop.width * 3, crop.height * 3), Image.NEAREST)
d = ImageDraw.Draw(crop)
# 每 32px（=1 格）画一条参考线
for i in range(0, crop.width, 32 * 3):
    d.line([(i, 0), (i, crop.height)], fill=(255, 0, 0), width=1)
    d.text((i + 2, 2), str(i // (32 * 3)), fill=(255, 255, 0))
for j in range(0, crop.height, 32 * 3):
    d.line([(0, j), (crop.width, j)], fill=(0, 160, 255), width=1)
    d.text((2, j + 2), str(j // (32 * 3)), fill=(0, 255, 255))
p = os.path.join(OUT, 'furniture-measure.png')
crop.save(p)
print('  工位放大图（每格=32px=1 tile）->', p, crop.size)
