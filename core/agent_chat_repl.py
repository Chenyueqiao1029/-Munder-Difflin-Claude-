# -*- coding: utf-8 -*-
"""星域对话终端（REPL）—— 让办公室 app 的【终端标签】变成真正能对话的终端。

用法：md-chat <员工id>        （由 md-chat.cmd 包装，app 用它当 agent 的 command）
行为：像 claude / codex 那样一行一行聊；每次回答调用该员工自己的引擎（原生无头模式），
      保留它自己的记忆/人设/星域身份。

内置命令（直接输入）：/status 看它当前状态与收件箱；/help 帮助；exit 退出。
"""
import json
import os
import subprocess
import sys
import time
import threading
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    pass
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
if HERE not in sys.path:
    sys.path.insert(0, HERE)
HOME = r'C:\Users\徐\yueqiaochangetheworld'
HIVE = os.path.join(HOME, 'hive')
NPM = os.path.join(os.environ.get('APPDATA', ''), 'npm')
PROJ = os.path.join(HIVE, 'projects')
STREAMS = os.path.join(HERE, 'streams')

AGENTS = {
    'god': ('月桥', '老板室 · 调度', HOME,
            ['tianshu-agent', '-p', '{text}', '--stream-json', '--skip-welcome', '--dangerously-skip-permissions'],
            ['tianshu-agent', '--goal', '{task}', '--budget', '4', '--stream-json', '--skip-welcome', '--dangerously-skip-permissions']),
    'tianshu-mv3d0002': ('天枢·执行星域（天梁）', '交付锚点', HIVE,
                         ['tianshu-agent', '-p', '{text}', '--stream-json', '--skip-welcome', '--dangerously-skip-permissions'],
                          ['tianshu-agent', '--goal', '{task}', '--budget', '4', '--stream-json', '--skip-welcome', '--dangerously-skip-permissions']),
    'tianshu-approve-mv3e02': ('天枢·审批星域（瑶光）', '复现复核', HIVE,
                               ['tianshu-agent', '-p', '{text}', '--stream-json', '--skip-welcome', '--dangerously-skip-permissions'],
                                ['tianshu-agent', '--goal', '{task}', '--budget', '4', '--stream-json', '--skip-welcome', '--dangerously-skip-permissions']),
    'tianshu-fix-mv3e03': ('天枢·纠错星域（辅）', '根因诊断', HIVE,
                           ['tianshu-agent', '-p', '{text}', '--stream-json', '--skip-welcome', '--dangerously-skip-permissions'],
                            ['tianshu-agent', '--goal', '{task}', '--budget', '4', '--stream-json', '--skip-welcome', '--dangerously-skip-permissions']),
    'harness-mv3d0001': ('DeepSeek Harness', '统筹', HIVE,
                         ['dsh', '--profile', 'headless', 'headless', '--json', '{text}'],
                         ['dsh', '--profile', 'headless', 'headless', '--json', '{task}']),
    'codex-mv2h4arh': ('Codex', '执行总裁', HIVE,
                       ['codex', 'exec', '--json', '-m', 'gpt-6-astra', '{text}'],
                       ['codex', 'exec', '--json', '-m', 'gpt-6-astra', '{task}']),
    'workbuddy-mv135oq0': ('WorkBuddy', '杂务', HIVE,
                           ['codebuddy', '-p', '--output-format', 'stream-json', '--dangerously-skip-permissions', '{text}'],
                           ['codebuddy', '-p', '--output-format', 'stream-json', '--dangerously-skip-permissions', '{task}']),
}

HEAD = ('你是「{name}」（{role}），正在办公室终端里和人类老板**面对面**对话。'
        '用中文、口语化、直接回答他，不要说"我将代办"、不要写文件、不要发 act 消息、不要通报 god。'
        '老板说：{text}')
TASK = ('你是「{name}」（{role}）。老板在终端里给你下了指令：{text}\n'
        '请当场执行：需要时读你自己的记忆/收件箱，把结果直接说给老板听（可写产出到 {outdir}），'
        '完成后用 act="inform" 回给 god（不要写 act="done"）。')


