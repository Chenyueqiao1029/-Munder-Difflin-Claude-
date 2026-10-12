# -*- coding: utf-8 -*-
"""月桥专属形象 → 36×64 帧表 + 头像。

设定集布局（1536×1024）：
  主行  FRONT / SIDE / BACK / IDLE   y≈150..500, x≈20..880
  工作状态 4 格（制定规划/查看资料/远程协同/决策掌舵） y≈690..990, x≈20..1050
背景是中紫渐变、角色是深紫近黑 → 用「深色阈值 + 填洞」抠剪影。
"""
import os
from collections import deque
from PIL import Image

OUT = r'D:\徐\MunderDifflin\custom-cast'
SRC = os.path.join(OUT, '_source', 'moon.png')
VIEWS = os.path.join(OUT, '_source', 'moon-views')
os.makedirs(VIEWS, exist_ok=True)

CELL_W, CELL_H = 36, 64
PORT_W, PORT_H = 72, 112
COLS, ROWS = 7, 3
CAST = 'michael'

MAIN_BAND = (20, 880, 140, 500, 4)     # x0, x1, y0, y1, 视图数
WORK_BAND = (20, 1050, 690, 995, 4)


def dark_bbox(im, x0, x1, y0, y1, thr=95):
    px = im.load()
    W, H = im.size
    minx, miny, maxx, maxy = W, H, -1, -1
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            r, g, b = px[x, y][:3]
            if max(r, g, b) < thr:
                if x < minx: minx = x
                if y < miny: miny = y
                if x > maxx: maxx = x
                if y > maxy: maxy = y
    if maxx < 0:
        return None
    return (minx, miny, maxx + 1, maxy + 1)


def slice_band(im, band, names, pad=10):
    x0, x1, y0, y1, n = band
    step = (x1 - x0) / n
    outs = []
    for i in range(n):
        sx0, sx1 = int(round(x0 + i * step)), int(round(x0 + (i + 1) * step))
        bb = dark_bbox(im, sx0, sx1, y0, y1)
        if not bb:
            outs.append(None)
            continue
        box = (max(sx0, bb[0] - pad), max(0, bb[1] - pad), min(sx1, bb[2] + pad), min(im.size[1], bb[3] + pad))
        c = im.crop(box)
        f = os.path.join(VIEWS, '%s.png' % names[i])
        c.save(f)
        outs.append(c)
        print('    %-14s %s' % (names[i], c.size))
    return outs


def silhouette(im, thr=95, grow=2, min_size=500):
    """深色阈值 → 膨胀 → 最大连通块 → 填洞。"""
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()
    mask = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if max(r, g, b) < thr:
                mask[y * w + x] = 1
    if grow:
        g2 = bytearray(w * h)
        for y in range(h):
            for x in range(w):
                if not mask[y * w + x]:
                    continue
                for dy in range(-grow, grow + 1):
                    for dx in range(-grow, grow + 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            g2[ny * w + nx] = 1
        mask = g2
    seen = bytearray(w * h)
    best = []
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
        if len(comp) > len(best):
            best = comp
    solid = set(best)
    if len(solid) < min_size:
        return None
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
        if outside[i] or i in solid:
            continue
        outside[i] = 1
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    filled = set(solid)
    for i in range(w * h):
        if not outside[i]:
            filled.add(i)
    out = im.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            if (y * w + x) not in filled:
                r, g, b, _ = op[x, y]
                op[x, y] = (r, g, b, 0)
    bbox = out.getbbox()
    return out.crop(bbox) if bbox else out


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
    if not os.path.exists(SRC):
        raise SystemExit('缺少 %s' % SRC)
    im = Image.open(SRC).convert('RGBA')
    print('  设定集', im.size)
    print('  主行视图:')
    main_views = slice_band(im, MAIN_BAND, ['front', 'side', 'back', 'idle'])
    print('  工作状态:')
    work_views = slice_band(im, WORK_BAND, ['w0', 'w1', 'w2', 'w3'])
    if any(v is None for v in main_views[:3]):
        raise SystemExit('主行切片失败')

    front = scale_into(silhouette(main_views[0]), CELL_W, CELL_H)
    side = scale_into(silhouette(main_views[1]), CELL_W, CELL_H)
    back = scale_into(silhouette(main_views[2]), CELL_W, CELL_H)
    work_raw = main_views[3] if main_views[3] is not None else main_views[0]  # IDLE 坐姿当工作帧
    work = scale_into(silhouette(work_raw), CELL_W, CELL_H)

    sheet = Image.new('RGBA', (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))

    def frames(base, wv):
        return [base, leg_shift(bob(base, -1), -1), leg_shift(bob(base, -1), 1),
                wv, bob(wv, -1), base, bob(base, -1)]

    for r, (base, wv) in enumerate([(front, work), (back, work), (side, work)]):
        for c, fr in enumerate(frames(base, wv)):
            sheet.alpha_composite(fr, (c * CELL_W, r * CELL_H))
    sheet.save(os.path.join(OUT, 'pack', '%s.sheet.png' % CAST))
    scale_into(front, PORT_W, PORT_H).save(os.path.join(OUT, 'pack', '%s.portrait.png' % CAST))
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(os.path.join(OUT, 'check-moon.png'))
    print('  帧表 -> pack/%s.sheet.png %s' % (CAST, sheet.size))
    print('  检查图 -> check-moon.png')


if __name__ == '__main__':
    main()
