"""U2: repair the installed 0.5.5 renderer, preserving custom cast/map patches.

Called by patch_renderer.py for every regeneration. Can also patch an existing
renderer directory. Exact anchors fail closed on a different upstream version.
"""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError('U2 anchor count: %d: %s' % (text.count(old), old[:100]))
    return text.replace(old, new, 1)


def patch(renderer):
    assets = Path(renderer) / 'assets'
    global_path = next(p for p in assets.glob('global-*.js') if 'reconcileWithLivePtys:' in p.read_text(encoding='utf-8'))
    main_path = next(p for p in assets.glob('index-*.js') if 'function useRestoreTeam(' in p.read_text(encoding='utf-8'))
    g = global_path.read_text(encoding='utf-8')
    m = main_path.read_text(encoding='utf-8')
    if '/*__mdU2Reconcile*/' in g and '/*__mdU2AlreadyLive*/' in m:
        print('U2 already installed')
        return

    g = replace_once(g,
        '    if (s.agents.some((a) => a.id === agent.id)) return s;',
        '''    /*__mdU2AddAgent*/
    const existing = s.agents.find((a) => a.id === agent.id);
    if (existing) {
      // A successful spawn must attach to a restored card that has no PTY.
      // Preserve its identity, notes, order and the user's current selection.
      const attach = !existing.ptyId && !!agent.ptyId;
      const agents = attach ? s.agents.map((a) => a.id === agent.id ? {
        ...a, ptyId: agent.ptyId, archived: false,
        status: agent.status, action: agent.action, seedPrompt: agent.seedPrompt,
        worktreePath: agent.worktreePath, recentTextTs: agent.recentTextTs
      } : a) : s.agents;
      if (!existing.ptyId && !attach) return s;
      const restorableAgents = s.restorableAgents.filter((a) => a.id !== agent.id);
      const archivedAgents = s.archivedAgents.filter((a) => a.id !== agent.id);
      if (!attach && restorableAgents.length === s.restorableAgents.length &&
          archivedAgents.length === s.archivedAgents.length) return s;
      persistAgents(agents, s.selectedId);
      persistRestorable(restorableAgents);
      persistArchived(archivedAgents);
      return { agents, restorableAgents, archivedAgents };
    }''')
    old = '''    const live = new Set(livePtyIds);
    const agents = s.agents.filter((a) => !a.ptyId || live.has(a.ptyId));
    if (agents.length === s.agents.length) return s;
    const dead = s.agents.filter(
      (a) => a.ptyId && !live.has(a.ptyId) && !a.isGod && !a.isAssistant
    );
    const restorableAgents = [
      ...s.restorableAgents.filter((r) => !dead.some((d) => d.id === r.id)),
      ...dead
    ];'''
    new = '''    /*__mdU2Reconcile*/
    const live = new Set(livePtyIds);
    // Legacy rosters can lose ptyId while retaining the real spawn recipe.
    // Only a PTY returned by main is a live connection; never invent one.
    const connected = s.agents.map((a) => {
      const id = a.ptyId || `pty-${a.id}`;
      return live.has(id) && a.ptyId !== id ? { ...a, ptyId: id } : a;
    });
    const needsPty = (a) => !!a.ptyId || !!(a.command?.trim() && a.cwd);
    const agents = connected.filter((a) => !needsPty(a) || live.has(a.ptyId));
    const activeIds = new Set(agents.filter((a) => a.ptyId && live.has(a.ptyId)).map((a) => a.id));
    const dead = connected.filter(
      (a) => needsPty(a) && !live.has(a.ptyId) && !a.isGod && !a.isAssistant
    );
    const restorableAgents = [
      ...s.restorableAgents.filter((r) => !activeIds.has(r.id) && !dead.some((d) => d.id === r.id)),
      ...dead
    ];
    if (agents.length === s.agents.length && agents.every((a, i) => a === s.agents[i]) &&
        restorableAgents.length === s.restorableAgents.length &&
        restorableAgents.every((a, i) => a === s.restorableAgents[i])) return s;'''
    g = replace_once(g, old, new)
    m = replace_once(m,
        '    if ((res.error ?? "").includes("already exists")) return { outcome: "already-live" };',
        '''    if ((res.error ?? "").includes("already exists")) {
      // Confirm ownership of an actual terminal before consuming the recipe.
      const live = await deps.listPtys();
      if (live.some((p) => p.id === ptyId)) return { outcome: "already-live", ptyId };
      return { outcome: "failed", error: "terminal exited while reconnecting; retry restore" };
    }''')
    m = replace_once(m,
        'const rendererRespawnDeps = {\n  gitIsRepo:',
        'const rendererRespawnDeps = {\n  listPtys: () => window.cth.listPtys(),\n  gitIsRepo:')
    m = replace_once(m,
        '''          } else if (res.outcome === "already-live") {
            alreadyLive++;
            useStore.getState().removeRestorableAgent(a.id);
          } else {''',
        '''          } else if (res.outcome === "already-live") {
            /*__mdU2AlreadyLive*/
            alreadyLive++;
            landed++;
            emit$2();
            return { ...a, provider, ptyId: res.ptyId, archived: false,
              status: "idle", action: "reconnected", carrying: void 0,
              currentStation: "desk", recentTextTs: Date.now() };
          } else {''')
    # Validate all anchors before writing either file.
    global_path.write_text(g, encoding='utf-8', newline='\n')
    main_path.write_text(m, encoding='utf-8', newline='\n')
    print('U2 patched: reconcile, attach, confirmed already-live reconnect')


if __name__ == '__main__':
    patch(sys.argv[1] if len(sys.argv) > 1 else HERE.parent / '_renderer-patched')
