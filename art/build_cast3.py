# -*- coding: utf-8 -*-
"""按「每行内容分段」重建角色（适配间距很大的新贴纸表）。
   - 先检测 8 个行带
   - 每行带内按 x 投影切出每个角色（首段是左侧标签牌，跳过）
   - 复用 build_cast2 的连通块抠图，保证没有邻格混入
"""
import os
import sys
from collections import deque
from PIL import Image

sys.path.insert(0, r'D:\徐\MunderDifflin\custom-cast')
from build_cast2 import cutout, scale_into, bob, leg_shift, CELL_W, CELL_H, PORT_W, PORT_H

OUT = r'D:\徐\MunderDifflin\custom-cast'
SRC = os.path.join(OUT, '_source', 'cast-sheet.png')
PACK = os.path.join(OUT, 'pack')

ROWS = [
    (0, 'stanley', 'WorkBuddy'),
    (1, None, 'Claude'),
    (2, 'kevin', 'Codex'),
    (3, 'jim', 'DeepSeek Harness'),
    (4, 'dwight', '天枢·执行星域'),
    (5, 'angela', '天枢·审批星域'),
    (6, 'oscar', '天枢·纠错星域'),
    (7, 'michael', '月桥'),
]


def bands(vals, thr=2, minlen=20):
    segs, cur = [], None
    for i, v in enumerate(vals):
        if v > thr:
            cur = [i, i] if cur is None else [cur[0], i]
        elif cur is not None:
            if cur[1] - cur[0] >= minlen:
                segs.append(tuple(cur))
            cur = None
    if cur is not None and cur[1] - cur[0] >= minlen:
        segs.append(tuple(cur))
    return segs


def main():
    im = Image.open(SRC).convert('RGBA')
    w, h = im.size
    px = im.load()

    def ink(x, y):
        r, g, b, a = px[x, y]
        return a > 40 and not (r > 235 and g > 235 and b > 235)

    rowproj = [sum(1 for x in range(0, w, 4) if ink(x, y)) for y in range(h)]
    rbands = bands(rowproj, 2, 20)
    print('  行带:', len(rbands))

    for idx, (r0, r1) in enumerate(rbands):
        cast, who = None, None
        for r, c, wn in ROWS:
            if r == idx:
                cast, who = c, wn
        colproj = [sum(1 for y in range(r0, r1 + 1, 2) if ink(x, y)) for x in range(w)]
        csegs = bands(colproj, 1, 18)
        # 首段是左侧标签牌（x 8-94），排除它
        cells = [s for s in csegs if s[0] > 100]
        print('  行%d 角色段数=%d  首段=%s' % (idx, len(cells), cells[0] if cells else None))
        if cast is None or len(cells) < 3:
            continue
        front = im.crop((cells[0][0], r0, cells[0][1] + 1, r1 + 1))
        side = im.crop((cells[1][0], r0, cells[1][1] + 1, r1 + 1))
        back = im.crop((cells[2][0], r0, cells[2][1] + 1, r1 + 1))
        f = scale_into(cutout(front), CELL_W, CELL_H)
        sd = scale_into(cutout(side).transpose(Image.FLIP_LEFT_RIGHT), CELL_W, CELL_H)
        bk = scale_into(cutout(back), CELL_W, CELL_H)
        wk = f

        def frames(base, wv):
            return [base, leg_shift(bob(base, -1), -1), leg_shift(bob(base, -1), 1),
                    wv, bob(wv, -1), base, bob(base, -1)]

        s = Image.new('RGBA', (CELL_W * 7, CELL_H * 3), (0, 0, 0, 0))
        for r, base in enumerate([f, bk, sd]):
            for c2, fr in enumerate(frames(base, wk)):
                s.alpha_composite(fr, (c2 * CELL_W, r * CELL_H))
        s.save(os.path.join(PACK, '%s.sheet.png' % cast))

        bb = f.getbbox() or (0, 0, CELL_W, CELL_H)
        f2 = f.crop(bb)
        ww, hh = f2.size
        sc = min(PORT_W / ww, (PORT_H - 2) / hh)
        nw, nh = max(1, round(ww * sc)), max(1, round(hh * sc))
        port = Image.new('RGBA', (PORT_W, PORT_H), (0, 0, 0, 0))
        port.alpha_composite(f2.resize((nw, nh), Image.NEAREST), ((PORT_W - nw) // 2, PORT_H - nh - 1))
        port.save(os.path.join(PACK, '%s.portrait.png' % cast))
        print('    %-9s %-18s OK' % (cast, who))

    # 预览
    names = [c for _r, c, _w in ROWS if c]
    tiles = [Image.open(os.path.join(PACK, '%s.sheet.png' % n)) for n in names]
    W, H = CELL_W * 7, CELL_H * 3
    canvas = Image.new('RGBA', (W * 2, H * 4), (26, 26, 34, 255))
    for i, t in enumerate(tiles):
        canvas.alpha_composite(t, ((i % 2) * W, (i // 2) * H))
    p = os.path.join(OUT, 'pack-preview-new.png')
    canvas.save(p)
    print('  预览 ->', p, canvas.size)


if __name__ == '__main__':
    main()
