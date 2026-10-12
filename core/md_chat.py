# -*- coding: utf-8 -*-
"""星域对话台：给每个员工一个"正常 AI 对话"的界面。
   纯标准库；只监听 127.0.0.1:8787；后台静默运行。
   - 选员工 → 发消息 → 用该引擎的原生无头模式回答 → 回显
   - 对话历史存 chat/<agent>.jsonl；可随时回看
"""
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
CHAT = os.path.join(HERE, 'chat')
os.makedirs(CHAT, exist_ok=True)
NPM = os.path.join(os.environ.get('APPDATA', ''), 'npm')
PORT = 8787
LOCK = threading.Lock()
BUSY = {}

AGENTS = [
    ('god', '月桥', '老板室 · 调度', r'C:\Users\徐\yueqiaochangetheworld',
     ['tianshu-agent', '-p', '{text}', '--skip-welcome', '--dangerously-skip-permissions']),
    ('tianshu-mv3d0002', '天枢·执行星域（天梁）', '交付', os.path.join(HOME, 'hive'),
     ['tianshu-agent', '-p', '{text}', '--skip-welcome', '--dangerously-skip-permissions']),
    ('tianshu-approve-mv3e02', '天枢·审批星域（瑶光）', '复核', os.path.join(HOME, 'hive'),
     ['tianshu-agent', '-p', '{text}', '--skip-welcome', '--dangerously-skip-permissions']),
    ('tianshu-fix-mv3e03', '天枢·纠错星域（辅）', '排错', os.path.join(HOME, 'hive'),
     ['tianshu-agent', '-p', '{text}', '--skip-welcome', '--dangerously-skip-permissions']),
    ('harness-mv3d0001', 'DeepSeek Harness', '统筹', os.path.join(HOME, 'hive'),
     ['dsh', '--profile', 'headless', 'headless', '{text}']),
    ('codex-mv2h4arh', 'Codex', '执行总裁', os.path.join(HOME, 'hive'),
     ['codex', 'exec', '-m', 'gpt-6-astra', '{text}']),
    ('workbuddy-mv135oq0', 'WorkBuddy', '杂务', os.path.join(HOME, 'hive'),
     ['codebuddy', '-p', '--dangerously-skip-permissions', '{text}']),
]
BY_ID = {a[0]: a for a in AGENTS}

PREAMBLE = ('老板对你说：{text}\n\n'
            '（你正在跟本办公室的人类老板面对面闲聊。用中文、直接、口语化地回答他；'
            '不要写文件、不要发 act 消息、不要通报给 god。就聊天。）')


def resolve(b):
    for c in (os.path.join(NPM, b + '.cmd'), os.path.join(NPM, b + '.exe')):
        if os.path.exists(c):
            return c
    return b


def hist_path(aid):
    return os.path.join(CHAT, aid + '.jsonl')


def append(aid, role, text, meta=''):
    with open(hist_path(aid), 'a', encoding='utf-8') as fh:
        fh.write(json.dumps({'role': role, 'text': text, 'meta': meta, 'at': time.time()},
                            ensure_ascii=False) + '\n')


def history(aid, n=200):
    p = hist_path(aid)
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p, encoding='utf-8', errors='replace'):
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out[-n:]


def ask(aid, text):
    """在后台线程里跑引擎（一次问答）。"""
    a = BY_ID.get(aid)
    if not a:
        return
    _, name, _role, cwd, cmd = a
    BUSY[aid] = True
    append(aid, 'you', text)
    try:
        argv = [c.format(text=PREAMBLE.format(text=text)) for c in cmd]
        argv[0] = resolve(argv[0])
        env = dict(os.environ)
        env.pop('ELECTRON_RUN_AS_NODE', None)
        env['RIVET_TRUST_PROJECT'] = '1'
        t0 = time.time()
        r = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=900)
        out = (r.stdout or '').strip()
        if r.returncode != 0 and not out:
            out = '(引擎返回码 %s)\n%s' % (r.returncode, (r.stderr or '')[-500:])
        append(aid, 'agent', out or '(空回答)', meta='%ds' % int(time.time() - t0))
    except subprocess.TimeoutExpired:
        append(aid, 'agent', '(超时 900 秒)', meta='timeout')
    except Exception as e:
        append(aid, 'agent', '(出错) %s' % e)
    finally:
        BUSY[aid] = False


