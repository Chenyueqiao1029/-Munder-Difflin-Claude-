# -*- coding: utf-8 -*-
"""按星宿给三个天枢星域分配人设（写进 roster 的 name/role —— app 会把 role 注入系统提示），
并在各自 hive 目录写一份 persona 说明，确保三个星域彼此独立、可区分。"""
import json
import os
import shutil
import time

HOME = r'C:\Users\徐\yueqiaochangetheworld'
ROSTER = os.path.join(HOME, 'roster.json')
AG = os.path.join(HOME, 'hive', 'agents')

PERSONA = {
    'tianshu-mv3d0002': (
        '天枢·执行星域',
        '天枢集群·执行星域（星宿：天梁 · 锚点之道）｜分段落地、分步开发、进度与产出。'
        '职责：把任务拆成可交付的锚点，逐段交付并给出可复现的产出路径。'
    ),
    'tianshu-approve-mv3e02': (
        '天枢·审批星域',
        '天枢集群·审批星域（星宿：瑶光 · 复现之道）｜第一层统一审批+验收；Codex 缺席时代行终审。'
        '职责：独立复现对方的结论，只认可复现的证据，不认口头结论。'
    ),
    'tianshu-fix-mv3e03': (
        '天枢·纠错星域',
        '天枢集群·纠错星域（星宿：辅 · 诊断之道）｜Bug 排查、逻辑修正、细节润色。'
        '职责：按诊断阶梯定位根因，先证伪再修，修完给出回归证据。'
    ),
}
INSTR = '''# 星域人设（独立身份，不要与其它星域混同）

- 星域名：{star}
- 主题：{theme}
- 角色：{role}

你与本办公室其它天枢星域**共用同一个天枢底座，但彼此完全独立**：各有自己的工作目录、
收件箱、记忆与系统提示。汇报时一律署名「{name} | {star}」，不要冒用其它星域的名字。
'''

STAR = {
    'tianshu-mv3d0002': ('天梁', '锚点之道（交付锚定）'),
    'tianshu-approve-mv3e02': ('瑶光', '复现之道（独立复现验证）'),
    'tianshu-fix-mv3e03': ('辅', '诊断之道（根因定位）'),
}

shutil.copy2(ROSTER, ROSTER + '.bak-persona-' + time.strftime('%Y%m%d-%H%M%S'))
d = json.load(open(ROSTER, encoding='utf-8'))
for key in ('agents', 'restorable'):
    for a in (d.get(key) or []):
        if isinstance(a, dict) and a.get('id') in PERSONA:
            name, role = PERSONA[a['id']]
            a['name'] = name
            a['role'] = role
json.dump(d, open(ROSTER, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

for aid, (star, theme) in STAR.items():
    name, role = PERSONA[aid]
    p = os.path.join(AG, aid, 'persona.md')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(INSTR.format(star=star, theme=theme, role=role, name=name))
    print('  %-24s -> %s（%s）  已写 persona.md' % (aid, star, theme))
print('  花名册 name/role 已更新')
for a in d['agents']:
    print('    %-24s %s' % (a.get('id'), a.get('name')))
