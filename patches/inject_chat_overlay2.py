# -*- coding: utf-8 -*-
"""把内联覆盖层改成外部 js（绕过 CSP 对内联脚本的拦截），并打印 index.html 的 CSP。"""
import os
import re
import shutil
import time

APP = r'D:\徐\MunderDifflin\Munder-Difflin-0.5.5-fixed\resources\app\out\renderer'
IDX = os.path.join(APP, 'index.html')
JS = os.path.join(APP, 'md-chat-overlay.js')
STAMP = time.strftime('%Y%m%d-%H%M%S')

html = open(IDX, encoding='utf-8').read()
m = re.search(r'<meta[^>]+Content-Security-Policy[^>]*>', html, re.I)
print('  CSP:', (m.group(0)[:200] if m else '（没有 CSP meta）'))

js = r'''(function(){
  if (window.__mdChat) return; window.__mdChat = 1;
  var BASE = 'http://127.0.0.1:8787', cur = null, timer = null;
  function esc(s){ return (s||'').replace(/[&<>]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]; }); }
  var fab = document.createElement('div');
  fab.textContent = '💬 星域对话';
  fab.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:2147483000;background:#4a3f9f;color:#fff;' +
    'border-radius:22px;padding:10px 16px;font:14px/1 "Microsoft YaHei",system-ui;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.45)';
  var box = document.createElement('div');
  box.style.cssText = 'display:none;position:fixed;right:16px;bottom:64px;width:420px;height:520px;z-index:2147483000;' +
    'background:#16132a;border:1px solid #4a3f7a;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.5);' +
    'flex-direction:column;font:13px/1.55 "Microsoft YaHei",system-ui;color:#e8e4ff';
  box.innerHTML = '<div style="padding:8px 10px;border-bottom:1px solid #302a4d;display:flex;gap:8px;align-items:center">' +
    '<select id="mdchat-who" style="flex:1;background:#241f3a;color:#e8e4ff;border:1px solid #302a4d;border-radius:6px;padding:5px"></select>' +
    '<span id="mdchat-x" style="cursor:pointer;color:#8e88b8">✕</span></div>' +
    '<div id="mdchat-log" style="flex:1;overflow:auto;padding:10px"></div>' +
    '<div style="padding:8px;border-top:1px solid #302a4d;display:flex;gap:6px">' +
    '<textarea id="mdchat-in" placeholder="跟他说点什么…（Enter 发送）" style="flex:1;height:52px;background:#241f3a;color:#e8e4ff;border:1px solid #302a4d;border-radius:8px;padding:6px;font:13px/1.4 inherit"></textarea>' +
    '<button id="mdchat-send" style="padding:0 14px;border:0;border-radius:8px;background:#4a3f9f;color:#fff;cursor:pointer">发送</button></div>';
  function mount(){ document.body.appendChild(fab); document.body.appendChild(box); wire(); }
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);

  function wire(){
    var log = document.getElementById('mdchat-log'), sel = document.getElementById('mdchat-who'), inp = document.getElementById('mdchat-in');
    fetch(BASE + '/ping?from=app').catch(function(){});
    fetch(BASE + '/agents').then(function(r){ return r.json(); }).then(function(l){
      l.forEach(function(a){ var o = document.createElement('option'); o.value = a[0]; o.textContent = a[1]; sel.appendChild(o); });
      cur = l[0][0]; load();
    }).catch(function(){ log.innerHTML = '<div style="color:#ff9">对话服务没起来（127.0.0.1:8787）</div>'; });
    function render(ms){
      log.innerHTML = '';
      ms.forEach(function(m){
        var d = document.createElement('div');
        d.style.margin = '8px 0'; d.style.textAlign = (m.role === 'you' ? 'right' : 'left');
        var b = document.createElement('span');
        b.style.cssText = 'display:inline-block;padding:7px 10px;border-radius:9px;white-space:pre-wrap;text-align:left;max-width:88%;' +
          'background:' + (m.role === 'you' ? '#2f3b6b' : '#241f3a');
        b.textContent = m.text; d.appendChild(b); log.appendChild(d);
      });
      log.scrollTop = log.scrollHeight;
    }
    window.__mdChatLoad = function(){ if (!cur) return; fetch(BASE + '/history?agent=' + encodeURIComponent(cur)).then(function(r){ return r.json(); }).then(render).catch(function(){}); };
    function load(){ window.__mdChatLoad(); }
    fab.onclick = function(){
      var open = box.style.display === 'flex';
      box.style.display = open ? 'none' : 'flex';
      if (!open) { load(); timer = setInterval(load, 3000); } else if (timer) { clearInterval(timer); timer = null; }
    };
    document.getElementById('mdchat-x').onclick = function(){ box.style.display = 'none'; if (timer) { clearInterval(timer); timer = null; } };
    sel.onchange = function(){ cur = sel.value; load(); };
    function send(){
      var v = inp.value.trim(); if (!v || !cur) return; inp.value = '';
      fetch(BASE + '/send', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ agent: cur, text: v }) })
        .then(function(){ load(); setTimeout(load, 900); }).catch(function(){});
    }
    document.getElementById('mdchat-send').onclick = send;
    inp.onkeydown = function(e){ if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } };
  }
})();
'''
open(JS, 'w', encoding='utf-8', newline='\n').write(js)
print('  已写外部脚本:', os.path.basename(JS), os.path.getsize(JS), 'B')

# 去掉内联块，换成外部引用
if 'md-chat-overlay.js' not in html:
    shutil.copy2(IDX, IDX + '.bak-ext-' + STAMP)
    i = html.find('<!-- MD_CHAT_OVERLAY')
    if i >= 0:
        j = html.find('</script>', i)
        html = html[:i] + '<script src="./md-chat-overlay.js"></script>\n' + html[j + 9:]
    else:
        html = html.replace('</body>', '<script src="./md-chat-overlay.js"></script>\n</body>', 1)
    open(IDX, 'w', encoding='utf-8', newline='\n').write(html)
    print('  index.html 已改为外部引用')
else:
    print('  index.html 已是外部引用')
print('  index.html 现在含:', 'MD_CHAT_OVERLAY' in html, '| js 引用:', 'md-chat-overlay.js' in html)
