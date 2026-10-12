# -*- coding: utf-8 -*-
"""按连通块精确裁剪 + 人物放大到 72×108。

裁剪逻辑：
  1) 抠掉棋盘格底（从边框洪水填充浅灰/白 + 去小噪点）
  2) 求不透明像素的连通块
  3) 只保留「与格子中央区域相交」或「面积够大且靠近中心」的块 —— 邻格混进来的
     另一半人物是独立连通块，且位于格子边缘，会被排除
  4) 按保留块的并集包围盒裁剪
"""
import os
from collections import deque
from PIL import Image

OUT = r'D:\徐\MunderDifflin\custom-cast'
SRC = os.path.join(OUT, '_source', 'cast-sheet.png')
PACK = os.path.join(OUT, 'pack')
CROP = os.path.join(OUT, '_source', 'cast-cells3')
os.makedirs(PACK, exist_ok=True)
os.makedirs(CROP, exist_ok=True)

X0, COLS, ROWS = 100, 15, 8
CELL_W, CELL_H = 72, 108
PORT_W, PORT_H = 144, 216

ROWMAP = [
    (0, 'stanley', 'WorkBuddy', 5),
    (1, None, 'Claude', 5),
    (2, 'kevin', 'Codex', 4),
    (3, 'jim', 'DeepSeek Harness', 8),
    (4, 'dwight', '天枢·执行星域', 5),
    (5, 'angela', '天枢·审批星域', 4),
    (6, 'oscar', '天枢·纠错星域', 9),
    (7, 'michael', '月桥', 8),
]
COL_FRONT, COL_SIDE, COL_BACK = 0, 1, 2


def raw_cell(im, row, col):
    W, H = im.size
    cw = (W - X0) / COLS
    ch = H / ROWS
    x0 = int(round(X0 + col * cw))
    x1 = int(round(X0 + (col + 1) * cw))
    y0 = int(round(row * ch))
    y1 = int(round((row + 1) * ch))
    return im.crop((x0, y0, x1, y1))


def components(mask, w, h):
    seen = bytearray(w * h)
    comps = []
    for s in range(w * h):
        if not mask[s] or seen[s]:
            continue
        comp = []
        q = deque([s]); seen[s] = 1
        while q:
            i = q.popleft(); comp.append(i)
            x, y = i % w, i // w
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    j = ny * w + nx
                    if mask[j] and not seen[j]:
                        seen[j] = 1; q.append(j)
        comps.append(comp)
    return comps


