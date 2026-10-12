# -*- coding: utf-8 -*-
"""用「深色描边 + 膨胀闭合 + 填洞」从图二的白紫款重建 Codex(kevin)。"""
import os
from collections import deque
from PIL import Image

OUT = r'D:\徐\MunderDifflin\custom-cast'
CROP = os.path.join(OUT, '_source', 'views')
PACK = os.path.join(OUT, 'pack')
CELL_W, CELL_H = 36, 64
PORT_W, PORT_H = 72, 112
COLS, ROWS = 7, 3
CAST = 'kevin'


def silhouette(im, tol=28, min_size=400):
    """白紫款专用：边缘取底色 → 剔除容差内像素 → 最大连通块 → 填洞。
    （它白裙贴浅紫底，用亮度阈值会咬碎裙子；容差 28 是扫描出来的最佳值。）"""
    from collections import Counter
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()
    cnt = Counter()
    for x in range(w):
        for d in range(4):
            cnt[px[x, d][:3]] += 1
            cnt[px[x, h - 1 - d][:3]] += 1
    for y in range(h):
        for d in range(4):
            cnt[px[d, y][:3]] += 1
            cnt[px[w - 1 - d, y][:3]] += 1
    bg = cnt.most_common(1)[0][0]

    mask = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            c = px[x, y][:3]
            if abs(c[0] - bg[0]) + abs(c[1] - bg[1]) + abs(c[2] - bg[2]) > tol:
                mask[y * w + x] = 1

    # 清掉底部标签带（FRONT/SIDE/BACK 字样）与顶部留白，免得被闭运算连进剪影
    for y in range(max(0, h - 52), h):
        base = y * w
        for x in range(w):
            mask[base + x] = 0
    for y in range(0, min(6, h)):
        base = y * w
        for x in range(w):
            mask[base + x] = 0

    # 先清掉孤立小色块（面板上的星星装饰），避免闭运算把它们连进剪影
    seen0 = bytearray(w * h)
    for s0 in range(w * h):
        if not mask[s0] or seen0[s0]:
            continue
        comp = []
        q0 = deque([s0]); seen0[s0] = 1
        while q0:
            i = q0.popleft(); comp.append(i)
            x, y = i % w, i // w
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    j = ny * w + nx
                    if mask[j] and not seen0[j]:
                        seen0[j] = 1; q0.append(j)
        if len(comp) < 80:
            for i in comp:
                mask[i] = 0

    # 形态学闭运算（膨胀 r 再腐蚀 r）：封住白裙上"接近底色"的细缝，避免抠出透明洞
    def dilate(m, r):
        out = bytearray(w * h)
        for y in range(h):
            for x in range(w):
                if not m[y * w + x]:
                    continue
                for dy in range(-r, r + 1):
                    ny = y + dy
                    if ny < 0 or ny >= h:
                        continue
                    base = ny * w
                    for dx in range(-r, r + 1):
                        nx = x + dx
                        if 0 <= nx < w:
                            out[base + nx] = 1
        return out

    def erode(m, r):
        out = bytearray(w * h)
        for y in range(h):
            for x in range(w):
                if not m[y * w + x]:
                    continue
                ok = True
                for dy in range(-r, r + 1):
                    ny = y + dy
                    if ny < 0 or ny >= h:
                        ok = False
                        break
                    base = ny * w
                    for dx in range(-r, r + 1):
                        nx = x + dx
                        if nx < 0 or nx >= w or not m[base + nx]:
                            ok = False
                            break
                    if not ok:
                        break
                if ok:
                    out[y * w + x] = 1
        return out

    mask = erode(dilate(mask, 6), 6)
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
    bb = out.getbbox()
    # 按「最大连通块」的包围盒裁剪：底部的 FRONT/SIDE 标签是另一个独立块，会被排除
    xs = [i % w for i in solid]
    ys = [i // w for i in solid]
    cb = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
    return out.crop(cb) if bb else out


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


def load(view):
    p = os.path.join(CROP, view + '.png')
    im = Image.open(p).convert('RGBA')
    w, h = im.size
    if h > 70:
        im = im.crop((0, 0, w, h - 46))
    return im


def main():
    front = scale_into(silhouette(load('whitepurple-0')), CELL_W, CELL_H)
    side = scale_into(silhouette(load('whitepurple-1')), CELL_W, CELL_H)
    back = scale_into(silhouette(load('whitepurple-2')), CELL_W, CELL_H)
    work = front

    sheet = Image.new('RGBA', (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))

    def frames(base, wv):
        return [base, leg_shift(bob(base, -1), -1), leg_shift(bob(base, -1), 1),
                wv, bob(wv, -1), base, bob(base, -1)]

    for r, (base, wv) in enumerate([(front, work), (back, work), (side, work)]):
        for c, fr in enumerate(frames(base, wv)):
            sheet.alpha_composite(fr, (c * CELL_W, r * CELL_H))
    sheet.save(os.path.join(PACK, '%s.sheet.png' % CAST))
    scale_into(front, PORT_W, PORT_H).save(os.path.join(PACK, '%s.portrait.png' % CAST))
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(os.path.join(OUT, 'check-kevin2.png'))
    print('  kevin 帧表已重建:', sheet.size)


if __name__ == '__main__':
    main()
