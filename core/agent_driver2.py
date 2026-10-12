# -*- coding: utf-8 -*-
r"""星域驱动 v2 —— 用各引擎【原生无头通道】投递（替代 app 的盲打，25% -> 接近 100%）。

  rivet（天枢三域） : tianshu-agent --goal "<任务>" --budget N --skip-welcome --dangerously-skip-permissions
  DSH              : dsh --profile headless headless "<任务>"
  Codex            : codex exec --dangerously-bypass-approvals-and-sandbox -m gpt-6-astra "<任务>"
  WorkBuddy        : codebuddy -p --dangerously-skip-permissions --output-format stream-json "<任务>"

只处理【新邮件】：处理成功的邮件移到 inbox/.driver-done/<ts>/（驱动侧归档，不写 act:done 消息）。
每轮输出写入 <项目>\员工\<星域名>\终端.log；状态写入 driver-status.json 供看板使用。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import threading
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from task_ledger import TaskLedger
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
HOME = r'C:\Users\徐\yueqiaochangetheworld'
HIVE = os.path.join(HOME, 'hive')
PROJ = os.path.join(HIVE, 'projects', 'YQC-6-员工被回收排查')
STATE = os.path.join(HERE, 'driver-state.json')
STATUS = os.path.join(HERE, 'driver-status.json')
STOP = os.path.join(HERE, 'driver-stop.flag')
MIN_GAP = 3600   # 同一员工两次投递最小间隔（秒）
MAX_PER_HOUR = 3  # 同一员工每小时最多投递次数
STREAMS = os.path.join(HERE, 'streams')
LEDGER = os.path.join(HERE, 'task-ledger.sqlite3')
LOCK = os.path.join(HERE, 'agent-driver.lock')
NPM = os.path.join(os.environ.get('APPDATA', ''), 'npm')

AGENTS = {
    'tianshu-mv3d0002': {
        'name': '天枢·执行星域（天梁·锚点之道）', 'out': '天枢执行星域',
        'cmd': ['tianshu-agent', '--goal', '{prompt}', '--budget', '4', '--stream-json', '--skip-welcome', '--dangerously-skip-permissions'],
        'timeout': 420,
    },
    'tianshu-approve-mv3e02': {
        'name': '天枢·审批星域（瑶光·复现之道）', 'out': '天枢审批星域',
        'cmd': ['tianshu-agent', '--goal', '{prompt}', '--budget', '4', '--stream-json', '--skip-welcome', '--dangerously-skip-permissions'],
        'timeout': 420,
    },
    'tianshu-fix-mv3e03': {
        'name': '天枢·纠错星域（辅·诊断之道）', 'out': '天枢纠错星域',
        'cmd': ['tianshu-agent', '--goal', '{prompt}', '--budget', '4', '--stream-json', '--skip-welcome', '--dangerously-skip-permissions'],
        'timeout': 420,
    },
    'harness-mv3d0001': {
        'name': 'DeepSeek Harness', 'out': 'dsh',
        'cmd': ['dsh', '--profile', 'headless', 'headless', '--json', '{prompt}'],
        'timeout': 420,
    },
    'codex-mv2h4arh': {
        'name': 'Codex（执行总裁）', 'out': 'codex',
        'cmd': ['codex', 'exec', '--json', '--dangerously-bypass-approvals-and-sandbox', '-m', 'gpt-6-astra', '{prompt}'],
        'timeout': 420,
    },
    'workbuddy-mv135oq0': {
        'name': 'WorkBuddy', 'out': 'WorkBuddy',
        'cmd': ['codebuddy', '-p', '--dangerously-skip-permissions', '--output-format', 'stream-json', '{prompt}'],
        'timeout': 420,
    },
}

PROMPT = (
    '你是{name}。只处理以下一封任务邮件，不扫描其他收件箱或重读全部 memory/persona。'
    '先检查指定产物是否已有；只做缺少的部分。最多一次执行；到时交出完成状态、证据或卡点。'
    '不得操作 E:\\Downloads\\lingshu-server；不得写 act="done"；汇报最多三行。\n'
    '任务键：{key}\n验收条件：{done_when}\n指定产物：{evidence}\n'
    '邮件：{mail}\n产物建议目录：{outdir}'
)


def resolve(binname):
    for cand in (os.path.join(NPM, binname + '.cmd'), os.path.join(NPM, binname + '.exe')):
        if os.path.exists(cand):
            return cand
    return binname


@contextmanager
def single_instance():
    """Keep one inbox consumer per office even if supervisor starts twice."""
    with open(LOCK, 'a+b') as fh:
        fh.seek(0, os.SEEK_END)
        if fh.tell() == 0:
            fh.write(b'0')
            fh.flush()
        fh.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        try:
            yield True
        finally:
            if os.name == 'nt':
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def load(p, default):
    try:
        with open(p, encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return default


def save(p, obj):
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, p)


def inbox_ids(aid):
    d = os.path.join(HIVE, 'agents', aid, 'inbox')
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.endswith('.json'))


def archive_mail(aid, ids, tag):
    """把已处理的邮件移到 inbox/.driver-done/<ts>/（驱动侧归档）。"""
    if not ids:
        return 0
    d = os.path.join(HIVE, 'agents', aid, 'inbox')
    dst = os.path.join(d, '.driver-done', tag)
    os.makedirs(dst, exist_ok=True)
    n = 0
    for f in ids:
        src = os.path.join(d, f)
        if os.path.exists(src):
            try:
                shutil.move(src, os.path.join(dst, f))
                n += 1
            except Exception:
                pass
    return n


def run_one(aid, cfg, state, ledger, force=False):
    ids = inbox_ids(aid)
    seen = set(state.get(aid, {}).get('seen', []))
    fresh = [i for i in ids if i not in seen]
    if not fresh:
        return 'idle'
    st0 = state.setdefault(aid, {})
    runs = [r for r in st0.get('runs', []) if r > time.time() - 3600]
    if len(runs) >= MAX_PER_HOUR:
        return 'idle'
    selected = None
    skipped = 'idle'
    for mail_id in fresh:
        mail_path = os.path.join(HIVE, 'agents', aid, 'inbox', mail_id)
        try:
            mail = load(mail_path, None)
            if not isinstance(mail, dict):
                skipped = 'invalid_mail'
                continue
            card = ledger.card(aid, mail)
        except (ValueError, TypeError) as exc:
            skipped = 'invalid_mail:' + str(exc)
            continue
        claim = ledger.claim(card)
        if claim == 'duplicate':
            moved = archive_mail(aid, [mail_id], time.strftime('%Y%m%d-%H%M%S'))
            if moved:
                st0['seen'] = sorted(set(st0.get('seen', [])) | {mail_id})
            st0['archived'] = st0.get('archived', 0) + moved
            skipped = 'duplicate'
            continue
        if claim == 'claimed':
            selected = (mail_id, mail, card)
            break
        skipped = claim
    if selected is None:
        return skipped
    mail_id, mail, card = selected
    outdir = os.path.join(PROJ, '员工', cfg['out'])
    os.makedirs(outdir, exist_ok=True)
    log = os.path.join(outdir, '终端.log')
    prompt = PROMPT.format(name=cfg['name'], key=card['dedupe_key'], done_when=card['done_when'],
                           evidence=json.dumps(card['evidence'], ensure_ascii=False),
                           mail=json.dumps({k: v for k, v in mail.items() if k != 'task'},
                                           ensure_ascii=False), outdir=outdir)
    cmd = [c.format(prompt=prompt) for c in cfg['cmd']]
    cmd[0] = resolve(cmd[0])
    env = dict(os.environ)
    env.pop('ELECTRON_RUN_AS_NODE', None)
    env['RIVET_TRUST_PROJECT'] = '1'
    if aid == 'harness-mv3d0001':
        # Windows ACL SACL edit fails without SeSecurityPrivilege in this user token.
        # DSH's own full-access mode skips that edit; scope it to this child only.
        env['DSH_PERMISSION_MODE'] = 'danger-full-access'
    started = time.time()
    from native_hook_bridge import HookBridge
    bridge = HookBridge(HIVE, aid)
    os.makedirs(STREAMS, exist_ok=True)
    stream_path = os.path.join(STREAMS, aid + '.log')
    usage = {'input_tokens': 0, 'cache_read_tokens': 0, 'output_tokens': 0,
             'total_tokens': 0}
    rivet_turns = {}
    timed_out = threading.Event()
    budget_stop = threading.Event()
    with open(log, 'a', encoding='utf-8', errors='replace') as fh, open(
            stream_path, 'a', encoding='utf-8', errors='replace') as live:
        def emit(line):
            fh.write(line)
            fh.flush()
            live.write(line)
            live.flush()
            if line.startswith('{'):
                try:
                    event = json.loads(line)
                    raw = event.get('usage', {})
                    if isinstance(raw, dict) and event.get('type') == 'turn_complete':
                        # Rivet emits both provisional and final usage for the same turn.
                        rivet_turns[event.get('turn', len(rivet_turns) + 1)] = raw
                        usage['input_tokens'] = sum(int(x.get('input_tokens', 0)) for x in rivet_turns.values())
                        usage['cache_read_tokens'] = sum(int(x.get('cache_read_input_tokens', 0)) for x in rivet_turns.values())
                        usage['output_tokens'] = sum(int(x.get('output_tokens', 0)) for x in rivet_turns.values())
                        usage['total_tokens'] = usage['input_tokens'] + usage['output_tokens']
                    elif isinstance(raw, dict) and event.get('phase') == 'step_end':
                        # DSH reports cache reads separately from uncached input.
                        usage['input_tokens'] += int(raw.get('inputTokens', 0))
                        usage['cache_read_tokens'] += int(raw.get('cacheReadTokens', 0))
                        usage['output_tokens'] += int(raw.get('outputTokens', 0))
                        usage['total_tokens'] = sum(usage[k] for k in ('input_tokens', 'cache_read_tokens', 'output_tokens'))
                    elif isinstance(raw, dict) and event.get('type') in ('turn.completed', 'usage'):
                        usage['input_tokens'] += int(raw.get('input_tokens', 0))
                        usage['cache_read_tokens'] += int(raw.get('cached_input_tokens', 0))
                        usage['output_tokens'] += int(raw.get('output_tokens', 0))
                        usage['total_tokens'] = usage['input_tokens'] + usage['output_tokens']
                except (ValueError, TypeError, AttributeError):
                    pass
        emit('[后台派发] %s 开始处理 %s\n' % (time.strftime('%H:%M:%S'), mail_id))
        try:
            p = subprocess.Popen(cmd, cwd=os.path.join(HOME, 'hive'), env=env,
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                                 errors='replace', bufsize=1)
            bridge.start()
            def expire():
                timed_out.set()
                if p.poll() is None:
                    p.kill()
            timer = threading.Timer(min(cfg['timeout'], card['budget']['wall_seconds']), expire)
            timer.start()
            tail = ''
            try:
                for line in p.stdout:
                    bridge.line(line)
                    emit(line)
                    tail = (tail + line)[-400:]
                    if usage['total_tokens'] >= card['budget']['max_tokens'] and p.poll() is None:
                        budget_stop.set()
                        p.kill()
                        break
                p.wait()
            finally:
                timer.cancel()
                bridge.finish(failed=timed_out.is_set() or budget_stop.is_set() or p.poll() != 0)
            ok = p.returncode == 0 and not timed_out.is_set() and not budget_stop.is_set()
            emit('[后台派发] %s 结束；退出码 %s；耗时 %ds%s\n' % (
                time.strftime('%H:%M:%S'), p.returncode, int(time.time() - started),
                '；超时' if timed_out.is_set() else ('；token 上限' if budget_stop.is_set() else '')))
        except Exception as e:
            emit('[后台派发] 异常 %s\n' % e)
            ok, tail = False, str(e)
    failure = ('token budget exceeded' if budget_stop.is_set() else
               'wall time exceeded' if timed_out.is_set() else tail[-300:])
    done, reason = ledger.finish(card, ok, HIVE, '' if ok else failure)
    moved = archive_mail(aid, [mail_id], time.strftime('%Y%m%d-%H%M%S')) if done else 0
    st = state.setdefault(aid, {})
    if moved:
        st['seen'] = sorted(set(st.get('seen', [])) | {mail_id})
    st['lastRun'] = started
    st['lastOk'] = done
    st['pending'] = len(inbox_ids(aid))
    st['archived'] = st.get('archived', 0) + moved
    st['tail'] = tail[-300:]
    st['usageLast'] = usage
    st.setdefault('runs', [])
    st['runs'] = ([r for r in st['runs'] if r > time.time() - 3600]) + [time.time()]
    return 'ran' if done else 'failed:' + reason[:80]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--once', action='store_true')
    ap.add_argument('--force', action='store_true', help='legacy flag; does not bypass safety limits')
    ap.add_argument('--only', default='')
    ap.add_argument('--interval', type=int, default=10)
    ap.add_argument('--dry-run', action='store_true', help='inspect pending tasks without starting agents')
    a = ap.parse_args()
    state = load(STATE, {})
    ledger = TaskLedger(LEDGER)
    targets = {k: v for k, v in AGENTS.items() if not a.only or k in a.only.split(',')}
    if a.dry_run:
        for aid in targets:
            seen = set(state.get(aid, {}).get('seen', []))
            for name in inbox_ids(aid):
                if name in seen:
                    continue
                mail = load(os.path.join(HIVE, 'agents', aid, 'inbox', name), {})
                try:
                    card = ledger.card(aid, mail)
                    previous = ledger.get(card['dedupe_key'])
                    waiting = any((ledger.get(key) or ('queued',))[0] != 'done'
                                  for key in card['depends_on'])
                    print('%s | %s | %s | %s' % (aid, card['dedupe_key'],
                                                 'waiting_dependency' if waiting else
                                                 (previous[0] if previous else 'queued'),
                                                 (mail.get('subject') or '')[:80]))
                except (ValueError, TypeError, AttributeError) as exc:
                    print('%s | invalid mail | %s' % (aid, exc))
        return
    print('[driver2] 启动，目标 %d 人，间隔 %ds' % (len(targets), a.interval), flush=True)
    while True:
        if os.path.exists(STOP):
            print('[driver2] 停止标记，退出', flush=True)
            return
        status = load(STATUS, {})
        # Independent agents can run together; never overlap runs for one owner.
        with ThreadPoolExecutor(max_workers=min(3, len(targets) or 1)) as pool:
            jobs = {aid: pool.submit(run_one, aid, cfg, state, ledger, a.force)
                    for aid, cfg in targets.items()}
            results = {aid: job.result() for aid, job in jobs.items()}
        save(STATE, state)
        for aid, cfg in targets.items():
            res = results[aid]
            pend = len(inbox_ids(aid))
            status[aid] = {'name': cfg['name'], 'state': res, 'pending': pend,
                           'lastRun': state.get(aid, {}).get('lastRun'),
                           'lastOk': state.get(aid, {}).get('lastOk'),
                           'usageLast': state.get(aid, {}).get('usageLast', {}),
                           'archived': state.get(aid, {}).get('archived', 0)}
            if res != 'idle':
                print('[driver2] %-24s %-6s 待处理 %d' % (aid, res, pend), flush=True)
        status['_updated'] = time.time()
        save(STATUS, status)
        if a.once:
            return
        time.sleep(a.interval)


if __name__ == '__main__':
    with single_instance() as acquired:
        if acquired:
            main()
        else:
            print('[driver2] 另一个实例已经运行，退出', flush=True)