def cutout(im, min_frac=0.06):
    """抠底 + 只保留中央区域的连通块 + 按并集裁剪。"""
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()

    def bg_like(c):
        return min(c[0], c[1], c[2]) >= 216 and max(c[:3]) - min(c[:3]) <= 16

    # 1) 边框洪水填充抠底
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

    # 2) 连通块
    mask = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 0:
                mask[y * w + x] = 1
    comps = [c for c in components(mask, w, h) if len(c) >= 24]
    if not comps:
        bb = im.getbbox()
        return im.crop(bb) if bb else im
    comps.sort(key=len, reverse=True)
    biggest = len(comps[0])

    # 3) 中央区域（横向中间 60%、纵向中间 80%）
    cx0, cx1 = int(w * 0.20), int(w * 0.80)
    cy0, cy1 = int(h * 0.06), int(h * 0.98)

    keep = []
    for c in comps:
        xs = [i % w for i in c]
        ys = [i // w for i in c]
        bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
        cx = (bx0 + bx1) / 2
        cy = (by0 + by1) / 2
        touches_center = (cx0 <= cx <= cx1) and (cy0 <= cy <= cy1)
        big_enough = len(c) >= biggest * min_frac
        if touches_center and big_enough:
            keep.append((bx0, by0, bx1 + 1, by1 + 1))
    if not keep:
        xs = [i % w for i in comps[0]]
        ys = [i // w for i in comps[0]]
        keep = [(min(xs), min(ys), max(xs) + 1, max(ys) + 1)]

    x0 = min(k[0] for k in keep); y0 = min(k[1] for k in keep)
    x1 = max(k[2] for k in keep); y1 = max(k[3] for k in keep)
    out = im.crop((x0, y0, x1, y1))
    # 去掉并集内不属于保留块的碎片（邻格碎片如果在并集里也会被清掉）
    keepset = set()
    for c in comps:
        xs = [i % w for i in c]
        ys = [i // w for i in c]
        cx = (min(xs) + max(xs)) / 2
        cy = (min(ys) + max(ys)) / 2
        if (cx0 <= cx <= cx1) and (cy0 <= cy <= cy1) and len(c) >= biggest * min_frac:
            keepset.update(c)
    op = out.load()
    ow, oh = out.size
    for y in range(oh):
        for x in range(ow):
            gi = (y + y0) * w + (x + x0)
            if mask[gi] and gi not in keepset:
                r, g, b, _ = op[x, y]
                op[x, y] = (r, g, b, 0)
    bb = out.getbbox()
    return out.crop(bb) if bb else out


def scale_into(im, cw, ch, pad=1):
    w, h = im.size
    s = min((cw - pad * 2) / w, (ch - pad * 2) / h)
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    small = im.resize((nw, nh), Image.NEAREST)
    canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    canvas.alpha_composite(small, ((cw - nw) // 2, ch - nh - pad))
    return canvas


def leg_shift(cell, dx):
    w, h = cell.size
    y0 = int(h * 0.66)
    out = cell.copy()
    legs = cell.crop((0, y0, w, h))
    out.paste((0, 0, 0, 0), (0, y0, w, h))
    out.alpha_composite(legs, (dx, y0))
    if dx > 0:
        out.paste(legs.crop((0, 0, dx, h - y0)), (0, y0))
    else:
        out.paste(legs.crop((w + dx, 0, w, h - y0)), (w + dx, y0))
    return out


def bob(cell, dy):
    out = Image.new('RGBA', cell.size, (0, 0, 0, 0))
    out.alpha_composite(cell, (0, dy))
    return out


def main():
    sheet = Image.open(SRC).convert('RGBA')
    tiles = {}
    for row, cast, who, workcol in ROWMAP:
        if cast is None:
            continue
        cells = {}
        for tag, col in (('front', COL_FRONT), ('side', COL_SIDE), ('back', COL_BACK), ('work', workcol)):
            c = cutout(raw_cell(sheet, row, col if tag != 'work' else COL_FRONT))
            if tag == 'side':
                c = c.transpose(Image.FLIP_LEFT_RIGHT)   # 表里侧面朝左；引擎给左走做翻转
            c.save(os.path.join(CROP, '%s-%s.png' % (cast, tag)))
            cells[tag] = scale_into(c, CELL_W, CELL_H)

        def frames(base, wv):
            return [base, leg_shift(bob(base, -1), -1), leg_shift(bob(base, -1), 1),
                    wv, bob(wv, -1), base, bob(base, -1)]

        s = Image.new('RGBA', (CELL_W * 7, CELL_H * 3), (0, 0, 0, 0))
        for r, (base, wv) in enumerate([(cells['front'], cells['work']),
                                        (cells['back'], cells['work']),
                                        (cells['side'], cells['work'])]):
            for c2, fr in enumerate(frames(base, wv)):
                s.alpha_composite(fr, (c2 * CELL_W, r * CELL_H))
        s.save(os.path.join(PACK, '%s.sheet.png' % cast))

        f2 = cells['front']
        bb = f2.getbbox() or (0, 0, CELL_W, CELL_H)
        f2 = f2.crop(bb)
        w, h = f2.size
        sc = min(PORT_W / w, (PORT_H - 2) / h)
        nw, nh = max(1, round(w * sc)), max(1, round(h * sc))
        port = Image.new('RGBA', (PORT_W, PORT_H), (0, 0, 0, 0))
        port.alpha_composite(f2.resize((nw, nh), Image.NEAREST), ((PORT_W - nw) // 2, PORT_H - nh - 1))
        port.save(os.path.join(PACK, '%s.portrait.png' % cast))
        tiles[cast] = s
        print('  %-9s %-18s 帧表 %s' % (cast, who, s.size))

    names = list(tiles)
    W, H = (CELL_W * 7) * 2, CELL_H * 3 * 2
    cols2 = 2
    rows2 = (len(names) + cols2 - 1) // cols2
    canvas = Image.new('RGBA', (W * cols2, H * rows2), (26, 26, 34, 255))
    for i, n in enumerate(names):
        canvas.alpha_composite(tiles[n].resize((W, H), Image.NEAREST), ((i % cols2) * W, (i // cols2) * H))
    p = os.path.join(OUT, 'pack-preview-new.png')
    canvas.save(p)
    print('  预览 ->', p, canvas.size)


if __name__ == '__main__':
    main()
