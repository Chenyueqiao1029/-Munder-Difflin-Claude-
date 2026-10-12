# -*- coding: utf-8 -*-
"""自定义模型/员工：把你上传的图变成办公室里看得见的一个"模型"。

用法：
  python tools/add_custom_agent.py --image D:\\我的图.png --name "我的模型" --key mymodel --model glm
  python tools/add_custom_agent.py --image 立绘.png --name "小助手" --key helper --install

做的事：
  1. 读你的图（任意尺寸、任意背景：纯色/棋盘格/透明都能处理）
  2. 生成引擎规格的 <key>.sheet.png（3 行 × 7 列，单元 72×108）与 <key>.portrait.png（144×216）
  3. 追加一条记录到 assets/custom-agents.json（自定义模型清单）
  4. 加 --install 才会调用补丁脚本装进办公室（会先备份 + 过语法门）
"""
import argparse
import glob
import io
import json
import os
import sys
import time

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'art'))
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_DIR = os.path.join(REPO, 'assets', 'chars')
MANIFEST = os.path.join(REPO, 'assets', 'custom-agents.json')
UNIT = (72, 108)
PORT = (144, 216)


def trim_and_clean(img):
    """去掉纯色/棋盘格背景，裁到内容，返回 RGBA。"""
    img = img.convert('RGBA')
    # 若四角基本同色 → 认为那是背景，做容差抠除
    w, h = img.size
    px = img.load()
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    if all(c[3] > 200 for c in corners):
        r0 = sum(c[0] for c in corners) // 4
        g0 = sum(c[1] for c in corners) // 4
        b0 = sum(c[2] for c in corners) // 4
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        op = out.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a > 40 and abs(r - r0) + abs(g - g0) + abs(b - b0) > 36:
                    op[x, y] = (r, g, b, a)
        img = out
    bb = img.getbbox()
    return img.crop(bb) if bb else img


def build(img, key):
    """由一张立绘生成 3×7 的 sheet 与头像。"""
    base = img
    back = base.transpose(Image.FLIP_LEFT_RIGHT)
    cw, ch = UNIT
    sheet = Image.new('RGBA', (cw * 7, ch * 3), (0, 0, 0, 0))

    def fit(im):
        w, h = im.size
        sc = min(cw / w, (ch - 6) / h)
        nw, nh = max(1, round(w * sc)), max(1, round(h * sc))
        s = im.resize((nw, nh), Image.NEAREST)
        cell = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
        cell.alpha_composite(s, ((cw - nw) // 2, ch - nh))
        return cell

    front_cell, back_cell = fit(base), fit(back)
    for r, cell in enumerate([front_cell, back_cell, front_cell]):
        for c in range(7):
            off = 0 if c in (0, 3, 5) else (-1 if c in (1, 4) else 1)   # 轻微上下位移当走路
            fr = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
            fr.alpha_composite(cell, (0, off))
            sheet.alpha_composite(fr, (c * cw, r * ch))
    os.makedirs(OUT_DIR, exist_ok=True)
    sp = os.path.join(OUT_DIR, key + '.sheet.png')
    sheet.save(sp)
    # 头像：头部区域放大
    w, h = base.size
    head = base.crop((0, 0, w, max(1, int(h * 0.45))))
    pw, ph = PORT
    sc = min(pw / head.width, ph / head.height)
    head = head.resize((max(1, int(head.width * sc)), max(1, int(head.height * sc))), Image.NEAREST)
    port = Image.new('RGBA', PORT, (0, 0, 0, 0))
    port.alpha_composite(head, ((pw - head.width) // 2, (ph - head.height) // 2))
    pp = os.path.join(OUT_DIR, key + '.portrait.png')
    port.save(pp)
    return sp, pp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--key', default='')
    ap.add_argument('--model', default='', help='这个角色背后用哪个模型（见 models/registry.json）')
    ap.add_argument('--install', action='store_true')
    a = ap.parse_args()

    if not os.path.exists(a.image):
        print('  ✗ 找不到图片：%s' % a.image)
        return 2
    key = a.key or os.path.splitext(os.path.basename(a.image))[0].lower().replace(' ', '-')
    key = ''.join(ch for ch in key if ch.isalnum() or ch in '-_') or 'custom'
    print('== 自定义模型导入 ==')
    print('   图片: %s' % a.image)
    print('   名称: %s ｜ key: %s ｜ 模型: %s' % (a.name, key, a.model or '(未指定)'))

    clean = trim_and_clean(Image.open(a.image))
    print('   抠背景后尺寸: %s' % (clean.size,))
    sp, pp = build(clean, key)
    print('   ✓ %s' % os.path.relpath(sp, REPO))
    print('   ✓ %s' % os.path.relpath(pp, REPO))

    rec = {'id': key, 'name': a.name, 'model': a.model, 'sheet': 'chars/%s.sheet.png' % key,
           'portrait': 'chars/%s.portrait.png' % key, 'source': os.path.abspath(a.image),
           'added': time.strftime('%Y-%m-%d %H:%M'), 'custom': True}
    data = {'_说明': '自定义模型/员工清单：由 tools/add_custom_agent.py 追加；产出图在 assets/chars/。', 'agents': []}
    if os.path.exists(MANIFEST):
        try:
            data = json.load(io.open(MANIFEST, encoding='utf-8'))
        except Exception:
            pass
    data.setdefault('agents', [])
    data['agents'] = [x for x in data['agents'] if x.get('id') != key] + [rec]
    data['count'] = len(data['agents'])
    io.open(MANIFEST, 'w', encoding='utf-8', newline='\n').write(json.dumps(data, ensure_ascii=False, indent=2))
    print('   ✓ 已登记到 %s（现有 %d 个自定义角色）' % (os.path.relpath(MANIFEST, REPO), data['count']))

    # 自检
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(REPO, 'art', 'check_assets.py'), sp],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('   —— 自检 ——')
    print('   ' + (r.stdout or '').strip().replace('\n', '\n   ')[:600])

    if a.install:
        pr = os.path.join(REPO, 'patches', 'patch_renderer.py')
        if os.path.exists(pr):
            print('   → 调用 patches/patch_renderer.py 安装（会先备份 + 过语法门）…')
            env = dict(os.environ)
            env['MD_IMPORT_KEY'] = key
            env['MD_IMPORT_NAME'] = a.name
            subprocess.run([sys.executable, pr], env=env)
        else:
            print('   ! 未找到 patches/patch_renderer.py，跳过安装')
    else:
        print('   （未加 --install，只生成与登记，没有动办公室）')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
