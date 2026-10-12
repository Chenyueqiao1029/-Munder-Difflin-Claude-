# -*- coding: utf-8 -*-
"""实时监控【桌面 Codex 应用】的干活进度（只读它的 rollout 轨迹，不打扰它）。

用法：
  python codex_watch.py              看最近 30 步
  python codex_watch.py --follow     持续跟随（每 5 秒打印新步骤）
  python codex_watch.py --md         额外写一份 Markdown 快照
"""
import argparse
import glob
import json
import os
import time

HOME = r'C:\Users\徐'
CODEX = os.path.join(HOME, '.codex', 'sessions')
OUT_MD = r'D:\徐\MunderDifflin\custom-cast\Codex实时进度.md'


def newest_rollout():
    best = None
    for root, _d, _fs in os.walk(CODEX):
        for f in glob.glob(os.path.join(root, 'rollout-*.jsonl')):
            m = os.path.getmtime(f)
            if best is None or m > best[0]:
                best = (m, f, os.path.getsize(f))
    return best


def tail_lines(path, bytes_back=3_000_000):
    """只读文件尾部若干字节，避免 47MB 全读。"""
    size = os.path.getsize(path)
    start = max(0, size - bytes_back)
    with open(path, 'rb') as fh:
        fh.seek(start)
        data = fh.read()
    if start:
        data = data.split(b'\n', 1)[1] if b'\n' in data else b''
    return data.decode('utf-8', 'replace').splitlines()


def summarize(o):
    """把一条 rollout 记录翻译成一行。"""
    ts = (o.get('timestamp') or '')[11:19]
    t = o.get('type')
    pl = o.get('payload') or {}
    pt = pl.get('type') if isinstance(pl, dict) else None

    if t == 'event_msg' and pt == 'task_started':
        return (ts, '▶️  新任务开始', '')
    if t == 'event_msg' and pt == 'task_complete':
        return (ts, '⏹  任务结束', '')
    if t == 'event_msg' and pt == 'token_count':
        info = pl.get('info') or {}
        tot = (info.get('total_token_usage') or {}).get('total_tokens')
        last = (info.get('last_token_usage') or {}).get('total_tokens')
        return (ts, '📊 用量', '本轮 %s ｜ 累计 %s' % (last, tot))
    if t == 'response_item' and pt == 'reasoning':
        txt = ''
        for s in (pl.get('summary') or []):
            txt += (s.get('text') or '')
        txt = txt or pl.get('text') or ''
        return (ts, '💭 思考', txt.replace('\n', ' ')[:200]) if txt.strip() else None
    if t == 'response_item' and pt == 'custom_tool_call':
        name = pl.get('name') or 'tool'
        args = pl.get('input') or pl.get('arguments') or ''
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                pass
        if isinstance(args, dict):
            args = args.get('command') or args.get('cmd') or args.get('input') or json.dumps(args, ensure_ascii=False)
        if isinstance(args, list):
            args = ' '.join(str(x) for x in args)
        return (ts, '🔧 %s' % name, str(args).replace('\n', ' ')[:220])
    if t == 'response_item' and pt == 'custom_tool_call_output':
        out = pl.get('output') or ''
        if isinstance(out, dict):
            out = out.get('output') or out.get('text') or json.dumps(out, ensure_ascii=False)
        return (ts, '   ↳ 输出', str(out).replace('\n', ' ')[:220])
    if t == 'response_item' and pt == 'message' and pl.get('role') == 'assistant':
        txt = ''
        for c in (pl.get('content') or []):
            if isinstance(c, dict):
                txt += (c.get('text') or '')
        return (ts, '💬 回复', txt.replace('\n', ' ')[:200]) if txt.strip() else None
    return None


def collect(path, max_steps=30, since=None):
    lines = tail_lines(path)
    steps = []
    for line in lines:
        try:
            o = json.loads(line)
        except Exception:
            continue
        s = summarize(o)
        if s:
            if since and s[0] <= since:
                continue
            steps.append(s)
    return steps[-max_steps:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--follow', action='store_true')
    ap.add_argument('--md', action='store_true')
    ap.add_argument('--n', type=int, default=30)
    a = ap.parse_args()
    info = newest_rollout()
    if not info:
        print('  没找到桌面 Codex 的 rollout 文件')
        return
    mt, path, size = info
    print('  桌面 Codex 轨迹：%s' % os.path.basename(path))
    print('  大小 %.1f MB ｜ 最后写入 %s' % (size / 1048576, time.strftime('%H:%M:%S', time.localtime(mt))))
    print('-' * 70)
    last_ts = None
    while True:
        steps = collect(path, a.n, since=last_ts if a.follow else None)
        for ts, kind, body in steps:
            print('  [%s] %-12s %s' % (ts, kind, body))
            last_ts = ts
        if a.md:
            mt, path, size = newest_rollout()
            allsteps = collect(path, 60)
            with open(OUT_MD, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write('# 桌面 Codex · 实时进度\n\n')
                fh.write('- 轨迹：`%s`（%.1f MB，最后写入 %s）\n\n' % (
                    os.path.basename(path), size / 1048576, time.strftime('%m-%d %H:%M:%S', time.localtime(mt))))
                for ts, kind, body in allsteps:
                    fh.write('- `%s` **%s** %s\n' % (ts, kind, body))
            print('  （快照已写 %s）' % OUT_MD)
        if not a.follow:
            return
        time.sleep(5)


if __name__ == '__main__':
    main()