def api_key():
    """从用户环境读 DEEPSEEK_API_KEY（app 启动时会给，独立跑时也要有）。"""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as k:
            v, _ = winreg.QueryValueEx(k, 'DEEPSEEK_API_KEY')
            return v
    except Exception:
        return ''


def resolve(b):
    for c in (os.path.join(NPM, b + '.cmd'), os.path.join(NPM, b + '.exe')):
        if os.path.exists(c):
            return c
    return b


_BUF = {'kind': None, 'text': ''}


def _flush():
    if _BUF['text'].strip():
        pre = '💭 ' if _BUF['kind'] == 'think' else '  '
        print(pre + _BUF['text'].strip(), flush=True)
    _BUF['kind'] = None
    _BUF['text'] = ''


def _add(kind, txt):
    if _BUF['kind'] != kind:
        _flush()
        _BUF['kind'] = kind
    _BUF['text'] += str(txt)


def render(line):
    """把引擎的事件流翻译成人话，实时打印（同类增量自动合并）。"""
    s = (line or '').rstrip('\n')
    if not s.strip():
        return
    if not s.lstrip().startswith('{'):
        _flush()
        print(s, flush=True)
        return
    try:
        o = json.loads(s)
    except Exception:
        _flush()
        print(s[:200], flush=True)
        return
    t = str(o.get('type') or o.get('event') or '')
    low = t.lower()
    if isinstance(o.get('item'), dict):
        item = o['item']
        itype = str(item.get('type') or '')
        if itype == 'agent_message':
            _flush()
            if item.get('text'):
                print('\n✅ ' + str(item['text']), flush=True)
            return
        if itype == 'reasoning':
            _add('think', item.get('text') or item.get('summary') or '')
            return
        if itype in ('command_execution', 'file_change'):
            _flush()
            if low.endswith('started'):
                print('🔧 ' + str(item.get('command') or item.get('changes') or itype), flush=True)
            elif low.endswith('completed'):
                value = item.get('aggregated_output') or item.get('output') or item.get('changes')
                if value:
                    print('   ↳ ' + str(value), flush=True)
            return
    if low in ('thread.started', 'turn.started', 'turn.completed', 'turn.failed'):
        _flush()
        print('[' + t + ']', flush=True)
        return
    if low == 'assistant' and isinstance(o.get('message'), dict):
        content = o['message'].get('content') or []
        if isinstance(content, str):
            _add('text', content)
            return
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get('type')
            if block_type == 'text':
                _add('text', block.get('text') or '')
            elif block_type in ('thinking', 'reasoning'):
                _add('think', block.get('thinking') or block.get('text') or '')
            elif block_type == 'tool_use':
                _flush()
                print('🔧 ' + str(block.get('name') or 'tool') + ' ' + str(block.get('input') or ''), flush=True)
        return
    if 'thinking' in low or low == 'reason':
        _add('think', (o.get('text') or o.get('content') or ''))
        return
    if low in ('text', 'text_delta', 'message', 'assistant', 'delta'):
        _add('text', (o.get('text') or o.get('content') or ''))
        return
    if low in ('final', 'result', 'answer'):
        _flush()
        txt = o.get('text') or o.get('content') or o.get('result') or ''
        if str(txt).strip():
            print('\n✅ ' + str(txt), flush=True)
        return
    if low == 'phase' and not (o.get('tool') or o.get('name')):
        return
    if 'tool' in low:
        _flush()
        name = o.get('name') or o.get('tool') or o.get('tool_name') or o.get('phase') or ''
        args = o.get('input') or o.get('args') or o.get('arguments') or o.get('reason') or ''
        out = o.get('output') or o.get('result') or ''
        line_txt = str(name) + ((' ' + str(args)[:200].replace('\n', ' ')) if args else '')
        print('🔧 ' + line_txt.strip(), flush=True)
        if out:
            print('   ↳ ' + str(out)[:280].replace('\n', ' '), flush=True)
        return
    if low == 'turn_complete':
        _flush()
        return
    if low in ('status', 'usage', 'session', 'meta', 'init', 'system', 'phase'):
        return
    _flush()
    print('· ' + s[:180], flush=True)


