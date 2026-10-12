# -*- coding: utf-8 -*-
"""自动校准切图：不靠人手数格子。
   1) 多色背景识别（格纹底也能去掉）
   2) 从"空白列/空白行"自动找出每个角色的帧边界
   3) 每行一个角色，取第 1/3/5 帧作为 正面/背面/侧面，重排成引擎要的 3 行 x 7 列
用法：python tools/slice_sheet_auto.py --image assets/source/brands12.png --keys glm,kimi,... --out build/auto
"""
import argparse
import json
import os
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
UNIT = (72, 108)
PORT = (144, 216)


def bg_colors(im, tol=18):
    """取背景色：四角 + 边缘一圈出现最多的若干种颜色。"""
    w, h = im.size
    px = im.load()
    samples = []
    for x in range(0, w, 7):
        samples += [px[x, 0], px[x, 1], px[x, h - 1], px[x, h - 2]]
    for y in range(0, h, 7):
        samples += [px[0, y], px[1, y], px[w - 1, y], px[w - 2, y]]
    cnt = Counter((r // 8 * 8, g // 8 * 8, b // 8 * 8) for r, g, b in samples)
    return [c for c, _n in cnt.most_common(6)]


def ink_mask(im, bgs, tol=22):
    w, h = im.size
    px = im.load()
    cols = [0] * w
    rows = [0] * h
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y][:3]
            bg = False
            for br, bg_, bb in bgs:
                if abs(r - br) <= tol + 8 and abs(g - bg_) <= tol + 8 and abs(b - bb) <= tol + 8:
                    bg = True
                    break
            if not bg:
                cols[x] += 1
                rows[y] += 1
    return cols, rows


def runs(profile, thresh=1, min_gap=4):
    """把 profile 切成交替的 [空, 有内容, 空, ...] 区段，返回内容段的 (start,end)。"""
    segs = []
    inrun = False
    s = 0
    gap = 0
    for i, v in enumerate(profile):
        if v > thresh:
            if not inrun:
                s = i
                inrun = True
            gap = 0
        else:
            if inrun:
                gap += 1
                if gap >= min_gap:
                    segs.append((s, i - gap + 1))
                    inrun = False
    if inrun:
        segs.append((s, len(profile)))
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', required=True)
    ap.add_argument('--keys', required=True, help='逗号分隔，自上而下每个角色的 id（跳过左侧标签栏）')
    ap.add_argument('--out', default=os.path.join(REPO, 'build', 'auto'))
    ap.add_argument('--front', type=int, default=0, help='正面用第几帧(0起)')
    ap.add_argument('--back', type=int, default=2, help='背面用第几帧')
    ap.add_argument('--side', type=int, default=4, help='侧面用第几帧')
    a = ap.parse_args()

    im = Image.open(a.image).convert('RGB')
    W, H = im.size
    print('  图: %s %s' % (a.image, im.size))
    bgs = bg_colors(im)
    print('  识别到背景色 %d 种: %s' % (len(bgs), ', '.join('#%02X%02X%02X' % c for c in bgs)))
    cols, rows = ink_mask(im, bgs)
    col_segs = runs(cols, 1, 4)
    row_segs = runs(rows, 1, 4)
    print('  列区段 %d 个 ｜ 行区段 %d 个' % (len(col_segs), len(row_segs)))
    print('    列: %s' % ', '.join('%d-%d' % s for s in col_segs[:16]))
    print('    行: %s' % ', '.join('%d-%d' % s for s in row_segs[:16]))

    keys = [k.strip() for k in a.keys.split(',') if k.strip()]
    # 丢掉最左边那个区段（标签栏），剩下的列区段里按"每行相同列位置"取帧
    if len(col_segs) > len(keys) and col_segs:
        col_segs = col_segs[1:]
    # 帧边界：优先按行区段数量与列区段对齐；若列区段太多（粘连），退化为等分
    if len(row_segs) < len(keys):
        print('  ! 行区段少于 keys，改用等分')
        row_segs = [(int(i * H / len(keys)), int((i + 1) * H / len(keys))) for i in range(len(keys))]

    os.makedirs(a.out, exist_ok=True)
    made = []
    for i, key in enumerate(keys):
        if i >= len(row_segs):
            break
        y0, y1 = row_segs[i]
        row = im.crop((0, y0, W, y1))
        rc, _rr = ink_mask(row, bgs)
        fr = runs(rc, 1, 4)
        if len(fr) > 1 and fr and fr[0][1] - fr[0][0] < 0.06 * W:
            fr = fr[1:]                      # 丢掉该行的标签栏
        if len(fr) < 3:
            print('  ! %s 该行只找到 %d 帧，跳过' % (key, len(fr)))
            continue
        def grab(idx):
            idx = min(idx, len(fr) - 1)
            x0, x1 = fr[idx]
            return row.crop((x0, 0, x1, y1 - y0))
        poses = [grab(a.front), grab(a.back), grab(a.side)]

        # 抠背景 -> RGBA
        def cut(img):
            img = img.convert('RGBA')
            p = img.load()
            w, h = img.size
            for yy in range(h):
                for xx in range(w):
                    r, g, b, al = p[xx, yy]
                    for br, bg_, bb in bgs:
                        if abs(r - br) <= 30 and abs(g - bg_) <= 30 and abs(b - bb) <= 30:
                            p[xx, yy] = (0, 0, 0, 0)
                            break
            return img
        poses = [cut(p) for p in poses]
        # 自适应缩放：取三姿态里最大的，统一比例
        bbs = [p.getbbox() for p in poses]
        mx = max((bb[2] - bb[0], bb[3] - bb[1]) for bb in bbs if bb)
        cw, ch = UNIT
        sc = min(cw / mx[0], (ch - 4) / mx[1])
        sheet = Image.new('RGBA', (cw * 7, ch * 3), (0, 0, 0, 0))
        for r, pose in enumerate(poses):
            bb = pose.getbbox()
            body = pose.crop(bb)
            nw, nh = max(1, round(body.width * sc)), max(1, round(body.height * sc))
            small = body.resize((nw, nh), Image.LANCZOS)
            for c in range(7):
                cell = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
                off = 0 if c in (0, 3, 5) else (-1 if c in (1, 4) else 1)
                cell.alpha_composite(small, ((cw - nw) // 2, ch - nh + off))
                sheet.alpha_composite(cell, (c * cw, r * ch))
        sheet.save(os.path.join(a.out, key + '.sheet.png'))
        # 头像
        front = poses[0].crop(poses[0].getbbox())
        head = front.crop((0, 0, front.width, max(1, int(front.height * 0.5))))
        pw, ph = PORT
        s2 = min(pw / head.width, ph / head.height)
        head = head.resize((max(1, int(head.width * s2)), max(1, int(head.height * s2))), Image.LANCZOS)
        port = Image.new('RGBA', PORT, (0, 0, 0, 0))
        port.alpha_composite(head, ((pw - head.width) // 2, (ph - head.height) // 2))
        port.save(os.path.join(a.out, key + '.portrait.png'))
        made.append((key, len(fr)))
        print('  ✓ %-10s 用第 %d/%d/%d 帧（该行共 %d 帧）' % (key, a.front, a.back, a.side, len(fr)))
    print('  共生成 %d 个 → %s' % (len(made), a.out))


if __name__ == '__main__':
    main()
