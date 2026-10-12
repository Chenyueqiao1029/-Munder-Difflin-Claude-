# -*- coding: utf-8 -*-
"""自我迭代器：持续从【桌面 Codex】的实测轨迹里学习它的干法，并审计我自己是否照做。

每次都做四件事：
  1) 读 Codex 最新轨迹的尾部 → 抽取最近的"行为模式"（隔离实验/单点补丁/改后校验/配测试/四段汇报…）
  2) 与《我的工作纪律.md》比对 → 发现"它做了但我没有的新模式"就**追加为新规则**（带观测证据）
  3) 审计我自己：最近我写过的产出里，是否包含「证据（命令/路径）」等要素 → 计分
  4) 生成《自我迭代报告.md》并追加一行到迭代日志

用法：python self_iterate.py          跑一次（**只在老板要求学习时运行，禁止常驻**）
     python self_iterate.py --loop   仅当老板明确要求持续学习时才用（默认禁止常驻）
"""
import argparse
import glob
import json
import os
import re
import time

HOME = r'C:\Users\徐'
CODEX = os.path.join(HOME, '.codex', 'sessions')
C = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(C, '我的工作纪律.md')
REPORT = os.path.join(C, '自我迭代报告.md')
LOG = os.path.join(C, 'self-iterate.log')
MYDIR = C


def log(m):
    line = '[%s] %s' % (time.strftime('%m-%d %H:%M:%S'), m)
    print(line, flush=True)
    try:
        with open(LOG, 'a', encoding='utf-8') as fh:
            fh.write(line + '\n')
    except Exception:
        pass


def newest_rollout():
    best = None
    for root, _d, _f in os.walk(CODEX):
        for f in glob.glob(os.path.join(root, 'rollout-*.jsonl')):
            m = os.path.getmtime(f)
            if best is None or m > best[0]:
                best = (m, f)
    return best


def codex_steps(path, nbytes=800_000):
    """读尾部，抽最近的步骤（工具调用/命令/回复）。"""
    size = os.path.getsize(path)
    with open(path, 'rb') as fh:
        fh.seek(max(0, size - nbytes))
        data = fh.read()
    if size > nbytes and b'\n' in data:
        data = data.split(b'\n', 1)[1]
    steps = []
    for line in data.decode('utf-8', 'replace').splitlines():
        try:
            o = json.loads(line)
        except Exception:
            continue
        t, pl = o.get('type'), (o.get('payload') or {})
        pt = pl.get('type') if isinstance(pl, dict) else None
        ts = (o.get('timestamp') or '')[11:19]
        if t == 'response_item' and pt == 'custom_tool_call':
            args = pl.get('input') or ''
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    pass
            if isinstance(args, dict):
                args = args.get('command') or json.dumps(args, ensure_ascii=False)
            steps.append((ts, 'tool', str(args)[:300]))
        elif t == 'response_item' and pt == 'message' and pl.get('role') == 'assistant':
            txt = ''.join((c.get('text') or '') for c in (pl.get('content') or []) if isinstance(c, dict))
            if txt.strip():
                steps.append((ts, 'reply', txt[:300]))
    return steps


PATTERNS = [
    ('R1', '隔离实验', r'(env:|设置|SET|export|临时|trial|probe).{0,40}(danger-full-access|PYTHONIOENCODING|--json)|exit_code.{0,4}0'),
    ('R2', '单点补丁', r'apply_patch'),
    ('R3', '改后校验/测试', r'py_compile|node --check|unittest|pytest|--test'),
    ('R5', '先读现状', r'driver-state\.json|Get-Content|read_text|Select-String|type '),
]


def load_rules():
    try:
        return open(RULES, encoding='utf-8').read()
    except Exception:
        return ''


