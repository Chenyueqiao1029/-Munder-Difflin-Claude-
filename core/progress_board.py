# -*- coding: utf-8 -*-
"""生成「星域办公室进度看板」HTML：全员状态 / 待办 / 最后一次产出 / 消息时间线。
用法：python progress_board.py    → 产出 进度看板.html
"""
import html
import json
import os
import subprocess
import time

HOME = r'C:\Users\徐\yueqiaochangetheworld'
HIVE = os.path.join(HOME, 'hive')
AG = os.path.join(HIVE, 'agents')
OUT = r'D:\徐\MunderDifflin\custom-cast\进度看板.html'

NAMES = {
    'god': ('月桥', '老板室'),
    'workbuddy-mv135oq0': ('WorkBuddy', '项目管理'),
    'codex-mv2h4arh': ('Codex', '执行总裁'),
    'harness-mv3d0001': ('DeepSeek Harness', '统筹'),
    'tianshu-mv3d0002': ('天枢·执行星域', '执行'),
    'tianshu-approve-mv3e02': ('天枢·审批星域', '审批'),
    'tianshu-fix-mv3e03': ('天枢·纠错星域', '纠错'),
}


def procs():
    try:
        r = subprocess.run(['powershell', '-NoProfile', '-Command',
                            "Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" | "
                            "Where-Object { $_.CommandLine -match 'entry\\.js|dsh-tui|codex|codebuddy' } | "
                            "ForEach-Object { $_.CommandLine }"],
                           capture_output=True, text=True, timeout=60)
        return r.stdout or ''
    except Exception:
        return ''


def read_json(p):
    try:
        with open(p, encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return None


def msgs_of(aid, limit=3):
    out = []
    for sub in ('outbox', '.sent'):
        d = os.path.join(AG, aid, 'outbox') if sub == 'outbox' else os.path.join(AG, aid, 'outbox', '.sent')
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith('.json'):
                out.append(os.path.join(d, f))
    out.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    res = []
    for p in out[:limit]:
        m = read_json(p) or {}
        res.append((os.path.getmtime(p), m))
    return res


def inbox_count(aid):
    d = os.path.join(AG, aid, 'inbox')
    if not os.path.isdir(d):
        return 0
    return len([f for f in os.listdir(d) if f.endswith('.json')])


def timeline(limit=40):
    rows = []
    p = os.path.join(HIVE, 'log.jsonl')
    if not os.path.exists(p):
        return rows
    with open(p, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get('kind') in ('message', 'spawn', 'agent-exit', 'archive'):
                rows.append(o)
    rows.sort(key=lambda o: o.get('ts', 0))
    return rows[-limit:]


def esc(s):
    return html.escape(str(s or ''))


def main():
    plist = procs()
    live = {k: (k in plist) for k in
            ('entry.js', 'dsh-tui', 'codex', 'codebuddy')}
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    cards = []
    for aid, (name, role) in NAMES.items():
        running = False
        if aid == 'god' or aid.startswith('tianshu'):
            running = 'entry.js' in plist
        elif aid.startswith('workbuddy'):
            running = 'codebuddy' in plist
        elif aid.startswith('codex'):
            running = 'codex' in plist
        elif aid.startswith('harness'):
            running = 'dsh-tui' in plist
        latest = msgs_of(aid, 1)
        sub = latest[0][1].get('subject') if latest else '(暂无产出)'
        when = time.strftime('%H:%M', time.localtime(latest[0][0])) if latest else '—'
        cards.append((name, role, aid, running, inbox_count(aid), when, sub))

    rows = timeline()
    tl = []
    for o in rows:
        t = time.strftime('%m-%d %H:%M:%S', time.localtime(o.get('ts', 0) / 1000))
        k = o.get('kind')
        if k == 'message':
            f = NAMES.get(o.get('from'), (o.get('from'),))[0]
            to = NAMES.get(o.get('to'), (o.get('to') or 'human',))[0]
            tl.append((t, f, to, o.get('act'), o.get('subject'), True))
        elif k == 'spawn':
            nm = NAMES.get(o.get('agentId'), (o.get('agentId'),))[0]
            tl.append((t, '系统', nm, 'spawn', '上线', False))
        else:
            nm = NAMES.get(o.get('agentId'), (o.get('agentId'),))[0]
            tl.append((t, '系统', nm, k, '掉线/归档' if k != 'archive' else '归档', False))

    h = ['<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
         '<title>星域办公室 · 进度看板</title>',
         '<style>',
         'body{background:#141222;color:#e8e4ff;font:14px/1.6 "Microsoft YaHei",system-ui;margin:0;padding:24px}',
         'h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:26px 0 10px;color:#b9a8ff}',
         '.meta{color:#8e88b8;font-size:12px;margin-bottom:18px}',
         '.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}',
         '.card{background:#1d1a30;border:1px solid #302a4d;border-radius:10px;padding:12px}',
         '.nm{font-weight:700;font-size:15px}.role{color:#8e88b8;font-size:12px}',
         '.on{color:#54e08a}.off{color:#ff6b81}',
         '.subj{margin-top:8px;color:#cfc7f5;font-size:13px;word-break:break-all}',
         'table{width:100%;border-collapse:collapse;font-size:13px}',
         'td,th{padding:6px 8px;border-bottom:1px solid #2a2540;text-align:left;vertical-align:top}',
         'th{color:#9d94c9;font-weight:600}',
         '.act{display:inline-block;padding:1px 6px;border-radius:5px;background:#2c2550;color:#c9b8ff;font-size:11px}',
         '.sys{color:#7b7398}',
         '</style></head><body>']
    h.append('<h1>星域办公室 · 进度看板</h1>')
    h.append('<div class="meta">生成时间 %s ｜ 进程：rivet=%s dsh-tui=%s codex=%s codebuddy=%s</div>' % (
        now, plist.count('entry.js'), plist.count('dsh-tui'), plist.count('codex'), plist.count('codebuddy')))
    h.append('<h2>员工状态</h2><div class="grid">')
    for name, role, aid, running, back, when, sub in cards:
        h.append('<div class="card"><div class="nm">%s <span class="%s">%s</span></div>'
                 '<div class="role">%s ｜ %s</div>'
                 '<div class="role">收件箱待办 <b>%d</b> ｜ 最后产出 %s</div>'
                 '<div class="subj">%s</div></div>' % (
                     esc(name), 'on' if running else 'off', '●在线' if running else '●掉线',
                     esc(role), esc(aid), back, esc(when), esc(sub)))
    h.append('</div>')
    h.append('<h2>消息 / 上下线时间线（最近 %d 条）</h2><table><tr><th>时间</th><th>发</th><th>收</th><th>类型</th><th>主题</th></tr>' % len(tl))
    for t, f, to, act, subj, is_msg in reversed(tl):
        cls = '' if is_msg else ' class="sys"'
        h.append('<tr%s><td>%s</td><td>%s</td><td>%s</td><td><span class="act">%s</span></td><td>%s</td></tr>' % (
            cls, t, esc(f), esc(to), esc(act), esc(subj)))
    h.append('</table></body></html>')
    with open(OUT, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(h))
    print('  看板 ->', OUT, os.path.getsize(OUT), 'B')
    print('  在线:', ', '.join('%s=%s' % (n, 'on' if r else 'off') for n, _r, _a, r, _b, _w, _s in cards))


if __name__ == '__main__':
    main()
