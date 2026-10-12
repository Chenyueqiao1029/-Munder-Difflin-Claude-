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

sys.dont_write_bytecode = True

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


def _backup_files(floor_path, image_path, backup_root):
    os.makedirs(backup_root, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    target = os.path.join(backup_root, 'map-' + stamp)
    os.makedirs(target)
    floor_backup = os.path.join(target, os.path.basename(floor_path))
    shutil.copy2(floor_path, floor_backup)
    image_backup = None
    if os.path.isfile(image_path):
        image_backup = os.path.join(target, os.path.basename(image_path))
        shutil.copy2(image_path, image_backup)
    print('修改前文件已备份:', target)
    return floor_backup, image_backup


def _rollback_files(floor_path, floor_backup, image_path, image_backup):
    shutil.copy2(floor_backup, floor_path)
    if image_backup:
        shutil.copy2(image_backup, image_path)
    elif os.path.exists(image_path):
        os.remove(image_path)
    print('安装失败，已恢复地图补丁前的文件。')


def install(paths):
    global _ROLLBACK
    STAGE = paths['stage']
    MAP_JSON = paths['map_json']
    MAP_PNG = paths['map_png']
    ESBUILD = paths['esbuild']
    BACKUP = paths['backup']
    if not STAGE:
        raise InstallError(
            '找不到补丁暂存目录。请设置 MD_STAGE_DIR，或在 config.json 中填写 stage_dir。')
    if not paths['pack']:
        raise InstallError(
            '找不到地图素材目录配置。请设置 MD_PACK_DIR，或在 config.json 中填写 pack_dir。')
    if not BACKUP:
        raise InstallError(
            '找不到备份目录配置。请设置 MD_BACKUP_DIR，或在 config.json 中填写 backup_dir。')
    assets = os.path.join(STAGE, 'assets')
    if not os.path.isdir(assets):
        raise InstallError(
            '找不到补丁目录的 assets：%s。请设置 MD_STAGE_DIR，'
            '或在 config.json 中填写 stage_dir。' % assets)
    if not os.path.isfile(MAP_JSON) or not os.path.isfile(MAP_PNG):
        raise InstallError(
            '缺少地图素材。请设置 MD_PACK_DIR，或在 config.json 中填写 pack_dir；'
            '该目录应包含 office-new.tmj 与 office-new-final.png。')
    floor_files = sorted(
        f for f in os.listdir(assets)
        if f.startswith('OfficeFloor-') and f.endswith('.js'))
    if not floor_files:
        raise InstallError('找不到 OfficeFloor-*.js：%s' % assets)
    fj = floor_files[0]
    fp = os.path.join(assets, fj)
    t = open(fp, encoding='utf-8').read()

    map_raw = open(MAP_JSON, encoding='utf-8').read().strip()
    json.loads(map_raw)
    if "'" in map_raw:
        raise InstallError('地图 JSON 含单引号，不能安全嵌入 officeMapRaw')

    # 1) 地图
    m = re.search(r"const officeMapRaw = '([^']*)';", t)
    if not m:
        raise InstallError('找不到 officeMapRaw 锚点')
    t = t[:m.start(1)] + map_raw + t[m.end(1):]

    # 2) tilesets（只匹配「后面紧跟 primarySeatNames 的那一个」= office 主题）
    g = re.search(r"tilesets: \[\n(?:.*?\n)*?  \],\n  primarySeatNames: \[", t)
    if not g:
        raise InstallError('找不到 office 主题的 tilesets 块')
    t = (t[:g.start()]
         + 'tilesets: [\n    { url: "./assets/office-new.png", embedded: true }\n  ],\n  primarySeatNames: ['
         + t[g.end():])

    # 3) primarySeatNames（紧随其后的那一个）
    h = re.search(r"primarySeatNames: \[\n(?:.*?\n)*?  \],", t)
    if not h:
        raise InstallError('找不到 primarySeatNames')
    block = 'primarySeatNames: [\n' + ''.join('    "%s",\n' % s for s in SEATS).rstrip(',\n') + '\n  ],'
    t = t[:h.start()] + block + t[h.end():]

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
        raise InstallError('分座锚点异常 %d' % t.count(seat_old))
    t = t.replace(seat_old, seat_new, 1)
    print('  L 已注入固定分座')

    # P. god（月桥）坐老板椅时面朝我们（原逻辑按"北边有家具就背对我们"）
    face_old = 'seatDirection: facingForSeat(seatTile),'
    face_new = 'seatDirection: agent.isGod ? "down" : facingForSeat(seatTile), /*__mdGodFacing*/'
    if t.count(face_old) != 1:
        raise InstallError('座位朝向锚点异常 %d' % t.count(face_old))
    t = t.replace(face_old, face_new, 1)
    print('  P 月桥朝向 -> down')

    image_path = os.path.join(assets, 'office-new.png')
    if os.path.normcase(os.path.realpath(MAP_PNG)) == os.path.normcase(os.path.realpath(image_path)):
        raise InstallError('map_png 不能与目标 office-new.png 是同一文件；请调整 MD_PACK_DIR。')
    try:
        backup_inside_stage = os.path.commonpath(
            [os.path.realpath(BACKUP), os.path.realpath(STAGE)]
        ) == os.path.realpath(STAGE)
    except ValueError:
        backup_inside_stage = False
    if backup_inside_stage:
        raise InstallError(
            'backup_dir 不能位于 stage_dir 内；请设置 MD_BACKUP_DIR，'
            '或修改 config.json 中的 backup_dir。')

    floor_backup, image_backup = _backup_files(fp, image_path, BACKUP)
    _ROLLBACK = (fp, floor_backup, image_path, image_backup)
    with open(fp, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(t)
    shutil.copy2(MAP_PNG, image_path)

    # 校验
    syntax_gate(fp, ESBUILD)

    t2 = open(fp, encoding='utf-8').read()
    # 自检：尺寸**从新地图自己的 JSON 里读**，不再硬编码（用户自定义地图尺寸各不相同）
    try:
        new_map = json.loads(open(MAP_JSON, encoding='utf-8').read())
        want_w = str(new_map.get('width'))
        want_tw = str(new_map.get('tilewidth'))
    except Exception as exc:
        raise InstallError('读不出新地图 %s：%s' % (MAP_JSON, exc))
    checks = [
        ('地图已换', ('"width":%s' % want_w) in t2 and ('"tilewidth":%s' % want_tw) in t2),
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
        raise InstallError('自检失败')
    _ROLLBACK = None
    print('地图补丁完成（已备份并通过语法门）')


def main():
    parser = argparse.ArgumentParser(description='安装 StarHive Office 自定义地图补丁')
    parser.add_argument('--dry-run', action='store_true',
                        help='只校验 app 与 esbuild，并打印将修改的文件；不写任何文件')
    args = parser.parse_args()
    try:
        paths, sources = resolve_paths()
        if args.dry_run:
            dry_run(paths, sources)
        else:
            install(paths)
        return 0
    except Exception as exc:
        if _ROLLBACK:
            try:
                _rollback_files(*_ROLLBACK)
            except OSError as rollback_exc:
                print('错误：%s' % exc, file=sys.stderr)
                print('回滚也失败：%s' % rollback_exc, file=sys.stderr)
                return 3
        print('错误：%s' % exc, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
