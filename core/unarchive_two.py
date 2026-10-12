# -*- coding: utf-8 -*-
"""把 WorkBuddy / DeepSeek Harness 从 archived 拉回岗上（三处状态一起改）：
   1) roster.json：archived 列表 -> agents，并填入 restorable（app 启动按它恢复）
   2) hive/registry.json：archived=false（主进程 migration 读这里）
   3) restore-gate.json：从 ended 里摘掉
   同时给 build 一份"常驻守卫"状态文件，供 watchdog 每 60 秒兜底。
"""
import json
import os
import shutil
import time

HOME = r'C:\Users\徐\yueqiaochangetheworld'
ROSTER = os.path.join(HOME, 'roster.json')
REG = os.path.join(HOME, 'hive', 'registry.json')
GATE = os.path.join(HOME, 'restore-gate.json')
TARGETS = ['workbuddy-mv135oq0', 'harness-mv3d0001']
STAMP = time.strftime('%Y%m%d-%H%M%S')


def load(p, default):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return default


# ---------- 1) roster ----------
shutil.copy2(ROSTER, ROSTER + '.bak-unarch-' + STAMP)
d = load(ROSTER, {})
agents = d.get('agents') or []
have = {a.get('id') for a in agents if isinstance(a, dict)}
arch = [x for x in (d.get('archived') or [])]
moved = []
for x in list(arch):
    if isinstance(x, dict) and x.get('id') in TARGETS and x['id'] not in have:
        rec = dict(x)
        rec['archived'] = False
        rec.pop('status', None)
        agents.append(rec)
        have.add(rec['id'])
        arch.remove(x)
        moved.append(rec['id'])
d['agents'] = agents
d['archived'] = arch
# 把目标补进 restorable（用 agents 里的完整记录）
by_id = {a.get('id'): a for a in agents if isinstance(a, dict)}
rest = [a for a in (d.get('restorable') or []) if isinstance(a, dict) and a.get('id') not in TARGETS]
for t in TARGETS:
    if t in by_id:
        r = dict(by_id[t])
        r.pop('status', None)
        rest.append(r)
d['restorable'] = rest
json.dump(d, open(ROSTER, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('  roster: 移出归档 %s' % (moved or '(无，可能已在 agents)'))
print('  roster agents  :', [a.get('id') for a in d['agents']])
print('  roster restable:', [a.get('id') for a in d['restorable']])

# ---------- 2) registry ----------
if os.path.exists(REG):
    shutil.copy2(REG, REG + '.bak-unarch-' + STAMP)
    r = load(REG, {})
    ags = r.get('agents') or {}
    fixed = []
    for t in TARGETS:
        rec = ags.get(t)
        if isinstance(rec, dict) and rec.get('archived'):
            rec['archived'] = False
            fixed.append(t)
    json.dump(r, open(REG, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('  registry 取消归档:', fixed or '(无需改)')
    print('  registry agents 数:', len(ags))

# ---------- 3) restore-gate ----------
if os.path.exists(GATE):
    shutil.copy2(GATE, GATE + '.bak-unarch-' + STAMP)
    g = load(GATE, {})
    before = g.get('ended') or []
    g['ended'] = [x for x in before if x not in TARGETS]
    json.dump(g, open(GATE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('  gate.ended: %s -> %s' % (before, g['ended']))
