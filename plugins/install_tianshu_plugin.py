# -*- coding: utf-8 -*-
"""把天枢委派插件装进 desktop-canary 影子 profile（不碰正式 desktop）。
   1) 备份 profile 的 package.json / cordis.patch.yml
   2) node_modules 下建 junction
   3) package.json：加 dependencies + dsh.profile.bundles
   4) 合并 cordis.patch.yml（把插件的四星域 insert 条目并进去）
   5) 在 node 里验证模块能被解析加载
用法：python install_tianshu_plugin.py [--profile desktop-canary] [--apply]
     不加 --apply 只预演（打印将要做的改动）
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import time

PLUGIN_SRC = r'D:\徐\星域蜂巢\plugins\dsh-subagent-tianshu'
PKG_NAME = '@starhive/dsh-subagent-tianshu'
STAMP = time.strftime('%Y%m%d-%H%M%S')


def log(s):
    print('  ' + s, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profile', default='desktop-canary')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    prof = os.path.join(os.path.expanduser('~'), '.dsh', 'profiles', a.profile)
    if not os.path.isdir(prof):
        log('✗ profile 不存在: %s' % prof)
        return 2
    pkgf = os.path.join(prof, 'package.json')
    patchf = os.path.join(prof, 'cordis.patch.yml')
    nm = os.path.join(prof, 'node_modules')
    scope = os.path.join(nm, '@starhive')
    target = os.path.join(scope, 'dsh-subagent-tianshu')

    log('目标 profile: %s' % prof)
    pkg = json.load(io.open(pkgf, encoding='utf-8')) if os.path.exists(pkgf) else {}
    deps = pkg.setdefault('dependencies', {})
    bundles = (pkg.get('dsh') or {}).get('profile', {}).get('bundles') or []
    log('现有 dependencies 里是否已有: %s' % (PKG_NAME in deps))
    log('现有 bundles 里是否已有: %s' % (PKG_NAME in bundles))
    log('将执行：')
    log('  1) 备份 package.json / cordis.patch.yml（.bak-tianshu-%s）' % STAMP)
    log('  2) 建 junction: %s -> %s' % (target, PLUGIN_SRC))
    log('  3) package.json: dependencies += %s，bundles += 同名' % PKG_NAME)
    log('  4) cordis.patch.yml: 追加四星域 insert 条目（若尚未包含）')
    log('  5) node 里验证模块可解析')
    if not a.apply:
        log('（预演结束；加 --apply 才真正写入）')
        return 0

    # 1) 备份
    for f in (pkgf, patchf):
        if os.path.exists(f):
            shutil.copy2(f, f + '.bak-tianshu-' + STAMP)
            log('已备份 %s' % os.path.basename(f))

    # 2) 复制插件进 node_modules
    #    注意：**不能用 junction** —— Node 会按 junction 的真实路径解析 import，
    #    于是找不到 profile 内的 peer 依赖（实测报 Cannot find package '@deepseek-ai/schemastery'）。
    if os.path.exists(target):
        log('目标已存在，先移除')
        try:
            if os.path.isdir(target) and not os.path.islink(target):
                shutil.rmtree(target)
            else:
                os.remove(target)
        except Exception as e:
            log('! 移除失败: %s' % e)
    shutil.copytree(PLUGIN_SRC, target, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.bak*', 'install_tianshu_plugin.py'))
    n = sum(len(fs) for _r, _d, fs in os.walk(target))
    log('已复制插件到 node_modules（%d 个文件）' % n)

    # 3) package.json
    deps[PKG_NAME] = 'file:' + PLUGIN_SRC
    if PKG_NAME not in bundles:
        bundles.append(PKG_NAME)
    pkg.setdefault('dsh', {}).setdefault('profile', {})['bundles'] = bundles
    io.open(pkgf, 'w', encoding='utf-8', newline='\n').write(json.dumps(pkg, ensure_ascii=False, indent=2))
    log('package.json 已更新（deps=%d, bundles=%d）' % (len(deps), len(bundles)))

    # 4) cordis.patch.yml
    src_patch = io.open(os.path.join(PLUGIN_SRC, 'cordis.patch.yml'), encoding='utf-8').read()
    body = '\n'.join(l for l in src_patch.split('\n') if not l.strip().startswith('#')).strip()
    old = io.open(patchf, encoding='utf-8').read() if os.path.exists(patchf) else ''
    if 'subagent-tianshu' in old:
        log('cordis.patch.yml 已包含 tianshu 条目，跳过')
    else:
        # 关键：整个文件必须是**一个 YAML 文档**。
        # 判断"是不是空列表"必须**忽略注释行**（profile 的文件常是「注释头 + []」）。
        code = '\n'.join(l for l in old.split('\n') if not l.strip().startswith('#')).strip()
        comments = '\n'.join(l for l in old.split('\n') if l.strip().startswith('#'))
        if code in ('', '[]', '---'):
            merged = (comments + '\n\n' if comments else '') + body + '\n'
            how = '注释头 + 空列表 → 保留注释、替换列表'
        else:
            merged = old.rstrip() + '\n\n# ==== dsh-subagent-tianshu（星域委派）====\n' + body + '\n'
            how = '非空列表 → 顶格并入同一列表'
        io.open(patchf, 'w', encoding='utf-8', newline='\n').write(merged)
        log('cordis.patch.yml 已写入（%s）' % how)

    # 5) node 解析验证（在 profile 目录里跑，才能解析到 peer 依赖）
    test = ("import('%s').then(m=>{console.log('  ✔ 模块加载成功: name='+m.name+' inject='+JSON.stringify(m.inject)+' 有apply='+(typeof m.apply));}).catch(e=>{console.log('  ✗ 加载失败: '+e.message);process.exit(1);});" % PKG_NAME)
    r = subprocess.run(['node', '--input-type=module', '-e', test], cwd=prof, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    log((r.stdout or '').strip() or (r.stderr or '').strip()[:300])
    log('node 验证退出码: %s' % r.returncode)
    return r.returncode


if __name__ == '__main__':
    sys.exit(main())
