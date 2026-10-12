/**
 * 天枢（rivet）无头调用核心 —— 从 Node 里跑一次天枢，拿回最终答复。
 *
 * 这是 dsh-subagent-tianshu 插件的"引擎"部分，单独可测：
 *   node plugins/dsh-subagent-tianshu/lib/tianshu-run.mjs "用一句话说你是谁"
 *   node plugins/dsh-subagent-tianshu/lib/tianshu-run.mjs --goal "列出当前目录" --budget 4
 *
 * 设计要点（都有实测依据）：
 *  · 天枢 CLI 的无头形态是 `rivet -p "<prompt>" [--json]`（一次性）
 *    或 `rivet --goal "<task>" --budget N [--json]`（目标模式）
 *  · 本机 CLI 垫片在 %APPDATA%\npm\tianshu-agent.cmd（走 cmd.exe），也支持 rivet 本体
 *  · Windows 上必须避开 ELECTRON_RUN_AS_NODE（本机 DSH shell 会设它，会让 node 变味）
 *  · 输出可能是 JSON 事件流（--json），要按行解析，取最终文本
 */
import { spawn, execFileSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

/**
 * 从 Windows 用户环境里取 DEEPSEEK_API_KEY（天枢运行时需要；子进程默认继承不到）。
 * 只读注册表值，不写入、不打印密钥。
 */
export function deepseekKeyFromUserEnv() {
  if (process.env.DEEPSEEK_API_KEY) return process.env.DEEPSEEK_API_KEY;
  try {
    const out = execFileSync('reg', ['query', 'HKCU\\Environment', '/v', 'DEEPSEEK_API_KEY'],
      { encoding: 'utf8', windowsHide: true });
    const m = out.match(/DEEPSEEK_API_KEY\s+REG_\w+\s+(.+)/);
    return m ? m[1].trim() : '';
  } catch {
    return '';
  }
}

/** 找天枢可执行文件：优先 tianshu-agent 垫片，其次 rivet。 */
export function resolveRivet() {
  const cands = [
    process.env.MD_TIANSHU_BIN,
    join(process.env.APPDATA || '', 'npm', 'tianshu-agent.cmd'),
    join(process.env.APPDATA || '', 'npm', 'rivet.cmd'),
    join(process.env.LOCALAPPDATA || '', 'Tianshu', 'rivet-runtime', 'cli', 'entry.js'),
    'rivet',
  ].filter(Boolean);
  for (const c of cands) {
    if (c === 'rivet') return { command: 'rivet', viaCmd: false };
    if (existsSync(c)) {
      if (c.endsWith('.js')) return { command: process.execPath, argsPrefix: [c], viaCmd: false };
      return { command: c, viaCmd: c.endsWith('.cmd') };
    }
  }
  return { command: 'rivet', viaCmd: false };
}

/** 组装天枢命令行参数。 */
export function rivetArgs(task, { goal = false, budget = 4, json = true, streamJson = false } = {}) {
  const a = [];
  if (goal) {
    a.push('--goal', task, '--budget', String(budget));
  } else {
    a.push('-p', task);
  }
  if (json) a.push('--json');
  if (streamJson) a.push('--stream-json');
  a.push('--skip-welcome', '--dangerously-skip-permissions');
  return a;
}

/** 从一段输出里尽力抽出"最终答复"。 */
export function extractAnswer(text) {
  if (!text) return '';
  const lines = text.split(/\r?\n/).filter((l) => l.trim());
  const finals = [];
  for (const l of lines) {
    const s = l.trim();
    if (s.startsWith('{')) {
      try {
        const o = JSON.parse(s);
        // 天枢无头 JSON 的最终信封：{"success":true,"text":"...","usage":{...}}
        if (typeof o.success === 'boolean' && typeof o.text === 'string') {
          finals.push(o.text);
          continue;
        }
        const t = o.type || o.event;
        if (t === 'final' || t === 'result' || t === 'answer') {
          finals.push(o.text || o.content || o.result || '');
          continue;
        }
        if (t === 'text' || t === 'message' || t === 'assistant') {
          const v = o.text || o.content;
          if (v) finals.push(Array.isArray(v) ? v.map(String).join('') : String(v));
          continue;
        }
      } catch {
        /* 不是 JSON 行，当纯文本 */
      }
    }
    if (!s.startsWith('{"') && !s.startsWith('[')) finals.push(s);
  }
  const joined = finals.join('\n').trim();
  return joined || text.trim();
}

/**
 * 跑一次天枢。
 * @param {string} task 任务文本
 * @param {object} opts {goal,budget,cwd,env,timeoutMs,json,onLine,abortSignal}
 * @returns {Promise<{answer:string,exitCode:number,raw:string,elapsedMs:number,argv:string[]}>}
 */
export function runTianshu(task, opts = {}) {
  const { goal = false, budget = 4, cwd = process.cwd(), env = {}, timeoutMs = 900000, json = true, onLine, abortSignal } = opts;
  const bin = resolveRivet();
  const args = [...(bin.argsPrefix || []), ...rivetArgs(task, { goal, budget, json })];
  const childEnv = { ...process.env, ...env };
  delete childEnv.ELECTRON_RUN_AS_NODE;      // 本机必须去掉（否则 node 行为异常）
  if (!childEnv.DEEPSEEK_API_KEY) {          // 天枢要它；子进程默认继承不到
    const k = deepseekKeyFromUserEnv();
    if (k) childEnv.DEEPSEEK_API_KEY = k;
  }
  const started = Date.now();
  const argv = [bin.command, ...args];

  return new Promise((resolve, reject) => {
    const child = spawn(bin.command, args, {
      cwd, env: childEnv, windowsHide: true, shell: !!bin.viaCmd || bin.command.endsWith('.cmd'),
    });
    let out = '';
    let err = '';
    let killed = false;
    const timer = setTimeout(() => { killed = true; try { child.kill(); } catch {} }, timeoutMs);
    const onAbort = () => { killed = true; try { child.kill(); } catch {} };
    if (abortSignal) abortSignal.addEventListener('abort', onAbort, { once: true });

    child.stdout?.setEncoding('utf8');
    child.stderr?.setEncoding('utf8');
    child.stdout?.on('data', (d) => { out += d; if (onLine) String(d).split(/\r?\n/).forEach((l) => l.trim() && onLine(l, 'out')); });
    child.stderr?.on('data', (d) => { err += d; if (onLine) String(d).split(/\r?\n/).forEach((l) => l.trim() && onLine(l, 'err')); });
    child.on('error', (e) => { clearTimeout(timer); reject(e); });
    child.on('close', (code) => {
      clearTimeout(timer);
      if (abortSignal) abortSignal.removeEventListener('abort', onAbort);
      const raw = out || err;
      resolve({
        answer: extractAnswer(raw), exitCode: code ?? -1, raw,
        elapsedMs: Date.now() - started, argv, killed,
      });
    });
  });
}

// ---- 直接运行时当 CLI 自测用 ----
import { pathToFileURL } from 'node:url';
const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  const argv = process.argv.slice(2);
  const goalIdx = argv.indexOf('--goal');
  const budgetIdx = argv.indexOf('--budget');
  const goal = goalIdx >= 0;
  const budget = budgetIdx >= 0 ? Number(argv[budgetIdx + 1]) || 4 : 4;
  const task = goal ? argv[goalIdx + 1] : (argv.find((a) => !a.startsWith('--') && a !== String(budget)) || '你好');
  console.log('  可执行文件:', JSON.stringify(resolveRivet()));
  console.log('  参数:', rivetArgs(task, { goal, budget }).join(' '));
  const t0 = Date.now();
  runTianshu(task, { goal, budget, onLine: (l) => console.log('   | ' + l.slice(0, 150)) })
    .then((r) => {
      console.log('  ---- 结果 ----');
      console.log('  退出码:', r.exitCode, '｜ 用时:', (r.elapsedMs / 1000).toFixed(1) + 's');
      console.log('  答复:', (r.answer || '(空)').slice(0, 600));
    })
    .catch((e) => { console.error('  失败:', e.message); process.exitCode = 1; });
}
