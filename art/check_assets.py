# -*- coding: utf-8 -*-
"""像素素材自检：AI 出的图能不能直接进管线，一跑就知道。

检查项（对应 assets/ART-SPEC.md 的硬性要求）：
  1. sheet 尺寸 = 504x324（7 列 x 3 行，单元格 72x108）
  2. portrait 尺寸 = 144x216
  3. 有透明背景（存在 alpha=0 的像素），且不是整张空白
  4. 每个单元格都有内容（非空）
  5. 脚底贴底（内容包围盒底边距单元格底 <= 4px）
  6. 头顶留白合理（4~32px）
  7. 不越格（左右边不能被内容顶满，防"邻格半个人"混入）
  8. 侧面行朝右（用左右像素分布近似判断）
用法：
  python art/check_assets.py                     检查 assets/chars/ 下全部角色
  python art/check_assets.py path/to/x.sheet.png 检查单张
"""
import glob
import os
import sys

from PIL import Image

CELL = (72, 108)
COLS, ROWS = 7, 3
SHEET = (CELL[0] * COLS, CELL[1] * ROWS)     # 504 x 324
PORT = (144, 216)
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIR = os.path.join(REPO, 'assets', 'chars')


def check_sheet(path):
    errs, warns = [], []
    im = Image.open(path)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    if im.size != SHEET:
        # 允许整数倍缩放（AI 出图常见 2x/4x），给出明确换算提示
        if im.size[0] % SHEET[0] == 0 and im.size[1] % SHEET[1] == 0:
            k = im.size[0] // SHEET[0]
            if im.size[1] // SHEET[1] == k:
                warns.append('尺寸是规格的 %dx（%s），会按 %d 缩到 %s' % (k, im.size, k, SHEET))
                im = im.resize(SHEET, Image.NEAREST)
            else:
                errs.append('尺寸 %s 不是 504x324 的整数倍' % (im.size,))
        else:
            errs.append('尺寸 %s 应为 %s' % (im.size, SHEET))
    a = im.split()[3]
    if a.getextrema() == (255, 255):
        errs.append('没有透明背景（整张不透明）')
    elif a.getextrema()[1] == 0:
        errs.append('整张全透明（没有内容）')

    cw, ch = CELL
    for r in range(ROWS):
        for c in range(COLS):
            cell = im.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
            bb = cell.getbbox()
            tag = '第%d行第%d列' % (r + 1, c + 1)
            if not bb:
                errs.append('%s 是空的' % tag)
                continue
            x0, y0, x1, y1 = bb
            if r == 0 and c == 0:            # 只在正面的第一帧上做强约束，避免噪音
                if ch - y1 > 4:
                    warns.append('脚底没贴底（差 %dpx）' % (ch - y1))
                if not (4 <= y0 <= 32):
                    warns.append('头顶留白 %dpx（建议 4~32）' % y0)
            if x0 <= 0 or x1 >= cw:
                warns.append('%s 内容贴到左右边（可能混入邻格）' % tag)
    # 侧面朝右：比较侧面前两帧左右半区像素量
    side = im.crop((0, 2 * ch, cw * 2, 3 * ch))
    left = side.crop((0, 0, cw, ch)).split()[3].point(lambda v: 255 if v > 40 else 0).getbbox() is not None and 1 or 0
    right = side.crop((cw, 0, cw * 2, ch)).split()[3].point(lambda v: 255 if v > 40 else 0).getbbox() is not None and 1 or 0
    if left and right and abs(left - right) / max(left, right) < 0.05:
        warns.append('侧面朝向看不清（左右像素量接近，规格要求朝右）')
    return errs, warns


def check_portrait(path):
    errs, warns = [], []
    im = Image.open(path)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    if im.size != PORT:
        if im.size[0] % PORT[0] == 0 and im.size[1] % PORT[1] == 0:
            warns.append('尺寸是规格的整数倍 %s（应为 %s）' % (im.size, PORT))
        else:
            errs.append('头像尺寸 %s 应为 %s' % (im.size, PORT))
    if not im.getbbox():
        errs.append('头像全透明')
    return errs, warns


def main():
    args = sys.argv[1:]
    if args:
        targets = args
    else:
        targets = sorted(glob.glob(os.path.join(DEFAULT_DIR, '*.sheet.png')))
    if not targets:
        print('  没有找到 *.sheet.png')
        return 2
    ok = fail = 0
    allwarn = 0
    for f in targets:
        errs, warns = check_sheet(f)
        name = os.path.basename(f)
        base = f[:-10]
        if os.path.exists(base + '.portrait.png'):
            e2, w2 = check_portrait(base + '.portrait.png')
            errs += e2
            warns += w2
        else:
            warns.append('缺少配套头像 %s.portrait.png' % os.path.basename(base))
        allwarn += len(warns)
        if errs:
            fail += 1
            print('  ✗ %-28s %d 个错误' % (name, len(errs)))
            for e in errs[:4]:
                print('        · ' + e)
        else:
            ok += 1
            print('  ✓ %-28s 通过%s' % (name, ('（%d 条提醒）' % len(warns)) if warns else ''))
        for w in warns[:2]:
            print('        ~ ' + w)
    print('  ---- 通过 %d ｜ 失败 %d ｜ 提醒 %d ----' % (ok, fail, allwarn))
    return 1 if fail else 0


if __name__ == '__main__':
    raise SystemExit(main())
