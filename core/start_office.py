# -*- coding: utf-8 -*-
"""一键启动像素办公室：
  1) 停掉旧实例
  2) 把 6 名员工从 archived 移回 agents，并填进 restorable（app 启动时按它恢复）
  3) 清掉 restore-gate 里针对他们的封禁
  4) 拉起 app（带 DEEPSEEK_API_KEY）
  5) 等 90 秒并报告谁起来了
用法：python start_office.py
"""
import glob
import json
import os
import subprocess
import sys
import time
import winreg

HOME = r'C:\Users\徐\yueqiaochangetheworld'
ROSTER = os.path.join(HOME, 'roster.json')
GATE = os.path.join(HOME, 'restore-gate.json')
APP = r'D:\徐\MunderDifflin\Munder-Difflin-0.5.5-fixed'
EXE = os.path.join(APP, 'Munder Difflin.exe')
WANT = ['workbuddy-mv135oq0', 'codex-mv2h4arh', 'harness-mv3d0001',
        'tianshu-mv3d0002', 'tianshu-approve-mv3e02', 'tianshu-fix-mv3e03']


def stop_app():
    subprocess.run(['taskkill', '/F', '/IM', 'Munder Difflin.exe'], capture_output=True)
    time.sleep(5)


def full_records():
    """从任一含 7 名员工完整字段的备份里取记录。"""
    for c in sorted(glob.glob(ROSTER + '.bak-*'), key=os.path.getmtime, reverse=True):
        try:
            d = json.load(open(c, encoding='utf-8'))
        except Exception:
            continue
        ags = {a.get('id'): a for a in (d.get('agents') or [])}
        if all(w in ags for w in WANT):
            return ags
    raise SystemExit('找不到含完整字段的花名册备份')


def fix_roster():
    recs = full_records()
    d = json.load(open(ROSTER, encoding='utf-8'))
    agents = d.get('agents') or []
    have = {a.get('id') for a in agents}
    arch = [x for x in (d.get('archived') or []) if not (isinstance(x, dict) and x.get('id') in WANT)]
    for w in WANT:
        if w not in have:
            a = dict(recs[w]); a['archived'] = False
            agents.append(a); have.add(w)
    d['agents'] = agents
    d['archived'] = arch
    d['restorable'] = [dict(recs[w], archived=False) for w in WANT]
    for a in d['restorable']:
        a.pop('status', None)
    with open(ROSTER, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=2)
    if os.path.exists(GATE):
        g = json.load(open(GATE, encoding='utf-8'))
        g['ended'] = [x for x in (g.get('ended') or []) if x not in WANT]
        with open(GATE, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(g, fh, ensure_ascii=False, indent=2)
    print('  花名册: agents=%d restorable=%d' % (len(d['agents']), len(d['restorable'])))


def api_key():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as k:
            v, _ = winreg.QueryValueEx(k, 'DEEPSEEK_API_KEY')
            return v
    except Exception:
        return ''


def main():
    print('== 启动像素办公室 ==')
    stop_app()
    fix_roster()
    env = dict(os.environ)
    env.pop('ELECTRON_RUN_AS_NODE', None)
    key = api_key()
    if key:
        env['DEEPSEEK_API_KEY'] = key
    subprocess.Popen([EXE], cwd=APP, env=env, close_fds=True)
    print('  已拉起 app，等待员工上线…')
    time.sleep(90)
    # 报告
    log = os.path.join(HOME, 'hive', 'log.jsonl')
    rows = []
    if os.path.exists(log):
        for line in open(log, encoding='utf-8', errors='replace'):
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get('kind') == 'spawn':
                rows.append((time.strftime('%H:%M:%S', time.localtime(o['ts'] / 1000)), o.get('agentId')))
    print('  最近 spawn:')
    for r in rows[-9:]:
        print('    [%s] %s' % r)
    ps = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Munder Difflin.exe'],
                        capture_output=True, text=True).stdout
    print('  app 进程:', '在' if 'Munder' in ps else '不在')


if __name__ == '__main__':
    main()
