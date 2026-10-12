# -*- coding: utf-8 -*-
"""最小改动版地图补丁：只替换 3 处必需项 + esbuild 语法门。

  1) const officeMapRaw = '...'  → 新地图 JSON
  2) theme.tilesets: [...]      → 单个新图集（external png）
  3) theme.primarySeatNames     → 新座位名
其余（coffee/anchors/errandSpots/cafeStands/cafeSeatNames）**保持原样** —— 引擎对这些
是容错读取的，不动它们能把"改坏对象字面量"的风险降到最低。
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOLS = os.path.join(REPO, 'tools')
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

SEATS = ['desk-ceo', 'desk-workbuddy', 'desk-claude', 'desk-codex',
         'desk-dsh', 'desk-exec', 'desk-approve', 'desk-fix']

_ROLLBACK = None


class InstallError(RuntimeError):
    pass


def _load_config():
    try:
        from md_config import cfg_with_source
    except (ImportError, SyntaxError) as exc:
        raise InstallError(
            '无法加载 tools/md_config.py（%s）。请确认该文件存在且能通过 py_compile。' % exc)
    return cfg_with_source


def _require_app(app):
    out_dir = os.path.join(app, 'resources', 'app', 'out') if app else ''
    if not app or not os.path.isdir(out_dir):
        raise InstallError(
            '找不到 Munder Difflin 应用目录。请设置环境变量 MD_APP_DIR，'
            '或在仓库根 config.json 中填写 app_dir（应包含 resources\\app\\out）。')


def _require_esbuild(esbuild):
    if not esbuild or not os.path.isfile(esbuild):
        raise InstallError(
            '找不到 esbuild。请设置环境变量 MD_ESBUILD，'
            '或在仓库根 config.json 中填写 esbuild（指向 esbuild.exe）。')


def resolve_paths():
    config = _load_config()
    values = {key: config(key) for key in
              ('app_dir', 'esbuild', 'stage_dir', 'pack_dir', 'backup_dir')}
    paths = {
        'app': os.path.abspath(values['app_dir'][0]) if values['app_dir'][0] else '',
        'esbuild': os.path.abspath(values['esbuild'][0]) if values['esbuild'][0] else '',
        'stage': os.path.abspath(values['stage_dir'][0]) if values['stage_dir'][0] else '',
        'pack': os.path.abspath(values['pack_dir'][0]) if values['pack_dir'][0] else '',
        'backup': os.path.abspath(values['backup_dir'][0]) if values['backup_dir'][0] else '',
    }
    paths['map_json'] = os.path.join(paths['pack'], 'office-new.tmj')
    paths['map_png'] = os.path.join(paths['pack'], 'office-new-final.png')
    _require_app(paths['app'])
    _require_esbuild(paths['esbuild'])
    return paths, {key: value[1] for key, value in values.items()}


def dry_run(paths, sources):
    assets = os.path.join(paths['stage'], 'assets')
    print('干跑模式：路径校验通过，不会写入任何文件。')
    print('  app      : %s [%s]' % (paths['app'], sources['app_dir']))
    print('  esbuild  : %s [%s]' % (paths['esbuild'], sources['esbuild']))
    print('  stage    : %s [%s]' % (paths['stage'], sources['stage_dir']))
    print('  pack     : %s [%s]' % (paths['pack'], sources['pack_dir']))
    print('  将读取   : %s' % paths['map_json'])
    print('  将读取   : %s' % paths['map_png'])
    print('  将修改   : %s' % os.path.join(assets, 'OfficeFloor-*.js'))
    print('  将写入   : %s' % os.path.join(assets, 'office-new.png'))
    print('  将备份到 : %s' % paths['backup'])


def syntax_gate(path, esbuild):
    """用 esbuild 解析该 bundle；有语法错误就返回错误文本。"""
    with tempfile.TemporaryDirectory(prefix='starhive-esbuild-') as temp_dir:
        result = subprocess.run(
            [esbuild, '--log-level=error',
             '--outfile=' + os.path.join(temp_dir, 'gate.js'),
             '--allow-overwrite', path],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        detail = (result.stderr or result.stdout or '未知语法错误').strip()[:1200]
        raise InstallError('esbuild 语法门未通过：%s\n%s' % (path, detail))
    print('  esbuild 语法门: 通过')


def main():
    assets = os.path.join(STAGE, 'assets')
    fj = [f for f in os.listdir(assets) if f.startswith('OfficeFloor-') and f.endswith('.js')][0]
    fp = os.path.join(assets, fj)
    t = open(fp, encoding='utf-8').read()
    orig = t

    map_raw = open(MAP_JSON, encoding='utf-8').read().strip()
    json.loads(map_raw)
    assert "'" not in map_raw, '地图 JSON 含单引号'

    # 1) 地图
    m = re.search(r"const officeMapRaw = '([^']*)';", t)
    if not m:
        sys.exit('找不到 officeMapRaw')
    t = t[:m.start(1)] + map_raw + t[m.end(1):]

    # 2) tilesets（只匹配「后面紧跟 primarySeatNames 的那一个」= office 主题）
    g = re.search(r"tilesets: \[\n(?:.*?\n)*?  \],\n  primarySeatNames: \[", t)
    if not g:
        sys.exit('找不到 office 主题的 tilesets 块')
    t = (t[:g.start()]
         + 'tilesets: [\n    { url: "./assets/office-new.png", embedded: true }\n  ],\n  primarySeatNames: ['
         + t[g.end():])

    # 3) primarySeatNames（紧随其后的那一个）
    h = re.search(r"primarySeatNames: \[\n(?:.*?\n)*?  \],", t)
    if not h:
        sys.exit('找不到 primarySeatNames')
    block = 'primarySeatNames: [\n' + ''.join('    "%s",\n' % s for s in SEATS).rstrip(',\n') + '\n  ],'
    t = t[:h.start()] + block + t[h.end():]

    open(fp, 'w', encoding='utf-8', newline='\n').write(t)

    # L. 按 agent id 固定分座（primarySeatNames 的序号：0=老板 1=workbuddy 2=claude 3=codex 4=dsh 5=exec 6=approve 7=fix）
    seat_old = """        for (let i2 = 1; i2 < seatTiles.length; i2++) {
          if (!seatClaims.has(i2)) {
            seatClaims.add(i2);
            return i2;
          }
        }"""
    seat_new = """        {const __mdSeatMap = { 'workbuddy-mv135oq0': 1, 'codex-mv2h4arh': 3, 'harness-mv3d0001': 4,
                              'tianshu-mv3d0002': 5, 'tianshu-approve-mv3e02': 6, 'tianshu-fix-mv3e03': 7 };
         const __fixed = __mdSeatMap[agent.id];
         if (__fixed !== undefined && __fixed < seatTiles.length && !seatClaims.has(__fixed)) {
           seatClaims.add(__fixed);
           return __fixed;
         }}
        for (let i2 = 1; i2 < seatTiles.length; i2++) {
          if (!seatClaims.has(i2)) {
            seatClaims.add(i2);
            return i2;
          }
        }"""
    if t.count(seat_old) != 1:
        sys.exit('分座锚点异常 %d' % t.count(seat_old))
    t = t.replace(seat_old, seat_new, 1)
    open(fp, 'w', encoding='utf-8', newline='\n').write(t)   # L 的改动要落盘（它在原保存之后）
    print('  L 已注入固定分座')

    # P. god（月桥）坐老板椅时面朝我们（原逻辑按"北边有家具就背对我们"）
    face_old = 'seatDirection: facingForSeat(seatTile),'
    face_new = 'seatDirection: agent.isGod ? "down" : facingForSeat(seatTile), /*__mdGodFacing*/'
    if t.count(face_old) != 1:
        sys.exit('座位朝向锚点异常 %d' % t.count(face_old))
    t = t.replace(face_old, face_new, 1)
    open(fp, 'w', encoding='utf-8', newline='\n').write(t)
    print('  P 月桥朝向 -> down')

    # 图集进 assets
    shutil.copy2(MAP_PNG, os.path.join(assets, 'office-new.png'))

    # 校验
    err = syntax_gate(fp)
    print('  esbuild 语法门:', '通过' if err is None else '失败 →\n' + err)
    if err:
        open(fp, 'w', encoding='utf-8', newline='\n').write(orig)
        sys.exit('已回滚该文件（语法门未通过）')

    t2 = open(fp, encoding='utf-8').read()
    checks = [
        ('地图已换', '"width":48' in t2 and '"tilewidth":32' in t2),
        ('图集引用', './assets/office-new.png' in t2),
        ('座位表', '"desk-workbuddy"' in t2 and '"desk-fix"' in t2),
        ('角色补丁仍在', '__mdCustomFrames' in t2),
        ('月桥朝向', '__mdGodFacing' in t2),
        ('固定分座', '__mdSeatMap' in t2),
        ('单引号安全', t2.count("const officeMapRaw = '") == 1),
    ]
    for label, ok in checks:
        print('  %-14s %s' % (label, 'OK' if ok else 'FAIL'))
    if not all(ok for _, ok in checks):
        sys.exit('自检失败')
    print('地图补丁完成（已过语法门）')


if __name__ == '__main__':
    main()
