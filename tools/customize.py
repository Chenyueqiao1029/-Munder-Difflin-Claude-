# -*- coding: utf-8 -*-
"""一键自定义：形象 / 办公室。**给普通用户用**——不用懂代码，选张图就行。

用法（三种都行）：
  1) 双击 自定义形象.cmd / 自定义办公室.cmd，然后把图片拖进去
  2) python tools/customize.py 形象 D:\\我的图.png --name "我的助手"
  3) python tools/customize.py 办公室 D:\\我的办公室.png --install

说明：
  · 形象：任意立绘 -> 引擎规格的角色图集（3 行 x 7 列，72x108）+ 头像（144x216）
  · 办公室：任意俯视图 -> 图集 + 可走性 + 自动排工位；加 --install 才会装进办公室（先备份）
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import time

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MAPDIR = os.path.join(REPO, 'assets', 'map')
ATLAS = os.path.join(MAPDIR, 'office-atlas.png')
MAPJSON = os.path.join(MAPDIR, 'office-map.json')
SEATS = os.path.join(MAPDIR, 'office-seats.json')
STAMP = time.strftime('%Y%m%d-%H%M%S')


def log(s):
    print('  ' + s, flush=True)


def pick_file(title='选一张图片'):
    """弹系统文件选择框（用户主动触发，不是偷弹）。"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        r = tk.Tk()
        r.withdraw()
        p = filedialog.askopenfilename(title=title, filetypes=[
            ('图片', '*.png *.jpg *.jpeg *.webp *.bmp'), ('所有文件', '*.*')])
        r.destroy()
        return p
    except Exception as e:
        log('（打不开文件选择框：%s）请改成：python tools/customize.py 形象 <图片路径>' % str(e)[:60])
        return ''


# ---------------------------------------------------------------- 形象
def do_char(img, name, key, install):
    t = os.path.join(HERE, 'add_custom_agent.py')
    if not os.path.exists(t):
        log('✗ 找不到 tools/add_custom_agent.py')
        return 2
    cmd = [sys.executable, t, '--image', img, '--name', name or '我的角色']
    if key:
        cmd += ['--key', key]
    if install:
        cmd += ['--install']
    log('→ 调用形象导入（自动抠背景 / 切 3x7 / 出头像）…')
    r = subprocess.run(cmd)
    if r.returncode == 0:
        log('完成 ✓ 产物在 assets/chars/%s.*，并登记到 assets/custom-agents.json' % (key or '(自动取名)'))
    return r.returncode


# ---------------------------------------------------------------- 办公室
def tile_walkable(im, ts):
    """判断每个图块能不能走：地面色偏亮、纹理方差小 -> 可走；墙/家具偏暗或花 -> 不可走。
       这是启发式（和 build_map2.py 的 tile_stats 同思路），不保证 100% 准，用户可手改 JSON。"""
    cols, rows = im.width // ts, im.height // ts
    grid = []
    for r in range(rows):
        line = []
        for c in range(cols):
            box = im.crop((c * ts, r * ts, (c + 1) * ts, (r + 1) * ts)).convert('L')
            px = list(box.getdata())
            avg = sum(px) / len(px)
            var = sum((p - avg) ** 2 for p in px) / len(px)
            # 亮 + 平整 -> 可走
            line.append(1 if (avg > 105 and var < 900) else 0)
        grid.append(line)
    return grid


