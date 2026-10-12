"""ASCII-path launcher for md-chat.cmd; cmd.exe cannot use a lossy 徐 path."""
from pathlib import Path
import runpy
import sys

target = Path('D:/') / Path.home().name / 'MunderDifflin' / 'custom-cast' / 'agent_chat_repl.py'
if not target.is_file():
    raise SystemExit('md-chat target not found: ' + str(target))
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name='__main__')
