# -*- coding: utf-8 -*-
"""总监督（单个进程管两个后台）：
   - 拉起并守护 agent_driver2.py（投递）与 watchdog.py（7 人在岗）
   - 每 60 秒巡检，子进程死了就拉起来；终端绑定由 app 的 U2 原生修复维护
   - 单实例（pid 文件）
用法：python supervisor.py [--once]
"""
import argparse
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
PIDF = os.path.join(HERE, 'supervisor.pid')
LOG = os.path.join(HERE, 'supervisor.log')
PY = sys.executable


def log(m):
    line = '[%s] %s' % (time.strftime('%H:%M:%S'), m)
    print(line, flush=True)
    try:
        with open(LOG, 'a', encoding='utf-8') as fh:
            fh.write(line + '\n')
    except Exception:
        pass


def alive(pid):
    try:
        out = subprocess.run(['tasklist', '/FI', 'PID eq %d' % pid], capture_output=True, text=True).stdout
        return str(pid) in out
    except Exception:
        return False


def children():
    out = {}
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command',
                            "Get-CimInstance Win32_Process | Where-Object { $_.Name -in "
                            "@('python.exe','pythonw.exe') -and $_.CommandLine } | "
                            "ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }"],
                           capture_output=True, text=True, timeout=60)
        for line in (r.stdout or '').splitlines():
            if '|' not in line:
                continue
            pid, cmd = line.split('|', 1)
            try:
                pid = int(pid.strip())
            except Exception:
                continue
            if 'agent_driver2.py' in cmd:
                out['driver'] = pid
            elif 'watchdog.py' in cmd:
                out['watchdog'] = pid
            elif 'md_chat.py' in cmd:
                out['chat'] = pid
    except Exception:
        pass
    return out


def spawn(script, *args):
    env = dict(os.environ)
    env.pop('ELECTRON_RUN_AS_NODE', None)
    try:
        p = subprocess.Popen([PY, os.path.join(HERE, script), *args], cwd=HERE, env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=0x00000008 | 0x00000200)  # DETACHED_PROCESS|NEW_PROCESS_GROUP
        log('拉起 %s pid=%d' % (script, p.pid))
        return p.pid
    except Exception as e:
        log('拉起 %s 失败: %s' % (script, e))
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--once', action='store_true')
    a = ap.parse_args()
    # 单实例
    if os.path.exists(PIDF):
        try:
            old = int(open(PIDF).read().strip())
            if old != os.getpid() and alive(old):
                log('已有 supervisor 在跑 pid=%d，退出' % old)
                return
        except Exception:
            pass
    open(PIDF, 'w').write(str(os.getpid()))
    log('supervisor 启动 pid=%d' % os.getpid())
    while True:
        ch = children()
        if 'driver' not in ch:
            spawn('agent_driver2.py', '--interval', '10')
        if 'watchdog' not in ch:
            spawn('watchdog.py')
        if 'chat' not in ch:
            spawn('md_chat.py')
        # U2: only the app knows which PTYs exist. Do not fabricate IDs or race
        # its roster writer. Keep supervising driver/watchdog as before.
        if a.once:
            return
        time.sleep(60)


if __name__ == '__main__':
    main()
