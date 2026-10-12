# -*- coding: utf-8 -*-
"""星域蜂巢 · 路径配置层（让开源项目在**别人的机器**上也能跑）。

解析顺序（先命中先用）：
  1) 环境变量：MD_APP_DIR / MD_STAGE_DIR / MD_PACK_DIR / MD_ESBUILD / MD_RENDERER_DIR / MD_BACKUP_DIR
  2) 仓库根 config.json（{"app_dir": "...", ...}）
  3) 自动探测（在常见位置找 Munder Difflin 的 resources\\app\\out）
  4) 内置默认（相对仓库自身，尽量能不依赖外部 app）

用法：
  from md_config import cfg                 # 取单个值
  from md_config import resolve             # 取全部 + 每个值的来源
  python tools/md_config.py                 # 打印当前解析结果与来源
  python tools/md_config.py --write         # 生成 config.json 模板（不覆盖已有）
  python tools/md_config.py --check         # 只检查 app 是否定位成功（找不到退出码 2）
"""
import argparse
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CONFIG = os.path.join(REPO, 'config.json')

ENV_KEYS = {
    'app_dir': 'MD_APP_DIR',
    'stage_dir': 'MD_STAGE_DIR',
    'pack_dir': 'MD_PACK_DIR',
    'esbuild': 'MD_ESBUILD',
    'renderer_dir': 'MD_RENDERER_DIR',
    'backup_dir': 'MD_BACKUP_DIR',
}

# 自动探测：这些位置里找 app 根目录（含 resources\app\out 或 Munder*.exe）
CANDIDATE_GLOBS = [
    r'D:\徐\MunderDifflin\*',
    r'D:\MunderDifflin\*',
    r'C:\MunderDifflin\*',
    os.path.join(os.path.expanduser('~'), 'MunderDifflin', '*'),
    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', '*Munder*'),
    os.path.join(os.environ.get('PROGRAMFILES', ''), '*Munder*'),
]


def _looks_like_app(p):
    if not p or not os.path.isdir(p):
        return False
    if os.path.isdir(os.path.join(p, 'resources', 'app', 'out')):
        return True
    if glob.glob(os.path.join(p, '*.exe')) and os.path.isdir(os.path.join(p, 'resources')):
        return True
    return False


def detect_app_dir():
    for pat in CANDIDATE_GLOBS:
        for p in sorted(glob.glob(pat)):
            if _looks_like_app(p):
                # 若命中一个含"fixed"的目录，优先（本机就是这么装的）
                return p
    return ''


def detect_esbuild():
    pats = [
        os.path.join(REPO, 'node_modules', '.pnpm', '@esbuild+win32-x64*', 'node_modules', '@esbuild', 'win32-x64', 'esbuild.exe'),
        r'D:\徐\_ref\munder-difflin-src\node_modules\.pnpm\@esbuild+win32-x64@0.21.5\node_modules\@esbuild\win32-x64\esbuild.exe',
        os.path.join(os.path.expanduser('~'), '_ref', 'munder-difflin-src', 'node_modules', '.pnpm',
                     '@esbuild+win32-x64*', 'node_modules', '@esbuild', 'win32-x64', 'esbuild.exe'),
    ]
    for pat in pats:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[0]
    return ''


def _from_config_file():
    if not os.path.exists(CONFIG):
        return {}
    try:
        return json.load(io.open(CONFIG, encoding='utf-8')) or {}
    except Exception:
        return {}


def resolve():
    """返回 {键: (值, 来源)}。"""
    filecfg = _from_config_file()
    out = {}
    app = ''

    # app_dir
    if os.environ.get(ENV_KEYS['app_dir']):
        app, src = os.environ[ENV_KEYS['app_dir']], 'env:' + ENV_KEYS['app_dir']
    elif filecfg.get('app_dir'):
        app, src = filecfg['app_dir'], 'config.json'
    else:
        app = detect_app_dir()
        src = 'auto-detect' if app else 'not-found'
    out['app_dir'] = (app, src)

    # 其它键：env -> config -> 由 app_dir 推导 -> 仓库内默认
    def pick(key, default_fn):
        if os.environ.get(ENV_KEYS[key]):
            return os.environ[ENV_KEYS[key]], 'env:' + ENV_KEYS[key]
        if filecfg.get(key):
            return filecfg[key], 'config.json'
        v = default_fn()
        return v, ('derived' if v else 'not-found')

    out['stage_dir'] = pick('stage_dir', lambda: os.path.join(app, '_renderer-patched') if app else '')
    out['pack_dir'] = pick('pack_dir', lambda: os.path.join(REPO, 'pack'))
    out['renderer_dir'] = pick('renderer_dir', lambda: os.path.join(app, 'resources', 'app', 'out', 'renderer')
                               if app and os.path.isdir(os.path.join(app, 'resources', 'app', 'out', 'renderer')) else '')
    out['backup_dir'] = pick('backup_dir', lambda: os.path.join(REPO, 'backups'))
    out['esbuild'] = pick('esbuild', detect_esbuild)
    return out


_cache = None


def cfg(key, default=''):
    global _cache
    if _cache is None:
        _cache = resolve()
    if key == 'repo':
        return REPO
    return (_cache.get(key) or ('', ''))[0] or default


def cfg_with_source(key):
    global _cache
    if _cache is None:
        _cache = resolve()
    return _cache.get(key, ('', 'not-found'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true', help='生成 config.json 模板（已有则不覆盖）')
    ap.add_argument('--check', action='store_true', help='只检查 app 是否定位成功')
    a = ap.parse_args()
    r = resolve()
    print('星域蜂巢 · 路径配置')
    print('  仓库: %s' % REPO)
    for k in ('app_dir', 'stage_dir', 'pack_dir', 'renderer_dir', 'backup_dir', 'esbuild'):
        v, s = r[k]
        print('  %-13s %-58s  [%s]' % (k, (v or '（未找到）')[:58], s))
    if a.check:
        ok = bool(r['app_dir'][0])
        print('  app 定位: %s' % ('成功 ✓' if ok else '失败 ✗ —— 请设环境变量 MD_APP_DIR 或写进 config.json'))
        return 0 if ok else 2
    if a.write:
        if os.path.exists(CONFIG):
            print('  config.json 已存在，不覆盖：%s' % CONFIG)
            return 0
        tpl = {k: r[k][0] for k in ('app_dir', 'stage_dir', 'pack_dir', 'renderer_dir', 'backup_dir', 'esbuild')}
        tpl['_说明'] = '星域蜂巢路径配置；改这里即可适配你自己的安装位置。环境变量 MD_* 优先级更高。'
        io.open(CONFIG, 'w', encoding='utf-8', newline='\n').write(json.dumps(tpl, ensure_ascii=False, indent=2))
        print('  已生成 %s' % CONFIG)
    return 0


if __name__ == '__main__':
    sys.exit(main())