def auto_seats(im, grid, ts, want):
    """在图块网格里自动排 want 个工位：避开最外圈，按行列均匀分布，优先落在可走格上。"""
    rows, cols = len(grid), len(grid[0]) if grid else 0
    if not rows or not cols:
        return []
    margin_y, margin_x = max(1, rows // 8), max(1, cols // 8)
    usable_r = list(range(margin_y, rows - margin_y))
    usable_c = list(range(margin_x, cols - margin_x))
    per_row = max(1, (want + 1) // 2)          # 上下两排摆
    seats = []
    step_y = max(1, len(usable_r) // 2)
    row_ys = usable_r[::step_y][:2] or usable_r[:1]
    for ri, ry in enumerate(row_ys):
        step_x = max(1, len(usable_c) // per_row)
        for cx in usable_c[::step_x][:per_row]:
            # 就近找一个可走格
            for dy in (0, 1, -1, 2, -2):
                for dx in (0, 1, -1, 2, -2):
                    rr, cc = ry + dy, cx + dx
                    if 0 <= rr < rows and 0 <= cc < cols and grid[rr][cc]:
                        seats.append({'x': cc * ts + ts // 2, 'y': rr * ts + ts // 2})
                        break
                else:
                    continue
                break
            if len(seats) >= want:
                return seats
    return seats[:want]


def do_office(img, tile, seats_n, install):
    global ATLAS
    im = Image.open(img).convert('RGB')
    ts = max(8, int(tile))
    W, H = (im.width // ts) * ts, (im.height // ts) * ts
    if W < ts * 4 or H < ts * 4:
        log('✗ 图片太小（%dx%d），至少 %dx%d' % (im.width, im.height, ts * 4, ts * 4))
        return 2
    if (W, H) != im.size:
        im = im.crop((0, 0, W, H))
    log('办公室图 %dx%d -> 对齐到 %dx%d（图块 %dpx）' % (Image.open(img).size[0], Image.open(img).size[1], W, H, ts))

    grid = tile_walkable(im, ts)
    walk = sum(sum(r) for r in grid)
    total = len(grid) * len(grid[0])
    log('可走图块 %d / %d（%.0f%%）—— 启发式判定，可在 %s 里手改' % (walk, total, 100.0 * walk / total,
                                                  os.path.relpath(MAPJSON, REPO)))
    os.makedirs(MAPDIR, exist_ok=True)
    if os.path.exists(ATLAS):
        bak = ATLAS.replace('.png', '.backup-' + STAMP + '.png')
        shutil.copy2(ATLAS, bak)
        log('已备份旧图集 → %s' % os.path.relpath(bak, REPO))
        # 从别处拷来的图常带"只读"属性，直接覆盖会 PermissionError —— 先解锁再删
        try:
            os.chmod(ATLAS, 0o666)
        except Exception:
            pass
        try:
            os.remove(ATLAS)
        except Exception as e:
            log('! 旧图集删不掉（%s），改用新文件名保存' % str(e)[:60])
            ATLAS = ATLAS.replace('.png', '.new-' + STAMP + '.png')
    im.save(ATLAS)
    log('已写入新图集 → %s' % os.path.relpath(ATLAS, REPO))

    cols, rows = W // ts, H // ts
    # Tiled 地图：一层 ground（全部图块，按行铺），一层 blocked（不可走格）
    def layer(name, data, lid):
        return {'id': lid, 'name': name, 'type': 'tilelayer', 'x': 0, 'y': 0,
                'width': cols, 'height': rows, 'opacity': 1, 'visible': True, 'data': data}
    ground = [1 + (r * cols + c) % (cols * rows) for r in range(rows) for c in range(cols)]
    blocked = [0] * (rows * cols)
    for r in range(rows):
        for c in range(cols):
            if not grid[r][c]:
                blocked[r * cols + c] = 1
    tmj = {
        'compressionlevel': -1, 'height': rows, 'width': cols, 'infinite': False,
        'layers': [layer('ground', ground, 1), layer('blocked', blocked, 2)],
        'nextlayerid': 3, 'nextobjectid': 1, 'orientation': 'orthogonal',
        'renderorder': 'right-down', 'tiledversion': '1.10.2',
        'tileheight': ts, 'tilewidth': ts, 'type': 'map', 'version': '1.10',
        'tilesets': [{'firstgid': 1, 'name': 'office-custom', 'image': 'office-atlas.png',
                      'imagewidth': W, 'imageheight': H, 'tilewidth': ts, 'tileheight': ts,
                      'columns': cols, 'tilecount': cols * rows}],
    }
    io.open(MAPJSON, 'w', encoding='utf-8', newline='\n').write(json.dumps(tmj, ensure_ascii=False, indent=1))
    log('已写入地图 → %s（%dx%d 格）' % (os.path.relpath(MAPJSON, REPO), cols, rows))

    st = auto_seats(im, grid, ts, max(1, seats_n))
    io.open(SEATS, 'w', encoding='utf-8', newline='\n').write(json.dumps(
        {'_说明': '自动排的工位（像素坐标，基于 office-atlas.png）。想调位置直接改 x/y。',
         'tile': ts, 'count': len(st), 'seats': st}, ensure_ascii=False, indent=1))
    log('已自动排 %d 个工位 → %s' % (len(st), os.path.relpath(SEATS, REPO)))

    if install:
        pm = os.path.join(REPO, 'patches', 'patch_map.py')
        if os.path.exists(pm):
            log('→ 调用 patches/patch_map.py 装进办公室（先备份 + 过语法门）…')
            subprocess.run([sys.executable, pm])
        else:
            log('! 没找到 patches/patch_map.py，跳过安装（产物已就绪）')
    else:
        log('（没加 --install：只生成，没动办公室。确认满意后再加 --install）')
    return 0


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument('mode', nargs='?', choices=['形象', '办公室', 'char', 'office', 'pick'])
    ap.add_argument('image', nargs='?')
    ap.add_argument('--name', default='')
    ap.add_argument('--key', default='')
    ap.add_argument('--tile', type=int, default=16)
    ap.add_argument('--seats', type=int, default=12)
    ap.add_argument('--install', action='store_true')
    a = ap.parse_args()

    print('==============================================')
    print(' 星域蜂巢 · 一键自定义（形象 / 办公室）')
    print('==============================================')
    mode = a.mode
    img = a.image
    if mode in (None, 'pick'):
        print('  1 = 自定义形象（一个人物立绘）')
        print('  2 = 自定义办公室（一张俯视场景图）')
        try:
            c = input('  输入 1 或 2 后回车：').strip()
        except Exception:
            c = '1'
        mode = '办公室' if c == '2' else '形象'
        if not img:
            img = pick_file('选一张图片')
            if not img:
                print('  没选图片，退出。')
                return 1
    if mode in ('char',):
        mode = '形象'
    if mode in ('office',):
        mode = '办公室'
    if not img:
        img = pick_file('选一张图片')
        if not img:
            print('  没给图片路径，退出。')
            return 1
    if not os.path.exists(img):
        print('  ✗ 找不到图片：%s' % img)
        return 2
    print('  模式：%s ｜ 图片：%s' % (mode, img))
    print('----------------------------------------------')
    if mode == '形象':
        return do_char(img, a.name, a.key, a.install)
    return do_office(img, a.tile, a.seats, a.install)


if __name__ == '__main__':
    raise SystemExit(main())
