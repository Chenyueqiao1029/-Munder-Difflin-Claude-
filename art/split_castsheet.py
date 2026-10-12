# -*- coding: utf-8 -*-
"""按网格切开精灵表，抠掉棋盘格背景，输出每格 PNG + 带列号的行strip（便于挑动作）。"""
import os
from collections import deque
from PIL import Image, ImageDraw

OUT = r'D:\徐\MunderDifflin\custom-cast'
SRC = os.path.join(OUT, '_source', 'cast-sheet.png')
CELLS = os.path.join(OUT, '_source', 'cast-cells')
os.makedirs(CELLS, exist_ok=True)

X0, COLS, ROWS = 100, 15, 8
NAMES = ['workbuddy', 'claude', 'codex', 'dsh', 'exec', 'approve', 'fix', 'yueqiao']


def strip_bg(im):
    """抠棋盘格底：从四边洪水填充「浅灰/白」像素，再填洞（保留深描边内部）。"""
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()

    def bg_like(c):
        r, g, b = c[0], c[1], c[2]
        return min(r, g, b) >= 218 and max(r, g, b) - min(r, g, b) <= 12

    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        i = y * w + x
        if seen[i]:
            continue
        seen[i] = 1
        if not bg_like(px[x, y]):
            continue
        r, g, b, _ = px[x, y]
        px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    # 填洞：从四边在「不透明」区域外洪水，没淹到的即内部
    opaque = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 0:
                opaque[y * w + x] = 1
    outside = bytearray(w * h)
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h:
            continue
        i = y * w + x
        if outside[i] or opaque[i]:
            continue
        outside[i] = 1
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    # 内部空洞（原本透明但被角色包围）填回：用邻近像素近似 → 直接给个浅色
    # 这里不做颜色推断，只把 alpha 打开，颜色沿用最近的可见像素不易；因此跳过填色，
    # 只保证外形连续（锯齿空洞很小，缩到 36×64 基本不可见）。
    return im


def main():
    im = Image.open(SRC).convert('RGBA')
    W, H = im.size
    cw = (W - X0) / COLS
    ch = H / ROWS
    strips = []
    for r in range(ROWS):
        row_imgs = []
        for c in range(COLS):
            x0 = int(round(X0 + c * cw))
            x1 = int(round(X0 + (c + 1) * cw))
            y0 = int(round(r * ch))
            y1 = int(round((r + 1) * ch))
            cell = im.crop((x0, y0, x1, y1))
            cell = strip_bg(cell)
            bb = cell.getbbox()
            if bb:
                cell = cell.crop(bb)
            cell.save(os.path.join(CELLS, '%s-%02d.png' % (NAMES[r], c)))
            row_imgs.append(cell)
        # 行 strip（每格等高缩放 + 标列号）
        Hh = 150
        tiles = []
        for i, cimg in enumerate(row_imgs):
            if cimg.size[1] == 0:
                continue
            w = max(1, int(cimg.size[0] * Hh / cimg.size[1]))
            tiles.append((i, cimg.resize((w, Hh), Image.NEAREST)))
        Wt = sum(t[1].size[0] + 8 for t in tiles) + 60
        strip = Image.new('RGBA', (Wt, Hh + 26), (30, 30, 38, 255))
        d = ImageDraw.Draw(strip)
        x = 60
        for i, t in tiles:
            strip.alpha_composite(t, (x, 22))
            d.text((x + 2, 4), '%d' % i, fill=(255, 220, 120, 255))
            x += t.size[0] + 8
        d.text((4, 60), NAMES[r][:10], fill=(160, 200, 255, 255))
        strips.append(strip)

    total_h = sum(s.size[1] + 6 for s in strips)
    Wt = max(s.size[0] for s in strips)
    sheet = Image.new('RGBA', (Wt, total_h), (20, 20, 26, 255))
    y = 0
    for s in strips:
        sheet.alpha_composite(s, (0, y))
        y += s.size[1] + 6
    p = os.path.join(OUT, 'cast-strips.png')
    sheet.save(p)
    print('  行 strip 总览 ->', p, sheet.size)
    print('  单格目录 ->', CELLS)


if __name__ == '__main__':
    main()
