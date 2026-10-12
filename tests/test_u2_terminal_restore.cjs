'use strict';
// Run the actual shipping bundle functions without Electron or the desktop.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');
const assets = path.join(process.argv[2] || 'D:/徐/MunderDifflin/_renderer-u2', 'assets');
const read = (prefix, needle) => fs.readdirSync(assets).filter(n => n.startsWith(prefix) && n.endsWith('.js'))
  .map(n => fs.readFileSync(path.join(assets, n), 'utf8')).find(s => s.includes(needle));
const g = read('global-', 'reconcileWithLivePtys:');
const m = read('index-', 'function useRestoreTeam(');
const between = (s, a, b) => { const start = s.indexOf(a); assert(start >= 0, a); const end = s.indexOf(b, start); assert(end > start, b); return s.slice(start, end); };
const agent = (id, extra = {}) => ({ id, name: id, command: 'test-engine', cwd: 'D:/test', status: 'idle', ...extra });
function harness(agents, restorable = []) {
  const disk = {}; const local = new Map();
  let state = { agents, restorableAgents: restorable, archivedAgents: [], feeds: {}, selectedId: agents[0]?.id || null, fullscreenAgentId: null };
  const ctx = vm.createContext({
    window: { localStorage: { setItem: (k,v) => local.set(k,v) } },
    LS_AGENTS: 'agents', LS_SELECTED: 'selected', LS_RESTORABLE: 'restorable',
    rosterMirror: disk, scheduleRosterFlush() {}, IS_IDE_WINDOW: false,
    persistArchived: a => { disk.archived = JSON.parse(JSON.stringify(a)); },
    refocusAfterRemoval: () => null,
    set: fn => { state = { ...state, ...fn(state) }; },
  });
  vm.runInContext(between(g, 'function slimAgents(', '\nfunction persistAgents(') +
    between(g, 'function persistAgents(', '\nconst VOLATILE_AGENT_FIELDS') +
    between(g, 'function persistRestorable(', '\nfunction loadPersistedRestorable('), ctx);
  const add = between(g, '  addAgent: (agent)', '\n  removeAgent:');
  const reconcile = between(g, '  reconcileWithLivePtys:', '\n  setAddAgentOpen:');
  const actions = vm.runInContext('({' + add + reconcile + '})', ctx);
  return { actions, state: () => state, disk, local };
}
test('lost ptyId with a spawn recipe becomes restorable; synthetic card stays', () => {
  const h = harness([agent('worker'), {id:'demo', name:'demo'}]);
  h.actions.reconcileWithLivePtys([]);
  assert.deepEqual(h.state().agents.map(a=>a.id), ['demo']);
  assert.equal(h.state().restorableAgents[0].id, 'worker');
});
test('surviving terminal reconnects and clears duplicate restore recipe', () => {
  const h = harness([agent('worker')], [agent('worker')]);
  h.actions.reconcileWithLivePtys(['pty-worker']);
  assert.equal(h.state().agents[0].ptyId, 'pty-worker');
  assert.equal(h.state().restorableAgents.length, 0);
  assert.equal(JSON.parse(h.local.get('agents'))[0].ptyId, 'pty-worker');
  const reload = harness(JSON.parse(JSON.stringify(h.disk.agents)));
  reload.actions.reconcileWithLivePtys(['pty-worker']);
  assert.equal(reload.state().agents[0].ptyId, 'pty-worker');
  reload.actions.reconcileWithLivePtys([]);
  assert.equal(reload.state().agents.length, 0);
  assert.equal(reload.state().restorableAgents[0].id, 'worker');
});
test('successful restore attaches to existing card and persists without changing order/notes/selection', () => {
  const h = harness([agent('first', {ptyId:'pty-first'}), agent('worker', {notes:'keep me'})], [agent('worker')]);
  h.actions.addAgent(agent('worker', {ptyId:'pty-worker', notes:'broadcast'}));
  assert.equal(h.state().agents.length, 2);
  assert.equal(h.state().agents[1].ptyId, 'pty-worker');
  assert.equal(h.state().agents[1].notes, 'keep me');
  assert.equal(h.state().selectedId, 'first');
  assert.equal(h.state().restorableAgents.length, 0);
  assert.equal(JSON.parse(h.local.get('agents'))[1].ptyId, 'pty-worker');
  h.actions.addAgent(agent('worker', {ptyId:'pty-worker'}));
  assert.equal(h.state().agents.length, 2);
});
test('explicit nonstandard live PTY survives; stale explicit ID is never falsely live', () => {
  const h = harness([agent('a', {ptyId:'custom-session'}), agent('b', {ptyId:'old-session'})]);
  h.actions.reconcileWithLivePtys(['custom-session', 'pty-b']);
  assert.equal(h.state().agents.length, 1);
  assert.equal(h.state().agents[0].ptyId, 'custom-session');
  assert.equal(h.state().restorableAgents[0].id, 'b');
});
const spawnCtx = vm.createContext({ COLS:100, ROWS$1:30, roleForHiveSpawn: () => 'worker' });
const respawn = vm.runInContext(between(m, 'async function respawnAgent(', '\nconst rendererRespawnDeps') + '\nrespawnAgent', spawnCtx);
test('spawn registers stable identity and returns the actual requested terminal ID', async () => {
  let opts;
  const res = await respawn(agent('worker'), {exe:'test-engine', provider:'custom', args:[]}, {
    spawnPty: async o => { opts=o; return {ok:true}; }
  });
  assert.equal(res.ptyId, 'pty-worker');
  assert.equal(opts.hive.id, 'worker');
  assert.equal(opts.id, res.ptyId);
});
test('already exists must be backed by a live PTY; failures remain retryable', async () => {
  const recipe = {exe:'test-engine', provider:'custom', args:[]};
  const deps = {spawnPty: async () => ({ok:false,error:'PTY already exists'}), listPtys:async()=>[{id:'pty-worker'}]};
  const live = await respawn(agent('worker'), recipe, deps);
  assert.equal(live.outcome, 'already-live');
  assert.equal(live.ptyId, 'pty-worker');
  const gone = await respawn(agent('worker'), recipe, {...deps,listPtys:async()=>[]});
  assert.equal(gone.outcome, 'failed');
  const failed = await respawn(agent('worker'), recipe, {...deps,spawnPty:async()=>({ok:false,error:'cannot spawn'})});
  assert.equal(failed.outcome, 'failed');
  assert.equal(failed.ptyId, undefined);
});
test('restore hook reconnects an already running terminal, consumes recipe only after add, and retains failures', async () => {
  const h = harness([], [agent('live'), agent('broken')]);
  const ctx = vm.createContext({
    reactExports:{useSyncExternalStore:()=>false,useEffect(){}}, subscribe$b(){}, getRestoring(){}, getNote(){}, getAutoRestoring(){},
    applyRestoreGate:async()=>{},
    useEffect(){}, restoring:false, note:null, landed:0, total:0, autoRestoring:false, emit$2(){},
    useStore:{getState:()=>({...h.state(),...h.actions})},
    inferAgentProvider:()=> 'custom', commandWithModel:c=>c,
    tokenizeCommand:c=>[c], rendererRespawnDeps:{}, console:{error(){}},
    respawnAgent:async a=>a.id==='live'?{outcome:'already-live',ptyId:'pty-live'}:{outcome:'failed',error:'failed for test'}
  });
  const fn = between(m, 'function useRestoreTeam(', '\nfunction ');
  const hook = vm.runInContext(fn+'\nuseRestoreTeam',ctx);
  await hook().restoreTeam();
  assert.equal(h.state().agents[0].ptyId,'pty-live');
  assert.equal(h.state().restorableAgents.length,1);
  assert.equal(h.state().restorableAgents[0].id,'broken');
  assert.equal(JSON.parse(h.local.get('agents'))[0].ptyId,'pty-live');
});
