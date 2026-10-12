# -*- coding: utf-8 -*-
"""给每个员工分配独立工作目录（app 按 cwd/会话归属，共用目录会导致星域串台），
并把 rivet 配置复制到新目录，保证引擎仍能登录。"""
import json
import os
import shutil
import time

HOME = r'C:\Users\徐\yueqiaochangetheworld'
ROSTER = os.path.join(HOME, 'roster.json')
BASE = r'D:\徐\agent'
SRC_RIVET = os.path.join(BASE, '.rivet')

CWDS = {
    'god': os.path.join(BASE, 'yueqiao'),
    'tianshu-mv3d0002': os.path.join(BASE, 'tianshu-exec'),
    'tianshu-approve-mv3e02': os.path.join(BASE, 'tianshu-approve'),
    'tianshu-fix-mv3e03': os.path.join(BASE, 'tianshu-fix'),
    'harness-mv3d0001': os.path.join(BASE, 'harness'),
    'codex-mv2h4arh': os.path.join(BASE, 'codex'),
    'workbuddy-mv135oq0': os.path.join(BASE, 'workbuddy'),
}

for aid, cwd in CWDS.items():
    os.makedirs(cwd, exist_ok=True)
    # rivet 配置（登录态）复制过去
    dst = os.path.join(cwd, '.rivet')
    if os.path.isdir(SRC_RIVET) and not os.path.exists(dst):
        try:
            shutil.copytree(SRC_RIVET, dst)
            print('  rivet 配置 -> %s' % cwd)
        except Exception as e:
            print('  rivet 复制失败 %s: %s' % (cwd, e))
    else:
        print('  目录就绪 %s' % cwd)

shutil.copy2(ROSTER, ROSTER + '.bak-cwd-' + time.strftime('%Y%m%d-%H%M%S'))
d = json.load(open(ROSTER, encoding='utf-8'))
for key in ('agents', 'restorable'):
    for a in (d.get(key) or []):
        if isinstance(a, dict) and a.get('id') in CWDS:
            old = a.get('cwd')
            a['cwd'] = CWDS[a['id']]
            if key == 'agents':
                print('  %-24s %s -> %s' % (a['id'], old, a['cwd']))
json.dump(d, open(ROSTER, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('  花名册 cwd 已更新')
