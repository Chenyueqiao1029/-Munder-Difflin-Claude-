# -*- coding: utf-8 -*-
"""把月桥发给人类的汇报放到看板最上面（最近 5 封，含正文摘要）。"""
import glob
import html
import json
import os
import time

OUT = r'D:\徐\MunderDifflin\custom-cast\进度看板.html'
GOD = r'C:\Users\徐\yueqiaochangetheworld\hive\agents\god\outbox\.sent'


def esc(s):
    return html.escape(str(s or ''))


msgs = []
for p in glob.glob(os.path.join(GOD, '*.json')):
    try:
        m = json.load(open(p, encoding='utf-8'))
    except Exception:
        continue
    if m.get('to') == 'human':
        msgs.append((os.path.getmtime(p), m, os.path.basename(p)))
msgs.sort(reverse=True)

items = []
for mt, m, fn in msgs[:5]:
    items.append(
        '<div class="gbrief"><div class="gh">[%s] %s</div><pre>%s</pre>'
        '<div class="cnt">文件：%s</div></div>' % (
            time.strftime('%m-%d %H:%M', time.localtime(mt)), esc(m.get('subject')),
            esc((m.get('body') or '')[:2500]), esc(fn)))

block = ('<h2 style="color:#ffd479">月桥 → 你 的汇报（最近 5 封 · 自动刷新 20 秒）</h2>'
         '<div class="cnt">月桥一直有回你，只是写在 <code>hive\\agents\\god\\outbox\\.sent\\*-human-*.json</code>，'
         'app 的「问我」板只收 act=ask，所以界面不显示它。这里直接列出来。</div>'
         + ''.join(items if items else ['<div class="cnt">（暂无）</div>']))

css = ('<style>.gbrief{background:#241f3a;border:1px solid #4a3f7a;border-radius:10px;padding:12px;margin:10px 0}'
       '.gh{color:#ffd479;font-weight:700;margin-bottom:6px}</style>')

t = open(OUT, encoding='utf-8').read()
if '月桥 → 你 的汇报' in t:
    i = t.find('<h2 style="color:#ffd479">')
    j = t.find('<h2', i + 10)
    t = t[:i] + css + block + (t[j:] if j > 0 else '</body></html>')
else:
    t = t.replace('<body>', '<body>' + css, 1)
    t = t.replace('<h1>', block + '<h1>', 1)
open(OUT, 'w', encoding='utf-8', newline='\n').write(t)
print('  看板已更新 ->', OUT, os.path.getsize(OUT), 'B  月桥汇报', len(items), '封')
