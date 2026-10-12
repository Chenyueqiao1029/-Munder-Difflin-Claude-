# -*- coding: utf-8 -*-
"""主进程补丁 __mdAutoRevive：
   PTY 异常退出时，若是花名册里的员工（非 god、非登录提示退出），
   20 秒后自动用原参数重新 spawn，并解除归档/恢复门。
   → Codex / DSH 不再一直处于掉线状态（每个员工最多自动复活 8 次）。
"""
import os
import shutil
import subprocess
import time

APP = r'D:\徐\MunderDifflin\Munder-Difflin-0.5.5-fixed'
MAIN = os.path.join(APP, 'resources', 'app', 'out', 'main', 'index.js')
ESBUILD = r'D:\徐\_ref\munder-difflin-src\node_modules\.pnpm\@esbuild+win32-x64@0.21.5\node_modules\@esbuild\win32-x64\esbuild.exe'

ANCHOR = '''  if (signInOffer) teardownPty(id, "revive");
  else teardownPty(id, "exit");
  if (signInOffer && run2) {'''

PATCH = '''  if (signInOffer) teardownPty(id, "revive");
  else teardownPty(id, "exit");
  /*__mdAutoRevive*/ try {
    const mdAid = run2 && run2.opts && run2.opts.hive && run2.opts.hive.id;
    if (!signInOffer && mdAid && !run2.opts.hive.isGod && run2.opts.command) {
      const mdRev = globalThis.__mdRevive || (globalThis.__mdRevive = /* @__PURE__ */ new Map());
      const n2 = mdRev.get(mdAid) || 0;
      if (n2 < 8) {
        mdRev.set(mdAid, n2 + 1);
        const reOpts = { ...run2.opts, hive: { ...run2.opts.hive } };
        const owner2 = run2.owner;
        console.log(`[md-revive] ${mdAid} exited (code ${exitCode}); respawning in 20s (attempt ${n2 + 1})`);
        setTimeout(() => {
          try {
            hive.setArchived(mdAid, false);
            try {
              restoreGate.release(mdAid);
            } catch (e) {
            }
            try {
              ptyManager.forgetLookups();
            } catch (e) {
            }
            void spawnAgentCore(reOpts, owner2).then((r) => console.log(`[md-revive] ${mdAid} respawn ok=${r && r.ok}`)).catch((e) => console.error("[md-revive] respawn failed:", e));
          } catch (e) {
            console.error("[md-revive] failed:", e);
          }
        }, 2e4);
      }
    }
  } catch (e) {
    console.error("[md-revive] hook failed:", e);
  }
  if (signInOffer && run2) {'''

t = open(MAIN, encoding='utf-8').read()
print('  锚点出现次数:', t.count(ANCHOR))
if '__mdAutoRevive' in t:
    print('  已打过补丁')
else:
    if t.count(ANCHOR) != 1:
        raise SystemExit('锚点不唯一')
    bak = MAIN + '.bak-autorevive-' + time.strftime('%Y%m%d-%H%M%S')
    shutil.copy2(MAIN, bak)
    open(MAIN, 'w', encoding='utf-8', newline='\n').write(t.replace(ANCHOR, PATCH, 1))
    out = os.path.join(os.environ['TEMP'], 'main-gate3.js')
    r = subprocess.run([ESBUILD, MAIN, '--log-level=error', '--outfile=' + out, '--allow-overwrite', '--format=cjs'],
                       capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(bak, MAIN)
        print('  语法门失败，已回滚:', (r.stderr or '')[:400])
        raise SystemExit(1)
    print('  语法门通过（备份 %s）' % os.path.basename(bak))
