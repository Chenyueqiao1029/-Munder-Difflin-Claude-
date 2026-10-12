# -*- coding: utf-8 -*-
"""主进程补丁 __mdPtyBind：
   pty:spawn 入口处，若 opts 没带 hive，就从 registry 把该 agent 的 hive 记录补回来，
   并无条件登记 ptyToAgent.set(ptyId, agentId)。
修复：恢复流程启动的员工没有 PTY 登记 → 界面「没有实时终端」、hook/叫醒/遥测全失效。
"""
import os
import re
import shutil
import subprocess
import time

APP = r'D:\徐\MunderDifflin\Munder-Difflin-0.5.5-fixed'
MAIN = os.path.join(APP, 'resources', 'app', 'out', 'main', 'index.js')
ESBUILD = r'D:\徐\_ref\munder-difflin-src\node_modules\.pnpm\@esbuild+win32-x64@0.21.5\node_modules\@esbuild\win32-x64\esbuild.exe'

ANCHOR = '''  const owner = electron.BrowserWindow.fromWebContents(evt.sender)?.webContents ?? null;
  return spawnAgentCore(opts, owner);
});'''

PATCH = '''  const owner = electron.BrowserWindow.fromWebContents(evt.sender)?.webContents ?? null;
  /*__mdPtyBind*/ try {
    if (opts && typeof opts.id === "string") {
      const aid = (opts.hive && opts.hive.id) || String(opts.id).replace(/^pty-/, "");
      if (aid) {
        if (!opts.hive) {
          const reg = hive.registry();
          const rec = reg && reg.agents ? reg.agents[aid] : null;
          if (rec) {
            opts.hive = {
              id: aid,
              name: rec.name,
              cwd: rec.cwd,
              role: rec.role,
              provider: rec.provider,
              character: rec.character,
              accent: rec.accent
            };
            console.log("[md-ptybind] restored hive record for", aid);
          }
        }
        ptyToAgent.set(opts.id, aid);
        console.log("[md-ptybind] bound", opts.id, "<->", aid);
      }
    }
  } catch (e) {
    console.error("[md-ptybind] failed:", e);
  }
  return spawnAgentCore(opts, owner);
});'''

t = open(MAIN, encoding='utf-8').read()
print('  锚点出现次数:', t.count(ANCHOR))
if '__mdPtyBind' in t:
    print('  已打过补丁，跳过')
else:
    if t.count(ANCHOR) != 1:
        raise SystemExit('锚点不唯一，放弃')
    bak = MAIN + '.bak-ptybind-' + time.strftime('%Y%m%d-%H%M%S')
    shutil.copy2(MAIN, bak)
    print('  备份 ->', os.path.basename(bak))
    t2 = t.replace(ANCHOR, PATCH, 1)
    open(MAIN, 'w', encoding='utf-8', newline='\n').write(t2)
    # 语法门
    out = os.path.join(os.environ['TEMP'], 'main-gate.js')
    r = subprocess.run([ESBUILD, MAIN, '--log-level=error', '--outfile=' + out, '--allow-overwrite', '--format=cjs'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, MAIN)
        print('  语法门失败，已回滚:\n', (r.stderr or '')[:500])
        raise SystemExit(1)
    print('  语法门通过')
    # 自检标记
    t3 = open(MAIN, encoding='utf-8').read()
    print('  自检 __mdPtyBind:', '__mdPtyBind' in t3, ' ptyToAgent.set 次数:', t3.count('ptyToAgent.set'))
