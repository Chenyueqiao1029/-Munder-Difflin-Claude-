# -*- coding: utf-8 -*-
"""① 从 oh-my-coder 抓它真实支持的模型清单 ② 合并成我们的模型注册表 ③ 渲染可视化海报。
    只读对方仓库；只写我们自己的仓库。
"""
import io
import json
import os
import re
import urllib.request

REPO = 'Chenyueqiao1029/oh-my-coder'
H = {'User-Agent': 'dsh-readonly'}
OURS = r'D:\徐\星域蜂巢'
MODELS = os.path.join(OURS, 'models')
BUILD = os.path.join(OURS, 'build')


def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30) as r:
        return r.read().decode('utf-8', 'replace')


def api(p):
    return json.loads(get('https://api.github.com/repos/%s/%s' % (REPO, p)))


print('== 1) 它 src/models/ 里的适配器 ==')
files = [i['name'] for i in api('contents/src/models') if i['type'] == 'file']
print('   ' + ', '.join(files))
try:
    data = [i['name'] for i in api('contents/src/models/data')]
    print('   data/: ' + ', '.join(data))
except Exception as e:
    print('   data/ 读不到:', e)

ids = set()
for f in files:
    if not f.endswith('.py') or f in ('__init__.py', 'base.py'):
        continue
    try:
        t = get('https://raw.githubusercontent.com/%s/main/src/models/%s' % (REPO, f))
    except Exception:
        continue
    for m in re.findall(r'["\']([a-zA-Z0-9][\w\.\-]{2,40})["\']', t):
        if re.search(r'(glm|deepseek|kimi|qwen|doubao|ernie|hunyuan|mimo|minimax|baichuan|spark|yi|gpt|claude|gemini|llama|mistral|grok|phi|ollama)', m, re.I):
            ids.add(m)
print('   抓到的模型 id（%d 个）: %s' % (len(ids), ', '.join(sorted(ids)[:40])))

