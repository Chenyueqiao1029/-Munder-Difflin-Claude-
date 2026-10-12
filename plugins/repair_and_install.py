# -*- coding: utf-8 -*-
"""修复 profile 的 cordis.patch.yml：清掉之前追加的 tianshu 块，恢复成合法 YAML，再幂等重装。
   · 清法：从 '# ==== dsh-subagent-tianshu' 标记起整段删除；若剩余为空则写回 '[]'
   · 然后调用 install_tianshu_plugin.py 重装（合并逻辑已修正为"单文档"）
用法：python repair_and_install.py [--profiles headless,desktop-canary] [--boot]
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALLER = os.path.join(HERE, 'install_tianshu_plugin.py')
MARK = '# ==== dsh-subagent-tianshu'
STAMP = time.strftime('%Y%m%d-%H%M%S')


def clean(patchf):
    if not os.path.exists(patchf):
        return '不存在'
    t = io.open(patchf, encoding='utf-8').read()
    if MARK not in t:
        return '无需清理'
    shutil.copy2(patchf, patchf + '.preclean-' + STAMP)
    head = t.split(MARK)[0].rstrip()
    # head 里可能还残留空行与旧 '[]'
    if head.strip() in ('', '[]', '---'):
        out = '[]\n'
    else:
        out = head + '\n'
    io.open(patchf, 'w', encoding='utf-8', newline='\n').write(out)
    return '已清理（新内容前 40 字: %r）' % out[:40]


def yaml_ok(path):
    try:
        import yaml
    except Exception:
        return None
    try:
        d = yaml.safe_load(io.open(path, encoding='utf-8').read())
        n = 0
        if isinstance(d, list):
            for e in d:
                if isinstance(e, dict) and 'insert' in e:
                    n += len(e['insert'])
        return n
    except Exception as e:
        return 'ERR: %s' % str(e)[:80]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profiles', default='headless,desktop-canary')
    ap.add_argument('--boot', action='store_true')
    a = ap.parse_args()
    for p in [x.strip() for x in a.profiles.split(',') if x.strip()]:
        prof = os.path.join(os.path.expanduser('~'), '.dsh', 'profiles', p)
        patchf = os.path.join(prof, 'cordis.patch.yml')
        print('== %s ==' % p)
        print('  清理: %s' % clean(patchf))
        r = subprocess.run([sys.executable, INSTALLER, '--profile', p, '--apply'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        for line in (r.stdout or '').split('\n'):
            if any(k in line for k in ('已写入', '已包含', '加载成功', '加载失败', '退出码', '已复制')):
                print('  ' + line.strip())
        print('  YAML 校验（insert 条目数）: %s' % yaml_ok(patchf))
    if a.boot:
        print('== 真启动（headless 任务）==')
        r = subprocess.run(['dsh', '--profile', 'headless', 'headless', '只回复两个字：正常'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace',
                           shell=True, timeout=600)
        out = (r.stdout or '') + (r.stderr or '')
        for line in out.split('\n'):
            if line.strip():
                print('   ' + line.strip()[:160])
        print('  退出码: %s' % r.returncode)
    return 0


if __name__ == '__main__':
    sys.exit(main())
