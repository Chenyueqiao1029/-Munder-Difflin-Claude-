# -*- coding: utf-8 -*-
"""端到端验收：一条命令给出 PASS/FAIL 汇总与退出码。

跑什么：
  1) 素材自检            art/check_assets.py（要求 0 失败）
  2) 形象上传（临时图）   tools/customize.py char   —— 产出到临时目录
  3) 办公室上传（合成图） tools/customize.py office —— 产出到临时目录
  4) 安装层干跑          patches/patch_renderer.py --dry-run 与 patches/patch_map.py --dry-run
  5) 洁净度             git status --porcelain 必须为空（跑完不许留下脏文件）

安全：所有会产生副作用的步骤都做「快照 → 执行 → 还原」，绝不把测试产物留在仓库里。
用法：python tools/acceptance.py [--keep]      --keep 表示保留临时目录便于排查
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PY = sys.executable
WATCH = ['assets/chars', 'assets/custom-agents.json', 'assets/map', 'assets/source']


def run(args, timeout=600):
    r = subprocess.run(args, cwd=REPO, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    return r.returncode, ((r.stdout or '') + (r.stderr or ''))


def _unlock(p):
    """清掉只读属性（从别处拷来的图常带 ReadOnly，会让复制/删除 Permission denied —— 踩过两次）。"""
    try:
        os.chmod(p, 0o666)
    except Exception:
        pass
    if os.path.isdir(p):
        for root, dirs, files in os.walk(p):
            for n in list(dirs) + list(files):
                try:
                    os.chmod(os.path.join(root, n), 0o666)
                except Exception:
                    pass


def snapshot(dst):
    os.makedirs(dst, exist_ok=True)
    for rel in WATCH:
        src = os.path.join(REPO, rel)
        if not os.path.exists(src):
            continue
        tgt = os.path.join(dst, rel.replace('/', '__'))
        _unlock(src)
        if os.path.isdir(src):
            shutil.copytree(src, tgt, dirs_exist_ok=True)
        else:
            shutil.copy2(src, tgt)


def restore(dst):
    for rel in WATCH:
        cur = os.path.join(REPO, rel)
        bak = os.path.join(dst, rel.replace('/', '__'))
        if os.path.exists(cur):
            _unlock(cur)
            if os.path.isdir(cur):
                shutil.rmtree(cur, ignore_errors=True)
            else:
                try:
                    os.remove(cur)
                except Exception:
                    pass
        if os.path.exists(bak):
            _unlock(bak)
            if os.path.isdir(bak):
                shutil.copytree(bak, cur, dirs_exist_ok=True)
            else:
                shutil.copy2(bak, cur)
            _unlock(cur)


def make_test_char(path):
    """造一张测试立绘：亮底 + 一个人形色块。"""
    try:
        from PIL import Image, ImageDraw
    except Exception as e:
        return False, '没有 Pillow: %s' % e
    im = Image.new('RGB', (240, 360), (250, 250, 250))
    d = ImageDraw.Draw(im)
    d.ellipse([90, 40, 150, 110], fill=(240, 200, 160))          # 头
    d.rectangle([95, 115, 145, 250], fill=(70, 110, 200))        # 身
    d.rectangle([80, 120, 95, 210], fill=(240, 200, 160))        # 左臂
    d.rectangle([145, 120, 160, 210], fill=(240, 200, 160))      # 右臂
    d.rectangle([98, 250, 118, 330], fill=(60, 60, 80))          # 左腿
    d.rectangle([122, 250, 142, 330], fill=(60, 60, 80))         # 右腿
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return True, ''


def make_test_office(path):
    try:
        from PIL import Image, ImageDraw
    except Exception as e:
        return False, '没有 Pillow: %s' % e
    im = Image.new('RGB', (640, 480), (214, 206, 190))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 639, 32], fill=(72, 62, 56))
    d.rectangle([608, 0, 639, 479], fill=(72, 62, 56))
    d.rectangle([0, 448, 639, 479], fill=(72, 62, 56))
    for i in range(4):
        d.rectangle([60 + i * 140, 220, 120 + i * 140, 260], fill=(92, 76, 60))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return True, ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--keep', action='store_true')
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix='starhive-accept-')
    snap = os.path.join(tmp, 'snap')
    results = []      # (名称, 通过?, 说明)

    # 跑之前的仓库状态：验收的判据是"**不新增**脏文件"，而不是"仓库必须完全干净"
    # （开发者本来就可能带着未提交改动跑验收）
    rc0, before = run(['git', 'status', '--porcelain'])
    before_set = {l.strip() for l in before.split('\n') if l.strip()}

    print('=' * 74)
    print(' 星域蜂巢 · 端到端验收    临时目录: %s' % tmp)
    print('=' * 74)

    # 1) 素材自检
    rc, out = run([PY, os.path.join(HERE, '..', 'art', 'check_assets.py')])
    tail = [l for l in out.split('\n') if '通过' in l and '失败' in l]
    results.append(('素材自检 art/check_assets.py', rc == 0, (tail[-1].strip() if tail else out.strip()[-80:])))

    # 快照
    snapshot(snap)
    char_img = os.path.join(tmp, 'test-char.png')
    office_img = os.path.join(tmp, 'test-office.png')
    okc, msgc = make_test_char(char_img)
    oko, msgo = make_test_office(office_img)

    # 2) 形象上传
    if okc:
        rc, out = run([PY, os.path.join(HERE, 'customize.py'), 'char', char_img,
                       '--name', '验收测试', '--key', 'acceptance-test'], timeout=600)
        ok = rc == 0 and os.path.exists(os.path.join(REPO, 'assets', 'chars', 'acceptance-test.sheet.png'))
        results.append(('形象上传 tools/customize.py char', ok, out.strip().split('\n')[-1][:90]))
    else:
        results.append(('形象上传 tools/customize.py char', False, msgc))

    # 3) 办公室上传
    if oko:
        rc, out = run([PY, os.path.join(HERE, 'customize.py'), 'office', office_img,
                       '--tile', '16', '--seats', '8'], timeout=600)
        ok = rc == 0 and os.path.exists(os.path.join(REPO, 'assets', 'map', 'office-map.json'))
        results.append(('办公室上传 tools/customize.py office', ok, out.strip().split('\n')[-1][:90]))
    else:
        results.append(('办公室上传 tools/customize.py office', False, msgo))

    # 4) 安装层干跑
    for name, rel in (('patch_renderer.py --dry-run', 'patches/patch_renderer.py'),
                      ('patch_map.py --dry-run', 'patches/patch_map.py')):
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            results.append((name, False, '文件不存在'))
            continue
        t = open(p, encoding='utf-8', errors='replace').read()
        if '--dry-run' not in t:
            results.append((name, False, '脚本还没实现 --dry-run（等 patches 可移植改造完成）'))
            continue
        rc, out = run([PY, p, '--dry-run'], timeout=600)
        results.append((name, rc == 0, out.strip().split('\n')[-1][:110] if out.strip() else ''))

    # 还原
    restore(snap)

    # 5) 洁净度：跑完不许**新增**脏文件（允许跑之前就存在的未提交改动）
    rc, out = run(['git', 'status', '--porcelain'])
    after_set = {l.strip() for l in out.split('\n') if l.strip()}
    new_dirty = sorted(after_set - before_set)
    new_dirty = [l for l in new_dirty if 'tools/acceptance.py' not in l and 'tools\\acceptance.py' not in l]
    results.append(('验收不新增脏文件', not new_dirty,
                    ('新增脏文件: ' + '; '.join(new_dirty[:4])) if new_dirty else '无新增 ✓（跑前已有 %d 项未提交，与本验收无关）' % len(before_set)))

    print()
    width = max(len(x[0]) for x in results)
    npass = 0
    for name, ok, note in results:
        mark = 'PASS' if ok else 'FAIL'
        npass += 1 if ok else 0
        print('  [%s] %-*s  %s' % (mark, width, name, note))
    print('-' * 74)
    print('  汇总：%d/%d 通过%s' % (npass, len(results), '' if npass == len(results) else '  ← 有未通过项'))
    if a.keep:
        print('  临时目录保留：%s' % tmp)
    else:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if npass == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())
