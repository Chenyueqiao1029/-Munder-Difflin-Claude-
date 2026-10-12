# -*- coding: utf-8 -*-
"""一眼看：现在有没有人在干活。
判据（都取实测数据，不看界面）：
  1) 最近 15 分钟有没有新产出文件
  2) 最近 15 分钟有没有 agent 之间/给人类的消息
  3) 每个人的收件箱待办（>0 = 有活等着他）
  4) 各引擎进程是否在跑
输出：第一行给结论；下面逐人一行。退出码 0=有人干活，1=没人在干活。
"""
import json
import os
import subprocess
import sys
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HOME = r'C:\Users\徐\yueqiaochangetheworld'
HIVE = os.path.join(HOME, 'hive')
AG = os.path.join(HIVE, 'agents')
PROJ = os.path.join(HIVE, 'projects')
WIN = 900  # 15 分钟
NAMES = {
    'god': '月桥', 'workbuddy-mv135oq0': 'WorkBuddy', 'tanshu': '天枢',
    'tianshu-mv3d0002': '天枢·执行星域', 'tianshu-approve-mv3e02': '天枢·审批星域',
    'tianshu-fix-mv3e03': '天枢·纠错星域', 'codex-mv2h4arh': 'Codex',
    'harness-mv3d0001': 'DeepSeek Harness',
}
now = time.time()

# 1) 新产出
new_files = []
for root, _d, fs in os.walk(PROJ):
    for f in fs:
        p = os.path.join(root, f)
        try:
            if now - os.path.getmtime(p) < WIN:
                new_files.append((os.path.getmtime(p), os.path.relpath(p, PROJ)))
        except Exception:
            pass
new_files.sort(reverse=True)

# 2) 新消息
new_msgs = []
try:
    for line in open(os.path.join(HIVE, 'log.jsonl'), encoding='utf-8', errors='replace'):
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get('kind') == 'message' and o.get('ts', 0) / 1000 > now - WIN:
            new_msgs.append(o)
except Exception:
    pass

# 3) 待办
def backlog(aid):
    d = os.path.join(AG, aid, 'inbox')
    if not os.path.isdir(d):
        return 0
    return len([f for f in os.listdir(d) if f.endswith('.json')])

aid_list = []
try:
    _r = json.load(open(os.path.join(HOME, 'roster.json'), encoding='utf-8'))
    aid_list = [a.get('id') for a in (_r.get('agents') or []) if isinstance(a, dict) and a.get('id')]
except Exception:
    aid_list = [a for a in os.listdir(AG) if os.path.isdir(os.path.join(AG, a)) and '.old-' not in a]

# 4) 进程
def procs():
    try:
        script = ("Get-CimInstance Win32_Process | Where-Object { "
                  "$_.Name -in @('python.exe','pythonw.exe','node.exe','codex.exe','codebuddy.exe') "
                  "-and $_.CommandLine -match 'tianshu-agent|dsh.*headless|codex exec|codebuddy -p' "
                  "} | Select-Object -ExpandProperty ProcessId")
        r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', script],
                           capture_output=True, text=True, timeout=15,
                           creationflags=0x08000000 if os.name == 'nt' else 0)
        return [int(s) for s in r.stdout.splitlines() if s.strip().isdigit()]
    except Exception:
        return []


active_pids = procs()

working = bool(active_pids)

print('=' * 64)
if working:
    print('  ✅ 现在【有引擎或驱动在运行】（PID: %s）' % ', '.join(map(str, active_pids)))
else:
    print('  ⏸  现在【没有办公室引擎或驱动在运行】')
    if any(backlog(a) > 0 for a in aid_list):
        print('     ⚠️ 但有人的收件箱堆着活没动（下面标「有活等着」的那些）')
print('=' * 64)
print('  判据：最近 %d 分钟 → 新产出 %d 个 ｜ 新消息 %d 条 ｜ 有待办的人 %d 个'
      % (WIN // 60, len(new_files), len(new_msgs), sum(1 for a in aid_list if backlog(a) > 0)))
if new_files:
    print('  最新产出：')
    for mt, rel in new_files[:4]:
        print('    [%s] %s' % (time.strftime('%H:%M', time.localtime(mt)), rel))
if new_msgs:
    print('  最新消息：')
    for o in new_msgs[-4:]:
        print('    [%s] %s → %s：%s' % (time.strftime('%H:%M', time.localtime(o['ts'] / 1000)),
                                        o.get('from'), o.get('to'), (o.get('subject') or '')[:46]))
print('-' * 64)
print('  %-22s %-6s %s' % ('员工', '待办', '状态'))
for a in sorted(aid_list):
    b = backlog(a)
    label = '有活等着' if b else '空闲'
    print('  %-22s %-6d %s' % (NAMES.get(a, a), b, label))
print('-' * 64)
print('  办公室相关进程 PID：%s' % (', '.join(map(str, active_pids)) or '无'))
sys.exit(0 if working else 1)
