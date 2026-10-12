"""Read account level quota data for the office. Never return credentials."""
import json
import os
from pathlib import Path
import threading
import time
import urllib.error
import urllib.request

_lock = threading.Lock()
_cache = {}


def _codex():
    roots = [Path.home() / '.codex' / 'sessions',
             Path.home() / 'yueqiaochangetheworld' / 'hive' / 'agents' /
             'codex-mv2h4arh' / '.codex' / 'sessions']
    files = sorted((p for root in roots if root.exists() for p in root.rglob('*.jsonl')),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:12]
    latest = None
    for path in files:
        try:
            with path.open('rb') as fh:
                fh.seek(max(0, path.stat().st_size - 2_000_000))
                if fh.tell():
                    fh.readline()
                lines = fh.readlines()
            for raw in reversed(lines):
                try:
                    row = json.loads(raw)
                    rate = row.get('payload', {}).get('rate_limits') or {}
                    if rate.get('limit_id') != 'codex' or not rate.get('primary'):
                        continue
                    stamp = row.get('timestamp', '')
                    if not latest or stamp > latest[0]:
                        latest = stamp, rate
                    break
                except (ValueError, AttributeError, TypeError):
                    continue
        except OSError:
            continue
    if not latest:
        return {'kind': 'unavailable', 'label': 'Codex 额度暂无本机数据'}
    stamp, rate = latest
    def window(item):
        if not item:
            return None
        used = item.get('used_percent')
        return {'remainingPercent': round(max(0, 100 - float(used)), 1) if used is not None else None,
                'resetsAt': item.get('resets_at'), 'windowMinutes': item.get('window_minutes')}
    return {'kind': 'codex', 'label': 'Codex 账号共享额度', 'sampleAt': stamp,
            'primary': window(rate.get('primary')), 'secondary': window(rate.get('secondary')),
            'plan': rate.get('plan_type')}


def _deepseek_key():
    key = os.environ.get('DEEPSEEK_API_KEY', '')
    if key:
        return key
    if os.name == 'nt':
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as reg:
                return winreg.QueryValueEx(reg, 'DEEPSEEK_API_KEY')[0]
        except (OSError, ImportError):
            pass
    return ''


def _deepseek():
    key = _deepseek_key()
    if not key:
        return {'kind': 'unavailable', 'label': 'DeepSeek API Key 未配置'}
    req = urllib.request.Request('https://api.deepseek.com/user/balance',
                                 headers={'Authorization': 'Bearer ' + key,
                                          'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.load(response)
        balances = [{'currency': x.get('currency'), 'total': x.get('total_balance')}
                    for x in data.get('balance_infos', [])]
        return {'kind': 'deepseek', 'label': 'DeepSeek API 账号共享余额',
                'sampleAt': time.time(), 'available': data.get('is_available'),
                'balances': balances}
    except urllib.error.HTTPError as exc:
        return {'kind': 'unavailable', 'label': 'DeepSeek 余额查询失败', 'error': 'HTTP %s' % exc.code}
    except (OSError, ValueError) as exc:
        return {'kind': 'unavailable', 'label': 'DeepSeek 余额暂不可读',
                'error': type(exc).__name__}


def quotas():
    now = time.time()
    with _lock:
        if _cache.get('until', 0) > now:
            return _cache['data']
        data = {'codex': _codex(), 'deepseek': _deepseek(),
                'workbuddy': {'kind': 'unavailable', 'label': 'WorkBuddy 未提供可读额度接口'}}
        _cache.update(data=data, until=now + 60)
        return data


def for_agent(aid):
    data = quotas()
    if aid == 'codex-mv2h4arh':
        return data['codex']
    if aid == 'workbuddy-mv135oq0':
        return data['workbuddy']
    if aid in ('god', 'harness-mv3d0001', 'tianshu-mv3d0002',
               'tianshu-approve-mv3e02', 'tianshu-fix-mv3e03'):
        return data['deepseek']
    return {'kind': 'unavailable', 'label': '未知智能体'}