PAGE = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>星域对话台</title>
<style>
*{box-sizing:border-box}body{margin:0;font:14px/1.6 "Microsoft YaHei",system-ui;background:#141222;color:#e8e4ff;display:flex;height:100vh}
#side{width:230px;background:#1b1830;border-right:1px solid #302a4d;overflow:auto;flex:0 0 230px}
.a{padding:10px 12px;border-bottom:1px solid #241f3a;cursor:pointer}.a:hover{background:#241f3a}
.a.on{background:#2c2550}.a b{display:block}.a span{color:#8e88b8;font-size:12px}
#main{flex:1;display:flex;flex-direction:column}
#head{padding:12px 16px;border-bottom:1px solid #302a4d;background:#1b1830}
#log{flex:1;overflow:auto;padding:16px}
.m{margin:10px 0;max-width:80%}.m.you{margin-left:auto;text-align:right}
.b{display:inline-block;padding:8px 12px;border-radius:10px;background:#241f3a;white-space:pre-wrap;text-align:left;word-break:break-word}
.m.you .b{background:#2f3b6b}
.meta{color:#7b7398;font-size:11px;margin-top:2px}
#bar{display:flex;gap:8px;padding:12px;border-top:1px solid #302a4d;background:#1b1830}
textarea{flex:1;height:64px;background:#241f3a;color:#e8e4ff;border:1px solid #302a4d;border-radius:8px;padding:8px;font:14px/1.5 inherit}
button{padding:0 20px;border:0;border-radius:8px;background:#4a3f9f;color:#fff;font-size:14px;cursor:pointer}
button:disabled{opacity:.5;cursor:default}
</style></head><body>
<div id="side"></div>
<div id="main">
  <div id="head"><b id="who">选一个员工</b><div class="meta" id="sub"></div></div>
  <div id="log"></div>
  <div id="bar"><textarea id="t" placeholder="跟他说点什么…（Enter 发送，Shift+Enter 换行）"></textarea><button id="s">发送</button></div>
</div>
<script>
let cur=null,busy=false;
fetch('/agents').then(r=>r.json()).then(l=>{
  const s=document.getElementById('side');
  l.forEach(a=>{const d=document.createElement('div');d.className='a';d.innerHTML='<b>'+a[1]+'</b><span>'+a[2]+'</span>';
    d.onclick=()=>pick(a[0],a[1],a[2]);s.appendChild(d);});
  pick(l[0][0],l[0][1],l[0][2]);
});
function pick(id,name,sub){cur=id;document.getElementById('who').textContent=name;
  document.getElementById('sub').textContent=sub+' · '+id;
  [...document.querySelectorAll('.a')].forEach((e,i)=>e.classList.toggle('on',e.querySelector('b').textContent===name));
  load();}
function load(){fetch('/history?agent='+encodeURIComponent(cur)).then(r=>r.json()).then(show);}
function show(ms){const L=document.getElementById('log');L.innerHTML='';
  ms.forEach(m=>{const d=document.createElement('div');d.className='m '+(m.role==='you'?'you':'');
    d.innerHTML='<div class="b">'+esc(m.text)+'</div><div class="meta">'+(m.meta||'')+'</div>';L.appendChild(d);});
  L.scrollTop=L.scrollHeight;}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
document.getElementById('s').onclick=send;
document.getElementById('t').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}};
function send(){const t=document.getElementById('t');const v=t.value.trim();if(!v||!cur)return;
  t.value='';fetch('/send',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({agent:cur,text:v})}).then(()=>{load();setTimeout(load,800);});}
setInterval(()=>{if(cur)load();},3000);
</script></body></html>"""


def _control_token():
    import secrets
    path = os.path.join(HERE, 'control-token.txt')
    try:
        return open(path, encoding='ascii').read().strip()
    except FileNotFoundError:
        token = secrets.token_hex(32)
        with open(path, 'x', encoding='ascii') as fh:
            fh.write(token)
        return token


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype='application/json; charset=utf-8'):
        b = body.encode('utf-8') if isinstance(body, str) else body
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith('/api/process?'):
            from urllib.parse import parse_qs, urlparse
            from process_control import status
            aid = (parse_qs(urlparse(self.path).query).get('agent') or [''])[0]
            if aid not in BY_ID:
                return self._send(404, '{"error":"unknown agent"}')
            try:
                return self._send(200, json.dumps(status(aid), ensure_ascii=False))
            except Exception:
                return self._send(503, '{"error":"process query unavailable"}')
        if self.path.startswith('/api/stream'):
            from urllib.parse import parse_qs, urlparse
            query = parse_qs(urlparse(self.path).query)
            aid = (query.get('agent') or [''])[0]
            if aid not in BY_ID:
                return self._send(404, '{"error":"unknown agent"}')
            try:
                offset = int((query.get('offset') or ['-1'])[0])
            except ValueError:
                offset = -1
            path = os.path.join(HERE, 'streams', aid + '.log')
            if not os.path.exists(path):
                return self._send(200, '{"offset":0,"lines":[]}')
            with open(path, 'rb') as fh:
                size = os.path.getsize(path)
                start = max(0, size - 4096) if offset < 0 else min(offset, size)
                fh.seek(start)
                if offset < 0 and start:
                    fh.readline()
                    start = fh.tell()
                raw = fh.read(262144)
            last = raw.rfind(b'\n')
            if last < 0:
                return self._send(200, json.dumps({'offset': start, 'lines': []}))
            payload = {'offset': start + last + 1,
                       'lines': raw[:last + 1].decode('utf-8', 'replace').splitlines()[-200:]}
            return self._send(200, json.dumps(payload, ensure_ascii=False))
        if self.path.startswith('/api/quota'):
            from urllib.parse import parse_qs, urlparse
            from quota_status import for_agent
            aid = (parse_qs(urlparse(self.path).query).get('agent') or [''])[0]
            if aid not in BY_ID:
                return self._send(404, '{"error":"unknown agent"}')
            return self._send(200, json.dumps(for_agent(aid), ensure_ascii=False))
        if self.path.startswith('/ping'):
            try:
                from urllib.parse import urlparse
                q = urlparse(self.path).query
                with open(os.path.join(CHAT, 'ping.log'), 'a', encoding='utf-8') as fh:
                    fh.write('%s %s\n' % (time.strftime('%H:%M:%S'), q))
            except Exception:
                pass
            return self._send(200, '{"ok":true}')
        if self.path.startswith('/agents'):
            self._send(200, json.dumps([[a[0], a[1], a[2]] for a in AGENTS], ensure_ascii=False))
        elif self.path.startswith('/history'):
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            aid = (q.get('agent') or [''])[0]
            self._send(200, json.dumps(history(aid), ensure_ascii=False))
        elif self.path in ('/', '/index.html'):
            self._send(200, PAGE, 'text/html; charset=utf-8')
        else:
            self._send(404, '{}')

    def do_OPTIONS(self):
        self._send(204, '')

    def do_POST(self):
        if self.path == '/api/interrupt':
            from process_control import interrupt
            origin = self.headers.get('Origin')
            if origin not in (None, 'null', 'http://127.0.0.1:8787'):
                return self._send(403, '{"error":"origin denied"}')
            if self.headers.get('X-MD-Control') != _control_token():
                return self._send(403, '{"error":"control token denied"}')
            try:
                length = int(self.headers.get('Content-Length') or 0)
                if length < 1 or length > 1024:
                    raise ValueError('invalid length')
                data = json.loads(self.rfile.read(length).decode('utf-8'))
                aid = data.get('agent')
            except Exception:
                return self._send(400, '{"error":"invalid request"}')
            if aid not in BY_ID:
                return self._send(404, '{"error":"unknown agent"}')
            try:
                result = interrupt(aid)
                return self._send(200 if result['ok'] else 409,
                                  json.dumps(result, ensure_ascii=False))
            except Exception:
                return self._send(503, '{"error":"interrupt unavailable"}')
        if self.path.startswith('/send'):
            n = int(self.headers.get('Content-Length') or 0)
            try:
                data = json.loads(self.rfile.read(n).decode('utf-8'))
            except Exception:
                return self._send(400, '{}')
            aid, text = data.get('agent'), (data.get('text') or '').strip()
            if aid in BY_ID and text:
                with LOCK:
                    if not BUSY.get(aid):
                        threading.Thread(target=ask, args=(aid, text), daemon=True).start()
            self._send(200, '{"ok":true}')
        else:
            self._send(404, '{}')


if __name__ == '__main__':
    print('星域对话台 → http://127.0.0.1:%d/  (只监听本机)' % PORT, flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), H).serve_forever()
