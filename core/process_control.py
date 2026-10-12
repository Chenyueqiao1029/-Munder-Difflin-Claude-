"""Inspect and interrupt only a verified engine child of an office PTY."""
import json
import os
import re
import subprocess
import threading
import time

_lock = threading.Lock()
_cache = {'until': 0, 'rows': []}
_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
_PS = ("Get-CimInstance Win32_Process | "
       "Select-Object ProcessId,ParentProcessId,Name,CommandLine | "
       "ConvertTo-Json -Compress -Depth 2")


def _processes(fresh=False):
    with _lock:
        if not fresh and _cache['until'] > time.time():
            return _cache['rows']
        result = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', _PS],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding='utf-8', errors='replace', timeout=12,
                                creationflags=_NO_WINDOW)
        if result.returncode:
            raise RuntimeError('process query failed')
        rows = json.loads(result.stdout or '[]')
        if isinstance(rows, dict):
            rows = [rows]
        _cache.update(until=time.time() + 2, rows=rows)
        return rows


def _office_chain(agent, rows):
    by_pid = {r.get('ProcessId'): r for r in rows if isinstance(r, dict)}
    app_pids = {r['ProcessId'] for r in rows if isinstance(r, dict)
                and r.get('Name') == 'Munder Difflin.exe'
                and '--type=' not in (r.get('CommandLine') or '')
                and 'Munder-Difflin-0.5.5-fixed' in (r.get('CommandLine') or '')}
    pattern = re.compile(r'md-chat\.cmd\s+' + re.escape(agent) + r'(?=\s|"|$)', re.I)
    roots = [r for r in rows if isinstance(r, dict) and r.get('Name') == 'cmd.exe'
             and r.get('ParentProcessId') in app_pids
             and pattern.search(r.get('CommandLine') or '')]
    if len(roots) != 1:
        return None, []
    root = roots[0]
    repls = [r for r in rows if isinstance(r, dict)
             and r.get('ParentProcessId') == root['ProcessId']
             and r.get('Name') in ('python.exe', 'pythonw.exe')
             and 'md-chat-launch.py' in (r.get('CommandLine') or '')
             and re.search(r'\b' + re.escape(agent) + r'\b', r.get('CommandLine') or '')]
    if len(repls) != 1:
        return root, []
    repl = repls[0]
    engines = [r for r in rows if isinstance(r, dict)
               and r.get('ParentProcessId') == repl['ProcessId']
               and r.get('Name') in ('cmd.exe', 'node.exe', 'codex.exe', 'dsh.exe',
                                      'tianshu-agent.exe', 'codebuddy.exe')
               and 'native_event_bridge.cjs' not in (r.get('CommandLine') or '')]
    return repl, engines


def status(agent):
    owner, engines = _office_chain(agent, _processes())
    return {'agent': agent, 'connected': owner is not None,
            'running': len(engines) == 1,
            'processes': [{'pid': x['ProcessId'], 'name': x.get('Name') or 'engine'}
                          for x in engines]}


def interrupt(agent):
    owner, engines = _office_chain(agent, _processes(fresh=True))
    if owner is None or len(engines) != 1:
        return {'ok': False, 'reason': 'no single verified active engine'}
    target = engines[0]
    pid = target['ProcessId']
    result = subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, encoding='utf-8', errors='replace', timeout=12,
                            creationflags=_NO_WINDOW)
    _cache['until'] = 0
    return {'ok': result.returncode == 0, 'pid': pid,
            'reason': 'interrupted' if result.returncode == 0 else 'process already ended or access denied'}