def background_view(line):
    """Show the separately dispatched task in the same office PTY."""
    s = (line or '').rstrip('\r\n')
    if not s:
        return
    if not s.lstrip().startswith('{'):
        print('\n' + s, flush=True)
        return
    try:
        event = json.loads(s)
    except ValueError:
        print('\n' + s, flush=True)
        return
    kind = str(event.get('type') or event.get('event') or '')
    item = event.get('item') if isinstance(event.get('item'), dict) else event
    item_kind = str(item.get('type') or kind)
    if kind == 'assistant' and isinstance(event.get('message'), dict):
        content = event['message'].get('content') or []
        if isinstance(content, str):
            content = [{'type': 'text', 'text': content}]
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get('type') == 'text' and block.get('text'):
                print('\n[后台回答] ' + str(block['text']), flush=True)
            elif block.get('type') == 'tool_use':
                print('\n[后台工具] ' + str(block.get('name') or 'tool'), flush=True)
        return
    if kind in ('thread.started', 'turn.started', 'turn.completed', 'turn.failed'):
        print('\n[后台派发] ' + kind, flush=True)
    elif item_kind in ('agent_message', 'message', 'text', 'assistant', 'delta', 'final', 'answer'):
        value = item.get('text') or item.get('content') or item.get('result')
        if value:
            print('\n[后台回答] ' + str(value), flush=True)
    elif 'reason' in item_kind or 'think' in item_kind:
        value = item.get('text') or item.get('content')
        if value:
            print('\n[后台思考] ' + str(value), flush=True)
    elif 'tool' in item_kind or item_kind in ('command_execution', 'file_change'):
        name = item.get('name') or item.get('tool') or item.get('command') or item_kind
        print('\n[后台工具] ' + str(name), flush=True)
        value = item.get('output') or item.get('result')
        if value:
            print(str(value), flush=True)
    elif kind not in ('usage', 'status', 'session', 'meta', 'init'):
        print('\n[后台事件] ' + s, flush=True)


def follow_background(aid):
    path = os.path.join(STREAMS, aid + '.log')
    position = None
    while True:
        try:
            with open(path, encoding='utf-8', errors='replace') as fh:
                if position is None:
                    fh.seek(max(0, os.path.getsize(path) - 4096))
                    if fh.tell():
                        fh.readline()
                else:
                    fh.seek(min(position, os.path.getsize(path)))
                while True:
                    line = fh.readline()
                    if not line:
                        position = fh.tell()
                        break
                    background_view(line)
        except OSError:
            pass
        time.sleep(0.3)


def quota_line(aid):
    from quota_status import for_agent
    q = for_agent(aid)
    if q['kind'] == 'codex':
        def part(label, window):
            return '%s剩余 %s%%' % (label, window.get('remainingPercent')) if window else '%s未知' % label
        return '%s：%s；%s（采样 %s）' % (
            q['label'], part('5 小时', q.get('primary')),
            part('周', q.get('secondary')), q.get('sampleAt', '未知'))
    if q['kind'] == 'deepseek':
        amounts = ' / '.join('%s %s' % (x['total'], x['currency']) for x in q['balances'])
        return '%s：%s' % (q['label'], amounts or '无余额信息')
    return q['label'] + (('（' + q['error'] + '）') if q.get('error') else '')


