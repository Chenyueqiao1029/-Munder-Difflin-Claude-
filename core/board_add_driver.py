# -*- coding: utf-8 -*-
"""给看板加「投递与运行状态（驱动 v2）」区，并开启 20 秒自动刷新。"""
import html
import json
import os
import time

OUT = r'D:\徐\MunderDifflin\custom-cast\进度看板.html'
STATUS = r'D:\徐\MunderDifflin\custom-cast\driver-status.json'
PROJ = r'C:\Users\徐\yueqiaochangetheworld\hive\projects\YQC-6-员工被回收排查\员工'
OUTDIR = {
    'harness-mv3d0001': 'dsh',
    'tianshu-mv3d0002': '天枢执行星域',
    'tianshu-approve-mv3e02': '天枢审批星域',
    'tianshu-fix-mv3e03': '天枢纠错星域',
    'codex-mv2h4arh': 'codex',
    'workbuddy-mv135oq0': 'WorkBuddy',
}


def esc(s):
    return html.escape(str(s or ''))


def tail(p, n=700):
    try:
        return open(p, encoding='utf-8', errors='replace').read()[-n:]
    except Exception:
        return ''


try:
    st = json.load(open(STATUS, encoding='utf-8'))
except Exception:
    st = {}

rows = []
for aid, sub in OUTDIR.items():
    rec = st.get(aid) or {}
    log = os.path.join(PROJ, sub, '终端.log')
    mt = time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(log))) if os.path.exists(log) else '—'
    state = rec.get('state', '—')
    ok = rec.get('lastOk')
    badge = {'ran': '✅ 已投递', 'idle': '⏸ 空闲（无新邮件）', 'failed': '❌ 投递失败'}.get(state, esc(state))
    if aid == 'codex-mv2h4arh' and rec.get('pending'):
        badge += '（额度限制，待恢复）'
    rows.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
        esc(rec.get('name') or aid), badge, rec.get('pending', '—'),
        time.strftime('%H:%M', time.localtime(rec['lastRun'])) if rec.get('lastRun') else '—',
        '正常' if ok else ('失败' if ok is False else '—'), mt))

block = ('<h2>投递与运行状态（驱动 v2 · 原生无头通道）</h2>'
         '<div class="cnt">投递方式：rivet --goal / dsh headless / codex exec / codebuddy -p；'
         '每 45 秒检查一次，只投递新邮件，成功即归档。自动刷新 20 秒。</div>'
         '<table><tr><th>员工</th><th>状态</th><th>待处理</th><th>上次投递</th><th>结果</th><th>日志更新</th></tr>'
         + ''.join(rows) + '</table>')

t = open(OUT, encoding='utf-8').read()
# 自动刷新
if 'http-equiv="refresh"' not in t:
    t = t.replace('<head><meta charset="utf-8">',
                  '<head><meta charset="utf-8"><meta http-equiv="refresh" content="20">', 1)
# 替换/插入区块
if '投递与运行状态' in t:
    i = t.find('<h2>投递与运行状态')
    j = t.find('<h2>', i + 10)
    t = t[:i] + block + (t[j:] if j > 0 else '</body></html>')
else:
    t = t.replace('<h2>员工产出与思考日志', block + '<h2>员工产出与思考日志', 1)
open(OUT, 'w', encoding='utf-8', newline='\n').write(t)
print('  看板已更新 ->', OUT, os.path.getsize(OUT), 'B  自动刷新:', 'http-equiv="refresh"' in t)