def audit_me():
    """轻量自审：最近 24 小时我写过的 .md 里，有多少带"证据类"内容（命令/路径/行号）。"""
    cut = time.time() - 86400
    files = []
    for f in glob.glob(os.path.join(MYDIR, '*.md')):
        if os.path.getmtime(f) >= cut:
            files.append(f)
    scored = []
    for f in files:
        try:
            t = open(f, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        hits = len(re.findall(r'`[^`]*(?:python|powershell|Get-|\.py|\.json|\.md|exit|命令)[^`]*`', t))
        has4 = all(k in t for k in ('结论', '证据', '下一步'))
        scored.append((os.path.basename(f), hits, has4))
    return scored


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--loop', action='store_true')
    a = ap.parse_args()
    while True:
        info = newest_rollout()
        rules = load_rules()
        new_rules = []
        counts = {}
        steps = []
        if info:
            mt, path = info
            steps = codex_steps(path)
            for rid, name, rx in PATTERNS:
                hit = [s for s in steps if re.search(rx, s[2], re.I)]
                if hit:
                    counts[name] = len(hit)
                    # 规则已在文件里就不再重复
                    if ('`%s`' % rid) not in rules and ('| %s |' % rid) not in rules:
                        new_rules.append((rid, name, hit[-1]))
        if new_rules and info:
            with open(RULES, 'a', encoding='utf-8') as fh:
                fh.write('\n## 自动追加（self_iterate · %s）\n' % time.strftime('%Y-%m-%d %H:%M'))
                for rid, name, (ts, kind, body) in new_rules:
                    fh.write('- **%s · %s**：观测到 Codex 于 %s 做了 `%s`\n' % (rid, name, ts, body[:160]))
                    log('新规则: %s %s（证据 %s）' % (rid, name, ts))
        mine = audit_me()
        lines = []
        lines.append('# 自我迭代报告')
        lines.append('')
        lines.append('- 生成时间：%s' % time.strftime('%Y-%m-%d %H:%M:%S'))
        if info:
            mt, path = info
            lines.append('- 学习对象：桌面 Codex ｜ 轨迹 `%s`（%.1f MB，最后写入 %s）'
                         % (os.path.basename(path), os.path.getsize(path) / 1048576,
                            time.strftime('%H:%M:%S', time.localtime(mt))))
        lines.append('- 本次从它轨迹里识别到的行为模式：%s' % (counts or '（暂无新命中）'))
        lines.append('- 新追加规则：%s' % ([n for _r, n, _e in new_rules] or '无'))
        lines.append('')
        lines.append('## 我自己的合规自审（最近 24 小时我写的文档）')
        lines.append('')
        lines.append('| 文档 | 证据类引用 | 是否含「结论/证据/下一步」 |')
        lines.append('|---|---|---|')
        for name, hits, has4 in mine[:12]:
            lines.append('| %s | %d | %s |' % (name, hits, '✅' if has4 else '❌'))
        bad = [n for n, _h, has4 in mine if not has4]
        lines.append('')
        lines.append('- 不合格（缺「结论/证据/下一步」结构）：**%s**' % (bad or '无'))
        lines.append('')
        lines.append('## 结论 / 证据 / 范围与影响 / 下一步')
        lines.append('')
        lines.append('- **结论**：%s' % ('已从 Codex 轨迹追加 %d 条新规则' % len(new_rules) if new_rules else '无新规则，纪律文件已最新'))
        lines.append('- **证据**：轨迹尾部解析出 %d 个步骤；模式命中 %s' % (len(steps), counts))
        lines.append('- **范围与影响**：只写 `我的工作纪律.md` 与 `自我迭代报告.md`，不碰任何生产代码与用户文件')
        lines.append('- **下一步**：%s' % ('按新规则调整行为；下一轮继续比对' if new_rules else '下一轮继续比对'))
        open(REPORT, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
        log('自我迭代完成：Codex 步骤 %d，模式 %s，新规则 %d，我不合格文档 %d'
            % (len(steps), counts, len(new_rules), len(bad)))
        if not a.loop:
            return
        time.sleep(1800)


if __name__ == '__main__':
    main()
