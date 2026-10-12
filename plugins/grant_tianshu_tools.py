# -*- coding: utf-8 -*-
"""最后一块：把"模型侧工具放行"补上——照 desktop profile 里 codex 的那行，
   为四个天枢星域各生成一行 @deepseek-ai/dsh-tool-subagent，插进 profile 的 cordis.patch.yml。
   然后用无头启动问模型"你有哪些工具"，用 subagent_tianshu* 是否出现来验收。
用法：python grant_tianshu_tools.py [--profiles headless,desktop-canary,desktop] [--apply] [--boot]
"""
import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import time

PROFILES = r'C:\Users\徐\.dsh\profiles'
STAMP = time.strftime('%Y%m%d-%H%M%S')
DOMAINS = [
    ('tianshu-qiming', 'subagent_tianshu_qiming', '启明星域（天枢默认身份）'),
    ('tianshu-exec', 'subagent_tianshu_exec', '执行星域（天梁·锚点之道）'),
    ('tianshu-approve', 'subagent_tianshu_approve', '审批星域（瑶光·复现之道）'),
    ('tianshu-fix', 'subagent_tianshu_fix', '纠错星域（辅·诊断之道）'),
]
MARK = '# ==== dsh-subagent-tianshu'


def log(s):
    print('  ' + s, flush=True)


def tool_rows():
    out = []
    for prov, tool, desc in DOMAINS:
        out.append("    # %s" % desc)
        out.append("    - id: tool-%s" % tool.replace('_', '-'))
        out.append("      name: '@deepseek-ai/dsh-tool-subagent'")
        out.append("      config:")
        out.append("        provider: %s" % prov)
        out.append("        toolName: %s" % tool)
        # 关键：必须声明 maxDepth 由谁负责，否则工具会拒绝激活
        # （实测报错：tool-subagent: provider "..." cannot enforce maxDepth）
        out.append("        maxDepth: provider-managed")
        # 注意：**不要**加 backgroundMode —— 天枢 provider 是一次性委派，
        # 加了会报 "does not support background..." 而拒绝激活（实测）。
    return '\n'.join(out)


def yaml_inserts(path):
    try:
        import yaml
    except Exception:
        return None
    try:
        d = yaml.safe_load(io.open(path, encoding='utf-8').read())
        n = 0
        for e in (d or []):
            if isinstance(e, dict) and 'insert' in e:
                n += len(e['insert'])
        return n
    except Exception as e:
        return 'ERR %s' % str(e)[:70]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--profiles', default='headless,desktop-canary,desktop')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--boot', action='store_true')
    a = ap.parse_args()

    for p in [x.strip() for x in a.profiles.split(',') if x.strip()]:
        patchf = os.path.join(PROFILES, p, 'cordis.patch.yml')
        if not os.path.exists(patchf):
            log('%s: 没有 cordis.patch.yml，跳过' % p)
            continue
        t = io.open(patchf, encoding='utf-8').read()
        if 'subagent_tianshu' in t:
            log('%s: 已有 tianshu 工具行，跳过' % p)
            continue
        block = '\n\n%s\n# 天枢星域委派工具（照 codex 那行克隆）\n- insert:\n%s\n' % (MARK, tool_rows())
        if not a.apply:
            log('%s: 将要追加 %d 行（工具放行）' % (p, block.count('\n')))
            continue
        shutil.copy2(patchf, patchf + '.pregrant-' + STAMP)
        io.open(patchf, 'w', encoding='utf-8', newline='\n').write(t.rstrip() + block)
        log('%s: 已追加工具放行（insert 条目数: %s）' % (p, yaml_inserts(patchf)))

    if a.boot:
        log('无头启动，问模型它有哪些工具…')
        r = subprocess.run(['dsh', '--profile', 'headless', 'headless',
                            '只做一件事：列出你可用的工具名，每行一个，不要调用工具'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace',
                           shell=True, timeout=900)
        out = (r.stdout or '') + (r.stderr or '')
        hits = sorted(set(re.findall(r'subagent_tianshu\w*', out)))
        print('  退出码: %s' % r.returncode)
        print('  输出片段: %s' % re.sub(r'\s+', ' ', out)[:400])
        print('  ✔ 命中的 tianshu 工具: %s' % (', '.join(hits) if hits else '（一个都没出现）'))
        return 0 if hits else 3
    return 0


if __name__ == '__main__':
    sys.exit(main())
