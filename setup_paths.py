# -*- coding: utf-8 -*-
"""把仓库里所有脚本中的作者本机路径替换成你自己的（开源前的隐私处理）。

用法：python setup_paths.py            # 预览要改什么（不写文件）
     python setup_paths.py --apply    # 真正替换
"""
import argparse
import os
import re
import sys

OLD = [r'C:\Users\徐', r'C:\Users\\徐', '/c/Users/徐']
NEW_HINT = os.path.expanduser('~')
PAT = re.compile(r'C:\\Users\\徐|C:\\Users\\徐'.replace('\\', '\\'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    hits = []
    for root, _d, fs in os.walk(here):
        for f in fs:
            if not f.endswith(('.py', '.cmd', '.ps1', '.md', '.js', '.cjs')):
                continue
            p = os.path.join(root, f)
            t = open(p, encoding='utf-8', errors='replace').read()
            if 'C:\\Users\\徐' in t or 'C:\\Users\\徐' in t:
                n = t.count('C:\\Users\\徐')
                hits.append((p, n))
                if a.apply:
                    t = t.replace('C:\\Users\\徐', NEW_HINT)
                    open(p, 'w', encoding='utf-8', newline='\n').write(t)
    if not hits:
        print('  没有需要替换的本机路径 ✓')
        return
    print('  发现 %d 个文件带作者路径（将替换为 %s）：' % (len(hits), NEW_HINT))
    for p, n in hits[:40]:
        print('   %-58s %d 处' % (os.path.relpath(p, here), n))
    print('  %s' % ('已替换 ✓' if a.apply else '加 --apply 才会真正替换'))


if __name__ == '__main__':
    main()
