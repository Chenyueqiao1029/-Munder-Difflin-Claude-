# -*- coding: utf-8 -*-
"""重做通行区：按「整格是否平坦均匀（像地板）」判定，而不是亮度。

- 地板/走廊/工位垫子：颜色均匀 → 可走
- 桌子/椅子/显示器/装饰：明暗杂（高方差）→ 阻挡
再做形态学清理 + 只保留与主走廊连通的部分，避免"上桌子"和"悬空"。
"""
import json
import os
from collections import Counter, deque
from PIL import Image, ImageDraw

OUT = r'D:\徐\MunderDifflin\custom-cast'
SRC = os.path.join(OUT, '_source', 'office-neon.png')
PACK = os.path.join(OUT, 'pack')
TS = 32
IMAGE = 'office-new.png'

# 主走廊上的一个种子格（确保是地板）：地图中心偏下的横向走道
SEED = (24, 13)


def main():
    im = Image.open(SRC).convert('RGB')
    W, H = im.size
    cols, rows = W // TS, H // TS
    px = im.load()

    def tile_stats(tx, ty):
        vals = []
        rs = gs = bs = 0
        n = 0
        for yy in range(ty * TS + 3, ty * TS + TS - 3, 2):
            for xx in range(tx * TS + 3, tx * TS + TS - 3, 2):
                r, g, b = px[xx, yy]
                rs += r; gs += g; bs += b; n += 1
                vals.append(0.299 * r + 0.587 * g + 0.114 * b)
        if not n:
            return 0, 0, (0, 0, 0)
        mean = sum(vals) / n
        var = sum((v - mean) ** 2 for v in vals) / n
        return mean, var ** 0.5, (rs // n, gs // n, bs // n)

    stats = {}
    for ty in range(rows):
        for tx in range(cols):
            stats[(tx, ty)] = tile_stats(tx, ty)

    UNIFORM = float(os.environ.get('MAP_UNIFORM', '20'))
    MINLUM = float(os.environ.get('MAP_MINLUM', '28'))

    cand = {}
    for (tx, ty), (mean, sd, _c) in stats.items():
        inside = 1 <= tx < cols - 1 and 1 <= ty < rows - 1
        cand[(tx, ty)] = inside and sd <= UNIFORM and mean >= MINLUM

    # 形态学：去掉孤立可走格（周围 8 格大多不可走）
    for _ in range(2):
        new = dict(cand)
        for (tx, ty), v in cand.items():
            if not v:
                continue
            nb = [cand.get((tx + dx, ty + dy), False) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                  if not (dx == 0 and dy == 0)]
            if sum(nb) < 3:
                new[(tx, ty)] = False
        cand = new

    # 只保留与种子连通的区域
    if not cand.get(SEED):
        # 种子不可走时，就近找一个可走格
        best = None
        for (tx, ty), v in cand.items():
            if not v:
                continue
            d = abs(tx - SEED[0]) + abs(ty - SEED[1])
            if best is None or d < best[0]:
                best = (d, (tx, ty))
        if best:
            print('  种子 %s 不可走，改用 %s' % (SEED, best[1]))
            seed = best[1]
        else:
            raise SystemExit('没有任何可走格')
    else:
        seed = SEED
    seen = set([seed])
    q = deque([seed])
    while q:
        tx, ty = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (tx + dx, ty + dy)
            if n in cand and cand[n] and n not in seen:
                seen.add(n)
                q.append(n)
    walk = seen
    print('  可走格 %d / %d (%.0f%%)  种子 %s' % (len(walk), cols * rows, 100 * len(walk) / (cols * rows), seed))

    floor_data = [(ty * cols + tx + 1) for ty in range(rows) for tx in range(cols)]
    coll_data = [0 if (tx, ty) in walk else 1 for ty in range(rows) for tx in range(cols)]

    seats = {
        'entrance': (760, 968),          # 底部中间的门口（等待点围绕它生成）
        'desk-ceo': (240, 262),
        'desk-workbuddy': (215, 604),
        'desk-claude': (455, 604),
        'desk-codex': (730, 604),
        'desk-dsh': (1000, 604),
        'desk-exec': (245, 852),
        'desk-approve': (630, 852),
        'desk-fix': (1015, 852),
        'cafe-stand-coffee': (1275, 300),
        'cafe-stand-vending': (1490, 300),
        'cafe-seat-1': (1285, 262),
        'cafe-seat-2': (1395, 262),
        'meeting-1': (735, 265),
        'meeting-2': (885, 265),
    }
    # 座位坐标是按 1536x1024 标注的；按当前图尺寸等比换算
    SX = W / 1536.0
    SY = H / 1024.0
    seats = {k: (int(x * SX), int(y * SY)) for k, (x, y) in seats.items()}

    objects, oid = [], 1
    for name, (x, y) in seats.items():
        tx, ty = x // TS, y // TS
        objects.append({'id': oid, 'name': name, 'type': '', 'shape': 'point', 'point': True,
                        'x': tx * TS + TS // 2, 'y': ty * TS + TS // 2, 'width': 0, 'height': 0,
                        'rotation': 0, 'visible': True})
        oid += 1
    zones = [
        {'id': oid, 'name': 'boardroom', 'type': '', 'shape': 'rectangle',
         'x': 37 * TS, 'y': 3 * TS, 'width': 15 * TS, 'height': 9 * TS, 'rotation': 0, 'visible': True},
        {'id': oid + 1, 'name': 'cafeteria', 'type': '', 'shape': 'rectangle',
         'x': 37 * TS, 'y': 3 * TS, 'width': 11 * TS, 'height': 9 * TS, 'rotation': 0, 'visible': True},
    ]

    def tl(name, data, lid):
        return {'id': lid, 'name': name, 'type': 'tilelayer', 'x': 0, 'y': 0, 'width': cols,
                'height': rows, 'opacity': 1, 'visible': True, 'data': data}

    m = {
        'compressionlevel': -1, 'height': rows, 'infinite': False,
        'layers': [tl('floor', floor_data, 1), tl('walls', [0] * (cols * rows), 2),
                   tl('furniture-below', [0] * (cols * rows), 3), tl('furniture-above', [0] * (cols * rows), 4),
                   tl('collision', coll_data, 5),
                   {'id': 6, 'name': 'spawn-points', 'type': 'objectgroup', 'opacity': 1, 'visible': True,
                    'x': 0, 'y': 0, 'draworder': 'topdown', 'objects': objects},
                   {'id': 7, 'name': 'zones', 'type': 'objectgroup', 'opacity': 1, 'visible': True,
                    'x': 0, 'y': 0, 'draworder': 'topdown', 'objects': zones}],
        'nextlayerid': 8, 'nextobjectid': oid + 2, 'orientation': 'orthogonal',
        'renderorder': 'right-down', 'tiledversion': '1.10.2', 'tileheight': TS,
        'tilesets': [{'firstgid': 1, 'name': 'office-new', 'image': IMAGE, 'imagewidth': W,
                      'imageheight': H, 'tilewidth': TS, 'tileheight': TS, 'columns': cols,
                      'tilecount': cols * rows}],
        'tilewidth': TS, 'type': 'map', 'version': '1.10', 'width': cols,
    }
    with open(os.path.join(PACK, 'office-new.tmj'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(m, fh, ensure_ascii=False, separators=(',', ':'))

    # 调试图
    dbg = im.copy()
    d = ImageDraw.Draw(dbg, 'RGBA')
    for ty in range(rows):
        for tx in range(cols):
            box = [tx * TS, ty * TS, tx * TS + TS - 1, ty * TS + TS - 1]
            d.rectangle(box, fill=(0, 255, 0, 45) if (tx, ty) in walk else (255, 0, 0, 85))
    for o in objects:
        d.ellipse([o['x'] - 6, o['y'] - 6, o['x'] + 6, o['y'] + 6], fill=(0, 120, 255, 230))
    dbg.save(os.path.join(OUT, 'map-debug.png'))
    half = dbg.resize((dbg.width * 2 // 3, dbg.height * 2 // 3))
    half.save(os.path.join(OUT, 'map-debug-half.png'))
    print('  地图 + 调试图已出')

    blocked_seats = [n for n, (x, y) in seats.items() if (x // TS, y // TS) not in walk]
    print('  座位落点不在可走格（引擎会强制放行）：%s' % (blocked_seats or '无'))


if __name__ == '__main__':
    main()