def run(argv, cwd, timeout, aid):
    """实时流式跑引擎：思考/工具调用/回答逐行渲染出来。"""
    from native_sessions import prepare, save, session_from_line
    argv, session_provider = prepare(argv, aid)
    argv = [resolve(argv[0])] + argv[1:]
    env = dict(os.environ)
    env.pop('ELECTRON_RUN_AS_NODE', None)
    env['RIVET_TRUST_PROJECT'] = '1'
    env['NO_COLOR'] = '1'
    if aid == 'harness-mv3d0001':
        env['DSH_PERMISSION_MODE'] = 'danger-full-access'
    if not env.get('DEEPSEEK_API_KEY'):
        k = api_key()
        if k:
            env['DEEPSEEK_API_KEY'] = k
    t0 = time.time()
    from native_hook_bridge import HookBridge
    bridge = HookBridge(HIVE, aid)
    try:
        p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding='utf-8', errors='replace', bufsize=1)
    except FileNotFoundError as e:
        print('(找不到引擎可执行文件) %s' % e, flush=True)
        return
    except Exception as e:
        print('(出错) %s' % e, flush=True)
        return
    bridge.start()
    session_id = None
    expired = threading.Event()
    def expire():
        expired.set()
        if p.poll() is None:
            p.kill()
    timer = threading.Timer(timeout, expire)
    timer.start()
    try:
        for line in p.stdout:
            candidate = session_from_line(line) if session_provider else None
            if candidate:
                session_id = candidate
            bridge.line(line)
            render(line)
    except Exception:
        pass
    finally:
        timer.cancel()
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
        p.wait()
    bridge.finish(failed=p.returncode != 0 or expired.is_set())
    if p.returncode == 0 and session_provider and session_id:
        save(aid, session_provider, session_id)
    if expired.is_set():
        print('\n(超过 %ds，已中止)' % timeout, flush=True)
    print('\n[退出码 %s ｜ 用时 %ds]' % (p.returncode, int(time.time() - t0)), flush=True)
    return p.returncode


def status_line(aid):
    try:
        f = json.load(open(os.path.join(HIVE, 'fleet.json'), encoding='utf-8'))
        ags = f.get('agents') if isinstance(f, dict) else f
        if isinstance(ags, dict):
            ags = list(ags.values())
        for a in (ags or []):
            if isinstance(a, dict) and a.get('id') == aid:
                d = os.path.join(HIVE, 'agents', aid, 'inbox')
                pend = len([x for x in os.listdir(d) if x.endswith('.json')]) if os.path.isdir(d) else 0
                return ('状态：%-8s ｜ 收件箱待办 %d ｜ breaker %s'
                        % (a.get('status') or 'idle', pend, a.get('breaker')))
    except Exception:
        pass
    return '状态：未知'


def main():
    aid = (sys.argv[1] if len(sys.argv) > 1 else 'god').strip()
    if aid not in AGENTS:
        print('未知员工：%s\n可选：%s' % (aid, ', '.join(AGENTS)))
        return
    name, role, cwd, chat_cmd, task_cmd = AGENTS[aid]
    outdir = os.path.join(PROJ, '员工', aid, '产出')

    print('=' * 62)
    print('  %s ｜ %s' % (name, role))
    print('  %s' % status_line(aid))
    print('  直接打字聊天；后台任务也在这里显示；/quota 看额度；/help 帮助')
    print('=' * 62, flush=True)

    threading.Thread(target=follow_background, args=(aid,), daemon=True).start()

    while True:
        try:
            line = input('\n你 > ')
        except (EOFError, KeyboardInterrupt):
            print('\n(会话结束)')
            return
        text = (line or '').strip()
        if not text:
            continue
        low = text.lower()
        if low in ('exit', 'quit', '/exit', '/quit'):
            print('(再见)')
            return
        if low == '/help':
            print('  /status  看状态与额度\n  /quota  看额度\n  /task <指令>  让它真去执行(可落盘)\n  exit  退出')
            continue
        if low == '/status':
            print('  ' + status_line(aid))
            print('  ' + quota_line(aid))
            continue
        if low == '/quota':
            print('  ' + quota_line(aid))
            continue
        if low.startswith('/task '):
            task = text[6:].strip()
            print('\n%s > (开始执行，下面实时显示它的思考与工具调用…)\n' % name, flush=True)
            run([c.format(task=TASK.format(name=name, role=role, text=task, outdir=outdir))
                  for c in task_cmd], cwd, 600, aid)
            continue
        print('\n%s > (开始，下面实时显示它的思考与工具调用…)\n' % name, flush=True)
        run([c.format(text=HEAD.format(name=name, role=role, text=text)) for c in chat_cmd], cwd, 600, aid)


if __name__ == '__main__':
    main()
