# -*- coding: utf-8 -*-
"""导入你自己的像素素材，让它在办公室里出现。

三种导入方式（都不用改代码）：

  A) 单个人物图（最省事）
     python import_assets.py char --image my-hero.png --name "我的英雄" [--key hero]
        - 支持两种输入：①单帧立绘 ②已经是多帧的横条/网格图
        - 输出引擎格式：<key>.sheet.png（3 行 = 正面/背面/侧面，7 列 = 动画帧）+ <key>.portrait.png

  B) 多角色角色表（一行一个角色，像随包附带的示例那样）
     python import_assets.py sheet --image my-sheet.png --map cast-map.json
        - cast-map.json 里写清楚：网格 x0/列数/行数、每一行对应哪个角色与名字
        - 自动做连通块抠图（去掉邻格混入的"半个人"）、侧面镜像、缩放对齐

  C) 地图（换掉整间办公室的贴图）
     python import_assets.py map --image my-office.png [--uniform 50]
        - 自动判定可走性并生成 Tiled 地图（复用 art/build_map2.py）

所有子命令都支持 --install：把产物拷进应用目录并交给 patches/patch_renderer.py 生效。
（--install 会先备份，且只在你显式指定时执行。）

先看有没有角色表示例：assets/cast-map.example.json
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, 'art')
ASSETS = os.path.join(HERE, 'assets')
OUT = os.path.join(HERE, 'build', 'assets')
sys.path.insert(0, ART)

DEFAULT_CELL = (72, 108)     # 引擎里的单元尺寸
DEFAULT_PORT = (144, 216)    # 头像尺寸


def _load_art():
    try:
        import build_cast2 as b2          # 提供 cutout / scale_into / bob / leg_shift
        return b2
    except Exception as e:
        print('  ✗ 找不到 art/build_cast2.py 的抠图函数：%s' % e)
        sys.exit(2)


def make_frames(module, base):
    """把一张姿态图变成 7 帧（行走 4 帧：两帧位移 + 两帧微跳；其余为工作/阅读姿态）。"""
    bob = module.bob
    leg = module.leg_shift
    return [base, leg(bob(base, -1), -1), leg(bob(base, -1), 1), base, bob(base, -1), base, bob(base, -1)]


def build_one(module, front, sides, back, key, cw, ch, pw, ph):
    """由 正面/侧面/背面 三张图生成引擎格式的 sheet + portrait。"""
    f = module.scale_into(front, cw, ch)
    s = module.scale_into(sides, cw, ch)
    b = module.scale_into(back, cw, ch)
    sheet = module.Image.new('RGBA', (cw * 7, ch * 3), (0, 0, 0, 0))
    for r, base in enumerate([f, b, s]):
        for i, fr in enumerate(make_frames(module, base)):
            sheet.alpha_composite(fr, (i * cw, r * ch))
    os.makedirs(OUT, exist_ok=True)
    sp = os.path.join(OUT, key + '.sheet.png')
    sheet.save(sp)
    bb = f.getbbox() or (0, 0, cw, ch)
    face = f.crop(bb)
    w, h = face.size
    sc = min(pw / w, (ph - 2) / h)
    nw, nh = max(1, round(w * sc)), max(1, round(h * sc))
    port = module.Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
    port.alpha_composite(face.resize((nw, nh), module.Image.NEAREST), ((pw - nw) // 2, ph - nh - 1))
    pp = os.path.join(OUT, key + '.portrait.png')
    port.save(pp)
    print('  ✓ %-14s → %s / %s' % (key, os.path.basename(sp), os.path.basename(pp)))
    return sp, pp


def load_image(path):
    import PIL.Image as I
    if not os.path.exists(path):
        print('  ✗ 找不到图片：%s' % path)
        sys.exit(2)
    return I.open(path).convert('RGBA')


def cmd_char(a):
    module = _load_art()
    im = load_image(a.image)
    w, h = im.size
    # 若是整张角色表（很宽），提示改用 sheet 模式
    if w > h * 3 and not a.force:
        print('  提示：这张图看起来是多角色角色表（%dx%d）。请改用：import_assets.py sheet --image ... --map cast-map.json' % (w, h))
        print('       确定要当单角色处理，请加 --force')
        return 1
    key = a.key or os.path.splitext(os.path.basename(a.image))[0].lower().replace(' ', '-')
    front = module.cutout(im)
    side = front.transpose(0)              # FLIP_LEFT_RIGHT
    side = side
    build_one(module, front, side, front, key, *DEFAULT_CELL, *DEFAULT_PORT)
    print('  名字建议填：%s' % a.name)
    if a.install:
        do_install(key, a.name)
    return 0


def cmd_sheet(a):
    module = _load_art()
    sheet = load_image(a.image)
    cfg = json.load(open(a.map, encoding='utf-8')) if a.map else {}
    x0 = cfg.get('x0', 0)
    cols = cfg.get('cols', 15)
    rows = cfg.get('rows', 8)
    skip_label = cfg.get('skip_first_column', False)
    mapping = cfg.get('rows_map', {})          # 行号(字符串) -> {"key":..,"name":..}
    W, H = sheet.size
    cw = (W - x0) / cols
    ch = H / rows
    made = []
    for r in range(rows):
        m = mapping.get(str(r))
        if not m:
            continue
        key = m.get('key') or ('char%d' % r)
        front_col, side_col, back_col = m.get('front', 0), m.get('side', 1), m.get('back', 2)
        def cell(c):
            x1 = int(round(x0 + c * cw)); x2 = int(round(x0 + (c + 1) * cw))
            y1 = int(round(r * ch)); y2 = int(round((r + 1) * ch))
            return sheet.crop((x1, y1, x2, y2))
        front = module.cutout(cell(front_col))
        side = module.cutout(cell(side_col)).transpose(0)   # 侧面镜像成朝右
        back = module.cutout(cell(back_col))
        sp, pp = build_one(module, front, side, back, key, *DEFAULT_CELL, *DEFAULT_PORT)
        made.append((key, m.get('name') or key, m.get('seat', '')))
    print('  共生成 %d 个角色' % len(made))
    for k, n, seat in made:
        print('   - %-14s 名字=%-12s 工位=%s' % (k, n, seat or '(未指定)'))
    if a.install:
        for k, n, _s in made:
            do_install(k, n)
    return 0


def cmd_map(a):
    script = os.path.join(ART, 'build_map2.py')
    if not os.path.exists(script):
        print('  ✗ 缺少 art/build_map2.py')
        return 2
    env = dict(os.environ)
    env['MAP_UNIFORM'] = str(a.uniform)
    env['MAP_SRC'] = a.image
    r = subprocess.run([sys.executable, script], env=env)
    print('  （地图生成退出码 %s；产物在 art/ 旁边，安装请用 patches/patch_map.py）' % r.returncode)
    return r.returncode


def do_install(key, name):
    """把产物交给补丁脚本生效（会先备份）。"""
    pr = os.path.join(HERE, 'patches', 'patch_renderer.py')
    if not os.path.exists(pr):
        print('  ! 未找到 patches/patch_renderer.py，跳过安装；产物在 %s' % OUT)
        return
    print('  → 调用 patches/patch_renderer.py 安装（它会自动备份并过语法门）…')
    env = dict(os.environ)
    env['MD_IMPORT_KEY'] = key
    env['MD_IMPORT_NAME'] = name
    env['MD_IMPORT_DIR'] = OUT
    r = subprocess.run([sys.executable, pr], env=env)
    print('  安装退出码：%s' % r.returncode)


def main():
    ap = argparse.ArgumentParser(description='导入你自己的像素素材到星域蜂巢')
    sub = ap.add_subparsers(dest='cmd', required=True)

    c = sub.add_parser('char', help='导入单个人物')
    c.add_argument('--image', required=True)
    c.add_argument('--name', default='')
    c.add_argument('--key', default='')
    c.add_argument('--force', action='store_true')
    c.add_argument('--install', action='store_true')
    c.set_defaults(fn=cmd_char)

    s = sub.add_parser('sheet', help='导入多角色角色表')
    s.add_argument('--image', required=True)
    s.add_argument('--map', default=os.path.join(ASSETS, 'cast-map.example.json'))
    s.add_argument('--install', action='store_true')
    s.set_defaults(fn=cmd_sheet)

    m = sub.add_parser('map', help='导入自己的办公室地图')
    m.add_argument('--image', required=True)
    m.add_argument('--uniform', type=int, default=50)
    m.set_defaults(fn=cmd_map)

    a = ap.parse_args()
    print('== 星域蜂巢 · 素材导入 ==')
    print('   工作目录：%s' % HERE)
    os.makedirs(OUT, exist_ok=True)
    rc = a.fn(a)
    print('== 完成（退出码 %s）==' % rc)
    return rc


if __name__ == '__main__':
    sys.exit(main())