# ---- 2) 我们的注册表：已支持 / 未支持 + 风格特色 + 评分 ----
# 评分维度：接入难度(1低5高，越低越好) 已在用 免费额度 中文能力 代码能力 上下文
REG = [
    # id, 显示名, 厂商, 属地, 我们是否已接入, 接入方式, 免费/额度, 中文, 编码, 上下文, 接入难度, 一句话特色
    ('deepseek', 'DeepSeek', '深度求索', '国产', True, 'rivet(天枢) / dsh headless', '注册送额度，日常便宜', 5, 5, '128K', 1, '性价比之王：中文强、代码强、我们全办公室的主力'),
    ('glm', 'GLM（智谱）', '智谱 AI', '国产', False, '待接：HTTP OpenAI 兼容', 'GLM-4.7-Flash 完全免费', 5, 4, '200K', 1, '免费额度最狠、中文最好，最适合当"白干活的杂务"'),
    ('kimi', 'Kimi', '月之暗面', '国产', False, '待接：HTTP OpenAI 兼容', '部分免费额度', 5, 4, '128K~256K', 2, '超长上下文，适合吞整本代码/长文档'),
    ('qwen', '通义千问 Qwen', '阿里', '国产', False, '待接：DashScope', '有免费额度', 5, 4, '128K+', 2, '开源生态最全（本地也能跑），工程化最稳'),
    ('doubao', '豆包 Doubao', '字节', '国产', False, '待接：火山方舟', '有免费额度', 4, 4, '128K+', 2, '便宜量大，适合当"批量杂活"'),
    ('ernie', '文心一言 ERNIE', '百度', '国产', False, '待接：千帆', '有免费额度', 5, 3, '128K', 3, '中文语感好，代码中等'),
    ('hunyuan', '混元 Hunyuan', '腾讯', '国产', False, '待接：腾讯云', '有免费额度', 5, 4, '128K', 3, '与腾讯生态贴，CodeBuddy 同源'),
    ('mimo', 'MiMo', '小米', '国产', False, '待接：HTTP', '活动期免费', 4, 4, '长上下文', 3, '长上下文+大文件处理，活动期可白嫖'),
    ('minimax', 'MiniMax', 'MiniMax', '国产', False, '待接：HTTP', '有免费额度', 4, 4, '长上下文', 3, '长文本与角色扮演见长'),
    ('baichuan', '百川 Baichuan', '百川智能', '国产', False, '待接：HTTP', '有免费额度', 5, 3, '128K', 3, '中文医疗/法律域有优势'),
    ('spark', '讯飞星火', '科大讯飞', '国产', False, '待接：HTTP', '有免费额度', 5, 3, '128K', 3, '语音+中文强'),
    ('yi', '零一万物 Yi', '零一万物', '国产', False, '待接：HTTP', '开源可本地', 4, 4, '32K~200K', 2, '开源权重，可本地私有化'),
    ('openai', 'OpenAI GPT', 'OpenAI', '国外', True, 'codex exec（订阅制）', '按订阅，额度有硬锁', 4, 5, '400K+', 2, '代码最稳之一，但额度锁会卡人（我们踩过）'),
    ('claude', 'Anthropic Claude', 'Anthropic', '国外', True, 'claude CLI（本机可达）', '按订阅/API', 5, 5, '200K', 2, '长任务与代码审查的标杆；国内可用性不稳'),
    ('gemini', 'Google Gemini', 'Google', '国外', False, '待接：API', '有免费额度', 4, 4, '1M+', 3, '上下文最长，适合"整仓库喂进去"'),
    ('grok', 'xAI Grok', 'xAI', '国外', False, '待接：API', '按量', 3, 4, '128K+', 4, '实时信息强，国内不可达（需代理）'),
    ('mistral', 'Mistral', 'Mistral AI', '国外', False, '待接：API/本地', '开源可本地', 2, 4, '128K', 2, '欧洲开源派，轻量高效'),
    ('llama', 'Meta Llama', 'Meta', '国外', False, '待接：本地 Ollama', '开源免费（吃显卡）', 3, 3, '128K', 3, '完全本地零 API 费，但吃硬件'),
    ('ollama', 'Ollama（本地）', '开源', '本地', False, '待接：本机 HTTP', '完全免费', 3, 3, '看模型', 2, '断网也能干活、零 API 成本；质量看硬件'),
]

os.makedirs(MODELS, exist_ok=True)
registry = {
    '_说明': '模型注册表：给"引擎网关"用。已接入=现在办公室能直接调；待接=给出接入方式，接好后即可上场。',
    '_数据来源': '模型 id 参考 oh-my-coder 的 src/models/ 适配器清单；**版本、价格、免费额度变动很快，请以各家官方为准**。',
    '_生成时间': '2026-10-12',
    'fields': ['id', 'name', 'vendor', 'region', 'connected', 'how', 'free', 'cn', 'code', 'context', 'difficulty', 'note'],
    'models': [],
}
for (mid, name, vendor, region, conn, how, free, cn, code, ctx, diff, note) in REG:
    registry['models'].append({
        'id': mid, 'name': name, 'vendor': vendor, 'region': region, 'connected': conn,
        'how': how, 'free': free, 'cn': cn, 'code': code, 'context': ctx,
        'difficulty': diff, 'note': note,
        'score': round((cn * 0.3 + code * 0.35 + (6 - diff) * 0.2 + (1 if '免费' in free else 0.5) * 0.15), 2),
    })
io.open(os.path.join(MODELS, 'registry.json'), 'w', encoding='utf-8', newline='\n').write(
    json.dumps(registry, ensure_ascii=False, indent=2))
print()
print('== 2) 我们的模型注册表 ==')
for m in registry['models']:
    print('   %-9s %-18s %-5s %s 综合 %.2f ｜ %s' % (
        m['id'], m['name'], m['region'], '已接入' if m['connected'] else '待接入', m['score'], m['note'][:34]))
print('   已接入 %d 个 ｜ 待接入 %d 个' % (
    sum(1 for m in registry['models'] if m['connected']),
    sum(1 for m in registry['models'] if not m['connected'])))
print('   → models/registry.json')
