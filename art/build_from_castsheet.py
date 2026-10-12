# -*- coding: utf-8 -*-
"""用用户给的「多角色精灵表」重建全部角色的 36×64 帧表 + 头像。

表结构：8 行（员工）× 15 列（动作）。每行的列 0=正面、1=侧面、2=背面，工作姿态列各不相同。
"""
import os
from collections import deque
from PIL import Image

OUT = r'D:\徐\MunderDifflin\custom-cast'
SRC = os.path.join(OUT, '_source', 'cast-sheet.png')
PACK = os.path.join(OUT, 'pack')
CELLS = os.path.join(OUT, '_source', 'cast-cells2')
os.makedirs(CELLS, exist_ok=True)
os.makedirs(PACK, exist_ok=True)

X0, COLS, ROWS = 100, 15, 8
CELL_W, CELL_H = 64, 96
PORT_W, PORT_H = 128, 192

# 行索引 → (cast 名, 员工, 工作姿态列)
ROWMAP = [
    (0, 'stanley', 'WorkBuddy', 5),
    (1, None,      'Claude',    5),      # 办公室没有 Claude，跳过
    (2, 'kevin',   'Codex',     4),
    (3, 'jim',     'DeepSeek Harness', 8),
    (4, 'dwight',  '天枢·执行星域', 5),
    (5, 'angela',  '天枢·审批星域', 4),
    (6, 'oscar',   '天枢·纠错星域', 9),
    (7, 'michael', '月桥',      8),
]
COL_FRONT, COL_SIDE, COL_BACK = 0, 1, 2


def cell_of(im, row, col):
    W, H = im.size
    cw = (W - X0) / COLS
    ch = H / ROWS
    x0 = int(round(X0 + col * cw))
    x1 = int(round(X0 + (col + 1) * cw))
    y0 = int(round(row * ch))
    y1 = int(round((row + 1) * ch))
    return im.crop((x0, y0, x1, y1))


def clean(im, speck=40, open_r=1):
    """抠棋盘格底 + 去孤立噪点 + 轻度开运算（消掉背景碎点）。"""
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()

    def bg_like(c):
        return min(c[0], c[1], c[2]) >= 218 and max(c[:3]) - min(c[:3]) <= 14

    # 1) 从四边洪水填充背景
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

    # 2) 去孤立小连通块
    opaque = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 0:
                opaque[y * w + x] = 1
    seen2 = bytearray(w * h)
    for s in range(w * h):
        if not opaque[s] or seen2[s]:
            continue
        comp = []
        q = deque([s]); seen2[s] = 1
        while q:
            i = q.popleft(); comp.append(i)
            x, y = i % w, i // w
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    j = ny * w + nx
                    if opaque[j] and not seen2[j]:
                        seen2[j] = 1; q.append(j)
        if len(comp) < speck:
            for i in comp:
                px[i % w, i // w] = (px[i % w, i // w][0], px[i % w, i // w][1], px[i % w, i // w][2], 0)

    # 3) 轻度腐蚀（r=1）：把残留的 1px 边噪吃掉
    if open_r:
        for _ in range(open_r):
            a = im.getchannel('A').load()
            for y in range(h):
                for x in range(w):
                    if a[x, y] == 0:
                        continue
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and a[nx, ny] == 0:
                            r, g, b, _ = px[x, y]
                            px[x, y] = (r, g, b, 0)
                            break

    bb = im.getbbox()
    return im.crop(bb) if bb else im


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
            c = clean(cell_of(sheet, row, col))
            if tag == 'side':
                # 表里的侧面朝左；引擎会把「右向行」水平翻转给向左走，
                # 所以这里先镜像成朝右，左右走就都对了
                c = c.transpose(Image.FLIP_LEFT_RIGHT)
            c.save(os.path.join(CELLS, '%s-%s.png' % (cast, tag)))
            cells[tag] = scale_into(c, CELL_W, CELL_H)

        def frames(base, wv):
            return [base, leg_shift(bob(base, -1), -1), leg_shift(bob(base, -1), 1),
                    wv, bob(wv, -1), base, bob(base, -1)]

        s = Image.new('RGBA', (CELL_W * 7, CELL_H * 3), (0, 0, 0, 0))
        for r, (base, wv) in enumerate([(cells['front'], cells['work']),
                                        (cells['back'], cells['work']),
                                        (cells['side'], cells['work'])]):
            for c, fr in enumerate(frames(base, wv)):
                s.alpha_composite(fr, (c * CELL_W, r * CELL_H))
        s.save(os.path.join(PACK, '%s.sheet.png' % cast))

        # 头像 = 正面格放大
        front = cells['front']
        bb = front.getbbox() or (0, 0, CELL_W, CELL_H)
        f2 = front.crop(bb)
        w, h = f2.size
        sc = min(PORT_W / w, (PORT_H - 2) / h)
        nw, nh = max(1, round(w * sc)), max(1, round(h * sc))
        port = Image.new('RGBA', (PORT_W, PORT_H), (0, 0, 0, 0))
        port.alpha_composite(f2.resize((nw, nh), Image.NEAREST), ((PORT_W - nw) // 2, PORT_H - nh - 1))
        port.save(os.path.join(PACK, '%s.portrait.png' % cast))
        tiles[cast] = s
        print('  %-9s %-18s 帧表 OK  正面格 %s' % (cast, who, cells['front'].size))

    names = list(tiles)
    W, H = 252 * 3, 192 * 3
    canvas = Image.new('RGBA', (W * 2, H * ((len(names) + 1) // 2)), (26, 26, 34, 255))
    for i, n in enumerate(names):
        canvas.alpha_composite(tiles[n].resize((W, H), Image.NEAREST), ((i % 2) * W, (i // 2) * H))
    p = os.path.join(OUT, 'pack-preview-new.png')
    canvas.save(p)
    print('  预览 ->', p, canvas.size)


if __name__ == '__main__':
    main()
