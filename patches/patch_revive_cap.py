# -*- coding: utf-8 -*-
"""给 __mdAutoRevive 加限流：同一员工每小时最多自动复活 3 次，避免 Codex 那种 20 秒无限循环。"""
import os
import re
import shutil
import subprocess
import time

MAIN = r'D:\徐\MunderDifflin\Munder-Difflin-0.5.5-fixed\resources\app\out\main\index.js'
ESB = r'D:\徐\_ref\munder-difflin-src\node_modules\.pnpm\@esbuild+win32-x64@0.21.5\node_modules\@esbuild\win32-x64\esbuild.exe'
t = open(MAIN, encoding='utf-8').read()
if 'mdReviveCap' in t:
    print('  已有限流')
    raise SystemExit(0)
old = "      const n2 = mdRev.get(mdAid) || 0;\n      if (n2 < 200) {"
new = ("      /*mdReviveCap*/ const mdNow = Date.now();\n"
       "      const mdHist = (mdRev.get(mdAid + ':t') || []).filter((x) => mdNow - x < 36e5);\n"
       "      if (mdHist.length >= 3) {\n"
       "        console.warn('[md-revive] ' + mdAid + ' 本小时已自动复活 ' + mdHist.length + ' 次，暂停复活（避免无限循环）');\n"
       "      } else {\n"
       "      mdRev.set(mdAid + ':t', mdHist.concat([mdNow]));\n"
       "      const n2 = mdRev.get(mdAid) || 0;\n"
       "      if (n2 < 200) {")
assert t.count(old) == 1, '锚点不唯一: %d' % t.count(old)
t = t.replace(old, new, 1)
# 补上新增的 } 以闭合 else
old2 = "  } catch (e) {\n    console.error(\"[md-revive] hook failed:\", e);\n  }"
assert t.count(old2) == 1
t = t.replace(old2, "      }\n  } catch (e) {\n    console.error(\"[md-revive] hook failed:\", e);\n  }", 1)
bak = MAIN + '.bak-revivecap-' + time.strftime('%Y%m%d-%H%M%S')
shutil.copy2(MAIN, bak)
open(MAIN, 'w', encoding='utf-8', newline='\n').write(t)
r = subprocess.run([ESB, MAIN, '--log-level=error', '--outfile=' + os.path.join(os.environ['TEMP'], 'g8.js'),
                    '--allow-overwrite', '--format=cjs'], capture_output=True)
if r.returncode != 0:
    shutil.copy2(bak, MAIN)
    print('  语法门失败，已回滚:', (r.stderr or b'')[:300].decode('utf-8', 'replace'))
    raise SystemExit(1)
print('  已加复活限流（每小时 3 次）｜语法门通过｜备份', os.path.basename(bak))
