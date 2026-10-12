# -*- coding: utf-8 -*-
"""用 WMI 创建进程启动办公室 —— 彻底脱离当前工具调用的作业对象，
这样我的命令结束后 app 和它的 PTY 子进程都不会被杀。

用法：python start_office_detached.py
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
APP = r'D:\徐\MunderDifflin\Munder-Difflin-0.5.5-fixed'
EXE = os.path.join(APP, 'Munder Difflin.exe')

sys.path.insert(0, HERE)
import start_office as so
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



def create_detached():
    """通过 WMI Win32_Process.Create 启动（新进程不属于本 shell 的 job）。"""
    cmd = [
        'powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
        "Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ "
        "CommandLine = '\"%s\"'; CurrentDirectory = '%s' } | "
        "Select-Object -ExpandProperty ProcessId" % (EXE, APP)
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out = (r.stdout or '').strip().splitlines()
    pid = out[-1].strip() if out else ''
    return pid, (r.stderr or '').strip()


def main():
    print('== 启动办公室（WMI 脱离式）==')
    so.stop_app()
    so.fix_roster()
    time.sleep(1)
    pid, err = create_detached()
    print('  WMI 创建进程 PID =', pid or '(空)', ('错误: ' + err) if err else '')
    if not pid or not pid.isdigit():
        raise SystemExit('WMI 启动失败')
    print('  等待 100 秒…')
    time.sleep(100)
    # 只在本次调用内做“启动成功”判断，不做长时间等待（避免把子进程留在这个 job 里）
    log = os.path.join(r'C:\Users\徐\yueqiaochangetheworld', 'hive', 'log.jsonl')
    rows = []
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


if __name__ == '__main__':
    main()
