# -*- coding: utf-8 -*-
"""v4：三视图 → 18×32 像素精灵（走 / 打字 / 阅读 三套动作分开）

配合 CharacterSprite 的「自定义动作表」：
    列 0–2 = 走（抬腿 + 起伏）   列 3–4 = 打字（手臂下压前伸 + 起伏）   列 5–6 = 阅读（双手合拢 + 一张纸）
行 = 下(正面) / 上(背面) / 侧(侧面)；每格 18×32，透明背景，沿轮廓 1px 深色描边。
"""
import os
from collections import deque
from PIL import Image, ImageEnhance

SRC = r'D:\徐\MunderDifflin\custom-cast\_source'
OUT = r'D:\徐\MunderDifflin\custom-cast'

CELL_W, CELL_H = 36, 64          # 场景帧（2× 于引擎默认的 18×32：像素数 ×4，细节更清）
PORT_W, PORT_H = 72, 112         # 卡片头像（同样放大，用图片原始尺寸绘制）
COLS, ROWS = 7, 3
WHITE_TOL = 238
PALETTE = 20
ALPHA_CUT = 100
OUTLINE = (58, 46, 74, 255)
HAIR_MIN = (226, 220, 240)
PAPER = (250, 246, 232, 255)


def key_white(im):
    """从四边洪水填充：只吃与外界连通的近白像素（保住白发/白裙内部）。"""
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()
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
        r, g, b, a = px[x, y]
        if r < WHITE_TOL or g < WHITE_TOL or b < WHITE_TOL:
            continue
        px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return im


def trim(im):
    bbox = im.getchannel('A').getbbox()
    return im.crop(bbox) if bbox else im


def clear_outline(cell):
    px = cell.load()
    w, h = cell.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and (r, g, b) == OUTLINE[:3]:
                px[x, y] = (r, g, b, 0)
    return cell


def add_outline(cell):
    w, h = cell.size
    a = cell.getchannel('A').load()
    out = cell.copy()
    px = out.load()
    for y in range(h):
        for x in range(w):
            if a[x, y] > 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and a[nx, ny] > 0:
                    px[x, y] = OUTLINE
                    break
    return out


def to_cell(im, cw, ch, outline=True):
    im = trim(im)
    w, h = im.size
    scale = min((cw - 2) / w, (ch - 2) / h)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    small = im.resize((nw, nh), Image.LANCZOS)
    rgb = ImageEnhance.Contrast(small.convert('RGB')).enhance(1.55)
    rgb = ImageEnhance.Color(rgb).enhance(1.45)
    px = rgb.load()
    for y in range(nh):
        for x in range(nw):
            r, g, b = px[x, y]
            if r > 232 and g > 228 and b > 236:
                px[x, y] = HAIR_MIN
    rgb = rgb.quantize(colors=PALETTE, method=Image.MEDIANCUT).convert('RGB')
    a = small.getchannel('A').point(lambda v: 255 if v >= ALPHA_CUT else 0)
    small = Image.merge('RGBA', (*rgb.split(), a))
    cell = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    cell.alpha_composite(small, ((cw - nw) // 2, ch - nh - 1))
    return add_outline(clear_outline(cell)) if outline else cell


def shift_body(cell, dy=0):
    out = Image.new('RGBA', cell.size, (0, 0, 0, 0))
    out.alpha_composite(clear_outline(cell.copy()), (0, dy))
    return add_outline(out)


def shift_band(cell, top_f, bot_f, dx=0, dy=0):
    """把一小段整体平移，并把空出来的行/列用相邻像素补上（不留接缝、不产生描边横线）。"""
    w, h = cell.size
    y0, y1 = int(h * top_f), int(h * bot_f)
    base = clear_outline(cell.copy())
    band = base.crop((0, y0, w, y1))
    out = base.copy()

    # 顺序很重要：先清空该区域 → 贴入平移后的段 → 再用原段边缘把空出来的条带补上
    out.paste((0, 0, 0, 0), (0, y0, w, y1))
    out.alpha_composite(band, (dx, y0 + dy))
    if dy > 0:
        out.paste(band.crop((0, 0, w, dy)), (0, y0))
    elif dy < 0:
        out.paste(band.crop((0, y1 - y0 + dy, w, y1 - y0)), (0, y1 + dy))
    if dx > 0:
        out.paste(band.crop((0, 0, dx, y1 - y0)), (0, y0))
    elif dx < 0:
        out.paste(band.crop((w + dx, 0, w, y1 - y0)), (w + dx, y0))
    return add_outline(out)


def draw_paper(cell, x, y, w=5, h=3):
    out = cell.copy()
    px = out.load()
    for yy in range(y, min(cell.size[1], y + h)):
        for xx in range(x, min(cell.size[0], x + w)):
            px[xx, yy] = PAPER
    return add_outline(clear_outline(out))


def build_frames(cell):
    """7 帧：走1 走2 走3 · 打字1 打字2 · 阅读1 阅读2"""
    base = clear_outline(cell.copy())
    walk1 = add_outline(base.copy())
    walk2 = shift_band(shift_body(base, -1), 0.62, 1.0, dx=-1)      # 抬左腿
    walk3 = shift_band(shift_body(base, -1), 0.62, 1.0, dx=1)       # 抬右腿
    type1 = shift_band(base, 0.40, 0.72, dy=1)                      # 手臂下压（伏案）
    type2 = shift_body(type1, -1)                                   # 起伏
    read1 = draw_paper(shift_band(base, 0.40, 0.72, dx=-1), 6, int(CELL_H * 0.50))
    read2 = draw_paper(shift_body(shift_band(base, 0.40, 0.72, dx=1), -1), 6, int(CELL_H * 0.50) - 1)
    return [walk1, walk2, walk3, type1, type2, read1, read2]


def main():
    views = {}
    for name in ('front', 'side', 'back'):
        views[name] = key_white(Image.open(os.path.join(SRC, 'view-%s.png' % name)))
        print('  抠图 %-5s ok' % name)

    sheet = Image.new('RGBA', (CELL_W * COLS, CELL_H * ROWS), (0, 0, 0, 0))
    for name, row in (('front', 0), ('back', 1), ('side', 2)):
        cell = to_cell(views[name], CELL_W, CELL_H)
        for col, fr in enumerate(build_frames(cell)):
            sheet.alpha_composite(fr, (col * CELL_W, row * CELL_H))
    sheet.save(os.path.join(OUT, 'jim-sheet.png'))
    print('帧表:', sheet.size)

    to_cell(views['front'], PORT_W, PORT_H).save(os.path.join(OUT, 'jim-portrait.png'))
    print('头像:', (PORT_W, PORT_H))

    sheet.resize((sheet.width * 8, sheet.height * 8), Image.NEAREST).save(
        os.path.join(OUT, 'jim-preview-x8.png'))
    print('预览已出')


if __name__ == '__main__':
    main()
