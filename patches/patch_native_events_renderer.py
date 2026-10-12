"""Render normalized thinking events received through the app's native hook pipe."""
from pathlib import Path
import sys


def patch(renderer):
    assets = Path(renderer) / 'assets'
    path = next(p for p in assets.glob('index-*.js') if 'function AgentScreen(' in p.read_text(encoding='utf-8'))
    source = path.read_text(encoding='utf-8')
    if '/*__mdThinkingHook*/' in source:
        return
    anchor = '''      } else if (e.event === "PostInvocation") {'''
    replacement = '''      } else if (e.event === "Thinking") { /*__mdThinkingHook*/
        if (!breakerArmed) updateAgent(e.agentId, { status: "working", action: (e.message || "thinking").slice(0, 120) });
''' + anchor
    if source.count(anchor) != 1:
        raise RuntimeError('thinking hook anchor count ' + str(source.count(anchor)))
    path.write_text(source.replace(anchor, replacement, 1), encoding='utf-8', newline='\n')
    print('native thinking hook patched:', path)


if __name__ == '__main__':
    patch(sys.argv[1] if len(sys.argv) > 1 else r'D:\徐\MunderDifflin\Munder-Difflin-0.5.5-fixed\resources\app\out\renderer')
