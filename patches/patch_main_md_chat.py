"""Tell main that md-chat is a custom PTY wrapper, even for a Codex employee.

The Codex identity remains in the roster and md-chat uses Codex headless to
answer. Main must not prepend `codex resume <session>` to this wrapper's args.
"""
from pathlib import Path
import shutil
import subprocess
import time

TARGET = Path('D:/徐/MunderDifflin/Munder-Difflin-0.5.5-fixed/resources/app/out/main/index.js')
OLD = '  const provider = inferAgentProvider(opts.command, opts.provider ?? opts.hive?.provider);'
NEW = '''  /*__mdChatProvider*/
  const provider = /^md-chat(?:\\.cmd)?$/i.test(opts.command.trim())
    ? "custom" : inferAgentProvider(opts.command, opts.provider ?? opts.hive?.provider);'''

def main():
    src = TARGET.read_text(encoding='utf-8')
    if '/*__mdChatProvider*/' in src:
        print('Already patched')
        return
    if src.count(OLD) != 1:
        raise SystemExit('Main spawn anchor changed; no file written')
    staged = TARGET.parent / 'index.u3-staged.js'
    staged.write_text(src.replace(OLD, NEW, 1), encoding='utf-8', newline='\n')
    check = subprocess.run(['node', '--check', str(staged)], capture_output=True, text=True)
    if check.returncode:
        staged.unlink()
        raise SystemExit(check.stderr)
    backup = TARGET.with_name('index.js.bak-u3-' + time.strftime('%Y%m%d-%H%M%S'))
    shutil.copy2(TARGET, backup)
    staged.replace(TARGET)
    print('Patched main; backup:', backup)

if __name__ == '__main__':
    main()
