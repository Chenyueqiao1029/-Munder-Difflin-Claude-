# -*- coding: utf-8 -*-
"""① 建 md-chat.cmd 包装（app 的 agent command 用它）  ② 把 7 名员工的 command 换成对话终端"""
import json
import os
import shutil
import time
from pathlib import Path

NPM = os.path.join(os.environ.get('APPDATA', ''), 'npm')
ROSTER = r'C:\Users\徐\yueqiaochangetheworld\roster.json'
STAMP = time.strftime('%Y%m%d-%H%M%S')

# ① 包装：纯 cmd（非 npm 形状 → app 走 cmd.exe，行式 REPL 完全没问题）
here = Path(__file__).resolve().parent
cmd = (here / 'md-chat.cmd.template').read_bytes()
if any(b > 127 for b in cmd):
    raise SystemExit('md-chat wrapper must be ASCII; use the Python launcher for Unicode paths')
p = os.path.join(NPM, 'md-chat.cmd')
shutil.copy2(p, p + '.bak-' + STAMP) if os.path.exists(p) else None
with open(p, 'wb') as fh:
    fh.write(cmd)
shutil.copy2(here / 'md-chat-launch.py', os.path.join(NPM, 'md-chat-launch.py'))
print('  已写', p, os.path.getsize(p), 'B')

# ② 花名册：把 command 换成 md-chat <id>
shutil.copy2(ROSTER, ROSTER + '.bak-chatcmd-' + STAMP)
d = json.load(open(ROSTER, encoding='utf-8'))
changed = []
for key in ('agents', 'restorable'):
    for a in (d.get(key) or []):
        if not isinstance(a, dict):
            continue
        aid = a.get('id')
        if aid in ('god', 'workbuddy-mv135oq0', 'harness-mv3d0001', 'tianshu-mv3d0002',
                   'tianshu-approve-mv3e02', 'tianshu-fix-mv3e03', 'codex-mv2h4arh'):
            new = 'md-chat %s' % aid
            if a.get('command') != new:
                changed.append((aid, a.get('command'), new))
                a['command'] = new
json.dump(d, open(ROSTER, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('  已改 command:')
for aid, old, new in changed:
    print('    %-24s %s → %s' % (aid, (old or '')[:34], new))
