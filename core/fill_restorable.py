# -*- coding: utf-8 -*-
"""把 6 名员工的完整配置填进 roster.restorable，让 app 启动时自动恢复它们。"""
import glob
import json
import os
import shutil
import time

H = r'C:\Users\徐\yueqiaochangetheworld'
ROSTER = os.path.join(H, 'roster.json')
WANT = ['workbuddy-mv135oq0', 'codex-mv2h4arh', 'harness-mv3d0001',
        'tianshu-mv3d0002', 'tianshu-approve-mv3e02', 'tianshu-fix-mv3e03']

# 找一份含全部 7 个 agent 完整字段的备份
cands = sorted(glob.glob(os.path.join(H, 'roster.json.bak-*')), key=os.path.getmtime, reverse=True)
best = None
for c in cands:
    try:
        d = json.load(open(c, encoding='utf-8'))
    except Exception:
        continue
    ids = {a.get('id') for a in (d.get('agents') or [])}
    if all(w in ids for w in WANT):
        best = (c, d)
        break
if not best:
    raise SystemExit('找不到含 7 名员工完整字段的备份')
print('  采用备份:', os.path.basename(best[0]))

src = {a['id']: a for a in best[1]['agents']}
cur = json.load(open(ROSTER, encoding='utf-8'))
shutil.copy2(ROSTER, ROSTER + '.bak-restorable-' + time.strftime('%Y%m%d-%H%M%S'))

# agents 保留 7 个（god + 6）
have = {a.get('id') for a in (cur.get('agents') or [])}
for w in WANT:
    if w not in have and w in src:
        a = dict(src[w]); a['archived'] = False
        cur.setdefault('agents', []).append(a)
        have.add(w)

# restorable 填 6 个（完整字段）
rest = []
for w in WANT:
    a = dict(src.get(w) or {})
    if not a:
        continue
    a['archived'] = False
    a.pop('status', None)
    rest.append(a)
cur['restorable'] = rest
json.dump(cur, open(ROSTER, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('  agents     :', [a.get('id') for a in cur['agents']])
print('  restorable :', [a.get('id') for a in cur['restorable']])
for a in cur['restorable']:
    print('    %-24s cmd=%-34s cwd=%s' % (a.get('id'), (a.get('command') or '')[:34], a.get('cwd')))
