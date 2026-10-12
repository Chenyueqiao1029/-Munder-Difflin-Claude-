# -*- coding: utf-8 -*-
"""常驻守卫：每 60 秒检查 7 名员工是否都在岗；有掉线就先修状态（roster/registry/gate）
   再整体重启 office（用既有的脱离式启动器）。全程静默、不弹窗。

用法：python watchdog.py           常驻
     python watchdog.py --once    只跑一轮
"""
import argparse
import json
import os
import subprocess
import sys
import time
# --- md-nowindow: 所有子进程不弹黑窗 ---
import subprocess as _mdsp
_md_run, _md_popen = _mdsp.run, _mdsp.Popen


def _md_wrap(fn):
    def _f(*a, **k):
        if os.name == 'nt':
            k.setdefault('creationflags', 0x08000000)  # CREATE_NO_WINDOW
        return fn(*a, **k)
    return _f


_mdsp.run, _mdsp.Popen = _md_wrap(_md_run), _md_wrap(_md_popen)
# --- /md-nowindow ---


HERE = os.path.dirname(os.path.abspath(__file__))
HIVE = r'C:\Users\徐\yueqiaochangetheworld\hive'
ROSTER = r'C:\Users\徐\yueqiaochangetheworld\roster.json'
STATE = os.path.join(HERE, 'watchdog-state.json')
LOG = os.path.join(HERE, 'watchdog.log')
STOP = os.path.join(HERE, 'watchdog-stop.flag')
ROLES = ['god', 'workbuddy-mv135oq0', 'harness-mv3d0001', 'tianshu-mv3d0002',
         'tianshu-approve-mv3e02', 'tianshu-fix-mv3e03', 'codex-mv2h4arh']
# All seven seats now run the md-chat wrapper. Checking node.exe and the old
# engine names falsely declared every seat dead and restarted the entire office.
NEED = {aid: 'md-chat.cmd ' + aid for aid in ROLES if aid != 'codex-mv2h4arh'}


def log(msg):
    line = '[%s] %s' % (time.strftime('%H:%M:%S'), msg)
    print(line, flush=True)
    try:
        with open(LOG, 'a', encoding='utf-8') as fh:
            fh.write(line + '\n')
    except Exception:
        pass


def procs():
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command',
                            "Get-CimInstance Win32_Process -Filter \"Name='cmd.exe' OR Name='Munder Difflin.exe'\" | "
                            "Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Compress"],
                           capture_output=True, text=True, timeout=90)
        rows = json.loads(r.stdout or '[]')
        if isinstance(rows, dict):
            rows = [rows]
        roots = {p.get('ProcessId') for p in rows
                 if p.get('Name') == 'Munder Difflin.exe'
                 and '--type=' not in (p.get('CommandLine') or '')
                 and 'Munder-Difflin-0.5.5-fixed' in (p.get('CommandLine') or '')}
        return '\n'.join((p.get('CommandLine') or '') for p in rows
                         if p.get('Name') == 'cmd.exe' and p.get('ParentProcessId') in roots)
    except Exception:
        return ''


def missing():
    out = procs()
    gone = []
    for aid, pat in NEED.items():
        if pat not in out:
            gone.append(aid)
    return gone


def fix_state():
    try:
        subprocess.run([sys.executable, os.path.join(HERE, 'unarchive_two.py')],
                       capture_output=True, text=True, timeout=120)
    except Exception as e:
        log('修状态失败: %s' % e)
    # 确保 restorable 覆盖全部 7 人
    try:
        d = json.load(open(ROSTER, encoding='utf-8'))
        by = {a.get('id'): a for a in (d.get('agents') or []) if isinstance(a, dict)}
        rest = [a for a in (d.get('restorable') or []) if isinstance(a, dict)]
        have = {a.get('id') for a in rest}
        add = 0
        for aid in ROLES:
            if aid == 'god':
                continue
            if aid in by and aid not in have:
                r = dict(by[aid]); r.pop('status', None)
                rest.append(r); add += 1
        d['restorable'] = rest
        json.dump(d, open(ROSTER, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        if add:
            log('restorable 补齐 %d 人' % add)
    except Exception as e:
        log('补 restorable 失败: %s' % e)


def restart_office():
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, 'start_office_detached.py')],
                           capture_output=True, text=True, timeout=600)
        tail = (r.stdout or '').strip().splitlines()[-3:]
        log('已重启 office: %s' % ' | '.join(tail))
    except Exception as e:
        log('重启失败: %s' % e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--once', action='store_true')
    a = ap.parse_args()
    state = {'fail': 0}
    while True:
        if os.path.exists(STOP):
            log('发现停止标记，退出')
            return
        gone = missing()
        if gone:
            log('掉线: %s' % gone)
            state['fail'] += 1
            if state['fail'] >= 2:
                # 用户明确要求：关掉就是关掉 —— 永不自动重启 office，只修状态并报告
                fix_state()
                log('（自动重启已禁用：需要时请手动运行 启动办公室.cmd）')
                state['fail'] = 0
            else:
                log('再观察一轮')
        else:
            if state['fail']:
                log('已全员在岗')
            state['fail'] = 0
        try:
            json.dump(state, open(STATE, 'w', encoding='utf-8'))
        except Exception:
            pass
        if a.once:
            return
        time.sleep(60)


if __name__ == '__main__':
    main()
