"""Keep each office terminal on its own persisted CLI conversation."""
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).with_name('terminal-sessions')
_ID = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]{7,127}$')


def _path(agent):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', agent):
        raise ValueError('invalid agent id')
    return ROOT / (agent + '.json')


def load(agent, provider):
    try:
        data = json.loads(_path(agent).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    sid = data.get('sessionId') if data.get('provider') == provider else None
    return sid if isinstance(sid, str) and _ID.fullmatch(sid) else None


def save(agent, provider, session_id):
    if not isinstance(session_id, str) or not _ID.fullmatch(session_id):
        return False
    path = _path(agent)
    path.parent.mkdir(exist_ok=True)
    temp = path.with_suffix('.json.tmp.' + str(os.getpid()))
    temp.write_text(json.dumps({'provider': provider, 'sessionId': session_id}), encoding='utf-8')
    os.replace(temp, path)
    return True


def session_from_line(line):
    try:
        event = json.loads(line)
    except (ValueError, TypeError):
        return None
    if not isinstance(event, dict):
        return None
    sid = event.get('sessionId') or event.get('session_id')
    return sid if isinstance(sid, str) and _ID.fullmatch(sid) else None


def prepare(argv, agent):
    """Insert verified resume flags before launching a new headless turn."""
    name = Path(argv[0]).stem.lower()
    if name == 'dsh':
        sid = load(agent, 'dsh')
        return argv[:-1] + (['--session-id', sid] if sid else []) + argv[-1:], 'dsh'
    if name == 'tianshu-agent':
        sid = load(agent, 'tianshu')
        return argv + (['--resume', sid] if sid else ['--new']), 'tianshu'
    return argv, None
