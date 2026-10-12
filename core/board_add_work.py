# -*- coding: utf-8 -*-
"""在看板里追加「员工产出与思考日志」区：每人最新阶段报告 + 终端日志尾部 + 产物清单。"""
import html
import os
import time

OUT = r'D:\徐\MunderDifflin\custom-cast\进度看板.html'
PROJ = r'C:\Users\徐\yueqiaochangetheworld\hive\projects\YQC-6-员工被回收排查\员工'

GROUPS = [
    ('月桥（调度）', '月桥'),
    ('Codex（侦查+终审）', 'codex'),
    ('天枢·执行星域（天梁）', '天枢执行星域'),
    ('天枢·审批星域（瑶光）', '天枢审批星域'),
    ('天枢·纠错星域（辅）', '天枢纠错星域'),
    ('WorkBuddy（杂务）', 'WorkBuddy'),
    ('DeepSeek Harness（我）', 'harness'),
]


def esc(s):
    return html.escape(str(s or ''))


def collect(sub):
    d = os.path.join(PROJ, sub)
    files = []
    if os.path.isdir(d):
        for root, _dirs, fs in os.walk(d):
            for f in fs:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, d)
                if rel.endswith(('终端.events.jsonl',)):
                    continue
                files.append((os.path.getmtime(p), rel, os.path.getsize(p)))
    files.sort(reverse=True)
    return files


def tail(path, n=1400):
    try:
        t = open(path, encoding='utf-8', errors='replace').read()
        return t[-n:]
    except Exception:
        return ''


blocks = []
for title, sub in GROUPS:
    d = os.path.join(PROJ, sub)
    files = collect(sub)
    logp = os.path.join(d, '终端.log')
    lg = tail(logp) if os.path.exists(logp) else ''
    rows = ''.join('<tr><td>%s</td><td>%.1f KB</td><td>%s</td></tr>' % (
        esc(rel), kb / 1024, time.strftime('%m-%d %H:%M', time.localtime(mt))) for mt, rel, kb in files[:8])
    blocks.append(
        '<div class="emp"><h3>%s</h3>%s<div class="cnt">产出 %d 个文件</div>%s</div>' % (
            esc(title),
            ('<table><tr><th>文件</th><th>大小</th><th>时间</th></tr>%s</table>' % rows) if rows else '<div class="cnt">（暂无产出）</div>',
            len(files),
            ('<details><summary>思考日志（终端.log 尾部）</summary><pre>%s</pre></details>' % esc(lg)) if lg else ''))

css = '''<style>
.emp{background:#1d1a30;border:1px solid #302a4d;border-radius:10px;padding:12px;margin:10px 0}
.emp h3{margin:0 0 8px;font-size:15px;color:#e8e4ff}
.cnt{color:#8e88b8;font-size:12px;margin:6px 0}
pre{white-space:pre-wrap;word-break:break-all;background:#141222;border:1px solid #2a2540;border-radius:8px;
    padding:10px;max-height:340px;overflow:auto;font-size:12px;color:#cfc7f5}
summary{cursor:pointer;color:#b9a8ff;font-size:13px}
</style>'''

html_add = css + '<h2>员工产出与思考日志（统筹视图）</h2>' + ''.join(blocks) + '</body>'
t = open(OUT, encoding='utf-8').read()
if '员工产出与思考日志' in t:
    i = t.find('<h2>员工产出与思考日志')
    t = t[:i] + html_add[len(css):]
else:
    t = t.replace('</body>', html_add)
open(OUT, 'w', encoding='utf-8', newline='\n').write(t)
print('  看板已更新 ->', OUT, os.path.getsize(OUT), 'B')
for title, sub in GROUPS:
    print('   %-24s %d 个产物' % (title, len(collect(sub))))
